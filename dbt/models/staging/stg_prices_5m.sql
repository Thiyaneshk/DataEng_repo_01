WITH source AS (SELECT * FROM {{ source('raw', 'raw_prices_5m') }}),
cleaned AS (SELECT symbol, datetime AS trade_datetime, ROUND(open, 4) AS open_price, ROUND(high, 4) AS high_price, ROUND(low, 4) AS low_price, ROUND(close, 4) AS close_price, CAST(volume AS BIGINT) AS volume FROM source)
SELECT * FROM cleaned
