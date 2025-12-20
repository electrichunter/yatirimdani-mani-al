"""
Haber Veritabanı Yöneticisi
Finansal haberlerin saklanması ve geri çağrılması için SQL işlemlerini yönetir
"""

import sqlite3
from datetime import datetime, timedelta
import os
import config
from utils.logger import setup_logger

logger = setup_logger("NewsDB")


class NewsDatabase:
    """Haber veritabanı işlemlerini yönetir"""
    
    def __init__(self, db_path=None):
        """
        Argümanlar:
            db_path: SQLite veritabanı dosyasının yolu
        """
        if db_path is None:
            db_path = config.NEWS_DB_PATH
        
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Veritabanı ve tablolar mevcut değilse oluşturur"""
        # Gerekiyorsa dizini oluştur
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Şemayı oku
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            # Şemayı uygula
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema)
            
            logger.info(f"✅ Haber veritabanı {self.db_path} adresinde hazırlandı")
        
        except FileNotFoundError:
            logger.warning(f"⚠️ {schema_path} adresinde şema dosyası bulunamadı, temel tablo oluşturuluyor")
            self.create_basic_schema()
    
    def create_basic_schema(self):
        """Yedek: schema.sql bulunamazsa temel şemayı oluşturur"""
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
        Veritabanına haber makalesi ekler
        
        Argümanlar:
            title: Haber başlığı
            source: Haber kaynağı (örn. "Reuters")
            published_at: Yayınlanma tarihi ve saati
            sentiment_score: Duygu skoru (-100 ile +100 arası)
            impact_level: "HIGH" (Yüksek), "MEDIUM" (Orta) veya "LOW" (Düşük)
            symbols: Virgülle ayrılmış semboller (örn. "EURUSD,GBPUSD")
            content: İsteğe bağlı tam içerik
            category: İsteğe bağlı kategori
            url: İsteğe bağlı URL
            
        Döner:
            Eklenen haberin ID'si
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
        Yakın zamandaki haber makalelerini getirir
        
        Argümanlar:
            symbol: Sembole göre filtreleme (örn. "EURUSD"), hepsi için None
            hours_lookback: Kaç saat geriye bakılacak
            min_impact: Minimum etki seviyeleri, örn. ["HIGH", "MEDIUM"]
            
        Döner:
            Sözlükler listesi olarak haber makaleleri
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_lookback)
        
        query = """
            SELECT id, title, content, source, published_at, sentiment_score, 
                   impact_level, symbols, category, url
            FROM news
            WHERE published_at >= ?
        """
        params = [cutoff_time.isoformat()]
        
        # Sembole göre filtrele
        if symbol:
            query += " AND symbols LIKE ?"
            params.append(f"%{symbol}%")
        
        # Etki seviyesine göre filtrele
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
        Bir sembol için toplu duygu analizini hesaplar
        
        Argümanlar:
            symbol: Ticari varlık
            hours_lookback: Geriye dönük bakılacak saat
            
        Döner:
            Ortalama duygu ve haber sayısını içeren sözlük
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
        """Belirtilen günden eski haberleri siler"""
        cutoff = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM news WHERE published_at < ?", (cutoff.isoformat(),))
            conn.commit()
            
            logger.info(f"🗑️ {cursor.rowcount} adet eski haber makalesi silindi")
