{{ audit_helper.compare_relations(
    a_relation=ref('fct_order_line'),
    b_relation=ref('odi_target_fct_order_line'),
    primary_key='order_line_id'
) }}
