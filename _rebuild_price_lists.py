import os
import sqlite3

DB = "pricecompro.db"
assert os.path.exists(DB), f"DB file not found: {DB}"

conn = sqlite3.connect(DB)
cur  = conn.cursor()

def table_exists(name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def column_names(table: str) -> list[str]:
    cur.execute(f"PRAGMA table_info({table});")
    return [r[1] for r in cur.fetchall()]

print("Opening DB:", DB)
cur.execute("PRAGMA foreign_keys=OFF;")
cur.execute("BEGIN;")

if not table_exists("currencies"):
    print("Creating table: currencies")
    cur.execute("""
    CREATE TABLE currencies (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        iso_code VARCHAR(8) NOT NULL UNIQUE,
        symbol_left VARCHAR(8),
        symbol_right VARCHAR(8),
        decimals INTEGER NOT NULL DEFAULT 2,
        rate FLOAT NOT NULL DEFAULT 1.0,
        is_primary BOOLEAN NOT NULL DEFAULT 0,
        active BOOLEAN NOT NULL DEFAULT 1
    );
    """)

if not table_exists("price_lists"):
    raise SystemExit("price_lists table not found")

cols = column_names("price_lists")
if "default_currency_id" in cols:
    print(" default_currency_id")
else:
    print("Rebuilding table: price_lists (default_currency_id)")

    # 1.1)   
    cur.execute("ALTER TABLE price_lists RENAME TO _price_lists_old;")

    # 1.2)      
    cur.execute("""
    CREATE TABLE price_lists (
        id INTEGER PRIMARY KEY,
        supplier_id INTEGER NOT NULL,
        name VARCHAR(200) NOT NULL,
        source_type VARCHAR(6) NOT NULL,
        source_config JSON,
        format VARCHAR(32),
        mapping JSON,
        schedule VARCHAR(128),
        last_run_at DATETIME,
        last_status VARCHAR(64),
        active BOOLEAN NOT NULL,
        default_currency_id INTEGER,
        FOREIGN KEY(default_currency_id) REFERENCES currencies(id) ON DELETE SET NULL
    );
    """)

    # 1.3)   (  )
    cur.execute("""
    INSERT INTO price_lists
    (id, supplier_id, name, source_type, source_config, format, mapping, schedule, last_run_at, last_status, active)
    SELECT id, supplier_id, name, source_type, source_config, format, mapping, schedule, last_run_at, last_status, active
    FROM _price_lists_old;
    """)

    # 1.4)  
    cur.execute("DROP TABLE _price_lists_old;")

cur.execute("COMMIT;")
cur.execute("PRAGMA foreign_keys=ON;")

#  
cur.execute("PRAGMA table_info(price_lists);")
print("price_lists columns:", [r[1] for r in cur.fetchall()])

conn.close()
print("Done.")
