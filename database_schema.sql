-- SusDE套利监控数据库表结构
-- 在Supabase SQL编辑器中执行此脚本

-- 1. 套利检查记录表
CREATE TABLE IF NOT EXISTS arbitrage_checks (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    check_type VARCHAR(20) NOT NULL DEFAULT 'scheduled', -- 'scheduled', 'manual', 'alert'
    amount DECIMAL(20, 6) NOT NULL,
    usdt_to_susde_price DECIMAL(20, 10),
    susde_to_usde_rate DECIMAL(20, 10),
    usde_to_usdt_price DECIMAL(20, 10),
    profit_loss DECIMAL(20, 6),
    profit_percentage DECIMAL(10, 6),
    annualized_return DECIMAL(10, 6),
    is_profitable BOOLEAN NOT NULL DEFAULT FALSE,
    execution_steps TEXT[],
    market_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 告警记录表
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alert_type VARCHAR(20) NOT NULL DEFAULT 'check', -- 'opportunity', 'check', 'error'
    message TEXT NOT NULL,
    arbitrage_data JSONB,
    is_opportunity BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_arbitrage_checks_timestamp ON arbitrage_checks(timestamp);
CREATE INDEX IF NOT EXISTS idx_arbitrage_checks_is_profitable ON arbitrage_checks(is_profitable);
CREATE INDEX IF NOT EXISTS idx_arbitrage_checks_annualized_return ON arbitrage_checks(annualized_return);
CREATE INDEX IF NOT EXISTS idx_arbitrage_checks_check_type ON arbitrage_checks(check_type);

CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_is_opportunity ON alerts(is_opportunity);

-- 4. 创建视图：最近的盈利机会
CREATE OR REPLACE VIEW recent_profitable_opportunities AS
SELECT 
    timestamp,
    amount,
    profit_loss,
    profit_percentage,
    annualized_return,
    execution_steps,
    market_data
FROM arbitrage_checks 
WHERE is_profitable = TRUE 
ORDER BY timestamp DESC;

-- 5. 创建存储过程：计算平均年化收益率
CREATE OR REPLACE FUNCTION avg_annualized_return(start_time TIMESTAMPTZ)
RETURNS DECIMAL AS $$
BEGIN
    RETURN (
        SELECT AVG(annualized_return)
        FROM arbitrage_checks
        WHERE timestamp >= start_time
    );
END;
$$ LANGUAGE plpgsql;

-- 6. 创建存储过程：获取统计数据
CREATE OR REPLACE FUNCTION get_arbitrage_statistics(days_back INTEGER DEFAULT 7)
RETURNS TABLE(
    total_checks BIGINT,
    profitable_count BIGINT,
    success_rate DECIMAL,
    max_apy DECIMAL,
    avg_apy DECIMAL,
    best_opportunity JSONB
) AS $$
DECLARE
    start_time TIMESTAMPTZ;
BEGIN
    start_time := NOW() - (days_back || ' days')::INTERVAL;
    
    RETURN QUERY
    SELECT 
        COUNT(*) as total_checks,
        COUNT(*) FILTER (WHERE is_profitable = TRUE) as profitable_count,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND((COUNT(*) FILTER (WHERE is_profitable = TRUE) * 100.0 / COUNT(*)), 2)
            ELSE 0
        END as success_rate,
        COALESCE(MAX(annualized_return), 0) as max_apy,
        COALESCE(AVG(annualized_return), 0) as avg_apy,
        (
            SELECT to_jsonb(sub)
            FROM (
                SELECT timestamp, profit_loss, annualized_return, market_data
                FROM arbitrage_checks
                WHERE timestamp >= start_time AND is_profitable = TRUE
                ORDER BY annualized_return DESC
                LIMIT 1
            ) sub
        ) as best_opportunity
    FROM arbitrage_checks
    WHERE timestamp >= start_time;
END;
$$ LANGUAGE plpgsql;

-- 7. 创建定期清理旧数据的函数
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 30)
RETURNS TABLE(
    deleted_checks BIGINT,
    deleted_alerts BIGINT
) AS $$
DECLARE
    cutoff_time TIMESTAMPTZ;
    check_count BIGINT;
    alert_count BIGINT;
BEGIN
    cutoff_time := NOW() - (days_to_keep || ' days')::INTERVAL;
    
    -- 删除旧的检查记录
    DELETE FROM arbitrage_checks WHERE timestamp < cutoff_time;
    GET DIAGNOSTICS check_count = ROW_COUNT;
    
    -- 删除旧的告警记录
    DELETE FROM alerts WHERE timestamp < cutoff_time;
    GET DIAGNOSTICS alert_count = ROW_COUNT;
    
    RETURN QUERY SELECT check_count, alert_count;
END;
$$ LANGUAGE plpgsql;

-- 8. 启用行级安全 (RLS) - 可选
-- ALTER TABLE arbitrage_checks ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- 9. 创建策略允许所有操作 (开发环境) - 可选
-- CREATE POLICY "Enable all operations for arbitrage_checks" ON arbitrage_checks FOR ALL USING (true);
-- CREATE POLICY "Enable all operations for alerts" ON alerts FOR ALL USING (true);

-- 10. 插入一些示例数据 (可选)
-- INSERT INTO arbitrage_checks (
--     check_type, amount, usdt_to_susde_price, susde_to_usde_rate, 
--     usde_to_usdt_price, profit_loss, profit_percentage, 
--     annualized_return, is_profitable, execution_steps
-- ) VALUES (
--     'manual', 100000, 0.95, 1.08, 0.98, 
--     1250.5, 1.25, 25.8, true, 
--     ARRAY['USDT -> sUSDe', 'sUSDe -> USDe', 'USDe -> USDT']
-- );

COMMENT ON TABLE arbitrage_checks IS 'SusDE套利检查记录表';
COMMENT ON TABLE alerts IS '告警记录表';
COMMENT ON FUNCTION avg_annualized_return IS '计算指定时间范围内的平均年化收益率';
COMMENT ON FUNCTION get_arbitrage_statistics IS '获取套利统计数据';
COMMENT ON FUNCTION cleanup_old_data IS '清理指定天数之前的旧数据';
