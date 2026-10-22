-- Migration fidèle du mapping ODI MAP_FCT_ORDER_LINE.
select
    order_line_id,
    order_id,
    customer_id,
    product_id,
    order_date,
    order_month,
    order_status,
    quantity,
    unit_price,
    discount_pct,
    net_amount,
    margin_vs_catalog
from {{ ref('int_order_lines') }}
