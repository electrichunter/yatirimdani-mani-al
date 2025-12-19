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
import json
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

# Global counter for consecutive zero-confidence LLM results per symbol
ZERO_CONF_COUNTERS = {}
# Global counter for analysis runs per symbol (to tag saved analyses)
ANALYSIS_COUNTERS = {}
LAST_SAVED_DECISIONS = {}

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

    # 4. Zaman Dilimi Seçimi
    print("\n4. Zaman Dilimi Seçin:")
    print("  [1] 1 Saatlik (H1)")
    print("  [4] 4 Saatlik (H4)")
    print("  [D] Günlük (D1)")
    print("  [W] Haftalık (W1)")
    
    while True:
        tf_choice = input("\nZaman dilimi (1/4/D/W): ").strip().upper()
        if tf_choice == '1':
            config.SELECTED_TIMEFRAME = "H1"
            break
        elif tf_choice == '4':
            config.SELECTED_TIMEFRAME = "H4"
            break
        elif tf_choice == 'D':
            config.SELECTED_TIMEFRAME = "D1"
            break
        elif tf_choice == 'W':
            config.SELECTED_TIMEFRAME = "W1"
            break
        print("❌ Lütfen geçerli bir seçim yapın!")
    
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
    print(f"✅ Zaman Dilimi: {config.SELECTED_TIMEFRAME}")
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


# --- Simulated trades helpers (for DRY_RUN / suggestion-only mode) ---
SIM_TRADES_FILE = os.path.join('data', 'simulated_trades.json')

def load_simulated_trades():
    try:
        if os.path.exists(SIM_TRADES_FILE):
            with open(SIM_TRADES_FILE, 'r', encoding='utf-8') as sf:
                return json.load(sf)
    except Exception:
        pass
    return []


def save_result_if_changed(symbol, data, archive=True):
    """Save result to web only if the decision changed since last saved for this symbol."""
    try:
        decision = data.get('decision') if isinstance(data, dict) else None
        if decision is None:
            ui.save_result_for_web(symbol, data, archive=archive)
            return
        last = LAST_SAVED_DECISIONS.get(symbol)
        if last == decision:
            return
        LAST_SAVED_DECISIONS[symbol] = decision
        ui.save_result_for_web(symbol, data, archive=archive)
    except Exception:
        try:
            ui.save_result_for_web(symbol, data, archive=archive)
        except Exception:
            pass

def save_simulated_trades(trades):
    try:
        os.makedirs(os.path.dirname(SIM_TRADES_FILE), exist_ok=True)
        with open(SIM_TRADES_FILE, 'w', encoding='utf-8') as sf:
            json.dump(trades, sf, ensure_ascii=False, indent=2)
    except Exception:
        pass

def add_simulated_trade(trade):
    trades = load_simulated_trades()
    trades.append(trade)
    save_simulated_trades(trades)

def update_simulated_trades(components):
    """Refresh current prices for simulated trades and compute unrealized P/L."""
    trades = load_simulated_trades()
    updated = False
    for t in trades:
        try:
            p = components['data_fetcher'].get_current_price(t.get('symbol'))
            price = None
            if isinstance(p, dict):
                price = p.get('mid') or p.get('price')
            else:
                try:
                    price = float(p)
                except Exception:
                    price = None

            if price is None:
                continue

            t['current_price'] = price

            # Ensure notional exists (fallback)
            if t.get('notional_usd') is None:
                try:
                    t['notional_usd'] = round((t.get('lot', 0) or 0) * 100000 * (t.get('entry_price') or price), 2)
                except Exception:
                    t['notional_usd'] = None

            # Compute unrealized USD and percent (BUY positive, SELL inverted)
            if t.get('entry_price'):
                try:
                    change = (price - float(t['entry_price'])) / float(t['entry_price'])
                    if t.get('direction', '').upper() == 'SELL':
                        change = -change
                    notional = float(t.get('notional_usd') or 0)
                    t['unrealized_usd'] = round(change * notional, 2)
                    t['unrealized_pct'] = round(change * 100, 4)
                except Exception:
                    t['unrealized_usd'] = 0.0
                    t['unrealized_pct'] = 0.0

            updated = True
        except Exception:
            continue

    if updated:
        save_simulated_trades(trades)
    return trades

def simulated_trades_summary():
    trades = load_simulated_trades()
    total_unreal = sum((t.get('unrealized_usd') or 0) for t in trades if t.get('status') == 'OPEN')
    total_notional = sum((t.get('notional_usd') or 0) for t in trades if t.get('status') == 'OPEN')
    total_realized = sum((t.get('realized_usd') or 0) for t in trades if t.get('status') == 'CLOSED')
    pct = (total_unreal / total_notional * 100) if total_notional else 0.0
    return {
        'count_open': sum(1 for t in trades if t.get('status') == 'OPEN'),
        'count_closed': sum(1 for t in trades if t.get('status') == 'CLOSED'),
        'total_unrealized_usd': round(total_unreal,2),
        'total_notional_usd': round(total_notional,2),
        'total_realized_usd': round(total_realized,2),
        'total_unrealized_pct': round(pct,4)
    }


def pip_multiplier(symbol: str):
    try:
        if "=X" in symbol:
            return 10000 if "JPY" not in symbol else 100
        if "GC=F" in symbol or "XAU" in symbol:
            return 10
        if "SI=F" in symbol or "XAG" in symbol:
            return 100
    except Exception:
        pass
    return 1


def compute_notional(symbol, lot, price):
    try:
        if price is None:
            return None
        # Forex lot convention: 1 lot = 100,000 units
        if "=X" in symbol or any(x in symbol for x in ["EUR", "USD", "JPY", "GBP", "AUD", "NZD", "CAD"]):
            return round(lot * 100000 * float(price), 2)
        # Otherwise treat lot as number of shares/contracts
        return round(lot * float(price), 2)
    except Exception:
        return None


def open_simulated_trade_from_spec(spec, components):
    """Spec is a dict with keys: symbol, direction, lot, optional entry, sl, tp, leverage"""
    try:
        symbol = spec.get('symbol')
        direction = (spec.get('direction') or 'BUY').upper()
        lot = float(spec.get('lot') or spec.get('volume') or getattr(config, 'MIN_DISPLAY_LOT', 0.01))
        entry = spec.get('entry')
        # If entry price not provided, fetch current
        if entry is None and components is not None:
            try:
                p = components['data_fetcher'].get_current_price(symbol)
                if isinstance(p, dict):
                    entry = p.get('mid') or p.get('price')
                else:
                    entry = float(p)
            except Exception:
                entry = None

        sl = spec.get('stop_loss')
        tp = spec.get('take_profit')
        leverage = float(spec.get('leverage', getattr(config, 'LEVERAGE', 30)))

        notional = compute_notional(symbol, lot, entry)
        margin = round((notional or 0) / leverage, 2) if leverage else None

        trade = {
            'id': spec.get('id') or f"sim-{int(time.time()*1000)}",
            'symbol': symbol,
            'direction': direction,
            'lot': lot,
            'entry_price': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'leverage': leverage,
            'margin_required': margin,
            'notional_usd': notional,
            'opened_at': datetime.now().isoformat(),
            'status': 'OPEN',
            'current_price': entry,
            'unrealized_usd': 0.0,
            'unrealized_pct': 0.0,
            'realized_usd': 0.0
        }
        add_simulated_trade(trade)
        return trade
    except Exception as e:
        logger.error(f"open_simulated_trade failed: {e}")
        return None


def close_simulated_trade_by_spec(spec, components):
    # spec may have 'id' or 'symbol' and optional 'close_price'
    try:
        trades = load_simulated_trades()
        changed = False
        for t in trades:
            if t.get('status') != 'OPEN':
                continue
            match = False
            if spec.get('id') and spec.get('id') == t.get('id'):
                match = True
            elif spec.get('symbol') and spec.get('symbol') == t.get('symbol'):
                match = True
            if not match:
                continue

            close_price = spec.get('close_price')
            if close_price is None and components is not None:
                try:
                    p = components['data_fetcher'].get_current_price(t.get('symbol'))
                    close_price = p.get('mid') if isinstance(p, dict) else float(p)
                except Exception:
                    close_price = None

            if close_price is None:
                continue

            # compute realized
            try:
                entry = float(t.get('entry_price') or 0)
                notional = float(t.get('notional_usd') or 0)
                change = (float(close_price) - entry) / entry if entry else 0
                if t.get('direction', '').upper() == 'SELL':
                    change = -change
                realized = round(change * notional, 2)
            except Exception:
                realized = 0.0

            t['status'] = 'CLOSED'
            t['closed_at'] = datetime.now().isoformat()
            t['close_price'] = close_price
            t['realized_usd'] = realized
            t['unrealized_usd'] = 0.0
            t['unrealized_pct'] = 0.0
            changed = True

        if changed:
            save_simulated_trades(trades)
        return changed
    except Exception as e:
        logger.error(f"close_simulated_trade failed: {e}")
        return False


def watch_manual_trade_files(components):
    """If files `data/open_trade.json` or `data/close_trade.json` exist, process and remove them."""
    try:
        open_path = os.path.join('data', 'open_trade.json')
        if os.path.exists(open_path):
            try:
                with open(open_path, 'r', encoding='utf-8') as of:
                    spec = json.load(of)
                # support list or single
                if isinstance(spec, list):
                    for s in spec:
                        t = open_simulated_trade_from_spec(s, components)
                        if t:
                            logger.info(f"🔁 Manuel sim trade açıldı: {t.get('id')} {t.get('symbol')} {t.get('direction')} {t.get('lot')}")
                elif isinstance(spec, dict):
                    t = open_simulated_trade_from_spec(spec, components)
                    if t:
                        logger.info(f"🔁 Manuel sim trade açıldı: {t.get('id')} {t.get('symbol')} {t.get('direction')} {t.get('lot')}")
            except Exception as e:
                logger.error(f"open_trade.json işlenirken hata: {e}")
            try:
                os.remove(open_path)
            except Exception:
                pass

        close_path = os.path.join('data', 'close_trade.json')
        if os.path.exists(close_path):
            try:
                with open(close_path, 'r', encoding='utf-8') as cf:
                    spec = json.load(cf)
                if isinstance(spec, list):
                    for s in spec:
                        if close_simulated_trade_by_spec(s, components):
                            logger.info(f"🔁 Manuel sim trade kapatıldı (list) {s}")
                elif isinstance(spec, dict):
                    if close_simulated_trade_by_spec(spec, components):
                        logger.info(f"🔁 Manuel sim trade kapatıldı {spec}")
            except Exception as e:
                logger.error(f"close_trade.json işlenirken hata: {e}")
            try:
                os.remove(close_path)
            except Exception:
                pass
    except Exception:
        pass

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
    
    # Açık pozisyon kontrolü - AYNI SEMBOLDE İŞLEM VAR MI?
    open_positions = broker.get_open_positions()
    for pos in open_positions:
        if pos.get('symbol') == symbol:
            logger.info(f"ℹ️ {symbol} - Zaten açık bir pozisyon var, analiz atlanıyor.")
            return False

    # LLM için gelecek olayları hazırla
    upcoming_events = economic_calendar.get_upcoming_events(symbol=symbol)

    # ========================================
    # 1. AŞAMA: TEKNİK SERT FİLTRE
    # ========================================
    # Hedef: İşlemlerin %90'ından fazlasını anında elemek
    # Hızlı çalışma (< 0.1 saniye), GPU kullanmaz
    
    market_data = data_fetcher.get_multi_timeframe_data(
        symbol=symbol,
        timeframes=[config.SELECTED_TIMEFRAME]
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

    # Kaydet: her LLM analizi hemen web'e kaydedilsin (intermediate)
    try:
        ANALYSIS_COUNTERS[symbol] = ANALYSIS_COUNTERS.get(symbol, 0) + 1
        analysis_meta = {
            "analysis_index": ANALYSIS_COUNTERS[symbol],
            "analysis_type": "llm",
            "analysis_ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "intermediate": True
        }
        temp_save = dict(stage3_result)
        # ensure entry price present for display
        temp_save.setdefault('entry_price', float(market_data.get('current_price', 0) or 0))
        temp_save.update(analysis_meta)
        ui.save_result_for_web(symbol, temp_save, archive=True)
    except Exception:
        pass

    # Eğer 0 güven döndüyse sayacı arttır, aksi halde sıfırla
    try:
        if float(stage3_result.get('confidence', 0)) == 0:
            ZERO_CONF_COUNTERS[symbol] = ZERO_CONF_COUNTERS.get(symbol, 0) + 1
        else:
            ZERO_CONF_COUNTERS[symbol] = 0
    except Exception:
        ZERO_CONF_COUNTERS[symbol] = 0

    # Eğer art arda 5 kez 0 geldiyse LLM kendi kapsamlı analizini yapıp force_publish ile döner
    if ZERO_CONF_COUNTERS.get(symbol, 0) >= 5:
        logger.info(f"⚠️ {symbol} için 5 kez art arda 0 güven bulundu — LLM self_assess tetikleniyor")
        self_assess = llm_engine.self_assess(context)
        if self_assess:
            self_assess['force_publish'] = True
            stage3_result = self_assess
            logger.info(f"ℹ️ {symbol} - LLM self-assess sonucu: {stage3_result.get('decision')} (%{stage3_result.get('confidence',0)})")
            # Save self-assess analysis to web results as well
            try:
                ANALYSIS_COUNTERS[symbol] = ANALYSIS_COUNTERS.get(symbol, 0) + 1
                analysis_meta = {
                    "analysis_index": ANALYSIS_COUNTERS[symbol],
                    "analysis_type": "self_assess",
                    "analysis_ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "intermediate": True,
                    "force_publish": True
                }
                temp_save = dict(stage3_result)
                temp_save.setdefault('entry_price', float(market_data.get('current_price', 0) or 0))
                temp_save.update(analysis_meta)
                ui.save_result_for_web(symbol, temp_save, archive=True)
            except Exception:
                pass
        ZERO_CONF_COUNTERS[symbol] = 0
    
    if stage3_result["decision"] == "PASS":
        logger.info(f"❌ {symbol} - 3. Aşama REDDEDİLDİ: {stage3_result['reasoning']}")
        return False
    
    # Eğer LLM düşük güven verirse, belirlenen sayıda yeniden dene (force_publish varsa atla).
    if stage3_result.get("confidence", 0) < config.MIN_CONFIDENCE and not stage3_result.get('force_publish', False):
        logger.info(f"❌ {symbol} - İlk karar düşük güven seviyesi ({stage3_result['confidence']}% < {config.MIN_CONFIDENCE}%). Yeniden denenecek...")

        retry_count = 0
        improved = False
        last_result = stage3_result

        while retry_count < getattr(config, 'MAX_CONFIDENCE_RETRIES', 5):
            retry_count += 1
            try:
                time.sleep(getattr(config, 'CONFIDENCE_RETRY_DELAY', 5))
                # Güncel bağlam için fiyatı güncelle
                market_data = data_fetcher.get_multi_timeframe_data(
                    symbol=symbol,
                    timeframes=list(config.TIMEFRAMES.keys())
                )
                context["current_price"] = market_data.get("current_price", context.get("current_price"))

                # Yeni karar al
                last_result = llm_engine.make_decision(context)
                logger.info(f"🔁 {symbol} - Yeniden deneme {retry_count}: Güven %{last_result.get('confidence',0)}")
                # Save this retry analysis to web results (sadece log'a yazalım, web'i kirletmeyelim)
                try:
                    logger.debug(f"🔁 {symbol} - Yeniden deneme {retry_count} kaydedildi (internal)")
                except Exception:
                    pass

                if last_result.get("confidence", 0) >= config.MIN_CONFIDENCE:
                    improved = True
                    stage3_result = last_result
                    logger.info(f"✅ {symbol} - Güven arttı: %{stage3_result['confidence']}")
                    break
            except Exception as e:
                logger.error(f"⚠️ {symbol} - Güven yeniden deneme hatası: {e}")

        if not improved:
            # 5 denemeden sonra da artmadıysa düşük güven olarak işaretle ve web'e kaydet
            logger.info(f"❌ {symbol} - Düşük güven seviyesi devam ediyor ({last_result.get('confidence',0)}%). Web'de 'düşük güven' olarak işaretlenecek.")
            signal_info = {
                "decision": f"DÜŞÜK GÜVEN ({last_result.get('confidence',0)}%)",
                "confidence": last_result.get('confidence', 0),
                "reasoning": last_result.get('reasoning', 'Gerekçe yok'),
                "entry_price": float(market_data.get('current_price', 0)),
                "stop_loss": None,
                "take_profit": None,
                "timeframe": last_result.get('timeframe', 'H1'),
                "expected_duration": last_result.get('expected_duration', 'Bilinmiyor'),
                "rr_ratio": None,
                "low_confidence": True
            }
            ui.save_result_for_web(symbol, signal_info)
            return False
    elif stage3_result.get('force_publish', False):
        logger.info(f"ℹ️ {symbol} - Force publish izni verildi; düşük güven yinede işleme alınacak.")
    
    # Karar BUY veya SELL değilse (BEKLEMEDE KAL vb.) işlemi burada durdur
    if stage3_result["decision"] not in ["BUY", "SELL"]:
        logger.info(f"⏸️ {symbol} - Karar: {stage3_result['decision']} (İşlem açılmıyor)")
        # Sinyal bilgisini yine de dashboard'a gönderelim ki kullanıcı görsün ama "Açık İşlemler"e girmesin
        signal_info = {
            "decision": stage3_result["decision"],
            "confidence": stage3_result["confidence"],
            "reasoning": stage3_result["reasoning"],
            "entry_price": float(market_data["current_price"]),
            "stop_loss": None,
            "take_profit": None,
            "timeframe": stage3_result.get("timeframe", "H1"),
            "expected_duration": stage3_result.get("expected_duration", "Bilinmiyor"),
            "rr_ratio": 0
        }
        ui.save_result_for_web(symbol, signal_info)
        return False

    # ========================================
    # RİSK YÖNETİMİ & DOĞRULAMA
    # ========================================
    
    # Boştaki bakiyeyi hesapla (User Request: 10% of available)
    def get_notional(sym, pos_size, price):
        # Forex için basitleştirilmiş notional (USD cinsinden)
        contract_size = 100000
        if sym.startswith("USD"): # USDJPY, USDCAD vb. (Base is USD)
            return pos_size * contract_size
        else: # EURUSD, GBPUSD, XAUUSD vb. (Base is not USD)
            return pos_size * contract_size * price

    def get_available_balance():
        total = float(getattr(config, 'VIRTUAL_BALANCE', 100.0))
        if not config.DRY_RUN:
            try:
                total = broker.get_balance()
            except Exception:
                pass
        
        used = 0.0
        try:
            pending = components["llm_engine"].learning_system.get_pending_trades()
            for t in pending:
                # Margin calculation (1:100 leverage assumed)
                t_notional = get_notional(t.get('symbol', ''), float(t.get('position_size', 0.01)), float(t.get('entry_price', 1.0)))
                used += t_notional / 100.0
        except Exception:
            pass
        return max(0.0, total - used)

    free_balance = get_available_balance()
    current_notional = get_notional(symbol, 0.01, float(market_data["current_price"])) # Min lot notional
    required_margin = current_notional / 100.0 # 1:100 kaldıraç varsayımı
    
    logger.info(f"💰 Boştaki Bakiye: ${free_balance:.2f} (Toplam: ${getattr(config, 'VIRTUAL_BALANCE', 100.0)})")
    
    if free_balance < required_margin:
        logger.warning(f"❌ {symbol} - Yetersiz Bakiye! Gerekli Margin: ${required_margin:.2f}, Mevcut: ${free_balance:.2f}")
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
    
    # Fiyatları doğrulanmış değerlerle güncelle (Eksikse AI yerine biz veriyoruz)
    entry = entry_to_use
    sl = float(trade_validation["sl"])
    tp = float(trade_validation["tp"])

    # stage3_result'ı güncelle ki loglara doğru gitsin
    stage3_result["entry_price"] = entry
    stage3_result["stop_loss"] = sl
    stage3_result["take_profit"] = tp
    
    if not trade_validation["valid"]:
        logger.warning(f"⚠️ {symbol} - {trade_validation['reason']} -> ⏸️ BEKLEMEDE KAL (Risk/Ödül Uygun Değil)")
        # Sinyali dashboard'a "BEKLE" olarak gönder
        signal_info = {
            "decision": "BEKLE (Düşük R:R)",
            "confidence": stage3_result["confidence"],
            "reasoning": f"Teknik olarak uygun ancak Risk/Ödül oranı ({trade_validation['rr_ratio']}) düşük. " + stage3_result.get("reasoning", ""),
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "timeframe": stage3_result.get("timeframe", "H1"),
            "expected_duration": stage3_result.get("expected_duration", "Bilinmiyor"),
            "rr_ratio": trade_validation['rr_ratio']
        }
        ui.save_result_for_web(symbol, signal_info)
        return False
    
    # Pozisyon büyüklüğünü hesapla (Boştaki bakiye üzerinden %10 risk)
    position_size = risk_manager.calculate_position_size(
        symbol=symbol,
        entry_price=entry,
        stop_loss=sl,
        risk_percent=config.RISK_PERCENT,
        balance_override=free_balance
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
    signal_info = {
        "decision": stage3_result["decision"],
        "confidence": stage3_result["confidence"],
        "reasoning": stage3_result["reasoning"],
        "entry_price": entry,
        "stop_loss": sl,
        "take_profit": tp,
        "timeframe": stage3_result.get("timeframe", "H1"),
        "expected_duration": stage3_result.get("expected_duration", "Bilinmiyor"),
        "rr_ratio": trade_validation['rr_ratio']
    }
    
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
                position_size=position_size,
                dry_run=config.DRY_RUN
            )
        except Exception as e:
            logger.error(f"⚠️ Öğrenme sistemi kayıt hatası: {e}")

    # Test modu kontrolü — DRY_RUN: işlemleri gerçek olarak açma; sadece öneri
    if config.DRY_RUN:
        # In DRY_RUN we collect signals and create a position plan later.
        return True
    
    # Gerçek işlemi gerçekleştir
    logger.info("💰 Gerçek işlem uygulanıyor...")
    # Re-entry cooldown kontrolü: aynı fiyata yakın tekrar açılmasını engelle
    try:
        if "llm_engine" in components and components["llm_engine"] is not None:
            allowed, reason = components["llm_engine"].learning_system.is_entry_allowed(symbol, entry)
            if not allowed:
                logger.info(f"❌ Yeni işlem engellendi: {reason}")
                # Kaydı güncelle: trade history'de PENDING yerine SKIPPED (veya benzeri)
                try:
                    # If we have just logged the trade, mark it as SKIPPED
                    # Find the most recent PENDING trade for this symbol and entry and mark as SKIPPED
                    pending = components["llm_engine"].learning_system.get_pending_trades()
                    for t in pending:
                        if t.get('symbol') == symbol and abs((t.get('entry_price') or 0) - (entry or 0)) <= getattr(config, 'REENTRY_PRICE_TOLERANCE', 0.001):
                            components["llm_engine"].learning_system.update_trade_outcome(t['id'], 'BREAKEVEN', profit_pips=0, profit_amount=0, close_price=entry)
                            break
                except Exception:
                    pass
                return False
    except Exception as e:
        logger.error(f"Cooldown kontrolünde hata: {e}")

    # Duplicate pending check: aynı symbol/direction ve yakın giriş fiyatı varsa tekrar açma
    try:
        if "llm_engine" in components and components["llm_engine"] is not None:
            pending = components["llm_engine"].learning_system.get_pending_trades()
            for t in pending:
                try:
                    if t.get('symbol') == symbol and t.get('direction') == stage3_result["decision"]:
                        existing_entry = t.get('entry_price') or 0
                        tol = getattr(config, 'REENTRY_PRICE_TOLERANCE', 0.001)
                        if abs((existing_entry or 0) - (entry or 0)) <= tol:
                            logger.info(f"❌ Aynı pozisyon zaten açık/pending: {symbol} {stage3_result['decision']} yakın fiyat {existing_entry}. Yeni emir atılmayacak.")
                            return False
                except Exception:
                    continue
    except Exception as e:
        logger.error(f"Duplicate pending kontrol hatası: {e}")

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
    
    # Dashboard'u arka planda başlat (konfigürasyonla kontrol edilir)
    if getattr(config, 'START_DASHBOARD', True):
        logger.info("🌐 Dashboard başlatılıyor...")
        threading.Thread(target=run_dashboard_server, daemon=True).start()
        time.sleep(2) # Sunucunun kalkması için kısa bir süre bekle
        try:
            webbrowser.open("http://localhost:8000/dashboard.html")
        except Exception:
            pass
    else:
        logger.info("ℹ️ Dashboard otomatik başlatma devre dışı (config.START_DASHBOARD=False)")

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

            # Update simulated trades as early as possible each loop
            try:
                if components is not None:
                    updated_trades = update_simulated_trades(components)
                    # push a short summary to web/dashboard
                    try:
                        summary = simulated_trades_summary()
                        ui.save_result_for_web('SIMULATED_TRADES_SUMMARY', summary)
                    except Exception:
                        pass
            except Exception:
                pass
            
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
            # Read monitoring state (pause/resume) from disk
            try:
                ms_path = os.path.join(os.getcwd(), 'data', 'monitoring_state.json')
                monitoring_state = { 'paused': False }
                if os.path.exists(ms_path):
                    with open(ms_path, 'r', encoding='utf-8') as mf:
                        monitoring_state = json.load(mf)
            except Exception:
                monitoring_state = { 'paused': False }

            # If monitoring paused, skip pending trade checks
            if monitoring_state.get('paused'):
                logger.debug("⏸️ Monitoring paused — bekleyen işlemler denetlenmiyor.")
            else:
                # If we just resumed (resumed_at present), run reconciliation
                try:
                    if "resumed_at" in monitoring_state:
                        logger.info("🔁 Monitoring resumed — reconcile başlatılıyor...")
                        if "llm_engine" in components and components["llm_engine"] is not None:
                            try:
                                # Provide a price getter that returns float current price or None
                                def _price_getter(sym):
                                    try:
                                        p = data_fetcher.get_current_price(sym)
                                        if isinstance(p, dict):
                                            return p.get('mid')
                                        return float(p)
                                    except Exception:
                                        return None
                                components["llm_engine"].learning_system.reconcile_pending_trades_on_resume(_price_getter)
                            except Exception as e:
                                logger.error(f"Reconcile hatası: {e}")
                        # Remove resumed_at so reconciliation runs only once
                        try:
                            os.remove(ms_path)
                        except Exception:
                            pass

                except Exception as e:
                    logger.error(f"Monitoring resume kontrol hatası: {e}")

                if "llm_engine" in components and components["llm_engine"] is not None:
                    try:
                        pending_trades = components["llm_engine"].learning_system.get_pending_trades()
                        if pending_trades:
                            logger.info(f"🔍 {len(pending_trades)} adet bekleyen işlem denetleniyor...")
                        for trade in pending_trades:
                            # Güncel fiyatı al (DataFetcher üzerinden, daha güvenli)
                            price_info = data_fetcher.get_current_price(trade["symbol"])
                            if price_info is None: continue

                            price = price_info.get("mid") if isinstance(price_info, dict) else None
                            if price is None:
                                # Eğer dict değilse, belki broker doğrudan fiyat döndü
                                try:
                                    price = float(price_info)
                                except Exception:
                                    continue
                            
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
                                
                                # SYNC: simulated_trades.json'daki kaydı da kapat
                                try:
                                    close_simulated_trade_by_spec({
                                        'symbol': trade["symbol"],
                                        'close_price': price
                                    }, components)
                                except Exception:
                                    pass
                            else:
                                # Eğer 2 günden uzun süredir açık kaldıysa LLM'e sorup zorunlu kapatma uygula
                                try:
                                    from datetime import datetime as _dt
                                    age = _dt.now() - _dt.fromisoformat(trade["timestamp"]) if isinstance(trade.get("timestamp"), str) else None
                                except Exception:
                                    age = None
                                close_after_days = getattr(config, 'CLOSE_PENDING_AFTER_DAYS', 2)
                                if age is not None and age.total_seconds() >= close_after_days * 86400:
                                    logger.info(f"⏳ Trade ID {trade['id']} açık {age.days} gün; LLM'e kapatma kararı soruluyor...")
                                    try:
                                        decision = components["llm_engine"].self_assess({"symbol": trade["symbol"], "entry_price": trade["entry_price"], "current_price": price, "direction": trade["direction"], "context": trade})
                                        # Expect decision like {'action': 'CLOSE'|'KEEP', 'reason': '...'}
                                        if isinstance(decision, dict) and decision.get('action') == 'CLOSE':
                                            # Force close and add cooldown
                                            components["llm_engine"].learning_system.force_close_trade(trade["id"], close_price=price, reason='LLM_FORCED_CLOSE')
                                            
                                            # SYNC: simulated_trades.json'daki kaydı da kapat
                                            try:
                                                close_simulated_trade_by_spec({
                                                    'symbol': trade["symbol"],
                                                    'close_price': price
                                                }, components)
                                            except Exception:
                                                pass
                                            # Add re-entry cooldown
                                            try:
                                                cooldown_hours = getattr(config, 'REENTRY_COOLDOWN_HOURS', 5)
                                                tol = getattr(config, 'REENTRY_PRICE_TOLERANCE', 0.001)
                                                components["llm_engine"].learning_system.add_entry_cooldown(trade["symbol"], price, cooldown_hours, tol)
                                            except Exception as _e:
                                                logger.error(f"Cooldown eklenemedi: {_e}")
                                    except Exception as e:
                                        logger.error(f"LLM self-assess hatası: {e}")
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

            # Pass-based scanning: tüm sembolleri baştan sona birkaç kez tara,
            # sonra bekle (kullanıcı isteğine göre 3 pass ve 5 dk bekleme)
            runs = getattr(config, 'LLM_PASS_RUNS', 3)
            post_wait = getattr(config, 'LLM_PASS_WAIT_SECONDS', 300)

            for run_idx in range(runs):
                logger.info(f"🔁 LLM Pass {run_idx+1}/{runs} başlatılıyor...")
                for symbol in config.SYMBOLS:
                    try:
                        process_symbol(symbol, components)

                        import gc
                        gc.collect()

                        # Küçük aralık, ama aynı sembolün arka arkaya işlenmesini engeller
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"❌ {symbol} işlenirken hata: {str(e)}")
            
            # After each pass, compute a position plan (allocation) based on latest signals
            try:
                plan = []

                # load latest web results (if any)
                wr_path = os.path.join('data', 'web_results.json')
                if os.path.exists(wr_path):
                    try:
                        with open(wr_path, 'r', encoding='utf-8') as wf:
                            web = json.load(wf)
                    except Exception:
                        web = []
                else:
                    web = []

                # Keep only latest per symbol (newest first)
                seen = set()
                unique = []
                for s in web:
                    key = s.get('symbol') or s.get('display_name')
                    if key and key not in seen:
                        seen.add(key)
                        unique.append(s)

                for s in unique:
                    data = s.get('data', {})
                    decision = (data.get('decision') or '').upper()
                    if 'BUY' in decision or 'SELL' in decision:
                        entry = data.get('entry_price')
                        sl = data.get('stop_loss')
                        tp = data.get('take_profit')

                        # Compute free balance
                        total_balance = float(getattr(config, 'VIRTUAL_BALANCE', 100.0))
                        if not getattr(config, 'DRY_RUN', False) and components.get('broker') is not None:
                            try:
                                total_balance = components['broker'].get_balance()
                            except Exception:
                                pass

                        used = 0.0
                        if components.get('llm_engine') is not None:
                            try:
                                pend = components['llm_engine'].learning_system.get_pending_trades()
                                for t in pend:
                                    try:
                                        t_sym = t.get('symbol', '')
                                        lot_ex = float(t.get('position_size') or 0.01)
                                        p_ex = float(t.get('entry_price', 1.0))
                                        # Use standard notional calc
                                        if t_sym.startswith("USD"):
                                            used += (lot_ex * 100000) / 100.0
                                        else:
                                            used += (lot_ex * 100000 * p_ex) / 100.0
                                    except Exception:
                                        continue
                            except Exception:
                                pass

                        free_balance = max(0.0, total_balance - used)

                        try:
                            lot = components['risk_manager'].calculate_position_size(
                                symbol=s.get('symbol'),
                                entry_price=float(entry) if entry else 0,
                                stop_loss=float(sl) if sl else 0,
                                risk_percent=config.RISK_PERCENT,
                                balance_override=free_balance
                            )
                        except Exception:
                            lot = 0.01

                        notional = None
                        try:
                            sym_p = s.get('symbol', '')
                            cp = components['data_fetcher'].get_current_price(sym_p)
                            cp_f = float(cp) if cp else None
                            if cp_f:
                                if sym_p.startswith("USD") or "USD" not in sym_p: # Simplified, real logic in compute_notional
                                    notional = compute_notional(sym_p, lot, cp_f)
                                else:
                                    notional = compute_notional(sym_p, lot, cp_f)
                        except Exception:
                            notional = None

                        plan.append({
                            'symbol': s.get('symbol'),
                            'decision': decision,
                            'entry': entry,
                            'lot': lot,
                            'notional_usd': notional,
                            'free_balance': round(free_balance, 2),
                            'used_balance': round(used, 2)
                        })

                # Save plan file
                os.makedirs('data', exist_ok=True)
                with open(os.path.join('data', 'position_plan.json'), 'w', encoding='utf-8') as pf:
                    json.dump(plan, pf, ensure_ascii=False, indent=2)
                
                # Execute Plan
                try:
                    def execute_position_plan(components, plan_data):
                        # Determine available free balance
                        try:
                            if getattr(config, 'DRY_RUN', False):
                                initial_balance = float(getattr(config, 'VIRTUAL_BALANCE', 100.0))
                            else:
                                initial_balance = float(components['broker'].get_balance() or 0)
                        except Exception:
                            initial_balance = 100.0

                        # Calculate current free balance by subtracting margin of open trades
                        trades = load_simulated_trades()
                        used_margin = sum(t.get('margin_required', 0) for t in trades if t.get('status') == 'OPEN')
                        free_bal = max(0.0, initial_balance - used_margin)

                        for item in plan_data:
                            try:
                                sym = item['symbol']
                                # check if exists
                                already_open = False
                                for t in trades:
                                    if t['symbol'] == sym and t['status'] == 'OPEN':
                                        already_open = True; break
                                if already_open: continue

                                lot = float(item.get('lot', 0.01))
                                entry = item.get('entry')
                                if not entry:
                                    cp = components['data_fetcher'].get_current_price(sym)
                                    entry = float(cp) if cp else None
                                
                                if not entry: continue

                                notional = compute_notional(sym, lot, entry)
                                leverage = 100.0 # Assumed leverage
                                margin_req = (notional or 0) / leverage

                                if free_bal >= margin_req:
                                    spec = {
                                        'symbol': sym,
                                        'direction': item.get('decision'),
                                        'lot': lot,
                                        'entry': entry,
                                        'stop_loss': None, # risk manager handles it in real trades, here we can fetch from signal
                                        'take_profit': None,
                                        'leverage': leverage
                                    }
                                    # Fetch TP/SL from web results for this signal
                                    for s in web:
                                        if (s.get('symbol') == sym or s.get('display_name') == sym):
                                            spec['stop_loss'] = s.get('data', {}).get('stop_loss')
                                            spec['take_profit'] = s.get('data', {}).get('take_profit')
                                            break
                                    
                                    t = open_simulated_trade_from_spec(spec, components)
                                    if t:
                                        free_bal -= margin_req
                                        logger.info(f"✅ Bot Planı Uyguladı: {sym} işlem açıldı. Lot: {lot}")
                            except Exception:
                                continue
                        
                        # Save stats summary
                        try:
                            summary = simulated_trades_summary()
                            ui.save_result_for_web('SIMULATED_TRADES_SUMMARY', summary)
                        except Exception:
                            pass

                    execute_position_plan(components, plan)
                except Exception as e:
                    logger.error(f"Plan yürütme hatası: {e}")
            except Exception as e:
                logger.error(f"⚠️ Position plan generation error: {e}")

            # Tüm pass'ler tamamlandı — belirtilen süre kadar bekle
            logger.info(f"⏳ Tüm pass'ler tamamlandı. {post_wait}s bekleniyor...")
            time.sleep(post_wait)
    
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
