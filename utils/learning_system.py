"""
Self-Learning System - Trade Performance Tracker
Bot kendi performansını izler ve zamanla daha iyi kararlar verir
"""

import sqlite3
import config
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

        # Cooldowns table: prevent re-entry near closed price for a period
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entry_cooldowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    blocked_from DATETIME DEFAULT CURRENT_TIMESTAMP,
                    blocked_until DATETIME,
                    blocked_price REAL,
                    tolerance REAL
                )
            """)
            conn.commit()
    
    def log_trade_decision(self, symbol, direction, context, llm_decision, dry_run=True, position_size=None, duplicate_tolerance=None):
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
        if str(direction).upper() not in ["BUY", "SELL"]:
            logger.info(f"ℹ️ Decision '{direction}' is not a trade. Skipping DB log.")
            return -1

        # Prevent duplicate pending trades for same symbol/direction near same price
        tol = duplicate_tolerance if duplicate_tolerance is not None else getattr(config, 'REENTRY_PRICE_TOLERANCE', 0.001)
        entry_price = llm_decision.get("entry_price")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if entry_price is not None:
                try:
                    cur = conn.execute("SELECT * FROM trade_history WHERE outcome = 'PENDING' AND symbol = ? AND direction = ? ORDER BY timestamp DESC", (symbol, direction))
                    rows = cur.fetchall()
                    for r in rows:
                        existing_entry = r['entry_price']
                        if existing_entry is None:
                            continue
                        try:
                            if abs(float(existing_entry) - float(entry_price)) <= float(tol):
                                # Duplicate found, return existing id
                                logger.info(f"⚠️ Duplicate pending trade detected for {symbol} {direction} near price {entry_price}. Skipping new log.")
                                return r['id']
                        except Exception:
                            continue
                except Exception:
                    pass

            cursor = conn.execute("""
                INSERT INTO trade_history (
                    symbol, direction, entry_price, stop_loss, take_profit, position_size,
                    technical_score, news_sentiment, llm_confidence, llm_reasoning,
                    trend_h1, trend_h4, trend_d1, rsi_value, macd_signal,
                    outcome, dry_run
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                direction,
                llm_decision.get("entry_price"),
                llm_decision.get("stop_loss"),
                llm_decision.get("take_profit"),
                position_size,
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

    def force_close_trade(self, trade_id, close_price, reason="LLM_FORCED_CLOSE"):
        """Zorunlu kapatma: pending trade'i kapat ve close_time/price yaz."""
        # Determine outcome relative to direction
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM trade_history WHERE id = ?", (trade_id,)).fetchone()
            if not row:
                return False
            direction = row['direction']
            entry = row['entry_price'] or 0

            outcome = 'BREAKEVEN'
            profit_pips = None
            if entry and close_price:
                profit = close_price - entry if direction == 'BUY' else entry - close_price
                profit_pips = abs(profit) * (100 if 'JPY' in row['symbol'] else 10000)
                if profit > 0:
                    outcome = 'WIN'
                elif profit < 0:
                    outcome = 'LOSS'
                else:
                    outcome = 'BREAKEVEN'

            conn.execute("""
                UPDATE trade_history
                SET outcome = ?, profit_pips = ?, profit_amount = ?, close_price = ?, close_time = ?
                WHERE id = ?
            """, (outcome, profit_pips, profit if entry else None, close_price, datetime.now(), trade_id))
            conn.commit()

        logger.info(f"🛑 Trade ID {trade_id} force-closed by system (reason={reason}) -> outcome={outcome}")
        return True

    def add_entry_cooldown(self, symbol, price, hours, tolerance):
        """Add a cooldown preventing re-entry near `price` for `hours` hours."""
        blocked_until = datetime.now() + timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO entry_cooldowns (symbol, blocked_from, blocked_until, blocked_price, tolerance)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, datetime.now(), blocked_until, price, tolerance))
            conn.commit()
        logger.info(f"⏳ Cooldown set for {symbol} at {price} until {blocked_until}")

    def is_entry_allowed(self, symbol, entry_price):
        """Check if a new entry at `entry_price` is allowed for `symbol`.
        Returns (allowed: bool, reason: str)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM entry_cooldowns WHERE symbol = ? AND blocked_until > ? ORDER BY blocked_until DESC", (symbol, datetime.now())).fetchall()
            for r in rows:
                blocked_price = r['blocked_price']
                tol = r['tolerance'] or 0
                if blocked_price is None:
                    return (True, '')
                # If tolerance looks like a small number (<0.1), treat as absolute difference,
                # otherwise treat as relative percentage
                try:
                    ep = float(entry_price)
                    bp = float(blocked_price)
                    diff = abs(ep - bp)
                    if diff <= float(tol):
                        return (False, f"Re-entry cooldown aktif (fiyat yakın: {bp} ±{tol})")
                except Exception:
                    continue
        return (True, '')

    def reconcile_pending_trades_on_resume(self, price_getter):
        """When monitoring is resumed, check pending trades against current prices.
        `price_getter` is a function that takes a symbol and returns the current price (float) or None.
        For each PENDING trade, if TP or SL condition already met, mark it closed.
        Returns a dict summary of actions taken.
        """
        summary = {
            'checked': 0,
            'closed': 0,
            'skipped': 0,
            'errors': 0
        }
        pending = self.get_pending_trades()
        for t in pending:
            summary['checked'] += 1
            try:
                symbol = t['symbol']
                current = price_getter(symbol)
                if current is None:
                    summary['skipped'] += 1
                    continue

                entry = t.get('entry_price') or 0
                sl = t.get('stop_loss')
                tp = t.get('take_profit')
                direction = t.get('direction')

                outcome = None
                if direction == 'BUY':
                    if tp is not None and current >= tp:
                        outcome = 'WIN'
                    elif sl is not None and current <= sl:
                        outcome = 'LOSS'
                else:  # SELL
                    if tp is not None and current <= tp:
                        outcome = 'WIN'
                    elif sl is not None and current >= sl:
                        outcome = 'LOSS'

                if outcome:
                    profit_pips = None
                    try:
                        profit = current - entry if direction == 'BUY' else entry - current
                        profit_pips = abs(profit) * (100 if 'JPY' in symbol else 10000)
                    except Exception:
                        profit_pips = None

                    self.update_trade_outcome(trade_id=t['id'], outcome=outcome, profit_pips=profit_pips, close_price=current)
                    summary['closed'] += 1
                else:
                    summary['skipped'] += 1
            except Exception:
                summary['errors'] += 1
                continue

        logger.info(f"🔁 Reconcile on resume: checked={summary['checked']} closed={summary['closed']} skipped={summary['skipped']}")
        return summary
    
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
