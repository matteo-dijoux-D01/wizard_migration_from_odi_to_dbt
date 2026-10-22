{{ audit_helper.compare_relations(
    a_relation=ref('dim_product'),
    b_relation=ref('odi_target_dim_product'),
    primary_key='product_id'
) }}
