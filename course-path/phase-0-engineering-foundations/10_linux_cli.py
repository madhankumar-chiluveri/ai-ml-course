"""
0.10 - Linux CLI.

Runnable: `python 10_linux_cli.py`
Requires: nothing. Standard library only.

SAFE: builds a throwaway log file and directory tree under the system temp
folder, analyses it, and deletes it. Nothing of yours is touched.

CROSS-PLATFORM: where real POSIX tools exist (Linux, macOS, WSL, or Git Bash
on Windows) the actual shell pipelines are RUN and their output shown. Where
they do not, the Python equivalent still runs, so every lesson lands.

What this proves practically:
  1. A pipeline is a chain of filters. Built up one stage at a time.
  2. "Address already in use" - triggered for real, then diagnosed.
  3. Permission bits are three octal digits. Why SSH refuses anything but 600.
  4. du | sort finds what is eating the disk. Usually not what you expect.
  5. tail -f sees lines that did not exist when you started reading.
  6. A pipeline REPORTS SUCCESS when a middle command fails. The CI trap.
"""

import os
import random
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

SEP = "=" * 70
IS_WINDOWS = sys.platform == "win32"
BASH = shutil.which("bash")
HAVE_POSIX = BASH is not None and shutil.which("grep") is not None

LEVELS = ["INFO"] * 60 + ["WARN"] * 12 + ["ERROR"] * 8
SERVICES = ["scorer", "retriever", "gateway", "embedder", "planner"]
MESSAGES = {
    "INFO": ["request served", "cache hit", "model warm"],
    "WARN": ["slow response", "retry scheduled", "queue depth high"],
    "ERROR": ["timeout calling provider", "rate limited by provider",
              "out of memory", "connection refused"],
}


def sh(script: str, cwd: Path) -> str:
    """Run a real shell pipeline and return its stdout."""
    r = subprocess.run([BASH, "-c", script], cwd=cwd,
                       capture_output=True, text=True)
    return r.stdout.rstrip("\n")


# ==================================================================== setup
def build_tree(base: Path) -> Path:
    """A miniature version of a real project after a few weeks of work."""
    rng = random.Random(42)
    log = base / "app.log"
    with log.open("w", encoding="utf-8", newline="\n") as f:
        for i in range(20_000):
            lvl = rng.choice(LEVELS)
            svc = rng.choice(SERVICES)
            msg = rng.choice(MESSAGES[lvl])
            f.write(f"2026-08-01T10:{i//600:02d}:{(i//10)%60:02d} "
                    f"{lvl:<5} {svc:<9} {msg}\n")

    # Directories sized to mimic what actually fills a disk on this path.
    sizes = {
        "mlruns": 900, "data/raw": 1500, ".venv": 2400,
        "src": 40, "notebooks": 120, "checkpoints": 3000,
    }
    for rel, kb in sizes.items():
        d = base / rel
        d.mkdir(parents=True, exist_ok=True)
        (d / "blob.bin").write_bytes(b"x" * (kb * 1024))
    return log


# ===================================================================== 1
def demo_pipeline(base: Path, log: Path) -> None:
    print(SEP)
    print("DEMO 1 - a pipeline is a chain of filters, built one stage at a time")
    print(SEP)

    total = sum(1 for _ in log.open(encoding="utf-8"))
    print(f"  app.log has {total:,} lines. Reading it by hand is not an option.")

    if HAVE_POSIX:
        stages = [
            ("wc -l < app.log", "how big is the problem"),
            ("grep ERROR app.log | wc -l", "how many are errors"),
            ("grep ERROR app.log | awk '{print $2, $3}' | head -3",
             "what do they look like"),
            # WRONG ON PURPOSE. The log pads its columns, so `cut -d' '`
            # keeps a different number of leading spaces per line and the
            # "identical" messages never group. Counts come out fragmented.
            ("grep ERROR app.log | cut -d' ' -f4- | sort | uniq -c "
             "| sort -rn | head -6", "ranked with cut - LOOKS fine, is WRONG"),
            # RIGHT. awk splits on RUNS of whitespace, so padding is absorbed.
            ("grep ERROR app.log | awk '{print substr($0, index($0,$4))}' "
             "| sort | uniq -c | sort -rn", "ranked with awk - correct"),
        ]
        for cmd, why in stages:
            print(f"\n  $ {cmd}")
            print(f"    ({why})")
            for line in sh(cmd, base).splitlines()[:6]:
                print(f"    {line}")
        print("\n  ^ Compare those last two blocks. `cut -d' '` treats EVERY")
        print("    space as a separator, so a column padded to a fixed width")
        print("    yields a different string per line and uniq never groups")
        print("    them. awk splits on RUNS of whitespace and gets it right.")
        print("    The wrong one produced plausible numbers - which is worse")
        print("    than an error, because you would have believed them.")
    else:
        print("\n  (no POSIX shell found - showing the Python equivalent only)")

    # The same answer in Python, so the lesson survives without a shell.
    errs = [l for l in log.read_text(encoding="utf-8").splitlines()
            if " ERROR " in l]
    ranked = Counter(" ".join(l.split()[3:]) for l in errs).most_common()
    print("\n  Python equivalent, same answer:")
    for msg, n in ranked:
        print(f"    {n:>5}  {msg}")

    print("\n  Read the pipeline right to left as a question:")
    print("    sort -rn  <- rank them")
    print("    uniq -c   <- count each distinct one  (REQUIRES sorted input)")
    print("    sort      <- group identical lines together")
    print("    cut       <- keep only the message")
    print("    grep      <- keep only errors")
    print("  `uniq` only collapses ADJACENT duplicates. Forgetting the sort")
    print("  before it is the single most common pipeline bug.")


# ===================================================================== 2
def demo_port_in_use() -> None:
    print(SEP)
    print("DEMO 2 - 'address already in use', triggered on purpose")
    print(SEP)

    holder = socket.socket()
    holder.bind(("127.0.0.1", 0))
    holder.listen(1)
    port = holder.getsockname()[1]
    print(f"  a socket is now holding 127.0.0.1:{port}")

    second = socket.socket()
    try:
        second.bind(("127.0.0.1", port))
        print("  second bind succeeded - unexpected")
    except OSError as e:
        print(f"  binding it again -> OSError [{e.errno}] {e.strerror}")
        print("  ^ this is the exact error a restarted FastAPI (0.9) or a")
        print("    crashed container (0.11) leaves behind.")
    finally:
        second.close()

    print("\n  Finding WHO holds it:")
    if IS_WINDOWS:
        cmd = f'netstat -ano | findstr ":{port}"'
        print(f"    Windows : {cmd}")
        r = subprocess.run(["cmd", "/c", cmd], capture_output=True, text=True)
        for line in r.stdout.splitlines()[:3]:
            print(f"      {line.strip()}")
        print(f"    Linux   : ss -ltnp | grep :{port}")
        print(f"    macOS   : lsof -i :{port}")
    else:
        for cmd in (f"ss -ltnp | grep :{port}", f"lsof -i :{port}"):
            if shutil.which(cmd.split()[0]):
                print(f"    $ {cmd}")
                for line in sh(cmd, Path.cwd()).splitlines()[:3]:
                    print(f"      {line}")
                break

    print("\n  Then stop it - and the choice matters:")
    print("    kill -TERM <pid>   ask politely: the process can flush logs,")
    print("                       close connections, finish a request")
    print("    kill -KILL <pid>   force: no cleanup, no flush, corrupt")
    print("                       half-written files. Only if TERM fails.")
    holder.close()
    print(f"\n  (port {port} released)")


# ===================================================================== 3
def demo_permissions(base: Path) -> None:
    print(SEP)
    print("DEMO 3 - permission bits, and why SSH refuses a readable key")
    print(SEP)

    print("  Each octal digit is three bits: read=4, write=2, execute=1")
    print(f"  {'octal':<7} {'owner':<6} {'group':<6} {'other':<6} typical use")
    print(f"  {'-'*7} {'-'*6} {'-'*6} {'-'*6} {'-'*34}")
    for octal, use in [("600", "SSH PRIVATE KEY, .env"),
                       ("644", "public keys, config files"),
                       ("700", "the ~/.ssh directory itself"),
                       ("755", "directories, executables"),
                       ("777", "never - world-writable")]:
        bits = [("r" if int(d) & 4 else "-") + ("w" if int(d) & 2 else "-")
                + ("x" if int(d) & 1 else "-") for d in octal]
        print(f"  {octal:<7} {bits[0]:<6} {bits[1]:<6} {bits[2]:<6} {use}")

    key = base / "id_ed25519"
    key.write_text("FAKE KEY - not a real credential\n",
                   encoding="utf-8", newline="\n")

    if IS_WINDOWS:
        print("\n  (Windows does not use POSIX mode bits - the numbers above")
        print("   apply the moment you SSH into a Linux box in 0.13, and on")
        print("   WSL. Windows enforces the same idea through ACLs instead.)")
    else:
        for mode in (0o644, 0o600):
            key.chmod(mode)
            got = stat.S_IMODE(key.stat().st_mode)
            verdict = ("SSH REFUSES THIS" if got & 0o077 else "SSH accepts")
            print(f"\n  chmod {mode:o} -> stat says {got:o}   {verdict}")

    print("\n  The rule: if ANY bit is set for group or other, SSH rejects the")
    print("  key outright. The error says 'UNPROTECTED PRIVATE KEY FILE' and")
    print("  never says 'chmod', which is why it costs an hour the first time.")
    print("  Fix:  chmod 700 ~/.ssh  &&  chmod 600 ~/.ssh/id_ed25519")


# ===================================================================== 4
def demo_disk_usage(base: Path) -> None:
    print(SEP)
    print("DEMO 4 - 'disk full' - find the culprit in one command")
    print(SEP)

    if HAVE_POSIX:
        # WRONG ON PURPOSE: the glob */ does not match hidden directories,
        # so the single biggest offender is invisible in this listing.
        print("  $ du -sh */ | sort -rh          <- the version everyone writes")
        for line in sh("du -sh */ 2>/dev/null | sort -rh", base).splitlines()[:8]:
            print(f"    {line}")

        print("\n  $ du -sh -- * .[!.]* | sort -rh   <- includes DOTFILES")
        for line in sh("du -sh -- * .[!.]* 2>/dev/null | sort -rh",
                       base).splitlines()[:8]:
            print(f"    {line}")
        print("\n  ^ .venv/ appears only in the second listing. Hidden")
        print("    directories are exactly where the space goes: .venv,")
        print("    .cache, .git, ~/.ollama. The habit of writing */ hides them.")
    else:
        print("  (no POSIX shell - Python equivalent below)")

    sizes = []
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        sizes.append((total, d.name))
    print("\n  Python equivalent, largest first:")
    for total, name in sorted(sizes, reverse=True):
        print(f"    {total/1024/1024:6.1f} MB  {name}/")

    print("\n  -s summarise per argument, -h human-readable, sort -rh sorts")
    print("  those human sizes correctly (2G above 900M). Plain `sort` would")
    print("  put 900M first because it compares text.")
    print("\n  On this path the usual offenders are checkpoints/ and data/raw/,")
    print("  then mlruns/ (7.10) and vector indexes (5.2). All are in .gitignore")
    print("  for a reason (0.4) - and none of them free space by being ignored.")


# ===================================================================== 5
def demo_tail_follow(base: Path) -> None:
    print(SEP)
    print("DEMO 5 - tail -f sees lines that did not exist when you started")
    print(SEP)

    live = base / "live.log"
    live.write_text("startup complete\n", encoding="utf-8", newline="\n")

    stop = threading.Event()

    def writer():
        # A running service, emitting as it works.
        for i in range(5):
            if stop.is_set():
                return
            with live.open("a", encoding="utf-8", newline="\n") as f:
                f.write(f"request {i} handled\n")
                f.flush()          # flush or the follower sees nothing
            time.sleep(0.2)

    # (a) read the whole file ONCE - what `cat` does
    snapshot = live.read_text(encoding="utf-8").splitlines()
    print(f"  cat live.log (before)  -> {len(snapshot)} line(s): {snapshot}")

    t = threading.Thread(target=writer, daemon=True)
    t.start()

    # (b) follow it - what `tail -f` does: seek to the end, then poll
    print("\n  tail -f live.log       -> (following, lines appear as written)")
    seen, deadline = [], time.time() + 2.0
    with live.open(encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)             # start at the END, not the start
        while time.time() < deadline and len(seen) < 5:
            line = f.readline()
            if not line:
                time.sleep(0.05)           # no new data yet; wait, do not exit
                continue
            seen.append(line.rstrip())
            print(f"    [{time.strftime('%H:%M:%S')}] {line.rstrip()}")
    stop.set()
    t.join(timeout=1)

    print(f"\n  cat saw {len(snapshot)} line(s); the follower saw "
          f"{len(seen)} MORE that were written afterwards.")
    print("  That is the whole difference, and it is why you start the tail")
    print("  BEFORE reproducing the bug - not after.")
    print("\n  Same idea, three places you will need it:")
    print("    tail -f app.log            a plain process")
    print("    docker logs -f <name>      a container (0.11)")
    print("    journalctl -u svc -f       a systemd service (7.11)")
    print("  Filter live with:  tail -f app.log | grep -i error")


# ===================================================================== 6
def demo_exit_codes(base: Path) -> None:
    print(SEP)
    print("DEMO 6 - a pipeline reports SUCCESS when a middle command fails")
    print(SEP)

    if not HAVE_POSIX:
        print("  (needs a POSIX shell - skipped. The lesson, in one line:)")
        print("  `a | b` reports only b's exit status, so a's failure is lost")
        print("  unless you set -o pipefail. This is how broken CI steps pass.")
        return

    checks = [
        ("grep ERROR app.log | wc -l; echo exit=$?",
         "the happy path"),
        ("grep ERROR missing-file.log | wc -l; echo exit=$?",
         "grep FAILS - file does not exist"),
        ("set -o pipefail; grep ERROR missing-file.log | wc -l; echo exit=$?",
         "same command, with pipefail"),
    ]
    for cmd, label in checks:
        out = sh(cmd + " 2>/dev/null", base).replace("\n", "  ")
        print(f"  {label:<38} -> {out}")

    print("\n  The middle line is the trap. grep failed, the file does not")
    print("  exist, wc printed 0 - and the pipeline reported exit=0, SUCCESS.")
    print("  A CI step (7.5) written that way passes forever while testing")
    print("  nothing. `set -euo pipefail` at the top of every script is the")
    print("  fix: -e exit on error, -u error on unset variable, -o pipefail")
    print("  make a pipeline fail if ANY stage fails.")


def main() -> None:
    print(f"platform: {sys.platform} | POSIX tools available: {HAVE_POSIX}"
          + ("" if HAVE_POSIX else "  (Python equivalents will still run)"))
    base = Path(tempfile.mkdtemp(prefix="cli-demo-"))
    print(f"scratch dir: {base}  (safe - deleted at the end)")
    try:
        log = build_tree(base)
        demo_pipeline(base, log)
        demo_port_in_use()
        demo_permissions(base)
        demo_disk_usage(base)
        demo_tail_follow(base)
        demo_exit_codes(base)
        print(SEP)
        print("None of these are logic bugs. They are resource and permission")
        print("failures - the kind that appear only on the box in 0.13 and")
        print("7.11, and each has a one-line diagnostic worth knowing cold.")
        print(SEP)
    finally:
        shutil.rmtree(base, ignore_errors=True)
        print(f"cleaned up {base}")


if __name__ == "__main__":
    main()
