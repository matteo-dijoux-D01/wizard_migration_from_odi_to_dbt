with orders as (
    select *
    from {{ ref('brz_orders') }}
),

order_lines as (
    select *
    from {{ ref('brz_order_lines') }}
),

products as (
    select *
    from {{ ref('brz_products') }}
),

joined as (
    select
        order_lines.order_line_id,
        orders.order_id,
        orders.customer_id,
        order_lines.product_id,
        cast(orders.order_ts as date) as order_date,
        substring(cast(cast(orders.order_ts as date) as varchar), 1, 7) as order_month,
        orders.status as order_status,
        order_lines.quantity,
        order_lines.unit_price,
        coalesce(order_lines.discount_pct, 0) as discount_pct,
        products.unit_price as catalog_price
    from order_lines
    inner join orders
        on order_lines.order_id = orders.order_id
    inner join products
        on order_lines.product_id = products.product_id
    -- Le mapping ODI exclut uniquement le statut CANCELLED exact.
    where orders.status <> 'CANCELLED'
),

calculated_amounts as (
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
        round(quantity * unit_price * (1 - discount_pct / 100), 2) as net_amount,
        round(
            quantity * unit_price * (1 - discount_pct / 100)
            - quantity * catalog_price,
            2
        ) as margin_vs_catalog
    from joined
)

select *
from calculated_amounts
