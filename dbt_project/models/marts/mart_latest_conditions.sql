with measurements as (
    select * from {{ ref('stg_measurements') }}
),

ranked as (
    select
        *,
        row_number() over (partition by city order by timestamp desc) as rn
    from measurements
)

select * from ranked where rn = 1
