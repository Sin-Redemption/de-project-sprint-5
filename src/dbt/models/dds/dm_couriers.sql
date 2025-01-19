{{
    config(
        materialized='incremental_ignore',
        unique_list=['courier_id'],
    )
}}


SELECT
    object_value::JSON->>'_id' as courier_id,
    object_value::JSON->>'name' as courier_name
FROM 
    {{ source('staging', 'api_couriers') }}
