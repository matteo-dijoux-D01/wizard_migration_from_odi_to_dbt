-- Migration fidèle du mapping ODI MAP_DIM_CUSTOMER.
select
    customer_id,
    first_name,
    last_name,
    email,
    country_code,
    country_name,
    region,
    signup_date,
    customer_segment
from {{ ref('int_customers') }}
