#!/usr/bin/env python3
"""
=============================================================================
  ONE-SHOT DATABASE MIGRATION SCRIPT
  Old Schema (EAN/goods_code) → New Schema (SKU-based)
=============================================================================

This script migrates an old-format GreaterWMS SQLite database to the new
SKU-based schema. It is IDEMPOTENT: safe to run multiple times. It detects
which steps have already been applied and skips them.

Tables affected:
  1. goods      → Add sku_code column (EAN→SKU mapping)
  2. sku        → Create if not exists (Global SKU registry)
  3. asndetail  → Rename goods_code→sku_code, goods_desc→sku_desc, goods_cost→sku_cost
  4. dndetail   → Rename goods_code→sku_code, goods_desc→sku_desc
  5. pickinglist→ Rename goods_code→sku_code, goods_desc→sku_desc (add if missing)
  6. stocklist  → Rename goods_code→sku_code, goods_desc→sku_desc
  7. stockbin   → Rename goods_code→sku_code, goods_desc→sku_desc

After schema migration, it also performs DATA migration:
  - Populates goods.sku_code from the sku table
  - Maps EAN values in dndetail/pickinglist/stocklist/stockbin to real SKU codes

Usage:
  .venv/bin/python migrate_old_db.py [path_to_db]
  
  If no path is given, defaults to db.sqlite3
=============================================================================
"""

import sqlite3
import sys
import os
import shutil
from datetime import datetime

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else 'db.sqlite3'

def get_columns(cursor, table):
    """Return a set of column names for a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}

def table_exists(cursor, table):
    """Check if a table exists."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

def rename_column_sqlite(cursor, table, old_name, new_name, col_type="VARCHAR(255)", default="''"):
    """
    Rename a column in SQLite (which didn't support ALTER TABLE RENAME COLUMN until 3.25).
    Uses the safe ADD+COPY+DROP approach for maximum compatibility.
    If old column doesn't exist, skip. If new column already exists, skip.
    """
    columns = get_columns(cursor, table)
    if new_name in columns:
        print(f"  ✓ {table}.{new_name} already exists, skipping rename")
        return False
    if old_name not in columns:
        print(f"  ⚠ {table}.{old_name} not found (and {new_name} not found), adding {new_name}")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} {col_type} NOT NULL DEFAULT {default}")
        return True
    
    # Use ALTER TABLE RENAME COLUMN (SQLite 3.25+)
    try:
        cursor.execute(f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}")
        print(f"  ✓ Renamed {table}.{old_name} → {new_name}")
        return True
    except Exception:
        # Fallback: add new column, copy data, can't drop old in SQLite easily
        print(f"  ⚠ RENAME COLUMN not supported, using ADD+COPY fallback")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_name} {col_type} NOT NULL DEFAULT {default}")
        cursor.execute(f"UPDATE {table} SET {new_name} = {old_name}")
        print(f"  ✓ Added {table}.{new_name} and copied data from {old_name}")
        return True

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database file not found: {DB_PATH}")
        sys.exit(1)

    # Create backup
    backup_path = DB_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(DB_PATH, backup_path)
    print(f"✓ Backup created: {backup_path}")
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable WAL mode for better performance
    cursor.execute("PRAGMA journal_mode=WAL")

    # =========================================================================
    # STEP 1: Create 'sku' table if it doesn't exist
    # =========================================================================
    print("=" * 60)
    print("STEP 1: Create 'sku' table (Global SKU registry)")
    print("=" * 60)
    if table_exists(cursor, 'sku'):
        print("  ✓ 'sku' table already exists")
    else:
        cursor.execute("""
            CREATE TABLE sku (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku_code VARCHAR(255) NOT NULL UNIQUE,
                sku_desc VARCHAR(255) NOT NULL DEFAULT '',
                sku_cost REAL NOT NULL DEFAULT 0,
                creater VARCHAR(255) NOT NULL DEFAULT '',
                openid VARCHAR(255) NOT NULL DEFAULT '',
                is_delete BOOLEAN NOT NULL DEFAULT 0,
                create_time DATETIME NOT NULL DEFAULT (datetime('now')),
                update_time DATETIME
            )
        """)
        print("  ✓ Created 'sku' table")
    conn.commit()
    print()

    # =========================================================================
    # STEP 2: Add 'sku_code' column to 'goods' table
    # =========================================================================
    print("=" * 60)
    print("STEP 2: Add 'sku_code' column to 'goods' table")
    print("=" * 60)
    goods_cols = get_columns(cursor, 'goods')
    if 'sku_code' in goods_cols:
        print("  ✓ goods.sku_code already exists")
    else:
        cursor.execute("ALTER TABLE goods ADD COLUMN sku_code VARCHAR(255) NOT NULL DEFAULT ''")
        print("  ✓ Added goods.sku_code column")
    conn.commit()
    print()

    # =========================================================================
    # STEP 3: Migrate 'asndetail' table
    # =========================================================================
    print("=" * 60)
    print("STEP 3: Migrate 'asndetail' (goods_code→sku_code, etc.)")
    print("=" * 60)
    rename_column_sqlite(cursor, 'asndetail', 'goods_code', 'sku_code')
    rename_column_sqlite(cursor, 'asndetail', 'goods_desc', 'sku_desc')
    rename_column_sqlite(cursor, 'asndetail', 'goods_cost', 'sku_cost', col_type="REAL", default="0")
    conn.commit()
    print()



    # =========================================================================
    # STEP 6: Migrate 'stocklist' table
    # =========================================================================
    print("=" * 60)
    print("STEP 6: Migrate 'stocklist' (goods_code→sku_code, etc.)")
    print("=" * 60)
    rename_column_sqlite(cursor, 'stocklist', 'goods_code', 'sku_code')
    rename_column_sqlite(cursor, 'stocklist', 'goods_desc', 'sku_desc')
    conn.commit()
    print()

    # =========================================================================
    # STEP 7: Migrate 'stockbin' table
    # =========================================================================
    print("=" * 60)
    print("STEP 7: Migrate 'stockbin' (goods_code→sku_code, etc.)")
    print("=" * 60)
    rename_column_sqlite(cursor, 'stockbin', 'goods_code', 'sku_code')
    # stockbin may or may not have goods_desc/sku_desc
    stockbin_cols = get_columns(cursor, 'stockbin')
    if 'sku_desc' not in stockbin_cols and 'goods_desc' not in stockbin_cols:
        cursor.execute("ALTER TABLE stockbin ADD COLUMN sku_desc VARCHAR(255) NOT NULL DEFAULT ''")
        print("  ✓ Added stockbin.sku_desc column (was missing)")
    else:
        rename_column_sqlite(cursor, 'stockbin', 'goods_desc', 'sku_desc')
    # stockbin keeps goods_cost as goods_cost (not renamed)
    conn.commit()
    print()

    # =========================================================================
    # STEP 8: Ensure 'dndetail' has custom columns
    # =========================================================================
    print("=" * 60)
    print("STEP 8: Ensure 'dndetail' has custom columns")
    print("=" * 60)
    dndetail_cols = get_columns(cursor, 'dndetail')
    custom_cols = {
        'orderitem_id': ("VARCHAR(255)", "''"),
        'account_name': ("VARCHAR(255)", "''"),
        'labeloffer_id': ("VARCHAR(255)", "''"),
        'label_id': ("VARCHAR(255)", "''"),
        'labelprocess_id': ("VARCHAR(255)", "''"),
        'dn_complete': ("INTEGER", "2"),
        'revenue_counted': ("BOOLEAN", "0"),
        'sending_date': ("DATETIME", "(datetime('now'))"),
        'stock_qty': ("BIGINT", "0"),
    }
    for col, (col_type, default) in custom_cols.items():
        if col not in dndetail_cols:
            cursor.execute(f"ALTER TABLE dndetail ADD COLUMN {col} {col_type} NOT NULL DEFAULT {default}")
            print(f"  ✓ Added dndetail.{col}")
        else:
            print(f"  ✓ dndetail.{col} already exists")
    conn.commit()
    print()

    # =========================================================================
    # STEP 9: DATA MIGRATION - Populate goods.sku_code from sku table
    # =========================================================================
    print("=" * 60)
    print("STEP 9: DATA MIGRATION - Link goods.sku_code ↔ sku table")
    print("=" * 60)
    # For goods records that have sku_code='', try to find a matching sku record
    # The goods.goods_code is the EAN. The sku table has sku_code.
    # We need to find EAN→SKU mappings. If goods already has sku_code set, skip.
    cursor.execute("SELECT COUNT(*) FROM goods WHERE sku_code = '' OR sku_code IS NULL")
    unmapped_goods = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM goods")
    total_goods = cursor.fetchone()[0]
    print(f"  Total goods records: {total_goods}")
    print(f"  Goods without sku_code: {unmapped_goods}")
    
    if unmapped_goods > 0:
        # Try to auto-populate: if goods_code itself is a valid sku_code in the sku table
        cursor.execute("""
            UPDATE goods 
            SET sku_code = (SELECT s.sku_code FROM sku s WHERE s.sku_code = goods.goods_code LIMIT 1)
            WHERE (sku_code = '' OR sku_code IS NULL)
              AND EXISTS (SELECT 1 FROM sku s WHERE s.sku_code = goods.goods_code)
        """)
        direct_mapped = cursor.rowcount
        print(f"  ✓ Direct-mapped {direct_mapped} goods (goods_code = sku_code)")

        # For remaining unmapped goods, set sku_code = goods_code as fallback
        cursor.execute("""
            UPDATE goods SET sku_code = goods_code 
            WHERE sku_code = '' OR sku_code IS NULL
        """)
        fallback_mapped = cursor.rowcount
        if fallback_mapped > 0:
            print(f"  ✓ Fallback-mapped {fallback_mapped} goods (sku_code = goods_code)")
    else:
        print("  ✓ All goods already have sku_code set")
    conn.commit()
    print()

    # =========================================================================
    # STEP 10: DATA MIGRATION - Populate sku table from goods
    # =========================================================================
    print("=" * 60)
    print("STEP 10: DATA MIGRATION - Populate sku table from goods")
    print("=" * 60)
    cursor.execute("SELECT COUNT(*) FROM sku")
    existing_skus = cursor.fetchone()[0]
    print(f"  Existing SKU records: {existing_skus}")

    # Insert unique sku_code values from goods that don't exist in sku yet
    cursor.execute("""
        INSERT OR IGNORE INTO sku (sku_code, sku_desc, sku_cost, creater, openid, is_delete, create_time)
        SELECT DISTINCT 
            g.sku_code, 
            g.goods_desc,
            g.goods_cost,
            g.creater,
            g.openid,
            0,
            datetime('now')
        FROM goods g
        WHERE g.sku_code != '' 
          AND g.sku_code IS NOT NULL
          AND g.is_delete = 0
          AND NOT EXISTS (SELECT 1 FROM sku s WHERE s.sku_code = g.sku_code)
    """)
    new_skus = cursor.rowcount
    print(f"  ✓ Inserted {new_skus} new SKU records from goods table")
    conn.commit()
    print()



    # =========================================================================
    # STEP 13: DATA MIGRATION - Map EAN→SKU in stocklist
    # =========================================================================
    print("=" * 60)
    print("STEP 13: DATA MIGRATION - Map EAN→SKU in stocklist")
    print("=" * 60)
    cursor.execute("""
        UPDATE stocklist 
        SET sku_code = (
            SELECT g.sku_code FROM goods g 
            WHERE g.goods_code = stocklist.sku_code 
              AND g.sku_code != '' AND g.sku_code != g.goods_code
            LIMIT 1
        ),
        sku_desc = COALESCE(
            (SELECT g.goods_desc FROM goods g 
             WHERE g.goods_code = stocklist.sku_code 
               AND g.sku_code != '' AND g.sku_code != g.goods_code
             LIMIT 1),
            stocklist.sku_desc
        )
        WHERE EXISTS (
            SELECT 1 FROM goods g 
            WHERE g.goods_code = stocklist.sku_code 
              AND g.sku_code != '' AND g.sku_code != g.goods_code
        )
    """)
    sl_mapped = cursor.rowcount
    print(f"  ✓ Mapped {sl_mapped} stocklist records from EAN to SKU")
    conn.commit()
    print()

    # =========================================================================
    # STEP 14: DATA MIGRATION - Map EAN→SKU in stockbin
    # =========================================================================
    print("=" * 60)
    print("STEP 14: DATA MIGRATION - Map EAN→SKU in stockbin")
    print("=" * 60)
    cursor.execute("""
        UPDATE stockbin 
        SET sku_code = (
            SELECT g.sku_code FROM goods g 
            WHERE g.goods_code = stockbin.sku_code 
              AND g.sku_code != '' AND g.sku_code != g.goods_code
            LIMIT 1
        ),
        sku_desc = COALESCE(
            (SELECT g.goods_desc FROM goods g 
             WHERE g.goods_code = stockbin.sku_code 
               AND g.sku_code != '' AND g.sku_code != g.goods_code
             LIMIT 1),
            stockbin.sku_desc
        )
        WHERE EXISTS (
            SELECT 1 FROM goods g 
            WHERE g.goods_code = stockbin.sku_code 
              AND g.sku_code != '' AND g.sku_code != g.goods_code
        )
    """)
    sb_mapped = cursor.rowcount
    print(f"  ✓ Mapped {sb_mapped} stockbin records from EAN to SKU")
    conn.commit()
    print()

    # =========================================================================
    # STEP 15: DATA MIGRATION - Map EAN→SKU in asndetail
    # =========================================================================
    print("=" * 60)
    print("STEP 15: DATA MIGRATION - Map EAN→SKU in asndetail")
    print("=" * 60)
    cursor.execute("""
        UPDATE asndetail 
        SET sku_code = (
            SELECT g.sku_code FROM goods g 
            WHERE g.goods_code = asndetail.sku_code 
              AND g.sku_code != '' AND g.sku_code != g.goods_code
            LIMIT 1
        ),
        sku_desc = COALESCE(
            (SELECT g.goods_desc FROM goods g 
             WHERE g.goods_code = asndetail.sku_code 
               AND g.sku_code != '' AND g.sku_code != g.goods_code
             LIMIT 1),
            asndetail.sku_desc
        )
        WHERE EXISTS (
            SELECT 1 FROM goods g 
            WHERE g.goods_code = asndetail.sku_code 
              AND g.sku_code != '' AND g.sku_code != g.goods_code
        )
    """)
    asn_mapped = cursor.rowcount
    print(f"  ✓ Mapped {asn_mapped} asndetail records from EAN to SKU")
    conn.commit()
    print()

    # =========================================================================
    # VERIFICATION
    # =========================================================================
    print("=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    # Check all tables have the right columns
    for table, expected_cols in [
        ('sku', ['sku_code', 'sku_desc', 'sku_cost']),
        ('goods', ['goods_code', 'sku_code', 'goods_desc']),
        ('asndetail', ['sku_code', 'sku_desc', 'sku_cost']),
        ('stocklist', ['sku_code', 'sku_desc']),
        ('stockbin', ['sku_code', 'sku_desc', 'goods_cost']),
    ]:
        cols = get_columns(cursor, table)
        missing = [c for c in expected_cols if c not in cols]
        if missing:
            print(f"  ✗ {table}: MISSING columns {missing}")
        else:
            print(f"  ✓ {table}: All required columns present")
    
    print()
    
    # Sample data check
    for table in ['stocklist', 'stockbin', 'asndetail']:
        cursor.execute(f"SELECT sku_code FROM {table} LIMIT 3")
        samples = [row[0] for row in cursor.fetchall()]
        print(f"  {table} samples: {samples}")
    
    print()
    cursor.execute("SELECT COUNT(*) FROM sku")
    print(f"  Total SKU records: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM goods WHERE sku_code != '' AND sku_code IS NOT NULL")
    print(f"  Goods with sku_code mapped: {cursor.fetchone()[0]}")

    conn.close()
    print()
    print("=" * 60)
    print("MIGRATION COMPLETE!")
    print(f"Backup saved at: {backup_path}")
    print("=" * 60)

if __name__ == '__main__':
    main()
