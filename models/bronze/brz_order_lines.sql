select
    cast(order_line_id as integer) as order_line_id,
    cast(order_id as integer) as order_id,
    cast(product_id as integer) as product_id,
    cast(quantity as integer) as quantity,
    cast(unit_price as numeric(12, 2)) as unit_price,
    cast(discount_pct as numeric(12, 2)) as discount_pct
from {{ ref('raw_order_lines') }}
