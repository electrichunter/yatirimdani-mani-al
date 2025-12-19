"""
Self-Learning System - Trade Performance Tracker
Bot kendi performansını izler ve zamanla daha iyi kararlar verir
"""

import sqlite3
from datetime import datetime, timedelta
import json
import os
from utils.logger import setup_logger

logger = setup_logger("LearningSystem")


class TradePerformanceTracker:
    """
    İşlem sonuçlarını kaydeder ve analiz eder
    Bot bu verilerden öğrenir
    """
    
    def __init__(self, db_path="./database/learning.db"):
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Veritabanı ve tabloları oluştur"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    position_size REAL,
                    
                    -- Karar verileri
                    technical_score INTEGER,
                    news_sentiment REAL,
                    llm_confidence INTEGER,
                    llm_reasoning TEXT,
                    
                    -- Sonuç (daha sonra güncellenir)
                    outcome TEXT,  -- 'WIN', 'LOSS', 'BREAKEVEN', 'PENDING'
                    profit_pips REAL,
                    profit_amount REAL,
                    close_time DATETIME,
                    close_price REAL,
                    
                    -- Pattern bilgileri
                    trend_h1 TEXT,
                    trend_h4 TEXT,
                    trend_d1 TEXT,
                    rsi_value REAL,
                    macd_signal TEXT,
                    
                    -- Metadata
                    dry_run BOOLEAN DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    win_rate REAL,
                    avg_profit REAL,
                    sample_size INTEGER,
                    confidence_level TEXT
                )
            """)
            
            conn.commit()
        
        logger.info("✅ Learning database initialized")
    
    def log_trade_decision(self, symbol, direction, context, llm_decision, dry_run=True):
        """
        İşlem kararını kaydet
        
        Args:
            symbol: Trading pair
            direction: BUY/SELL
            context: Stage 1 & 2 context
            llm_decision: Stage 3 LLM decision
            dry_run: DRY_RUN mode mu?
            
        Returns:
            Trade ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO trade_history (
                    symbol, direction, entry_price, stop_loss, take_profit,
                    technical_score, news_sentiment, llm_confidence, llm_reasoning,
                    trend_h1, trend_h4, trend_d1, rsi_value, macd_signal,
                    outcome, dry_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                direction,
                llm_decision.get("entry_price"),
                llm_decision.get("stop_loss"),
                llm_decision.get("take_profit"),
                context.get("technical_score"),
                context.get("news_sentiment"),
                llm_decision.get("confidence"),
                llm_decision.get("reasoning"),
                context.get("technical_signals", {}).get("trend_h1"),
                context.get("technical_signals", {}).get("trend_h4"),
                context.get("technical_signals", {}).get("trend_d1"),
                context.get("technical_signals", {}).get("rsi"),
                context.get("technical_signals", {}).get("macd_signal", {}).get("signal"),
                "PENDING",
                dry_run
            ))
            
            trade_id = cursor.lastrowid
            conn.commit()
        
        logger.info(f"📝 Trade logged: ID {trade_id} - {symbol} {direction}")
        return trade_id
    
    def update_trade_outcome(self, trade_id, outcome, profit_pips=None, profit_amount=None, close_price=None):
        """
        İşlem sonucunu güncelle
        
        Args:
            trade_id: Trade ID
            outcome: 'WIN', 'LOSS', 'BREAKEVEN'
            profit_pips: Kar/Zarar (pip)
            profit_amount: Kar/Zarar (para)
            close_price: Kapanış fiyatı
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE trade_history
                SET outcome = ?,
                    profit_pips = ?,
                    profit_amount = ?,
                    close_price = ?,
                    close_time = ?
                WHERE id = ?
            """, (outcome, profit_pips, profit_amount, close_price, datetime.now(), trade_id))
            
            conn.commit()
        
        logger.info(f"✅ Trade updated: ID {trade_id} - {outcome} ({profit_pips} pips)")

    def get_pending_trades(self):
        """Henüz sonuçlanmamış işlemleri getir"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM trade_history WHERE outcome = 'PENDING'")
            return [dict(row) for row in cursor.fetchall()]
    
    def analyze_patterns(self, min_samples=10):
        """
        Pattern'leri analiz et ve öğren
        
        Returns:
            Dict of learned patterns
        """
        patterns = {}
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 1. Trend bazlı analiz
            trend_analysis = conn.execute("""
                SELECT 
                    trend_h1, trend_h4, trend_d1,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    AVG(CASE WHEN outcome = 'WIN' THEN profit_pips ELSE 0 END) as avg_win_pips
                FROM trade_history
                WHERE outcome IN ('WIN', 'LOSS')
                GROUP BY trend_h1, trend_h4, trend_d1
                HAVING COUNT(*) >= ?
                ORDER BY wins * 1.0 / total DESC
            """, (min_samples,)).fetchall()
            
            patterns["trend_patterns"] = []
            for row in trend_analysis:
                win_rate = (row["wins"] / row["total"]) * 100 if row["total"] > 0 else 0
                if win_rate >= 60:  # Sadece %60+ başarılı pattern'leri öğren
                    patterns["trend_patterns"].append({
                        "h1": row["trend_h1"],
                        "h4": row["trend_h4"],
                        "d1": row["trend_d1"],
                        "win_rate": round(win_rate, 1),
                        "sample_size": row["total"],
                        "avg_win": round(row["avg_win_pips"], 1)
                    })
            
            # 2. Confidence bazlı analiz
            confidence_analysis = conn.execute("""
                SELECT 
                    CASE 
                        WHEN llm_confidence >= 95 THEN '95+'
                        WHEN llm_confidence >= 90 THEN '90-94'
                        ELSE '<90'
                    END as conf_range,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM trade_history
                WHERE outcome IN ('WIN', 'LOSS')
                GROUP BY conf_range
            """).fetchall()
            
            patterns["confidence_analysis"] = []
            for row in confidence_analysis:
                win_rate = (row["wins"] / row["total"]) * 100 if row["total"] > 0 else 0
                patterns["confidence_analysis"].append({
                    "range": row["conf_range"],
                    "win_rate": round(win_rate, 1),
                    "sample_size": row["total"]
                })
            
            # 3. Haber sentiment etkisi
            sentiment_analysis = conn.execute("""
                SELECT 
                    CASE 
                        WHEN news_sentiment > 50 THEN 'Strong Bullish'
                        WHEN news_sentiment > 0 THEN 'Weak Bullish'
                        WHEN news_sentiment > -50 THEN 'Weak Bearish'
                        ELSE 'Strong Bearish'
                    END as sentiment_category,
                    direction,
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM trade_history
                WHERE outcome IN ('WIN', 'LOSS') AND news_sentiment IS NOT NULL
                GROUP BY sentiment_category, direction
                HAVING COUNT(*) >= 5
            """).fetchall()
            
            patterns["news_impact"] = []
            for row in sentiment_analysis:
                win_rate = (row["wins"] / row["total"]) * 100 if row["total"] > 0 else 0
                patterns["news_impact"].append({
                    "sentiment": row["sentiment_category"],
                    "direction": row["direction"],
                    "win_rate": round(win_rate, 1),
                    "sample_size": row["total"]
                })
        
        # Save insights
        self._save_insights(patterns)
        
        return patterns
    
    def _save_insights(self, patterns):
        """Öğrenilen pattern'leri kaydet"""
        with sqlite3.connect(self.db_path) as conn:
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    conn.execute("""
                        INSERT INTO learning_insights (pattern_type, pattern_data, win_rate, sample_size)
                        VALUES (?, ?, ?, ?)
                    """, (
                        pattern_type,
                        json.dumps(pattern),
                        pattern.get("win_rate", 0),
                        pattern.get("sample_size", 0)
                    ))
            
            conn.commit()
    
    def get_learned_patterns(self, days_back=30):
        """Son öğrenilen pattern'leri getir"""
        cutoff = datetime.now() - timedelta(days=days_back)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            insights = conn.execute("""
                SELECT pattern_type, pattern_data, win_rate, sample_size
                FROM learning_insights
                WHERE created_at >= ?
                ORDER BY win_rate DESC, sample_size DESC
                LIMIT 20
            """, (cutoff,)).fetchall()
            
            return [
                {
                    "type": row["pattern_type"],
                    "data": json.loads(row["pattern_data"]),
                    "win_rate": row["win_rate"],
                    "sample_size": row["sample_size"]
                }
                for row in insights
            ]
    
    def get_performance_stats(self, days=30):
        """Performans istatistikleri"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    AVG(CASE WHEN outcome = 'WIN' THEN profit_pips ELSE 0 END) as avg_win_pips,
                    AVG(CASE WHEN outcome = 'LOSS' THEN profit_pips ELSE 0 END) as avg_loss_pips,
                    AVG(llm_confidence) as avg_confidence
                FROM trade_history
                WHERE timestamp >= ? AND outcome IN ('WIN', 'LOSS')
            """, (cutoff,)).fetchone()
            
            if stats["total_trades"] > 0:
                win_rate = (stats["wins"] / stats["total_trades"]) * 100
            else:
                win_rate = 0
            
            return {
                "total_trades": stats["total_trades"],
                "win_rate": round(win_rate, 1),
                "wins": stats["wins"],
                "losses": stats["losses"],
                "avg_win_pips": round(stats["avg_win_pips"] or 0, 1),
                "avg_loss_pips": round(stats["avg_loss_pips"] or 0, 1),
                "avg_confidence": round(stats["avg_confidence"] or 0, 1)
            }
