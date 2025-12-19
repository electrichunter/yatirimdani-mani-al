"""
Stage 2: News Sentiment Filter
Fast SQL-based news retrieval without GPU usage
Goal: Validate trade direction with fundamental data
"""

import config
from database.news_db import NewsDatabase
from utils.logger import setup_logger, log_trade_decision

logger = setup_logger("NewsFilter")


class NewsFilter:
    """
    News sentiment analysis and filtering
    No GPU required, SQL queries only
    """
    
    def __init__(self):
        self.db = NewsDatabase()
        self.logger = logger
    
    def check_sentiment(self, symbol, direction, hours_lookback=None):
        """
        Check if news sentiment aligns with trade direction
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            direction: Trade direction ("BUY" or "SELL")
            hours_lookback: Hours to look back (default from config)
            
        Returns:
            Dict with pass/fail, sentiment score, and relevant news
        """
        if hours_lookback is None:
            hours_lookback = config.NEWS_LOOKBACK_HOURS
        
        try:
            # Get aggregated sentiment
            sentiment_data = self.db.get_aggregated_sentiment(symbol, hours_lookback)
            
            # Get relevant news articles
            relevant_news = self.db.get_recent_news(
                symbol=symbol,
                hours_lookback=hours_lookback,
                min_impact=config.NEWS_IMPACT_LEVELS
            )
            
            avg_sentiment = sentiment_data["average_sentiment"]
            news_count = sentiment_data["news_count"]
            high_impact_count = sentiment_data["high_impact_count"]
            
            # ========================================
            # DECISION LOGIC
            # ========================================
            
            # If no news, neutral pass (doesn't block trade)
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
            
            # Check sentiment alignment
            passed = False
            reason = ""
            
            if direction == "BUY":
                # For BUY, we want positive sentiment or neutral
                if avg_sentiment >= config.MIN_NEWS_SENTIMENT:
                    passed = True
                    reason = f"Yükseliş eğilimli duygu ({avg_sentiment:.1f}) ALIM'ı destekliyor"
                elif avg_sentiment >= -20:  # Slightly negative is acceptable
                    passed = True
                    reason = f"Nötr duygu ({avg_sentiment:.1f}) ALIM ile uyuşmuyor"
                else:
                    passed = False
                    reason = f"Düşüş eğilimli duygu ({avg_sentiment:.1f}) ALIM yönüyle çelişiyor"
            
            elif direction == "SELL":
                # For SELL, we want negative sentiment or neutral
                if avg_sentiment <= -config.MIN_NEWS_SENTIMENT:
                    passed = True
                    reason = f"Düşüş eğilimli duygu ({avg_sentiment:.1f}) SATIM'ı destekliyor"
                elif avg_sentiment <= 20:  # Slightly positive is acceptable
                    passed = True
                    reason = f"Nötr duygu ({avg_sentiment:.1f}) SATIM ile uyuşmuyor"
                else:
                    passed = False
                    reason = f"Yükseliş eğilimli duygu ({avg_sentiment:.1f}) SATIM yönüyle çelişiyor"
            
            else:
                # NEUTRAL direction from Stage 1
                passed = False
                reason = "1. Aşamadan net bir yön bilgisi yok"
            
            # Prepare result
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
                    for n in relevant_news[:5]  # Top 5 most recent
                ],
                "news_count": news_count,
                "high_impact_count": high_impact_count,
                "reason": reason
            }
            
            # Log the decision
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
        """Add sample news for testing (remove in production)"""
        from datetime import datetime
        
        logger.info("📰 Adding sample news data...")
        
        samples = [
            {
                "title": "Fed Signals Continued Rate Hikes",
                "source": "Bloomberg",
                "published_at": datetime.now().isoformat(),
                "sentiment_score": -60,  # Bearish for USD pairs
                "impact_level": "HIGH",
                "symbols": "EURUSD,GBPUSD,USDJPY",
                "category": "Central Bank"
            },
            {
                "title": "ECB Holds Rates Steady, Dovish Outlook",
                "source": "Reuters",
                "published_at": datetime.now().isoformat(),
                "sentiment_score": -40,  # Bearish for EUR
                "impact_level": "HIGH",
                "symbols": "EURUSD,EURJPY,EURGBP",
                "category": "Central Bank"
            },
            {
                "title": "Gold Rallies on Safe Haven Demand",
                "source": "CNBC",
                "published_at": datetime.now().isoformat(),
                "sentiment_score": 70,  # Bullish for XAUUSD
                "impact_level": "MEDIUM",
                "symbols": "XAUUSD",
                "category": "Commodities"
            }
        ]
        
        for news in samples:
            self.db.add_news(**news)
        
        logger.info(f"✅ Added {len(samples)} sample news articles")
