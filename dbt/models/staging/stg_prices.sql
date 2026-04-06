/*
    stg_prices.sql — Staging model for market prices.

    Learning goals:
    - This is a "cleaning" layer: rename columns, cast types, filter nulls.
    - Materialized as a VIEW (zero storage cost, always up-to-date).
    - Reference the raw source with {{ source('raw', 'raw_prices_5m') }}.

    After running `dbt run`, query this:
        SELECT * FROM stg_prices LIMIT 10;
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_prices_5m') }}
),

cleaned AS (
    SELECT
        symbol,
        datetime            AS trade_datetime,
        ROUND(CAST(open AS numeric),  4)     AS open_price,
        ROUND(CAST(high AS numeric),  4)     AS high_price,
        ROUND(CAST(low AS numeric),   4)     AS low_price,
        ROUND(CAST(close AS numeric), 4)     AS close_price,
        CAST(volume AS BIGINT) AS volume,

        -- Derived columns useful for downstream analysis
        ROUND(CAST(high AS numeric) - CAST(low AS numeric), 4) AS bar_range,
        ROUND((CAST(close AS numeric) - CAST(open AS numeric)) / NULLIF(CAST(open AS numeric), 0) * 100, 4) AS bar_return_pct

    FROM source
    WHERE symbol   IS NOT NULL
      AND datetime IS NOT NULL
      AND close    IS NOT NULL
)

SELECT * FROM cleaned
