# 📌 FastAPI on AWS to PostgreSQL: Complete Handshake & Lifecycle Guide

> **Scenario**: A FastAPI server running on an AWS EC2 VM, connected to a PostgreSQL database (e.g., AWS RDS or another VM), handling incoming user requests.

---

### 1. 🏗️ The 3 Architecture Components

```mermaid
flowchart LR
    User["👤 User / Mobile App"] -->|"1. HTTPS / API Call"| EC2["☁️ AWS EC2 VM<br>(FastAPI + Uvicorn + SQLAlchemy)"]
    
    subgraph AWSVPC ["AWS VPC Private Network"]
        EC2
        RDS["🗄️ PostgreSQL Database<br>(Port 5432)"]
    end

    EC2 -->|"2. Pre-warmed Connection Pool<br>(Persistent TCP/TLS Sockets)"| RDS

    style User fill:#e8f4f8,stroke:#2b6cb0,stroke-width:1px,color:#000
    style EC2 fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#000
    style RDS fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#000
    style AWSVPC fill:#f3f4f6,stroke:#9ca3af,stroke-width:2px,stroke-dasharray: 5 5,color:#000
```

---

### 2. 🤝 The 4 Handshakes to Open 1 Database Connection

When FastAPI boots up (or opens a new connection for the pool), it goes through **4 strict verification layers**:

```mermaid
sequenceDiagram
    autonumber
    participant App as 🐍 FastAPI / asyncpg (EC2)
    participant Sec as 🛡️ AWS Security Group
    participant PG as 🗄️ PostgreSQL Server (Port 5432)

    Note over App,PG: Layer 1: AWS Network Firewall Check
    App->>Sec: Outbound Port 5432 -> Inbound to Postgres
    Sec-->>PG: Traffic Allowed (Source EC2 IP whitelisted)

    Note over App,PG: Layer 2: TCP 3-Way Handshake (OS Network Level)
    App->>PG: TCP SYN (Let's establish a raw byte stream)
    PG-->>App: TCP SYN-ACK (Acknowledged, ready)
    App->>PG: TCP ACK (Connected!)

    Note over App,PG: Layer 3: SSL / TLS Encryption Handshake (Security Level)
    App->>PG: SSLRequest Code (80877103)
    PG-->>App: Server Reply 'S' (SSL supported)
    App->>PG: TLS ClientHello
    PG-->>App: TLS ServerHello + Server Certificate (RDS CA)
    App->>PG: Verify Cert & Key Exchange (ECDHE)
    Note over App,PG: 🔒 Channel is now 100% Encrypted

    Note over App,PG: Layer 4: PostgreSQL Authentication & Startup Handshake
    App->>PG: StartupMessage (user="dbuser", db="appdb")
    PG-->>App: AuthenticationSASL (Requests SCRAM-SHA-256 auth)
    App->>PG: SASLInitialResponse (Client password proof)
    PG-->>App: AuthenticationOk (Password verified! Access granted)
    PG-->>App: ReadyForQuery ('Z' message: "I am ready for SQL commands")
    
    Note over App: Socket is placed into FastAPI's Connection Pool (Idle & Ready)
```

---

### 3. ⏱️ Breakdown of Each Handshake Layer

| Layer | Protocol | What is Verified? | What Fails if Broken? |
| :--- | :--- | :--- | :--- |
| **1. AWS Network** | AWS Security Groups / VPC | Is EC2's IP allowed to talk to Postgres on Port 5432? | `Connection timed out` / Hangs forever. |
| **2. Transport** | TCP (Layer 4) | Can the two operating systems exchange IP packets? | `Connection Refused` (Postgres not running). |
| **3. Encryption** | SSL / TLS (Layer 6) | Is the connection encrypted? Is the server's certificate valid? | `SSLError: Certificate verify failed`. |
| **4. Application** | Postgres SCRAM-SHA-256 | Is username/password valid? Does the database `appdb` exist? | `FATAL: password authentication failed for user`. |

---

### 4. ⚡ How It Works in FastAPI Code (SQLAlchemy / asyncpg)

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# 1. DEFINE THE CONNECTION POOL AT STARTUP
DATABASE_URL = "postgresql+asyncpg://dbuser:mypassword@db.internal:5432/appdb"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,         # Keep 10 pre-warmed, authenticated sockets open
    max_overflow=5,       # Allow up to 5 extra temporary sockets during traffic spikes
    pool_timeout=30,      # Wait max 30s for a free socket before erroring
    pool_recycle=1800,    # Recycle connections every 30 minutes
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency to borrow a connection from the pool
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session # 2. Sits here while query runs, returns socket to pool when done

# 3. RUNTIME ENDPOINT
@app.get("/users/{user_id}")
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    # Sockets are ALREADY authenticated! Zero handshake delay here!
    result = await db.execute(f"SELECT name, email FROM users WHERE id = {user_id}")
    return result.mappings().first()
```

---

### 5. 🔄 Full Runtime Flow (User Click $\rightarrow$ JSON Response)

When a real user hits `GET https://api.myapp.com/users/42`:

```text
1. User clicks in Frontend ──> Hits FastAPI over HTTPS (40ms)
2. FastAPI receives request  ──> Enters get_user_profile()
3. FastAPI borrows Socket #1 ──> (0ms delay - already handshaked & authenticated!)
4. Sends SQL over Socket #1 ──> "SELECT name, email FROM users WHERE id = 42"
5. Postgres executes SQL     ──> Takes 1.5ms
6. Postgres returns rows     ──> Socket #1 is released back into Pool
7. FastAPI serializes JSON   ──> Returns 200 OK {"name": "Alice", "email": "alice@site.com"}
Total Time: ~45ms
```
