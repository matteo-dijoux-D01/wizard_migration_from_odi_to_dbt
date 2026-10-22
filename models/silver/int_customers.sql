with customers as (
    select *
    from {{ ref('brz_customers') }}
),

countries as (
    select *
    from {{ ref('brz_countries') }}
),

cleaned_and_ranked as (
    select
        customers.customer_id,
        coalesce(upper(trim(customers.first_name)), 'UNKNOWN') as first_name,
        coalesce(upper(trim(customers.last_name)), 'UNKNOWN') as last_name,
        upper(trim(customers.email)) as email,
        coalesce(upper(trim(countries.country_code)), 'XX') as country_code,
        coalesce(upper(trim(countries.country_name)), 'UNKNOWN') as country_name,
        coalesce(upper(trim(countries.region)), 'N/A') as region,
        customers.signup_date,
        case upper(trim(customers.loyalty_tier))
            when 'A' then 'GOLD'
            when 'B' then 'SILVER'
            when 'C' then 'BRONZE'
            else 'STANDARD'
        end as customer_segment,
        -- ODI conserve la ligne la plus récente pour chaque email normalisé.
        row_number() over (
            partition by upper(trim(customers.email))
            order by customers.last_update_ts desc, customers.customer_id desc
        ) as email_recency_rank
    from customers
    left join countries
        on customers.country_id = countries.country_id
)

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
from cleaned_and_ranked
where email_recency_rank = 1
  and signup_date <= current_date
