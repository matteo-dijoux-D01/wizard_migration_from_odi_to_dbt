-- Migration fidèle du mapping ODI MAP_DIM_PRODUCT.
select
    product_id,
    sku,
    product_name,
    category_code,
    category_group,
    catalog_price,
    cost_price,
    is_premium_flag
from {{ ref('int_products') }}
