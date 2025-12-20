"""
Otomatik Haber Güncelleme Script
Her saat başı çalıştırılabilir veya cron job olarak ayarlanabilir
"""

import time
from datetime import datetime
from utils.news_fetcher import NewsAPIFetcher, AlphaVantageFetcher
from utils.logger import setup_logger
from database.news_db import NewsDatabase

logger = setup_logger("NewsUpdater")


def update_news():
    """Tüm kaynaklardan haberleri güncelle"""
    logger.info("=" * 60)
    logger.info(f"📰 News Update Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    total_added = 0
    
    # 1. NewsAPI (eğer key varsa)
    try:
        newsapi = NewsAPIFetcher()
        count = newsapi.fetch_forex_news(hours_back=24)
        total_added += count
    except Exception as e:
        logger.error(f"NewsAPI failed: {str(e)}")
    
    # 2. Alpha Vantage (eğer key varsa)
    try:
        alphavantage = AlphaVantageFetcher()
        count = alphavantage.fetch_economic_indicators()
        total_added += count
    except Exception as e:
        logger.error(f"Alpha Vantage failed: {str(e)}")
    
    # 3. Eski haberleri temizle (30 günden eski)
    try:
        db = NewsDatabase()
        db.clear_old_news(days_old=30)
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
    
    logger.info("=" * 60)
    logger.info(f"✅ News Update Complete - {total_added} new articles")
    logger.info("=" * 60)
    
    return total_added


def run_continuous(interval_minutes=60):
    """
    Belirli aralıklarla sürekli haber güncelle
    
    Args:
        interval_minutes: Güncelleme aralığı (dakika)
    """
    logger.info(f"🔄 Starting continuous news updates (every {interval_minutes} minutes)")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            update_news()
            
            logger.info(f"⏳ Next update in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
    
    except KeyboardInterrupt:
        logger.info("🛑 News updater stopped by user")


if __name__ == "__main__":
    # Manuel güncelleme
    update_news()
    
    # Veya sürekli çalıştır (her saat)
    # run_continuous(interval_minutes=60)
