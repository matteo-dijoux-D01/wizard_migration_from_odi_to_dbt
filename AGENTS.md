# AGENTS.md

## Contexte métier

ShopEasy est un distributeur fictif (e-commerce et magasins) en Europe et en Amérique du Nord.
Le domaine couvre les **clients**, les **commandes** (et leurs lignes) et les **produits**.
Toutes les données de ce dépôt sont fictives et générées par `scripts/generate_data.py`.

## Objectif

Migrer vers dbt le chargement d'entrepôt aujourd'hui réalisé avec Oracle Data Integrator (ODI) :

- les définitions ODI de référence sont dans `odi_export/` (4 mappings et 1 package) ;
- les sources brutes sont les seeds `raw_*` (schéma `raw`) ;
- les résultats produits par ODI sont les seeds `odi_results/odi_target_*` (schéma `odi_legacy`),
  qui servent de référence pour le recettage de la migration.

La cible est une architecture en trois couches : `models/bronze`, `models/silver`, `models/gold`
(schémas respectifs `bronze`, `silver`, `gold`).

## Règles de travail

- Les modèles dbt ne sont pas encore écrits : `models/` est volontairement vide.
- Le recettage compare les modèles dbt aux seeds `odi_target_*`, colonne par colonne (`audit_helper`).
- Les skills et instructions d'agent propres au projet vont dans `.agents/skills/`.
- Ne jamais committer `profiles.yml` : la connexion est gérée par dbt platform.

## Langue

- Documentation, descriptions de modèles et de colonnes (YAML), commentaires, messages de commit
  et de PR : **français**.
- Noms d'objets (modèles, colonnes, macros) : anglais, en `snake_case`.
