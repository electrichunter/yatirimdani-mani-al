-- News Database Schema for Sniper Trading Bot
-- Stores pre-scored financial news for Stage 2 filtering

CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    source TEXT NOT NULL,
    published_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Financial impact scoring
    sentiment_score INTEGER NOT NULL CHECK(sentiment_score BETWEEN -100 AND 100),
    -- -100 = very bearish, 0 = neutral, +100 = very bullish
    
    impact_level TEXT NOT NULL CHECK(impact_level IN ('HIGH', 'MEDIUM', 'LOW')),
    
    -- Symbol relevance
    symbols TEXT NOT NULL, -- Comma-separated list, e.g., "EURUSD,GBPUSD"
    
    -- Optional fields
    category TEXT, -- e.g., "Central Bank", "Economic Data", "Geopolitical"
    url TEXT
);

-- Indexing for fast queries
CREATE INDEX IF NOT EXISTS idx_published ON news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_symbols ON news(symbols);
CREATE INDEX IF NOT EXISTS idx_impact ON news(impact_level);

-- Example data insertion queries (for reference):
-- INSERT INTO news (title, content, source, published_at, sentiment_score, impact_level, symbols, category)
-- VALUES (
--     'ECB Raises Interest Rates by 50 Basis Points',
--     'European Central Bank announces aggressive rate hike...',
--     'Reuters',
--     '2025-12-17 10:00:00',
--     -75,  -- Bearish for EURUSD (strengthens EUR, but may hurt economy)
--     'HIGH',
--     'EURUSD,EURJPY,EURGBP',
--     'Central Bank'
-- );
