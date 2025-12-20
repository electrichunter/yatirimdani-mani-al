from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI(title="Sniper Trading Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Yollar - Daha esnek hale getirildi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CONFIG_FILE = os.path.join(DATA_DIR, "bot_config.json")
RESULTS_PATH = os.path.join(DATA_DIR, "web_results.json")
NEWS_PATH = os.path.join(DATA_DIR, "news_results.json")
TRADES_FILE = os.path.join(DATA_DIR, "simulated_trades.json")
TRADING_LOG = os.path.join(LOGS_DIR, "trading.log")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

class BotConfig(BaseModel):
    dataSource: str = 'C'
    llm: str = 'G'
    timeframe: str = '1'
    mode: Optional[str] = 'T'
    duration: Optional[int] = 0

@app.get("/api/results")
async def get_results():
    if not os.path.exists(RESULTS_PATH): return []
    try:
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

@app.get("/api/trades/all")
async def get_all_trades():
    if not os.path.exists(TRADES_FILE): return []
    try:
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

@app.get("/api/trades/open")
@app.get("/api/open_positions")
async def get_open_trades():
    trades = await get_all_trades()
    return [t for t in trades if t.get('status') == 'OPEN']

@app.get("/api/trades/closed")
async def get_closed_trades():
    trades = await get_all_trades()
    return [t for t in trades if t.get('status') == 'CLOSED']

@app.get("/api/stats")
async def get_bot_stats():
    trades = await get_all_trades()
    closed = [t for t in trades if t.get('status') == 'CLOSED']
    total = len(closed)
    wins = len([t for t in closed if (t.get('realized_usd', 0)) > 0])
    
    return {
        "total_trades": total,
        "success_rate": round((wins / total * 100), 2) if total > 0 else 0,
        "total_profit": round(sum(t.get('realized_usd', 0) for t in closed), 2),
        "open_count": len([t for t in trades if t.get('status') == 'OPEN']),
        "free_balance": 100.0 + sum(t.get('realized_usd', 0) for t in closed)
    }

@app.get("/api/config")
async def get_config():
    if not os.path.exists(CONFIG_FILE): return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return None

@app.post("/api/config")
async def save_config(config: BotConfig):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config.dict(), f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news")
async def get_news():
    if not os.path.exists(NEWS_PATH): return []
    try:
        with open(NEWS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

@app.get("/api/status")
async def get_status():
    return {"running": os.path.exists(CONFIG_FILE), "timestamp": datetime.now().isoformat()}

@app.get("/api/terminal")
async def get_terminal_logs():
    if not os.path.exists(TRADING_LOG):
        return {"logs": ["Log dosyası henüz oluşturulmadı. Backend başlatılıyor..."]}
    try:
        with open(TRADING_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return {"logs": lines[-50:]}
    except Exception as e:
        return {"logs": [f"Log okuma hatası: {str(e)}"]}

@app.post("/api/stop")
async def stop_bot():
    """Botu durdurur ve konfigürasyonu sıfırlar."""
    try:
        # Config dosyasını sil (Botu bekleme moduna sokar)
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        
        # Kapatma sinyali oluştur (başlat.py için)
        STOP_SIGNAL = os.path.join(DATA_DIR, "system_stop.signal")
        with open(STOP_SIGNAL, "w") as f:
            f.write("STOP")
            
        return {"status": "success", "message": "Sistem kapatma sinyali gönderildi."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
