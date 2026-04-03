{{ config(materialized='table') }}
WITH daily_prices AS (SELECT * FROM {{ ref('fct_daily_prices') }}),
emas AS (SELECT symbol, trade_date, AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ema_20, AVG(daily_close) OVER (PARTITION BY symbol ORDER BY trade_date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ema_50 FROM daily_prices)
SELECT p.symbol, p.trade_date, p.daily_close, e.ema_20, e.ema_50 FROM daily_prices p JOIN emas e ON p.symbol = e.symbol AND p.trade_date = e.trade_date
