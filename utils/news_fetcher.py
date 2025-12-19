"""
Real-time Economic News Fetcher
Supports multiple news sources
"""

import requests
from datetime import datetime, timedelta
import os
from database.news_db import NewsDatabase
from utils.logger import setup_logger

logger = setup_logger("NewsFetcher")


class NewsAPIFetcher:
    """
    NewsAPI.org entegrasyonu
    Ücretsiz plan: Günde 100 istek, 1 ay geriye
    Ücretli plan: $50/ay unlimited
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        self.base_url = "https://newsapi.org/v2/everything"
        self.db = NewsDatabase()
    
    def fetch_forex_news(self, symbols=None, hours_back=24):
        """
        Forex haberleri çek
        
        Args:
            symbols: İlgili semboller (örn: ["EURUSD", "GBPUSD"])
            hours_back: Kaç saat geriye bakılacak
            
        Returns:
            Eklenen haber sayısı
        """
        if not self.api_key:
            logger.error("❌ NewsAPI key not found. Set NEWSAPI_KEY in .env")
            return 0
        
        # Arama kelimeleri
        query = "forex OR currency OR EUR OR USD OR GBP OR gold OR trading"
        
        # Tarih aralığı
        from_date = (datetime.now() - timedelta(hours=hours_back)).isoformat()
        
        params = {
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"❌ NewsAPI error: {response.status_code}")
                return 0
            
            data = response.json()
            articles = data.get("articles", [])
            
            added_count = 0
            
            for article in articles[:50]:  # İlk 50 haber
                # Sentiment analizi yap (basit keyword-based)
                sentiment = self._analyze_sentiment(article["title"] + " " + article.get("description", ""))
                
                # İlgili sembolleri bul
                related_symbols = self._find_related_symbols(article["title"], article.get("description", ""))
                
                if related_symbols:
                    # Veritabanına ekle
                    self.db.add_news(
                        title=article["title"],
                        content=article.get("description", ""),
                        source=article["source"]["name"],
                        published_at=article["publishedAt"],
                        sentiment_score=sentiment,
                        impact_level=self._determine_impact(article),
                        symbols=",".join(related_symbols),
                        url=article.get("url")
                    )
                    added_count += 1
            
            logger.info(f"✅ NewsAPI: {added_count} haber eklendi")
            return added_count
        
        except Exception as e:
            logger.error(f"❌ NewsAPI fetch failed: {str(e)}")
            return 0
    
    def _analyze_sentiment(self, text):
        """Basit keyword-based sentiment analizi"""
        text_lower = text.lower()
        
        bullish_words = ["rise", "rally", "gain", "jump", "surge", "strength", "positive", "up", "boost"]
        bearish_words = ["fall", "drop", "decline", "plunge", "weak", "negative", "down", "crash", "sell"]
        
        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)
        
        # -100 ile +100 arası skor
        if bullish_count > bearish_count:
            return min(bullish_count * 20, 80)
        elif bearish_count > bullish_count:
            return max(-bearish_count * 20, -80)
        else:
            return 0
    
    def _find_related_symbols(self, title, description):
        """İlgili sembolleri bul"""
        text = (title + " " + description).upper()
        symbols = []
        
        symbol_keywords = {
            "EURUSD": ["EUR", "EURO", "EUROPEAN"],
            "GBPUSD": ["GBP", "POUND", "STERLING", "BRITAIN", "UK"],
            "USDJPY": ["JPY", "YEN", "JAPAN"],
            "XAUUSD": ["GOLD", "BULLION"],
            "BTCUSD": ["BITCOIN", "BTC", "CRYPTO"]
        }
        
        for symbol, keywords in symbol_keywords.items():
            if any(kw in text for kw in keywords):
                symbols.append(symbol)
        
        return symbols
    
    def _determine_impact(self, article):
        """Haber etkisini belirle"""
        title = article["title"].lower()
        source = article["source"]["name"].lower()
        
        # Yüksek etkili kaynaklar
        high_impact_sources = ["reuters", "bloomberg", "cnbc", "financial times", "wall street"]
        
        # Yüksek etkili kelimeler
        high_impact_words = ["fed", "ecb", "central bank", "interest rate", "gdp", "inflation", "employment"]
        
        if any(source_name in source for source_name in high_impact_sources):
            if any(word in title for word in high_impact_words):
                return "HIGH"
            return "MEDIUM"
        
        return "LOW"


class AlphaVantageFetcher:
    """
    Alpha Vantage - Ücretsiz
    Limit: Günde 25 istek, ayda 500
    Economic indicators ve news sentiment API'si var
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.db = NewsDatabase()
    
    def fetch_economic_indicators(self):
        """
        Ekonomik göstergeleri çek
        Örn: GDP, CPI, Unemployment
        """
        if not self.api_key:
            logger.error("❌ Alpha Vantage key not found. Set ALPHAVANTAGE_KEY in .env")
            return 0
        
        indicators = [
            ("REAL_GDP", "GDP"),
            ("CPI", "Inflation"),
            ("UNEMPLOYMENT", "Employment"),
            ("NONFARM_PAYROLL", "Jobs Report")
        ]
        
        added_count = 0
        
        for indicator_name, display_name in indicators:
            try:
                params = {
                    "function": indicator_name,
                    "apikey": self.api_key
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Son veriyi al
                    if "data" in data and len(data["data"]) > 0:
                        latest = data["data"][0]
                        
                        # Sentiment belirle (örnek)
                        sentiment = self._interpret_economic_data(indicator_name, latest.get("value"))
                        
                        self.db.add_news(
                            title=f"US {display_name}: {latest.get('value')}",
                            content=f"Latest {display_name} data: {latest.get('value')}",
                            source="Alpha Vantage",
                            published_at=latest.get("date", datetime.now().isoformat()),
                            sentiment_score=sentiment,
                            impact_level="HIGH",
                            symbols="EURUSD,GBPUSD,USDJPY",
                            category="Economic Data"
                        )
                        added_count += 1
            
            except Exception as e:
                logger.error(f"❌ Failed to fetch {indicator_name}: {str(e)}")
        
        logger.info(f"✅ Alpha Vantage: {added_count} gösterge eklendi")
        return added_count
    
    def _interpret_economic_data(self, indicator, value):
        """Ekonomik veriyi yorumla"""
        # Basit yorumlama - gerçekte önceki değerle karşılaştırmalı
        try:
            val = float(value)
            if indicator == "UNEMPLOYMENT":
                return -50 if val > 5.0 else 30  # Yüksek işsizlik kötü
            elif indicator == "REAL_GDP":
                return 60 if val > 2.0 else -30  # Düşük GDP kötü
            elif indicator == "CPI":
                return -40 if val > 3.0 else 20  # Yüksek enflasyon kötü
        except:
            pass
        
        return 0


class ForexFactoryScraper:
    """
    Forex Factory Calendar - Web Scraping
    Tamamen ücretsiz ama scraping prohibited olabilir
    Sadece eğitim amaçlı
    """
    
    def __init__(self):
        self.base_url = "https://www.forexfactory.com/calendar"
        self.db = NewsDatabase()
        logger.warning("⚠️ Forex Factory scraping may violate ToS. Use official API when available.")
    
    def fetch_calendar(self):
        """Economic calendar'ı çek"""
        # Bu basit örnek - gerçekte BeautifulSoup ile parse edilmeli
        logger.info("📅 Forex Factory scraping not implemented (use NewsAPI or Alpha Vantage)")
        return 0
