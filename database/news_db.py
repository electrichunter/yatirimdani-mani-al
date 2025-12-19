"""
News Database Manager
Handles SQL operations for financial news storage and retrieval
"""

import sqlite3
from datetime import datetime, timedelta
import os
import config
from utils.logger import setup_logger

logger = setup_logger("NewsDB")


class NewsDatabase:
    """Manages news database operations"""
    
    def __init__(self, db_path=None):
        """
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = config.NEWS_DB_PATH
        
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Create database and tables if they don't exist"""
        # Create directory if needed
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Read schema
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            # Execute schema
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema)
            
            logger.info(f"✅ News database initialized at {self.db_path}")
        
        except FileNotFoundError:
            logger.warning(f"⚠️ Schema file not found at {schema_path}, creating basic table")
            self.create_basic_schema()
    
    def create_basic_schema(self):
        """Fallback: Create basic schema if schema.sql not found"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    source TEXT NOT NULL,
                    published_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sentiment_score INTEGER NOT NULL CHECK(sentiment_score BETWEEN -100 AND 100),
                    impact_level TEXT NOT NULL CHECK(impact_level IN ('HIGH', 'MEDIUM', 'LOW')),
                    symbols TEXT NOT NULL,
                    category TEXT,
                    url TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_published ON news(published_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols ON news(symbols)")
            conn.commit()
    
    def add_news(self, title, source, published_at, sentiment_score, impact_level, symbols, 
                 content=None, category=None, url=None):
        """
        Add news article to database
        
        Args:
            title: News title
            source: News source (e.g., "Reuters")
            published_at: Publication datetime
            sentiment_score: Sentiment score -100 to +100
            impact_level: "HIGH", "MEDIUM", or "LOW"
            symbols: Comma-separated symbols (e.g., "EURUSD,GBPUSD")
            content: Optional full content
            category: Optional category
            url: Optional URL
            
        Returns:
            Inserted news ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO news (title, content, source, published_at, sentiment_score, 
                                 impact_level, symbols, category, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, content, source, published_at, sentiment_score, impact_level, 
                 symbols, category, url))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_news(self, symbol=None, hours_lookback=24, min_impact=None):
        """
        Retrieve recent news articles
        
        Args:
            symbol: Filter by symbol (e.g., "EURUSD"), None for all
            hours_lookback: How many hours to look back
            min_impact: Minimum impact level(s), e.g., ["HIGH", "MEDIUM"]
            
        Returns:
            List of news articles as dicts
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_lookback)
        
        query = """
            SELECT id, title, content, source, published_at, sentiment_score, 
                   impact_level, symbols, category, url
            FROM news
            WHERE published_at >= ?
        """
        params = [cutoff_time.isoformat()]
        
        # Filter by symbol
        if symbol:
            query += " AND symbols LIKE ?"
            params.append(f"%{symbol}%")
        
        # Filter by impact level
        if min_impact:
            placeholders = ','.join(['?' for _ in min_impact])
            query += f" AND impact_level IN ({placeholders})"
            params.extend(min_impact)
        
        query += " ORDER BY published_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            news_list = []
            for row in cursor.fetchall():
                news_list.append({
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "source": row["source"],
                    "published_at": row["published_at"],
                    "sentiment_score": row["sentiment_score"],
                    "impact_level": row["impact_level"],
                    "symbols": row["symbols"],
                    "category": row["category"],
                    "url": row["url"]
                })
            
            return news_list
    
    def get_aggregated_sentiment(self, symbol, hours_lookback=24):
        """
        Calculate aggregated sentiment for a symbol
        
        Args:
            symbol: Trading symbol
            hours_lookback: Hours to look back
            
        Returns:
            Dict with average sentiment and news count
        """
        news_list = self.get_recent_news(symbol, hours_lookback, min_impact=["HIGH", "MEDIUM"])
        
        if not news_list:
            return {
                "average_sentiment": 0,
                "news_count": 0,
                "high_impact_count": 0
            }
        
        total_sentiment = sum(n["sentiment_score"] for n in news_list)
        avg_sentiment = total_sentiment / len(news_list)
        high_impact = sum(1 for n in news_list if n["impact_level"] == "HIGH")
        
        return {
            "average_sentiment": round(avg_sentiment, 1),
            "news_count": len(news_list),
            "high_impact_count": high_impact
        }
    
    def clear_old_news(self, days_old=30):
        """Delete news older than specified days"""
        cutoff = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM news WHERE published_at < ?", (cutoff.isoformat(),))
            conn.commit()
            
            logger.info(f"🗑️ Deleted {cursor.rowcount} old news articles")
