{{ config(materialized='incremental', unique_key='(symbol, trade_date)') }}

WITH base AS (
    SELECT * FROM {{ ref('stg_prices_5m') }}
    {% if is_incremental() %} 
        WHERE trade_datetime >= (SELECT MAX(trade_date) FROM {{ this }}) - INTERVAL '5 DAY'
    {% endif %}
),

daily_agg AS (
    SELECT 
        symbol,
        CAST(trade_datetime AS DATE) AS trade_date,
        MAX(high_price) AS daily_high,
        MIN(low_price) AS daily_low,
        SUM(volume) AS daily_volume,
        COUNT(*) AS num_bars
    FROM base 
    GROUP BY symbol, CAST(trade_datetime AS DATE)
),

with_ohlc AS (
    SELECT 
        da.symbol,
        da.trade_date,
        FIRST_VALUE(bp.open_price) OVER (PARTITION BY bp.symbol, CAST(bp.trade_datetime AS DATE) ORDER BY bp.trade_datetime ASC) AS daily_open,
        da.daily_high,
        da.daily_low,
        LAST_VALUE(bp.close_price) OVER (PARTITION BY bp.symbol, CAST(bp.trade_datetime AS DATE) ORDER BY bp.trade_datetime ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS daily_close,
        da.daily_volume,
        da.num_bars
    FROM daily_agg da
    JOIN base bp ON da.symbol = bp.symbol AND da.trade_date = CAST(bp.trade_datetime AS DATE)
)

SELECT DISTINCT ON (symbol, trade_date)
    symbol,
    trade_date,
    daily_open,
    daily_high,
    daily_low,
    daily_close,
    daily_volume,
    num_bars,
    ROUND((daily_close - daily_open) / NULLIF(daily_open, 0) * 100, 4) AS daily_return_pct
FROM with_ohlc
ORDER BY symbol, trade_date
