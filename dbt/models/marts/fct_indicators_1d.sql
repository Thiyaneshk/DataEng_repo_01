{{ config(materialized='table') }}
WITH daily_prices AS (SELECT * FROM {{ ref('fct_daily_prices') }}),

-- Calculate EMAs
emas AS (
    SELECT
        symbol,
        trade_date,
        daily_close,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ema_20,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ema_50,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS ema_200
    FROM daily_prices
),

-- Calculate RSI (Relative Strength Index)
rsi_calc AS (
    SELECT
        symbol,
        trade_date,
        daily_close,
        daily_return_pct,
        CASE WHEN daily_return_pct > 0 THEN daily_return_pct ELSE 0 END AS gain,
        CASE WHEN daily_return_pct < 0 THEN ABS(daily_return_pct) ELSE 0 END AS loss
    FROM daily_prices
),

rsi_14 AS (
    SELECT
        symbol,
        trade_date,
        AVG(gain) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_gain_14,
        AVG(loss) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS avg_loss_14
    FROM rsi_calc
),

-- Calculate MACD (Moving Average Convergence Divergence)
macd_calc AS (
    SELECT
        symbol,
        trade_date,
        daily_close,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS ema_12,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 25 PRECEDING AND CURRENT ROW) AS ema_26
    FROM daily_prices
),

macd_signal AS (
    SELECT
        symbol,
        trade_date,
        ema_12,
        ema_26,
        (ema_12 - ema_26) AS macd_line,
        AVG(ema_12 - ema_26) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW) AS signal_line,
        ((ema_12 - ema_26) - AVG(ema_12 - ema_26) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW)) AS macd_histogram
    FROM macd_calc
),

-- Calculate Bollinger Bands
bb_calc AS (
    SELECT
        symbol,
        trade_date,
        daily_close,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20,
        STDDEV(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS stddev_20
    FROM daily_prices
),

bollinger_bands AS (
    SELECT
        symbol,
        trade_date,
        sma_20 AS bb_middle,
        (sma_20 + 2 * stddev_20) AS bb_upper,
        (sma_20 - 2 * stddev_20) AS bb_lower,
        ((daily_close - (sma_20 - 2 * stddev_20)) / NULLIF((sma_20 + 2 * stddev_20) - (sma_20 - 2 * stddev_20), 0)) AS bb_position
    FROM bb_calc
),

-- Calculate Stochastic Oscillator
stoch_calc AS (
    SELECT
        symbol,
        trade_date,
        daily_high,
        daily_low,
        daily_close,
        MAX(daily_high) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS highest_high_14,
        MIN(daily_low) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS lowest_low_14
    FROM daily_prices
),

stochastic AS (
    SELECT
        symbol,
        trade_date,
        100 * ((daily_close - lowest_low_14) / NULLIF((highest_high_14 - lowest_low_14), 0)) AS stoch_k,
        AVG(100 * ((daily_close - lowest_low_14) / NULLIF((highest_high_14 - lowest_low_14), 0))) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS stoch_d
    FROM stoch_calc
)

-- Final join of all indicators
SELECT
    p.symbol,
    p.trade_date,
    p.daily_open,
    p.daily_high,
    p.daily_low,
    p.daily_close,
    p.daily_volume,
    p.daily_return_pct,

    -- EMAs
    e.ema_20,
    e.ema_50,
    e.ema_200,

    -- RSI
    CASE
        WHEN r.avg_loss_14 = 0 THEN 100
        ELSE 100 - (100 / (1 + (r.avg_gain_14 / NULLIF(r.avg_loss_14, 0))))
    END AS rsi_14,

    -- MACD
    m.macd_line,
    m.signal_line,
    m.macd_histogram,

    -- Bollinger Bands
    b.bb_middle,
    b.bb_upper,
    b.bb_lower,
    b.bb_position,

    -- Stochastic
    s.stoch_k,
    s.stoch_d

FROM daily_prices p
LEFT JOIN emas e ON p.symbol = e.symbol AND p.trade_date = e.trade_date
LEFT JOIN rsi_14 r ON p.symbol = r.symbol AND p.trade_date = r.trade_date
LEFT JOIN macd_signal m ON p.symbol = m.symbol AND p.trade_date = m.trade_date
LEFT JOIN bollinger_bands b ON p.symbol = b.symbol AND p.trade_date = b.trade_date
LEFT JOIN stochastic s ON p.symbol = s.symbol AND p.trade_date = s.trade_date
ORDER BY p.symbol, p.trade_date
