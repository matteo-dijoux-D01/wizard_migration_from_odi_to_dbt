select
    cast(product_id as integer) as product_id,
    cast(sku as varchar) as sku,
    cast(product_name as varchar) as product_name,
    cast(category as varchar) as category,
    cast(unit_price as numeric(12, 2)) as unit_price,
    cast(cost_price as numeric(12, 2)) as cost_price,
    cast(created_date as date) as created_date
from {{ ref('raw_products') }}
