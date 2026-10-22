select
    cast(customer_id as integer) as customer_id,
    cast(first_name as varchar) as first_name,
    cast(last_name as varchar) as last_name,
    cast(email as varchar) as email,
    cast(country_id as integer) as country_id,
    cast(signup_date as date) as signup_date,
    cast(loyalty_tier as varchar) as loyalty_tier,
    cast(last_update_ts as timestamp) as last_update_ts
from {{ ref('raw_customers') }}
