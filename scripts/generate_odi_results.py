#!/usr/bin/env python3
"""Calcule le résultat des 4 mappings ODI (odi_export/MAP_*.xml) à partir des seeds raw_*.

Écrit seeds/odi_results/odi_target_*.csv : les tables cibles ODI de référence pour le recettage.
Bibliothèque standard uniquement ; arithmétique décimale avec arrondi Oracle (ROUND : moitié
éloignée de zéro).

Usage : python scripts/generate_odi_results.py [répertoire_seeds] [répertoire_sortie]
"""
import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEEDS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "seeds"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else SEEDS / "odi_results"

CENT = Decimal("0.01")


# ----------------------------------------------------------------- fonctions Oracle
def nvl(v, default):
    return default if v is None else v


def trim(s):
    return None if s is None else s.strip(" ")


def upper(s):
    return None if s is None else s.upper()


def oracle_round(x: Decimal, places=2) -> Decimal:
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def decode(expr, *args):
    """DECODE(expr, s1, r1, s2, r2, ..., défaut) ; NULL = NULL est vrai en DECODE."""
    pairs, default = args[:-1], args[-1]
    for i in range(0, len(pairs), 2):
        if expr == pairs[i]:
            return pairs[i + 1]
    return default


def sign(x: Decimal) -> int:
    return (x > 0) - (x < 0)


# --------------------------------------------------------------------- lecture seeds
def read(name):
    with open(SEEDS / f"{name}.csv", newline="", encoding="utf-8") as f:
        return [{k: (v if v != "" else None) for k, v in row.items()} for row in csv.DictReader(f)]


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, Decimal):
        return f"{v:.2f}"
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"odi_target_{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([fmt(r[h]) for h in header])
    print(f"{path.name}: {len(rows)} lignes")


# ------------------------------------------------------------------------- mappings
def map_dim_customer():
    countries = {c["country_id"]: c for c in read("raw_countries")}
    rows = []
    for c in read("raw_customers"):
        co = countries.get(c["country_id"]) if c["country_id"] else None  # jointure externe gauche
        rows.append({
            "c": c, "co": co or {},
            "email_key": upper(trim(c["email"])),
            "last_upd": datetime.fromisoformat(c["last_update_ts"]),
            "cid": int(c["customer_id"]),
        })
    # ROW_NUMBER() OVER (PARTITION BY UPPER(TRIM(EMAIL)) ORDER BY LAST_UPDATE_TS DESC, CUSTOMER_ID DESC)
    groups = defaultdict(list)
    for r in rows:
        groups[r["email_key"]].append(r)
    today = date.today()  # SYSDATE
    out = []
    for grp in groups.values():
        grp.sort(key=lambda r: (r["last_upd"], r["cid"]), reverse=True)
        r = grp[0]  # RN = 1
        c, co = r["c"], r["co"]
        signup = date.fromisoformat(c["signup_date"])
        if not signup <= today:
            continue
        out.append({
            "customer_id": r["cid"],
            "first_name": nvl(upper(trim(c["first_name"])), "UNKNOWN"),
            "last_name": nvl(upper(trim(c["last_name"])), "UNKNOWN"),
            "email": r["email_key"],
            "country_code": nvl(upper(trim(co.get("country_code"))), "XX"),
            "country_name": nvl(upper(trim(co.get("country_name"))), "UNKNOWN"),
            "region": nvl(upper(trim(co.get("region"))), "N/A"),
            "signup_date": signup,
            "customer_segment": decode(upper(trim(c["loyalty_tier"])),
                                       "A", "GOLD", "B", "SILVER", "C", "BRONZE", "STANDARD"),
        })
    out.sort(key=lambda r: r["customer_id"])
    write("dim_customer", ["customer_id", "first_name", "last_name", "email", "country_code",
                           "country_name", "region", "signup_date", "customer_segment"], out)


def map_dim_product():
    group_map = ("LAPTOPS", "ELECTRONICS", "PHONES", "ELECTRONICS", "TABLETS", "ELECTRONICS",
                 "HEADPHONES", "ELECTRONICS", "SOFAS", "HOME", "LAMPS", "HOME", "TABLES", "HOME",
                 "SHOES", "FASHION", "JACKETS", "FASHION", "T-SHIRTS", "FASHION", "OTHER")
    out = []
    for p in read("raw_products"):
        price = Decimal(p["unit_price"])
        sku = upper(trim(p["sku"]))
        out.append({
            "product_id": int(p["product_id"]),
            "sku": sku,
            "product_name": trim(p["product_name"]),
            "category_code": sku[:3],  # SUBSTR(sku, 1, 3)
            "category_group": decode(upper(trim(p["category"])), *group_map),
            "catalog_price": price,
            "cost_price": Decimal(p["cost_price"]),
            "is_premium": decode(sign(price - 200), -1, "N", "Y"),
        })
    out.sort(key=lambda r: r["product_id"])
    write("dim_product", ["product_id", "sku", "product_name", "category_code", "category_group",
                          "catalog_price", "cost_price", "is_premium"], out)


def map_fct_order_line():
    orders = {o["order_id"]: o for o in read("raw_orders")}
    products = {p["product_id"]: p for p in read("raw_products")}
    out = []
    for ol in read("raw_order_lines"):
        o, p = orders.get(ol["order_id"]), products.get(ol["product_id"])
        if o is None or p is None:  # jointures internes
            continue
        if o["status"] == "CANCELLED":  # filtre STATUS <> 'CANCELLED'
            continue
        qty = int(ol["quantity"])
        unit = Decimal(ol["unit_price"])
        disc = Decimal(nvl(ol["discount_pct"], "0"))
        net_exact = qty * unit * (1 - disc / 100)
        ts = datetime.fromisoformat(o["order_ts"])
        out.append({
            "order_line_id": int(ol["order_line_id"]),
            "order_id": int(o["order_id"]),
            "customer_id": int(o["customer_id"]),
            "product_id": int(ol["product_id"]),
            "order_date": ts.date(),  # TRUNC(ORDER_TS)
            "order_month": ts.strftime("%Y-%m"),  # TO_CHAR(ORDER_DATE, 'YYYY-MM')
            "order_status": o["status"],
            "quantity": qty,
            "unit_price": unit,
            "discount_pct": disc,
            "net_amount": oracle_round(net_exact),
            "margin_vs_catalog": oracle_round(net_exact - qty * Decimal(p["unit_price"])),
        })
    out.sort(key=lambda r: r["order_line_id"])
    write("fct_order_line", ["order_line_id", "order_id", "customer_id", "product_id", "order_date",
                             "order_month", "order_status", "quantity", "unit_price", "discount_pct",
                             "net_amount", "margin_vs_catalog"], out)
    return out


def map_fct_product_monthly_sales(lines):
    groups = defaultdict(list)
    for r in lines:
        groups[(r["product_id"], r["order_month"])].append(r)
    out = []
    for (pid, month), g in groups.items():
        total_qty = sum(r["quantity"] for r in g)
        if total_qty < 5:  # HAVING SUM(QUANTITY) >= 5
            continue
        out.append({
            "product_id": pid,
            "order_month": month,
            "total_quantity": total_qty,
            "total_net_amount": sum((r["net_amount"] for r in g), Decimal(0)),
            "order_count": len({r["order_id"] for r in g}),
            "avg_unit_price": oracle_round(sum((r["unit_price"] for r in g), Decimal(0)) / len(g)),
        })
    out.sort(key=lambda r: (r["product_id"], r["order_month"]))
    write("fct_product_monthly_sales", ["product_id", "order_month", "total_quantity",
                                        "total_net_amount", "order_count", "avg_unit_price"], out)


if __name__ == "__main__":
    map_dim_customer()
    map_dim_product()
    fct_lines = map_fct_order_line()
    map_fct_product_monthly_sales(fct_lines)
