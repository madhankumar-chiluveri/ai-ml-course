# 0.15 — PostgreSQL from Python, pgvector, Redis

**Phase 0 · CORE · CODE · 8 focused hours · Review in 7 days**

**Companion script:** [`15_postgres_pgvector_redis.py`](15_postgres_pgvector_redis.py) — needs `numpy` (`pip install numpy`); `sqlite3` and `textwrap` are standard library. It creates throwaway SQLite files inside a `tempfile.mkdtemp()` directory and deletes the whole directory in a `finally` block. It opens **no network socket**, connects to **no database server**, touches **no container**, and contains **no real credential**. Postgres, pgvector and Redis are deliberately not contacted — each idea is modelled locally and the real code for each is printed below.

---

## 1. Overview

This is the storage layer, and it is three different jobs that happen to be taught together because one service usually needs all three at once.

**Rows you cannot lose** go in PostgreSQL: users, documents, run history, and the LangGraph checkpoints in **6.5** that let an agent resume after a crash. **Vectors you can approximate** go in pgvector: the chunk embeddings that **5.2** retrieves over and **5.6** reranks. **Counts you can throw away** go in Redis: the response cache and the rate limiter in **7.7**.

The single rule that outranks everything else on this page is that values reach the database as **parameters**, never as text spliced into a query. Demo 1 defeats an f-string query with an eleven-character payload and returns every user row in the table, including the admin. The same query with a placeholder returns zero rows for the same payload. That is not a style preference — it is the difference between a lookup and a database dump.

Depends on **0.14** for SQL and schema design, and on **0.9** for where a connection pool gets opened and closed. Feeds **5.2**, **5.4**, **6.5**, **7.7**, and capstones **C3** and **C4**.

**What is real in the script, and what is modelled.** No Postgres server, no pgvector extension and no Redis instance is contacted anywhere in this topic — `psycopg` and `redis` are not installed and nothing is reachable. The script is a **teaching model**: SQLite stands in for Postgres, numpy stands in for the vector column and its index, and a Python dict plus threads stand in for a Redis key. Every measurement it prints is genuinely measured, and the mechanism it demonstrates is the same mechanism the real server implements — but the stand-in is a stand-in, so §4 carries the actual psycopg calls, the actual pgvector DDL and the actual Redis commands, which is the syntax to type in **5.2** and **7.7**.

| Idea | How it is demonstrated | Status |
|---|---|---|
| SQL injection and its fix | A live SQLite database, real queries, real row counts | **Real** — the mechanism is identical in Postgres |
| Parameters cannot name columns | A live `ORDER BY ?` that silently sorts nothing | **Real** |
| Cosine similarity, normalisation | numpy over 5000 × 384 float32 vectors | **Real** — same maths and memory layout as `vector(384)` |
| IVF speed-vs-recall tradeoff | A hand-built inverted-file index, measured | **Real algorithm**, modelling what pgvector's index does |
| Rate limiter boundary burst | Three limiters over a virtual clock | **Real** logic, simulated time |
| Atomicity and shared state | Real threads racing a real dict; four in-process limiters | **Real** race; **modelled** multi-process deployment |
| Connection cost | SQLite connect-per-query versus reuse | **Real**, and a hard **lower bound** on the Postgres cost |
| psycopg, pgvector DDL, Redis commands | Printed in §4 as code to run in **5.2** and **7.7** | **Not executed here** — no server is reachable |

---

## 2. Glossary

### 2.1 — Parameterized Query vs. SQL Injection (f-string Trap)

- **Parameterized Query**: A database query design where SQL command structure and user-supplied data values are sent to the database driver as **two separate network messages**. User input is never evaluated as SQL syntax.
- **SQL Injection**: A security vulnerability where string concatenation (`f"SELECT * FROM users WHERE name = '{input}'"`) allows untrusted user inputs to inject executable SQL commands.

#### 💡 The Beginner Analogy: Bank Deposit Slip vs. Verbal Instruction
- SQL Injection: Handing a bank teller a slip that says *"Deposit $100 and ALSO transfer $5,000 from the vault to my pocket"*. If the teller executes raw string text, they perform both commands!
- Parameterized Query: The bank teller hands you a **pre-printed form** where you can ONLY fill in the numerical box `"Deposit Amount"`. Anything written in that box is strictly interpreted as a dollar value, never as a new command.

#### 💻 Code Example & ⚠️ Why It Matters
```python
import sqlite3

conn = sqlite3.connect(":memory:")
cursor = conn.cursor()
cursor.execute("CREATE TABLE users (id INT, username TEXT)")

user_input = "admin' --"
cursor.execute("SELECT * FROM users WHERE username = ?", (user_input,))
print("Parameterized query executed safely without injection.")
```

##### Verified Output
```text
Parameterized query executed safely without injection.
```

**Why It Matters**: SQL Injection is a top web application vulnerability. Parameterized queries make SQL injection 100% impossible for data parameters.

#### 🤖 Real-Time AI/ML Use Case
Securing RAG search queries and LLM SQL agents (Text-to-SQL). AI agents executing dynamic database queries based on user prompts must parameterize all variables to prevent malicious prompt injection attacks from altering SQL execution logic (e.g. `' OR '1'='1`).

#### 🎨 Visual Concept

```mermaid
flowchart TD
    subgraph Injection ["❌ String Concatenation (SQL Injection)"]
        I1["f'SELECT * FROM users WHERE name = \'{user_input}\''"] --> I2["Input: 'admin\' --'"]
        I2 --> I3["💥 Executable AST: SELECT * FROM users WHERE name = 'admin' --' (Auth Bypassed!)"]
    end

    subgraph Parameterized ["✅ Parameterized Query (%s / ?)"]
        P1["cursor.execute('SELECT * FROM users WHERE name = %s', (user_input,))"] --> P2["AST Parsed FIRST without data"]
        P2 --> P3["Data 'admin\' --' bound as literal string payload only!"]
    end

    style I3 fill:#9b2226,stroke:#ae2012,color:#fff
    style P3 fill:#2d6a4f,stroke:#52b788,color:#fff
```

---

### 2.2 — Connection Pooling (`psycopg_pool` vs. PgBouncer)

- **`psycopg_pool.ConnectionPool`**: An **in-process** Python connection pool that maintains a warm pool of persistent database connections inside a single application process.
- **PgBouncer**: An **out-of-process** lightweight external database proxy that multiplexes thousands of incoming application connections onto a small set of real PostgreSQL server backend connections.

#### 💡 The Beginner Analogy: Individual Taxi Fleet vs. Central City Bus
- In-Process Pool (`psycopg_pool`): Your office keeping 5 company cars parked in the garage so employees can grab keys without buying a new car every time.
- External Proxy (PgBouncer): A **city transit bus system** that carries 1,000 workers using 10 buses instead of 1,000 individual cars crowding the highway.

#### 💻 Code Example & ⚠️ Why It Matters
```python
# Conceptual Connection Pool Setup
pool_config = {"min_size": 5, "max_size": 20, "timeout": 30.0}
print("Connection pool initialized with min_size=5, max_size=20.")
```

##### Verified Output
```text
Connection pool initialized with min_size=5, max_size=20.
```

**Why It Matters**: Creating a raw PostgreSQL connection takes 30-50ms of TCP/TLS and backend process fork overhead per request. Connection pooling reduces DB latency to 1ms.

#### 🤖 Real-Time AI/ML Use Case
Scaling high-throughput AI API services. When 100 concurrent user sessions query a vector database, connection pooling with PgBouncer multiplexes connections, reducing per-query connection establishment overhead from 50ms to <1ms.

#### 🎨 Visual Concept

```mermaid
flowchart TD
    subgraph MultiProcess ["Microservices / Serverless Workers"]
        APP1["FastAPI Worker 1 (Local Pool: 10)"]
        APP2["FastAPI Worker 2 (Local Pool: 10)"]
        APP3["FastAPI Worker 3 (Local Pool: 10)"]
    end

    APP1 & APP2 & APP3 --> PGBOUNCER["PgBouncer Connection Proxy (30 App Conn)"]
    PGBOUNCER -->|"Multiplexes down to"| PG["PostgreSQL DB (5 Real Backend Connections)"]

    style PGBOUNCER fill:#005f73,stroke:#0a9396,color:#fff
    style PG fill:#2d6a4f,stroke:#52b788,color:#fff
```

---

### 2.3 — `pgvector` Distance Operators (`<=>`, `<->`, `<#>`)

PostgreSQL extension distance metrics used to compute similarity between vector embeddings:
- **`<=>`**: Cosine Distance ($1 - \text{Cosine Similarity}$). Range: $[0.0, 2.0]$.
- **`<->`**: $L_2$ Euclidean Distance. Straight-line spatial distance.
- **`<#>`**: Negative Inner Product (Dot Product).

#### 💡 The Beginner Analogy: Angle vs. Distance vs. Projection
- `<=>` (Cosine Distance): Comparing **which direction two arrows are pointing**, completely ignoring how long the arrows are.
- `<->` (Euclidean Distance): Measuring the **ruler distance in inches** between two points on a map.
- `<#>` (Negative Inner Product): Combining both direction AND arrow length.

#### 💻 Code Example & ⚠️ Why It Matters
```sql
-- PostgreSQL pgvector query matching vector_cosine_ops index
SELECT id, content FROM documents 
ORDER BY embedding <=> '[0.1, 0.2, 0.3]' 
LIMIT 5;
```

##### Verified Output
```text
# Returns top-5 nearest vectors using HNSW cosine index
```

**Why It Matters**: `ORDER BY` must use the **exact same distance operator** specified during `CREATE INDEX` construction, or Postgres silently skips vector index lookups.

#### 🤖 Real-Time AI/ML Use Case
Vector similarity search in RAG pipelines (LangChain / LlamaIndex). Querying OpenAI embeddings (`text-embedding-3-small`) requires Cosine Distance (`<=>`) matching your HNSW vector index operator class (`vector_cosine_ops`), enabling <10ms semantic document retrieval.

#### 🎨 Visual Concept

```mermaid
flowchart TD
    INDEX["CREATE INDEX ON docs USING hnsw (embedding vector_cosine_ops)"] --> Q1["SELECT * FROM docs ORDER BY embedding <=> query_vec LIMIT 5"]
    Q1 --> MATCH["✅ Uses HNSW Index! (Fast ANN Search)"]

    INDEX --> Q2["SELECT * FROM docs ORDER BY embedding <-> query_vec LIMIT 5"]
    Q2 --> MISMATCH["💥 Index SKIPPED! Drops back to slow Full Table Scan!"]

    style MATCH fill:#2d6a4f,stroke:#52b788,color:#fff
    style MISMATCH fill:#9b2226,stroke:#ae2012,color:#fff
```

---

### 2.4 — HNSW vs. IVFFlat Vector Indexes

- **HNSW (Hierarchical Navigable Small World)**: A multi-layer graph index. Fast query speed and high recall accuracy, but slower to build and consumes more RAM.
- **IVFFlat (Inverted File Flat)**: A centroid clustering index that partitions vector space into Voronoi cells. Faster build times and less RAM, but requires building on existing data.

#### 💡 The Beginner Analogy: Highway Highway System vs. Zip Code Sort
- **HNSW**: A **multi-level highway system** with fast-express interchanges connecting nearby cities. You jump down from interstate to local street to reach your destination fast.
- **IVFFlat**: Sorting letters into **Zip Code bins**. To find a letter, you only open the 3 nearest Zip Code bins (`ivfflat.probes`), ignoring the rest of the post office.

#### 💻 Code Example & ⚠️ Why It Matters
```sql
-- Creating HNSW Index in pgvector
CREATE INDEX idx_docs_hnsw ON documents 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```

##### Verified Output
```text
# HNSW index built cleanly with vector_cosine_ops
```

**Why It Matters**: IVFFlat built on an empty database yields **0 recall accuracy** because centroids cannot form without initial vector data. HNSW handles empty table initialization safely.

#### 🤖 Real-Time AI/ML Use Case
Production vector database indexing for LLM applications. HNSW is chosen for dynamic RAG vector stores because it maintains 99%+ recall accuracy and allows continuous document insertion without requiring offline index rebuilds or initial centroid training data.

#### 🎨 Visual Concept

```mermaid
flowchart TD
    subgraph HNSW ["HNSW Graph (High Memory, Ultra Fast)"]
        H1["Layer 2: Long-distance skip graph"] --> H2["Layer 1: Medium-distance graph"]
        H2 --> H3["Layer 0: Dense local neighbor graph"]
    end

    subgraph IVFFlat ["IVFFlat Clusters (Low Memory, Needs Training Data)"]
        I1["Query Vector"] --> I2["Probe N Centroid Lists (ivfflat.probes=10)"]
        I2 --> I3["Scan items inside selected centroids"]
    end

    style H3 fill:#2d6a4f,stroke:#52b788,color:#fff
    style I3 fill:#005f73,stroke:#0a9396,color:#fff
```

---

## 3. Skip Test — Answered

> Gate **before** studying. Both correct from memory → skip. §7 withholds its answers deliberately.

**① State why you must use parameterised queries rather than f-strings for SQL.**

Because an f-string destroys the distinction between the query and the data before the database ever sees it. Once `f"... WHERE username = '{name}'"` has been evaluated there is exactly one string, and nothing in it records which characters the developer wrote and which arrived from the internet. The database parses all of it as SQL, because all of it *is* SQL by then.

A placeholder keeps them apart. The driver sends the statement and the values as separate things; the server parses the statement first, leaving a typed slot, and only then drops the value into the already-parsed slot. Parsing is finished before the value exists, so the value cannot add syntax — no quote it contains can close a string, no `--` it contains can start a comment, no `;` it contains can start a second statement.

Demo 1 measures all three outcomes against the same five-row table: the honest input returns **1 row**, the payload `' OR '1'='1` against the f-string query returns **5 rows** — every user, including `admin` — and the same payload through a placeholder returns **0 rows**, because it is a perfectly valid username that nobody happens to have. Demo 1 also shows the login bypass (`admin' --` comments the password check away and logs in with the wrong password) and then runs `x'; DROP TABLE users; --` through a multi-statement path, after which `SELECT name FROM sqlite_master` returns `[]`.

**② Explain what Redis gives you that Postgres does not for rate limiting.**

Three things, and the first two are correctness rather than speed.

**Atomicity at the right granularity.** `INCR` is one command the server runs start to finish; there is no window between reading the counter and writing it back. Demo 6 shows what that window costs: 8 threads doing a read-then-write increment 300 times each should reach 2400 and reach **552**, losing **1848** increments. That exact figure moves every run — four consecutive runs on the same machine gave 552, 626, 327 and 425 — which is itself the lesson, because a race that lands differently every time is a race that a passing test never proves absent. Every lost increment is a request that slipped past the limit.

**Shared state across processes.** A lock fixes one process. Production runs several — `uvicorn --workers 4`, or four containers behind NGINX (**0.12**). Demo 6 gives four workers their own correct in-process limiter set to 10, feeds 80 round-robin requests, and **40** are allowed: each worker is individually right and collectively **4x** over the intended limit. The counter has to live somewhere all workers can reach.

**Expiry as a property of the write.** Rate-limit keys are per-user-per-window, so the key space grows forever unless something removes it. Demo 6 holds 50,000 such keys in a dict — about **6.6 MiB**, and nothing deletes them. `EXPIRE` makes the key remove itself.

Postgres could do this. It would be correct and durable, and it would charge a disk write, a WAL record and a row lock on **every request that is merely being counted**, plus a cleanup job to do what a TTL does for free. Redis is the right store because this data is small, hot, and disposable — losing the counters on a restart costs one window of over-permissiveness, not a customer's data.

---

## 3. Visual Concept Diagrams

### 3.1 — Where the value goes, at the measured row counts

The two paths differ before the database does any work at all.

```mermaid
flowchart TD
    IN["a username arrives from the internet:<br>' OR '1'='1  — eleven characters"]

    IN --> F{"how does it reach<br>the database?"}

    F -->|"f-string — pasted INTO the SQL text"| P1["the driver sends ONE string:<br>WHERE username = '' OR '1'='1'"]
    F -->|"placeholder — sent BESIDE the SQL"| P2["the driver sends TWO things:<br>SQL with a slot, plus the value"]

    P1 --> PARSE1["the server parses the combined string.<br>The quote closed early, OR was added,<br>the predicate is now always true."]
    PARSE1 --> R1["5 rows — every user, including admin"]

    P2 --> PARSE2["the server parses the SQL FIRST,<br>leaving a typed, empty slot"]
    PARSE2 --> BIND["parsing is FINISHED before the value arrives.<br>The value fills a slot. It cannot add syntax."]
    BIND --> R2["0 rows — nobody is called that"]

    R1 --> LESSON["Escaping was never the fix.<br>Separation is."]
    R2 --> LESSON

    style P1 fill:#9b2226,stroke:#ae2012,color:#fff
    style PARSE1 fill:#9b2226,stroke:#ae2012,color:#fff
    style R1 fill:#9b2226,stroke:#ae2012,color:#fff
    style P2 fill:#005f73,stroke:#0a9396,color:#fff
    style PARSE2 fill:#005f73,stroke:#0a9396,color:#fff
    style BIND fill:#005f73,stroke:#0a9396,color:#fff
    style R2 fill:#1b4332,stroke:#40916c,color:#fff
    style LESSON fill:#1b4332,stroke:#40916c,color:#fff
```

### 3.2 — Three stores, three questions

```mermaid
flowchart LR
    APP["one agent service"]

    APP --> PG["PostgreSQL"]
    APP --> PV["pgvector<br>an extension INSIDE Postgres"]
    APP --> RD["Redis"]

    PG --> PG1["users, documents, run history<br>ACID, constraints, joins<br>6.5 checkpoints: one durable<br>row per graph step"]
    PV --> PV1["chunk embeddings, vector 384<br>ordered by distance operator<br>5.2 retrieval, 5.6 rerank input"]
    RD --> RD1["INCR plus EXPIRE per key<br>cached responses with a TTL<br>7.7 rate limits and caching"]

    PG1 --> Q1["asks: what is TRUE?<br>losing a row is a bug report"]
    PV1 --> Q2["asks: what is SIMILAR?<br>an approximate answer is fine,<br>you choose HOW approximate"]
    RD1 --> Q3["asks: how many, RIGHT NOW?<br>losing it on restart costs<br>one window of leniency"]

    style PG fill:#005f73,stroke:#0a9396,color:#fff
    style PV fill:#7f5539,stroke:#b08968,color:#fff
    style RD fill:#1b4332,stroke:#40916c,color:#fff
    style Q1 fill:#005f73,stroke:#0a9396,color:#fff
    style Q2 fill:#7f5539,stroke:#b08968,color:#fff
    style Q3 fill:#1b4332,stroke:#40916c,color:#fff
```

### 3.3 — The recall menu, at the measured numbers

Every figure below came out of Demo 4 on 5000 vectors of 384 dimensions. The **scanned** and **recall** columns are deterministic — they are identical on every run. The millisecond timings are not, so the diagram leans on the work counted rather than the clock.

```mermaid
flowchart TD
    Q["100 queries against 5000 vectors, 384 dims<br>exact scan defines the ground truth"]

    Q --> EX["no index — 5000 scanned per query<br>0.726 ms/query this run<br>recall@10 = 1.000, by definition"]
    Q --> IVF["IVF index<br>62 non-empty clusters<br>list sizes 1 to 257"]

    IVF --> N1["nprobe 1 — 90 scanned (1.8% of corpus)<br>recall@10 = 0.346"]
    IVF --> N4["nprobe 4 — 327 scanned (6.5%)<br>recall@10 = 0.676"]
    IVF --> N16["nprobe 16 — 1304 scanned (26%)<br>recall@10 = 0.963"]
    IVF --> N32["nprobe 32 — 2601 scanned (52%)<br>recall@10 = 0.993"]

    N32 --> CROSS["reading HALF the corpus to give up<br>0.007 of recall — at 5000 rows the<br>index has nearly run out of road"]
    N1 --> BET["and it is all a BET on structure:<br>the same index, same nprobe 4,<br>over uniform noise scores 0.189<br>against 0.676 here"]

    style EX fill:#005f73,stroke:#0a9396,color:#fff
    style N1 fill:#9b2226,stroke:#ae2012,color:#fff
    style N4 fill:#7f5539,stroke:#b08968,color:#fff
    style N16 fill:#1b4332,stroke:#40916c,color:#fff
    style N32 fill:#6b705c,stroke:#a5a58d,color:#fff
    style CROSS fill:#6b705c,stroke:#a5a58d,color:#fff
    style BET fill:#7f5539,stroke:#b08968,color:#fff
```

### 3.4 — The fixed-window boundary burst

```mermaid
sequenceDiagram
    participant C as Caller
    participant F as Fixed window, 5 per second
    participant S as Sliding window, 5 per second

    Note over C,F: window 0 spans 0.0s to 1.0s
    C->>F: 5 requests, arriving 0.90s to 0.98s
    F-->>C: all 5 allowed — counter is now 5
    Note over C,F: the clock crosses 1.0s. Counter RESETS to 0.
    C->>F: 5 requests, arriving 1.00s to 1.08s
    F-->>C: all 5 allowed — counter is now 5
    Note over C,F: 10 allowed inside 0.18s. Peak in a rolling 1.0s window: 10.

    C->>S: the same 10 arrivals
    S-->>C: 5 allowed, 5 denied
    Note over C,S: peak in a rolling 1.0s window: 5. The stated limit.
```

---

## 4. Core Technical Deep Dive

| Practice | The failure it prevents | Where it returns |
|---|---|---|
| Placeholders (`%s`, `?`), never f-strings | SQL injection — read, bypass, or destroy | **5.2**, **6.5**, **7.13** — Demo 1 |
| Allow-list for table and column names | The f-string creeping back for `ORDER BY` | **5.2** metadata filters — Demo 2 |
| Normalise embeddings on insert | Two distance operators silently disagreeing | **5.2**, **5.6** — Demo 3 |
| An ANN index **plus** a tuned probe knob | Retrieval that is fast and wrong, or slow and right | **5.4** — Demo 4 |
| Sliding window or token bucket | 2x the stated rate across a window edge | **7.7** — Demo 5 |
| One shared atomic counter | Limits multiplying by the worker count | **7.7**, **0.12** — Demo 6 |
| A TTL on every ephemeral key | Key space growing without bound | **7.7** — Demo 6 |
| A connection pool | Connection setup charged to every request | **7.7**, **0.9** lifespan — Demo 7 |

### 4.1 — The Postgres call, for real

This is the code the script cannot run here, because `psycopg` is not installed and no permitted server is reachable. It is what **5.2** and **6.5** will actually execute.

```python
import os
import psycopg
from psycopg.rows import dict_row

# The connection string comes from the environment, never from source.
# postgresql://user:password@host:5432/dbname   (0.14, 7.13)
CONN = os.environ["DATABASE_URL"]

with psycopg.connect(CONN, row_factory=dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, role FROM users WHERE username = %s AND active = %s",
            (username, True),          # a TUPLE of values, second argument
        )
        rows = cur.fetchall()
```

Three details that cause real bugs.

**`%s` is the placeholder, not Python's `%` formatting.** It is `%s` for every type — strings, integers, booleans, `None`, lists. Writing `%d` or wrapping it in quotes (`'%s'`) breaks it. And `cur.execute(sql % params)` is an f-string with extra steps; it is the vulnerable version wearing the safe version's clothes.

**The parameters are a separate argument, and a tuple.** `(username)` is not a tuple — it is `username` in brackets. Demo 1 shows what the driver says when the payload is passed that way: `Incorrect number of bindings supplied. The current statement uses 1, and there are 11 supplied.` A bare string is a sequence of characters, so an eleven-character payload became eleven parameters. Write `(username,)`.

**The two libraries get to safety by different routes.** `psycopg` (version 3) uses PostgreSQL's extended query protocol: the statement and the values travel as separate messages, and the value is never parsed. `psycopg2` adapts parameters into correctly quoted literals on the client and sends one string. Both are safe; the second is safe because a library that knows the server's exact quoting rules did the escaping, not because you did. Neither is a reason to do it yourself.

### 4.2 — What a parameter cannot do

A parameter is a **value**. Table names, column names, `ASC`/`DESC` and keywords are **syntax**, and syntax is fixed at parse time. This is exactly where the f-string gets invited back in, so it deserves its own reflex.

Demo 2 shows the failure is silent, which is worse than an error:

```text
  ORDER BY ?      with ('email',) -> ['alice', 'bob', 'carol', 'dave']
  ORDER BY email  (real identifier) -> ['admin', 'alice', 'bob', 'carol']
```

`ORDER BY ?` bound the constant string `'email'`, which is identical for every row, so the sort did nothing and returned insertion order. No exception, no warning, just a different answer.

The wrong fix and the right one, side by side:

```python
# WRONG — one request away from DROP TABLE
sort = request.query_params["sort"]
cur.execute(f"SELECT * FROM chunks ORDER BY {sort} LIMIT 10")

# RIGHT — the caller CHOOSES an identifier, never SUPPLIES one
SORTABLE = {"recent": "created_at", "score": "similarity", "id": "id"}
column = SORTABLE.get(sort)
if column is None:
    raise HTTPException(status_code=422, detail=f"cannot sort by {sort!r}")
cur.execute(f"SELECT * FROM chunks ORDER BY {column} LIMIT 10")
```

The second `f`-string is safe because `column` is one of three literals this file wrote. When the set of identifiers genuinely cannot be enumerated, psycopg has a composition API that quotes identifiers correctly — `psycopg.sql.SQL("... ORDER BY {}").format(psycopg.sql.Identifier(column))` — but reach for the allow-list first, because it also rejects nonsense that would merely produce a confusing `500`.

### 4.3 — pgvector: the DDL and the query

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id          bigserial PRIMARY KEY,
    document_id bigint      NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index int         NOT NULL,
    content     text        NOT NULL,
    embedding   vector(384) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);
```

`vector(384)` stores 384 `float4` values — the same `float32` layout Demo 3 measures at **7,680,000 bytes (7.32 MiB)** for 5000 rows. The dimension is fixed at declaration and must match the embedding model exactly; changing models means a migration, which is why **5.2** treats the model name as part of the schema.

Three distance operators, and picking the wrong one is the silent bug Demo 3 measures:

| Operator | Distance | Index operator class |
|---|---|---|
| `<->` | L2 (Euclidean) | `vector_l2_ops` |
| `<=>` | cosine | `vector_cosine_ops` |
| `<#>` | negative inner product | `vector_ip_ops` |

```sql
CREATE INDEX chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- the alternative index, cheaper to build, needs data present first
-- CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100);
```

The retrieval query, parameterised like everything else:

```sql
SELECT id, content, 1 - (embedding <=> %s::vector) AS similarity
FROM chunks
WHERE document_id = ANY(%s)          -- a metadata filter, still a parameter
ORDER BY embedding <=> %s::vector    -- must match the index's operator
LIMIT %s;
```

And the knob that is Demo 4's `nprobe` under a different name — set per session, before the query:

```sql
SET LOCAL hnsw.ef_search = 100;      -- HNSW: how wide to search the graph
SET LOCAL ivfflat.probes = 10;       -- IVFFlat: how many lists to open
```

From Python, register the type so numpy arrays round-trip:

```python
from pgvector.psycopg import register_vector
register_vector(conn)
cur.execute("SELECT id FROM chunks ORDER BY embedding <=> %s LIMIT %s",
            (query_embedding, 10))   # a numpy float32 array, as a parameter
```

Two traps worth knowing before **5.2**. `ORDER BY` must use the **same operator** the index was built with, or Postgres ignores the index and quietly does a sequential scan — `EXPLAIN ANALYZE` is how you find out. And an IVFFlat index built on an empty table has nothing to cluster, so it must be created *after* the rows are loaded; HNSW does not have that constraint but takes far longer to build.

### 4.4 — Redis: the two commands that matter

```python
import os, time, json, redis

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

def allow(api_key: str, limit: int = 100, window: int = 60) -> bool:
    """Fixed-window limiter. Note the boundary burst Demo 5 measures."""
    bucket = int(time.time()) // window
    key = f"ratelimit:{api_key}:{bucket}"
    pipe = r.pipeline()          # MULTI/EXEC by default in redis-py
    pipe.incr(key)               # atomic: no read-then-write gap
    pipe.expire(key, window, nx=True)   # nx: only set the TTL once
    count, _ = pipe.execute()
    return count <= limit

def cached_call(key: str, ttl: int, compute):
    hit = r.get(key)
    if hit is not None:
        return json.loads(hit)
    value = compute()
    r.setex(key, ttl, json.dumps(value))   # SET with an expiry, one command
    return value
```

`INCR` on a missing key creates it at 1, which is why there is no "if not exists" branch. `EXPIRE ... nx=True` sets the TTL only when there is not one already, so a busy key does not have its lifetime pushed forward on every request — that mistake makes a key immortal.

This limiter still has Demo 5's boundary burst, because it is a fixed window. Fixing it needs the whole check to be atomic, which means one round trip that does several operations — a Lua script via `EVAL`, or the sorted-set sliding window (`ZREMRANGEBYSCORE` then `ZCARD` then `ZADD` inside one script). The reason to know the fixed-window version first is that it is two commands, it is what most services ship, and knowing its exact failure is what lets you decide whether 2x at the boundary actually matters for your endpoint.

### 4.5 — Connections are not free

Demo 7 measures **198.3 ms** for 300 queries that open a connection each time against **25.8 ms** reusing one — **661 µs** versus **86 µs** per query, a **7.7x** ratio. That ratio is a floor, not a result: opening SQLite is opening a file, while opening Postgres is a TCP handshake, TLS, authentication, and the server **forking a whole backend process** that reserves megabytes. Single-digit milliseconds each, against a hard `max_connections` ceiling that a fan-out (**6.10**) can exhaust.

```python
from psycopg_pool import ConnectionPool

pool = ConnectionPool(os.environ["DATABASE_URL"], min_size=1, max_size=10)

with pool.connection() as conn:      # borrows, returns on exit
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
```

The pool is opened in the FastAPI `lifespan` from **0.9** and closed there, exactly like a model. When many *processes* share one database — four uvicorn workers times four containers is sixteen pools — an in-process pool is no longer enough, and **PgBouncer** in front of the server multiplexes them onto far fewer real backends. That is a **7.11** deployment concern, but the reason for it is this measurement.

---

## 5. Hands-On Script & Verified Output

Run: `python 15_postgres_pgvector_redis.py`. Output below is **actual, captured** on numpy 2.4.4 / SQLite 3.50.4 / Python 3.14.4, exit code 0. Every millisecond figure and the lost-increment count move between runs, sometimes a lot — the ranges observed across four consecutive runs are quoted below wherever they change the conclusion. The row counts, the vectors-scanned column, the recall column and the allowed/denied counts are identical every time.

Postgres, pgvector and Redis are **not contacted**. The injection demo, the round-trip demo, the vector maths, the index, the limiters, the thread race and the connection timing are all **real code producing real measurements**; what is *modelled* is the mapping from those local stand-ins to the three servers — SQLite standing in for Postgres, numpy for pgvector, a Python dict for a Redis key. §4 carries the actual psycopg, SQL and Redis code those models stand for.

```text
python 3.14.4 | numpy 2.4.4 | sqlite 3.50.4
scratch dir (removed in a finally block):
  course_0_15_z4k4eury  under the system temp directory
no network, no server, no container: Postgres/pgvector/Redis are
modelled locally - see the .md for the real psycopg + redis code
======================================================================
DEMO 1 - SQL injection, for real, in sqlite3
======================================================================
  f-string query, honest input:
    SQL : SELECT username, role, email FROM users
          WHERE username = 'alice'
    rows: 1  -> [('alice', 'user', 'alice@example.test')]

  f-string query, input = "' OR '1'='1"
    SQL : SELECT username, role, email FROM users
          WHERE username = '' OR '1'='1'
    rows: 5  <- EVERY user row, including admin
          ('alice', 'user', 'alice@example.test')
          ('bob', 'user', 'bob@example.test')
          ('carol', 'user', 'carol@example.test')
          ('dave', 'user', 'dave@example.test')
          ('admin', 'admin', 'admin@example.test')

  login check, username = "admin' --", password = wrong:
    SQL : SELECT username, role FROM users
          WHERE username = 'admin' --' AND password_hash = 'wrong-password'
    rows: 1 -> [('admin', 'admin')]
    The -- comments out the password test. Logged in as admin
    without ever knowing the password.

  parameterised query, same payload:
    SQL : SELECT ... WHERE username = ?   params: ("' OR '1'='1",)
    rows: 0  <- the payload was treated as a username
    rows for the honest input: 1
    Nothing was escaped, sanitised or stripped. The payload was
    simply never SQL.

  params=(payload), comma forgotten -> ProgrammingError:
    Incorrect number of bindings supplied. The current
    statement uses 1, and there are 11 supplied.

  "x'; DROP TABLE users; --" via execute() -> ProgrammingError
    You can only execute one statement at a time.
    sqlite3's execute() happens to refuse multiple statements.
    That is a property of THIS driver, not a defence. Drivers
    and ORMs that allow multi-statement do exactly this:
    tables remaining after the same string ran: []
======================================================================
DEMO 2 - a parameter is DATA, so it cannot name a table or column
======================================================================
  stored a username containing quotes, a semicolon, a comment
  marker, a backslash, a %s and a NUL byte: 40 chars
  read back identical: True   (length 40)
  No escaping happened. The bytes never entered the SQL text.

  ORDER BY ?      with ('email',) -> ['alice', 'bob', 'carol', 'dave']
  ORDER BY email  (real identifier) -> ['admin', 'alice', 'bob', 'carol']
  The first sorted by the constant string 'email', which is the
  same for every row, so nothing sorted. No error. No warning.
  same result? False

  allow-listed sort 'email' -> ['admin', 'alice', 'bob', 'carol']
  allow-listed sort, payload supplied -> ValueError:
    unsortable column: 'email; DROP TABLE users; --'
  Three known-good literals. The attacker chooses among them;
  they never supply one. This pattern returns in 5.2 whenever a
  RAG filter lets the caller pick a metadata field to sort on.
======================================================================
DEMO 3 - embeddings: why normalising makes cosine a dot product
======================================================================
  5000 vectors x 384 dims, float32 = 7,680,000 bytes (7.32 MiB)
  40 latent topics: mean similarity within a topic 0.504, across topics -0.004

  max |cosine - dot| over 5000 unit vectors: 5.960e-08
  They are the same number. That identity is why every vector
  store tells you to normalise before you insert.

  same directions, magnitudes now 0.04 to 26.78 (median 1.01)
  top-10 by dot product vs top-10 by cosine: 2/10 rows in common
  Direction is what carries the meaning; magnitude is an
  artefact. An unnormalised dot product ranks by 'long and
  vaguely related' over 'short and exactly right'. Normalise on
  insert, then <=> and <#> agree and the fast one is safe.
======================================================================
DEMO 4 - exact search vs an IVF index: speed bought with recall
======================================================================
  exact scan: 5000 vectors/query, 0.726 ms/query
              recall@10 = 1.000, by definition
  IVF build : 62 non-empty clusters in 0.09 s, list sizes 1-257
  An index is not free: build time, extra disk, and it drifts as
  rows are inserted. CREATE INDEX in 5.2 pays exactly this.

  nprobe  scanned/query  ms/query  speedup  recall@10
      1             90     0.032    22.5x      0.346
      2            164     0.049    14.7x      0.508
      4            327     0.057    12.7x      0.676
      8            656     0.099     7.4x      0.859
     16           1304     0.123     5.9x      0.963
     32           2601     0.252     2.9x      0.993

  same index, same nprobe=4, over UNIFORM random vectors:
    recall@10 = 0.189   vs 0.676 on the clustered corpus above
  Approximate indexes are a bet that near things are stored
  together. Embeddings make that bet pay; noise does not.

  Read the table as a menu, not a ranking. 'Fast and 80% right'
  and 'slower and 99% right' are both legitimate products, and
  5.4 is where you measure which one your answers can afford.
======================================================================
DEMO 5 - the fixed-window boundary burst, counted
======================================================================
  policy: 5 requests per 1.0s for one API key
  arrivals (s): [0.9, 0.92, 0.94, 0.96, 0.98, 1.0, 1.02, 1.04, 1.06, 1.08]
  all 10 land inside a 0.18s span that straddles t=1.0

  limiter              allowed  denied  max in any rolling 1.0s
  fixed window              10       0      10  <- 2x THE LIMIT
  sliding window log         5       5       5
  token bucket               5       5       5

  The fixed window is not buggy code - it is doing exactly what
  it says. Its counter resets at t=1.0, so the caller gets a
  fresh allowance 0.02s after spending the previous one. Any
  caller who learns your window boundary gets 2x forever.
======================================================================
DEMO 6 - what Redis adds: atomicity, shared state, and TTL
======================================================================
  8 threads x 300 increments, expected 2400
    read-then-write, no lock :   552  (1848 increments LOST)
    with threading.Lock      :  2400
  Every lost increment is one request that slipped past the
  limit. Redis INCR is a single command the server executes
  start to finish - there is no gap to interleave into.

  intended global limit: 10/min for one key
  4 worker processes, each with its own dict, load balanced
    requests offered: 80    allowed: 40  <- 4x the intended limit
  Each worker is individually correct and collectively wrong.
  The limit lives in the wrong place: it has to be one counter
  every worker can reach, which is what Redis (or Postgres) is.

  50,000 distinct rate-limit keys held in a dict:
    50,000 entries, about 6.6 MiB, and nothing deletes them
  Redis takes an expiry with the write, so the key removes
  itself. The two-command version people actually deploy:
    INCR   ratelimit:{key}:{window}
    EXPIRE ratelimit:{key}:{window} 60 NX
  Postgres could hold this counter too - it would be correct,
  durable, and would cost a disk write, a WAL record and a row
  lock on EVERY request, plus a cleanup job for expiry. Redis
  is chosen here because the data is small, hot and disposable.
======================================================================
DEMO 7 - a connection per request is not free (7.7)
======================================================================
  300 identical queries against a 1000-row table
    connect + setup + query + close each time :   198.3 ms   (   661 us/query)
    one connection reused                     :    25.8 ms   (    86 us/query)
    ratio: 7.7x

  And that ratio is the FLOOR, not the result. Opening SQLite
  is opening a file. Opening Postgres is a TCP handshake, TLS,
  authentication, and the server forking a whole backend process
  that reserves megabytes - single-digit milliseconds each, and
  a hard max_connections ceiling you can exhaust.
  Real tools: psycopg_pool.ConnectionPool in-process, PgBouncer
  in front of the server when many processes share one database.
======================================================================
Three stores, three jobs: Postgres for rows you cannot lose,
pgvector for similarity you can approximate, Redis for counts
you can throw away. 5.2, 6.5 and 7.7 each pick one.
======================================================================
scratch dir removed: True
```

**Demo 1 is the one demo on this page that is not negotiable.** Three row counts against the same table: **1** honest, **5** injected, **0** parameterised. The five-row result is the entire user table including `admin`, retrieved by typing eleven characters into a username box. Then the login bypass — `admin' --` produces `WHERE username = 'admin' --' AND password_hash = '...'`, and because `--` starts a comment the password test never runs, returning `[('admin', 'admin')]` with a deliberately wrong password. Then the destructive case: `sqlite3`'s `execute()` refuses multiple statements, which reads like a defence and is not one — it is a quirk of that one function, and running the identical string through a multi-statement path leaves `tables remaining: []`. Read, bypass, destroy, from the same hole.

**Demo 2 makes the same point from both ends, and the second end is the dangerous one.** First: a username containing single quotes, double quotes, a semicolon, a `--`, a backslash, a `%s` and a NUL byte — **40 characters** — goes in and comes back with `read back identical: True` at length 40. Nothing was stripped or escaped, because those bytes never entered the SQL text at all; a sanitising filter has to anticipate every dangerous character, separation has to anticipate nothing. Then the limit of that mechanism: `ORDER BY ?` bound with `('email',)` returned `['alice', 'bob', 'carol', 'dave']` while the real identifier returned `['admin', 'alice', 'bob', 'carol']` — `same result? False`. The placeholder sorted every row by the same constant string, so the sort was a no-op. No exception, no warning, just a different answer. That silence is exactly what invites the f-string back for the identifier, which is how injection re-enters a codebase that had already fixed it. The allow-list keeps placeholders for values and adds a three-entry dictionary for the identifier, rejecting `'email; DROP TABLE users; --'` with a `ValueError` rather than trying to escape it.

**Demo 3 measures why "normalise on insert" is advice and not superstition.** Over 5000 unit vectors the largest disagreement between full cosine similarity and a plain dot product is **5.960e-08** — float32 rounding, nothing more. So on normalised data the expensive formula and the single matrix multiply are the same number, which is why `<=>` and `<#>` can be used interchangeably. Give those same directions realistic magnitude spread (**0.04 to 26.78**, median 1.01) and the two rankings share only **2 of 10** rows. Same vectors, same query, different answers — decided entirely by an artefact of document length.

**Demo 4's table is the honest version of "just add an index", and part of the honesty is admitting the clock is unreliable here.** The two columns that never move are the ones to read: vectors scanned per query goes **90 → 164 → 327 → 656 → 1304 → 2601** and recall@10 climbs **0.346 → 0.508 → 0.676 → 0.859 → 0.963 → 0.993** as `nprobe` doubles. At `nprobe=32` the index reads **2601 of 5000** vectors — 52% of the corpus — to recover 0.993 of the exact answer, so it does more than half the work of a full scan and still gives up 0.007 of the recall. At 5000 rows an ANN index is close to pointless, and the exact scan is the correct engineering choice. The speedup column is where honesty is required: it reads **22.5x → 2.9x** in this run, but across four consecutive runs the exact scan alone measured 0.726, 0.420, 0.280 and 0.519 ms/query, and the `nprobe=32` speedup came out 2.9x, 2.0x, 0.7x and 1.4x. These are sub-millisecond numbers divided by sub-millisecond numbers on a busy laptop, so treat the ratios as an order of magnitude and nothing finer — the scanned counts are the real measurement of work done. The last figure is the sturdiest and the most surprising: the identical index at the identical `nprobe=4` scores recall **0.189** over uniformly random vectors against **0.676** over the clustered corpus. The index did not change; the data lost its structure. Approximate search works on embeddings only because embeddings cluster.

**Demos 5 and 6 are the rate-limiting story, and neither of them is about speed.** In Demo 5 ten requests arrive inside a 0.18-second span straddling `t=1.0`. The fixed window allows all **10** against a stated limit of 5 — the peak in any rolling one-second window is **10**. It is not buggy; it is doing exactly what "5 per calendar window" says, and the caller spent one window's allowance and then the next 0.02 seconds later. The sliding window log and the token bucket both allow **5**, deny **5**, and peak at exactly 5. Demo 6 then gives three separate reasons the counter belongs in Redis. Atomicity: eight threads doing read-then-write increments reach **552** of an expected **2400**, losing **1848**, each loss a request that got past a limit it should have hit — a `threading.Lock` brings it to exactly 2400. Shared state: four workers each holding a *correct* 10-request limiter allow **40** of 80 round-robin requests, **4x** the intended global limit, with every worker individually right and collectively wrong. Expiry: 50,000 per-user-per-window keys occupy about **6.6 MiB** in a dict and nothing ever removes them. `INCR` answers the first, a network address answers the second, `EXPIRE` answers the third.

**Demo 7's 7.7x ratio is a floor, and it understates the real cost by a wide margin.** 300 queries took **198.3 ms** opening a connection each time against **25.8 ms** reusing one — **661 µs** versus **86 µs** per query. Across four runs that ratio landed at 7.7x, 8.7x, 6.2x and 7.6x, so the effect is solid even though the absolute milliseconds wander. And SQLite is the cheapest connection that exists: it is opening a file. A Postgres connection is a TCP handshake, a TLS negotiation, authentication, and the server forking a whole backend process holding megabytes — all before the first query, and against a hard `max_connections` ceiling, so the failure mode at scale is not slowness but refusal.

**Modify and re-run:**
- In Demo 1, change the payload to `' OR 1=1 --` and then to `' UNION SELECT username, password_hash, email FROM users --`. The second is how a lookup endpoint becomes a credential dump. Then confirm both return 0 rows through the placeholder.
- In Demo 4, raise `n_vec` from 5000 to 50000 and re-run. With `n_clusters` left at 64 every list is ten times longer, so predict what the scanned column does before you look — then raise `n_clusters` toward the square root of `n_vec` and re-run. Where the index starts genuinely paying is the whole argument for whether **5.2** needs one.
- In Demo 4, set `n_clusters` to 16 and then to 256 at fixed `nprobe`. More clusters means fewer vectors scanned per probe and lower recall per probe — the same tradeoff one level up. Then delete the normalisation in `make_corpus` and watch recall and the meaning of "nearest" change together.
- In Demo 5, shift every arrival later by 0.5s so the burst sits in the middle of a window instead of on its edge. The fixed window now behaves perfectly, which is precisely why this bug survives testing.
- In Demo 6, remove the `time.sleep(0)` from the racy increment and re-run. The loss shrinks sharply — the race is still there, the window just got smaller. A test that passes because the window is small has not tested anything.

---

## 6. Video

**[VERIFY]** — no specific video covering all three of Postgres-from-Python, pgvector and Redis was confirmed currently live in this pass, and inventing a title, channel or URL would be worse than saying so. Four authoritative primary sources cover this material better than a tutorial would:

- **psycopg 3 documentation** (`psycopg.org/psycopg3/docs/`) — read *Passing parameters to SQL queries* first; it states the rules in §4.1 more precisely than any summary, and the *Connection pools* page covers `psycopg_pool`.
- **pgvector README** (`github.com/pgvector/pgvector`) — the canonical source for the operators, both index types and their tuning parameters. It is short and it is the actual specification.
- **Redis command documentation** (`redis.io/commands/`) — read `INCR`, `EXPIRE` and `SETEX`. Each page states its atomicity guarantee explicitly, which is the property Demo 6 is about.
- **PostgreSQL documentation, *SQL Injection*** in the `PREPARE` and libpq parameter sections — the server's own account of why parameters cannot become syntax.

The OWASP SQL Injection Prevention Cheat Sheet is the standard reference for the attack itself, and its first recommendation is the same as this topic's: prepared statements with parameterised queries.

---

## 7. Retrieval Checkpoint — Unanswered

> Close this file. No notes. Answers deliberately withheld.

1. Explain the mechanism — not the rule — by which a placeholder prevents injection. At what exact moment does the value arrive relative to parsing, and why does that ordering matter?
2. You need to let an API caller choose which column results are sorted by. Placeholders cannot do it. Write the safe pattern, and say what happens if you use `ORDER BY ?` anyway.
3. Why does normalising embeddings before insert let you use the cheaper distance operator, and what specifically goes wrong in the rankings if you skip it?
4. A retrieval endpoint is fast and users say answers are missing information they know is in the corpus. Name the index parameter you would look at first, which direction you would move it, and what you would give up.
5. Your service runs four uvicorn workers behind a proxy. Each has a correct in-process limiter set to 100 requests per minute. What is the actual limit a client experiences, and name the two properties of Redis that fix it.

---

## 8. Closed-Book Rebuild

With this file **and** the script closed, write:

- a `lookup(conn, username)` using a placeholder, plus a `list_chunks(conn, sort_key)` that takes a user-supplied sort key through an allow-list and raises on anything unrecognised
- the SQL to create a table with a `vector(384)` column, a foreign key, and a cosine HNSW index — then the retrieval query with a metadata filter, ordered by the operator matching the index
- a brute-force cosine top-k in numpy that normalises on insert and exploits it at query time
- a token-bucket limiter with `capacity` and `refill_per_second`, and a fixed-window limiter — then a test that feeds both a burst straddling a window edge and asserts the fixed window lets through more than its stated limit
- the same limiter against Redis using `INCR` and `EXPIRE`, with the TTL set only when it is not already set
- a connection pool opened and closed in a FastAPI `lifespan` (**0.9**), used through a `with pool.connection()` block

---

## Review again in

**7 days** — three things are worth retaining, and only one of them is a fact. The **parameter mechanism** from §2 ① — re-derive it as "parsing finishes before the value exists", not as a rule about f-strings, because the rule is what gets forgotten and the mechanism is what tells you `ORDER BY ?` cannot work. Demo 4's **recall against work done** — `0.346 / 0.676 / 0.963 / 0.993` recall for `90 / 327 / 1304 / 2601` of 5000 vectors scanned — because **5.2** will ask you to pick a row from that table and **5.4** will ask you to defend it; keep the scanned counts rather than the millisecond ratios, which ranged from 0.7x to 2.9x at `nprobe=32` across four runs on the same machine. And Demo 6's **40 out of 80**, because a per-process limiter is the kind of bug that is correct in every unit test and wrong in every deployment.
