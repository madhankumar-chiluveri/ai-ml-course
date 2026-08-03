"""
0.15 - PostgreSQL from Python, pgvector, Redis.

Runnable: `python 15_postgres_pgvector_redis.py`
Requires: numpy. Everything else is the standard library (sqlite3).

SAFE + OFFLINE: creates throwaway SQLite files inside a tempfile.mkdtemp()
directory and deletes that directory in a finally block. It opens no
network socket, connects to no database server, touches no container, and
contains no real credential.

Postgres, pgvector and Redis are deliberately NOT contacted here. Each of
the three ideas is modelled locally with a faithful stand-in - SQLite for
the SQL layer, numpy for the vector layer, a virtual clock plus threads
for the rate-limit layer - and the companion .md carries the exact psycopg
and redis code for the real systems. Every number printed below is real;
what is modelled is labelled as modelled.

What this proves practically:
  1. An f-string SQL query is defeated by a 10-character payload. Row
     counts prove it: 1 row honest, 5 rows injected, 0 rows parameterised.
  2. A parameter is DATA and can never become SQL - which is also why it
     cannot name a table or a column. `ORDER BY ?` fails SILENTLY.
  3. Unit-normalising embeddings makes cosine similarity exactly a dot
     product - measured to 1e-7. Skipping it changes which rows win.
  4. An IVF-style index trades recall for speed. Both are measured:
     vectors scanned, milliseconds per query, and recall@10.
  5. A fixed-window rate limiter lets 2x the limit through across a
     window boundary. Counted. A sliding window and a token bucket do not.
  6. A per-process counter loses increments under threads AND multiplies
     the limit by the worker count. That is what Redis INCR/EXPIRE fixes.
  7. Opening a connection per request costs measurable time even for
     SQLite, which is the cheapest possible connection.
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import textwrap
import threading
import time

import numpy as np

SEP = "=" * 70

# Fake, obviously-not-real credentials. Never a live key in course code.
USERS = [
    ("alice", "hash$alice", "user", "alice@example.test"),
    ("bob", "hash$bob", "user", "bob@example.test"),
    ("carol", "hash$carol", "user", "carol@example.test"),
    ("dave", "hash$dave", "user", "dave@example.test"),
    ("admin", "hash$sup3rsecret", "admin", "admin@example.test"),
]


def make_users_db(path: str) -> sqlite3.Connection:
    """A tiny users table. SQLite stands in for Postgres here.

    The injection mechanics are identical in psycopg: the difference is
    only the placeholder character (? here, %s there). What matters is
    that the driver sends the query and the values as separate things.
    """
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE users ("
        " id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT,"
        " role TEXT, email TEXT)"
    )
    con.executemany(
        # Note: even the SETUP uses placeholders. There is no context in
        # which building SQL by concatenation is the convenient option.
        "INSERT INTO users (username, password_hash, role, email)"
        " VALUES (?, ?, ?, ?)",
        USERS,
    )
    con.commit()
    return con


# ===================================================================== 1
def demo_sql_injection(tmp: str) -> None:
    print(SEP)
    print("DEMO 1 - SQL injection, for real, in sqlite3")
    print(SEP)
    con = make_users_db(os.path.join(tmp, "inject.db"))

    honest = "alice"
    payload = "' OR '1'='1"           # 11 characters, and that is the whole
    #                                   attack. No tooling required.

    # ---- the WRONG way -------------------------------------------------
    # The username is pasted into the SQL text. The database has no way to
    # know which characters came from the developer and which came from
    # the internet, because by the time it arrives they are one string.
    def lookup_fstring(name):
        # The newline is only so the printed SQL fits the page. It changes
        # nothing: SQL does not care, and neither does the attack.
        sql = ("SELECT username, role, email FROM users\n"
               f"          WHERE username = '{name}'")
        return sql, con.execute(sql).fetchall()

    sql_ok, rows_ok = lookup_fstring(honest)
    sql_bad, rows_bad = lookup_fstring(payload)

    print("  f-string query, honest input:")
    print(f"    SQL : {sql_ok}")
    print(f"    rows: {len(rows_ok)}  -> {rows_ok}")
    print("\n  f-string query, input = \"' OR '1'='1\"")
    print(f"    SQL : {sql_bad}")
    print(f"    rows: {len(rows_bad)}  <- EVERY user row, including admin")
    for r in rows_bad:
        print(f"          {r}")

    # ---- the login bypass, which is the version that actually hurts ----
    def login_fstring(name, password):
        sql = ("SELECT username, role FROM users\n"
               f"          WHERE username = '{name}'"
               f" AND password_hash = '{password}'")
        return sql, con.execute(sql).fetchall()

    sql_l, rows_l = login_fstring("admin' --", "wrong-password")
    print("\n  login check, username = \"admin' --\", password = wrong:")
    print(f"    SQL : {sql_l}")
    print(f"    rows: {len(rows_l)} -> {rows_l}")
    print("    The -- comments out the password test. Logged in as admin")
    print("    without ever knowing the password.")

    # ---- the RIGHT way -------------------------------------------------
    # The driver sends "SELECT ... WHERE username = ?" and the value in a
    # separate field. The server parses the query FIRST, then binds the
    # value into an already-parsed slot. The value cannot change the shape
    # of the statement because parsing is already finished.
    def lookup_param(name):
        return con.execute(
            "SELECT username, role, email FROM users WHERE username = ?",
            (name,),                          # a TUPLE - see the trap below
        ).fetchall()

    print("\n  parameterised query, same payload:")
    print("    SQL : SELECT ... WHERE username = ?   params: (\"' OR '1'='1\",)")
    print(f"    rows: {len(lookup_param(payload))}  <- the payload was treated"
          " as a username")
    print(f"    rows for the honest input: {len(lookup_param(honest))}")
    print("    Nothing was escaped, sanitised or stripped. The payload was")
    print("    simply never SQL.")

    # A classic trap worth seeing once: forgetting the comma. A bare string
    # is a SEQUENCE of characters, so the driver sees 11 parameters.
    try:
        con.execute("SELECT * FROM users WHERE username = ?", (payload))
    except (sqlite3.ProgrammingError, ValueError) as e:
        print(f"\n  params=(payload), comma forgotten -> "
              f"{type(e).__name__}:")
        for line in textwrap.wrap(str(e), 56):
            print(f"    {line}")
    con.close()

    # ---- and it is not only about reading ------------------------------
    con2 = make_users_db(os.path.join(tmp, "drop.db"))
    drop_payload = "x'; DROP TABLE users; --"
    sql_drop = f"SELECT * FROM users WHERE username = '{drop_payload}'"
    try:
        con2.execute(sql_drop)
    except sqlite3.ProgrammingError as e:
        print(f"\n  \"x'; DROP TABLE users; --\" via execute() -> "
              f"{type(e).__name__}")
        print(f"    {str(e)[:60]}")
        print("    sqlite3's execute() happens to refuse multiple statements.")
        print("    That is a property of THIS driver, not a defence. Drivers")
        print("    and ORMs that allow multi-statement do exactly this:")
    # executescript is what a multi-statement-capable path looks like.
    con2.executescript(sql_drop)
    tables = con2.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"    tables remaining after the same string ran: {tables}")
    con2.close()


# ===================================================================== 2
def demo_parameters_are_data(tmp: str) -> None:
    print(SEP)
    print("DEMO 2 - a parameter is DATA, so it cannot name a table or column")
    print(SEP)
    con = make_users_db(os.path.join(tmp, "params.db"))

    # 2a. Values that would need escaping round-trip byte for byte.
    nasty = """O'Brien "quoted" ; DROP -- \\ %s {} \x00tail"""
    con.execute(
        "INSERT INTO users (username, password_hash, role, email)"
        " VALUES (?, ?, ?, ?)", (nasty, "h", "user", "n@example.test"))
    con.commit()
    back = con.execute(
        "SELECT username FROM users WHERE username = ?", (nasty,)
    ).fetchone()[0]
    print(f"  stored a username containing quotes, a semicolon, a comment")
    print(f"  marker, a backslash, a %s and a NUL byte: {len(nasty)} chars")
    print(f"  read back identical: {back == nasty}   (length {len(back)})")
    print("  No escaping happened. The bytes never entered the SQL text.")

    # 2b. The limit of placeholders. This is where people reach back for
    # f-strings and reintroduce the hole.
    rows_const = con.execute(
        "SELECT username FROM users ORDER BY ? LIMIT 4", ("email",)
    ).fetchall()
    rows_real = con.execute(
        "SELECT username FROM users ORDER BY email LIMIT 4").fetchall()
    print(f"\n  ORDER BY ?      with ('email',) -> "
          f"{[r[0] for r in rows_const]}")
    print(f"  ORDER BY email  (real identifier) -> "
          f"{[r[0] for r in rows_real]}")
    print("  The first sorted by the constant string 'email', which is the")
    print("  same for every row, so nothing sorted. No error. No warning.")
    print(f"  same result? {[r[0] for r in rows_const] == [r[0] for r in rows_real]}")

    # 2c. The fix: an allow-list. The user input SELECTS an identifier, it
    # never BECOMES one. Anything unrecognised is rejected, not escaped.
    SORTABLE = {"email": "email", "name": "username", "role": "role"}

    def list_users(sort_key: str):
        column = SORTABLE.get(sort_key)
        if column is None:
            raise ValueError(f"unsortable column: {sort_key!r}")
        # Safe: `column` is one of three literals THIS file wrote.
        return con.execute(
            f"SELECT username FROM users ORDER BY {column} LIMIT 4").fetchall()

    print(f"\n  allow-listed sort 'email' -> "
          f"{[r[0] for r in list_users('email')]}")
    try:
        list_users("email; DROP TABLE users; --")
    except ValueError as e:
        print(f"  allow-listed sort, payload supplied -> ValueError:")
        print(f"    {e}")
    print("  Three known-good literals. The attacker chooses among them;")
    print("  they never supply one. This pattern returns in 5.2 whenever a")
    print("  RAG filter lets the caller pick a metadata field to sort on.")
    con.close()


def top_k(sims: np.ndarray, k: int = 10) -> np.ndarray:
    """Indices of the k largest similarities, best first.

    argpartition is O(n) and only sorts the k that matter. Sorting all
    5000 to look at 10 is the most common accidental slowdown in a
    hand-written retriever (5.2).
    """
    k = min(k, sims.shape[0])
    idx = np.argpartition(sims, -k)[-k:]
    return idx[np.argsort(-sims[idx])]


def make_corpus(rng, n_vec, dim, n_topics, spread=1.0):
    """Unit-norm embeddings that CLUSTER, the way real ones do.

    Real sentence embeddings are not uniformly scattered on the sphere:
    documents about the same thing land near each other. That structure
    is the entire reason an approximate index can work at all, so a demo
    built on uniform noise would flatter nothing. Demo 4 measures the
    difference against uniform noise directly.
    """
    topics = rng.normal(size=(n_topics, dim)).astype(np.float32)
    topics /= np.linalg.norm(topics, axis=1)[:, None]
    topic_of = rng.integers(0, n_topics, size=n_vec)
    noise = rng.normal(size=(n_vec, dim)).astype(np.float32)
    noise /= np.linalg.norm(noise, axis=1)[:, None]
    vecs = topics[topic_of] + spread * noise
    vecs /= np.linalg.norm(vecs, axis=1)[:, None]
    return vecs.astype(np.float32), topic_of


# ===================================================================== 3
def demo_embeddings_and_cosine(state: dict) -> None:
    print(SEP)
    print("DEMO 3 - embeddings: why normalising makes cosine a dot product")
    print(SEP)
    rng = np.random.default_rng(0)
    n_vec, dim, n_topics = 5000, 384, 40   # 384 = the width of several small
    #                                        sentence-transformer models, and
    #                                        the number in vector(384).

    # float32 on purpose: pgvector's `vector` type stores float4, so this
    # is the memory layout the real table would use (5.2).
    unit, topic_of = make_corpus(rng, n_vec, dim, n_topics)

    nbytes = unit.nbytes
    print(f"  {n_vec} vectors x {dim} dims, float32 = "
          f"{nbytes:,} bytes ({nbytes/1024/1024:.2f} MiB)")
    print(f"  {n_topics} latent topics: mean similarity within a topic "
          f"{float((unit[topic_of == 0] @ unit[topic_of == 0].T).mean()):.3f},"
          f" across topics "
          f"{float((unit[topic_of == 0] @ unit[topic_of == 1].T).mean()):+.3f}")

    q_unit = unit[0]

    # cosine(a, b) = (a . b) / (|a| |b|). When both are unit length the
    # denominator is 1, so the whole similarity IS the dot product - one
    # matrix multiply instead of a multiply plus two norms plus a divide.
    cos_full = (unit @ q_unit) / (np.linalg.norm(unit, axis=1)
                                  * np.linalg.norm(q_unit))
    dot_only = unit @ q_unit
    print(f"\n  max |cosine - dot| over {n_vec} unit vectors: "
          f"{np.abs(cos_full - dot_only).max():.3e}")
    print("  They are the same number. That identity is why every vector")
    print("  store tells you to normalise before you insert.")

    # And the cost of skipping it. Give the SAME directions wildly
    # different magnitudes - which is what happens when vectors come from
    # documents of very different lengths, or from averaging token vectors.
    scale = np.exp(rng.normal(0.0, 0.9, size=n_vec)).astype(np.float32)
    raw = (unit * scale[:, None]).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1)
    print(f"\n  same directions, magnitudes now {norms.min():.2f} to "
          f"{norms.max():.2f} (median {np.median(norms):.2f})")

    q_raw = raw[0]
    raw_dot = top_k(raw @ q_raw)
    raw_cos = top_k((raw @ q_raw) / (norms * np.linalg.norm(q_raw)))
    overlap = len(set(raw_dot.tolist()) & set(raw_cos.tolist()))
    print(f"  top-10 by dot product vs top-10 by cosine: "
          f"{overlap}/10 rows in common")
    print("  Direction is what carries the meaning; magnitude is an")
    print("  artefact. An unnormalised dot product ranks by 'long and")
    print("  vaguely related' over 'short and exactly right'. Normalise on")
    print("  insert, then <=> and <#> agree and the fast one is safe.")

    state["unit"] = unit
    state["dim"] = dim
    state["n_vec"] = n_vec
    state["n_topics"] = n_topics


# ===================================================================== 4
def build_ivf(vecs, n_clusters, rng, iters=12):
    """Cluster once, then store each list CONTIGUOUSLY.

    The "inverted file" in IVF is literally this: rows physically grouped
    by cluster so probing one list is a sequential read. Packing them is
    not an optimisation detail, it is the data structure.
    """
    n = vecs.shape[0]
    centroids = vecs[rng.choice(n, n_clusters, replace=False)].copy()
    for _ in range(iters):                       # a few Lloyd iterations
        assign = (vecs @ centroids.T).argmax(axis=1)
        for c in range(n_clusters):
            members = vecs[assign == c]
            if len(members):
                v = members.sum(axis=0)
                centroids[c] = v / np.linalg.norm(v)
    assign = (vecs @ centroids.T).argmax(axis=1)
    order = np.argsort(assign, kind="stable")
    packed = np.ascontiguousarray(vecs[order])
    counts = np.bincount(assign, minlength=n_clusters)
    # Lloyd's algorithm can strand a centroid with zero members. Keeping
    # it would let a query probe an empty list and scan nothing - a real
    # bug this script hit. Drop empties; argsort grouped by ascending
    # cluster id, so removing zero-length runs leaves the offsets valid.
    keep = counts > 0
    centroids, counts = centroids[keep], counts[keep]
    starts = np.concatenate([[0], np.cumsum(counts)])
    return centroids, packed, order, starts, counts


def ivf_search(centroids, packed, order, starts, q, nprobe, k):
    """Return (neighbour ids, how many vectors were actually scanned)."""
    probe = top_k(centroids @ q, nprobe)
    sims, ids = [], []
    for c in probe:
        s, e = int(starts[c]), int(starts[c + 1])
        if e > s:
            sims.append(packed[s:e] @ q)     # a SLICE, not a copy
            ids.append(order[s:e])
    sims = np.concatenate(sims)
    ids = np.concatenate(ids)
    return ids[top_k(sims, k)], sims.shape[0]


def demo_ivf_tradeoff(state: dict) -> None:
    print(SEP)
    print("DEMO 4 - exact search vs an IVF index: speed bought with recall")
    print(SEP)
    unit = state["unit"]
    n_vec, dim, n_topics = state["n_vec"], state["dim"], state["n_topics"]
    rng = np.random.default_rng(1)
    n_q, k, n_clusters = 100, 10, 64

    # Queries that look like the corpus: drawn from the same topics. A
    # query nobody would ever ask is not a benchmark.
    queries, _ = make_corpus(rng, n_q, dim, n_topics)

    # ---- exact brute force --------------------------------------------
    # This is what Postgres does with a vector column and NO index: read
    # every row, compute every distance, sort. Perfect recall by
    # definition - it IS the definition.
    for q in queries[:5]:
        top_k(unit @ q)                        # warm up BLAS
    t0 = time.perf_counter()
    exact = [top_k(unit @ q, k) for q in queries]
    exact_ms = (time.perf_counter() - t0) / n_q * 1000
    print(f"  exact scan: {n_vec} vectors/query, {exact_ms:.3f} ms/query")
    print(f"              recall@10 = 1.000, by definition")

    t0 = time.perf_counter()
    centroids, packed, order, starts, counts = build_ivf(unit, n_clusters, rng)
    build_s = time.perf_counter() - t0
    print(f"  IVF build : {len(counts)} non-empty clusters in "
          f"{build_s:.2f} s, list sizes {counts.min()}-{counts.max()}")
    print("  An index is not free: build time, extra disk, and it drifts as")
    print("  rows are inserted. CREATE INDEX in 5.2 pays exactly this.")

    print("\n  nprobe  scanned/query  ms/query  speedup  recall@10")
    recall_at_4 = 0.0
    for nprobe in (1, 2, 4, 8, 16, 32):
        scanned_total, hits = 0, 0
        t0 = time.perf_counter()
        for qi, q in enumerate(queries):
            got, scanned = ivf_search(centroids, packed, order, starts,
                                      q, nprobe, k)
            scanned_total += scanned
            hits += len(set(got.tolist()) & set(exact[qi].tolist()))
        ms = (time.perf_counter() - t0) / n_q * 1000
        recall = hits / (n_q * k)
        if nprobe == 4:
            recall_at_4 = recall
        print(f"  {nprobe:>5}  {scanned_total/n_q:>13.0f}  {ms:>8.3f}"
              f"  {exact_ms/ms:>6.1f}x  {recall:>9.3f}")

    # ---- the assumption the whole index rests on -----------------------
    # Everything above works because similar rows sit near each other. Run
    # the identical index over vectors with no structure at all and watch
    # recall collapse: the index has not changed, the data has.
    flat = rng.normal(size=(n_vec, dim)).astype(np.float32)
    flat /= np.linalg.norm(flat, axis=1)[:, None]
    fq = rng.normal(size=(n_q, dim)).astype(np.float32)
    fq /= np.linalg.norm(fq, axis=1)[:, None]
    fc, fp, fo, fs, _ = build_ivf(flat, n_clusters, rng)
    hits = 0
    for q in fq:
        got, _ = ivf_search(fc, fp, fo, fs, q, 4, k)
        hits += len(set(got.tolist()) & set(top_k(flat @ q, k).tolist()))
    print(f"\n  same index, same nprobe=4, over UNIFORM random vectors:")
    print(f"    recall@10 = {hits/(n_q*k):.3f}   vs {recall_at_4:.3f} on the"
          f" clustered corpus above")
    print("  Approximate indexes are a bet that near things are stored")
    print("  together. Embeddings make that bet pay; noise does not.")
    print("\n  Read the table as a menu, not a ranking. 'Fast and 80% right'")
    print("  and 'slower and 99% right' are both legitimate products, and")
    print("  5.4 is where you measure which one your answers can afford.")


# ===================================================================== 5
def demo_rate_limit_boundary() -> None:
    print(SEP)
    print("DEMO 5 - the fixed-window boundary burst, counted")
    print(SEP)
    limit, window = 5, 1.0

    class FixedWindow:
        """Count per (key, window index). One INCR per request in Redis."""

        def __init__(self):
            self.counts = {}

        def allow(self, key, now):
            w = int(now // window)            # 0.99 -> window 0, 1.00 -> 1
            c = self.counts.get((key, w), 0)
            if c >= limit:
                return False
            self.counts[(key, w)] = c + 1
            return True

    class SlidingWindowLog:
        """Keep the timestamps themselves. Exact, but O(requests) memory."""

        def __init__(self):
            self.logs = {}

        def allow(self, key, now):
            log = self.logs.setdefault(key, [])
            cutoff = now - window
            while log and log[0] <= cutoff:
                log.pop(0)
            if len(log) >= limit:
                return False
            log.append(now)
            return True

    class TokenBucket:
        """Tokens refill continuously. Allows a burst, bounds the average."""

        def __init__(self):
            self.tokens, self.last = {}, {}

        def allow(self, key, now):
            tok = self.tokens.get(key, float(limit))
            tok = min(limit, tok + (now - self.last.get(key, now))
                      * (limit / window))
            self.last[key] = now
            ok = tok >= 1.0
            self.tokens[key] = tok - 1.0 if ok else tok
            return ok

    # A virtual clock, so this is deterministic and instant. Five requests
    # squeezed into the END of window 0, five into the START of window 1.
    arrivals = [0.90, 0.92, 0.94, 0.96, 0.98,
                1.00, 1.02, 1.04, 1.06, 1.08]

    def max_in_rolling_window(times):
        best = 0
        for i, t in enumerate(times):
            best = max(best, sum(1 for s in times[:i + 1] if s > t - window))
        return best

    print(f"  policy: {limit} requests per {window:.0f}.0s for one API key")
    print(f"  arrivals (s): {arrivals}")
    print("  all 10 land inside a 0.18s span that straddles t=1.0\n")
    print("  limiter              allowed  denied  max in any rolling 1.0s")
    for name, lim in (("fixed window", FixedWindow()),
                      ("sliding window log", SlidingWindowLog()),
                      ("token bucket", TokenBucket())):
        allowed = [t for t in arrivals if lim.allow("key:abc", t)]
        peak = max_in_rolling_window(allowed)
        flag = "  <- 2x THE LIMIT" if peak > limit else ""
        print(f"  {name:<20} {len(allowed):>7}  {len(arrivals)-len(allowed):>6}"
              f"  {peak:>6}{flag}")

    print("\n  The fixed window is not buggy code - it is doing exactly what")
    print("  it says. Its counter resets at t=1.0, so the caller gets a")
    print("  fresh allowance 0.02s after spending the previous one. Any")
    print("  caller who learns your window boundary gets 2x forever.")


# ===================================================================== 6
def demo_shared_state() -> None:
    print(SEP)
    print("DEMO 6 - what Redis adds: atomicity, shared state, and TTL")
    print(SEP)

    # 6a. ATOMICITY. A dict counter is a read, then a write. Anything that
    # can run between those two steps can lose an increment.
    def hammer(store, key, n, lock=None):
        for _ in range(n):
            if lock:
                with lock:
                    store[key] = store.get(key, 0) + 1
            else:
                cur = store.get(key, 0)
                time.sleep(0)      # yields - models the gap a real check
                #                    has while it waits on the network
                store[key] = cur + 1

    threads_n, per_thread = 8, 300
    expected = threads_n * per_thread

    racy = {}
    ts = [threading.Thread(target=hammer, args=(racy, "k", per_thread))
          for _ in range(threads_n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    safe, lock = {}, threading.Lock()
    ts = [threading.Thread(target=hammer, args=(safe, "k", per_thread, lock))
          for _ in range(threads_n)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()

    print(f"  {threads_n} threads x {per_thread} increments, expected "
          f"{expected}")
    print(f"    read-then-write, no lock : {racy.get('k', 0):>5}  "
          f"({expected - racy.get('k', 0)} increments LOST)")
    print(f"    with threading.Lock      : {safe.get('k', 0):>5}")
    print("  Every lost increment is one request that slipped past the")
    print("  limit. Redis INCR is a single command the server executes")
    print("  start to finish - there is no gap to interleave into.")

    # 6b. SHARED STATE. The lock above fixed one process. Deployments run
    # several (uvicorn --workers 4, or four containers behind NGINX 0.12).
    class PerProcessLimiter:
        def __init__(self, limit):
            self.limit, self.seen = limit, {}

        def allow(self, key):
            c = self.seen.get(key, 0)
            if c >= self.limit:
                return False
            self.seen[key] = c + 1
            return True

    workers = [PerProcessLimiter(10) for _ in range(4)]
    allowed = sum(1 for i in range(80)
                  if workers[i % 4].allow("key:abc"))   # round-robin LB
    print(f"\n  intended global limit: 10/min for one key")
    print(f"  4 worker processes, each with its own dict, load balanced")
    print(f"    requests offered: 80    allowed: {allowed}  "
          f"<- {allowed // 10}x the intended limit")
    print("  Each worker is individually correct and collectively wrong.")
    print("  The limit lives in the wrong place: it has to be one counter")
    print("  every worker can reach, which is what Redis (or Postgres) is.")

    # 6c. TTL. Nothing removes a key from a dict. Rate-limit keys are
    # per-user-per-window, so the key space grows forever.
    keyspace = {}
    for user in range(50_000):
        keyspace[f"ratelimit:user{user:06d}:win1712345"] = 1
    footprint = sys.getsizeof(keyspace) + sum(
        sys.getsizeof(k) + sys.getsizeof(v) for k, v in keyspace.items())
    print(f"\n  50,000 distinct rate-limit keys held in a dict:")
    print(f"    {len(keyspace):,} entries, about {footprint/1024/1024:.1f} MiB,"
          f" and nothing deletes them")
    print("  Redis takes an expiry with the write, so the key removes")
    print("  itself. The two-command version people actually deploy:")
    print("    INCR   ratelimit:{key}:{window}")
    print("    EXPIRE ratelimit:{key}:{window} 60 NX")
    print("  Postgres could hold this counter too - it would be correct,")
    print("  durable, and would cost a disk write, a WAL record and a row")
    print("  lock on EVERY request, plus a cleanup job for expiry. Redis")
    print("  is chosen here because the data is small, hot and disposable.")


# ===================================================================== 7
def demo_connection_cost(tmp: str) -> None:
    print(SEP)
    print("DEMO 7 - a connection per request is not free (7.7)")
    print(SEP)
    path = os.path.join(tmp, "pool.db")
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, body TEXT)")
    con.executemany("INSERT INTO items (body) VALUES (?)",
                    [(f"row-{i}",) for i in range(1000)])
    con.commit()
    con.close()

    n_req = 300
    query = "SELECT body FROM items WHERE id = ?"

    # Per-request connect. Note the PRAGMA: every real connection also
    # needs session setup - search_path, timezone, statement_timeout in
    # Postgres - and that setup runs again on every new connection.
    t0 = time.perf_counter()
    for i in range(n_req):
        c = sqlite3.connect(path)
        c.execute("PRAGMA foreign_keys = ON")
        c.execute(query, (i % 1000 + 1,)).fetchone()
        c.close()
    per_req = time.perf_counter() - t0

    t0 = time.perf_counter()
    c = sqlite3.connect(path)
    c.execute("PRAGMA foreign_keys = ON")
    for i in range(n_req):
        c.execute(query, (i % 1000 + 1,)).fetchone()
    c.close()
    reused = time.perf_counter() - t0

    print(f"  {n_req} identical queries against a {1000}-row table")
    print(f"    connect + setup + query + close each time : "
          f"{per_req*1000:7.1f} ms   ({per_req/n_req*1e6:6.0f} us/query)")
    print(f"    one connection reused                     : "
          f"{reused*1000:7.1f} ms   ({reused/n_req*1e6:6.0f} us/query)")
    print(f"    ratio: {per_req/reused:.1f}x")
    print("\n  And that ratio is the FLOOR, not the result. Opening SQLite")
    print("  is opening a file. Opening Postgres is a TCP handshake, TLS,")
    print("  authentication, and the server forking a whole backend process")
    print("  that reserves megabytes - single-digit milliseconds each, and")
    print("  a hard max_connections ceiling you can exhaust.")
    print("  Real tools: psycopg_pool.ConnectionPool in-process, PgBouncer")
    print("  in front of the server when many processes share one database.")


def main() -> None:
    tmp = tempfile.mkdtemp(prefix="course_0_15_")
    state: dict = {}
    print(f"python {sys.version.split()[0]} | numpy {np.__version__} "
          f"| sqlite {sqlite3.sqlite_version}")
    print(f"scratch dir (removed in a finally block):")
    print(f"  {os.path.basename(tmp)}  under the system temp directory")
    print("no network, no server, no container: Postgres/pgvector/Redis are")
    print("modelled locally - see the .md for the real psycopg + redis code")
    try:
        demo_sql_injection(tmp)
        demo_parameters_are_data(tmp)
        demo_embeddings_and_cosine(state)
        demo_ivf_tradeoff(state)
        demo_rate_limit_boundary()
        demo_shared_state()
        demo_connection_cost(tmp)
        print(SEP)
        print("Three stores, three jobs: Postgres for rows you cannot lose,")
        print("pgvector for similarity you can approximate, Redis for counts")
        print("you can throw away. 5.2, 6.5 and 7.7 each pick one.")
        print(SEP)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"scratch dir removed: {not os.path.exists(tmp)}")


if __name__ == "__main__":
    main()
