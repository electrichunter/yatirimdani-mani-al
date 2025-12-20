from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from typing import List, Dict

app = FastAPI(title="Sniper Trading Bot API")

# CORS ayarları - Next.js frontend'i için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Geliştirme aşamasında her şeye izin ver
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root dizindeki data klasörüne bakar
RESULTS_PATH = "data/web_results.json"
NEWS_PATH = "data/news_results.json"

@app.get("/")
async def root():
    return {"status": "online", "message": "Trading Bot API is running from Root"}

@app.get("/api/results")
async def get_results():
    if not os.path.exists(RESULTS_PATH):
        return []
    try:
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news")
async def get_news():
    if not os.path.exists(NEWS_PATH):
        return []
    try:
        with open(NEWS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # API'yi 8000 portunda başlatır
    uvicorn.run(app, host="0.0.0.0", port=8000)
