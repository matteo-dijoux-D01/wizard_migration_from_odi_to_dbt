{{ audit_helper.compare_relations(
    a_relation=ref('dim_customer'),
    b_relation=ref('odi_target_dim_customer'),
    primary_key='customer_id'
) }}
