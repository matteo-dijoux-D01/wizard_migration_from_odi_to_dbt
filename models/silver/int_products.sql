with products as (
    select *
    from {{ ref('brz_products') }}
),

cleaned_products as (
    select
        product_id,
        upper(trim(sku)) as sku,
        trim(product_name) as product_name,
        substring(upper(trim(sku)), 1, 3) as category_code,
        case upper(trim(category))
            when 'LAPTOPS' then 'ELECTRONICS'
            when 'PHONES' then 'ELECTRONICS'
            when 'TABLETS' then 'ELECTRONICS'
            when 'HEADPHONES' then 'ELECTRONICS'
            when 'SOFAS' then 'HOME'
            when 'LAMPS' then 'HOME'
            when 'TABLES' then 'HOME'
            when 'SHOES' then 'FASHION'
            when 'JACKETS' then 'FASHION'
            when 'T-SHIRTS' then 'FASHION'
            else 'OTHER'
        end as category_group,
        unit_price as catalog_price,
        cost_price,
        -- Le DECODE(SIGN(...)) ODI classe 200 et plus comme premium.
        case when unit_price < 200 then 'N' else 'Y' end as is_premium_flag
    from products
)

select *
from cleaned_products
