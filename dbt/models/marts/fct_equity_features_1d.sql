{{ config(materialized='table') }}
SELECT p.*, i.ema_20, i.ema_50, 'Symbol: ' || p.symbol || ' | Close: ' || ROUND(p.daily_close, 2) AS context_string
FROM {{ ref('fct_daily_prices') }} p LEFT JOIN {{ ref('fct_indicators_1d') }} i ON p.symbol = i.symbol AND p.trade_date = i.trade_date
