with source as (
    select * from {{ source('air_quality', 'raw_measurements') }}
),

renamed as (
    select
        city,
        latitude,
        longitude,
        timestamp,
        pm10,
        pm2_5,
        no2,
        o3,
        so2,
        aqi
    from source
)

select * from renamed
