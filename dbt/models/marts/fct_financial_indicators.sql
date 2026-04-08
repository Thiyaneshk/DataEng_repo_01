{{ config(materialized='table') }}

WITH base AS (
    SELECT
        *,
        LAG(close_price) OVER (PARTITION BY symbol ORDER BY trade_datetime) as prev_close
    FROM {{ ref('stg_prices') }}
),
diffs AS (
    SELECT
        *,
        CASE WHEN close_price > prev_close THEN close_price - prev_close ELSE 0 END as gain,
        CASE WHEN close_price < prev_close THEN prev_close - close_price ELSE 0 END as loss
    FROM base
),
avg_gains_losses AS (
    -- Simple RSI calculation (14 periods)
    -- Using window functions for simplicity in this example
    SELECT
        *,
        AVG(gain) OVER (PARTITION BY symbol ORDER BY trade_datetime ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_gain,
        AVG(loss) OVER (PARTITION BY symbol ORDER BY trade_datetime ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_loss
    FROM diffs
),
rsi_calc AS (
    SELECT
        *,
        CASE
            WHEN avg_loss = 0 THEN 100
            ELSE 100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0))))
        END as rsi_14
    FROM avg_gains_losses
),
emas AS (
    -- EMA calculation in SQL can be complex without recursive CTEs or specific window functions
    -- For simplicity, we'll provide placeholders or use simplified versions if Postgres/DuckDB allows
    -- Here we use AVG as a placeholder for EMA 50/200 logic
    SELECT
        *,
        AVG(close_price) OVER (PARTITION BY symbol ORDER BY trade_datetime ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as ema_50,
        AVG(close_price) OVER (PARTITION BY symbol ORDER BY trade_datetime ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) as ema_200
    FROM rsi_calc
),
atr_calc AS (
    -- SuperTrend needs ATR. Simplified ATR here (10 period)
    SELECT
        *,
        GREATEST(
            high_price - low_price,
            ABS(high_price - prev_close),
            ABS(low_price - prev_close)
        ) as true_range
    FROM emas
),
supertrend_prep AS (
    SELECT
        *,
        AVG(true_range) OVER (PARTITION BY symbol ORDER BY trade_datetime ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) as atr_10
    FROM atr_calc
)

SELECT
    symbol,
    trade_datetime,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    rsi_14,
    ema_50,
    ema_200,
    -- SuperTrend basic bands
    (high_price + low_price) / 2 + (3 * atr_10) as basic_upper_band,
    (high_price + low_price) / 2 - (3 * atr_10) as basic_lower_band
FROM supertrend_prep
