"""
Sniper Trading Bot - Main Loop
Three-Tier Filtering System: Technical -> News -> RAG+LLM
Optimized for RTX 3050 4GB VRAM
"""

import time
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

# ========================================
# INITIALIZATION
# ========================================

logger = setup_logger("SniperBot")

def select_mode():
    """Interactive mode selection"""
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
    print("  [O] Ollama (Yerel - Mistral)")
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
    
    # Config'i güncelle
    config.DEMO_MODE = (veri == 'D')
    config.DRY_RUN = True # YFinance ile işlem yapılamaz, daima True (Sanal)
    config.USE_GEMINI_API = (llm_choice == 'G')
    
    # Eğer Ollama seçildiyse Mistral kullandığından emin olalım
    if not config.USE_GEMINI_API:
        config.LLM_MODEL = "mistral:latest"
    
    print("\n" + "=" * 60)
    print(f"✅ Veri: {'📊 Canlı (YFinance)' if veri == 'C' else '🎲 Simüle'}")
    print(f"✅ Mod: {'📋 Test/Sanal' if islem == 'T' else 'ℹ️ Sinyal Modu'}")
    print(f"✅ AI Backend: {'☁️ Gemini' if config.USE_GEMINI_API else '🏠 Ollama (Mistral)'}")
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
    """Initialize all components"""
    logger.info("=" * 60)
    logger.info("🎯 SNIPER TRADING BOT - SİSTEM BAŞLATILIYOR")
    logger.info("=" * 60)
    logger.info(f"Başlangıç Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mod: {'📋 TEST MODU (Sadece Öneriler)' if config.DRY_RUN else '💰 CANLI İŞLEM'}")
    logger.info(f"LLM Model: {config.GEMINI_MODEL if config.USE_GEMINI_API else config.LLM_MODEL} {'(CLOUD)' if config.USE_GEMINI_API else '(LOCAL)'}")
    logger.info(f"İzlenen Varlıklar: {len(config.SYMBOLS)} adet")
    logger.info(f"Kontrol Aralığı: {config.CHECK_INTERVAL}s ({config.CHECK_INTERVAL/60:.1f} dakika)")
    logger.info(f"Min Güven: %{config.MIN_CONFIDENCE}")
    logger.info(f"Min Risk/Ödül: {config.MIN_RISK_REWARD_RATIO}:1")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📊 SKORLARIN ANLAMI - REHBERİNİZ:")
    logger.info("=" * 60)
    logger.info("")
    logger.info("🔹 TEKNİK SKOR (1. Aşama Filtresi):")
    logger.info("   • 0-100 arası değer alır")
    logger.info("   • RSI, MACD, Trend Analizi ve Hacim sinyallerinden oluşur")
    logger.info("   • RSI Sinyali: Max 30 puan (aşırı alım/satım bölgelerinde)")
    logger.info("   • MACD Sinyali: Max 25 puan (çapraz geçişlerde)")
    logger.info("   • Trend Uyumu: Max 30 puan (tüm zaman dilimleri aynı yönde)")
    logger.info("   • Hacim Doğrulaması: Max 15 puan (ortalamanın 1.5x üstünde)")
    logger.info(f"   • Geçiş Eşiği: {config.TECHNICAL_MIN_SCORE} puan")
    logger.info("   → Örnek: 75/100 = Çok güçlü teknik sinyal")
    logger.info("")
    logger.info("🔹 DUYGU SKORU (2. Aşama Filtresi):")
    logger.info("   • -100 ile +100 arası değer alır")
    logger.info("   • Haberlerin ortalama duygu analizi skorudur")
    logger.info("   • -100: Tamamen düşüş beklentisi (bearish)")
    logger.info("   • 0: Nötr (karışık haberler)")
    logger.info("   • +100: Tamamen yükseliş beklentisi (bullish)")
    logger.info("   • ALIM için: +50 veya üstü ideal")
    logger.info("   • SATIM için: -50 veya altı ideal")
    logger.info("   → Örnek: +70 = Güçlü pozitif haber akışı, ALIM desteklenir")
    logger.info("")
    logger.info("🔹 GÜVEN SEVİYESİ (3. Aşama - LLM Kararı):")
    logger.info("   • 0-100 arası değer alır")
    logger.info("   • Yapay zekanın işleme olan güven derecesi")
    logger.info(f"   • Minimum %{config.MIN_CONFIDENCE} gerekir (işlem yapılması için)")
    logger.info("   • 90-100: Çok yüksek güven (mükemmel setup)")
    logger.info("   • 80-89: Yüksek güven (iyi setup)")
    logger.info("   • 70-79: Orta güven (kabul edilebilir)")
    logger.info("   • 70 altı: Düşük güven (işlem yapılmaz)")
    logger.info("   → Örnek: %95 = Tüm sinyaller mükemmel uyumlu, yüksek başarı beklentisi")
    logger.info("")
    logger.info("=" * 60)
    logger.info("💡 İPUCU: İyi bir işlem için her üç skorun da yüksek olması önemlidir!")
    logger.info("=" * 60)
    
    # Initialize core components
    # broker = MT5Broker()
    broker = YFinanceBroker()
    if not broker.initialized:
        logger.error("❌ Broker başlatılamadı")
        return None
    
    data_fetcher = DataFetcher(broker)
    risk_manager = RiskManager(broker)
    
    # Stage 1 & 2 (No GPU)
    technical_filter = TechnicalFilter()
    news_filter = NewsFilter()
    
    # Economic Calendar (for future events)
    economic_calendar = EconomicCalendar()
    
    # Stage 3 (Lazy loading - only when needed)
    llm_engine = None  # Will initialize on first need
    
    logger.info("✅ Sistem başarıyla başlatıldı")
    logger.info("")
    
    return {
        "broker": broker,
        "data_fetcher": data_fetcher,
        "risk_manager": risk_manager,
        "technical_filter": technical_filter,
        "news_filter": news_filter,
        "economic_calendar": economic_calendar,
        "llm_engine": llm_engine
    }


def process_symbol(symbol, components):
    """
    Process a single symbol through the three-tier filter
    
    Args:
        symbol: Trading symbol
        components: Dict of initialized components
        
    Returns:
        True if trade executed, False otherwise
    """
    logger.info(f"\n{'#'*60}")
    logger.info(f"🚀 ANALYZING ASSET: {symbol}")
    logger.info(f"{'#'*60}")
    
    # Unpack components
    data_fetcher = components["data_fetcher"]
    technical_filter = components["technical_filter"]
    news_filter = components["news_filter"]
    economic_calendar = components["economic_calendar"]
    risk_manager = components["risk_manager"]
    broker = components["broker"]
    
    # ========================================
    # PRE-STAGE: ECONOMIC CALENDAR CHECK
    # ========================================
    upcoming_events = economic_calendar.get_upcoming_events(symbol=symbol)
    if upcoming_events:
        logger.info(f"📅 BEKLENEN ÖNEMLİ HABERLER ({len(upcoming_events)} adet):")
        for event in upcoming_events:
            etki = event.get('impact', 'MEDIUM').replace('HIGH', '🔴 YÜKSEK').replace('MEDIUM', '🟡 ORTA').replace('LOW', '🟢 DÜŞÜK')
            logger.info(f"  • {event.get('date')} | {event.get('title')} | Etki: {etki}")
        logger.info(f"{'-'*40}")
    else:
        logger.info("📅 Yakın zamanda önemli ekonomik haber bulunamadı.")
        logger.info(f"{'-'*40}")

    # ========================================
    # STAGE 1: TECHNICAL HARD FILTER
    # ========================================
    # Goal: Eliminate 90%+ of trades immediately
    # No GPU usage, fast execution (< 0.1 seconds)
    
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
    
    # Translate direction
    yon_tr = stage1_result['direction'].replace("BUY", "AL").replace("SELL", "SAT").replace("NEUTRAL", "NÖTR")
    
    logger.info(f"✅ {symbol} - 1. Aşama GEÇİLDİ (Puan: {stage1_result['score']}/100, Yön: {yon_tr})")
    
    
    # ========================================
    # STAGE 2: NEWS SENTIMENT FILTER
    # ========================================
    # Goal: Validate trade direction with fundamentals
    # SQL query only, still no GPU (< 0.5 seconds)
    
    trade_direction = stage1_result["direction"]
    
    stage2_result = news_filter.check_sentiment(
        symbol=symbol,
        direction=trade_direction,
        hours_lookback=config.NEWS_LOOKBACK_HOURS
    )
    
    if not stage2_result["pass"]:
        logger.info(f"❌ {symbol} - 2. Aşama BAŞARISIZ (Haber Filtresi): {stage2_result['reason']}")
        return False
    
    logger.info(f"✅ {symbol} - 2. Aşama GEÇİLDİ (Duygu Skoru: {stage2_result['sentiment_score']:.1f})")
    
    
    # ========================================
    # STAGE 3: LLM DECISION (SNIPER MODE)
    # ========================================
    # Goal: Final validation with strategy knowledge
    # NOW we load the LLM (2-5 seconds, GPU required)
    
    # Lazy load LLM (saves VRAM and startup time)
    if components["llm_engine"] is None:
        logger.info("🔧 Loading LLM Decision Engine for first time...")
        components["llm_engine"] = LLMDecisionEngine(
            model_name=config.LLM_MODEL,
            rag_data_path=config.RAG_DATA_PATH
        )
    
    llm_engine = components["llm_engine"]
    
    # Prepare context for LLM (upcoming_events already fetched at start)
    
    # Prepare context for LLM
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
    
    # Ask LLM: "Should I take this trade?"
    stage3_result = llm_engine.make_decision(context)
    
    if stage3_result["decision"] == "PASS":
        logger.info(f"❌ {symbol} - 3. Aşama REDDEDİLDİ: {stage3_result['reasoning']}")
        return False
    
    if stage3_result["confidence"] < config.MIN_CONFIDENCE:
        logger.info(f"❌ {symbol} - Düşük güven seviyesi ({stage3_result['confidence']}% < {config.MIN_CONFIDENCE}%)")
        return False
    
    logger.info("=" * 60)
    logger.info(f"🎯 SNIPER MODU AKTİF - {symbol}")
    logger.info(f"   Karar: {stage3_result['decision']}")
    logger.info(f"   Güven: {stage3_result['confidence']}%")
    logger.info(f"   Mantık: {stage3_result['reasoning']}")
    logger.info("=" * 60)
    
    
    # ========================================
    # RISK MANAGEMENT & VALIDATION
    # ========================================
    
    # Check position limits
    position_check = risk_manager.check_position_limits()
    if not position_check["allowed"]:
        logger.warning(f"⚠️ {symbol} - {position_check['reason']}")
        return False
    
    # Validate risk/reward ratio (with auto-fallback for missing SL/TP)
    # If entry_price is missing (0.0), use current price
    llm_entry = float(stage3_result.get("entry_price", 0))
    entry_to_use = llm_entry if llm_entry > 0 else float(market_data["current_price"])
    
    trade_validation = risk_manager.validate_trade(
        entry_price=entry_to_use,
        stop_loss=stage3_result["stop_loss"],
        take_profit=stage3_result["take_profit"],
        decision=stage3_result["decision"]
    )
    
    if not trade_validation["valid"]:
        logger.warning(f"❌ {symbol} - {trade_validation['reason']}")
        return False
    
    # Update prices with potential fallbacks from risk_manager
    sl = float(trade_validation["sl"])
    tp = float(trade_validation["tp"])
    entry = entry_to_use
    
    # Calculate position size
    position_size = risk_manager.calculate_position_size(
        symbol=symbol,
        entry_price=entry,
        stop_loss=sl,
        risk_percent=config.RISK_PERCENT
    )
    
    
    # ========================================
    # EXECUTE TRADE (OR SHOW RECOMMENDATION)
    # ========================================
    
    # Calculate pip difference for TP and SL
    try:
        # Determine pip multiplier (forex vs stocks/indices)
        if "=X" in symbol:  # Forex
            pip_multiplier = 10000 if "JPY" not in symbol else 100
        else:
            pip_multiplier = 1  # For indices, stocks, crypto
        
        sl_distance = abs(entry - sl) * pip_multiplier
        tp_distance = abs(tp - entry) * pip_multiplier
    except Exception as e:
        logger.error(f"❌ Mesafe hesaplama hatası: {e}")
        sl_distance = 0
        tp_distance = 0
    
    logger.info("=" * 60)
    logger.info("🎯 TİCARET SİNYALİ")
    logger.info("=" * 60)
    logger.info(f"📊 Varlık: {symbol}")
    logger.info(f"")
    logger.info(f"📍 Yön: {stage3_result['decision'].replace('BUY', '🟢 ALIM (AL)').replace('SELL', '🔴 SATIM (SAT)')}")
    logger.info(f"💰 Giriş Fiyatı: {entry:.5f}")
    logger.info(f"🛑 Zarar Kes (SL): {sl:.5f} ({sl_distance:.1f} pip uzakta)")
    logger.info(f"🎯 Kar Al (TP): {tp:.5f} ({tp_distance:.1f} pip uzakta)")
    logger.info(f"")
    logger.info(f"📦 Pozisyon Büyüklüğü: {position_size} lot")
    logger.info(f"⚖️ Risk/Ödül Oranı: {trade_validation['rr_ratio']:.2f}:1")
    logger.info(f"✅ Güven Seviyesi: %{stage3_result['confidence']}")
    logger.info(f"⚠️ Risk Skoru: {stage3_result.get('risk_score', 'N/A')}/100")
    logger.info(f"⏳ Beklenen Süre: {stage3_result.get('expected_duration', 'Belirtilmedi')}")
    logger.info(f"")
    logger.info(f"💡 NEDEN: {stage3_result['reasoning']}")
    logger.info("=" * 60)
    
    # Check if dry run mode
    if config.DRY_RUN:
        logger.info("📋 TEST MODU - İşlem uygulanmadı (sadece öneri)")
        logger.info("   Gerçek işlem için config.py'de DRY_RUN = False yapın")
        logger.info("=" * 60)
        return True  # Return True to indicate recommendation was generated
    
    # Execute real trade
    logger.info("💰 Gerçek işlem uygulanıyor...")
    
    order = broker.place_order(
        symbol=symbol,
        action=stage3_result["decision"],
        volume=position_size,
        entry=None,  # Market order
        sl=sl,
        tp=tp,
        comment=f"Sniper-{stage3_result['confidence']}%"
    )
    
    if order["success"]:
        logger.info(f"✅ EMİR UYGULANDIR: Ticket #{order['ticket']}")
        logger.info(f"   Fiyat: {order['price']}")
        logger.info(f"   Hacim: {order['volume']} lot")
        logger.info("=" * 60)
        return True
    else:
        logger.error(f"❌ EMİR BAŞARISIZ: {order['error']}")
        logger.info("=" * 60)
        return False


from update_news import update_news

def main():
    """Main trading loop"""
    # Mode selection
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Auto-configure for Test Mode + Yahoo Finance
        config.DEMO_MODE = False
        config.DRY_RUN = True
        logger.info("🤖 Otomatik Başlatma: Yahoo Finance + Test Modu")
    else:
        select_mode()
    
    # Initialize system
    components = initialize_system()
    
    if components is None:
        logger.error("❌ Sistem başlatma başarısız")
        return
    
    # Main loop
    try:
        while True:
            loop_start = time.time()
            
            logger.info("")
            logger.info(f"⏰ Tarama başlatıldı: {datetime.now().strftime('%H:%M:%S')}")
            
            # Update News from External APIs
            try:
                logger.info("🌍 Dış kaynaktan (API) haberler güncelleniyor...")
                update_news()
            except Exception as e:
                logger.error(f"⚠️ Haber güncelleme hatası: {str(e)}")

            # Process each symbol
            for symbol in config.SYMBOLS:
                try:
                    process_symbol(symbol, components)
                    
                    import gc
                    gc.collect()  # Force garbage collection to free VRAM/RAM
                    
                    # Delay between assets (User Request)
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"❌ Error processing {symbol}: {str(e)}")
            
            # Wait before next scan
            loop_duration = time.time() - loop_start
            wait_time = max(0, config.CHECK_INTERVAL - loop_duration)
            
            logger.info("")
            logger.info(f"⏳ Sonraki tarama {wait_time:.0f} saniye sonra... (Durdurmak için Ctrl+C)")
            logger.info("")
            
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🛑 SNIPER BOT KULLANICI TARAFINDAN DURDURULDU")
        logger.info("=" * 60)
        components["broker"].close()
    
    except Exception as e:
        logger.error(f"❌ Ana döngüde kritik hata: {str(e)}")
        components["broker"].close()


if __name__ == "__main__":
    main()
