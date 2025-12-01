with classified as (
    select * from {{ ref('mart_quality_classification') }}
),

ranked as (
    select
        *,
        row_number() over (partition by city order by timestamp desc) as rn
    from classified
)

select * from ranked where rn = 1
