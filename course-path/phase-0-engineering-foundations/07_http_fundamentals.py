"""
0.7 - HTTP Fundamentals.

Runnable: `python 07_http_fundamentals.py`
Requires: nothing. Standard library only.

SAFE + OFFLINE: starts a throwaway HTTP server on 127.0.0.1 on a random
free port, talks to it, and shuts it down. No internet, no real API keys,
nothing leaves your machine.

What this proves practically:
  1. HTTP is TEXT. A raw socket + a hand-typed request gets a real response.
  2. Status codes split into three ACTIONS, not nine trivia facts.
  3. A missing Content-Type header really does get you a 415.
  4. Streaming: first byte arrives long before the last one. Timed.
  5. .json() on a streaming body RAISES. The body is not one document.
  6. A key in the query string lands in the server log. In the body it does not.
  7. GET is idempotent, POST is not - shown with a counter.
"""

import json
import socket
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SEP = "=" * 70

ACCESS_LOG: list[str] = []          # what the server "logs" - the leak surface
COUNTER = {"orders": 0}             # proves POST is not idempotent
FAKE_KEY = "sk-live-DEMO0000NOTAREALKEY0000"
STREAM_WORDS = ["This ", "invoice ", "is ", "overdue", "."]
STREAM_GAP = 0.15                   # seconds between server-sent events


# ==================================================================== server
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"   # keep-alive; requires Content-Length

    def log_message(self, fmt, *args):
        # Real servers log the REQUEST LINE - method, path, query string.
        # That is exactly why a credential in the URL is a leak (7.13).
        ACCESS_LOG.append(fmt % args)

    def _send(self, code, payload=None, ctype="application/json", extra=None):
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    # ---- GET ----------------------------------------------------------
    def do_GET(self):
        path, _, query = self.path.partition("?")

        if path.startswith("/status/"):
            code = int(path.rsplit("/", 1)[1])
            # 429 is the one 4xx that tells you HOW LONG to wait.
            extra = {"Retry-After": "2"} if code == 429 else None
            self._send(code, {"code": code}, extra=extra)

        elif path == "/stream":
            self._stream()

        elif path == "/counter":
            self._send(200, {"orders": COUNTER["orders"]})

        elif path == "/echo":
            self._send(200, {"query": query})

        else:
            self._send(404, {"error": "no such resource"})

    # ---- POST ---------------------------------------------------------
    def do_POST(self):
        # Always drain the body first, even when rejecting - otherwise the
        # unread bytes corrupt the next request on a kept-alive connection.
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b""

        if self.path == "/echo":
            if self.headers.get("Content-Type") != "application/json":
                # 415 Unsupported Media Type. Not a guess - servers really
                # do this, and "it worked in curl" usually means curl set it.
                self._send(415, {"error": "expected Content-Type: application/json"})
                return
            self._send(200, {"received": json.loads(raw or b"{}")})

        elif self.path == "/orders":
            COUNTER["orders"] += 1          # a SIDE EFFECT - this is the point
            self._send(201, {"order_id": COUNTER["orders"]})

        else:
            self._send(404, {"error": "no such resource"})

    def _stream(self):
        """Server-Sent Events: many small writes, not one body."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")   # no length: we stream to EOF
        self.end_headers()
        for word in STREAM_WORDS:
            evt = ("event: content_block_delta\n"
                   f"data: {json.dumps({'delta': {'text': word}})}\n\n")
            self.wfile.write(evt.encode())
            self.wfile.flush()                    # flush or nothing streams
            time.sleep(STREAM_GAP)
        self.close_connection = True


def start_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)   # port 0 = any free
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


# ===================================================================== 1
def demo_raw_socket(host, port) -> None:
    print(SEP)
    print("DEMO 1 - HTTP is TEXT. Hand-typed request over a raw socket.")
    print(SEP)

    request = (
        "POST /echo HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Content-Type: application/json\r\n"
        f"x-api-key: {FAKE_KEY}\r\n"
        "Connection: close\r\n"
        # Content-Length must be the EXACT byte count of the body. Get it
        # wrong and the server either hangs waiting for bytes that never
        # come, or reads into the next request. Libraries compute this.
        "Content-Length: 32\r\n"
        "\r\n"
        '{"model":"demo","max_tokens":10}'
    )
    print("  --- what goes ON THE WIRE (\\r\\n shown as line breaks) ---")
    for line in request.split("\r\n"):
        print(f"    {line}" if line else "    <-- BLANK LINE: headers end, body begins")

    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(request.encode())
        chunks = []
        while True:
            b = sock.recv(4096)
            if not b:
                break
            chunks.append(b)
    raw = b"".join(chunks).decode()

    print("\n  --- what comes BACK, byte for byte ---")
    for line in raw.split("\r\n"):
        print(f"    {line}" if line else "    <-- BLANK LINE: headers end, body begins")

    print("\n  No library involved. requests, httpx and every SDK in Phase 4")
    print("  are typing these same bytes for you.")


# ===================================================================== 2
RETRYABLE = {408, 429, 500, 502, 503, 504}


def decide(code: int) -> str:
    """The whole retry policy. Three actions, not nine facts."""
    if 200 <= code < 300:
        return "PROCEED"
    if code in RETRYABLE:
        return "RETRY with backoff"
    if 400 <= code < 500:
        return "DO NOT RETRY - the request is wrong"
    return "DO NOT RETRY - unclassified"


def demo_status_codes(base) -> None:
    print(SEP)
    print("DEMO 2 - status codes, grouped by the ACTION they demand")
    print(SEP)
    meanings = {
        200: "OK", 201: "Created", 400: "Malformed request",
        401: "Not authenticated", 403: "Authenticated but not permitted",
        404: "No such resource", 422: "Valid JSON, invalid meaning",
        429: "Rate limited", 500: "Server fault", 503: "Temporarily unavailable",
    }
    print(f"  {'code':<5} {'meaning':<34} {'Retry-After':<12} action")
    print(f"  {'-'*5} {'-'*34} {'-'*12} {'-'*30}")
    for code, meaning in meanings.items():
        req = urllib.request.Request(f"{base}/status/{code}")
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                got, hdr = r.status, r.headers.get("Retry-After")
        except urllib.error.HTTPError as e:
            # urllib raises on 4xx/5xx. The RESPONSE is still in the exception -
            # headers and body included. Throwing it away loses the reason.
            got, hdr = e.code, e.headers.get("Retry-After")
        print(f"  {got:<5} {meaning:<34} {str(hdr or '-'):<12} {decide(got)}")

    print("\n  The operational rule: 4xx = YOU are wrong, 5xx = THEY are wrong.")
    print("  429 is the single 4xx worth retrying, and it is the only code")
    print("  above that told you how long to wait.")


# ===================================================================== 3
def demo_headers_matter(base) -> None:
    print(SEP)
    print("DEMO 3 - the same body, one header apart")
    print(SEP)
    body = json.dumps({"invoice": "INV-001"}).encode()

    for ctype in (None, "application/json"):
        req = urllib.request.Request(f"{base}/echo", data=body, method="POST")
        if ctype:
            req.add_header("Content-Type", ctype)
        label = ctype or "(none - urllib sends x-www-form-urlencoded)"
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                print(f"  Content-Type: {label:<48} -> {r.status} OK")
        except urllib.error.HTTPError as e:
            detail = json.loads(e.read())["error"]
            print(f"  Content-Type: {label:<48} -> {e.code} {detail}")

    print("\n  Identical bytes in the body. One header decided the outcome.")


# ===================================================================== 4
def demo_streaming(base) -> None:
    print(SEP)
    print("DEMO 4 - streaming: time to FIRST token vs time to LAST")
    print(SEP)

    # (a) read incrementally, as a streaming client does
    t0 = time.perf_counter()
    first_at = None
    events = []
    with urllib.request.urlopen(f"{base}/stream", timeout=10) as r:
        print(f"  Content-Type: {r.headers.get('Content-Type')}")
        for line in r:                       # yields AS DATA ARRIVES
            line = line.decode().strip()
            if line.startswith("data: "):
                if first_at is None:
                    first_at = time.perf_counter() - t0
                events.append(json.loads(line[6:])["delta"]["text"])
    stream_total = time.perf_counter() - t0

    # (b) wait for the whole body, as a non-streaming client does
    t0 = time.perf_counter()
    with urllib.request.urlopen(f"{base}/stream", timeout=10) as r:
        whole = r.read()
    buffered_first = time.perf_counter() - t0

    print(f"\n  streaming   : first token at {first_at*1000:6.0f} ms, "
          f"complete at {stream_total*1000:6.0f} ms")
    print(f"  buffered    : first token at {buffered_first*1000:6.0f} ms, "
          f"complete at {buffered_first*1000:6.0f} ms")
    print(f"  reassembled : {''.join(events)!r}")
    print(f"\n  Same {len(whole)} bytes, same total time. The ONLY difference is")
    print(f"  when the user sees the first word: {(buffered_first - first_at)*1000:.0f} ms earlier.")
    print("  That gap is the entire user-facing case for streaming (4.9).")

    print("\n  --- and why .json() cannot work on this body ---")
    try:
        json.loads(whole)
    except json.JSONDecodeError as e:
        print(f"    json.loads(body) -> JSONDecodeError: {e}")
    print("    The body is a SEQUENCE of events separated by blank lines,")
    print("    not one JSON document. Parse it line by line or use an SDK.")
    print("\n  NOTE: NGINX with default proxy_buffering would turn the first")
    print("  timing into the second - it holds chunks until the response")
    print("  completes. That is the 0.12 setting that silently kills streaming.")


# ===================================================================== 5
def demo_credential_leak(base) -> None:
    print(SEP)
    print("DEMO 5 - key in the URL vs key in the body: read the server log")
    print(SEP)
    ACCESS_LOG.clear()

    # WRONG: credential as a query parameter
    urllib.request.urlopen(f"{base}/echo?api_key={FAKE_KEY}&limit=10",
                           timeout=5).read()

    # RIGHT: credential as a header, payload in the body
    req = urllib.request.Request(f"{base}/echo",
                                 data=json.dumps({"limit": 10}).encode(),
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", FAKE_KEY)
    urllib.request.urlopen(req, timeout=5).read()

    print("  server access log, exactly as written:")
    for entry in ACCESS_LOG:
        print(f"    {entry}")

    leaked = [e for e in ACCESS_LOG if FAKE_KEY in e]
    print(f"\n  entries containing the key: {len(leaked)} of {len(ACCESS_LOG)}")
    print("  The header request sent the SAME key and the log has no trace of")
    print("  it. Query strings are logged by every server, proxy and CDN in")
    print("  the path - and those logs are retained, shipped and indexed.")


# ===================================================================== 6
def demo_idempotency(base) -> None:
    print(SEP)
    print("DEMO 6 - GET is idempotent. POST is not. Hence retry policy.")
    print(SEP)

    def get_count():
        with urllib.request.urlopen(f"{base}/counter", timeout=5) as r:
            return json.loads(r.read())["orders"]

    print(f"  GET  /counter x3 -> {get_count()}, {get_count()}, {get_count()}"
          "   (nothing changed)")

    ids = []
    for _ in range(3):
        req = urllib.request.Request(f"{base}/orders", data=b"{}", method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as r:
            ids.append(json.loads(r.read())["order_id"])
    print(f"  POST /orders  x3 -> order ids {ids}   (THREE orders now exist)")

    print("\n  This is why a timed-out POST is the hard case: the request may")
    print("  have succeeded before the timeout fired. Retrying a read is free;")
    print("  retrying a write needs an idempotency key or you double-charge.")


def main() -> None:
    srv, base = start_server()
    host, port = srv.server_address[0], srv.server_address[1]
    print(f"throwaway server on {base}  (offline, 127.0.0.1 only)")
    try:
        demo_raw_socket(host, port)
        demo_status_codes(base)
        demo_headers_matter(base)
        demo_streaming(base)
        demo_credential_leak(base)
        demo_idempotency(base)
        print(SEP)
        print("Every LLM call in Phase 4 and every MCP transport in 6.12 is")
        print("one of these exchanges. The status code decides what an agent")
        print("does next, and that decision is worth real money in 6.14.")
        print(SEP)
    finally:
        srv.shutdown()
        print("server stopped")


if __name__ == "__main__":
    main()
