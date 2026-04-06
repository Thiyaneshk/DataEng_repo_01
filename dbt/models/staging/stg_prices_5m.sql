WITH source AS (SELECT * FROM {{ source('raw', 'raw_prices_5m') }}),
cleaned AS (SELECT symbol, datetime AS trade_datetime, ROUND(CAST(open AS numeric), 4) AS open_price, ROUND(CAST(high AS numeric), 4) AS high_price, ROUND(CAST(low AS numeric), 4) AS low_price, ROUND(CAST(close AS numeric), 4) AS close_price, CAST(volume AS BIGINT) AS volume FROM source)
SELECT * FROM cleaned
