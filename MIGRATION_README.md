# Migration ODI vers dbt

## 1. Résumé de la migration

Les quatre mappings du package ODI `PKG_DAILY_LOAD` ont été migrés vers une architecture dbt en trois couches : bronze pour le typage des seeds sources, silver pour les nettoyages, jointures et calculs ODI, et gold pour les quatre tables cibles. L'ordre de dépendance du package ODI est reproduit par le DAG dbt : dimensions client et produit, fait ligne de commande, puis agrégat mensuel produit.

Les expressions Oracle ont été traduites en SQL Snowflake portable : `NVL` par `coalesce`, `DECODE` par `case`, `TRUNC` par un cast en date, `TO_CHAR` par une représentation `YYYY-MM`, et les fenêtres et arrondis ont été conservés. Les seeds sources et les seeds de référence ODI n'ont pas été modifiées.

## 2. Modèles créés

### Bronze

- `brz_countries`
- `brz_customers`
- `brz_products`
- `brz_orders`
- `brz_order_lines`

### Silver

- `int_customers` : nettoyage, jointure pays, segmentation et dédoublonnage par email.
- `int_products` : nettoyage, regroupement des catégories et indicateur premium.
- `int_order_lines` : jointures commande-produit, exclusion des annulations et calcul des montants.

### Gold

- `dim_customer`, issu de `MAP_DIM_CUSTOMER`.
- `dim_product`, issu de `MAP_DIM_PRODUCT`.
- `fct_order_line`, issu de `MAP_FCT_ORDER_LINE`.
- `fct_product_monthly_sales`, issu de `MAP_FCT_PRODUCT_MONTHLY_SALES`.

## 3. Tests ajoutés

**18 tests** ont été ajoutés :

- 4 tests `unique` sur les clés simples et l'email client ;
- 6 tests `not_null` sur les clés simples, l'email et la clé composite mensuelle ;
- 3 tests `accepted_values` sur le segment client, l'indicateur premium et le statut de commande ;
- 3 tests `relationships` entre les faits et les dimensions ;
- 1 test `dbt_utils.unique_combination_of_columns` sur `(product_id, order_month)` ;
- 1 test singulier de cohérence de la formule de `net_amount`.

Le test de relation entre `fct_order_line.customer_id` et `dim_customer.customer_id` met en évidence 125 lignes orphelines réparties sur 15 identifiants (`35`, `36`, `65`, `67`, `81`, `103`, `115`, `124`, `133`, `146`, `163`, `190`, `195`, `198`, `200`). Cette anomalie vient de la logique ODI : la dimension conserve l'identifiant de la ligne client la plus récente par email, sans remapper les identifiants déjà portés par les commandes. La fidélité au mapping a été privilégiée et l'écart n'a pas été masqué.

## 4. Résultat de `dbt build`

Commande exécutée : `dbt build --no-partial-parse`.

| Statut | Nombre |
|---|---:|
| Réussis | 38 |
| En erreur | 1 |
| Ignorés | 0 |
| Total | 39 |

Les 9 seeds et les 12 modèles ont été construits. Sur les 18 tests, 17 ont réussi et le test de relation client décrit ci-dessus a échoué avec 125 lignes.

## 5. Recettage dbt contre ODI

Quatre analyses `audit_helper.compare_relations` ont été créées et exécutées. Des différences d'ensembles bidirectionnelles sur toutes les colonnes ont ensuite servi à détailler les écarts.

| Table | Clé | Colonne | Valeur dbt | Valeur ODI | Cause probable |
|---|---|---|---|---|---|
| `dim_customer` | `customer_id=62` | `last_name` | `VINCENT` | `Vincent` | La seed ODI ne respecte pas `UPPER(TRIM(LAST_NAME))` pour cette ligne ; la valeur dbt suit le XML. |
| `fct_order_line` | `order_line_id=347` | `net_amount` | `447.37` | `447.38` | Le calcul décimal exact vaut `447.372` ; dbt applique `ROUND(..., 2)` conformément au XML, tandis que la référence semble issue d'un arrondi flottant différent. |
| `fct_product_monthly_sales` | `product_id=17`, `order_month=2026-06` | Ligne complète | `total_quantity=12`, `total_net_amount=6737.85`, `order_count=7`, `avg_unit_price=577.53` | Ligne absente | Omission probable dans le résultat ODI : les lignes du fait satisfont le seuil `SUM(quantity) >= 5` et produisent cet agrégat. |

`dim_product` est identique à la référence ODI sur toutes les colonnes. Aucun seed n'a été modifié pour réduire ces écarts.

## 6. Durée de la migration

- Heure de début : **2026-10-22 08:49:22 UTC**
- Heure de fin : **2026-10-22 08:57:45 UTC**
- Durée totale : **8 minutes 23 secondes**


## 7. Tokens consommés

Le nombre de tokens consommés n'est pas accessible dans cet environnement ; aucun chiffre n'est inventé.
