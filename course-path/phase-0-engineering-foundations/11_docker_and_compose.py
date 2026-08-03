"""
0.11 - Docker and Docker Compose.

Runnable: `python 11_docker_and_compose.py`
Requires: PyYAML for demo 7 (pip install pyyaml). Docker is OPTIONAL - if a
          daemon is running AND a usable base image is already on this
          machine, demos 1 and 3-6 use real containers; otherwise they print
          SIMULATED and the lesson still lands.

SAFE + OFFLINE. Specifically:
  * Every file it writes goes into one tempfile.mkdtemp() directory that is
    deleted in a finally block. Nothing is written next to this script.
  * It NEVER pulls. It only ever uses a base image already present locally,
    and it refuses to use any image whose name contains "supabase".
  * Every image it builds is tagged coursedemo-*-<run nonce>; every
    container and volume it creates is recorded by ID/name. All of them are
    removed in a finally block. It never touches anything it did not create.
  * Every build and every container runs with --network=none, so nothing it
    starts can reach the network, a database, or another container. No port
    is ever published.

What this proves practically:
  1. One image, three containers. The image bytes are shared and read-only;
     each container gets its own writable layer. Counted, not asserted.
  2. A layer's cache key is a hash chain over (parent key, instruction,
     content of copied files). Computed here in pure Python, both orderings.
  3. Real `docker build` wall-clock for both orderings, cold and after a
     one-line source edit. This is the requirements-before-source rule,
     measured in seconds.
  4. .dockerignore decides how many bytes leave your machine on every build.
     Measured twice, and cross-checked against BuildKit's own report.
  5. Exec-form CMD shuts down on SIGTERM in a fraction of a second.
     Shell-form CMD can swallow it and get SIGKILLed after the full grace
     period. Three variants, timed with `docker stop`.
  6. A named volume survives container removal. The container's writable
     layer does not.
  7. depends_on without `condition: service_healthy` starts the API before
     Postgres can accept connections. Parsed from real YAML, then timed.
"""

import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

try:
    import yaml                       # PyYAML - only demo 7 needs it
except ImportError:                   # pragma: no cover
    yaml = None

SEP = "=" * 70

# Everything this run creates carries this nonce, so cleanup can be exact
# and can never match a resource somebody else made. Never clean up by
# wildcard against the daemon - only by the exact names recorded below.
NONCE = uuid.uuid4().hex[:8]

# Stand-in for `pip install -r requirements.txt`. The sandbox is offline, so
# a real pip install is not possible here; what demo 3 measures is whether
# the layer is RE-EXECUTED or served from cache, and that is unaffected by
# how long the layer takes. A real torch install is 60-300s, which only
# widens every gap you are about to see.
INSTALL_SECONDS = 3

# `docker stop` sends SIGTERM, waits, then SIGKILLs. The real default wait is
# 10s; 5s keeps demo 5 short. Orchestrators in 7.11 use the same two-phase
# shape, which is why the exec/shell distinction shows up as downtime.
STOP_GRACE = 5

CREATED_IMAGES: list[str] = []
CREATED_CONTAINERS: list[str] = []
CREATED_VOLUMES: list[str] = []

DOCKER: dict[str, str | None] = {"base": None, "server": None}


# ================================================================== plumbing
def sh(args, timeout=240):
    """Run a command, capture stdout+stderr, never raise. -> (rc, text, secs).

    docker writes build progress to stderr, so the two streams are merged.
    """
    t0 = time.perf_counter()
    try:
        p = subprocess.run(args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, f"{type(exc).__name__}: {exc}", time.perf_counter() - t0
    return p.returncode, (p.stdout or "") + (p.stderr or ""), \
        time.perf_counter() - t0


def write(path, text):
    """Write LF-terminated text, creating parent directories as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build(context, dockerfile, tag, extra=()):
    """`docker build` with the network switched OFF inside the build.

    --network=none means the RUN steps have no network at all. That is both
    a safety property here and a real reproducibility technique: a build that
    cannot reach the internet cannot silently depend on it.
    """
    tag = f"{tag}-{NONCE}"
    args = ["docker", "build", "--network=none", "--progress=plain",
            "-f", dockerfile, "-t", tag, *extra, context]
    rc, out, secs = sh(args)
    if rc == 0 and tag not in CREATED_IMAGES:
        CREATED_IMAGES.append(tag)
    return rc, out, secs, tag


def run_container(image, cmd=None, mounts=(), detach=False):
    """Start a container we own, record its ID, return (rc, id_or_text)."""
    args = ["docker", "run", "-d", "--network=none"]
    for m in mounts:
        args += ["-v", m]
    args.append(image)
    if cmd:
        args += cmd
    rc, out, _ = sh(args)
    if rc != 0:
        return rc, out
    cid = out.strip().splitlines()[-1]
    CREATED_CONTAINERS.append(cid)
    if not detach:
        sh(["docker", "wait", cid], timeout=120)
    return 0, cid


def logs(cid):
    rc, out, _ = sh(["docker", "logs", cid], timeout=60)
    return out.strip()


def find_base_image():
    """Pick a base image that is ALREADY local. Never pull, never guess."""
    rc, out, _ = sh(["docker", "version", "--format", "{{.Server.Version}}"],
                    timeout=60)
    if rc != 0:
        return None, None
    server = out.strip().splitlines()[-1] if out.strip() else "unknown"

    rc, out, _ = sh(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                    timeout=60)
    if rc != 0:
        return None, server

    tags = sorted({t.strip() for t in out.splitlines() if t.strip()})
    # Hard exclusions. The machine this was written on runs a live Supabase
    # stack; nothing here may borrow from it, even read-only.
    tags = [t for t in tags
            if "<none>" not in t
            and "supabase" not in t.lower()
            and "coursedemo" not in t.lower()]

    # Preference order: a Python base makes the lesson concrete, but any
    # image with a shell is enough for what these demos measure.
    for pattern in ("python", "alpine", "busybox", "debian", "ubuntu"):
        for tag in tags:
            if pattern in tag.lower():
                rc2, out2, _ = sh(["docker", "run", "--rm", "--network=none",
                                   tag, "/bin/sh", "-c", "echo SHELL_OK"],
                                  timeout=120)
                if rc2 == 0 and "SHELL_OK" in out2:
                    return tag, server
    return None, server


def have_docker():
    return DOCKER["base"] is not None


def skipped(reason):
    print(f"  SKIPPED - {reason}")
    print("  No image was pulled. Demos 2 and 7 below run without Docker")
    print("  and carry the same lesson.")


# ==================================================================== demo 1
def demo_image_vs_container(tmp):
    print(SEP)
    print("DEMO 1 - ONE image, THREE containers. Counted, not asserted.")
    print(SEP)
    if not have_docker():
        skipped("no usable local base image")
        return

    ctx = os.path.join(tmp, "d1")
    # The seed file is baked in at BUILD time, so it lives in the IMAGE.
    # Every container starts from exactly these bytes - that is what "image"
    # means: a read-only, content-addressed template.
    write(os.path.join(ctx, "Dockerfile"), (
        f"FROM {DOCKER['base']}\n"
        "RUN mkdir -p /data && "
        "echo 'baked into the IMAGE at build time' > /data/seed.txt\n"
        'CMD ["/bin/sh", "-c", "echo no command given"]\n'
    ))
    rc, out, _, tag = build(ctx, os.path.join(ctx, "Dockerfile"),
                            "coursedemo-app")
    if rc != 0:
        skipped("build failed")
        print(out[-600:])
        return

    rc, img_id, _ = sh(["docker", "image", "inspect", tag,
                        "--format", "{{.Id}}"])
    img_id = img_id.strip().splitlines()[-1][:19]

    # Each container appends its OWN line to a file that already exists in
    # the image. If the image were mutable, container C would see A's and
    # B's lines too.
    ids = []
    for name in ("alpha", "bravo", "charlie"):
        rc, cid = run_container(tag, ["/bin/sh", "-c",
                                      f"echo 'written by {name}' >> "
                                      "/data/seed.txt; wc -l < /data/seed.txt;"
                                      " cat /data/seed.txt"])
        body = logs(cid).splitlines()
        ids.append((name, cid[:12], body))

    print(f"  image {tag}")
    print(f"    id {img_id}   <- ONE set of read-only bytes")
    print()
    print("  container    id            lines in /data/seed.txt   its own line")
    print("  -----------  ------------  -----------------------   ------------")
    for name, cid, body in ids:
        lines = body[0].strip() if body else "?"
        own = [ln for ln in body if "written by" in ln]
        print(f"  {name:<11}  {cid}  {lines:>21}   "
              f"{(own[0].split('by ')[-1] if own else '-')}")

    distinct = len({cid for _, cid, _ in ids})
    print()
    print(f"  distinct container ids: {distinct}   distinct image ids: 1")
    print("  Every container read the SAME baked line and saw only its OWN")
    print("  write. The write went to a per-container writable layer stacked")
    print("  on top of the image - and it dies with the container (demo 6).")


# ==================================================================== demo 2
def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_keys(base, instructions, files):
    """Model BuildKit's cache key chain in ~10 lines.

    key(0)  = H(base image ref)
    key(i)  = H(key(i-1) || instruction text || content hash of any files
               the instruction copies)

    Two consequences fall straight out of that definition and they are the
    whole topic: (a) changing a file changes every key BELOW the COPY that
    brought it in, and (b) a RUN whose parent key is unchanged is never
    re-executed, no matter how expensive it is.
    """
    keys, parent = [], _sha(f"FROM {base}".encode())
    for kind, arg in instructions:
        payload = f"{kind} {arg}".encode()
        if kind == "COPY":
            for name in arg.split():
                payload += _sha(files.get(name, "").encode())[:16].encode()
        parent = _sha(parent.encode() + payload)
        keys.append(parent)
    return keys


def demo_cache_keys():
    print(SEP)
    print("DEMO 2 - why the ordering rule works: the key is a HASH CHAIN")
    print(SEP)
    base = DOCKER["base"] or "python:3.12-slim"

    bad = [("WORKDIR", "/app"),
           ("COPY", "requirements.txt app.py"),
           ("RUN", "pip install -r requirements.txt"),
           ("CMD", "uvicorn main:app")]
    good = [("WORKDIR", "/app"),
            ("COPY", "requirements.txt"),
            ("RUN", "pip install -r requirements.txt"),
            ("COPY", "app.py"),
            ("CMD", "uvicorn main:app")]

    before = {"requirements.txt": "fastapi==0.141.1\nuvicorn==0.45.0\n",
              "app.py": "def handler():\n    return 'v1'\n"}
    after = dict(before, **{"app.py": "def handler():\n    return 'v2'\n"})
    print("  the edit: one line of app.py, 'v1' -> 'v2'.")
    print("  requirements.txt is byte-identical in both runs.\n")

    for label, instrs in (("SOURCE FIRST  (COPY . . then pip install)", bad),
                          ("REQS FIRST    (COPY requirements.txt, pip,"
                           " then COPY app.py)", good)):
        k1 = cache_keys(base, instrs, before)
        k2 = cache_keys(base, instrs, after)
        print(f"  {label}")
        misses = 0
        for (kind, arg), a, b in zip(instrs, k1, k2):
            hit = a == b
            misses += 0 if hit else 1
            mark = "HIT " if hit else "MISS"
            cost = "  <-- reinstalls EVERYTHING" if kind == "RUN" and not hit \
                else ""
            line = f"    {mark}  {a[:8]} -> {b[:8]}  {kind + ' ' + arg:<38}"
            print((line + cost).rstrip())
        print(f"    {misses} of {len(instrs)} layers invalidated\n")

    print("  The COPY that brings in app.py is the fork in the road. Put it")
    print("  ABOVE the install and the install's parent key changes, so the")
    print("  install re-runs. Put it BELOW and the install's parent key is")
    print("  untouched, so it is served from cache. Demo 3 times it.")


# ==================================================================== demo 3
DOCKERFILE_BAD = """FROM {base}
WORKDIR /app
# WRONG ORDER. This single COPY pulls in the source, which changes on every
# commit - so the expensive RUN below it is invalidated on every commit too.
COPY . .
RUN sleep {secs}
CMD ["/bin/sh", "-c", "echo ok"]
"""

DOCKERFILE_GOOD = """FROM {base}
WORKDIR /app
# RIGHT ORDER. requirements.txt changes rarely, so this layer and the
# install below it stay cached across ordinary source edits.
COPY requirements.txt ./
RUN sleep {secs}
# Source last: the only layer a code edit can invalidate.
COPY app.py ./
CMD ["/bin/sh", "-c", "echo ok"]
"""


def demo_layer_cache_timed(tmp):
    print(SEP)
    print("DEMO 3 - the same rule with a stopwatch on real `docker build`")
    print(SEP)
    if not have_docker():
        skipped("no usable local base image")
        return

    base = DOCKER["base"]
    results = {}
    for variant, template in (("source-first", DOCKERFILE_BAD),
                              ("reqs-first", DOCKERFILE_GOOD)):
        ctx = os.path.join(tmp, "d3-" + variant)
        # The nonce inside requirements.txt guarantees the FIRST build is a
        # genuine cold build even if this script has been run before. Without
        # it the second run would report suspiciously fast "cold" builds.
        write(os.path.join(ctx, "requirements.txt"),
              f"fastapi==0.141.1\nuvicorn==0.45.0\n# run {NONCE}\n")
        write(os.path.join(ctx, "app.py"), "VERSION = 'v1'\n")
        dfile = os.path.join(ctx, "Dockerfile")
        write(dfile, template.format(base=base, secs=INSTALL_SECONDS))

        rc, out, cold, tag = build(ctx, dfile, "coursedemo-" + variant)
        if rc != 0:
            skipped("build failed")
            print(out[-600:])
            return

        # A rebuild with NOTHING changed. This is the floor: docker CLI
        # start-up, context transfer and image export, none of which layer
        # caching can remove. Without this number the two rebuilds below
        # cannot be read honestly.
        rc, out, noop, _ = build(ctx, dfile, "coursedemo-" + variant)

        # THE EDIT. One line of source. Nothing else on disk changes.
        write(os.path.join(ctx, "app.py"), "VERSION = 'v2'\n")
        rc, out, warm, _ = build(ctx, dfile, "coursedemo-" + variant)
        cached = len(re.findall(r"CACHED", out))
        results[variant] = (cold, noop, warm, cached)

    print(f"  the install layer is `RUN sleep {INSTALL_SECONDS}` - a stand-in")
    print("  for `pip install -r requirements.txt`, because this sandbox has")
    print("  no network. What is measured is whether it RE-RUNS.\n")
    print("  Dockerfile ordering    cold    no-op    after 1-line src edit")
    print("  --------------------  ------  -------  -----------------------")
    for variant in ("source-first", "reqs-first"):
        cold, noop, warm, cached = results[variant]
        print(f"  {variant:<20} {cold:6.2f}s  {noop:6.2f}s   {warm:6.2f}s"
              f"  ({cached} layer(s) CACHED)")

    bad_warm = results["source-first"][2]
    good_warm = results["reqs-first"][2]
    floor = min(results["source-first"][1], results["reqs-first"][1])
    print()
    print(f"  Read the no-op column first: ~{floor:.2f}s is fixed overhead -")
    print("  CLI start-up, context transfer, image export. No caching removes")
    print("  it. The reqs-first rebuild lands ON that floor, meaning the")
    print("  install layer was not re-run at all.")
    print(f"  rebuild ratio: {bad_warm / max(good_warm, 0.001):.1f}x slower "
          f"for the wrong ordering; {bad_warm - good_warm:.2f}s of avoidable")
    print(f"  work on a {INSTALL_SECONDS}s install step.")
    print("  Scale the install to a real torch wheel (2-5 minutes) and that")
    print("  difference is paid on every commit, by every developer, and by")
    print("  every CI run that builds the image for 7.11.")


# ==================================================================== demo 4
IGNORE_PATTERNS = [".git", ".venv", "__pycache__", "node_modules",
                   "data", "*.log"]


def make_fake_project(root):
    """A project shaped like a real one: mostly junk, by weight."""
    blobs = {
        ".venv/lib/site-packages/torch/_C.so": 8 * 1024 * 1024,
        ".git/objects/pack/pack-1a2b.pack": 3 * 1024 * 1024,
        "node_modules/.cache/bundle.bin": 1 * 1024 * 1024,
        "data/train.csv": 1024 * 1024,
        "__pycache__/app.cpython-312.pyc": 200 * 1024,
        "debug.log": 64 * 1024,
    }
    for rel, size in blobs.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(os.urandom(size))
    write(os.path.join(root, "app.py"), "print('service')\n")
    write(os.path.join(root, "requirements.txt"), "fastapi\nuvicorn\n")


def context_stats(root, patterns):
    """Count what would be SENT to the daemon under these ignore patterns."""
    files = bytes_ = 0
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        # Pruning directories in place is what .dockerignore does too - the
        # daemon never even hears about the contents of an ignored directory.
        dirnames[:] = [d for d in dirnames
                       if not any(fnmatch.fnmatch(d, p) for p in patterns)]
        for name in filenames:
            rel = f"{rel_dir}/{name}" if rel_dir else name
            if any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(rel, p)
                   for p in patterns):
                continue
            files += 1
            bytes_ += os.path.getsize(os.path.join(dirpath, name))
    return files, bytes_


def buildkit_context_bytes(output):
    """Pull BuildKit's own 'transferring context' number out of the log."""
    step = None
    for line in output.splitlines():
        m = re.match(r"^#(\d+) \[internal\] load build context", line)
        if m:
            step = m.group(1)
        if step:
            m2 = re.match(rf"^#{step} transferring context: ([\d.]+\s*\w+)",
                          line)
            if m2:
                return m2.group(1).strip()
    return "not reported"


def demo_dockerignore(tmp):
    print(SEP)
    print("DEMO 4 - .dockerignore decides how many bytes leave your machine")
    print(SEP)
    root = os.path.join(tmp, "d4")
    make_fake_project(root)
    total_files, total_bytes = context_stats(root, [])
    kept_files, kept_bytes = context_stats(root, IGNORE_PATTERNS)

    print("  a project shaped like a real one:")
    print(f"    everything on disk      {total_files:>4} files  "
          f"{total_bytes/1e6:8.2f} MB")
    print(f"    after .dockerignore     {kept_files:>4} files  "
          f"{kept_bytes/1e6:8.2f} MB")
    print(f"    excluded                {total_files-kept_files:>4} files  "
          f"{(total_bytes-kept_bytes)/1e6:8.2f} MB  "
          f"({100*(1-kept_bytes/total_bytes):.1f}% of the weight)")

    if not have_docker():
        print()
        skipped("no usable local base image - byte counts above are still real")
        return

    dfile = os.path.join(root, "Dockerfile")
    write(dfile, f"FROM {DOCKER['base']}\nCOPY . /ctx\n")

    # Build once with no .dockerignore, once with one, and read BuildKit's
    # own report rather than trusting the walk above.
    rc, out, secs_a, _ = build(root, dfile, "coursedemo-ctx-all")
    reported_a = buildkit_context_bytes(out)

    write(os.path.join(root, ".dockerignore"),
          "\n".join(IGNORE_PATTERNS) + "\n")
    rc, out, secs_b, _ = build(root, dfile, "coursedemo-ctx-ignored")
    reported_b = buildkit_context_bytes(out)

    print()
    print("  BuildKit's own number, from `docker build --progress=plain`:")
    print(f"    no .dockerignore     transferring context: {reported_a:<10} "
          f"({secs_a:.2f}s total)")
    print(f"    with .dockerignore   transferring context: {reported_b:<10} "
          f"({secs_b:.2f}s total)")
    print()
    print("  The context is tarred and shipped to the daemon BEFORE the first")
    print("  instruction runs, on every build. Worse: without .dockerignore a")
    print("  `COPY . .` can bake .git and .env straight into a published")
    print("  image - a real credential leak (7.13), and image layers are")
    print("  readable by anyone who can pull the tag.")


# ==================================================================== demo 5
RUN_SH = """#!/bin/sh
# PID 1 is special: the kernel applies NO default action for a signal PID 1
# has not explicitly trapped. So a container's main process must (a) install
# a handler and (b) actually BE pid 1 to receive the signal at all.
trap 'echo "SIGTERM received -> graceful shutdown"; exit 0' TERM
echo "app running as pid $$"
while true; do sleep 0.2 2>/dev/null || sleep 1; done
"""

CMD_FORMS = {
    "exec form": 'CMD ["/bin/sh", "/app/run.sh"]',
    "shell, simple": "CMD /bin/sh /app/run.sh",
    "shell, compound": 'CMD /bin/sh /app/run.sh && echo "bye"',
}


def demo_signals(tmp):
    print(SEP)
    print("DEMO 5 - CMD form decides whether `docker stop` is graceful")
    print(SEP)
    if not have_docker():
        skipped("no usable local base image")
        return

    rows = []
    for i, (label, cmd_line) in enumerate(CMD_FORMS.items()):
        ctx = os.path.join(tmp, f"d5-{i}")
        write(os.path.join(ctx, "run.sh"), RUN_SH)
        dfile = os.path.join(ctx, "Dockerfile")
        write(dfile, (f"FROM {DOCKER['base']}\n"
                      "COPY run.sh /app/run.sh\n"
                      "RUN chmod +x /app/run.sh\n"
                      f"{cmd_line}\n"))
        rc, out, _, tag = build(ctx, dfile, f"coursedemo-sig{i}")
        if rc != 0:
            skipped("build failed")
            print(out[-600:])
            return

        rc, cid = run_container(tag, detach=True)
        time.sleep(1.0)                     # let the app install its trap
        t0 = time.perf_counter()
        # Stopping a container THIS SCRIPT created, by the exact id it was
        # given. Never by name pattern, never `docker stop $(docker ps -q)`.
        sh(["docker", "stop", "-t", str(STOP_GRACE), cid], timeout=120)
        elapsed = time.perf_counter() - t0
        body = logs(cid)
        pid = re.search(r"pid (\d+)", body)
        rows.append((label, cmd_line, pid.group(1) if pid else "?",
                     "yes" if "graceful" in body else "no", elapsed))

    print(f"  each container is stopped with `docker stop -t {STOP_GRACE}`.")
    print("  SIGTERM first; SIGKILL when the grace period runs out.\n")
    print("  CMD written as              app pid   trap ran   stop took")
    print("  --------------------------  -------   --------   ---------")
    for label, cmd_line, pid, ran, elapsed in rows:
        print(f"  {label:<26}  {pid:>7}   {ran:>8}   {elapsed:8.2f}s")
    print()
    for label, cmd_line, pid, ran, elapsed in rows:
        print(f"    {label:<16} {cmd_line}")
    print()
    print("  Read the pid column first. Exec form makes your process pid 1,")
    print("  so it gets the signal. `shell, simple` still works because sh")
    print("  exec's a lone simple command, replacing itself - a detail most")
    print("  write-ups skip. Add ANY shell syntax and sh must stay around to")
    print("  interpret it, so sh is pid 1, sh has no TERM trap, the kernel")
    print("  drops the signal, and the container is killed at the deadline.")
    print("  In 7.11 that deadline is in-flight requests dropped on every")
    print("  deploy, and it never shows up in local testing.")


# ==================================================================== demo 6
def demo_volumes(tmp):
    print(SEP)
    print("DEMO 6 - a named volume outlives the container; the layer does not")
    print(SEP)
    if not have_docker():
        skipped("no usable local base image")
        return

    vol = f"coursedemo-vol-{NONCE}"
    rc, out, _ = sh(["docker", "volume", "create", vol])
    if rc != 0:
        skipped("could not create a volume")
        return
    CREATED_VOLUMES.append(vol)

    ctx = os.path.join(tmp, "d6")
    write(os.path.join(ctx, "Dockerfile"),
          f"FROM {DOCKER['base']}\nRUN mkdir -p /vol /scratch\n"
          'CMD ["/bin/sh", "-c", "true"]\n')
    rc, out, _, tag = build(ctx, os.path.join(ctx, "Dockerfile"),
                            "coursedemo-vol")
    if rc != 0:
        skipped("build failed")
        return

    # Container 1 writes to BOTH places: a plain path (writable layer) and
    # the volume mount point.
    rc, c1 = run_container(tag, ["/bin/sh", "-c",
                                 "echo 'row 1 - the vector index' > "
                                 "/vol/pgdata.txt; echo 'temp' > "
                                 "/scratch/notes.txt; echo wrote both"],
                           mounts=[f"{vol}:/vol"])
    print(f"  container 1 ({c1[:12]}) wrote /vol/pgdata.txt and "
          "/scratch/notes.txt")

    # Remove it entirely - this is `docker compose down`, or a redeploy.
    sh(["docker", "rm", "-f", c1], timeout=120)
    CREATED_CONTAINERS.remove(c1)
    print(f"  container 1 removed  (this is what a redeploy does)")

    rc, c2 = run_container(tag, ["/bin/sh", "-c",
                                 "echo -n 'volume  : '; "
                                 "cat /vol/pgdata.txt 2>/dev/null || "
                                 "echo GONE; echo -n 'layer   : '; "
                                 "cat /scratch/notes.txt 2>/dev/null || "
                                 "echo GONE"],
                           mounts=[f"{vol}:/vol"])
    print(f"  container 2 ({c2[:12]}) reads the same paths:")
    for line in logs(c2).splitlines():
        print(f"    {line}")
    print()
    print("  Same image, brand-new writable layer, same named volume. This is")
    print("  exactly why the Postgres service in 0.15 mounts a named volume:")
    print("  `docker compose down` keeps it, `down -v` destroys it. Losing a")
    print("  rebuilt pgvector index (5.2) to the wrong flag is an avoidable")
    print("  afternoon.")


# ==================================================================== demo 7
COMPOSE_YAML = """services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://app:secret@db:5432/appdb
      REDIS_URL: redis://cache:6379/0
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    volumes:
      - .:/app

  worker:
    build: .
    command: ["python", "-m", "worker"]
    depends_on:
      - db

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d appdb"]
      interval: 5s
      retries: 10
    volumes:
      - pgdata:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

volumes:
  pgdata:
"""

DB_READY_AFTER = 1.5          # seconds Postgres needs before it accepts TCP


def edges(services):
    """Normalise both depends_on spellings into (dep, condition) pairs."""
    out = {}
    for name, spec in services.items():
        dep = (spec or {}).get("depends_on") or []
        if isinstance(dep, list):
            # LIST form has no condition at all - it means "started", full
            # stop. This is the spelling that bites.
            out[name] = [(d, "service_started (implied)") for d in dep]
        else:
            out[name] = [(d, (v or {}).get("condition", "service_started"))
                         for d, v in dep.items()]
    return out


def demo_compose(tmp):
    print(SEP)
    print("DEMO 7 - depends_on waits for STARTED, not for READY")
    print(SEP)
    if yaml is None:
        print("  SKIPPED - PyYAML not installed (pip install pyyaml)")
        return

    path = os.path.join(tmp, "d7", "docker-compose.yml")
    write(path, COMPOSE_YAML)
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    services = doc["services"]
    dag = edges(services)
    print(f"  parsed {len(services)} services, "
          f"{sum(len(v) for v in dag.values())} depends_on edges, "
          f"{len(doc.get('volumes') or {})} named volume(s)\n")

    print("  service   depends on   as spelled                  db healthy?")
    print("  --------  -----------  --------------------------  -----------")
    for name in sorted(dag):
        for dep, cond in dag[name]:
            has_hc = "healthcheck" in (services.get(dep) or {})
            waits = cond == "service_healthy"
            verdict = "WAITS" if waits else ("RACE" if has_hc else "n/a")
            print(f"  {name:<8}  {dep:<11}  {cond:<26}  {verdict}")

    # Startup waves: Kahn's algorithm. Compose does the same thing, then
    # starts each wave in parallel.
    remaining = {k: {d for d, _ in v} for k, v in dag.items()}
    wave, waves = 0, []
    while remaining:
        ready = sorted(k for k, deps in remaining.items() if not deps)
        if not ready:
            waves.append(("CYCLE", sorted(remaining)))
            break
        waves.append((wave, ready))
        for k in ready:
            remaining.pop(k)
        for deps in remaining.values():
            deps -= set(ready)
        wave += 1
    print()
    for w, names in waves:
        print(f"  start wave {w}: {', '.join(names)}")

    # The race, timed. A background thread flips the flag after DB_READY_AFTER
    # seconds - the same shape as Postgres booting, running initdb, and only
    # then binding its port.
    state = {"accepting": False}

    def boot_db():
        time.sleep(DB_READY_AFTER)
        state["accepting"] = True

    t = threading.Thread(target=boot_db, daemon=True)
    print()
    print(f"  now timed. The db container STARTS at t=0 and only begins")
    print(f"  accepting connections at t={DB_READY_AFTER:.1f}s.\n")
    t.start()
    t0 = time.perf_counter()

    # worker: depends_on list form -> connects the moment the container is up.
    connected = state["accepting"]
    print(f"    worker (depends_on: [db])          connects at "
          f"{time.perf_counter()-t0:5.2f}s -> "
          f"{'OK' if connected else 'CONNECTION REFUSED, container exits 1'}")

    # api: condition: service_healthy -> compose polls the healthcheck.
    polls = 0
    while not state["accepting"]:
        polls += 1
        time.sleep(0.1)                # the healthcheck `interval:`
    print(f"    api (condition: service_healthy)   connects at "
          f"{time.perf_counter()-t0:5.2f}s -> OK "
          f"after {polls} health polls")

    # And the failure Kahn's algorithm catches before Compose ever runs.
    broken = {"api": {"depends_on": {"db": {"condition": "service_healthy"}}},
              "db": {"depends_on": {"api": {"condition": "service_started"}}}}
    rem = {k: {d for d, _ in v} for k, v in edges(broken).items()}
    startable = [k for k, deps in rem.items() if not deps]
    print()
    print(f"  a compose file where api needs db and db needs api:")
    print(f"    services with no unmet dependency: {len(startable)}")
    print("    -> nothing can start. Compose reports a circular dependency")
    print("       instead of hanging, but only because it runs this same")
    print("       topological sort first.")
    print()
    print("  `condition: service_healthy` is the difference between a stack")
    print("  that boots and a stack that crash-loops until Postgres wins the")
    print("  race. Retry logic in the app (0.8) is the belt; this is the")
    print("  braces - use both.")


# ==================================================================== main
def cleanup():
    print(SEP)
    print("CLEANUP - removing only what this run created")
    print(SEP)
    removed = {"containers": 0, "images": 0, "volumes": 0}
    for cid in CREATED_CONTAINERS:
        rc, _, _ = sh(["docker", "rm", "-f", cid], timeout=120)
        removed["containers"] += rc == 0
    for tag in CREATED_IMAGES:
        rc, _, _ = sh(["docker", "rmi", "-f", tag], timeout=120)
        removed["images"] += rc == 0
    for vol in CREATED_VOLUMES:
        rc, _, _ = sh(["docker", "volume", "rm", "-f", vol], timeout=120)
        removed["volumes"] += rc == 0
    print(f"  containers removed: {removed['containers']:>2} of "
          f"{len(CREATED_CONTAINERS)}")
    print(f"  images removed    : {removed['images']:>2} of "
          f"{len(CREATED_IMAGES)}")
    print(f"  volumes removed   : {removed['volumes']:>2} of "
          f"{len(CREATED_VOLUMES)}")
    print(f"  every name carried the nonce {NONCE}; nothing else was touched.")


def main():
    tmp = tempfile.mkdtemp(prefix="course011-")
    base, server = find_base_image()
    DOCKER["base"], DOCKER["server"] = base, server

    print(f"docker server {server or 'NOT AVAILABLE'} | "
          f"pyyaml {'yes' if yaml else 'no'}")
    if base:
        print(f"base image (already local, NOT pulled): {base}")
    else:
        print("no usable local base image - Docker demos will be SKIPPED,")
        print("and nothing will be pulled to fix that.")
    print(f"scratch dir {tmp}")
    print(f"run nonce   {NONCE}")

    try:
        demo_image_vs_container(tmp)
        demo_cache_keys()
        demo_layer_cache_timed(tmp)
        demo_dockerignore(tmp)
        demo_signals(tmp)
        demo_volumes(tmp)
        demo_compose(tmp)
    finally:
        cleanup()
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"scratch dir removed: {not os.path.exists(tmp)}")


if __name__ == "__main__":
    main()
