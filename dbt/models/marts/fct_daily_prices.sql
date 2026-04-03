{{ config(materialized='incremental', unique_key='(symbol, trade_date)') }}
WITH base AS (SELECT * FROM {{ ref('stg_prices_5m') }} {% if is_incremental() %} WHERE trade_datetime >= (SELECT MAX(trade_date) FROM {{ this }}) - INTERVAL 5 DAY {% endif %}),
daily_agg AS (SELECT symbol, CAST(trade_datetime AS DATE) AS trade_date, ARG_MIN(open_price, trade_datetime) AS daily_open, MAX(high_price) AS daily_high, MIN(low_price) AS daily_low, ARG_MAX(close_price, trade_datetime) AS daily_close, SUM(volume) AS daily_volume, COUNT(*) AS num_bars FROM base GROUP BY 1, 2)
SELECT *, ROUND((daily_close - daily_open) / NULLIF(daily_open, 0) * 100, 4) AS daily_return_pct FROM daily_agg
