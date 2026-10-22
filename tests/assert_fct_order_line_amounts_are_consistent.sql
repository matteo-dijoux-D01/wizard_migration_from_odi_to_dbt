-- Retourne les lignes dont les montants ne respectent pas les formules du mapping ODI.
select
    order_line_id,
    net_amount,
    round(quantity * unit_price * (1 - discount_pct / 100), 2) as expected_net_amount
from {{ ref('fct_order_line') }}
where net_amount <> round(quantity * unit_price * (1 - discount_pct / 100), 2)
