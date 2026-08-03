"""
0.8 - Consuming REST APIs from Python.

Runnable: `python 08_consuming_rest_apis.py`
Requires: requests  (pip install requests)

SAFE + OFFLINE: starts a throwaway HTTP server on 127.0.0.1 on a random
free port that deliberately misbehaves - rate limits, breaks, and hangs -
then shuts it down. No internet, no API keys, no money spent.

What this proves practically:
  1. A Session reuses ONE TCP connection. Counted server-side, not timed.
  2. Retrying 429 with backoff succeeds. Real elapsed time per attempt.
  3. Retrying 400 is pure waste - the server counter proves fail-fast works.
  4. timeout=(connect, read) fires when it should. Measured.
  5. Jitter breaks the thundering herd. Histogram of 24 clients retrying.
  6. Streaming needs iter_lines; .json() on an SSE body raises.
"""

import json
import random
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from requests.adapters import HTTPAdapter

SEP = "=" * 70

# Server-side truth. The client cannot fake these numbers.
STATS = {"connections": 0, "requests": 0}
ATTEMPTS: dict[str, int] = {}
STREAM_WORDS = ["The ", "invoice ", "was ", "paid ", "late", "."]
STREAM_GAP = 0.12


# ==================================================================== server
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"          # keep-alive: required for pooling

    def setup(self):
        super().setup()
        STATS["connections"] += 1          # ONE per TCP connection

    def log_message(self, *a):
        pass                               # quiet

    def _send(self, code, payload=None, extra=None):
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _route(self):
        STATS["requests"] += 1
        path = self.path.split("?")[0]
        ATTEMPTS[path] = ATTEMPTS.get(path, 0) + 1
        n = ATTEMPTS[path]

        if path == "/ping":
            self._send(200, {"ok": True})

        elif path == "/flaky":
            # Rate limited twice, then succeeds. Exactly the shape a real
            # provider produces when you exceed a per-minute quota.
            if n <= 2:
                # Retry-After on the FIRST one only, so the demo shows both
                # branches: honour the server, then fall back to your formula.
                extra = {"Retry-After": "1"} if n == 1 else None
                self._send(429, {"error": "rate limited", "attempt": n},
                           extra=extra)
            else:
                self._send(200, {"ok": True, "attempt": n})

        elif path == "/broken":
            # Always 400. No amount of retrying will ever change this.
            self._send(400, {"error": "max_tokens must be positive",
                             "attempt": n})

        elif path == "/slow":
            time.sleep(3.0)                # longer than the read timeout
            self._send(200, {"ok": True})

        elif path == "/stream":
            self._stream()

        else:
            self._send(404, {"error": "no such resource"})

    def do_GET(self):
        self._route()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)        # always drain, even when rejecting
        self._route()

    def _stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        for word in STREAM_WORDS:
            evt = ("event: content_block_delta\n"
                   f"data: {json.dumps({'delta': {'text': word}})}\n\n")
            self.wfile.write(evt.encode())
            self.wfile.flush()
            time.sleep(STREAM_GAP)
        self.close_connection = True


class QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # Demo 1 deliberately abandons 40 connections, and Demo 4 walks away
        # mid-response when the read timeout fires. The resulting resets are
        # EXPECTED here, so they are not printed. Any other exception still is.
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


def start_server():
    srv = QuietServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


# ================================================================ the client
RETRYABLE = {408, 429, 500, 502, 503, 504}


def backoff_seconds(attempt: int, rng: random.Random,
                    base: float = 0.25, cap: float = 8.0) -> float:
    """Exponential backoff WITH FULL JITTER.

    Without jitter every client that was rate-limited at the same instant
    retries at the same instant, rebuilding the exact spike that caused the
    429 - the thundering herd. Demo 5 measures that. random.uniform(0, raw)
    is "full jitter": spread across the whole window, not a wobble around it.
    """
    raw = min(cap, base * (2 ** attempt))      # 0.25, 0.5, 1.0, 2.0 ... cap
    return rng.uniform(0, raw)


def build_session(api_key: str) -> requests.Session:
    """A Session reuses the underlying TCP connection across calls.

    Bare requests.get() opens and tears down a connection every time. Over
    an agent loop making dozens of calls, the handshake cost (TLS especially)
    is a measurable share of latency (7.7). Demo 1 counts the connections.
    """
    s = requests.Session()
    s.headers.update({
        # Credential in a HEADER, read from the environment in real code.
        # Never hardcoded, never in a query string - it gets logged (0.7).
        "x-api-key": api_key,
        "Content-Type": "application/json",
    })
    # pool_maxsize caps concurrent connections so a fan-out in 6.10 cannot
    # exhaust file descriptors on the host.
    s.mount("http://", HTTPAdapter(pool_maxsize=20))
    s.mount("https://", HTTPAdapter(pool_maxsize=20))
    return s


def call_with_backoff(session, url, payload, *, rng, max_attempts=5,
                      connect_timeout=3.0, read_timeout=10.0, verbose=True):
    """The 0.7 decision tree, in code."""
    started = time.perf_counter()

    for attempt in range(max_attempts):
        try:
            resp = session.post(
                url, json=payload,
                # ALWAYS a timeout. The tuple separates "could not establish
                # a connection" (should be fast) from "the model is still
                # thinking" (legitimately slow). A single scalar forces one
                # bad compromise. No timeout means an infinite hang - the
                # single most common agent failure in 6.14.
                timeout=(connect_timeout, read_timeout),
            )
        except requests.Timeout as e:
            wait = backoff_seconds(attempt, rng)
            if verbose:
                print(f"    attempt {attempt+1}: TIMEOUT ({type(e).__name__})"
                      f" -> sleeping {wait:.2f}s")
            time.sleep(wait)
            continue

        elapsed = time.perf_counter() - started

        if resp.ok:
            if verbose:
                print(f"    attempt {attempt+1}: {resp.status_code} OK"
                      f"  (total elapsed {elapsed:.2f}s)")
            return resp.json()

        if resp.status_code not in RETRYABLE:
            # Fail FAST and LOUD. Raising is correct: the caller - an agent
            # node in 6.14 - needs a typed error to reason about, not a
            # silent None that poisons state three steps later.
            if verbose:
                print(f"    attempt {attempt+1}: {resp.status_code} "
                      f"NON-RETRYABLE -> raising immediately, no sleep")
            raise RuntimeError(
                f"non-retryable {resp.status_code}: {resp.text[:120]}")

        # Honour the server's own instruction when it gives one. Guessing a
        # backoff when the provider told you the exact number is how you get
        # rate-limited harder.
        hinted = resp.headers.get("Retry-After")
        wait = float(hinted) if hinted else backoff_seconds(attempt, rng)
        if verbose:
            src = "Retry-After header" if hinted else "jittered backoff"
            print(f"    attempt {attempt+1}: {resp.status_code} retryable"
                  f" -> sleeping {wait:.2f}s ({src})")
        time.sleep(wait)

    raise RuntimeError(f"exhausted {max_attempts} attempts")


# ===================================================================== 1
def demo_session_reuse(base) -> None:
    print(SEP)
    print("DEMO 1 - Session reuses ONE connection. Counted by the server.")
    print(SEP)
    n = 40

    STATS["connections"] = STATS["requests"] = 0
    t0 = time.perf_counter()
    for _ in range(n):
        requests.get(f"{base}/ping", timeout=5)      # new Session every time
    bare_t = time.perf_counter() - t0
    bare_conns = STATS["connections"]

    STATS["connections"] = STATS["requests"] = 0
    s = build_session("demo-key")
    t0 = time.perf_counter()
    for _ in range(n):
        s.get(f"{base}/ping", timeout=5)
    sess_t = time.perf_counter() - t0
    sess_conns = STATS["connections"]
    s.close()

    print(f"  {n} requests, bare requests.get() : "
          f"{bare_conns:>3} TCP connections   {bare_t*1000:6.0f} ms")
    print(f"  {n} requests, one Session        : "
          f"{sess_conns:>3} TCP connection{'s' if sess_conns != 1 else ' '}"
          f"    {sess_t*1000:6.0f} ms")
    print(f"\n  The connection count is the real result: {bare_conns} -> "
          f"{sess_conns}  ({bare_t/sess_t:.1f}x faster here).")
    print("  And this is plain HTTP to localhost - the cheapest handshake")
    print("  that exists. Against a real provider each of those connections")
    print("  also costs a TLS negotiation over the public internet, so the")
    print("  gap is wider still. An agent loop makes dozens of calls (6.10).")


# ===================================================================== 2
def demo_retry_success(base, rng) -> None:
    print(SEP)
    print("DEMO 2 - 429 twice, then 200. Backoff, and Retry-After honoured.")
    print(SEP)
    ATTEMPTS.clear()
    s = build_session("demo-key")
    result = call_with_backoff(s, f"{base}/flaky", {"prompt": "hi"}, rng=rng)
    s.close()
    print(f"\n  returned: {result}")
    print(f"  server saw {ATTEMPTS['/flaky']} requests - 2 refused, 1 served.")
    print("  Attempt 1 slept exactly 1.00s because the server SAID so.")
    print("  Attempt 2 had no header, so the jittered formula decided.")


# ===================================================================== 3
def demo_fail_fast(base, rng) -> None:
    print(SEP)
    print("DEMO 3 - 400 is not retryable. Proof: the server sees ONE request.")
    print(SEP)
    ATTEMPTS.clear()
    s = build_session("demo-key")
    t0 = time.perf_counter()
    try:
        call_with_backoff(s, f"{base}/broken", {"max_tokens": -5}, rng=rng)
    except RuntimeError as e:
        elapsed = time.perf_counter() - t0
        print(f"\n  raised after {elapsed*1000:.0f} ms: {e}")
    s.close()

    print(f"  server saw {ATTEMPTS['/broken']} request(s), max_attempts was 5.")
    print("\n  Now the same endpoint with a NAIVE retry-everything client:")
    ATTEMPTS.clear()
    s = build_session("demo-key")
    t0 = time.perf_counter()
    for attempt in range(5):
        r = s.post(f"{base}/broken", json={"max_tokens": -5}, timeout=5)
        if r.ok:
            break
        time.sleep(backoff_seconds(attempt, rng))     # retrying blindly
    naive = time.perf_counter() - t0
    s.close()
    print(f"    server saw {ATTEMPTS['/broken']} identical requests over "
          f"{naive:.2f}s, all 400.")
    print("    Against a real provider that is 5x the tokens, 5x the money,")
    print("    and the same failure. Retrying a 4xx cannot work: nothing")
    print("    about the request changed between attempts.")


# ===================================================================== 4
def demo_timeouts(base) -> None:
    print(SEP)
    print("DEMO 4 - timeout=(connect, read). The endpoint sleeps 3s.")
    print(SEP)
    s = build_session("demo-key")

    t0 = time.perf_counter()
    try:
        s.get(f"{base}/slow", timeout=(3.0, 1.0))   # read timeout 1s
    except requests.ReadTimeout:
        print(f"  timeout=(3.0, 1.0) -> ReadTimeout after "
              f"{time.perf_counter()-t0:.2f}s   <- the READ budget fired")

    t0 = time.perf_counter()
    r = s.get(f"{base}/slow", timeout=(3.0, 10.0))  # generous read timeout
    print(f"  timeout=(3.0, 10.0) -> {r.status_code} after "
          f"{time.perf_counter()-t0:.2f}s   <- server was just slow, not broken")
    s.close()

    # A connect timeout to a black-hole address, kept short so the demo
    # does not stall. 10.255.255.1 is non-routable: packets vanish.
    t0 = time.perf_counter()
    try:
        requests.get("http://10.255.255.1:9999/x", timeout=(1.0, 30.0))
    except requests.RequestException as e:
        print(f"  unreachable host, connect budget 1.0s -> "
              f"{type(e).__name__} after {time.perf_counter()-t0:.2f}s")

    print("\n  One scalar timeout cannot express both. Generation legitimately")
    print("  takes 60s; a TCP connect that takes 60s is a dead host. The tuple")
    print("  lets you fail fast on the second without killing the first.")


# ===================================================================== 5
def demo_thundering_herd() -> None:
    print(SEP)
    print("DEMO 5 - jitter vs no jitter: 24 clients rate-limited at once")
    print(SEP)
    clients = 24
    window = 1.0                      # backoff window for attempt 0

    rng = random.Random(42)           # seeded so this output is reproducible
    no_jitter = [window] * clients                       # everyone waits 1.0s
    with_jitter = [rng.uniform(0, window) for _ in range(clients)]

    def histogram(times, label):
        bins = [0] * 10                                   # 100 ms buckets
        for t in times:
            bins[min(9, int(t * 10))] += 1
        print(f"\n  {label}")
        for i, count in enumerate(bins):
            bar = "#" * count
            print(f"    {i/10:.1f}-{(i+1)/10:.1f}s |{bar:<24} {count}")
        return max(bins)

    peak_no = histogram(no_jitter, "WITHOUT jitter - retry at exactly 1.0s")
    peak_yes = histogram(with_jitter, "WITH full jitter - uniform(0, 1.0)")

    print(f"\n  peak retries in any 100ms window: {peak_no} vs {peak_yes}"
          f"   ({peak_no/max(peak_yes,1):.1f}x reduction)")
    print("  Without jitter you rebuild the exact spike that caused the 429,")
    print("  aimed at a server that is already struggling. Every client fails")
    print("  again together, and the herd re-forms at 2s, 4s, 8s.")
    print("  This is why 6.10 parallel fan-out needs jitter, not just backoff.")


# ===================================================================== 6
def demo_streaming(base) -> None:
    print(SEP)
    print("DEMO 6 - stream=True is NOT enough. chunk_size decides.")
    print(SEP)
    s = build_session("demo-key")

    def read_stream(chunk_size):
        """Return (time to first token, total time, reassembled text)."""
        t0 = time.perf_counter()
        first_at, pieces = None, []
        # stream=True stops requests from downloading the whole body before
        # returning the response object. The `with` block matters: it releases
        # the connection back to the pool instead of leaking it.
        with s.get(f"{base}/stream", timeout=(3.0, 30.0), stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(chunk_size=chunk_size,
                                        decode_unicode=True):
                if line and line.startswith("data: "):
                    if first_at is None:
                        first_at = time.perf_counter() - t0
                    pieces.append(json.loads(line[6:])["delta"]["text"])
        return first_at, time.perf_counter() - t0, "".join(pieces)

    # iter_lines() defaults to chunk_size=512: it asks the socket for 512
    # bytes and BLOCKS until it gets them or the connection closes. This whole
    # response is smaller than that, so nothing is yielded until the very end.
    # stream=True was honoured; the ITERATOR is what buffered.
    d_first, d_total, text = read_stream(512)
    print(f"  iter_lines()            (chunk_size=512, the DEFAULT)")
    print(f"    first token at {d_first*1000:5.0f} ms, "
          f"complete at {d_total*1000:5.0f} ms   <- identical: NOT streaming")

    # chunk_size=1 reads byte by byte, so a line is yielded the instant its
    # newline arrives. Slightly more syscalls; actual incremental delivery.
    s_first, s_total, _ = read_stream(1)
    print(f"  iter_lines(chunk_size=1)")
    print(f"    first token at {s_first*1000:5.0f} ms, "
          f"complete at {s_total*1000:5.0f} ms   <- streaming, "
          f"{(d_first - s_first)*1000:.0f} ms sooner")

    print(f"\n  reassembled (both identical): {text!r}")
    print("  Same flag, same server, same bytes. The default chunk_size threw")
    print("  the streaming away silently - no error, no warning, just a slow")
    print("  UI. Check time-to-first-token; do not trust stream=True alone.")

    # And the failure people hit exactly once: calling .json() on an SSE body.
    r = s.get(f"{base}/stream", timeout=(3.0, 30.0))
    try:
        r.json()
    except requests.exceptions.JSONDecodeError as e:
        print(f"\n  resp.json() on the same endpoint -> "
              f"{type(e).__name__}: {str(e)[:52]}")
    print("  The body is a sequence of SSE events, not one JSON document.")
    print("  Provider SDKs in Phase 4 wrap this loop - and set chunk_size -")
    print("  for you. Writing it once is how you recognise it going wrong.")
    s.close()


def main() -> None:
    srv, base = start_server()
    rng = random.Random(7)                 # seeded: reproducible backoffs
    print(f"requests {requests.__version__}")
    print(f"misbehaving server on {base}  (offline, 127.0.0.1 only)")
    try:
        demo_session_reuse(base)
        demo_retry_success(base, rng)
        demo_fail_fast(base, rng)
        demo_timeouts(base)
        demo_thundering_herd()
        demo_streaming(base)
        print(SEP)
        print("Every one of these six behaviours is a named agent failure mode")
        print("in 6.14. The client is where they get prevented - not in the")
        print("prompt, and not in the graph.")
        print(SEP)
    finally:
        srv.shutdown()
        print("server stopped")


if __name__ == "__main__":
    main()
