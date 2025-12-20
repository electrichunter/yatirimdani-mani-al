"""
Sniper Trading Bot - Yapılandırma Yönetimi
NVIDIA RTX 3050 (4GB VRAM) için optimize edilmiştir
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# İŞLEM MODU
# ==========================================
DRY_RUN = True  # True ise, sadece işlem önerilerini gösterir, uygulama yapmaz
                # Gerçek işlemler için False yapın (önce iyice test edin!)

DEMO_MODE = True  # True ise, simüle edilmiş piyasa verilerini kullanır (MT5 gerekmez)
                  # Gerçek MT5 verilerini kullanmak için False yapın

# ==========================================
# İŞLEM YAPILANDIRMASI
# ==========================================
 
# Not: Hafıza sorunu için şimdilik sınırlı sembol ve zaman dilimi
SYMBOLS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GC=F", "SI=F"]

# Eğer bir sembolde Yahoo'da veri bulunmazsa denenebilecek alternatif semboller
SYMBOL_FALLBACKS = {
    "SI=F": ["XAGUSD=X", "XAG=X"],
    "GC=F": ["XAUUSD=X", "XAU=X"]
}

# ==========================================
# MT5 YAPILANDIRMASI  (şu anda çalışmıyor)
# ==========================================
MT5_LOGIN = os.getenv("MT5_LOGIN", "")
# Varsa int'e çevir, MetaTrader 5 tamsayı giriş bekler
if MT5_LOGIN and MT5_LOGIN.isdigit():
    MT5_LOGIN = int(MT5_LOGIN)
else:
    MT5_LOGIN = 0

MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
MT5_PATH = os.getenv("MT5_PATH", "") # Opsiyonel: terminal64.exe yolu

# SYMBOLS_FULL Listesi (Yedek/Referans için duruyor)
# [ ... içerik gizlendi ... ]

TIMEFRAMES = {
    "M1": "1 dakika",
    "M5": "5 dakika",
    "M15": "15 dakika",
    "M30": "30 dakika",
    "H1": "1 saat",
    "H4": "4 saat",
    "D1": "1 gün",
    "W1": "1 hafta"
}

# Seçilen zaman dilimi (main.py'de kullanıcı tarafından belirlenecek)
SELECTED_TIMEFRAME = "H1"

# Risk Yönetimi
RISK_PERCENT = 10.0  # İşlem başına hesap bakiyesinin %10'unu riske at (Kullanıcı Talebi)
MIN_RISK_REWARD_RATIO = 1.5  # Daha agresif işlemler için düşürüldü (önceden 2.0 idi)
MAX_DAILY_TRADES = 10  # Daha fazla aktivite için artırıldı
MAX_OPEN_POSITIONS = 5  # Daha fazla aktivite için artırıldı

# ==========================================
# FİLTRE EŞİKLERİ (SNIPER MODU)
# ==========================================

# 1. Aşama: Teknik Filtre
TECHNICAL_MIN_SCORE = 10  # Test için düşürüldü (Normalde 70)
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
VOLUME_MULTIPLIER = 1.5  # Ortalama hacmin 1.5 katı olmalı

# 2. Aşama: Haber Filtresi
NEWS_LOOKBACK_HOURS = 24
MIN_NEWS_SENTIMENT = 50  # 100 üzerinden (işlem yönüyle uyumlu olmalı)
NEWS_IMPACT_LEVELS = ["HIGH", "MEDIUM"]  # DÜŞÜK etkili haberleri yoksay

# 3. Aşama: LLM Kararı
MIN_CONFIDENCE = 70  # Uygulama için minimum güven (önceden 90 idi)

# Gösterim: düşük güvenli durumlarda kullanıcıyı rahatlatmak için
# Web'de minimum gösterilecek güven seviyesi (gerçek confidence değişmez)
MIN_DISPLAY_CONFIDENCE = 10  # yüzde olarak (ör. %10)

# Sanal bakiye simülasyonu (kullanıcıya $100 ile işlem açıyormuş gibi göster)
VIRTUAL_BALANCE = 100.0  # USD cinsinden
# Sanal hesapta işlem açılırken risk yüzdesi (ör. 1 => %1)
VIRTUAL_RISK_PERCENT = 1.0
# Eğer bir LLM kararı düşük güven seviyesindeyse, kaç kez yeniden deneneceği
# ve denemeler arasında kaç saniye bekleneceği.
MAX_CONFIDENCE_RETRIES = 5
CONFIDENCE_RETRY_DELAY = 5  # saniye

# ==========================================
# LLM ARKA UÇ SEÇİMİ
# ==========================================
USE_GEMINI_API = True  # ✅ ÖNERİLEN: Hızlı, güvenilir, ücretsiz kota (günde 1500 istek)
                       # False = Yerel Ollama kullan (daha yavaş, GPU gerektirir)

# Gemini API Ayarları (USE_GEMINI_API = True ise)
GEMINI_MODEL = "gemini-2.0-flash"  
# GEMINI_MODEL = "gemini-2.5-flash"    

# Ollama Ayarları (USE_GEMINI_API = False ise)
 
LLM_MODEL = "mistral:latest"  # Alternatif: 4.4GB
 

LLM_TEMPERATURE = 0.0  # "Rüya görmeyi" (halüsinasyonu) engellemek için SIFIR
LLM_TOP_P = 0.1        # Sadece en yüksek olasılıklı teknik sonuçlara odaklan
LLM_MAX_TOKENS = 1024  # Detaylı raporlar için
LLM_CONTEXT_WINDOW = 2048 # Forex verileri için yeterli, VRAM tasarrufu sağlar

# LLM çoklu analiz (ensemble-like) ayarları
LLM_ANALYSIS_RUNS = 3        # (deprecated) eski çoklu analiz ayarı
LLM_POST_ANALYSIS_DELAY = 5  # (deprecated) kısa bekleme ayarı (saniye)

# Yeni: LLM pass davranışı - tüm semboller üzerinde kaç kez tarama yapılacak
# Örneğin 3: tüm sembolleri baştan sona tarar, sonra tekrar, sonra tekrar, sonrasında bekler
LLM_PASS_RUNS = 3
# Bekleme süresi (saniye) tüm pass'lerden sonra (ör. 5 dakika = 300)
LLM_PASS_WAIT_SECONDS = 300

# ==========================================
# RAG YAPILANDIRMASI
# ==========================================
ENABLE_RAG = False  # RAG'ı (Bilgi Geri Çağırma) devre dışı bırakmak için False yapın
VECTOR_DB_TYPE = "chromadb"  # Seçenekler: chromadb, faiss
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Hafif, hızlı vektörleştirme modeli
RAG_TOP_K = 3  # En ilgili 3 strateji parçasını getir
RAG_DATA_PATH = "./data/strategies"
VECTOR_DB_PATH = "./data/embeddings/chroma_db"

# ==========================================
# VERİTABANI YAPILANDIRMASI
# ==========================================
NEWS_DB_PATH = "./database/news.db"

# ==========================================
# SİSTEM YAPILANDIRMASI
# ==========================================
CHECK_INTERVAL = 60  # Daha hızlı kontrol (1 dakika)
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "./logs/trading.log"
ERROR_LOG_FILE = "./logs/errors.log"

# ==========================================
# PERFORMANS VE ANALİZ OPTİMİZASYONU (RAG-SIZ SİSTEM)
# ==========================================
ENABLE_GPU = True          # LLM'in kendisini GPU'da çalıştırmak için True
MAX_VRAM_MB = 2000         # Sistem stabilitesi için 4GB'ın biraz altında (3.5GB) tutun afk bırtakacagım için ekran kartını yormamamk amacı ile 
LAZY_LOAD_LLM = False      # RAG olmadığı için doğrudan LLM ile başlayacağız
CACHE_EMBEDDINGS = False   # Vektörleme yapılmayacağı için bellek harcamasın
 
# ==========================================
# EK: Re-entry / Pending trade management
# ==========================================
# Eğer bir pozisyon açıldıktan sonra kapanana kadar beklenmesi isteniyorsa
# ve eğer pozisyon 2 günden uzun süre açık kalırsa LLM'e kapatma kararı sorulsun.
CLOSE_PENDING_AFTER_DAYS = 2

# Pozisyon kapandıktan sonra aynı fiyata yakın yeni pozisyon açılmasını engellemek
# için kaç saat beklenmesi gerektiği
REENTRY_COOLDOWN_HOURS = 5

# Fiyat toleransı (mutlak fark veya yüzde olarak yorumlanır). Örn: 0.001 ~ 0.1%
REENTRY_PRICE_TOLERANCE = 0.001

# Dashboard auto-start kontrolü: eğer False ise `main.py` dashboard'u arka planda başlatmaz
START_DASHBOARD = True

# Minimum lot gösterimi (fallback) - UI ve plan için
MIN_DISPLAY_LOT = 0.01
