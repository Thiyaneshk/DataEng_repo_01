{{ config(materialized='table') }}
SELECT
    p.*,
    i.ema_20,
    i.ema_50,
    i.ema_200,
    i.rsi_14,
    i.macd_line,
    i.signal_line,
    i.macd_histogram,
    i.bb_middle,
    i.bb_upper,
    i.bb_lower,
    i.bb_position,
    i.stoch_k,
    i.stoch_d,
    'Symbol: ' || p.symbol ||
    ' | Close: ' || ROUND(p.daily_close, 2) ||
    ' | RSI: ' || ROUND(i.rsi_14, 1) ||
    ' | MACD: ' || ROUND(i.macd_line, 2) ||
    ' | BB Pos: ' || ROUND(i.bb_position, 2) AS context_string
FROM {{ ref('fct_daily_prices') }} p
LEFT JOIN {{ ref('fct_indicators_1d') }} i ON p.symbol = i.symbol AND p.trade_date = i.trade_date
