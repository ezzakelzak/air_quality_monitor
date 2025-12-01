with measurements as (
    select * from {{ ref('stg_measurements') }}
)

select
    city,
    date_trunc('day', timestamp) as measurement_day,
    avg(pm10) as avg_pm10,
    avg(pm2_5) as avg_pm2_5,
    avg(no2) as avg_no2,
    avg(o3) as avg_o3,
    avg(so2) as avg_so2,
    max(aqi) as max_aqi
from measurements
group by 1, 2
