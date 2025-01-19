{{
    config(
        materialized='incremental_ignore',
        unique_list=['courier_id'],
    )
}}

WITH cte AS (
    SELECT 
        do2.courier_id as "courier_id",
        dc.courier_name as "courier_name",
        dt."year" as "settlement_year",
        dt."month" as "settlement_month",
        COUNT(DISTINCT fd.order_id) AS "orders_count",
        SUM(fd."sum") as "orders_total_sum",
        AVG(fd.rate) as "rate_avg",
        SUM(fd."sum") * 0.25 as "order_processing_fee",
        CASE 
            WHEN AVG(fd.rate) < 4 THEN GREATEST(SUM(fd."sum") * 0.05, 100.0)
            WHEN AVG(fd.rate) >= 4 AND AVG(fd.rate) < 4.5 THEN GREATEST(SUM(fd."sum") * 0.07, 150.0)
            WHEN AVG(fd.rate) >= 4.5 AND AVG(fd.rate) < 4.9 THEN GREATEST(SUM(fd."sum") * 0.08, 175.0)
            WHEN AVG(fd.rate) >= 4.9 THEN GREATEST(SUM(fd."sum") * 0.1, 200.0)
        END as "courier_order_sum",
        SUM(fd.tip_sum) as "courier_tips_sum"
    FROM 
        {{ source('dds', 'fct_deliveries') }} fd
        INNER JOIN {{ source('dds', 'dm_orders') }} do2 ON fd.order_id = do2.id
        INNER JOIN {{ source('dds', 'dm_couriers') }} dc ON do2.courier_id = dc.id
        INNER JOIN {{ source('dds', 'dm_timestamps') }} dt ON do2.timestamp_id = dt.id
    GROUP BY
        do2.courier_id,
        dc.courier_name,
        dt."year",
        dt."month"
) SELECT *, courier_order_sum + courier_tips_sum * 0.95 AS "courier_reward_sum" from cte