{{ config(materialized='table') }}

WITH daily_base AS (
    -- Aggregate 5m data to daily if needed, or use daily data directly if available
    -- Here we simulate daily aggregation from the 5m data loaded
    SELECT
        symbol,
        DATE(datetime) as trade_date,
        (array_agg(open ORDER BY datetime ASC))[1] as daily_open,
        MAX(high) as daily_high,
        MIN(low) as daily_low,
        (array_agg(close ORDER BY datetime DESC))[1] as daily_close,
        SUM(volume) as daily_volume
    FROM {{ source('raw', 'raw_prices_5m') }}
    GROUP BY 1, 2
),
base AS (
    SELECT
        *,
        LAG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date) as prev_close
    FROM daily_base
),
diffs AS (
    SELECT
        *,
        CASE WHEN daily_close > prev_close THEN daily_close - prev_close ELSE 0 END as gain,
        CASE WHEN daily_close < prev_close THEN prev_close - daily_close ELSE 0 END as loss
    FROM base
),
indicators AS (
    SELECT
        *,
        -- RSI 14
        AVG(gain) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_gain,
        AVG(loss) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_loss,
        -- EMAs
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as ema_20,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as ema_50,
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) as ema_200,
        -- Bollinger Bands
        AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as bb_middle,
        STDDEV(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as bb_std
    FROM diffs
)

SELECT
    symbol,
    trade_date,
    daily_open,
    daily_high,
    daily_low,
    daily_close,
    daily_volume,
    ROUND((daily_close - prev_close) / NULLIF(prev_close, 0) * 100, 2) as daily_return_pct,
    CASE
        WHEN avg_loss = 0 THEN 100
        ELSE 100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0))))
    END as rsi_14,
    ema_20,
    ema_50,
    ema_200,
    bb_middle + (2 * bb_std) as bb_upper,
    bb_middle,
    bb_middle - (2 * bb_std) as bb_lower,
    (daily_close - bb_middle) / NULLIF(bb_std, 0) as bb_position
FROM indicators
