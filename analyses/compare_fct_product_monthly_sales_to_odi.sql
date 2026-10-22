{{ audit_helper.compare_relations(
    a_relation=ref('fct_product_monthly_sales'),
    b_relation=ref('odi_target_fct_product_monthly_sales'),
    primary_key="product_id || '|' || order_month"
) }}
