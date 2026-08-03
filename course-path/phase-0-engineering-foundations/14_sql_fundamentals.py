"""
0.14 - SQL Fundamentals: joins, grouping, indexes, NULLs and fan-out.

Runnable: `python 14_sql_fundamentals.py`
Requires: nothing outside the standard library. sqlite3 ships with Python,
so there is no server to install, no port to bind, no credentials to manage.

SAFE + OFFLINE: builds ONE throwaway SQLite database file inside a fresh
tempfile.mkdtemp() directory and deletes that whole directory in a finally
block. It opens no socket, and it never touches a database, container or
service already running on this machine.

What this proves practically:
  1. INNER JOIN silently DROPS the rows a report most needs. Counted:
     400 vendors go in, 340 come out, and the 60 missing ones are the
     dormant vendors procurement was asking about.
  2. WHERE filters ROWS before grouping; HAVING filters GROUPS after.
     Swapping them returns a different answer with no error at all.
  3. One index turns SCAN into SEARCH. The same 200 lookups are timed
     before and after, with the real EXPLAIN QUERY PLAN printed both times.
  4. The same index makes writes slower and the file bigger. Both measured
     on identical row sets, so the trade is visible in both directions.
  5. NULL is not a value. NULL = NULL is not true, COUNT(col) skips NULLs,
     SUM over no rows is NULL, and NOT IN over a NULL returns nothing.
  6. A JOIN that fans out multiplies every SUM downstream of it. Measured
     against the true total, then fixed by aggregating before joining.
  7. Wrapping an indexed column in a function throws the index away, and
     the query plan says so out loud.
"""

import os
import random
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import date, timedelta

SEP = "=" * 70

# Seeded so every count in the output is reproducible. Only the timings
# move between runs; the row counts, plans and ratios do not.
RNG_SEED = 20240614
N_VENDORS = 400
N_DORMANT = 60                 # vendors that never sent an invoice
N_ACTIVE = N_VENDORS - N_DORMANT
N_INVOICES = 50_000
N_WRITE_ROWS = 40_000          # for the write-cost measurement
N_LOOKUPS = 200                # for the read-cost measurement

WORDS = [
    "Acme", "Borealis", "Cedar", "Delta", "Everest", "Fulcrum", "Granite",
    "Halcyon", "Ionis", "Juniper", "Kestrel", "Lumen", "Meridian", "Nimbus",
    "Onyx", "Pinnacle", "Quarry", "Ridgeline", "Summit", "Tundra",
]
COUNTRIES = ["IN", "DE", "US", "SG", "BR"]


# ============================================================ small helpers
def one(conn, sql, params=()):
    """First column of the first row. Most of these demos return one number."""
    return conn.execute(sql, params).fetchone()[0]


def rows(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()


def qplan(conn, sql, params=()):
    """The REAL query plan, straight from SQLite.

    EXPLAIN QUERY PLAN is the single most useful debugging tool in SQL and
    every engine has an equivalent (Postgres: EXPLAIN ANALYZE, which 0.15
    uses). SCAN means "read every row". SEARCH means "jump straight to the
    matching rows through an index". Reading this beats guessing.
    """
    out = []
    for r in conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall():
        out.append(r[3])                       # the human-readable 'detail'
    return out


def show_plan(conn, sql, params=(), label=""):
    for line in qplan(conn, sql, params):
        print(f"    {label}{line}")


def db_bytes(conn):
    """Size of the database in bytes, from SQLite's own page accounting.

    More honest than os.path.getsize during a run, because pages are not
    necessarily flushed to the file yet.
    """
    return one(conn, "PRAGMA page_count") * one(conn, "PRAGMA page_size")


def human(n_bytes):
    return f"{n_bytes / 1_048_576:.2f} MB"


# ============================================================== build the db
def build_db(path):
    """A small ERP-shaped schema: vendors, invoices, invoice lines.

    This is deliberately the same domain as capstone C1 (predicting invoice
    payment delay), because the SQL that assembles a training table is where
    most tabular ML bugs are actually born - not in the model.
    """
    conn = sqlite3.connect(path)
    # Autocommit off at the driver level: transactions are managed by hand
    # below so the write-cost demo measures inserts, not fsyncs.
    conn.isolation_level = None

    conn.executescript("""
        CREATE TABLE vendors (
            vendor_id   INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            country     TEXT,               -- deliberately NULL for some
            tier        TEXT NOT NULL
        );
        CREATE TABLE invoices (
            invoice_id  INTEGER PRIMARY KEY,
            vendor_id   INTEGER NOT NULL REFERENCES vendors(vendor_id),
            issued_on   TEXT    NOT NULL,   -- 'YYYY-MM-DD', sorts correctly
            amount      REAL    NOT NULL,
            status      TEXT    NOT NULL,   -- PAID / OPEN / DISPUTED
            paid_on     TEXT               -- NULL until it is actually paid
        );
        CREATE TABLE invoice_lines (
            line_id     INTEGER PRIMARY KEY,
            invoice_id  INTEGER NOT NULL REFERENCES invoices(invoice_id),
            sku         TEXT    NOT NULL,
            line_amount REAL    NOT NULL
        );
    """)

    rng = random.Random(RNG_SEED)

    # -- vendors ----------------------------------------------------------
    # vendor_id 1..N_ACTIVE send invoices. The last N_DORMANT never do, and
    # those are exactly the rows an INNER JOIN will delete from the report.
    vendors = []
    for vid in range(1, N_VENDORS + 1):
        name = f"{WORDS[(vid * 7) % len(WORDS)]}-{vid:03d}"
        # ~8% have no country on file. Real master data always looks like
        # this, and it is why the NULL demo is not a toy.
        country = None if vid % 13 == 0 else COUNTRIES[vid % len(COUNTRIES)]
        tier = "STRATEGIC" if vid <= 40 else ("PREFERRED" if vid <= 160
                                              else "STANDARD")
        vendors.append((vid, name, country, tier))

    # -- invoices ---------------------------------------------------------
    # Zipf-ish skew: a few vendors send most of the invoices, which is what
    # real spend data looks like and what makes indexes worth measuring.
    active = list(range(1, N_ACTIVE + 1))
    weights = [1.0 / (r ** 0.8) for r in active]
    picks = rng.choices(active, weights=weights, k=N_INVOICES)

    start = date(2023, 1, 1)
    invoices, lines = [], []
    line_id = 0
    for inv_id, vendor_id in enumerate(picks, start=1):
        issued = start + timedelta(days=rng.randrange(1095))   # 3 years
        amount = round(rng.lognormvariate(7.0, 0.9), 2)
        roll = rng.random()
        if roll < 0.70:
            status = "PAID"
            paid = issued + timedelta(days=rng.randrange(3, 75))
            paid_on = paid.isoformat()
        elif roll < 0.94:
            status, paid_on = "OPEN", None
        else:
            status, paid_on = "DISPUTED", None
        invoices.append((inv_id, vendor_id, issued.isoformat(), amount,
                         status, paid_on))

        # 1-4 line items per invoice, splitting the invoice amount EXACTLY.
        # Exact splitting matters: it lets Demo 6 prove the fan-out fix is
        # right, because the corrected number must land on the true total.
        k = rng.choices((1, 2, 3, 4), weights=(40, 30, 20, 10))[0]
        part = round(amount / k, 2)
        for j in range(k):
            line_id += 1
            val = part if j < k - 1 else round(amount - part * (k - 1), 2)
            lines.append((line_id, inv_id, f"SKU-{rng.randrange(1, 900):03d}",
                          val))

    conn.execute("BEGIN")
    conn.executemany("INSERT INTO vendors VALUES (?,?,?,?)", vendors)
    conn.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?)", invoices)
    conn.executemany("INSERT INTO invoice_lines VALUES (?,?,?,?)", lines)
    conn.execute("COMMIT")
    return conn, len(lines)


# ===================================================================== 1
def demo_join_shapes(conn):
    print(SEP)
    print("DEMO 1 - INNER JOIN silently DROPS rows. Counted, not asserted.")
    print(SEP)

    n_vendors = one(conn, "SELECT COUNT(*) FROM vendors")
    n_invoices = one(conn, "SELECT COUNT(*) FROM invoices")

    inner = one(conn, """
        SELECT COUNT(*) FROM vendors v
        JOIN invoices i ON i.vendor_id = v.vendor_id""")
    left = one(conn, """
        SELECT COUNT(*) FROM vendors v
        LEFT JOIN invoices i ON i.vendor_id = v.vendor_id""")

    print(f"  vendors table                    : {n_vendors:>7,}")
    print(f"  invoices table                   : {n_invoices:>7,}")
    print(f"  vendors INNER JOIN invoices      : {inner:>7,} rows")
    print(f"  vendors LEFT  JOIN invoices      : {left:>7,} rows"
          f"   (+{left - inner})")
    print(f"  the +{left - inner} are vendors with NO invoice. INNER JOIN "
          f"deleted them.")

    # The report a procurement team actually asks for: spend per vendor.
    inner_groups = one(conn, """
        SELECT COUNT(*) FROM (
            SELECT v.vendor_id
            FROM vendors v JOIN invoices i ON i.vendor_id = v.vendor_id
            GROUP BY v.vendor_id)""")
    left_groups = one(conn, """
        SELECT COUNT(*) FROM (
            SELECT v.vendor_id
            FROM vendors v LEFT JOIN invoices i ON i.vendor_id = v.vendor_id
            GROUP BY v.vendor_id)""")
    print(f"\n  'spend per vendor' report, INNER : {inner_groups} vendors")
    print(f"  'spend per vendor' report, LEFT  : {left_groups} vendors")
    print("  Nothing errors. The report is just quietly missing the vendors")
    print("  with zero spend - usually the exact ones being asked about.")

    # Second trap, hiding inside the fix: COUNT(*) counts the OUTER row that
    # LEFT JOIN manufactured, so a vendor with no invoices reports 1.
    print("\n  And the trap inside the fix - LEFT JOIN + COUNT(*):")
    print(f"    {'vendor':<16}{'COUNT(*)':>10}{'COUNT(i.invoice_id)':>22}"
          f"{'SUM(i.amount)':>16}")
    for r in rows(conn, """
        SELECT v.name, COUNT(*), COUNT(i.invoice_id), SUM(i.amount)
        FROM vendors v
        LEFT JOIN invoices i ON i.vendor_id = v.vendor_id
        GROUP BY v.vendor_id, v.name
        HAVING COUNT(i.invoice_id) = 0
        ORDER BY v.vendor_id
        LIMIT 3"""):
        print(f"    {r[0]:<16}{r[1]:>10}{r[2]:>22}{str(r[3]):>16}")
    print("    COUNT(*) says 1 invoice. COUNT(i.invoice_id) says 0. The 0 is")
    print("    correct: COUNT(col) skips NULLs, COUNT(*) counts rows. And")
    print("    SUM over no rows is None, not 0 - COALESCE(SUM(...), 0).")


# ===================================================================== 2
def demo_where_vs_having(conn):
    print(SEP)
    print("DEMO 2 - WHERE filters ROWS. HAVING filters GROUPS. Not the same.")
    print(SEP)

    # The skip-test query: join two tables, keep only groups with > 5 rows.
    correct = """
        SELECT v.name, COUNT(*) AS n, ROUND(SUM(i.amount), 2) AS value
        FROM vendors v
        JOIN invoices i ON i.vendor_id = v.vendor_id
        WHERE i.status = 'DISPUTED'
          AND i.issued_on >= '2024-01-01'
          AND i.issued_on <  '2025-01-01'
        GROUP BY v.vendor_id, v.name
        HAVING COUNT(*) > 5
        ORDER BY n DESC, v.name
    """
    got = rows(conn, correct)
    print("  CORRECT - predicate in WHERE, aggregate test in HAVING:")
    print("    WHERE status='DISPUTED' AND issued_on in 2024")
    print("    GROUP BY vendor  HAVING COUNT(*) > 5")
    print(f"    -> {len(got)} vendors qualify. Top 3:")
    for r in got[:3]:
        print(f"       {r[0]:<16} n={r[1]:<5} disputed value={r[2]:>12,.2f}")

    # The same predicates moved into HAVING. SQLite ACCEPTS this: a bare
    # column in HAVING resolves to an arbitrary row of the group. No error,
    # no warning, completely different numbers.
    swapped = """
        SELECT v.name, COUNT(*) AS n, ROUND(SUM(i.amount), 2) AS value
        FROM vendors v
        JOIN invoices i ON i.vendor_id = v.vendor_id
        GROUP BY v.vendor_id, v.name
        HAVING COUNT(*) > 5
           AND i.status = 'DISPUTED'
           AND i.issued_on >= '2024-01-01'
           AND i.issued_on <  '2025-01-01'
        ORDER BY n DESC, v.name
    """
    try:
        bad = rows(conn, swapped)
        print("\n  WRONG - same predicates moved into HAVING:")
        print(f"    -> {len(bad)} vendors, and the counts are not the same "
              f"number at all:")
        for r in bad[:3]:
            print(f"       {r[0]:<16} n={r[1]:<5} 'disputed' value="
                  f"{r[2]:>12,.2f}")
        print("    It ran. No error. The counts now include EVERY invoice for")
        print("    that vendor - all statuses, all three years - because the")
        print("    grouping happened before the filter ever applied.")
    except sqlite3.OperationalError as e:
        print(f"\n  WRONG - same predicates moved into HAVING -> {e}")

    # And the mirror-image mistake: an aggregate in WHERE. This one is loud.
    try:
        rows(conn, """
            SELECT v.vendor_id, COUNT(*)
            FROM vendors v JOIN invoices i ON i.vendor_id = v.vendor_id
            WHERE COUNT(*) > 5
            GROUP BY v.vendor_id""")
    except sqlite3.OperationalError as e:
        print(f"\n  WHERE COUNT(*) > 5   -> OperationalError: {e}")
        print("    WHERE runs BEFORE the rows are grouped, so no count exists")
        print("    yet. That is the whole rule, and it is why HAVING exists.")


# ===================================================================== 3
def demo_index_reads(conn, rng):
    print(SEP)
    print("DEMO 3 - one index: SCAN becomes SEARCH. Timed both ways.")
    print(SEP)

    lookup = "SELECT COUNT(*), SUM(amount) FROM invoices WHERE vendor_id = ?"
    ids = [rng.randrange(1, N_ACTIVE + 1) for _ in range(N_LOOKUPS)]

    def run_workload():
        for vid in ids:
            conn.execute(lookup, (vid,)).fetchone()

    run_workload()                       # warm the page cache FIRST, so the
                                         # no-index number is as good as it
                                         # gets. This makes the measured
                                         # speedup conservative, not inflated.
    t0 = time.perf_counter()
    run_workload()
    before = time.perf_counter() - t0

    print(f"  query: {lookup}")
    print(f"  plan BEFORE the index:")
    show_plan(conn, lookup, (1,))
    print(f"  {N_LOOKUPS} lookups, no index : {before*1000:8.1f} ms"
          f"   ({before/N_LOOKUPS*1e6:6.0f} us each)")

    size_before = db_bytes(conn)
    t0 = time.perf_counter()
    conn.execute("CREATE INDEX idx_inv_vendor ON invoices(vendor_id)")
    build_ms = (time.perf_counter() - t0) * 1000
    size_after = db_bytes(conn)

    run_workload()                       # warm again, same treatment
    t0 = time.perf_counter()
    run_workload()
    after = time.perf_counter() - t0

    print(f"\n  plan AFTER  the index:")
    show_plan(conn, lookup, (1,))
    print(f"  {N_LOOKUPS} lookups, indexed  : {after*1000:8.1f} ms"
          f"   ({after/N_LOOKUPS*1e6:6.0f} us each)")
    print(f"\n  read speedup       : {before/after:.1f}x")
    print(f"  index build time   : {build_ms:.0f} ms (one time)")
    print(f"  database grew      : {human(size_before)} -> "
          f"{human(size_after)}  (+{human(size_after - size_before)})")
    print("  SCAN reads all 50,000 rows and throws almost all of them away.")
    print("  SEARCH walks a sorted B-tree straight to the matching rows.")
    print("  This is the same mechanism behind a WHERE tenant_id = ? filter")
    print("  in 5.7 and 7.13 - without it, isolation is also a full scan.")


# ===================================================================== 4
def demo_index_writes(conn):
    print(SEP)
    print("DEMO 4 - the other direction: what that index costs on writes.")
    print(SEP)

    # Three fresh copies of each table so the insert can be repeated and the
    # BEST time taken. Best-of-3 removes OS scheduling and disk-flush noise;
    # a single run of this measurement swings by 40% on a laptop.
    cols = ("id INTEGER PRIMARY KEY, vendor_id INTEGER, issued_on TEXT, "
            "amount REAL, status TEXT")
    for k in range(3):
        conn.execute(f"CREATE TABLE plain_{k} ({cols})")
        conn.execute(f"CREATE TABLE idxed_{k} ({cols})")
        # Three indexes on columns a report would filter and join on. Each
        # one is a second sorted copy that every INSERT must also update.
        conn.execute(f"CREATE INDEX ix_v_{k} ON idxed_{k}(vendor_id)")
        conn.execute(f"CREATE INDEX ix_d_{k} ON idxed_{k}(issued_on)")
        conn.execute(f"CREATE INDEX ix_s_{k} ON idxed_{k}(status, vendor_id)")

    # IDENTICAL rows into both shapes, so the only difference is the indexes.
    rng = random.Random(99)
    payload = [
        (i, rng.randrange(1, N_ACTIVE + 1),
         (date(2023, 1, 1) + timedelta(days=rng.randrange(1095))).isoformat(),
         round(rng.lognormvariate(7.0, 0.9), 2),
         rng.choice(("PAID", "OPEN", "DISPUTED")))
        for i in range(1, N_WRITE_ROWS + 1)
    ]

    def bulk_insert(table):
        pages0 = one(conn, "PRAGMA page_count")
        conn.execute("BEGIN")
        t0 = time.perf_counter()
        conn.executemany(f"INSERT INTO {table} VALUES (?,?,?,?,?)", payload)
        conn.execute("COMMIT")
        return time.perf_counter() - t0, one(conn, "PRAGMA page_count") - pages0

    plain_runs = [bulk_insert(f"plain_{k}") for k in range(3)]
    idx_runs = [bulk_insert(f"idxed_{k}") for k in range(3)]
    plain_t = min(t for t, _ in plain_runs)
    idx_t = min(t for t, _ in idx_runs)
    plain_pages = plain_runs[0][1]
    idx_pages = idx_runs[0][1]
    page_size = one(conn, "PRAGMA page_size")

    print(f"  {N_WRITE_ROWS:,} identical rows, one transaction, best of 3:")
    print(f"    no indexes        : {plain_t*1000:8.1f} ms"
          f"   ({N_WRITE_ROWS/plain_t:>9,.0f} rows/sec)")
    print(f"    three indexes     : {idx_t*1000:8.1f} ms"
          f"   ({N_WRITE_ROWS/idx_t:>9,.0f} rows/sec)")
    print(f"    write slowdown    : {idx_t/plain_t:.2f}x")
    print(f"\n  storage for the same rows:")
    print(f"    no indexes        : {human(plain_pages * page_size)}"
          f"  ({plain_pages:,} pages)")
    print(f"    three indexes     : {human(idx_pages * page_size)}"
          f"  ({idx_pages:,} pages)")
    print(f"    index overhead    : "
          f"{human((idx_pages - plain_pages) * page_size)}")
    print("\n  That is the entire trade, in both directions and on one screen:")
    print("  an index is a second sorted copy of a column. Reads jump to a")
    print("  position instead of scanning; every INSERT, UPDATE and DELETE")
    print("  must keep that copy sorted, and it occupies real bytes.")
    print("  Index the columns you filter and join on. Not the rest.")


# ===================================================================== 5
def demo_nulls(conn):
    print(SEP)
    print("DEMO 5 - NULL is not a value. It is 'unknown', and it spreads.")
    print(SEP)

    r = conn.execute(
        "SELECT NULL = NULL, NULL <> NULL, NULL IS NULL, 1 = NULL"
    ).fetchone()
    print(f"  SELECT NULL = NULL   -> {r[0]}      (not true - UNKNOWN)")
    print(f"  SELECT NULL <> NULL  -> {r[1]}      (also not true)")
    print(f"  SELECT NULL IS NULL  -> {r[2]}         (IS NULL is the only test)")
    print(f"  SELECT 1 = NULL      -> {r[3]}      (any comparison to NULL)")

    total = one(conn, "SELECT COUNT(*) FROM invoices")
    paid = one(conn, "SELECT COUNT(paid_on) FROM invoices")
    vend = one(conn, "SELECT COUNT(*) FROM vendors")
    ctry = one(conn, "SELECT COUNT(country) FROM vendors")
    print(f"\n  COUNT(*)         on invoices : {total:>7,}")
    print(f"  COUNT(paid_on)   on invoices : {paid:>7,}"
          f"   ({total - paid:,} unpaid rows skipped)")
    print(f"  COUNT(*)         on vendors  : {vend:>7,}")
    print(f"  COUNT(country)   on vendors  : {ctry:>7,}"
          f"   ({vend - ctry} vendors have no country on file)")
    print("  COUNT(col) counts NON-NULL values. COUNT(*) counts rows. If a")
    print("  'coverage' metric uses the wrong one, it is silently wrong.")

    # A filter that quietly deletes rows: unpaid invoices have paid_on NULL,
    # and NULL fails EVERY comparison, so they vanish from BOTH sides of a
    # supposedly exhaustive split. This is how a reconciliation loses money.
    a = one(conn, "SELECT COUNT(*) FROM invoices WHERE paid_on <  '2025-01-01'")
    b = one(conn, "SELECT COUNT(*) FROM invoices WHERE paid_on >= '2025-01-01'")
    print(f"\n  WHERE paid_on <  '2025-01-01' : {a:>7,}")
    print(f"  WHERE paid_on >= '2025-01-01' : {b:>7,}")
    print(f"  the two branches sum to       : {a + b:>7,}"
          f"  of {total:,} rows")
    print(f"  {total - a - b:,} rows are in NEITHER branch - every unpaid"
          f" invoice.")
    print("  'A or not A' does not partition a table that contains NULLs.")

    empty = one(conn, "SELECT SUM(amount) FROM invoices WHERE vendor_id = -1")
    empty_c = one(conn,
                  "SELECT COALESCE(SUM(amount), 0) FROM invoices "
                  "WHERE vendor_id = -1")
    print(f"\n  SUM over zero rows           : {empty}   <- not 0")
    print(f"  COALESCE(SUM(...), 0)        : {empty_c}      <- the fix")

    # NOT IN against a subquery containing NULL: the classic silent zero.
    conn.executescript("""
        CREATE TABLE blocked_vendors (vendor_id INTEGER);
        INSERT INTO blocked_vendors VALUES (1), (2), (3), (NULL);
    """)
    in_n = one(conn, """
        SELECT COUNT(*) FROM invoices
        WHERE vendor_id IN (SELECT vendor_id FROM blocked_vendors)""")
    notin_n = one(conn, """
        SELECT COUNT(*) FROM invoices
        WHERE vendor_id NOT IN (SELECT vendor_id FROM blocked_vendors)""")
    notin_fixed = one(conn, """
        SELECT COUNT(*) FROM invoices
        WHERE vendor_id NOT IN (
            SELECT vendor_id FROM blocked_vendors WHERE vendor_id IS NOT NULL)
        """)
    not_exists = one(conn, """
        SELECT COUNT(*) FROM invoices i
        WHERE NOT EXISTS (SELECT 1 FROM blocked_vendors b
                          WHERE b.vendor_id = i.vendor_id)""")
    print(f"\n  blocked_vendors holds 1, 2, 3 and one NULL (a bad import):")
    print(f"    vendor_id IN     (subquery)            : {in_n:>7,}")
    print(f"    vendor_id NOT IN (subquery)            : {notin_n:>7,}"
          f"   <- ZERO ROWS")
    print(f"    NOT IN (subquery WHERE id IS NOT NULL) : {notin_fixed:>7,}")
    print(f"    NOT EXISTS (correlated)                : {not_exists:>7,}")
    print("  NOT IN expands to id<>1 AND id<>2 AND id<>3 AND id<>NULL. That")
    print("  last term is UNKNOWN for every row, so nothing is ever TRUE.")
    print("  IN survives it; NOT IN does not. Prefer NOT EXISTS by default.")


# ===================================================================== 6
def demo_fanout(conn):
    print(SEP)
    print("DEMO 6 - a JOIN that fans out multiplies every SUM after it.")
    print(SEP)

    where = "i.status = 'PAID' AND i.issued_on >= '2025-01-01'"

    true_total = one(conn, f"SELECT SUM(amount) FROM invoices i WHERE {where}")
    true_count = one(conn, f"SELECT COUNT(*) FROM invoices i WHERE {where}")

    joined = conn.execute(f"""
        SELECT COUNT(*), SUM(i.amount)
        FROM invoices i
        JOIN invoice_lines l ON l.invoice_id = i.invoice_id
        WHERE {where}""").fetchone()

    # The fix: aggregate the many-side FIRST, then join one row to one row.
    fixed = conn.execute(f"""
        WITH per_invoice AS (
            SELECT invoice_id, SUM(line_amount) AS lines_total, COUNT(*) AS n
            FROM invoice_lines
            GROUP BY invoice_id
        )
        SELECT COUNT(*), SUM(i.amount), SUM(p.lines_total)
        FROM invoices i
        JOIN per_invoice p ON p.invoice_id = i.invoice_id
        WHERE {where}""").fetchone()

    print(f"  invoices matching the filter                 : {true_count:>7,}")
    print(f"  SUM(amount) straight from invoices           : "
          f"{true_total:>15,.2f}")
    print(f"\n  after JOIN invoice_lines (1..4 lines each):")
    print(f"    rows                                       : {joined[0]:>7,}"
          f"   ({joined[0]/true_count:.2f}x)")
    print(f"    SUM(i.amount)                              : "
          f"{joined[1]:>15,.2f}")
    print(f"    inflation                                  : "
          f"{joined[1]/true_total:>15.2f}x")
    print(f"    overstated by                              : "
          f"{joined[1]-true_total:>15,.2f}")
    print("  Nothing is broken. The join duplicated each invoice row once per")
    print("  line item, and SUM faithfully added the same amount 1-4 times.")
    print("\n  FIX - aggregate the many-side in a CTE, then join 1-to-1:")
    print(f"    rows                                       : {fixed[0]:>7,}")
    print(f"    SUM(i.amount)                              : "
          f"{fixed[1]:>15,.2f}")
    print(f"    SUM(per-invoice line totals)               : "
          f"{fixed[2]:>15,.2f}")
    print(f"    difference vs the true total               : "
          f"{abs(fixed[1]-true_total):>15,.2f}")
    print("  Both corrected numbers land on the true total. The line totals")
    print("  agree because each invoice was split exactly across its lines.")
    print("  Rule of thumb: the instant a JOIN can match more than one row,")
    print("  every aggregate downstream of it is suspect until proven.")
    print("  Check the row count before and after a join. Every time.")


# ===================================================================== 7
def demo_sargable(conn):
    print(SEP)
    print("DEMO 7 - a function around an indexed column throws the index away")
    print("         - and SEARCH is not automatically faster than SCAN.")
    print(SEP)

    conn.execute("CREATE INDEX idx_inv_issued ON invoices(issued_on)")
    total = one(conn, "SELECT COUNT(*) FROM invoices")

    def bench(sql, repeat=15):
        conn.execute(sql).fetchone()                      # warm the cache
        t0 = time.perf_counter()
        for _ in range(repeat):
            out = conn.execute(sql).fetchone()
        return out, (time.perf_counter() - t0) / repeat * 1000

    # -- part A: same answer, one query can use the index and one cannot ---
    wrapped = ("SELECT COUNT(*), SUM(amount) FROM invoices "
               "WHERE strftime('%Y-%m', issued_on) = '2024-03'")
    ranged = ("SELECT COUNT(*), SUM(amount) FROM invoices "
              "WHERE issued_on >= '2024-03-01' AND issued_on < '2024-04-01'")
    w_out, w_ms = bench(wrapped)
    r_out, r_ms = bench(ranged)

    w_label = "strftime('%Y-%m', issued_on) = '2024-03'"
    r_label = "issued_on >= '2024-03-01' AND < '2024-04-01'"
    print("  A - the SAME month, asked two ways:")
    print(f"    {'predicate':<46}{'plan':<8}{'ms/run':>9}")
    print(f"    {w_label:<46}"
          f"{qplan(conn, wrapped)[0].split()[0]:<8}{w_ms:>9.2f}")
    print(f"    {r_label:<46}"
          f"{qplan(conn, ranged)[0].split()[0]:<8}{r_ms:>9.2f}")
    print(f"    identical answers: {w_out == r_out}"
          f"   ({w_out[0]:,} rows)   ->  {w_ms/r_ms:.1f}x")
    print("    The index stores issued_on, NOT strftime(issued_on), so the")
    print("    first form can never use it at any selectivity. Same trap in")
    print("    LOWER(email) = ?, CAST(id AS TEXT) = ?, amount * 1.2 > 100.")
    print("    Keep the indexed column bare on one side of the comparison.")

    # -- part B: same predicate, index allowed vs forbidden ----------------
    # NOT INDEXED forbids SQLite from using any index on this table, so this
    # is the SAME query measured with and without the index. Nothing else
    # differs - which is the only way to attribute the difference to it.
    windows = [
        ("1 month",   "2024-03-01", "2024-04-01"),
        ("12 months", "2024-01-01", "2025-01-01"),
        ("36 months", "2023-01-01", "2026-01-01"),
    ]
    print("\n  B - the SAME range predicate, index allowed vs forbidden:")
    print(f"    {'window':<11}{'rows':>8}{'% table':>9}{'SEARCH':>10}"
          f"{'SCAN':>10}   verdict")
    for label, lo, hi in windows:
        base = ("SELECT COUNT(*), SUM(amount) FROM invoices{hint} "
                f"WHERE issued_on >= '{lo}' AND issued_on < '{hi}'")
        idx_out, idx_ms = bench(base.format(hint=""))
        scan_out, scan_ms = bench(base.format(hint=" NOT INDEXED"))
        assert idx_out == scan_out, "the two forms must agree"
        if idx_ms < scan_ms:
            verdict = f"index wins {scan_ms/idx_ms:.1f}x"
        else:
            verdict = f"SCAN wins {idx_ms/scan_ms:.1f}x"
        print(f"    {label:<11}{idx_out[0]:>8,}{idx_out[0]/total*100:>8.1f}%"
              f"{idx_ms:>10.2f}{scan_ms:>10.2f}   {verdict}")

    print("\n  SEARCH is not a synonym for fast. Each index hit costs a B-tree")
    print("  descent plus a jump back to the row, so once the predicate")
    print("  matches a large fraction of the table, reading the table in")
    print("  order is cheaper. Indexes pay off on SELECTIVE predicates.")
    print("  The plan tells you WHAT the engine did; only a clock tells you")
    print("  whether it helped. 0.15's EXPLAIN ANALYZE reports both at once.")


def main():
    tmpdir = tempfile.mkdtemp(prefix="sql_fundamentals_")
    path = os.path.join(tmpdir, "erp.db")
    conn = None
    try:
        t0 = time.perf_counter()
        conn, n_lines = build_db(path)
        build_ms = (time.perf_counter() - t0) * 1000

        print(f"python {sys.version.split()[0]} | "
              f"sqlite {sqlite3.sqlite_version}")
        print(f"throwaway db: {path}")
        print(f"vendors {one(conn, 'SELECT COUNT(*) FROM vendors'):,} | "
              f"invoices {one(conn, 'SELECT COUNT(*) FROM invoices'):,} | "
              f"lines {n_lines:,} | {human(db_bytes(conn))} | "
              f"built in {build_ms:.0f} ms")

        rng = random.Random(RNG_SEED)
        demo_join_shapes(conn)
        demo_where_vs_having(conn)
        demo_index_reads(conn, rng)
        demo_index_writes(conn)
        demo_nulls(conn)
        demo_fanout(conn)
        demo_sargable(conn)

        print(SEP)
        print("Every wrong answer above ran without an error message. That is")
        print("what makes SQL bugs expensive: the query succeeds, the number")
        print("is plausible, and it reaches a dashboard, a training set (C1)")
        print("or an agent tool result (6.13) before anyone checks it.")
        print(SEP)
    finally:
        if conn is not None:
            conn.close()
        # Everything this script created lived in one temp directory.
        shutil.rmtree(tmpdir, ignore_errors=True)
        print(f"temp database deleted: {not os.path.exists(tmpdir)}")


if __name__ == "__main__":
    main()
