"""
0.12 - NGINX as Reverse Proxy.

Runnable: `python 12_nginx_reverse_proxy.py`
Requires: nothing. Standard library only. NGINX itself is NOT installed and
is NOT needed to run this.

SAFE + OFFLINE: starts two throwaway HTTP servers on 127.0.0.1, both on a
random free port (bind port 0, read back what the OS assigned). One is the
"app" - an SSE streaming upstream of the shape 0.9 builds. The other is a
small reverse proxy that implements the handful of NGINX directives this
topic is about. Both are shut down in a finally block. No internet, no
Docker, no API keys, nothing written to disk, no fixed port taken.

THIS IS A TEACHING MODEL, NOT NGINX. The Python proxy reproduces the
BEHAVIOUR of proxy_buffering, gzip, proxy_read_timeout, proxy_connect_timeout,
client_max_body_size, X-Accel-Buffering and the X-Forwarded-* headers so the
failures can be MEASURED on a machine with no nginx binary. Real NGINX is C,
is far faster, and has hundreds of directives this file ignores. Every
directive named in the output below exists in nginx.conf and does there what
the model does here.

What this proves practically:
  1. The app streams perfectly and the CLIENT still waits - one default did it.
  2. proxy_buffering off restores time-to-first-token. Measured both ways.
  3. gzip on an event stream re-breaks streaming even with buffering off.
  4. X-Accel-Buffering: no lets the APP override a proxy it does not own.
  5. X-Forwarded-For set the wrong way collapses every user into ONE
     rate-limit bucket. Counted, not asserted.
  6. 502 and 504 are different failures with different fixes. Timed.
  7. proxy_read_timeout is a between-reads budget, not a total budget.
  8. client_max_body_size rejects a large prompt payload BEFORE the app sees
     it - which is exactly why the app log is empty when it happens.
"""

import http.client
import json
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SEP = "=" * 70

# The stream the app produces. Eight tokens, 120 ms apart -> just under a
# second of generation. Real generation is slower; the SHAPE is identical.
TOKENS = ["Streaming ", "only ", "helps ", "if ", "every ",
          "hop ", "forwards ", "immediately."]
TOKEN_GAP = 0.12

# Where the proxy sends traffic. A dict so a demo can point it at a dead
# port to produce a genuine 502 (this is nginx's `upstream {}` block).
UPSTREAM = {"host": "127.0.0.1", "port": 0}

# Server-side truth. The client cannot fake these.
UP_STATS = {"requests": 0, "uploads": 0, "upload_bytes": 0}

# The proxy's "nginx.conf". Demos mutate it between runs, which is the
# model's stand-in for editing the file and running `nginx -s reload`.
CFG = {
    "proxy_buffering": True,          # nginx DEFAULT. This is the whole topic.
    "gzip": False,
    "forwarded_mode": "append",       # "none" | "remote_addr" | "append"
    "scheme": "https",                # TLS was terminated HERE, at the proxy
    "proxy_connect_timeout": 2.0,
    "proxy_read_timeout": 60.0,       # nginx default is 60s
    "client_max_body_size": 1024 * 1024,   # nginx default is 1m
}

# Headers that belong to ONE hop and must never be copied to the next one.
# Forwarding `Connection` or `Transfer-Encoding` corrupts the second hop's
# framing - this is why a proxy cannot just replay the header block.
HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate",
              "proxy-authorization", "te", "trailers",
              "transfer-encoding", "upgrade"}


def set_cfg(**kw):
    for k, v in kw.items():
        if k not in CFG:
            raise KeyError(f"no such directive: {k}")
        CFG[k] = v


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # A client that walked away mid-response is EXPECTED here: the 504
        # demo abandons a request the app is still working on. Real nginx
        # logs "client prematurely closed connection" and moves on.
        pass


# ================================================================ the "app"
class AppHandler(BaseHTTPRequestHandler):
    """The upstream. This is the 0.9 FastAPI service, in miniature."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _json(self, code, payload, extra=None):
        body = json.dumps(payload).encode()
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            self.close_connection = True   # proxy gave up on us; see demo 5

    def _identity(self):
        """What the app can work out about the caller. All of it is hearsay
        unless the proxy in front is trusted and sets the headers itself."""
        xff = self.headers.get("X-Forwarded-For")
        xfp = self.headers.get("X-Forwarded-Proto")
        # A per-user rate limiter needs ONE stable key per user. The leftmost
        # X-Forwarded-For entry is the original client; remote_addr is only
        # ever the last hop, which behind a proxy is the proxy itself.
        key = xff.split(",")[0].strip() if xff else self.client_address[0]
        scheme = xfp or "http"
        return {
            "remote_addr": self.client_address[0],
            "x_forwarded_for": xff,
            "x_forwarded_proto": xfp,
            "rate_limit_key": key,
            # If the app believes the connection is plain http it will try to
            # send the user to https - and that redirect comes straight back
            # through the proxy as http again. That is the redirect loop.
            "secure": scheme == "https",
            "redirect_to": f"{scheme}://api.example.com/dashboard",
            "header_names": sorted(self.headers.keys()),
        }

    def _sse(self, n, gap, accel):
        """Server-Sent Events, flushed one token at a time (0.7, 0.9)."""
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            if accel:
                # The app-side override. 0.9 sets this on StreamingResponse.
                # It is what you use when you do not own the proxy config.
                self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            for i in range(n):
                text = TOKENS[i % len(TOKENS)]
                evt = f"data: {json.dumps({'delta': {'text': text}})}\n\n"
                self.wfile.write(evt.encode())
                self.wfile.flush()      # without this, nothing streams at all
                time.sleep(gap)
        except OSError:
            pass
        self.close_connection = True

    def do_GET(self):
        UP_STATS["requests"] += 1
        path, _, qs = self.path.partition("?")
        q = urllib.parse.parse_qs(qs)

        if path == "/ping":
            self._json(200, {"ok": True})
        elif path == "/whoami":
            self._json(200, self._identity())
        elif path == "/stream":
            self._sse(n=int(q.get("n", [len(TOKENS)])[0]),
                      gap=float(q.get("gap", [TOKEN_GAP])[0]),
                      accel=q.get("accel", ["0"])[0] == "1")
        elif path == "/slow":
            # Silent think time: nothing at all on the wire until it ends.
            # This is a cold model load, or a long tool call in 6.14.
            time.sleep(float(q.get("delay", ["3"])[0]))
            self._json(200, {"ok": True, "app_was_fine": True})
        elif path == "/crash":
            # The worker dies mid-request: the connection was accepted, then
            # closed with no status line at all. An OOM kill, a segfault in a
            # native extension, an unhandled exception in a worker.
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.connection.close()
        else:
            self._json(404, {"error": "no such resource"})

    def do_POST(self):
        UP_STATS["requests"] += 1
        n = int(self.headers.get("Content-Length", 0) or 0)
        data = self.rfile.read(n) if n else b""
        if self.path.split("?")[0] == "/upload":
            UP_STATS["uploads"] += 1
            UP_STATS["upload_bytes"] += len(data)
            self._json(200, {"ok": True, "bytes": len(data)})
        else:
            self._json(404, {"error": "no such resource"})


# =============================================================== the "nginx"
class ProxyHandler(BaseHTTPRequestHandler):
    """A ~120-line model of the NGINX directives this topic is about."""

    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_GET(self):
        self._safe("GET")

    def do_POST(self):
        self._safe("POST")

    def _safe(self, method):
        try:
            self._proxy(method)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def _error(self, code, text):
        """Errors GENERATED BY THE PROXY. The app never sees these requests,
        so nothing about them appears in the app's logs (0.10)."""
        body = json.dumps({"error": text, "generated_by": "proxy"}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _proxy(self, method):
        length = int(self.headers.get("Content-Length", 0) or 0)

        # --- client_max_body_size ------------------------------------------
        # Enforced at the EDGE. A 4 MB PDF for 5.4 ingestion, or a very long
        # prompt payload, dies here and the app is never told.
        if length > CFG["client_max_body_size"]:
            remaining = length
            while remaining > 0:      # drain so the demo is deterministic on
                block = self.rfile.read(min(65536, remaining))   # Windows;
                if not block:                                    # real nginx
                    break                                        # may reset
                remaining -= len(block)
            self._error(413, "Request Entity Too Large - client_max_body_size "
                             f"is {CFG['client_max_body_size']} bytes")
            return

        body = self.rfile.read(length) if length else None

        # --- build the upstream request header block ------------------------
        fwd = {}
        for k, v in self.headers.items():
            if k.lower() in HOP_BY_HOP:
                continue          # never replay a hop-by-hop header
            fwd[k] = v
        # `proxy_set_header Host $host` keeps the client's Host so the app can
        # still do name-based routing and build correct absolute URLs.

        mode = CFG["forwarded_mode"]
        client_ip = self.client_address[0]
        if mode == "none":
            # No proxy_set_header lines at all. nginx passes client headers
            # through untouched - including an X-Forwarded-For the CLIENT
            # invented. That is the spoofing case in demo 4C.
            pass
        elif mode == "remote_addr":
            # proxy_set_header X-Forwarded-For $remote_addr;   <- the common
            # mistake. It OVERWRITES the chain with this hop's view.
            fwd["X-Forwarded-For"] = client_ip
            fwd["X-Forwarded-Proto"] = CFG["scheme"]
        elif mode == "append":
            # proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            # APPENDS this hop to whatever arrived, preserving the chain.
            prior = self.headers.get("X-Forwarded-For")
            fwd["X-Forwarded-For"] = f"{prior}, {client_ip}" if prior else client_ip
            fwd["X-Real-IP"] = client_ip
            # TLS terminated here, so the app cannot see the real scheme.
            # Without this header the app thinks every user is on plain http.
            fwd["X-Forwarded-Proto"] = CFG["scheme"]

        # --- phase 1: reach the upstream at all -----------------------------
        # Kept SEPARATE from phase 2 on purpose. The two phases fail for
        # different reasons, produce different status codes, and have their
        # own directive - exactly like the (connect, read) tuple in 0.8.
        conn = http.client.HTTPConnection(
            UPSTREAM["host"], UPSTREAM["port"],
            timeout=CFG["proxy_connect_timeout"])       # proxy_connect_timeout
        try:
            conn.connect()
        except TimeoutError:
            # Packets went out, nothing came back at all: a firewall black
            # hole or a host that is gone. nginx calls this 504 too.
            self._error(504, "Gateway Timeout - upstream did not accept a "
                             f"connection within proxy_connect_timeout "
                             f"{CFG['proxy_connect_timeout']}s")
            return
        except (ConnectionRefusedError, socket.gaierror):
            # Actively refused, or the name does not resolve. NOTHING is
            # listening. The app is not slow; the app is not there.
            self._error(502, "Bad Gateway - upstream "
                             f"{UPSTREAM['host']}:{UPSTREAM['port']} refused the connection")
            return
        except OSError as e:
            self._error(502, f"Bad Gateway - {type(e).__name__} on connect")
            return

        # --- phase 2: send the request and wait for a response header -------
        try:
            conn.sock.settimeout(CFG["proxy_read_timeout"])  # proxy_read_timeout
            conn.request(method, self.path, body=body, headers=fwd)
            resp = conn.getresponse()
        except TimeoutError:
            # We reached it and heard nothing in time. The app may be
            # perfectly healthy and still generating. 504, not 502.
            self._error(504, "Gateway Timeout - no response from upstream "
                             f"within proxy_read_timeout {CFG['proxy_read_timeout']}s")
            return
        except (http.client.HTTPException, OSError) as e:
            # Connection accepted, then dropped with no valid response: the
            # worker died mid-request. nginx logs "upstream prematurely
            # closed connection" and returns 502.
            self._error(502, f"Bad Gateway - upstream closed the connection "
                             f"without a response ({type(e).__name__})")
            return

        # --- decide whether to buffer ---------------------------------------
        buffering = CFG["proxy_buffering"]
        if (resp.getheader("X-Accel-Buffering") or "").lower() == "no":
            buffering = False        # the app overrode us; nginx honours this

        want_gzip = (CFG["gzip"]
                     and "gzip" in (self.headers.get("Accept-Encoding") or ""))

        # Headers go out immediately in BOTH modes, exactly as nginx does.
        # What buffering changes is when the BODY bytes move.
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            lk = k.lower()
            if lk in HOP_BY_HOP or lk == "content-length":
                continue
            if lk.startswith("x-accel-"):
                continue     # nginx CONSUMES X-Accel-*; the client never sees it
            self.send_header(k, v)
        if want_gzip:
            self.send_header("Content-Encoding", "gzip")
        # This model always closes the connection so no Content-Length is
        # needed. A real proxy keeps upstream connections alive (`keepalive
        # 32`) - the same pooling idea as requests.Session in 0.8.
        self.send_header("Connection", "close")
        self.end_headers()

        co = (zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
              if want_gzip else None)
        held = []
        try:
            while True:
                # read1 returns whatever has ARRIVED, rather than waiting for
                # a full buffer. Reading with read(65536) here would buffer
                # the stream inside the proxy by accident.
                chunk = resp.read1(65536)
                if not chunk:
                    break
                if co is not None:
                    # A compressor cannot emit until it has enough input to
                    # code. nginx's gzip module fills gzip_buffers first.
                    # Modelled as: hold everything until the response ends.
                    chunk = co.compress(chunk)
                if buffering:
                    held.append(chunk)          # proxy_buffering on
                elif chunk:
                    self.wfile.write(chunk)     # proxy_buffering off
                    self.wfile.flush()
        except TimeoutError:
            # The headers are already on the wire, so this can no longer be
            # turned into a 504. nginx just cuts the connection - which the
            # client sees as a truncated stream with no error at all.
            conn.close()
            self.close_connection = True
            return

        if co is not None:
            # The compressor only releases its window at the very end. This is
            # why a compressed event stream is not a stream at all.
            tail = co.flush()
            if buffering:
                held.append(tail)
            elif tail:
                self.wfile.write(tail)
                self.wfile.flush()
        if buffering:
            blob = b"".join(held)
            if blob:
                self.wfile.write(blob)
                self.wfile.flush()
        conn.close()
        self.close_connection = True


# ==================================================================== client
def start(handler_cls):
    srv = QuietServer(("127.0.0.1", 0), handler_cls)   # port 0 = any free port
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def free_port():
    """Bind port 0, read the number, release it. Nothing listens there now,
    so connecting to it produces a genuine ConnectionRefusedError."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def fetch(url, headers=None, data=None, timeout=30.0):
    """Returns (status, parsed_json). 4xx/5xx come back as values, not
    exceptions - the proxy's error body is the interesting part."""
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return e.code, {"raw": raw[:60].decode("utf-8", "replace")}


def read_sse(url, headers=None, timeout=60.0):
    """Read an SSE response INCREMENTALLY and time the first usable token.

    Returns (ttft_seconds_or_None, total_seconds, text, response_headers).
    TTFT is stamped when the first DECODED event text becomes available,
    which is the only definition matching what a user actually sees. If the
    bytes arrived but a gzip window is still holding them, they do not count.
    """
    req = urllib.request.Request(url, headers=headers or {})
    t0 = time.perf_counter()
    first = None
    dec = None
    buf = b""
    parts = []
    with urllib.request.urlopen(req, timeout=timeout) as r:
        hdrs = dict(r.getheaders())
        if (r.getheader("Content-Encoding") or "").lower() == "gzip":
            dec = zlib.decompressobj(16 + zlib.MAX_WBITS)
        while True:
            raw = r.read1(65536)
            if not raw:
                break
            data = dec.decompress(raw) if dec is not None else raw
            if not data:
                continue          # bytes in, nothing out: the window is full
            if first is None:
                first = time.perf_counter() - t0
            buf += data
            while b"\n\n" in buf:
                block, buf = buf.split(b"\n\n", 1)
                for line in block.decode("utf-8", "replace").splitlines():
                    if line.startswith("data: "):
                        parts.append(json.loads(line[6:])["delta"]["text"])
    return first, time.perf_counter() - t0, "".join(parts), hdrs


def ms(x):
    return "  n/a" if x is None else f"{x * 1000:5.0f}"


# ===================================================================== 1
def demo_topology(app_base, proxy_base):
    print(SEP)
    print("DEMO 1 - what the extra hop costs, and what it rewrites")
    print(SEP)
    set_cfg(forwarded_mode="append", proxy_buffering=True, gzip=False)

    n = 40
    t0 = time.perf_counter()
    for _ in range(n):
        fetch(f"{app_base}/ping")
    direct = (time.perf_counter() - t0) / n
    t0 = time.perf_counter()
    for _ in range(n):
        fetch(f"{proxy_base}/ping")
    hopped = (time.perf_counter() - t0) / n

    print(f"  {n} x GET /ping, client -> app          : {direct*1000:5.2f} ms each")
    print(f"  {n} x GET /ping, client -> proxy -> app : {hopped*1000:5.2f} ms each")
    print(f"  the second hop costs {(hopped-direct)*1000:.2f} ms per request "
          f"({hopped/direct:.1f}x)")

    _, d = fetch(f"{app_base}/whoami")
    _, p = fetch(f"{proxy_base}/whoami")
    dn, pn = set(d["header_names"]), set(p["header_names"])
    print(f"\n  headers the APP saw, direct        : {', '.join(sorted(dn))}")
    print(f"  headers the APP saw, through proxy : {', '.join(sorted(pn))}")
    print(f"  ADDED by the proxy   : {', '.join(sorted(pn - dn)) or '(none)'}")
    print(f"  DROPPED by the proxy : {', '.join(sorted(dn - pn)) or '(none)'}"
          "   <- hop-by-hop, must not be replayed")
    print("\n  A reverse proxy is not transparent. It rewrites the request on")
    print("  the way in and the response on the way out, and every default it")
    print("  applies is a decision somebody made for you.")


# ===================================================================== 2
def demo_buffering(app_base, proxy_base):
    print(SEP)
    print("DEMO 2 - THE TOPIC: the app streams, the client waits anyway")
    print(SEP)
    set_cfg(forwarded_mode="append")

    rows = []
    set_cfg(proxy_buffering=True, gzip=False)
    a = read_sse(f"{app_base}/stream")
    rows.append(("client -> app          (no proxy)", "n/a", "n/a", a))

    b = read_sse(f"{proxy_base}/stream")
    rows.append(("client -> proxy -> app", "on  (DEFAULT)", "off", b))

    set_cfg(proxy_buffering=False)
    c = read_sse(f"{proxy_base}/stream")
    rows.append(("client -> proxy -> app", "off", "off", c))

    set_cfg(gzip=True)
    d = read_sse(f"{proxy_base}/stream", headers={"Accept-Encoding": "gzip"})
    rows.append(("client -> proxy -> app", "off", "on", d))
    set_cfg(gzip=False)

    print(f"  {'route':<34} {'proxy_buffering':<15} {'gzip':<5} "
          f"{'1st tok':>8} {'complete':>9}  verdict")
    print(f"  {'-'*34} {'-'*15} {'-'*5} {'-'*8} {'-'*9}  {'-'*14}")
    for label, buf, gz, (first, total, text, _h) in rows:
        streaming = first is not None and first < total * 0.5
        verdict = "streaming" if streaming else "NOT streaming"
        print(f"  {label:<34} {buf:<15} {gz:<5} {ms(first):>6} ms "
              f"{ms(total):>6} ms  {verdict}")

    texts = {r[3][2] for r in rows}
    print(f"\n  reassembled text, all four rows identical: {len(texts) == 1}")
    print(f"    {rows[0][3][2]!r}")
    delta = (rows[1][3][0] - rows[0][3][0]) * 1000
    print(f"\n  Same app. Same bytes. Same total time. The default proxy config")
    print(f"  moved the first token {delta:.0f} ms later - which is the entire")
    print("  user-facing benefit of streaming (4.9, 6.9), deleted by one line")
    print("  nobody wrote, in a file the application developer does not own.")


# ===================================================================== 3
def demo_accel_header(app_base, proxy_base):
    print(SEP)
    print("DEMO 3 - X-Accel-Buffering: no, the override the APP controls")
    print(SEP)
    # Proxy left in its DEFAULT buffering config for both requests below.
    set_cfg(proxy_buffering=True, gzip=False)

    plain = read_sse(f"{proxy_base}/stream")
    accel = read_sse(f"{proxy_base}/stream?accel=1")
    direct = read_sse(f"{app_base}/stream?accel=1")

    print("  proxy config is UNCHANGED for both rows: proxy_buffering on\n")
    print(f"  {'app response header':<32} {'1st tok':>8} {'complete':>9}  verdict")
    print(f"  {'-'*32} {'-'*8} {'-'*9}  {'-'*14}")
    for label, r in (("(none)", plain), ("X-Accel-Buffering: no", accel)):
        first, total, _t, _h = r
        v = "streaming" if first < total * 0.5 else "NOT streaming"
        print(f"  {label:<32} {ms(first):>6} ms {ms(total):>6} ms  {v}")

    print(f"\n  the app really did send it   : "
          f"{'X-Accel-Buffering' in direct[3]} "
          f"(value {direct[3].get('X-Accel-Buffering')!r}, read straight from the app)")
    print(f"  the client received it       : "
          f"{'X-Accel-Buffering' in accel[3]}"
          "   <- the proxy CONSUMED the header")
    print("\n  This is the one lever a FastAPI service (0.9) has when somebody")
    print("  else owns nginx.conf. It is a request, not a guarantee: a proxy")
    print("  that does not implement it ignores it silently.")


# ===================================================================== 4
EDGE_USERS = ["203.0.113.7", "203.0.113.8", "198.51.100.22"]


def demo_forwarded_headers(proxy_base):
    print(SEP)
    print("DEMO 4 - X-Forwarded-For / -Proto: who is the client, really?")
    print(SEP)

    print("  (A) plain client, nothing in front of the proxy")
    print(f"    {'nginx config':<42} {'XFF app saw':<12} {'XFP':<6} "
          f"{'TLS?':<5} redirect the app builds")
    print(f"    {'-'*42} {'-'*12} {'-'*6} {'-'*5} {'-'*33}")
    for mode, label in (("none", "(no proxy_set_header lines)"),
                        ("append", "$proxy_add_x_forwarded_for + $scheme")):
        set_cfg(forwarded_mode=mode)
        _, w = fetch(f"{proxy_base}/whoami")
        print(f"    {label:<42} {str(w['x_forwarded_for'] or '-'):<12} "
              f"{str(w['x_forwarded_proto'] or '-'):<6} "
              f"{('yes' if w['secure'] else 'NO'):<5} {w['redirect_to']}")

    print("\n    Row 1 is an infinite redirect loop in production: the proxy")
    print("    terminated TLS, so the app sees plain http, decides the user is")
    print("    insecure and 301s to https - which arrives at the proxy, is")
    print("    decrypted, and reaches the app as http again. Forever.")

    print(f"\n  (B) with a CDN / load balancer in front - 3 users arrive with")
    print(f"      X-Forwarded-For already set: {', '.join(EDGE_USERS)}")
    print(f"    {'nginx directive':<44} {'XFF for user 1':<26} buckets")
    print(f"    {'-'*44} {'-'*26} {'-'*30}")
    for mode, label in (("remote_addr", "X-Forwarded-For $remote_addr   WRONG"),
                        ("append", "X-Forwarded-For $proxy_add_x_..  RIGHT")):
        set_cfg(forwarded_mode=mode)
        keys, first_xff = [], None
        for ip in EDGE_USERS:
            _, w = fetch(f"{proxy_base}/whoami", headers={"X-Forwarded-For": ip})
            keys.append(w["rate_limit_key"])
            first_xff = first_xff or w["x_forwarded_for"]
        n = len(set(keys))
        note = ("all 3 users share ONE" if n == 1 else "one per user")
        print(f"    {label:<44} {first_xff:<26} {n}  <- {note}")

    print("\n    One bucket for every user means the per-user rate limit in")
    print("    7.13 throttles everybody the moment one person is busy, and the")
    print("    audit log records the load balancer as the actor.")

    print("\n  (C) the caveat: X-Forwarded-For is client-supplied text.")
    set_cfg(forwarded_mode="append")
    _, w = fetch(f"{proxy_base}/whoami",
                 headers={"X-Forwarded-For": "10.9.9.9"})
    print(f"    a client that simply CLAIMS to be 10.9.9.9 -> app keys on "
          f"{w['rate_limit_key']!r}")
    print(f"    full chain the app saw: {w['x_forwarded_for']!r}")
    print("    Appending preserves the chain but cannot make the left end")
    print("    true. Trust it only from an edge you control (set_real_ip_from /")
    print("    real_ip_header in nginx), and count the hops you trust.")


# ===================================================================== 5
def demo_502_vs_504(proxy_base):
    print(SEP)
    print("DEMO 5 - 502 and 504 are different failures with different fixes")
    print(SEP)
    set_cfg(forwarded_mode="append", proxy_buffering=True, gzip=False,
            proxy_connect_timeout=5.0)

    # (a) 502 - the worker accepted the request and then died
    before = UP_STATS["requests"]
    t0 = time.perf_counter()
    code, payload = fetch(f"{proxy_base}/crash")
    el = time.perf_counter() - t0
    print(f"  app accepts, then dies       -> {code} after {el*1000:6.1f} ms")
    print(f"    {payload['error']}")
    print(f"    app requests during that  : {UP_STATS['requests'] - before}"
          "   <- it DID arrive; the app died holding it")

    # (b) 502 - nothing is listening upstream at all
    real_port = UPSTREAM["port"]
    UPSTREAM["port"] = free_port()
    before = UP_STATS["requests"]
    t0 = time.perf_counter()
    code, payload = fetch(f"{proxy_base}/ping")
    el = time.perf_counter() - t0
    UPSTREAM["port"] = real_port
    print(f"\n  nothing listening upstream   -> {code} after {el*1000:6.1f} ms")
    print(f"    {payload['error']}")
    print(f"    app requests during that  : {UP_STATS['requests'] - before}"
          "   <- the app never heard about it")
    print("    (that is not instant: this machine retransmits the SYN before")
    print("     surfacing the refusal, so even 'nothing is there' costs ~2s)")

    # (c) 504 - reachable, but silent for longer than the read budget
    set_cfg(proxy_read_timeout=1.0)
    t0 = time.perf_counter()
    code, payload = fetch(f"{proxy_base}/slow?delay=3")
    el = time.perf_counter() - t0
    print(f"\n  app thinks for 3s, budget 1s -> {code} after {el:6.2f} s")
    print(f"    {payload['error']}")
    print("    The app is fine and still working. The proxy gave up.")

    # (c) same endpoint, honest budget
    set_cfg(proxy_read_timeout=5.0)
    t0 = time.perf_counter()
    code, payload = fetch(f"{proxy_base}/slow?delay=3")
    el = time.perf_counter() - t0
    print(f"\n  app thinks for 3s, budget 5s -> {code} after {el:6.2f} s"
          f"   app_was_fine={payload.get('app_was_fine')}")

    # (d) the non-obvious part: the budget is BETWEEN READS, not total
    set_cfg(proxy_read_timeout=1.0, proxy_buffering=False)
    first, total, text, _h = read_sse(f"{proxy_base}/stream?n=5&gap=0.4")
    print(f"\n  stream: 5 tokens 0.4s apart, total 2.0s, budget still 1.0s")
    print(f"    -> completed in {total:.2f} s, first token at {first*1000:.0f} ms,"
          f" {len(text.split())} words")
    print("    proxy_read_timeout is the gap allowed BETWEEN two successive")
    print("    reads, not a cap on the whole response. A stream that keeps")
    print("    emitting survives it; a long SILENT think time before the first")
    print("    token does not. That is why keepalive comments (': ping') get")
    print("    sent on idle SSE connections.")
    set_cfg(proxy_read_timeout=60.0, proxy_buffering=True)


# ===================================================================== 6
def demo_body_limit(app_base, proxy_base):
    print(SEP)
    print("DEMO 6 - client_max_body_size: rejected before the app exists")
    print(SEP)
    set_cfg(forwarded_mode="append", proxy_buffering=True, gzip=False)

    payload = b'{"prompt": "' + b"x" * (2 * 1024 * 1024) + b'"}'
    hdr = {"Content-Type": "application/json"}
    mb = len(payload) / 1024 / 1024
    print(f"  payload: {len(payload):,} bytes ({mb:.2f} MiB) - a long prompt,")
    print("  a pasted transcript, or a scanned PDF for 5.4 ingestion.\n")

    before = UP_STATS["uploads"]
    code, r = fetch(f"{app_base}/upload", data=payload, headers=hdr)
    print(f"  straight to the app, no proxy         -> {code} "
          f"bytes={r.get('bytes'):,}   uploads seen: "
          f"{UP_STATS['uploads'] - before}")

    for limit in (1024 * 1024, 8 * 1024 * 1024):
        set_cfg(client_max_body_size=limit)
        before = UP_STATS["uploads"]
        code, r = fetch(f"{proxy_base}/upload", data=payload, headers=hdr)
        seen = UP_STATS["uploads"] - before
        tail = (f"bytes={r['bytes']:,}" if code == 200
                else r["error"].split(" - ")[0])
        print(f"  through proxy, client_max_body_size {limit//1024//1024}m  -> "
              f"{code} {tail:<26} uploads seen: {seen}")

    set_cfg(client_max_body_size=1024 * 1024)
    print("\n  The 413 row is the one that wastes an afternoon: the app handled")
    print("  the same bytes perfectly one line above, and its log has NOTHING")
    print("  in it, because the request stopped at the proxy. nginx's own")
    print("  error.log is where that evidence lives (0.10) - not the app's.")


def main():
    app_srv, app_base = start(AppHandler)
    UPSTREAM["port"] = app_srv.server_address[1]
    proxy_srv, proxy_base = start(ProxyHandler)

    print("NGINX is NOT installed and NOT required. The proxy below is a")
    print("stdlib Python model of the directives, so they can be measured.")
    print(f"  app   (upstream) : {app_base}")
    print(f"  proxy (the model): {proxy_base}   -> {app_base}")
    try:
        demo_topology(app_base, proxy_base)
        demo_buffering(app_base, proxy_base)
        demo_accel_header(app_base, proxy_base)
        demo_forwarded_headers(proxy_base)
        demo_502_vs_504(proxy_base)
        demo_body_limit(app_base, proxy_base)
        print(SEP)
        print("Every number above came from a default nobody chose. The app")
        print("was correct in all six demos. In 7.11 this proxy is the thing")
        print("in front of your deployment, and 7.11's streaming bug report")
        print("will be one of these six lines.")
        print(SEP)
    finally:
        for srv in (proxy_srv, app_srv):
            srv.shutdown()
            srv.server_close()
        print("both servers stopped")


if __name__ == "__main__":
    main()
