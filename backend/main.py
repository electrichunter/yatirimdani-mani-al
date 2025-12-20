
import time
import os
import threading
import json
import webbrowser
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
from update_news import update_news
from database.news_db import NewsDatabase

logger = setup_logger("SniperBot")
ui = UIFormatter()

# Global States
ANALYSIS_COUNTERS = {}
LAST_SAVED_DECISIONS = {}

def is_market_open():
    # Demo/Simülasyon modunda hafta sonu engelini kaldır
    if getattr(config, 'DEMO_MODE', False):
        return True
    now = datetime.now()
    if now.weekday() >= 5: return False
    return True

def select_mode():
    """Frontend'den konfigürasyon bekleyen modern seçici"""
    config_file = os.path.join('data', 'bot_config.json')
    if os.path.exists(config_file):
        try: os.remove(config_file)
        except: pass

    logger.info("⏳ Frontend'den başlangıç komutu bekleniyor...")
    
    while not os.path.exists(config_file):
        time.sleep(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            fe_config = json.load(f)
        
        config.DEMO_MODE = (fe_config.get('dataSource') == 'D')
        config.DRY_RUN = True
        config.USE_GEMINI_API = (fe_config.get('llm') == 'G')
        
        tf = fe_config.get('timeframe')
        tf_map = {
            'S': ('SCAN', 10),
            '1': ('H1', 3600), 
            '4': ('H4', 14400), 
            'D': ('D1', 86400), 
            'W': ('W1', 604800)
        }
        config.SELECTED_TIMEFRAME, config.CHECK_INTERVAL = tf_map.get(tf, ('H1', 3600))

        logger.info(f"🚀 SİSTEM BAŞLATILDI | TF: {config.SELECTED_TIMEFRAME} | INTERVAL: {config.CHECK_INTERVAL}s")
    except Exception as e:
        logger.error(f"Başlatma hatası: {e}")
        exit(1)

def run_dashboard_server():
    """FastAPI Sunucusu"""
    import uvicorn
    try:
        from api import app
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
    except Exception as e:
        logger.error(f"API Hatası: {e}")

def process_symbol(symbol, components):
    """Tek bir sembolü analiz eder"""
    data_fetcher = components["data_fetcher"]
    technical_filter = components["technical_filter"]
    news_filter = components["news_filter"]
    llm_engine = components["llm_engine"]
    risk_manager = components["risk_manager"]

    # 1. Teknik
    market_data = data_fetcher.get_multi_timeframe_data(symbol, [config.SELECTED_TIMEFRAME])
    if not market_data: return False
    
    tech_res = technical_filter.analyze(market_data)
    if not tech_res["pass"]: return False

    # 2. Haber
    news_res = news_filter.check_sentiment(symbol, tech_res["direction"])
    
    # 3. LLM
    context = {
        "symbol": symbol, "technical_signals": tech_res["signals"],
        "technical_score": tech_res["score"], "news_sentiment": news_res["sentiment_score"],
        "current_price": market_data["current_price"], "direction": tech_res["direction"]
    }
    decision = llm_engine.make_decision(context)
    
    if decision["decision"] in ["BUY", "SELL"]:
        # Risk & TP/SL
        val = risk_manager.validate_trade(market_data["current_price"], decision["stop_loss"], decision["take_profit"], symbol, decision["decision"])
        
        signal = {
            "symbol": symbol, "decision": decision["decision"], "confidence": decision["confidence"],
            "entry_price": market_data["current_price"], "stop_loss": val["sl"], "take_profit": val["tp"],
            "reasoning": decision["reasoning"], "rr_ratio": val["rr_ratio"],
            "technical_score": tech_res["score"], "sentiment_score": news_res["sentiment_score"]
        }
        ui.save_result_for_web(symbol, signal)
        
        # Simüle İşlem Aç
        from run_dashboard import open_simulated_trade_from_spec
        open_simulated_trade_from_spec({
            'symbol': symbol, 'direction': decision["decision"], 'lot': 0.1,
            'entry': market_data["current_price"], 'stop_loss': val["sl"], 'take_profit': val["tp"]
        }, components)
        return True
    return False

# Yardımcı Fonksiyonlar (Dashboard/API uyumu için)
def load_simulated_trades():
    path = os.path.join('data', 'simulated_trades.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return []

def save_simulated_trades(trades):
    path = os.path.join('data', 'simulated_trades.json')
    with open(path, 'w', encoding='utf-8') as f: json.dump(trades, f, indent=2)

def update_simulated_trades(components):
    trades = load_simulated_trades()
    updated = False
    for t in trades:
        if t['status'] == 'OPEN':
            curr = components['data_fetcher'].get_current_price(t['symbol'])
            price = float(curr) if curr else None
            if price:
                t['current_price'] = price
                # TP/SL Kontrolü
                is_win = (t['direction'] == 'BUY' and price >= t['take_profit']) or (t['direction'] == 'SELL' and price <= t['take_profit'])
                is_loss = (t['direction'] == 'BUY' and price <= t['stop_loss']) or (t['direction'] == 'SELL' and price >= t['stop_loss'])
                
                if is_win or is_loss:
                    t['status'] = 'CLOSED'
                    t['closed_at'] = datetime.now().isoformat()
                    t['realized_usd'] = 10.0 if is_win else -10.0 # Basit puanlama
                updated = True
    if updated: save_simulated_trades(trades)

def watch_manual_trade_files(components): pass

def main():
    select_mode()
    
    # Eski verileri temizle (Fresh Start)
    for f in ['web_results.json', 'simulated_trades.json', 'news_results.json']:
        p = os.path.join('data', f)
        if os.path.exists(p):
            try: os.remove(p)
            except: pass
            
    broker = YFinanceBroker()
    components = {
        "broker": broker, "data_fetcher": DataFetcher(broker),
        "risk_manager": RiskManager(broker), "technical_filter": TechnicalFilter(),
        "news_filter": NewsFilter(), "llm_engine": LLMDecisionEngine(model_name=config.LLM_MODEL)
    }

    logger.info("💎 SNIPER ENGINE AKTİF. OPERASYON BAŞLADI.")
    logger.info("🚀 İLK TARAMA BAŞLATILIYOR (Tüm Semboller)...")
    
    # Haberleri başlangıçta bir kez kaydet ve eğer boşsa örnek ekle
    try:
        db = NewsDatabase()
        all_news = db.get_recent_news(hours_back=24)
        if not all_news:
            nf = NewsFilter()
            nf.add_sample_news()
            all_news = db.get_recent_news(hours_back=24)
        ui.save_news_for_web(all_news)
    except: pass

    last_news_update = 0
    first_scan = True

    while True:
        loop_start = time.time()
        
        # Her 30 dakikada bir haberleri güncelle
        if time.time() - last_news_update > 1800:
            try:
                update_news()
                # Güncel haberleri web için kaydet
                db = NewsDatabase()
                all_news = db.get_recent_news(hours_back=24)
                ui.save_news_for_web(all_news)
                last_news_update = time.time()
            except: pass

        try:
            update_simulated_trades(components)
        except: pass

        if is_market_open() or first_scan:
            if first_scan:
                logger.info("⚡ İLK TARAMA: Piyasa durumundan bağımsız olarak tüm semboller kontrol ediliyor...")
            
            for symbol in config.SYMBOLS:
                try:
                    process_symbol(symbol, components)
                except Exception as e:
                    logger.error(f"Hata {symbol}: {e}")
                time.sleep(1)
            first_scan = False
        
        elapsed = time.time() - loop_start
        # 60 yerine 10 saniye minimum bekleme
        wait_time = max(10, config.CHECK_INTERVAL - elapsed)
        logger.info(f"⏳ Bir sonraki tarama {wait_time:.1f} saniye sonra.")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()
