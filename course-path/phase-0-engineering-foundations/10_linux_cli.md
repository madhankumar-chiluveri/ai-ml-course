# 0.10 — Linux CLI

**Phase 0 · CORE · CODE · 6 focused hours · Review in 7 days**

**Companion script:** [`10_linux_cli.py`](10_linux_cli.py) — standard library only, no installs. It builds a throwaway 20,000-line log and a fake project tree under the system temp folder, analyses them, and deletes everything afterwards. Where real POSIX tools exist (Linux, macOS, WSL, or Git Bash on Windows) it **runs the actual shell pipelines** and shows their output; where they do not, the Python equivalent still runs, so every lesson lands.

---

## 1. Overview

Docker in **0.11**, OCI in **0.13**, and every production deployment in **7.11** happen over SSH on a Linux box. `tail -f` on a log is how you debug a running agent before **7.6** tracing exists to do it properly.

The specific reason this earns a slot on an AI path rather than being assumed: **the failures you will hit here are resource and permission failures, not logic failures.** A PyTorch process killed silently by the OOM killer during **3.10**. A port still bound after a crashed container in **0.11**. A permission-denied on an SSH key blocking **0.13** on the very first connection. Each has a one-line diagnostic, and not knowing it turns a two-minute fix into an afternoon.

Depends on nothing; unlocks **0.11**, **0.12**, **0.13**, and **7.11**.

---

## 2. Skip Test — Answered

> Gate **before** studying. Both correct from memory → skip. §7 withholds its answers deliberately.

**① How would you find which process is holding port 8000, and stop it?**

Find the owner with `ss -ltnp | grep :8000` on Linux (`lsof -i :8000` on macOS, `netstat -ano | findstr ":8000"` on Windows). The flags: `-l` listening, `-t` TCP, `-n` numeric ports, `-p` show the owning process.

Then stop it with `kill -TERM <pid>` — **not** `kill -KILL`. `TERM` asks politely, letting the process flush logs, close connections and finish the request it is serving. `KILL` cannot be caught or ignored, so it skips all of that and can leave half-written files behind. Reach for `KILL` only when `TERM` has already failed.

Demo 2 triggers the error for real by binding a port twice, so you see the exact message the operating system produces.

**② What does `chmod 600` do, and why does an SSH key need it?**

`600` is `rw- --- ---`: the owner can read and write; group and other get nothing. Each octal digit is three bits — read 4, write 2, execute 1 — for owner, group and other respectively.

SSH **refuses** to use a private key if any group or other bit is set. The reasoning is that a key readable by anyone else on the machine must be treated as already compromised. The trap is that the error message says `UNPROTECTED PRIVATE KEY FILE` and never mentions `chmod`, which is why it costs an hour the first time and five seconds thereafter. Both the key **and** its directory need fixing: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_ed25519`.

---

## 3. Visual Concept Diagrams

### 3.1 — A pipeline is a chain of filters

Read it **right to left** as a question: what do I want, and what must be true for that to work?

```mermaid
flowchart LR
    LOG["app.log<br>20,000 lines"] --> G["grep ERROR<br>keep only errors<br>→ 2,080 lines"]
    G --> C["cut / awk<br>keep only the message"]
    C --> S["sort<br>group identical<br>lines together"]
    S --> U["uniq -c<br>count each distinct one"]
    U --> R["sort -rn<br>rank by count"]
    R --> OUT["536 timeout calling provider<br>534 rate limited by provider<br>517 connection refused<br>493 out of memory"]

    S -.->|"uniq only collapses<br>ADJACENT duplicates —<br>without this sort, every<br>count is wrong"| U

    style G fill:#005f73,stroke:#0a9396,color:#fff
    style S fill:#7f5539,stroke:#b08968,color:#fff
    style OUT fill:#1b4332,stroke:#40916c,color:#fff
```

### 3.2 — `cut` versus `awk` on padded columns, as measured

The wrong version does not error. It returns plausible numbers.

```mermaid
flowchart TD
    LINE["log line, columns PADDED to fixed width<br>'2026-08-01T10:00:00 ERROR gateway   timeout calling provider'"]

    LINE --> CUT["cut -d' ' -f4-<br>splits on EVERY single space"]
    LINE --> AWK["awk '{print substr($0, index($0,$4))}'<br>splits on RUNS of whitespace"]

    CUT --> CUT2["different leading spaces per line<br>→ 'identical' messages never group"]
    AWK --> AWK2["padding absorbed<br>→ messages group correctly"]

    CUT2 --> CUT3["221 timeout calling provider<br>115 connection refused<br>111  timeout calling provider<br>SAME MESSAGE, SPLIT ACROSS ROWS"]
    AWK2 --> AWK3["536 timeout calling provider<br>534 rate limited by provider<br>517 connection refused<br>493 out of memory"]

    CUT3 --> WORSE["No error. No warning.<br>Plausible numbers you would<br>have believed and reported."]

    style CUT fill:#9b2226,stroke:#ae2012,color:#fff
    style CUT3 fill:#9b2226,stroke:#ae2012,color:#fff
    style WORSE fill:#9b2226,stroke:#ae2012,color:#fff
    style AWK fill:#1b4332,stroke:#40916c,color:#fff
    style AWK3 fill:#1b4332,stroke:#40916c,color:#fff
```

### 3.3 — Permission bits, and the SSH gate

```mermaid
flowchart TD
    OCT["octal digit = r(4) + w(2) + x(1)<br>three digits: owner · group · other"]

    OCT --> M600["600 = rw- --- ---<br>SSH private key, .env"]
    OCT --> M644["644 = rw- r-- r--<br>public keys, configs"]
    OCT --> M700["700 = rwx --- ---<br>the ~/.ssh directory"]
    OCT --> M755["755 = rwx r-x r-x<br>directories, executables"]
    OCT --> M777["777 = rwx rwx rwx<br>never"]

    M600 --> GATE{"SSH checks the key:<br>any group or other bit set?"}
    M644 --> GATE
    M777 --> GATE

    GATE -->|"yes"| NO["REFUSED<br>'UNPROTECTED PRIVATE KEY FILE'<br>— the message never says chmod"]
    GATE -->|"no"| YES["accepted"]

    NO --> FIX["chmod 700 ~/.ssh<br>chmod 600 ~/.ssh/id_ed25519<br>BOTH are required"]

    style M600 fill:#1b4332,stroke:#40916c,color:#fff
    style YES fill:#1b4332,stroke:#40916c,color:#fff
    style M777 fill:#9b2226,stroke:#ae2012,color:#fff
    style NO fill:#9b2226,stroke:#ae2012,color:#fff
    style FIX fill:#2d6a4f,stroke:#52b788,color:#fff
```

### 3.4 — Exit codes: how a broken CI step passes forever

```mermaid
flowchart TD
    P["grep ERROR missing-file.log | wc -l"]

    P --> G["grep runs<br>file does not exist<br>EXIT 2 — FAILED"]
    G --> W["wc -l runs on empty input<br>prints 0<br>EXIT 0 — succeeded"]

    W --> D{"what does the<br>SHELL report?"}
    D -->|"default"| BAD["exit=0 — SUCCESS<br>only the LAST command's<br>status is kept"]
    D -->|"set -o pipefail"| GOOD["exit=2 — FAILURE<br>any stage failing<br>fails the pipeline"]

    BAD --> CI["A CI step written this way<br>passes forever while testing<br>nothing at all — 7.5"]
    GOOD --> SAFE["set -euo pipefail<br>at the top of every script"]

    style BAD fill:#9b2226,stroke:#ae2012,color:#fff
    style CI fill:#9b2226,stroke:#ae2012,color:#fff
    style GOOD fill:#1b4332,stroke:#40916c,color:#fff
    style SAFE fill:#2d6a4f,stroke:#52b788,color:#fff
```

---

## 4. Core Technical Deep Dive

| Symptom | The command that diagnoses it | Where it bites |
|---|---|---|
| "Address already in use" | `ss -ltnp \| grep :8000` | **0.9** restarts, **0.11**, **7.11** |
| Training died with no traceback | `dmesg -T \| grep -i "killed process"` | **3.10**, **4.11** |
| Disk full, unclear why | `du -sh -- * .[!.]* \| sort -rh` | **7.10** MLflow runs, **5.2** indexes |
| SSH key rejected | `chmod 600` the key, `700` the dir | **0.13** first connection |
| Job dies when the laptop sleeps | `tmux new -s train`, detach with `Ctrl-b d` | **4.11** long fine-tunes |
| Need to watch a bug happen | `tail -f` / `docker logs -f` | everything before **7.6** |
| Secret about to be committed | `grep -rn "API_KEY" . --exclude-dir=.venv` | **0.4**, **7.13** |
| CI step passes but tests nothing | `set -euo pipefail` | **7.5** |

**The commands worth having in muscle memory:**

```bash
# Orientation
pwd; ls -lah          # -a matters: .env and .venv are hidden by default
cd -                  # jump back to the previous directory

# Resource checks — the AI-specific failures
free -h               # if `available` is near zero, the OOM killer is coming (3.10)
df -h                 # checkpoints and vector indexes fill disks quietly and fast
nvidia-smi            # GPU memory and utilisation, if a GPU exists
dmesg -T | grep -i "killed process"   # WAS my training run OOM-killed?

# Environment variables
set -a; source .env; set +a   # -a exports everything defined, so CHILD processes see it
printenv | grep -i api        # what is actually set right now

# Long-running jobs over SSH — a 6-hour fine-tune (4.11) must not depend on your laptop
tmux new -s train     # ... start the job ... then Ctrl-b then d to detach
tmux attach -t train  # reattach later, from anywhere
```

**Why `du -sh */` is the wrong habit.** Demo 4 runs both forms on the same tree. `*/` is a shell glob, and shell globs **do not match names beginning with a dot**. So `.venv/` — 2.4 MB, the second-largest directory present — is completely absent from the output. That is not a corner case: `.venv`, `.cache`, `.git` and `~/.ollama` are precisely where disk goes. Use `du -sh -- * .[!.]* | sort -rh` instead.

**Why `sort -rh` and not `sort -r`.** `-h` compares human-readable sizes numerically, so `2G` ranks above `900M`. Plain `sort` compares text, which puts `900M` first.

**`kill -TERM` versus `kill -KILL`.** `TERM` is a request the process can catch — it can flush its logs, close database connections and finish the in-flight request. `KILL` cannot be caught, so none of that happens. Using `KILL` first is how you get a corrupt checkpoint file and a database connection that stays open until it times out server-side.

**The OOM killer leaves no traceback.** A training process that vanishes with no error and no stack trace was almost certainly killed by the kernel for using too much memory. Nothing appears in your application log, because your application never got to run any code. The evidence lives in `dmesg`.

---

## 5. Hands-On Script & Verified Output

Run: `python 10_linux_cli.py`. Output below is **actual, captured** on Windows with Git Bash providing the POSIX tools. On Linux, macOS or WSL the same pipelines run natively.

```text
platform: win32 | POSIX tools available: True
scratch dir: ...\Temp\cli-demo-k9p1ofg9  (safe - deleted at the end)
======================================================================
DEMO 1 - a pipeline is a chain of filters, built one stage at a time
======================================================================
  app.log has 20,000 lines. Reading it by hand is not an option.

  $ wc -l < app.log                       (how big is the problem)
    20000

  $ grep ERROR app.log | wc -l            (how many are errors)
    2080

  $ grep ERROR app.log | awk '{print $2, $3}' | head -3
    ERROR gateway
    ERROR retriever
    ERROR gateway

  $ grep ERROR app.log | cut -d' ' -f4- | sort | uniq -c | sort -rn | head -6
    (ranked with cut - LOOKS fine, is WRONG)
        221   timeout calling provider
        211   connection refused
        210   rate limited by provider
        188   out of memory
        115  connection refused
        111    timeout calling provider

  $ grep ERROR app.log | awk '{print substr($0, index($0,$4))}' | sort | uniq -c | sort -rn
    (ranked with awk - correct)
        536 timeout calling provider
        534 rate limited by provider
        517 connection refused
        493 out of memory
======================================================================
DEMO 2 - 'address already in use', triggered on purpose
======================================================================
  a socket is now holding 127.0.0.1:58436
  binding it again -> OSError [10048] Only one usage of each socket address
                      (protocol/network address/port) is normally permitted

  Finding WHO holds it:
    Windows : netstat -ano | findstr ":58436"
    Linux   : ss -ltnp | grep :58436
    macOS   : lsof -i :58436
======================================================================
DEMO 3 - permission bits, and why SSH refuses a readable key
======================================================================
  Each octal digit is three bits: read=4, write=2, execute=1
  octal   owner  group  other  typical use
  ------- ------ ------ ------ ----------------------------------
  600     rw-    ---    ---    SSH PRIVATE KEY, .env
  644     rw-    r--    r--    public keys, config files
  700     rwx    ---    ---    the ~/.ssh directory itself
  755     rwx    r-x    r-x    directories, executables
  777     rwx    rwx    rwx    never - world-writable
======================================================================
DEMO 4 - 'disk full' - find the culprit in one command
======================================================================
  $ du -sh */ | sort -rh          <- the version everyone writes
    3.0M    checkpoints/
    1.5M    data/
    900K    mlruns/
    120K    notebooks/
    40K     src/

  $ du -sh -- * .[!.]* | sort -rh   <- includes DOTFILES
    3.0M    checkpoints
    2.4M    .venv
    1.5M    data
    968K    app.log
    900K    mlruns
    120K    notebooks
    40K     src
    1.0K    id_ed25519

  ^ .venv/ appears only in the second listing.
======================================================================
DEMO 5 - tail -f sees lines that did not exist when you started
======================================================================
  cat live.log (before)  -> 1 line(s): ['startup complete']

  tail -f live.log       -> (following, lines appear as written)
    [16:28:14] request 0 handled
    [16:28:14] request 1 handled
    [16:28:14] request 2 handled
    [16:28:14] request 3 handled
    [16:28:14] request 4 handled

  cat saw 1 line(s); the follower saw 5 MORE that were written afterwards.
======================================================================
DEMO 6 - a pipeline reports SUCCESS when a middle command fails
======================================================================
  the happy path                         -> 2080  exit=0
  grep FAILS - file does not exist       -> 0  exit=0
  same command, with pipefail            -> 0  exit=2
======================================================================
cleaned up ...\Temp\cli-demo-k9p1ofg9
```

**Demo 1 contains a deliberate wrong answer, and it is the most useful thing on the page.** The `cut` version and the `awk` version rank the same 2,080 errors. `cut` reports `221 timeout calling provider` and, four rows later, `111   timeout calling provider` again — the same message split across multiple rows because the log pads its columns and `cut -d' '` treats every single space as a separator. `awk` splits on *runs* of whitespace and gets `536`. Nothing errored. Nothing warned. The wrong pipeline produced numbers you would have put in a report.

**Demo 2 produces the real operating-system error**, not a description of it: `OSError [10048]` on Windows, `EADDRINUSE` on Linux. This is the exact message left behind by a FastAPI process from **0.9** that did not shut down cleanly, or a crashed container from **0.11**.

**Demo 4 shows a habit that hides the answer.** `du -sh */` lists five directories and misses `.venv` at 2.4 MB — the second-largest thing in the tree — because shell globs skip dotted names. The second command finds it. On a real machine the hidden offenders are `.venv`, `.cache`, `.git` and model caches, and they are exactly what fills a small cloud disk in **0.13**.

**Demo 5 makes the point of `tail -f` concrete.** `cat` saw **1** line. The follower saw **5 more** that did not exist when it started reading. That is why you start the tail *before* reproducing the bug, and it is the same mechanism behind `docker logs -f` (**0.11**) and `journalctl -u svc -f` (**7.11**).

**Demo 6 is the one that silently ruins CI.** `grep` on a nonexistent file exits `2` — a genuine failure — and the pipeline still reports `exit=0`, because a shell keeps only the **last** command's status. With `set -o pipefail` the same command reports `exit=2`. A CI step (**7.5**) written without it passes forever while testing nothing.

**Modify and re-run:**
- In Demo 1, remove the `sort` before `uniq -c` and compare the counts. `uniq` only collapses *adjacent* duplicates, so the result becomes nonsense — quietly.
- In Demo 4, add a `.cache` directory larger than `checkpoints/` and re-run both `du` forms. Confirm the first still hides it.
- In Demo 5, remove the `f.flush()` in the writer and re-run. The follower will see nothing until the buffer fills — the same reason a container's logs sometimes appear to stop.
- In Demo 6, add `set -e` to the failing pipeline and observe that it alone is **not** enough; `pipefail` is the part that matters here.
- Change the log format in `build_tree` to comma-separated and rewrite Demo 1's pipeline with `cut -d','`. On unpadded delimited data, `cut` is the right tool — find out why.

---

## 6. Video

**"The 50 Most Popular Linux & Terminal Commands - Full Course for Beginners"** — *freeCodeCamp.org*, developed by Colt Steele — [youtube.com/watch?v=ZtqBQ68cfJc](https://www.youtube.com/watch?v=ZtqBQ68cfJc). Verified live. ~5 hours covering navigation, file manipulation, permissions and process management; every command works on Linux, macOS and WSL.

It is ~5 hours end to end. If basic navigation is comfortable, skip to the permissions and process-management sections — those are the parts that block **0.13**.

---

## 7. Retrieval Checkpoint — Unanswered

> Close this file. No notes. Answers deliberately withheld.

1. Your FastAPI app will not start: "address already in use" on port 8000. Give the exact command to find the owning process, and the command to stop it gracefully — and say what the ungraceful version risks.
2. What does `chmod 600` set, and why specifically does SSH refuse a private key with looser permissions? Name the *second* path that also needs fixing.
3. A PyTorch training run vanished with no traceback and no error message. Which command tells you whether the kernel killed it, and why is your application log empty?
4. `du -sh */ | sort -rh` reports 4 GB total but `df -h` says 30 GB is used. Give the most likely explanation and the corrected command.
5. A CI step runs `pytest --json | jq .summary` and has passed for months. Explain how it could be passing without ever running a test, and the one line that would have caught it.

---

## 8. Closed-Book Rebuild

With this file **and** the script closed, from a fresh shell: find which process holds a given port and stop it gracefully; tail a log filtered to errors *while* the errors are being written; check whether free memory is about to run out and whether a process was previously OOM-killed; set correct permissions on an SSH key and its directory; load a `.env` so a **child** process can see the variables; start a detachable session for a long job; and write a five-stage pipeline that ranks the most common error in a padded log — using the tool that handles the padding correctly.

---

## 9. Glossary

**Pipe (`|`)** — connects one command's stdout to the next command's stdin. The composition primitive the whole shell is built on.

**`grep -rn`** — search recursively, showing line numbers. The cheapest possible secret scan before a commit (**0.4**).

**`cut -d' '`** — split on a single-character delimiter. Treats **every** occurrence as a separator, so it breaks on padded columns.

**`awk`** — a field-aware text processor. Splits on runs of whitespace by default, which is why it survives padding.

**`uniq -c`** — count consecutive identical lines. Requires sorted input; without it the counts are silently wrong.

**`sort -rh`** — reverse, human-numeric. Ranks `2G` above `900M`; plain `sort` does not.

**`ss -ltnp`** — listening, TCP, numeric, with process. The modern replacement for `netstat`.

**`SIGTERM` / `SIGKILL`** — a catchable stop request versus an uncatchable one. `TERM` allows cleanup; `KILL` does not.

**OOM killer** — the kernel subsystem that terminates a process when the machine runs out of memory. Leaves no application-level traceback; evidence is in `dmesg`.

**Octal permission bits** — three digits (owner, group, other), each summing read 4, write 2, execute 1.

**`tail -f`** — seek to the end of a file and keep reading as new data is appended. The live-debugging tool before tracing exists (**7.6**).

**Exit status** — a command's numeric result; `0` is success. A pipeline reports only its **last** command's status unless `pipefail` is set.

**`set -euo pipefail`** — exit on error, error on unset variable, fail the pipeline if any stage fails. The first line of every serious shell script.

**`tmux`** — a terminal multiplexer. Lets a long job survive the SSH session that started it.

---

## Review again in

**7 days** — most of this is quick to absorb. Three things are worth retaining because each costs real time the first time: the **OOM-kill diagnostic**, the **SSH permission rule**, and `set -euo pipefail`. Add a fourth if you write pipelines against logs: `cut` and `awk` are not interchangeable, and only one of them tells you when it got it wrong.
