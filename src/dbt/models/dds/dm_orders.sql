{{
    config(
        materialized='incremental_ignore',
        unique_list=['order_key'],
    )
}}

SELECT
    oo.object_id as "order_key",
    oo.object_value::JSON->>'final_status' as "order_status",
    dr.id as "restaurant_id",
    dt.id as "timestamp_id",
    du.id as "user_id",
    dc.id as "courier_id"
FROM 
    {{ source('staging', 'ordersystem_orders') }} oo
    INNER JOIN {{ source('staging', 'api_deliveries') }} ad ON oo.object_id = ad.object_value->>'order_id'
    INNER JOIN {{ source('dds', 'dm_restaurants') }} dr ON dr.restaurant_id = (oo.object_value::JSON->>'restaurant')::JSON->>'id'
    INNER JOIN {{ source('dds', 'dm_timestamps') }} dt ON dt.ts = (oo.object_value::JSON->>'date')::TIMESTAMP
    INNER JOIN {{ source('dds', 'dm_users') }} du ON du.user_id = (oo.object_value::JSON->>'user')::JSON->>'id'
    INNER JOIN {{ source('dds', 'dm_couriers') }} dc ON dc.courier_id = ad.object_value::JSON->>'courier_id'