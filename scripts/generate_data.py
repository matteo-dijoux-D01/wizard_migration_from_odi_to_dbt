#!/usr/bin/env python3
"""Génère les seeds sources fictives ShopEasy (seeds/raw_*.csv).

Déterministe (graine fixe) et sans dépendance : bibliothèque standard uniquement.
Les CSV produits sont versionnés ; ce script n'est pas exécuté par dbt platform.

Défauts volontairement présents : espaces parasites, casse mixte, doublons clients
sur l'email, valeurs NULL (cellules vides), statuts variés.

Usage : python scripts/generate_data.py [répertoire_de_sortie]
"""
import csv
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

SEED = 20260101
N_BASE_CUSTOMERS = 185
N_DUPLICATES = 15
N_ORDERS = 800
TARGET_LINES = 2000
LAST_DAY = date(2026, 9, 30)

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "seeds"

rng = random.Random(SEED)

# --------------------------------------------------------------------------- pays
COUNTRIES = [
    ("FR", "France", "Western Europe"),
    ("DE", "Germany", "Western Europe"),
    ("ES", "Spain", "Southern Europe"),
    ("IT", "Italy", "Southern Europe"),
    ("GB", "United Kingdom", "Northern Europe"),
    ("BE", "Belgium", "Western Europe"),
    ("NL", "Netherlands", "Western Europe"),
    ("CH", "Switzerland", "Western Europe"),
    ("PT", "Portugal", "Southern Europe"),
    ("IE", "Ireland", "Northern Europe"),
    ("US", "United States", "North America"),
    ("CA", "Canada", "North America"),
    ("SE", "Sweden", "Northern Europe"),
    ("PL", "Poland", "Eastern Europe"),
    ("AT", "Austria", "Western Europe"),
]


def make_countries():
    rows = []
    for i, (code, name, region) in enumerate(COUNTRIES, start=1):
        # défauts : espaces, casse mixte
        if i == 2:
            name = name + " "
        if i == 5:
            name = name.upper()
        if i == 7:
            region = region.lower()
        if i == 9:
            region = " " + region
        if i == 12:
            code = code.lower()
        rows.append([i, code, name, region])
    return rows


# ------------------------------------------------------------------------ clients
FIRST = ["Camille", "Lucas", "Emma", "Hugo", "Lea", "Louis", "Chloe", "Jules", "Manon", "Arthur",
         "Sarah", "Nathan", "Ines", "Tom", "Julie", "Paul", "Laura", "Adam", "Clara", "Theo",
         "Anna", "Max", "Sofia", "Leon", "Mia", "Noah", "Eva", "Liam", "Zoe", "Marco"]
LAST = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy",
        "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux",
        "Vincent", "Fournier", "Muller", "Schmidt", "Rossi", "Smith", "Jones", "Brown", "Novak",
        "Silva", "Jansen", "Lindqvist"]
DOMAINS = ["example.com", "mail.test", "shopeasy-demo.org", "webmail.example", "inbox.test"]


def rand_date(lo: date, hi: date) -> date:
    return lo + timedelta(days=rng.randint(0, (hi - lo).days))


def rand_ts(lo: date, hi: date) -> datetime:
    d = rand_date(lo, hi)
    return datetime(d.year, d.month, d.day, rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))


def messy_text(value: str):
    """Applique un défaut de saisie aléatoire (espaces, casse)."""
    r = rng.random()
    if r < 0.10:
        return value.upper()
    if r < 0.18:
        return value.lower()
    if r < 0.26:
        return " " + value
    if r < 0.34:
        return value + "  "
    return value


def make_customers():
    rows = []
    used_emails = set()
    for cid in range(1, N_BASE_CUSTOMERS + 1):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        email = f"{first}.{last}{cid}@{rng.choice(DOMAINS)}".lower()
        used_emails.add(email)
        signup = rand_date(date(2023, 1, 1), date(2026, 3, 31))
        last_upd = rand_ts(signup, LAST_DAY)
        tier = rng.choice(["A", "B", "C", "C", None, None])
        if tier and rng.random() < 0.3:
            tier = tier.lower() if rng.random() < 0.5 else f" {tier} "
        country_id = rng.choices(range(1, 16), weights=[20, 12, 8, 8, 8, 5, 5, 4, 3, 3, 10, 5, 3, 3, 3])[0]
        rows.append({
            "customer_id": cid,
            "first_name": None if rng.random() < 0.02 else messy_text(first),
            "last_name": None if rng.random() < 0.03 else messy_text(last),
            "email": email,
            "country_id": None if rng.random() < 0.04 else country_id,
            "signup_date": signup,
            "loyalty_tier": tier,
            "last_update_ts": last_upd,
        })

    # doublons sur l'email (casse / espaces différents), nouveaux customer_id
    for k in range(N_DUPLICATES):
        src = rng.choice(rows[:N_BASE_CUSTOMERS])
        cid = N_BASE_CUSTOMERS + 1 + k
        mail = src["email"]
        variant = rng.choice(["upper", "pad", "title"])
        if variant == "upper":
            mail = mail.upper()
        elif variant == "pad":
            mail = f" {mail} "
        else:
            mail = mail.title()
        # la plupart des doublons sont plus récents, quelques-uns plus anciens
        if k % 5 == 4:
            new_ts = src["last_update_ts"] - timedelta(days=rng.randint(5, 120), hours=rng.randint(0, 20))
        else:
            span = max(1, (datetime.combine(LAST_DAY, datetime.min.time()) - src["last_update_ts"]).days)
            new_ts = src["last_update_ts"] + timedelta(days=rng.randint(1, span), minutes=rng.randint(1, 600))
            new_ts = min(new_ts, datetime(2026, 9, 30, 23, 59, 59))
        dup = dict(src)
        dup.update({
            "customer_id": cid,
            "email": mail,
            "last_update_ts": new_ts,
            "signup_date": min(src["signup_date"], new_ts.date()),
            "country_id": rng.choice([src["country_id"], rng.randint(1, 15)]),
        })
        rows.append(dup)
    return rows


# ---------------------------------------------------------------------- produits
CATALOG = [
    # (catégorie, préfixe SKU, nombre, prix min, prix max, noms)
    ("Laptops", "LAP", 4, 549, 1899, ["Aero 14", "Pro 16", "Slim 13", "Studio 15"]),
    ("Phones", "PHO", 4, 199, 1199, ["Nova S", "Nova Pro", "Lite 5G", "Max Ultra"]),
    ("Tablets", "TAB", 3, 179, 899, ["Tab Air", "Tab Pro", "Tab Mini"]),
    ("Headphones", "HDP", 4, 29, 349, ["Buds Go", "Over-Ear Studio", "Sport Fit", "Noise Cancel X"]),
    ("Sofas", "SOF", 3, 399, 1590, ["Oslo 3 places", "Milan Angle", "Lund 2 places"]),
    ("Lamps", "LMP", 3, 15, 129, ["Arc Floor", "Desk Led", "Pendant Round"]),
    ("Tables", "TBL", 3, 89, 699, ["Dining Oak", "Coffee Round", "Desk Pine"]),
    ("Shoes", "SHO", 4, 39, 189, ["Runner Light", "City Sneaker", "Leather Derby", "Trail Grip"]),
    ("Jackets", "JKT", 3, 59, 329, ["Parka Winter", "Rain Shell", "Denim Classic"]),
    ("T-Shirts", "TSH", 3, 9, 39, ["Basic Cotton", "Graphic Tee", "Polo Pique"]),
    ("Books", "BOK", 3, 7, 34, ["Atlas du Monde", "Cuisine Facile", "Roman Noir"]),
    ("Toys", "TOY", 3, 12, 89, ["Brick Set 500", "Puzzle 1000", "Robot Kit"]),
]


def money(x: float) -> Decimal:
    return Decimal(str(round(x, 2))).quantize(Decimal("0.01"))


def make_products():
    rows, pid = [], 0
    for cat, prefix, n, lo, hi, names in CATALOG:
        for i in range(n):
            pid += 1
            price = money(rng.uniform(lo, hi) // 1 + rng.choice([0.0, 0.49, 0.9, 0.99]))
            cost = money(float(price) * rng.uniform(0.55, 0.75))
            rows.append({
                "product_id": pid,
                "sku": f"{prefix}-{pid:03d}" if rng.random() > 0.1 else f"{prefix.lower()}-{pid:03d}",
                "product_name": messy_text(names[i]),
                "category": messy_text(cat),
                "unit_price": price,
                "cost_price": cost,
                "created_date": rand_date(date(2022, 6, 1), date(2024, 12, 31)),
            })
    # un produit sans catégorie
    rows[-2]["category"] = None
    return rows


# --------------------------------------------------------------- commandes, lignes
def make_orders(customers):
    signup = {c["customer_id"]: c["signup_date"] for c in customers}
    ids = list(signup)
    rows = []
    for oid in range(1, N_ORDERS + 1):
        cid = rng.choice(ids)
        lo = max(signup[cid], date(2025, 1, 1))
        ts = rand_ts(lo, LAST_DAY)
        status = rng.choices(["SHIPPED", "NEW", "CANCELLED", "RETURNED"], weights=[62, 12, 14, 12])[0]
        # les commandes récentes ont plus de chances d'être NEW
        if ts.date() > date(2026, 9, 10) and rng.random() < 0.5:
            status = "NEW"
        rows.append({
            "order_id": oid,
            "customer_id": cid,
            "order_ts": ts,
            "status": status,
            "channel": rng.choice(["WEB", "WEB", "MOBILE", "STORE", "web", " STORE", None]),
        })
    rows.sort(key=lambda r: (r["order_ts"], r["order_id"]))
    for new_id, r in enumerate(rows, start=1):  # numérotation chronologique
        r["order_id"] = new_id
    return rows


def make_order_lines(orders, products):
    rows, lid = [], 0
    pids = [p["product_id"] for p in products]
    price = {p["product_id"]: p["unit_price"] for p in products}
    weights = [1 + (i % 7) for i in range(len(pids))]  # popularité inégale
    for o in orders:
        n = rng.choices([1, 2, 3, 4, 5], weights=[26, 32, 22, 12, 8])[0]
        for pid in rng.sample(pids, n) if rng.random() < 0.5 else _weighted_unique(pids, weights, n):
            lid += 1
            unit = price[pid]
            if rng.random() < 0.25:  # prix différent du catalogue (promo / évolution)
                unit = money(float(unit) * rng.choice([0.9, 0.95, 1.05, 1.1]))
            disc = rng.choice([None, None, None, 0, 0, 5, 10, 10, 15, 20, 25])
            rows.append({
                "order_line_id": lid,
                "order_id": o["order_id"],
                "product_id": pid,
                "quantity": rng.choices([1, 2, 3, 4, 5], weights=[50, 25, 12, 8, 5])[0],
                "unit_price": unit,
                "discount_pct": disc,
            })
    return rows


def _weighted_unique(pids, weights, n):
    chosen = []
    pool = list(zip(pids, weights))
    while len(chosen) < n:
        pick = rng.choices(pool, weights=[w for _, w in pool])[0]
        chosen.append(pick[0])
        pool.remove(pick)
    return chosen


# ------------------------------------------------------------------------ écriture
def fmt(v):
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return f"{v:.2f}"
    return str(v)


def write_csv(name, header, rows):
    path = OUT / f"{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow([fmt(x) for x in (r if isinstance(r, list) else [r[h] for h in header])])
    print(f"{path.name}: {len(rows)} lignes")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    countries = make_countries()
    customers = make_customers()
    products = make_products()
    orders = make_orders(customers)
    lines = make_order_lines(orders, products)

    write_csv("raw_countries", ["country_id", "country_code", "country_name", "region"], countries)
    write_csv("raw_customers", ["customer_id", "first_name", "last_name", "email", "country_id",
                                "signup_date", "loyalty_tier", "last_update_ts"], customers)
    write_csv("raw_products", ["product_id", "sku", "product_name", "category", "unit_price",
                               "cost_price", "created_date"], products)
    write_csv("raw_orders", ["order_id", "customer_id", "order_ts", "status", "channel"], orders)
    write_csv("raw_order_lines", ["order_line_id", "order_id", "product_id", "quantity",
                                  "unit_price", "discount_pct"], lines)


if __name__ == "__main__":
    main()
