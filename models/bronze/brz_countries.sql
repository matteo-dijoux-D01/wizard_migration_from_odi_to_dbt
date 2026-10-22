select
    cast(country_id as integer) as country_id,
    cast(country_code as varchar) as country_code,
    cast(country_name as varchar) as country_name,
    cast(region as varchar) as region
from {{ ref('raw_countries') }}
