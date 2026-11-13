"""Local-only web server. API credentials never reach browser responses or exports."""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .companion import AppError, Companion, ROOT, http_json, read_env


def identity(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9-]{8,80}", value):
        raise AppError("Invalid visitor or conversation identifier.")
    return value


class Handler(BaseHTTPRequestHandler):
    server_version = "LanternCompanion/1.0"

    @property
    def app(self):
        return self.server.app

    def log_message(self, fmt, *args):
        # Do not log URLs, visitor identifiers, messages, or credentials.
        pass

    def send(self, data, status=200, content_type="application/json; charset=utf-8", attachment=False):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if isinstance(data, (dict, list)) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if attachment:
            self.send_header("Content-Disposition", f'attachment; filename="{self.app.character_id}-conversation.json"')
        self.end_headers()
        self.wfile.write(body)

    def validate_origin(self):
        # localhost binding plus Host/Origin checks block drive-by key writes and DNS rebinding.
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.headers.get("Host") not in allowed:
            raise AppError("This app only accepts local requests.", 403)
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + host for host in allowed}:
            raise AppError("Cross-site requests are not allowed.", 403)

    def do_GET(self):
        try:
            self.validate_origin()
            route = urlsplit(self.path)
            query = parse_qs(route.query)
            if route.path == "/api/status":
                c = self.app.config
                self.send({"character": {k:v for k,v in self.app.character.items() if k != "profile"},
                           "provider": c.provider, "model": c.model, "configured": bool(c.api_key) if c.provider == "deepseek" else True,
                           "character_id": self.app.character_id, "retrieval": "BM25", "version": "1.1"})
            elif route.path == "/api/session":
                visitor = identity(query.get("visitor", [None])[0])
                session = self.app.store.session(identity(query.get("session", [None])[0]), visitor)
                # Full prompts are available only in the explicit research export.
                for m in session["messages"]:
                    if m["metadata"]:
                        m["metadata"].pop("prompt", None)
                self.send({"session": session, "memory": self.app.store.memory(visitor)})
            elif route.path == "/api/memory":
                self.send({"memory": self.app.store.memory(identity(query.get("visitor", [None])[0]))})
            elif route.path == "/api/export":
                visitor = identity(query.get("visitor", [None])[0])
                session = self.app.store.session(identity(query.get("session", [None])[0]), visitor)
                session.pop("visitor", None)
                self.send({"project": "Whale Companion — " + self.app.character["name"], "character_id": self.app.character_id, "session": session,
                           "note": "Contains conversation text, supplied memory and prompts. Review personal details before sharing."}, attachment=True)
            elif route.path in ("/", "/app.js", "/style.css", "/mira.svg", "/pet.png"):
                filename = "index.html" if route.path == "/" else route.path[1:]
                path = self.app.web_root / filename
                if not path.is_file():
                    raise AppError("Not found.", 404)
                content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
                self.send(path.read_bytes(), content_type=content_type)
            else:
                raise AppError("Not found.", 404)
        except AppError as error:
            self.send({"error": str(error)}, error.status)
        except Exception:
            self.send({"error": "An internal error occurred. Please restart the app."}, 500)

    def body(self):
        if self.headers.get_content_type() != "application/json":
            raise AppError("Expected JSON.", 415)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 16384:
                raise ValueError
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise ValueError
            return value
        except (ValueError, UnicodeError):
            raise AppError("Invalid request body.") from None

    def do_POST(self):
        try:
            self.validate_origin()
            data = self.body()
            route = urlsplit(self.path).path
            if route == "/api/connect":
                key = data.get("key", "").strip() if isinstance(data.get("key", ""), str) else ""
                model = data.get("model", "deepseek-flash")
                if not 10 <= len(key) <= 512 or re.search(r"\s", key):
                    raise AppError("Enter a valid DeepSeek API key.")
                if model not in ("deepseek-flash", "deepseek-v4-pro"):
                    raise AppError("Select a supported model.")
                models = http_json("https://api.deepseek.com/models", headers={"Authorization": "Bearer " + key}, timeout=20)
                available = {m.get("id") for m in models.get("data", [])}
                if available and model not in available:
                    raise AppError("This model is not available to your API account.")
                with self.app.lock:
                    values = read_env()
                    values.update(COMPANION_PROVIDER="deepseek", DEEPSEEK_API_KEY=key, DEEPSEEK_MODEL=model)
                    content = "# Local credentials. Keep this file private.\n" + "\n".join(f"{k}={v}" for k,v in values.items()) + "\n"
                    temporary = ROOT / ".env.tmp"
                    temporary.write_text(content, encoding="utf-8")
                    temporary.replace(ROOT / ".env")
                    self.app.config.provider = "deepseek"
                    self.app.config.api_key = key
                    self.app.config.deepseek_model = model
                self.send({"ok": True, "provider": "deepseek", "model": model})
                return
            visitor = identity(data.get("visitor"))
            if route == "/api/session":
                with self.app.lock:
                    self.send({"session": self.app.store.new_session(visitor, data.get("mode", "enhanced")), "memory": self.app.store.memory(visitor)})
            elif route == "/api/chat":
                if not isinstance(data.get("message"), str):
                    raise AppError("Expected a text message.")
                self.send(self.app.chat(visitor, identity(data.get("session")), data["message"]))
            elif route == "/api/memory":
                values = data.get("values")
                if not isinstance(values, dict) or not set(values).issubset({"name", "preference", "goal"}):
                    raise AppError("Unknown memory field.")
                if any(not isinstance(v, str) or len(v) > 160 or "\n" in v for v in values.values()):
                    raise AppError("Each memory must be a single line, at most 160 characters.")
                with self.app.lock:
                    self.app.store.save_memory(visitor, {k:v.strip() for k,v in values.items()})
                self.send({"memory": self.app.store.memory(visitor)})
            elif route == "/api/forget":
                with self.app.lock:
                    self.app.store.forget(visitor)
                self.send({"ok": True})
            else:
                raise AppError("Not found.", 404)
        except AppError as error:
            self.send({"error": str(error)}, error.status)
        except Exception:
            self.send({"error": "An internal error occurred. Please restart the app."}, 500)


def make_server(port=8765, app=None):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.app = app or Companion()
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.getenv("COMPANION_PORT", read_env().get("COMPANION_PORT", "8765"))))
    parser.add_argument("--character", choices=("mira", "feiyu"), default="feiyu")
    args = parser.parse_args()
    with make_server(args.port, Companion(character_id=args.character)) as server:
        print(f"Companion ({args.character}) is ready at http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
