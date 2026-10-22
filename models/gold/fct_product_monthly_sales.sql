-- Migration fidèle du mapping ODI MAP_FCT_PRODUCT_MONTHLY_SALES.
with order_lines as (
    select *
    from {{ ref('fct_order_line') }}
),

monthly_sales as (
    select
        product_id,
        order_month,
        sum(quantity) as total_quantity,
        sum(net_amount) as total_net_amount,
        count(distinct order_id) as order_count,
        round(avg(unit_price), 2) as avg_unit_price
    from order_lines
    group by product_id, order_month
    -- ODI ne conserve que les groupes atteignant cinq unités.
    having sum(quantity) >= 5
)

select *
from monthly_sales
