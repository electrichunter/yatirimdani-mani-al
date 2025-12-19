"""
Sniper Trading Bot - Configuration Management
Optimized for NVIDIA RTX 3050 (4GB VRAM)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# TRADING MODE
# ==========================================
DRY_RUN = True  # If True, only shows trade recommendations without executing
                # Set to False for live trading (test thoroughly first!)

DEMO_MODE = True  # If True, uses simulated market data (no MT5 needed)
                  # Set to False to use real MT5 data

# ==========================================
# TRADING CONFIGURATION
# ==========================================

# 100+ Farklı Varlık - Forex, Emtia, İndeks, Kripto
# Not: Hafıza sorunu için şimdilik tek sembol ve tek zaman dilimi
SYMBOLS = ["EURUSD=X", "GC=F", "SI=F"]

# ==========================================
# MT5 CONFIGURATION (Moved to .env for security)
# ==========================================
MT5_LOGIN = os.getenv("MT5_LOGIN", "")
# Convert to int if exists, MetaTrader 5 expects an integer login
if MT5_LOGIN and MT5_LOGIN.isdigit():
    MT5_LOGIN = int(MT5_LOGIN)
else:
    MT5_LOGIN = 0

MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
MT5_PATH = os.getenv("MT5_PATH", "") # Optional: Path to terminal64.exe

# SYMBOLS_FULL = [
#     # === MAJOR FOREX ÇİFTLERİ (28) ===
#     "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X", "NZDUSD=X",
#     "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURAUD=X", "EURCAD=X", "EURNZD=X",
#     "GBPJPY=X", "GBPCHF=X", "GBPAUD=X", "GBPCAD=X", "GBPNZD=X",
#     "AUDJPY=X", "AUDCHF=X", "AUDCAD=X", "AUDNZD=X", "XAUUSD" ,
#     "CADJPY=X", "CADCHF=X",
#     "CHFJPY=X",
#     "NZDJPY=X", "NZDCHF=X", "NZDCAD=X",
#     XAGUSD
#     # === EXOTIC FOREX (10) ===
#     "USDTRY=X", "USDZAR=X", "USDMXN=X", "USDBRL=X", "USDRUB=X",
#     "USDKRW=X", "USDINR=X", "USDSGD=X", "USDHKD=X", "USDTHB=X",
#     
#     # === DEĞERLİ MADENLER (6) ===
#     "GC=F",     # Gold (Altın)
#     "SI=F",     # Silver (Gümüş)
#     "PL=F",     # Platinum (Platin)
#     "PA=F",     # Palladium (Paladyum)
#     "HG=F",     # Copper (Bakır)
#     "ALI=F",    # Aluminum (Alüminyum)
#     
#     # === ENERJİ (4) ===
#     "CL=F",     # Crude Oil WTI (Ham Petrol)
#     "BZ=F",     # Brent Crude Oil
#     "NG=F",     # Natural Gas (Doğal Gaz)
#     "RB=F",     # Gasoline (Benzin)
#     
#     # === TAHILLAR & TARIM (8) ===
#     "ZC=F",     # Corn (Mısır)
#     "ZW=F",     # Wheat (Buğday)
#     "ZS=F",     # Soybeans (Soya Fasulyesi)
#     "KC=F",     # Coffee (Kahve)
#     "SB=F",     # Sugar (Şeker)
#     "CT=F",     # Cotton (Pamuk)
#     "CC=F",     # Cocoa (Kakao)
#     "OJ=F",     # Orange Juice (Portakal Suyu)
#     
#     # === AMERİKA İNDEKSLERİ (7) ===
#     "^GSPC",    # S&P 500
#     "^DJI",     # Dow Jones
#     "^IXIC",    # NASDAQ
#     "^RUT",     # Russell 2000
#     "^VIX",     # Volatility Index
#     "ES=F",     # E-mini S&P 500 Futures
#     "NQ=F",     # E-mini NASDAQ Futures
#     
#     # === AVRUPA İNDEKSLERİ (5) ===
#     "^FTSE",    # FTSE 100 (UK)
#     "^GDAXI",   # DAX (Germany)
#     "^FCHI",    # CAC 40 (France)
#     "^STOXX50E",# Euro Stoxx 50
#     "^AEX",     # AEX (Netherlands)
#     
#     # === ASYA-PASİFİK İNDEKSLERİ (6) ===
#     "^N225",    # Nikkei 225 (Japan)
#     "^HSI",     # Hang Seng (Hong Kong)
#     "000001.SS",# Shanghai Composite
#     "^AXJO",    # ASX 200 (Australia)
#     "^KS11",    # KOSPI (South Korea)
#     "^TWII",    # Taiwan Weighted
#     
#     # === KRİPTO PARALAR (20) ===
#     "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD",
#     "DOGE-USD", "SOL-USD", "DOT-USD", "MATIC-USD", "LTC-USD",
#     "SHIB-USD", "TRX-USD", "AVAX-USD", "UNI-USD", "LINK-USD",
#     "ATOM-USD", "XLM-USD", "ALGO-USD", "VET-USD", "FIL-USD",
#     
#     # === TÜRK VARLIKLAR (6) ===
#     "XU100.IS",  # BIST 100
#     "GARAN.IS",  # Garanti Bankası
#     "EREGL.IS",  # Ereğli Demir Çelik
#     "THYAO.IS",  # Türk Hava Yolları
#     "AKBNK.IS",  # Akbank
#     "TUPRS.IS",  # Tüpraş
# ]

TIMEFRAMES = {
    "H1": "1 hour",
    "H4": "4 hours",
    "D1": "1 day"
}

# Risk Management
RISK_PERCENT = 1.0  # Risk 1% of account per trade
MIN_RISK_REWARD_RATIO = 1.5  # Lowered for more aggressive trading (was 2.0)
MAX_DAILY_TRADES = 10  # Increased for more activity
MAX_OPEN_POSITIONS = 5  # Increased for more activity

# ==========================================
# FILTER THRESHOLDS (SNIPER MODE)
# ==========================================

# Stage 1: Technical Filter
TECHNICAL_MIN_SCORE = 10  # Test için düşürüldü (Normalde 70)
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
VOLUME_MULTIPLIER = 1.5  # Must be 1.5x average volume

# Stage 2: News Filter
NEWS_LOOKBACK_HOURS = 24
MIN_NEWS_SENTIMENT = 50  # Out of 100 (must align with trade direction)
NEWS_IMPACT_LEVELS = ["HIGH", "MEDIUM"]  # Ignore LOW impact news

# Stage 3: LLM Decision
MIN_CONFIDENCE = 70  # Minimum confidence to execute (was 90)

# ==========================================
# LLM BACKEND SELECTION
# ==========================================
USE_GEMINI_API = True  # ✅ RECOMMENDED: Fast, reliable, free tier (1500 req/day)
                       # False = Use local Ollama (slower, requires GPU)

# Gemini API Settings (if USE_GEMINI_API = True)
GEMINI_MODEL = "gemini-2.0-flash"  # Latest stable high-performance model
# GEMINI_MODEL = "gemini-2.5-flash"      # Experimental version

# Ollama Settings (if USE_GEMINI_API = False)
LLM_MODEL = "llama3.2:latest"  # ✅ EN HIZLI - 2GB, hızlı yanıt verir
# LLM_MODEL = "phi3:latest"  # Alternatif: Microsoft modeli, hızlı (2.2GB)
# LLM_MODEL = "mistral:latest"  # ❌ ÇOK YAVAŞ - Timeout veriyor (4.4GB)
# LLM_MODEL = "tinyllama:latest"  # ❌ ÇOK KÜÇÜK - JSON formatını takip edemez (637MB)

LLM_TEMPERATURE = 0.3  # Slightly higher for more creative/risky analysis
LLM_MAX_TOKENS = 1024  # Increased for detailed reports

# ==========================================
# RAG CONFIGURATION
# ==========================================
ENABLE_RAG = False  # Set to False to disable RAG (Retrieval Augmented Generation)
VECTOR_DB_TYPE = "chromadb"  # Options: chromadb, faiss
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight, fast embeddings
RAG_TOP_K = 3  # Retrieve top 3 most relevant strategy excerpts
RAG_DATA_PATH = "./data/strategies"
VECTOR_DB_PATH = "./data/embeddings/chroma_db"

# ==========================================
# DATABASE CONFIGURATION
# ==========================================
NEWS_DB_PATH = "./database/news.db"

# ==========================================
# SYSTEM CONFIGURATION
# ==========================================
CHECK_INTERVAL = 300  # Check markets every 5 minutes (seconds)
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "./logs/trading.log"
ERROR_LOG_FILE = "./logs/errors.log"

# ==========================================
# PERFORMANCE OPTIMIZATION
# ==========================================
ENABLE_GPU = True  # Use GPU for embeddings (if available)
MAX_VRAM_MB = 4000  # 4GB VRAM limit
LAZY_LOAD_LLM = True  # Only load LLM when Stage 1 & 2 pass
CACHE_EMBEDDINGS = True  # Cache RAG embeddings to reduce re-computation
