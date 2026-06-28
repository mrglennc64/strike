-- ============================================================================
-- Betting Framework Database Schema - PostgreSQL
-- Production-ready database initialization script
-- ============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Core Authentication & User Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_is_active (is_active)
);

-- ============================================================================
-- Bankroll & Account Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS bankrolls (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    initial_amount NUMERIC(12, 2) NOT NULL,
    current_amount NUMERIC(12, 2) NOT NULL,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    total_wagered NUMERIC(12, 2) DEFAULT 0,
    total_won NUMERIC(12, 2) DEFAULT 0,
    total_lost NUMERIC(12, 2) DEFAULT 0,
    daily_loss_today NUMERIC(12, 2) DEFAULT 0,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id),
    INDEX idx_bankroll_user (user_id),
    INDEX idx_bankroll_current_amount (current_amount)
);

-- ============================================================================
-- Predictions
-- ============================================================================

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sport VARCHAR(50) NOT NULL,
    market VARCHAR(100) NOT NULL,
    event VARCHAR(255) NOT NULL,
    target VARCHAR(255) NOT NULL,
    predicted_probability NUMERIC(5, 4) NOT NULL,
    market_probability NUMERIC(5, 4),
    edge NUMERIC(5, 4),
    kelly_fraction NUMERIC(5, 4),
    confidence NUMERIC(5, 2),
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prediction_user (user_id),
    INDEX idx_prediction_sport (sport),
    INDEX idx_prediction_status (status),
    INDEX idx_prediction_created (created_at)
);

-- ============================================================================
-- Bets & Wagering
-- ============================================================================

CREATE TABLE IF NOT EXISTS bets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prediction_id INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'PENDING',

    -- Bet Details
    stake NUMERIC(10, 2) NOT NULL,
    odds NUMERIC(6, 2) NOT NULL,
    potential_return NUMERIC(10, 2) NOT NULL,
    kelly_fraction_used NUMERIC(5, 4),
    kelly_stake NUMERIC(10, 2),

    -- Settlement
    is_settled BOOLEAN DEFAULT FALSE,
    actual_outcome VARCHAR(255),
    is_winner BOOLEAN,
    actual_return NUMERIC(10, 2),
    pnl NUMERIC(10, 2),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    live_at TIMESTAMP,
    settled_at TIMESTAMP,

    notes TEXT,

    INDEX idx_bet_user (user_id),
    INDEX idx_bet_prediction (prediction_id),
    INDEX idx_bet_status (status),
    INDEX idx_bet_is_settled (is_settled),
    INDEX idx_bet_created (created_at)
);

-- ============================================================================
-- CLV Tracking (Closing Line Value)
-- ============================================================================

CREATE TABLE IF NOT EXISTS clv_bets (
    id SERIAL PRIMARY KEY,
    date VARCHAR(10) NOT NULL,
    player VARCHAR(255) NOT NULL,
    your_side VARCHAR(10) NOT NULL,

    -- Odds
    your_american NUMERIC(8, 2) NOT NULL,
    your_decimal NUMERIC(6, 3),
    close_over_american NUMERIC(8, 2),
    close_under_american NUMERIC(8, 2),

    -- CLV Calculation
    close_fair_prob NUMERIC(5, 4),
    your_break_even NUMERIC(5, 4),
    clv_value NUMERIC(5, 4),

    -- Metadata
    status VARCHAR(20) DEFAULT 'PENDING',
    sport VARCHAR(50) DEFAULT 'baseball_mlb',
    market VARCHAR(100) DEFAULT 'pitcher_strikeouts',
    bookmaker VARCHAR(100),

    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recorded_at TIMESTAMP,
    closed_at TIMESTAMP,
    analyzed_at TIMESTAMP,

    UNIQUE (date, player, your_side),
    INDEX idx_clv_date (date),
    INDEX idx_clv_player (player),
    INDEX idx_clv_status (status),
    INDEX idx_clv_created (created_at)
);

CREATE TABLE IF NOT EXISTS line_captures (
    id SERIAL PRIMARY KEY,
    date VARCHAR(10) NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tag VARCHAR(20) NOT NULL,

    event VARCHAR(255),
    player VARCHAR(255) NOT NULL,

    line NUMERIC(5, 1) NOT NULL,
    over_odds NUMERIC(8, 2) NOT NULL,
    under_odds NUMERIC(8, 2) NOT NULL,
    bookmaker VARCHAR(100) NOT NULL,

    sport VARCHAR(50) DEFAULT 'baseball_mlb',
    market VARCHAR(100) DEFAULT 'pitcher_strikeouts',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_line_date (date),
    INDEX idx_line_player (player),
    INDEX idx_line_captured (captured_at)
);

-- ============================================================================
-- Positions Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bet_id INTEGER REFERENCES bets(id) ON DELETE SET NULL,

    sport VARCHAR(50) NOT NULL,
    market VARCHAR(100) NOT NULL,
    target VARCHAR(255) NOT NULL,

    position_size NUMERIC(10, 2) NOT NULL,
    entry_price NUMERIC(10, 2) NOT NULL,
    current_price NUMERIC(10, 2),
    unrealized_pnl NUMERIC(10, 2),

    status VARCHAR(20) DEFAULT 'OPEN',
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,

    INDEX idx_position_user (user_id),
    INDEX idx_position_status (status),
    INDEX idx_position_opened (opened_at)
);

-- ============================================================================
-- Settlement & Outcomes
-- ============================================================================

CREATE TABLE IF NOT EXISTS settlements (
    id SERIAL PRIMARY KEY,
    bet_id INTEGER NOT NULL REFERENCES bets(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    settled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actual_outcome VARCHAR(255) NOT NULL,
    is_winner BOOLEAN NOT NULL,
    actual_return NUMERIC(10, 2),
    pnl NUMERIC(10, 2),

    notes TEXT,

    INDEX idx_settlement_bet (bet_id),
    INDEX idx_settlement_user (user_id),
    INDEX idx_settlement_settled (settled_at)
);

-- ============================================================================
-- Audit & Logging
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    resource_id INTEGER,

    old_value JSON,
    new_value JSON,
    changes_json JSON,

    ip_address VARCHAR(45),
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_resource (resource),
    INDEX idx_audit_created (created_at)
);

-- ============================================================================
-- Economics & Fed Predictions
-- ============================================================================

CREATE TABLE IF NOT EXISTS economics_predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    metric VARCHAR(50) NOT NULL,
    threshold NUMERIC(10, 4),
    prediction_type VARCHAR(50),

    predicted_probability NUMERIC(5, 4) NOT NULL,
    confidence NUMERIC(5, 2),

    market_probability NUMERIC(5, 4),
    market_source VARCHAR(50),

    latest_value NUMERIC(10, 4),
    actual_outcome BOOLEAN,

    edge NUMERIC(5, 4),
    edge_percentage NUMERIC(5, 2),
    kelly_fraction NUMERIC(5, 4),
    expected_value NUMERIC(10, 4),

    fomc_meeting_date TIMESTAMP,
    next_release_date TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,

    metadata JSON,

    INDEX idx_econ_user (user_id),
    INDEX idx_econ_metric (metric),
    INDEX idx_econ_created (created_at)
);

CREATE TABLE IF NOT EXISTS economics_model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,

    auc_score NUMERIC(5, 4),
    brier_score NUMERIC(5, 4),
    accuracy NUMERIC(5, 4),
    precision NUMERIC(5, 4),
    recall NUMERIC(5, 4),

    train_size INTEGER,
    test_size INTEGER,
    threshold NUMERIC(5, 4),

    training_duration_seconds NUMERIC(10, 2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_econ_model (model_name),
    INDEX idx_econ_metric_type (metric_type)
);

CREATE TABLE IF NOT EXISTS fed_meeting_schedule (
    id SERIAL PRIMARY KEY,
    meeting_date TIMESTAMP NOT NULL UNIQUE,
    decision_date TIMESTAMP,
    description VARCHAR(255),

    expected_rate_cut BOOLEAN,
    actual_rate_cut BOOLEAN,
    rate_change_bps INTEGER,

    notes VARCHAR(500),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_fed_meeting_date (meeting_date)
);

CREATE TABLE IF NOT EXISTS economic_releases (
    id SERIAL PRIMARY KEY,
    release_name VARCHAR(100) NOT NULL,
    series_id VARCHAR(50) UNIQUE,
    release_schedule VARCHAR(50),

    last_release_date TIMESTAMP,
    last_value NUMERIC(12, 4),
    last_forecast NUMERIC(12, 4),
    last_prior NUMERIC(12, 4),

    next_release_date TIMESTAMP,
    next_forecast NUMERIC(12, 4),

    mean_value NUMERIC(12, 4),
    std_dev NUMERIC(12, 4),
    min_value NUMERIC(12, 4),
    max_value NUMERIC(12, 4),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_release_name (release_name),
    INDEX idx_release_series (series_id)
);

CREATE TABLE IF NOT EXISTS economics_edge_opportunities (
    id SERIAL PRIMARY KEY,
    metric VARCHAR(100) NOT NULL,
    direction VARCHAR(10),
    edge_percentage NUMERIC(5, 2),
    kelly_fraction NUMERIC(5, 4),
    kelly_adjusted_fraction NUMERIC(5, 4),

    market_source VARCHAR(50),
    market_price NUMERIC(6, 4),
    market_liquidity NUMERIC(12, 2),

    model_prediction NUMERIC(5, 4),
    confidence_level VARCHAR(20),

    bet_placed BOOLEAN DEFAULT FALSE,
    bet_id INTEGER REFERENCES bets(id),
    position_size NUMERIC(10, 2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    resolved_at TIMESTAMP,

    outcome BOOLEAN,
    realized_edge NUMERIC(5, 2),

    notes VARCHAR(500),

    INDEX idx_edge_metric (metric),
    INDEX idx_edge_created (created_at)
);

-- ============================================================================
-- Earnings Predictions
-- ============================================================================

CREATE TABLE IF NOT EXISTS earnings_predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,

    symbol VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),

    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    earnings_date TIMESTAMP NOT NULL,

    predicted_prob_beat NUMERIC(5, 4),
    predicted_prob_miss NUMERIC(5, 4),
    predicted_prob_in_line NUMERIC(5, 4),

    market_implied_prob_beat NUMERIC(5, 4),

    edge_probability NUMERIC(5, 4),
    edge_pct NUMERIC(5, 2),
    expected_move_pct NUMERIC(5, 2),

    recommendation VARCHAR(50),
    confidence NUMERIC(5, 2),

    features_json JSON,

    analyst_consensus_strength NUMERIC(5, 2),
    num_analysts INTEGER,
    guidance_revision_trend NUMERIC(5, 2),
    iv_rank NUMERIC(5, 2),
    vol_skew NUMERIC(5, 2),
    implied_move_pct NUMERIC(5, 2),
    smart_money_flow VARCHAR(20),

    actual_outcome VARCHAR(20),
    actual_eps NUMERIC(10, 4),
    actual_revenue NUMERIC(15, 2),
    surprise_pct NUMERIC(5, 2),

    outcome_date TIMESTAMP,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_earnings_symbol (symbol),
    INDEX idx_earnings_date (earnings_date),
    INDEX idx_earnings_created (created_at)
);

CREATE TABLE IF NOT EXISTS earnings_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),

    earnings_date TIMESTAMP NOT NULL,
    fiscal_period VARCHAR(20),

    eps_estimate NUMERIC(10, 4),
    revenue_estimate NUMERIC(15, 2),
    guidance_eps_low NUMERIC(10, 4),
    guidance_eps_high NUMERIC(10, 4),

    eps_actual NUMERIC(10, 4),
    revenue_actual NUMERIC(15, 2),

    eps_surprise_pct NUMERIC(5, 2),
    revenue_surprise_pct NUMERIC(5, 2),
    beat_miss VARCHAR(20),

    stock_price_pre_earnings NUMERIC(10, 2),
    stock_price_post_earnings NUMERIC(10, 2),
    post_earnings_move_pct NUMERIC(5, 2),

    iv_rank NUMERIC(5, 2),
    implied_move_pct NUMERIC(5, 2),
    put_call_ratio NUMERIC(5, 4),

    num_analysts INTEGER,
    guidance_revision_trend NUMERIC(5, 2),

    sector VARCHAR(100),
    sector_avg_surprise NUMERIC(5, 2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_earnings_hist_symbol (symbol),
    INDEX idx_earnings_hist_date (earnings_date)
);

-- ============================================================================
-- Portfolio & Risk Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolio_allocations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    mlb_allocation NUMERIC(5, 4),
    tennis_allocation NUMERIC(5, 4),
    cricket_allocation NUMERIC(5, 4),
    horse_allocation NUMERIC(5, 4),
    hockey_allocation NUMERIC(5, 4),
    economics_allocation NUMERIC(5, 4),
    earnings_allocation NUMERIC(5, 4),

    total_allocation NUMERIC(5, 4),

    rationale TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_portfolio_user (user_id),
    INDEX idx_portfolio_timestamp (timestamp)
);

CREATE TABLE IF NOT EXISTS risk_limits_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    daily_loss_limit NUMERIC(10, 2),
    daily_loss_actual NUMERIC(10, 2),
    max_bet_size NUMERIC(10, 2),
    max_kelly_fraction NUMERIC(5, 4),

    limits_exceeded BOOLEAN DEFAULT FALSE,
    limit_type VARCHAR(50),

    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_risk_user (user_id),
    INDEX idx_risk_recorded (recorded_at)
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_bets_user_created ON bets(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bets_user_status ON bets(user_id, status);
CREATE INDEX IF NOT EXISTS idx_predictions_user_created ON predictions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user_created ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clv_date_player ON clv_bets(date, player);

-- ============================================================================
-- Triggers & Functions
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bankrolls_updated_at BEFORE UPDATE ON bankrolls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bets_updated_at BEFORE UPDATE ON bets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Schema Documentation
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts for authentication and account management';
COMMENT ON TABLE bankrolls IS 'User bankroll tracking and account balance';
COMMENT ON TABLE bets IS 'Placed bets with state machine tracking';
COMMENT ON TABLE clv_bets IS 'Closing line value tracking for CLV analysis';
COMMENT ON TABLE predictions IS 'Model predictions across all sports and markets';
COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for all user actions';
COMMENT ON TABLE earnings_predictions IS 'Earnings beat/miss predictions for stocks';
COMMENT ON TABLE economics_predictions IS 'Fed/Economics predictions for macro trades';
COMMENT ON TABLE portfolio_allocations IS 'Risk allocation across verticals';

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

CREATE OR REPLACE VIEW user_performance AS
SELECT
    u.id,
    u.username,
    u.email,
    b.initial_amount,
    b.current_amount,
    ROUND((b.current_amount - b.initial_amount), 2) as total_pnl,
    ROUND(((b.current_amount - b.initial_amount) / b.initial_amount * 100), 2) as roi_percent,
    b.win_count,
    b.loss_count,
    ROUND((b.win_count::numeric / NULLIF(b.win_count + b.loss_count, 0) * 100), 2) as win_rate,
    b.total_wagered,
    COUNT(DISTINCT bet.id) as total_bets,
    u.created_at
FROM users u
LEFT JOIN bankrolls b ON u.id = b.user_id
LEFT JOIN bets bet ON u.id = bet.user_id AND bet.is_settled = TRUE
GROUP BY u.id, u.username, u.email, b.initial_amount, b.current_amount,
         b.win_count, b.loss_count, b.total_wagered, u.created_at;

CREATE OR REPLACE VIEW recent_bets AS
SELECT
    b.id,
    u.username,
    b.stake,
    b.odds,
    b.status,
    b.pnl,
    p.sport,
    p.target,
    b.created_at
FROM bets b
JOIN users u ON b.user_id = u.id
JOIN predictions p ON b.prediction_id = p.id
ORDER BY b.created_at DESC;

-- ============================================================================
-- Initial Data (Optional)
-- ============================================================================

-- Create test user (remove in production)
-- INSERT INTO users (email, username, hashed_password) VALUES
-- ('test@example.com', 'testuser', 'hashed_password_here')
-- ON CONFLICT (email) DO NOTHING;

COMMIT;
