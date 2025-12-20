"""
2. Aşama: Haber Duygu Filtresi
GPU kullanımı gerektirmeyen hızlı SQL tabanlı haber çekme
Hedef: İşlem yönünü temel verilerle doğrulamak
"""

import config
from database.news_db import NewsDatabase
from utils.logger import setup_logger, log_trade_decision

logger = setup_logger("NewsFilter")


class NewsFilter:
    """
    Haber duygu analizi ve filtreleme
    GPU gerektirmez, sadece SQL sorguları kullanır
    """
    
    def __init__(self):
        self.db = NewsDatabase()
        self.logger = logger
    
    def check_sentiment(self, symbol, direction, hours_lookback=None):
        """
        Haber duygusunun işlem yönüyle uyumlu olup olmadığını kontrol eder
        
        Argümanlar:
            symbol: Ticari varlık (örn. "EURUSD")
            direction: İşlem yönü ("BUY" veya "SELL")
            hours_lookback: Geriye dönük bakılacak saat (varsayılanı config'den alır)
            
        Döner:
            Geçti/kaldı durumu, duygu skoru ve ilgili haberleri içeren sözlük
        """
        if hours_lookback is None:
            hours_lookback = config.NEWS_LOOKBACK_HOURS
        
        try:
            # Toplam duygu verisini al
            sentiment_data = self.db.get_aggregated_sentiment(symbol, hours_lookback)
            
            # İlgili haber makalelerini al
            relevant_news = self.db.get_recent_news(
                symbol=symbol,
                hours_lookback=hours_lookback,
                min_impact=config.NEWS_IMPACT_LEVELS
            )
            
            avg_sentiment = sentiment_data["average_sentiment"]
            news_count = sentiment_data["news_count"]
            high_impact_count = sentiment_data["high_impact_count"]
            
            # ========================================
            # KARAR MANTIĞI
            # ========================================
            
            # Haber yoksa, tarafsız geçiş (işlemi engellemez)
            if news_count == 0:
                result = {
                    "pass": True,
                    "sentiment_score": 0,
                    "relevant_news": [],
                    "news_count": 0,
                    "reason": "Yakın zamanda yüksek/orta etkili haber yok"
                }
                log_trade_decision(logger, symbol, 2, result)
                return result
            
            # Duygu uyumunu kontrol et
            passed = False
            reason = ""
            
            if direction == "BUY":
                # ALIM için pozitif veya nötr duygu istenir
                if avg_sentiment >= config.MIN_NEWS_SENTIMENT:
                    passed = True
                    reason = f"Yükseliş eğilimli duygu ({avg_sentiment:.1f}) ALIM'ı destekliyor"
                elif avg_sentiment >= -20:  # Hafif negatif kabul edilebilir
                    passed = True
                    reason = f"Nötr duygu ({avg_sentiment:.1f}) ALIM ile uyuşmuyor"
                else:
                    passed = False
                    reason = f"Düşüş eğilimli duygu ({avg_sentiment:.1f}) ALIM yönüyle çelişiyor"
            
            elif direction == "SELL":
                # SATIM için negatif veya nötr duygu istenir
                if avg_sentiment <= -config.MIN_NEWS_SENTIMENT:
                    passed = True
                    reason = f"Düşüş eğilimli duygu ({avg_sentiment:.1f}) SATIM'ı destekliyor"
                elif avg_sentiment <= 20:  # Hafif pozitif kabul edilebilir
                    passed = True
                    reason = f"Nötr duygu ({avg_sentiment:.1f}) SATIM ile uyuşmuyor"
                else:
                    passed = False
                    reason = f"Yükseliş eğilimli duygu ({avg_sentiment:.1f}) SATIM yönüyle çelişiyor"
            
            else:
                # 1. Aşamadan NÖTR yön gelmişse
                passed = False
                reason = "1. Aşamadan net bir yön bilgisi yok"
            
            # Sonucu hazırla
            result = {
                "pass": passed,
                "sentiment_score": avg_sentiment,
                "relevant_news": [
                    {
                        "title": n["title"],
                        "source": n["source"],
                        "sentiment": n["sentiment_score"],
                        "impact": n["impact_level"],
                        "published_at": n["published_at"]
                    }
                    for n in relevant_news[:5]  # En yeni 5 haber
                ],
                "news_count": news_count,
                "high_impact_count": high_impact_count,
                "reason": reason
            }
            
            # Kararı günlükle
            log_trade_decision(logger, symbol, 2, result)
            
            return result
        
        except Exception as e:
            logger.error(f"{symbol} haber duygu kontrolü hatası: {str(e)}")
            return {
                "pass": False,
                "sentiment_score": 0,
                "relevant_news": [],
                "reason": f"Haber filtresi hatası: {str(e)}"
            }
    
    def add_sample_news(self):
        """Test için örnek haberler ekler (üretimde kaldırılır)"""
        from datetime import datetime
        
        logger.info("📰 Örnek haber verileri ekleniyor...")
        
        samples = [
            {
                "title": "Fed Faiz Artırımlarının Devam Edeceği Sinyalini Verdi",
                "source": "Bloomberg",
                "published_at": datetime.now().isoformat(),
                "sentiment_score": -60,  # USD çiftleri için düşüş eğilimli
                "impact_level": "HIGH",
                "symbols": "EURUSD,GBPUSD,USDJPY",
                "category": "Merkez Bankası"
            },
            {
                "title": "ECB Faizleri Sabit Tuttu, Güvercin Görünüm",
                "source": "Reuters",
                "published_at": datetime.now().isoformat(),
                "sentiment_score": -40,  # EUR için düşüş eğilimli
                "impact_level": "HIGH",
                "symbols": "EURUSD,EURJPY,EURGBP",
                "category": "Merkez Bankası"
            },
            {
                "title": "Güvenli Liman Talebiyle Altın Yükseliyor",
                "source": "CNBC",
                "published_at": datetime.now().isoformat(),
                "sentiment_score": 70,  # XAUUSD için yükseliş eğilimli
                "impact_level": "MEDIUM",
                "symbols": "XAUUSD",
                "category": "Emtialar"
            }
        ]
        
        for news in samples:
            self.db.add_news(**news)
        
        logger.info(f"✅ {len(samples)} örnek haber makalesi eklendi")
