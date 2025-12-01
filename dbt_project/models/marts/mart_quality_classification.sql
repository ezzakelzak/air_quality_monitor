with measurements as (
    select * from {{ ref('stg_measurements') }}
)

select
    *,
    case
        when aqi <= 20 then 'Bon'
        when aqi <= 60 then 'Moyen'
        else 'Médiocre'
    end as quality_label,
    case
        when aqi <= 20 then 'Good'
        when aqi <= 60 then 'Fair/Moderate'
        else 'Poor'
    end as quality_label_en
from measurements
