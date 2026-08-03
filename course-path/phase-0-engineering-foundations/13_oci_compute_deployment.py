"""
0.13 - OCI Compute: Free Tier and Deployment.

Runnable: `python 13_oci_compute_deployment.py`
Requires: nothing mandatory. Demo 5 uses numpy if it is importable to MEASURE
          this machine's arithmetic and memory throughput; if numpy is absent
          it says so and skips those two numbers rather than inventing them.

SAFE + OFFLINE: this script makes NO cloud call, NO network call, and never
touches the OCI CLI (which is not installed here anyway). Provisioning a VM
genuinely cannot be simulated on a laptop - so instead of pretending, every
demo below models the DECISIONS that surround provisioning as data and then
evaluates them. Those decisions are where the time is actually lost. The only
filesystem writes go to a tempfile.mkdtemp() directory that is deleted in a
finally block. No real keys: the key material below is a hand-typed stub.

What this proves practically:
  1. OCI has TWO independent firewalls. A packet must pass BOTH. Counted.
  2. iptables is FIRST-MATCH-WINS, so `-A` (append) after the REJECT rule
     produces a rule that is present, correct-looking, and never evaluated.
  3. 0.0.0.0/0 is 4,294,967,296 source addresses. A /32 is 1. Computed.
  4. An image built on this machine is linux/amd64; Always Free A1 is
     aarch64. The mismatch is decided by a string comparison, not by luck.
  5. OpenSSH's private-key permission rule, and the paste-the-wrong-file
     mistake, are both mechanically checkable before you are locked out.
  6. 4 OCPU / 24 GB comfortably SERVES an agent and cannot TRAIN one -
     shown with memory arithmetic and a measured throughput extrapolation.
  7. Four completely different faults produce one identical symptom:
     "connection timed out, nothing in any log."
"""

import ipaddress
import os
import platform
import shutil
import stat
import tempfile
import time
from dataclasses import dataclass, field

SEP = "=" * 70

try:
    import numpy as _np
except ImportError:                      # numpy is optional here (0.6 installs it)
    _np = None


# ===================================================== packet + rule modelling
@dataclass(frozen=True)
class Packet:
    """One inbound connection attempt, described completely enough to decide."""
    label: str
    source_ip: str
    dest_port: int
    protocol: str = "tcp"
    conn_state: str = "NEW"     # NEW for an inbound connection someone initiates
    iface: str = "eth0"         # not "lo": this arrived from outside the box


@dataclass(frozen=True)
class Ingress:
    """One OCI Security List / NSG ingress rule. Cloud layer, set in the console."""
    source: str                 # CIDR
    protocol: str               # "tcp" | "udp" | "icmp" | "all"
    port_min: int | None = None
    port_max: int | None = None
    note: str = ""


@dataclass(frozen=True)
class IptRule:
    """One iptables INPUT rule. Host layer, set over SSH on the instance."""
    target: str                 # ACCEPT | DROP | REJECT
    protocol: str = "all"
    dport: int | None = None
    sport: int | None = None
    iface: str | None = None
    states: frozenset = frozenset()
    source: str = "0.0.0.0/0"
    text: str = ""


def ip_in(cidr: str, ip: str) -> bool:
    """Membership test done by the stdlib, not by eyeballing the numbers.

    This same call is what makes least-privilege auditable in 7.13: a rule is
    either provably narrow or it is not, and the number of addresses it admits
    is a property you can print.
    """
    return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr)


def eval_security_list(rules: list[Ingress], pkt: Packet) -> tuple[bool, str]:
    """OCI security lists are ALLOW-lists with an implicit default DENY.

    Order does not matter here - any matching rule permits the packet. That is
    the opposite of iptables below, and mixing the two mental models up is how
    a correct-looking host rule ends up unreachable.
    """
    for r in rules:
        if not ip_in(r.source, pkt.source_ip):
            continue
        if r.protocol not in ("all", pkt.protocol):
            continue
        if r.port_min is not None and not (r.port_min <= pkt.dest_port <= r.port_max):
            continue
        return True, f"allowed by ingress {r.source} {r.protocol}/{r.port_min}"
    return False, "no ingress rule matches -> implicit DENY"


def eval_iptables(chain: list[IptRule], policy: str,
                  pkt: Packet) -> tuple[bool, int, str]:
    """iptables is ORDERED and FIRST-MATCH-WINS. This is the whole lesson.

    Returns (allowed, rule_number, explanation). Rule number 0 means no rule
    matched and the chain POLICY decided. Note that the ESTABLISHED,RELATED
    rule never matches an inbound NEW connection - which is exactly why your
    outbound `apt-get update` keeps working while inbound HTTPS is dead, and
    why the box feels "fine" while being unreachable.
    """
    for i, r in enumerate(chain, start=1):
        if r.iface and r.iface != pkt.iface:
            continue
        if r.protocol not in ("all", pkt.protocol):
            continue
        if r.dport is not None and r.dport != pkt.dest_port:
            continue
        if r.states and pkt.conn_state not in r.states:
            continue
        if not ip_in(r.source, pkt.source_ip):
            continue
        return r.target == "ACCEPT", i, r.text
    return policy == "ACCEPT", 0, f"fell through to chain policy {policy}"


# ---- the actual data: what an Oracle-provided Linux image ships with -------
# Reproduced as data so it can be evaluated rather than admired. The REJECT at
# position 6 is the reason the documented fix is `-I INPUT 6` and not `-A`.
OCI_DEFAULT_CHAIN = [
    IptRule("ACCEPT", states=frozenset({"ESTABLISHED", "RELATED"}),
            text="ACCEPT all ESTABLISHED"),
    IptRule("ACCEPT", protocol="icmp", text="ACCEPT icmp"),
    IptRule("ACCEPT", iface="lo", text="ACCEPT all in:lo"),
    IptRule("ACCEPT", protocol="udp", sport=123, text="ACCEPT udp spt:123"),
    IptRule("ACCEPT", protocol="tcp", dport=22, states=frozenset({"NEW"}),
            text="ACCEPT tcp NEW dpt:22"),
    IptRule("REJECT", text="REJECT all (catch-all)"),
]

ALLOW_443 = IptRule("ACCEPT", protocol="tcp", dport=443, states=frozenset({"NEW"}),
                    text="ACCEPT tcp NEW dpt:443")

# Default VCN security list: SSH from anywhere, and nothing else inbound.
SL_DEFAULT = [
    Ingress("0.0.0.0/0", "tcp", 22, 22, "default: SSH from the whole internet"),
    Ingress("0.0.0.0/0", "icmp", note="path-MTU / unreachable"),
]
# What you get after "Add Ingress Rule: 0.0.0.0/0, TCP, 443" in the console.
SL_443 = SL_DEFAULT + [Ingress("0.0.0.0/0", "tcp", 443, 443, "HTTPS, added by you")]

PROBES = [
    Packet("ssh, random host  ", "203.0.113.9", 22),
    Packet("https, a browser  ", "203.0.113.9", 443),
    Packet("http, certbot ACME", "203.0.113.9", 80),
    Packet("raw uvicorn port  ", "198.51.100.7", 8000),
    Packet("postgres, in-VCN  ", "10.0.0.5", 5432),
]


# ============================================================== DEMO 1
def demo_two_layer_firewall() -> None:
    print(SEP)
    print("DEMO 1 - TWO firewalls. A packet must pass BOTH. Evaluated.")
    print(SEP)

    # Four configurations of the same box. Only the last one works, and three
    # of the four produce the identical user-visible symptom: a hang.
    configs = [
        ("A  console untouched, host untouched", SL_DEFAULT, OCI_DEFAULT_CHAIN),
        ("B  console 443 opened, host untouched", SL_443, OCI_DEFAULT_CHAIN),
        # -A APPENDS. The chain already ends in REJECT, so this lands at
        # position 7 and is never reached. `iptables -L` shows it. It is dead.
        ("C  console 443 + iptables -A (append)", SL_443,
         OCI_DEFAULT_CHAIN + [ALLOW_443]),
        # -I INPUT 6 INSERTS before the REJECT. Same rule text, different index.
        ("D  console 443 + iptables -I INPUT 6", SL_443,
         OCI_DEFAULT_CHAIN[:5] + [ALLOW_443] + OCI_DEFAULT_CHAIN[5:]),
    ]

    def rule_index(chain, pred):
        return next((i for i, r in enumerate(chain, 1) if pred(r)), None)

    for name, sl, chain in configs:
        reachable = 0
        print(f"\n  {name}")
        for pkt in PROBES:
            cloud_ok, _ = eval_security_list(sl, pkt)
            host_ok, host_n, host_why = eval_iptables(chain, "ACCEPT", pkt)
            if not cloud_ok:
                verdict, blame = "BLOCKED", "security list: implicit DENY"
            elif not host_ok:
                verdict, blame = "BLOCKED", f"iptables {host_n}: {host_why}"
            else:
                verdict, blame = "reaches app", f"iptables {host_n}: {host_why}"
                reachable += 1
            print(f"    {pkt.label} :{pkt.dest_port:<5} {verdict:<11} {blame}")
        # The measurable difference between "appended" and "inserted" is a
        # single integer, and it decides whether the box is reachable.
        pos_443 = rule_index(chain, lambda r: r.dport == 443 and r.target == "ACCEPT")
        pos_rej = rule_index(chain, lambda r: r.target == "REJECT")
        print(f"    chain: 443-ACCEPT rule={pos_443 or 'ABSENT'}  "
              f"REJECT rule={pos_rej}  ({len(chain)} rules)")
        print(f"    -> {reachable}/{len(PROBES)} probes reach the application")

    print("\n  B and C give byte-identical probe results. That is the point.")
    print("  In C the rule EXISTS, reads correctly, and shows up in")
    print("  `iptables -L`. It is at position 7; the REJECT that matches")
    print("  everything is at position 6. The rule is never evaluated.")
    print("  First-match-wins is not a detail; it is the whole semantics,")
    print("  and it is why the documented fix is `-I INPUT 6`, not `-A`.")
    print("  Cloud security lists are the opposite - an unordered allow-list")
    print("  where order cannot matter. Two layers, two different models.")


# ============================================================== DEMO 2
def demo_cidr_blast_radius() -> None:
    print(SEP)
    print("DEMO 2 - how wide is 0.0.0.0/0? Counted, not asserted.")
    print(SEP)

    candidates = ["0.0.0.0/0", "203.0.113.0/24", "203.0.113.9/32", "10.0.0.0/16"]
    print("  CIDR              addresses admitted   relative to /32")
    print("  ----------------  ------------------   ---------------")
    for c in candidates:
        net = ipaddress.ip_network(c)
        print(f"  {c:<16}  {net.num_addresses:>18,}   {net.num_addresses:>15,}x")

    # The same two IPs, tested against each policy. Least privilege is not a
    # slogan here - it is a ratio you can print.
    tested = [("0.0.0.0/0", 11), ("203.0.113.0/24", 16), ("203.0.113.9/32", 16)]
    print("\n  source IP        0.0.0.0/0  203.0.113.0/24  203.0.113.9/32")
    print("  ---------------  ---------  --------------  --------------")
    for who, ip in [("your office", "203.0.113.9"),
                    ("a port scanner", "45.128.232.11")]:
        cells = "".join(f"{str(ip_in(c, ip)):<{w}}" for c, w in tested)
        print(f"  {ip:<15}  {cells}({who})")

    wide = ipaddress.ip_network("0.0.0.0/0").num_addresses
    narrow = ipaddress.ip_network("203.0.113.9/32").num_addresses
    print(f"\n  SSH open to 0.0.0.0/0 admits {wide:,} sources.")
    print(f"  SSH open to a /32 admits {narrow}.")
    print(f"  Narrowing the SSH rule alone removes {wide - narrow:,} of them")
    print(f"  ({wide // narrow:,}x reduction) and costs one console edit.")
    print("\n  443 genuinely needs 0.0.0.0/0 - that is what public means.")
    print("  22 and 5432 almost never do. The default security list opens 22")
    print("  to the entire internet; that default is a starting point, not a")
    print("  recommendation. Same argument as least-privilege secrets in 7.13.")


# ============================================================== DEMO 3
def demo_architecture_mismatch() -> None:
    print(SEP)
    print("DEMO 3 - aarch64 vs amd64. Decided by a string, not by luck.")
    print(SEP)

    raw = platform.machine()
    # Normalise the vendor spellings. "AMD64" from Windows and "x86_64" from
    # Linux are the same ISA; "arm64" from macOS and "aarch64" from Linux are
    # the same ISA. Docker's canonical names are amd64 and arm64.
    alias = {"AMD64": "amd64", "x86_64": "amd64", "x86-64": "amd64",
             "aarch64": "arm64", "arm64": "arm64", "armv8l": "arm64"}
    local = alias.get(raw, raw.lower())

    print(f"  this machine reports platform.machine() = {raw!r} -> {local}")
    print(f"  running {platform.system()} {platform.release()}, "
          f"Python {platform.python_version()}")
    print(f"  a plain `docker build .` here produces an image for: linux/{local}")
    print("  Always Free VM.Standard.A1.Flex is Ampere Altra  : linux/arm64")

    # The runtime check the kernel performs is exactly this comparison.
    cases = [
        ("linux/amd64", "linux/arm64"),
        ("linux/arm64", "linux/arm64"),
        ("linux/arm64", "linux/amd64"),
        ("linux/amd64", "linux/amd64"),
    ]
    print("\n  image platform   host platform    result")
    print("  ---------------  ---------------  ------------------------------")
    for img, host in cases:
        if img == host:
            result = "starts"
        else:
            result = "exec format error / cannot start"
        print(f"  {img:<15}  {host:<15}  {result}")

    mismatch = sum(1 for img, host in cases if img != host)
    print(f"\n  {mismatch} of {len(cases)} combinations fail, and the failure is")
    print("  'exec /usr/local/bin/uvicorn: exec format error' - which reads")
    print("  like a corrupt binary and is actually a CPU architecture.")

    print("\n  Three fixes, cheapest first:")
    print("    1. git clone on the VM and `docker compose up -d --build` there.")
    print("       The build happens on aarch64, so the question never arises.")
    print("    2. docker buildx build --platform linux/arm64 -t app:arm64 .")
    print("       Cross-build from this machine via QEMU emulation. Slower.")
    print("    3. docker buildx build --platform linux/amd64,linux/arm64 --push")
    print("       A multi-arch manifest; the VM pulls the variant it can run.")
    print("  All three are 0.11 commands. The constraint is the CPU, not Docker.")
    print("  Watch for pinned base images too: not every tag has an arm64")
    print("  variant, and `FROM some/image:tag` that resolves on your laptop")
    print("  can 'no matching manifest' on the VM.")


# ============================================================== DEMO 4
def demo_ssh_key_hygiene(workdir: str) -> None:
    print(SEP)
    print("DEMO 4 - SSH key permissions and the paste-the-wrong-file mistake.")
    print(SEP)

    # Entirely fabricated key material. Nothing here is a real key, and the
    # file lives in a temp dir that is deleted in main()'s finally block.
    priv = os.path.join(workdir, "oci_ed25519")
    pub = os.path.join(workdir, "oci_ed25519.pub")
    with open(priv, "w", newline="\n") as fh:
        fh.write("-----BEGIN OPENSSH PRIVATE KEY-----\n"
                 "NOTAREALKEYb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAA\n"
                 "-----END OPENSSH PRIVATE KEY-----\n")
    with open(pub, "w", newline="\n") as fh:
        fh.write("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5NOTAREALKEY0000 oci-deploy\n")

    os.chmod(priv, 0o600)
    real_mode = stat.S_IMODE(os.stat(priv).st_mode)
    print(f"  wrote a stub key, called os.chmod(0o600), and os.stat now says: "
          f"0o{real_mode:03o}")
    if real_mode != 0o600:
        print("  ^ that is NOT 600, and it is not a bug in this script.")
        print("    Windows has no POSIX mode bits; os.chmod only toggles the")
        print("    read-only attribute. WSL, Git Bash and the VM are where the")
        print("    real check happens. So the rule is evaluated as data below.")

    # OpenSSH's actual rule for a private key: group and other must have NO
    # permission bits at all. Owner-execute is tolerated but pointless.
    def openssh_accepts(mode: int) -> bool:
        return (mode & 0o077) == 0

    print("\n  mode   symbolic     group/other bits   OpenSSH loads it?")
    print("  -----  -----------  -----------------  ------------------")
    for mode in (0o600, 0o400, 0o640, 0o644, 0o664, 0o777, 0o700):
        sym = stat.filemode(mode)[1:]          # drop the file-type char
        leak = mode & 0o077
        ok = openssh_accepts(mode)
        print(f"  0{mode:03o}   {sym:<11}  0o{leak:03o}{'':<14}"
              f"{'yes' if ok else 'NO - refuses'}")

    print("\n  The refusal message is 'UNPROTECTED PRIVATE KEY FILE!' and it")
    print("  does not tell you to run chmod. From 0.10, the two commands:")
    print("    chmod 700 ~/.ssh          # the directory must be owner-only too")
    print("    chmod 600 ~/.ssh/oci_ed25519")

    # The other half of the mistake, and it is the expensive one.
    def safe_to_paste(path: str) -> tuple[bool, str]:
        head = open(path, encoding="utf-8").readline().strip()
        if head.startswith("-----BEGIN") and "PRIVATE KEY" in head:
            return False, "PRIVATE key - pasting it compromises it"
        if head.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-")):
            return True, "PUBLIC key - what the console wants"
        return False, "unrecognised - do not paste it anywhere"

    print("\n  'Paste your public key' at instance-create time. Which file?")
    for path in (pub, priv):
        ok, why = safe_to_paste(path)
        print(f"    {os.path.basename(path):<16} -> "
              f"{'PASTE' if ok else 'DO NOT PASTE':<13}{why}")
    print("  The first line of the file settles it. Getting this wrong means")
    print("  regenerating the key and rebuilding the instance, because a")
    print("  leaked private key cannot be un-leaked. `ssh-keygen -t ed25519`")
    print("  writes both files; only the one ending .pub ever leaves the box.")


# ============================================================== DEMO 5
def demo_capacity_budget() -> None:
    print(SEP)
    print("DEMO 5 - 4 OCPU / 24 GB: serves comfortably, cannot train.")
    print(SEP)

    FREE_OCPU, FREE_GB = 4, 24
    print(f"  Always Free A1 pool: {FREE_OCPU} OCPU and {FREE_GB} GB TOTAL,")
    print("  splittable across instances. Validating three splits:")
    for split in [[(4, 24)], [(2, 12), (2, 12)], [(4, 24), (1, 6)]]:
        ocpu = sum(c for c, _ in split)
        gb = sum(g for _, g in split)
        ok = ocpu <= FREE_OCPU and gb <= FREE_GB
        shape = " + ".join(f"{c} OCPU/{g} GB" for c, g in split)
        print(f"    {shape:<28} {ocpu} OCPU/{gb:>2} GB  "
              f"{'fits' if ok else 'EXCEEDS -> billed'}")

    # ---- serving budget: itemised, summed, honest ------------------------
    print("\n  SERVING a capstone stack, per-component resident memory:")
    stack = [
        ("Ubuntu base + sshd + systemd", 0.6),
        ("nginx reverse proxy (0.12)", 0.1),
        ("4x uvicorn workers, FastAPI agent (0.9)", 4 * 0.35),
        ("Postgres 16 + pgvector (0.14, 0.15)", 2.0),
        ("Redis cache (7.7)", 0.3),
        ("sentence-transformers embedder, CPU (5.3)", 1.2),
    ]
    used = 0.0
    for name, gb in stack:
        used += gb
        print(f"    {name:<44} {gb:>5.2f} GB")
    print(f"    {'-' * 44} {'-' * 8}")
    print(f"    {'total resident':<44} {used:>5.2f} GB")
    print(f"    {'headroom on 24 GB':<44} {FREE_GB - used:>5.2f} GB "
          f"({(FREE_GB - used) / FREE_GB * 100:.0f}% free)")
    print("  The LLM itself is an API call to a provider (Phase 4), so its")
    print("  weights are somebody else's RAM. That is why this fits at all.")

    # ---- training budget: the same arithmetic, different answer ----------
    print("\n  TRAINING, full fine-tune, mixed precision. Memory per parameter:")
    print("    fp16 weights 2B + fp16 grads 2B + fp32 master 4B")
    print("    + Adam m 4B + Adam v 4B  =  16 bytes/param, before activations")
    per_param = 2 + 2 + 4 + 4 + 4
    print("\n    params    weights   optimizer+grads   TOTAL     fits in 24 GB?")
    print("    --------  --------  ----------------  --------  ---------------")
    for n_params, label in [(1.5e9, "1.5B"), (7e9, "7B"), (70e9, "70B")]:
        weights = n_params * 2 / 1e9
        total = n_params * per_param / 1e9
        print(f"    {label:<8}  {weights:>6.1f} GB  {total - weights:>13.1f} GB  "
              f"{total:>6.1f} GB  "
              f"{'exactly 24.0' if total <= FREE_GB else 'NO'}")
    print("    The 1.5B row lands on 24.0 GB - the whole machine, with zero")
    print("    left for activations, the OS, or the dataset loader. It does")
    print("    not fit either; it just fails one step later.")
    print("    ...and none of it matters, because there is no GPU at all.")

    # ---- measured throughput, clearly labelled as THIS machine ------------
    if _np is None:
        print("\n  (numpy not importable - skipping the measured throughput")
        print("   section rather than quoting a number nobody measured.)")
        return

    n = 1024
    a = _np.random.rand(n, n).astype(_np.float32)
    b = _np.random.rand(n, n).astype(_np.float32)
    a @ b                                          # warm up BLAS threads
    t0 = time.perf_counter()
    reps = 20
    for _ in range(reps):
        a @ b
    matmul_s = (time.perf_counter() - t0) / reps
    gflops = (2 * n ** 3) / matmul_s / 1e9

    buf = _np.empty(64 * 1024 * 1024, dtype=_np.uint8)   # 64 MB
    dst = _np.empty_like(buf)
    _np.copyto(dst, buf)                                  # warm up
    t0 = time.perf_counter()
    for _ in range(10):
        _np.copyto(dst, buf)
    copy_s = (time.perf_counter() - t0) / 10
    bw = (2 * buf.nbytes) / copy_s / 1e9            # read + write

    print(f"\n  Measured on THIS machine ({platform.machine()}), not on an A1:")
    print(f"    fp32 matmul   : {gflops:8.1f} GFLOP/s")
    print(f"    memory copy   : {bw:8.1f} GB/s (read+write)")

    # Chinchilla-style compute estimate: ~6 FLOPs per parameter per token for
    # a forward+backward pass. This is the standard first-order model.
    tokens = 100e6
    flops = 6 * 7e9 * tokens
    days = flops / (gflops * 1e9) / 86400
    tolerable_days = 0.25               # one overnight run: 6 hours
    print(f"\n    Fine-tuning 7B on {tokens/1e6:.0f}M tokens needs ~6*N*D = "
          f"{flops:.2e} FLOPs.")
    print(f"    At the rate measured above that is {days:,.0f} days "
          f"({days/365:.1f} years).")
    print(f"    That is {days/tolerable_days:,.0f}x a tolerable 6-hour run - "
          f"about {len(str(int(days/tolerable_days))) - 1} orders of magnitude.")
    print("    Even if the A1 were twice as fast as this machine - four")
    print(f"    Ampere cores against this one, it is not - {days/2:,.0f} days")
    print("    changes no decision. The conclusion is robust to the")
    print("    measurement being wrong by a factor of ten.")

    # Inference, by contrast, is memory-bandwidth bound: each generated token
    # reads every weight once. This is why a 4-bit 7B is usable on CPU and a
    # fine-tune is not. Same machine, same maths, opposite verdict.
    model_gb = 7e9 * 0.5 / 1e9          # 7B at 4-bit quantisation (4.12)
    tok_s = bw / model_gb
    print(f"\n    Serving a 4-bit 7B locally (4.12) must read {model_gb:.1f} GB")
    print(f"    per generated token, so the ceiling is ~{tok_s:.0f} tok/s at the")
    print("    bandwidth above - slow, but alive. Training misses by orders")
    print("    of magnitude; local CPU inference misses by a small factor.")
    print("    Same box, same arithmetic, two completely different verdicts.")


# ============================================================== DEMO 6
def demo_unreachable_ladder() -> None:
    print(SEP)
    print("DEMO 6 - six configurations, and what the client actually sees.")
    print(SEP)

    OPEN_CHAIN = OCI_DEFAULT_CHAIN[:5] + [ALLOW_443] + OCI_DEFAULT_CHAIN[5:]

    @dataclass
    class Box:
        name: str
        app_listening: bool = True
        bind_addr: str = "0.0.0.0"       # 0.11: 127.0.0.1 inside a container
        public_route: bool = True        # internet gateway + 0.0.0.0/0 route
        sl: list = field(default_factory=lambda: SL_443)
        chain: list = field(default_factory=lambda: list(OPEN_CHAIN))

    boxes = [
        Box("everything correct"),
        Box("container crashed on boot", app_listening=False),
        Box("app bound to 127.0.0.1", bind_addr="127.0.0.1"),
        Box("launched in a private subnet", public_route=False),
        Box("console rule never added", sl=SL_DEFAULT),
        Box("iptables 443 never added", chain=list(OCI_DEFAULT_CHAIN)),
    ]
    probe = Packet("browser", "203.0.113.9", 443)

    # The symptom column is the part worth being precise about, because it is
    # the ONLY information the client has. Getting it wrong sends you to the
    # wrong layer first, and each wrong guess costs a console round-trip.
    rows = []
    for box in boxes:
        if not box.public_route:
            rows.append((box.name, "route table / no gateway", "TIMEOUT",
                         "packets never arrive at the VM"))
        elif not eval_security_list(box.sl, probe)[0]:
            rows.append((box.name, "security list (cloud)", "TIMEOUT",
                         "dropped upstream; VM sees nothing"))
        elif not eval_iptables(box.chain, "ACCEPT", probe)[0]:
            rows.append((box.name, "iptables (host)", "TIMEOUT*",
                         "REJECT sends ICMP, usually filtered"))
        elif not box.app_listening:
            rows.append((box.name, "app not running", "refused",
                         "kernel replies RST immediately"))
        elif box.bind_addr != "0.0.0.0":
            rows.append((box.name, "bind address (0.11)", "refused",
                         "nothing listening on that address"))
        else:
            rows.append((box.name, "-- reaches the app --", "200 OK",
                         "nginx -> uvicorn (0.12, 0.9)"))

    print("  configuration                 first failing layer       client sees")
    print("  ----------------------------  ------------------------  -----------")
    for name, layer, symptom, why in rows:
        print(f"  {name:<28}  {layer:<24}  {symptom}")
    print("\n  why each one looks the way it does:")
    for name, _, _, why in rows:
        print(f"    {name:<28}  {why}")

    timeouts = sum(1 for _, _, s, _ in rows if s.startswith("TIMEOUT"))
    refused = sum(1 for _, _, s, _ in rows if s == "refused")
    print(f"\n  {timeouts} distinct root causes collapse into ONE symptom:")
    print(f"  a hang and then a timeout. {refused} more give 'connection")
    print("  refused', which is the kind failure - an RST comes back")
    print("  instantly and tells you the packet REACHED the host.")
    print("  * a REJECT does send ICMP host-prohibited, which surfaces as")
    print("    'No route to host'. Intermediate networks filter that ICMP")
    print("    often enough that in practice it degrades to a timeout too.")
    print("\n  So the symptom cannot identify the layer, and the ladder is")
    print("  worth memorising in this order - cheapest evidence first:")
    print("    1. curl -v localhost:443 ON the VM   -> app alive at all?")
    print("    2. ss -ltnp | grep :443              -> 0.0.0.0 or 127.0.0.1?")
    print("    3. sudo iptables -L INPUT --line-numbers")
    print("       -> check the line NUMBER, not just that the rule exists")
    print("    4. console: VCN > Subnet > Security List / NSG")
    print("    5. console: VCN > Route Table -> 0.0.0.0/0 via internet gateway")
    print("  Steps 1-3 are 0.10 commands over SSH and cost seconds.")
    print("  Steps 4-5 are the browser, and only after 1-3 come back clean.")


def main() -> None:
    workdir = tempfile.mkdtemp(prefix="oci_0_13_")
    print("0.13 - OCI Compute, evaluated offline.")
    print("NO cloud call, NO network call, NO OCI CLI. Provisioning itself")
    print("cannot run on a laptop; the decisions around it can be checked.")
    print(f"temp dir: {workdir}")
    try:
        demo_two_layer_firewall()
        demo_cidr_blast_radius()
        demo_architecture_mismatch()
        demo_ssh_key_hygiene(workdir)
        demo_capacity_budget()
        demo_unreachable_ladder()
        print(SEP)
        print("Every failure above is a configuration fact, not a mystery.")
        print("The two that cost the most hours on a first deploy are the")
        print("second firewall layer and the aarch64 image. Both are decided")
        print("before you ever open the console. 7.11 is this, with a CI")
        print("pipeline in front of it.")
        print(SEP)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        print(f"temp dir removed: {not os.path.exists(workdir)}")


if __name__ == "__main__":
    main()
