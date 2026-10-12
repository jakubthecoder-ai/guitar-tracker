"""Local write-back server for the HTML report (mode A). Binds 127.0.0.1 only; requires a random token."""

import json
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .events import validate_event
from .report import render_html, view_model
from .views import render_all

MAX_BODY = 1_000_000


def make_handler(ctx, token: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep stdout for JSON only
            pass

        def _authorized(self) -> bool:
            q = parse_qs(urlparse(self.path).query)
            return secrets.compare_digest(q.get("t", [""])[0], token)

        def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode())

        def do_GET(self):
            if not self._authorized():
                return self._json(403, {"ok": False, "error": "bad token"})
            route = urlparse(self.path).path
            if route == "/health":
                return self._json(200, {"ok": True})
            if route in ("/", "/index.html"):
                st = ctx.state()
                html = render_html(view_model(ctx.store, st, ctx.today, server={"live": True}))
                return self._send(200, html.encode(), "text/html; charset=utf-8")
            return self._json(404, {"ok": False, "error": "not found"})

        def do_POST(self):
            if not self._authorized():
                return self._json(403, {"ok": False, "error": "bad token"})
            if urlparse(self.path).path != "/events":
                return self._json(404, {"ok": False, "error": "not found"})
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json(413, {"ok": False, "error": "too large"})
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._json(400, {"ok": False, "error": "invalid json"})
            events = data.get("events", []) if isinstance(data, dict) else []
            rejected = []
            for ev in events:
                errs = validate_event(ev)
                if errs:
                    rejected.append({"id": ev.get("id"), "errors": errs})
                elif ev.get("source") != "html":
                    rejected.append({"id": ev.get("id"), "errors": ["source musi być 'html'"]})
            if rejected or not events:
                return self._json(400, {"ok": False, "rejected": rejected, "error": "brak zdarzeń" if not events else None})
            with ctx.store.lock():
                res = ctx.store.append_events(events)
                render_all(ctx.store.home, ctx.state())
            return self._json(200, {"ok": True, **res})

    return Handler


def serve(ctx, port: int, open_browser: bool) -> None:
    token = secrets.token_urlsafe(16)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(ctx, token))
    url = f"http://127.0.0.1:{httpd.server_address[1]}/?t={token}"
    print(json.dumps({"ok": True, "url": url, "note": "Ctrl+C kończy serwer. Commit danych: `gt derive` / koniec sesji."},
                     ensure_ascii=False), flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        ctx.store.commit("raport: zmiany z HTML")
