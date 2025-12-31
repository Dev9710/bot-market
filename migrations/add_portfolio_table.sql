-- Portfolio Tracker Table
-- Stores user's active positions for tracking performance

CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    pool_address TEXT NOT NULL,
    network TEXT NOT NULL,
    token_symbol TEXT NOT NULL,
    token_name TEXT NOT NULL,

    -- Entry details
    entry_price REAL NOT NULL,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    position_size REAL,  -- Optional: amount invested

    -- Current status
    status TEXT DEFAULT 'ACTIVE',  -- ACTIVE, TP1_HIT, TP2_HIT, TP3_HIT, STOP_LOSS, CLOSED
    current_price REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Performance tracking
    tp1_price REAL,
    tp2_price REAL,
    tp3_price REAL,
    stop_loss_price REAL,
    tp1_hit BOOLEAN DEFAULT 0,
    tp2_hit BOOLEAN DEFAULT 0,
    tp3_hit BOOLEAN DEFAULT 0,
    stop_loss_hit BOOLEAN DEFAULT 0,

    -- Calculated metrics
    current_pnl_percent REAL,
    highest_price REAL,
    max_gain_percent REAL,

    -- Notes
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_status ON portfolio(status);
CREATE INDEX IF NOT EXISTS idx_portfolio_alert ON portfolio(alert_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_network ON portfolio(network);
