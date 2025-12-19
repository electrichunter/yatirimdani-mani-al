"""
Sniper Trading Bot - Ana Döngü
Üç Kademeli Filtreleme Sistemi: Teknik -> Haber -> RAG+LLM
RTX 3050 4GB VRAM için optimize edilmiştir
"""

import time
import os
import webbrowser
import threading
import subprocess
from datetime import datetime
import config
from core.broker_yfinance import YFinanceBroker
from core.data_fetcher import DataFetcher
from core.risk_manager import RiskManager
from filters.stage1_technical import TechnicalFilter
from filters.stage2_news import NewsFilter
from filters.stage3_llm import LLMDecisionEngine
from utils.logger import setup_logger
from utils.economic_calendar import EconomicCalendar
from utils.formatter import UIFormatter

# ========================================
# BAŞLATMA
# ========================================

logger = setup_logger("SniperBot")
ui = UIFormatter()

def select_mode():
    """Etkileşimli mod seçimi"""
    print("\n" + "=" * 60)
    print("🎯 SNIPER TRADING BOT")
    print("=" * 60)
    
    print("\n1. Veri Kaynağı Seçin:")
    print("  [C] Canlı Piyasa Verisi (Yahoo Finance)")
    print("  [D] Demo/Simüle Veri (Simulated Data)")
    
    print("\n2. İşlem Modu:")
    print("  [S] Sinyal Modu (Sadece Analiz)")
    print("  [T] Test Modu (DRY RUN - Analiz + Sanal Emir)")
    
    print("\n3. Yapay Zeka (LLM) Seçin:")
    print("  [G] Gemini API (Bulut - Hızlı)")
    print(f"  [O] Ollama (Yerel - {config.LLM_MODEL})")
    print("=" * 60)
    
    # 1. Veri kaynağı seçimi
    while True:
        veri = input("\nVeri kaynağı (C/D): ").strip().upper()
        if veri in ['C', 'D']:
            break
        print("❌ Lütfen C veya D girin!")
    
    # 2. İşlem modu seçimi
    while True:
        islem = input("İşlem modu (S/T): ").strip().upper()
        if islem in ['S', 'T']:
            break
        print("❌ Lütfen S veya T girin!")
        
    # 3. LLM seçimi
    while True:
        llm_choice = input("Yapay Zeka Seçimi (G/O): ").strip().upper()
        if llm_choice in ['G', 'O']:
            break
        print("❌ Lütfen G veya O girin!")
    
    # Yapılandırmayı güncelle
    config.DEMO_MODE = (veri == 'D')
    config.DRY_RUN = True # YFinance ile gerçek işlem yapılamaz, daima True (Sanal)
    config.USE_GEMINI_API = (llm_choice == 'G')
    
    # Eğer Ollama seçildiyse Config'deki modeli kullanalım
    if not config.USE_GEMINI_API:
        # config.LLM_MODEL zaten config.py'de tanımlı, burada dokunmuyoruz ki kullanıcı ne yazdıysa o gelsin
        pass
    
    print("\n" + "=" * 60)
    print(f"✅ Veri: {'📊 Canlı (YFinance)' if veri == 'C' else '🎲 Simüle'}")
    print(f"✅ Mod: {'📋 Test/Sanal' if islem == 'T' else 'ℹ️ Sinyal Modu'}")
    print(f"✅ AI Backend: {'☁️ Gemini' if config.USE_GEMINI_API else f'🏠 Ollama ({config.LLM_MODEL})'}")
    print("=" * 60)
    
    if islem == 'S':
        print("\nℹ️  Sinyal Modu: Gerçek veri ile analiz yapılacak.")
        print("   Alım-satım emirleri ekrana yazılacak ancak iletilmeyecek.")
        
    confirm = input("   Devam etmek istediğinize emin misiniz? (y/n): ").strip().lower()
    if confirm not in ["y", "yes", "evet", "e"]:
        print("❌ İptal edildi.")
        exit(0)
    
    input("\nDevam etmek için Enter'a basın...")
    print("\n")

def initialize_system():
    """Tüm bileşenleri başlatır"""
    logger.info("=" * 60)
    logger.info("🎯 SNIPER TRADING BOT - SİSTEM BAŞLATILIYOR")
    logger.info("=" * 60)
    logger.info(f"Başlangıç Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mod: {'📋 TEST MODU (Sadece Öneriler)' if config.DRY_RUN else '💰 CANLI İŞLEM'}")
    logger.info(f"LLM Model: {config.GEMINI_MODEL if config.USE_GEMINI_API else config.LLM_MODEL} {'(BULUT)' if config.USE_GEMINI_API else '(YEREL)'}")
    logger.info(f"İzlenen Varlıklar: {len(config.SYMBOLS)} adet")
    logger.info(f"Kontrol Aralığı: {config.CHECK_INTERVAL}s ({config.CHECK_INTERVAL/60:.1f} dakika)")
    logger.info(f"Min Güven: %{config.MIN_CONFIDENCE}")
    logger.info(f"Min Risk/Ödül: {config.MIN_RISK_REWARD_RATIO}:1")
    logger.info("=" * 60)
    
    # Çekirdek bileşenleri başlat
    broker = YFinanceBroker()
    if not broker.initialized:
        logger.error("❌ Broker başlatılamadı")
        return None
    
    data_fetcher = DataFetcher(broker)
    risk_manager = RiskManager(broker)
    
    # 1. ve 2. Aşama (GPU Gerektirmez)
    technical_filter = TechnicalFilter()
    news_filter = NewsFilter()
    news_db = news_filter.db # Haber veritabanına doğrudan erişim
    
    # Ekonomik Takvim (gelecek olaylar için)
    economic_calendar = EconomicCalendar()
    
    # 3. Aşama (Lazy loading - sadece ihtiyaç duyulduğunda yüklenir)
    llm_engine = None  # İlk ihtiyaçta başlatılacaktır
    
    logger.info("✅ Sistem başarıyla başlatıldı")
    logger.info("")
    
    return {
        "broker": broker,
        "data_fetcher": data_fetcher,
        "risk_manager": risk_manager,
        "technical_filter": technical_filter,
        "news_filter": news_filter,
        "news_db": news_db, # Haber veritabanı erişimi
        "economic_calendar": economic_calendar,
        "llm_engine": llm_engine
    }

def process_symbol(symbol, components):
    """
    Tek bir sembolü üç kademeli filtreden geçirir
    """
    ui.print_market_header(symbol)
    
    # Bileşenleri çıkart
    data_fetcher = components["data_fetcher"]
    technical_filter = components["technical_filter"]
    news_filter = components["news_filter"]
    economic_calendar = components["economic_calendar"]
    risk_manager = components["risk_manager"]
    broker = components["broker"]
    
    # LLM için gelecek olayları hazırla
    upcoming_events = economic_calendar.get_upcoming_events(symbol=symbol)

    # ========================================
    # 1. AŞAMA: TEKNİK SERT FİLTRE
    # ========================================
    # Hedef: İşlemlerin %90'ından fazlasını anında elemek
    # Hızlı çalışma (< 0.1 saniye), GPU kullanmaz
    
    market_data = data_fetcher.get_multi_timeframe_data(
        symbol=symbol,
        timeframes=list(config.TIMEFRAMES.keys())
    )
    
    if not market_data or market_data.get("current_price") is None:
        logger.warning(f"⚠️ {symbol} - Piyasa verisi alınamadı")
        return False
    
    current_price = market_data["current_price"]
    logger.info(f"💰 {symbol} Güncel Fiyat: {current_price}")
    
    stage1_result = technical_filter.analyze(market_data)
    
    if not stage1_result["pass"]:
        logger.info(f"❌ {symbol} - 1. Aşama BAŞARISIZ (Teknik Filtre): {stage1_result['reason']}")
        return False
    
    ui.print_stage_result(1, stage1_result, symbol)
    
    # ========================================
    # 2. AŞAMA: HABER DUYGU FİLTRESİ
    # ========================================
    # Hedef: İşlem yönünü temel verilerle doğrulamak
    # Sadece SQL sorgusu (< 0.5 saniye), GPU kullanmaz
    
    trade_direction = stage1_result["direction"]
    
    stage2_result = news_filter.check_sentiment(
        symbol=symbol,
        direction=trade_direction,
        hours_lookback=config.NEWS_LOOKBACK_HOURS
    )
    
    ui.print_stage_result(2, stage2_result, symbol)
    
    # ========================================
    # 3. AŞAMA: LLM KARARI (SNIPER MODU)
    # ========================================
    # Hedef: Strateji bilgisiyle son doğrulama
    # ŞİMDİ LLM'i yüklüyoruz (2-5 saniye, GPU gerekir)
    
    if components["llm_engine"] is None:
        logger.info("🔧 LLM Karar Motoru ilk kez yükleniyor...")
        components["llm_engine"] = LLMDecisionEngine(
            model_name=config.LLM_MODEL,
            rag_data_path=config.RAG_DATA_PATH
        )
    
    llm_engine = components["llm_engine"]
    
    # LLM için bağlam hazırla
    context = {
        "symbol": symbol,
        "technical_signals": stage1_result["signals"],
        "technical_score": stage1_result["score"],
        "news_sentiment": stage2_result["sentiment_score"],
        "relevant_news": stage2_result["relevant_news"],
        "upcoming_events": upcoming_events,
        "current_price": market_data["current_price"],
        "direction": trade_direction
    }
    
    # LLM'e Sor: "Bu işlemi yapmalı mıyım?"
    stage3_result = llm_engine.make_decision(context)
    
    if stage3_result["decision"] == "PASS":
        logger.info(f"❌ {symbol} - 3. Aşama REDDEDİLDİ: {stage3_result['reasoning']}")
        return False
    
    if stage3_result["confidence"] < config.MIN_CONFIDENCE:
        logger.info(f"❌ {symbol} - Düşük güven seviyesi ({stage3_result['confidence']}% < {config.MIN_CONFIDENCE}%)")
        return False
    
    # UI için sonucu hazırla
    signal_info = {
        "decision": stage3_result["decision"],
        "confidence": stage3_result["confidence"],
        "reasoning": stage3_result["reasoning"],
        "entry_price": float(market_data["current_price"]),
        "stop_loss": stage3_result["stop_loss"],
        "take_profit": stage3_result["take_profit"],
        "timeframe": stage3_result.get("timeframe", "H1"),
        "expected_duration": stage3_result.get("expected_duration", "Bilinmiyor"),
        "rr_ratio": 0 # Doğrulamadan sonra güncellenecek
    }
    
    # ========================================
    # RİSK YÖNETİMİ & DOĞRULAMA
    # ========================================
    
    # Pozisyon limitlerini kontrol et
    position_check = risk_manager.check_position_limits()
    if not position_check["allowed"]:
        logger.warning(f"⚠️ {symbol} - {position_check['reason']}")
        return False
    
    # Risk/ödül oranını doğrula
    llm_entry = float(stage3_result.get("entry_price", 0))
    entry_to_use = llm_entry if llm_entry > 0 else float(market_data["current_price"])
    
    trade_validation = risk_manager.validate_trade(
        entry_price=entry_to_use,
        stop_loss=stage3_result["stop_loss"],
        take_profit=stage3_result["take_profit"],
        symbol=symbol,
        decision=stage3_result["decision"]
    )
    
    if not trade_validation["valid"]:
        logger.warning(f"⚠️ {symbol} - {trade_validation['reason']} -> ⏸️ BEKLEMEDE KAL (Risk/Ödül Uygun Değil)")
        # Sinyali dashboard'a "BEKLE" olarak gönder
        signal_info["decision"] = "BEKLE (Düşük R:R)"
        signal_info["reasoning"] = f"Teknik olarak uygun ancak Risk/Ödül oranı ({trade_validation['rr_ratio']}) düşük. " + signal_info.get("reasoning", "")
        ui.save_result_for_web(symbol, signal_info)
        return False
    
    # Fiyatları risk_manager'dan gelen (veya düzeltilen) değerlerle güncelle
    sl = float(trade_validation["sl"])
    tp = float(trade_validation["tp"])
    entry = entry_to_use
    
    # Pozisyon büyüklüğünü hesapla
    position_size = risk_manager.calculate_position_size(
        symbol=symbol,
        entry_price=entry,
        stop_loss=sl,
        risk_percent=config.RISK_PERCENT
    )
    
    # ========================================
    # İŞLEMİ UYGULA (VEYA ÖNERİYİ GÖSTER)
    # ========================================
    
    # SL ve TP için pip mesafesini hesapla
    try:
        # Pip çarpanını belirle
        if "=X" in symbol:  # Forex
            pip_multiplier = 10000 if "JPY" not in symbol else 100
        elif "GC=F" in symbol or "XAU" in symbol:  # Altın
            pip_multiplier = 10  # 0.1 birim = 1 pip
        elif "SI=F" in symbol or "XAG" in symbol:  # Gümüş
            pip_multiplier = 100 # 0.01 birim = 1 pip
        else:
            pip_multiplier = 1  # Endeksler, hisseler, kripto için
        
        sl_distance = abs(entry - sl) * pip_multiplier
        tp_distance = abs(tp - entry) * pip_multiplier
    except Exception as e:
        logger.error(f"❌ Mesafe hesaplama hatası: {e}")
        sl_distance = 0
        tp_distance = 0
    
    # Final UI Çıktısı & Kaydet
    signal_info["rr_ratio"] = trade_validation['rr_ratio']
    signal_info["entry_price"] = entry
    signal_info["stop_loss"] = sl
    signal_info["take_profit"] = tp
    
    ui.print_trade_signal(symbol, signal_info)

    # ========================================
    # ÖĞRENME SİSTEMİ: İşlemi Günlüğe Kaydet
    # ========================================
    if "llm_engine" in components and components["llm_engine"] is not None:
        try:
            # Context'i hazırla (Stage 1 & 2 verileri)
            learning_context = {
                "technical_score": stage1_result.get("score", 0),
                "news_sentiment": stage2_result.get("sentiment_score", 0),
                "technical_signals": stage1_result.get("signals", {})
            }
            # Kararı kaydet
            components["llm_engine"].learning_system.log_trade_decision(
                symbol=symbol,
                direction=stage3_result["decision"],
                context=learning_context,
                llm_decision=stage3_result,
                dry_run=config.DRY_RUN
            )
        except Exception as e:
            logger.error(f"⚠️ Öğrenme sistemi kayıt hatası: {e}")

    # Test modu kontrolü
    if config.DRY_RUN:
        return True
    
    # Gerçek işlemi gerçekleştir
    logger.info("💰 Gerçek işlem uygulanıyor...")
    
    order = broker.place_order(
        symbol=symbol,
        action=stage3_result["decision"],
        volume=position_size,
        entry=None,  # Market emri
        sl=sl,
        tp=tp,
        comment=f"Sniper-{stage3_result['confidence']}%"
    )
    
    if order["success"]:
        logger.info(f"✅ EMİR UYGULANDI: Ticket #{order['ticket']}")
        logger.info(f"   Fiyat: {order['price']}")
        logger.info(f"   Hacim: {order['volume']} lot")
        logger.info("=" * 60)
        return True
    else:
        logger.error(f"❌ EMİR BAŞARISIZ: {order['error']}")
        logger.info("=" * 60)
        return False

from update_news import update_news

def run_dashboard_server():
    """Dashboard sunucusunu arka planda çalıştırır"""
    subprocess.run(["python", "run_dashboard.py"])

def main():
    """Ana işlem döngüsü"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Otomatik başlatma: Test Modu + Yahoo Finance
        config.DEMO_MODE = False
        config.DRY_RUN = True
        logger.info("🤖 Otomatik Başlatma: Yahoo Finance + Test Modu")
    else:
        select_mode()
    
    # Dashboard'u arka planda başlat
    logger.info("🌐 Dashboard başlatılıyor...")
    threading.Thread(target=run_dashboard_server, daemon=True).start()
    time.sleep(2) # Sunucunun kalkması için kısa bir süre bekle
    webbrowser.open("http://localhost:8000/dashboard.html")

    # Sistemi başlat
    components = initialize_system()
    
    if components is None:
        logger.error("❌ Sistem başlatma başarısız")
        return
    
    # Ana döngü
    try:
        # Veri dizininin var olduğundan emin ol
        os.makedirs("data", exist_ok=True)
        logger.info("📁 Veri dizini kontrol edildi.")

        last_news_update = 0
        NEWS_UPDATE_INTERVAL = 24 * 60 * 60 # 24 saat (saniye)

        while True:
            loop_start = time.time()
            
            logger.info("")
            logger.info(f"⏰ Tarama başlatıldı: {datetime.now().strftime('%H:%M:%S')}")
            
            # Haberleri API'den güncelle (Sadece 24 saatte bir)
            if time.time() - last_news_update > NEWS_UPDATE_INTERVAL:
                try:
                    logger.info("🌍 Dış kaynaktan (API) haberler güncelleniyor (24 saatlik rutin)...")
                    update_news()
                    last_news_update = time.time()
                except Exception as e:
                    logger.error(f"⚠️ Haber güncelleme hatası: {str(e)}")
            else:
                next_update = (last_news_update + NEWS_UPDATE_INTERVAL) - time.time()
                logger.debug(f"ℹ️ Haberler güncel. Bir sonraki derin tarama {next_update/3600:.1f} saat sonra.")

            # --- SİSTEM ÖĞRENİMİ: BEKLEYEN İŞLEMLERİ DENETLE ---
            if "llm_engine" in components and components["llm_engine"] is not None:
                try:
                    pending_trades = components["llm_engine"].learning_system.get_pending_trades()
                    if pending_trades:
                        logger.info(f"🔍 {len(pending_trades)} adet bekleyen işlem denetleniyor...")
                        for trade in pending_trades:
                            # Güncel fiyatı al (YFinance)
                            ticker = data_fetcher.broker.get_ticker(trade["symbol"])
                            if ticker is None: continue
                            
                            price = ticker.info.get("regularMarketPrice")
                            if price is None: continue
                            
                            # TP/SL Kontrolü
                            outcome = None
                            if trade["direction"] == "BUY":
                                if price >= trade["take_profit"]: outcome = "WIN"
                                elif price <= trade["stop_loss"]: outcome = "LOSS"
                            else: # SELL
                                if price <= trade["take_profit"]: outcome = "WIN"
                                elif price >= trade["stop_loss"]: outcome = "LOSS"
                            
                            if outcome:
                                profit_pips = abs(price - trade["entry_price"]) * (10000 if "JPY" not in trade["symbol"] else 100)
                                components["llm_engine"].learning_system.update_trade_outcome(
                                    trade_id=trade["id"],
                                    outcome=outcome,
                                    profit_pips=profit_pips,
                                    close_price=price
                                )
                                # Pattern analizini tetikle
                                components["llm_engine"].learning_system.analyze_patterns(min_samples=1) # Test için düşük eşik
                except Exception as e:
                    logger.error(f"⚠️ Bekleyen işlem denetleme hatası: {e}")

            # --- DASHBOARD VERİ HAZIRLAMA (Haberler + Beklenen Olaylar) ---
            try:
                combined_news = []
                
                # 1. Gelecek Önemli Haberler (Ekonomik Takvim - TÜMÜ)
                if "economic_calendar" in components:
                    ec = components["economic_calendar"]
                    upcoming = ec.get_upcoming_events("ALL", days_ahead=7)
                    if upcoming:
                        logger.info(f"📅 BEKLENEN ÖNEMLİ HABERLER ({len(upcoming)} adet):")
                        for event in upcoming:
                            etki = event.get('impact', 'MEDIUM').replace('HIGH', '🔴 YÜKSEK').replace('MEDIUM', '🟡 ORTA').replace('LOW', '🟢 DÜŞÜK')
                            logger.info(f"  • {event.get('date')} | {event.get('title')} | Etki: {etki}")
                            
                            combined_news.append({
                                "title": f"📅 [BEKLENEN] {event.get('title', 'Bilinmiyor')}",
                                "source": event.get("country", "ECON"),
                                "published_at": event.get("date"),
                                "sentiment_score": 0,
                                "impact_level": event.get("impact", "LOW"),
                                "symbols": event.get("country", "")
                            })
                        logger.info("-" * 40)
                    else:
                        logger.info("📅 Yakın zamanda önemli ekonomik haber bulunamadı.")
                
                # 2. Geçmiş/Güncel Haberler (Veritabanından)
                if "news_db" in components:
                    recent = components["news_db"].get_recent_news(hours_lookback=24)
                    for n in recent:
                        combined_news.append(n)
                
                # Dashboard için kaydet
                ui.save_news_for_web(combined_news)
                
            except Exception as e:
                logger.error(f"⚠️ Dashboard haber birleştirme hatası: {str(e)}")

            # Her sembolü işle
            for symbol in config.SYMBOLS:
                try:
                    process_symbol(symbol, components)
                    
                    import gc
                    gc.collect()  # VRAM/RAM'i boşaltmak için çöp toplayıcıyı çalıştır
                    
                    # İşlemler arası gecikme (Kullanıcı talebi)
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"❌ {symbol} işlenirken hata: {str(e)}")
            
            # Sonraki taramadan önce bekle
            loop_duration = time.time() - loop_start
            wait_time = max(0, config.CHECK_INTERVAL - loop_duration)
            
            ui.print_loop_status(wait_time)
            
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🛑 SNIPER BOT KULLANICI TARAFINDAN DURDURULDU")
        logger.info("=" * 60)
        components["broker"].close()
        # İşlem sonu dosyayı sil
        if os.path.exists("data/web_results.json"):
            os.remove("data/web_results.json")
    
    except Exception as e:
        logger.error(f"❌ Ana döngüde kritik hata: {str(e)}")
        components["broker"].close()
        # İşlem sonu dosyayı sil
        if os.path.exists("data/web_results.json"):
            os.remove("data/web_results.json")

if __name__ == "__main__":
    main()
