{{
    config(
        materialized='incremental_ignore',
        unique_list=['order_id'],
    )
}}

SELECT 
    do2.id AS "order_id",
    ad.object_value::JSON->>'delivery_id' as "delivery_id",
    ad.object_value::JSON->>'address' as "address",
    (ad.object_value::JSON->>'delivery_ts')::TIMESTAMP as "delivery_ts",
    (ad.object_value::JSON->>'rate')::SMALLINT as "rate",
    (ad.object_value::JSON->>'sum')::NUMERIC as "sum",
    (ad.object_value::JSON->>'tip_sum')::NUMERIC as "tip_sum"
FROM 
    {{ source('staging', 'api_deliveries') }} ad
    INNER JOIN {{ source('dds', 'dm_orders') }} do2 ON ad.object_value->>'order_id' = do2.order_key 