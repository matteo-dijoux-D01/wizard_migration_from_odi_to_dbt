# Migration ODI vers dbt : repo de démonstration

Ce dépôt est le point de départ d'une démonstration de migration d'un chargement d'entrepôt
**Oracle Data Integrator (ODI)** vers **dbt**, sur dbt platform. Le cas fictif est celui de
**ShopEasy**, un distributeur avec des clients, des commandes et des produits.

Le dépôt contient les sources, les définitions ODI et les résultats produits par ODI.
Le dossier `models/` est volontairement vide : les modèles bronze, silver et gold sont à écrire
pendant la démo.

## Contenu

| Élément | Rôle |
|---------|------|
| `odi_export/` | Exports XML ODI 12c : 4 mappings (`MAP_DIM_CUSTOMER`, `MAP_DIM_PRODUCT`, `MAP_FCT_ORDER_LINE`, `MAP_FCT_PRODUCT_MONTHLY_SALES`) et le package `PKG_DAILY_LOAD` |
| `seeds/raw_*.csv` | Données sources fictives (schéma `raw`) : clients, pays, produits, commandes, lignes de commande |
| `seeds/odi_results/odi_target_*.csv` | Tables cibles telles que chargées par ODI (schéma `odi_legacy`), pour le recettage |
| `seeds/seeds.yml` | Types de colonnes des seeds |
| `scripts/` | Génération déterministe des sources (`generate_data.py`) ; calcul de référence des 4 mappings à partir des seeds (`generate_odi_results.py`) |
| `models/` | Vide. Schémas prévus dans `dbt_project.yml` : `bronze`, `silver`, `gold` |
| `macros/`, `tests/` | Vides |
| `.agents/skills/` | Skills d'agent propres au projet |
| `AGENTS.md` | Contexte du projet et conventions (documentation en français) |

## Arborescence

```text
.
├── AGENTS.md
├── README.md
├── dbt_project.yml          # projet wizard_odi_migration, schémas par couche
├── packages.yml             # dbt_utils, audit_helper
├── models/                  # vide (.gitkeep)
├── macros/
├── tests/
├── seeds/
│   ├── raw_countries.csv        (15 lignes)
│   ├── raw_customers.csv        (200 lignes)
│   ├── raw_products.csv         (40 lignes)
│   ├── raw_orders.csv           (800 lignes)
│   ├── raw_order_lines.csv      (1 976 lignes)
│   ├── seeds.yml
│   └── odi_results/
│       ├── odi_target_dim_customer.csv
│       ├── odi_target_dim_product.csv
│       ├── odi_target_fct_order_line.csv
│       └── odi_target_fct_product_monthly_sales.csv
├── odi_export/
│   ├── MAP_DIM_CUSTOMER.xml
│   ├── MAP_DIM_PRODUCT.xml
│   ├── MAP_FCT_ORDER_LINE.xml
│   ├── MAP_FCT_PRODUCT_MONTHLY_SALES.xml
│   └── PKG_DAILY_LOAD.xml
├── scripts/
│   ├── generate_data.py
│   └── generate_odi_results.py
└── .agents/skills/
```

## Mise en place dans dbt platform

1. **Connexion Git** : dans dbt platform, créer un projet et le relier à ce dépôt
   (intégration GitHub ou URL SSH). Aucun `profiles.yml` n'est versionné : la connexion à
   l'entrepôt se configure dans les paramètres du projet.
2. **Connexion à l'entrepôt** : renseigner les identifiants de développement. Le compte doit
   pouvoir créer des schémas, car le projet écrit dans `raw`, `odi_legacy`, `bronze`, `silver`
   et `gold` (préfixés par le schéma de développement personnel de chaque utilisateur).
3. **Environnement de développement** : ouvrir l'IDE (ou le Studio) sur la branche principale.
4. **Dépendances** : exécuter `dbt deps` pour installer `dbt_utils` et `audit_helper`.
5. **Données** : exécuter `dbt seed`. Neuf tables sont créées : cinq dans `raw`, quatre dans
   `odi_legacy`.

Les types de colonnes de `seeds/seeds.yml` utilisent `varchar(n)`, valable sur Snowflake,
Postgres, Redshift et Databricks. Sur BigQuery, remplacer par `string`.

`dbt_project.yml` déclare des configurations pour `models/bronze`, `models/silver` et
`models/gold` alors que `models/` est vide : dbt peut afficher un avertissement sur des chemins
de configuration sans ressource. C'est attendu.

## Régénérer les sources (facultatif)

Les CSV sont versionnés ; dbt platform n'a besoin d'aucun Python. Pour reproduire les sources
`raw_*` en local (Python 3, bibliothèque standard uniquement) :

```bash
python scripts/generate_data.py
```

La graine est fixe : deux exécutions donnent les mêmes fichiers.
