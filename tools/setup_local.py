"""Install a project-local Ollama runtime and fetch the configured model."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
WORK = ROOT / ".work"
HOST = "http://127.0.0.1:11434"
VERSION = "v0.40.15"
MODEL = "qwen3:4b"


def request_json(url, data=None, timeout=30):
    payload = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, payload, {"Content-Type": "application/json", "User-Agent": "WhaleCompanion-local-setup"})
    return urllib.request.urlopen(req, timeout=timeout)


def install_runtime():
    exe = RUNTIME / "ollama" / "ollama.exe"
    if exe.exists():
        return exe
    RUNTIME.mkdir(exist_ok=True)
    with request_json(f"https://api.github.com/repos/ollama/ollama/releases/tags/{VERSION}") as response:
        release = json.load(response)
    asset = next(a for a in release["assets"] if a["name"] == "ollama-windows-amd64.zip")
    digest = asset.get("digest", "")
    if not digest.startswith("sha256:"):
        raise RuntimeError("The release has no SHA256 checksum; verify the download before installing.")
    archive = RUNTIME / "ollama-windows-amd64.zip"
    if not archive.exists():
        part = archive.with_suffix(".zip.part")
        print(f"Downloading Ollama {VERSION}: {asset['size'] / 1e9:.2f} GB", flush=True)
        with urllib.request.urlopen(asset["browser_download_url"], timeout=60) as source, part.open("wb") as target:
            downloaded = 0
            last_print = 0
            while block := source.read(1024 * 1024):
                target.write(block)
                downloaded += len(block)
                if downloaded - last_print >= 128 * 1024 * 1024:
                    print(f"Runtime: {downloaded / asset['size']:.0%}", flush=True)
                    last_print = downloaded
        part.replace(archive)
    with archive.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
    if checksum != digest.split(":", 1)[1]:
        archive.unlink()
        raise RuntimeError("Ollama checksum did not match. Run setup again.")
    print("Runtime checksum verified. Extracting...", flush=True)
    destination = RUNTIME / "ollama"
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            resolved = (destination / item.filename).resolve()
            if not resolved.is_relative_to(destination.resolve()):
                raise RuntimeError("Unsafe archive member")
        z.extractall(destination)
    archive.unlink()
    return exe


def ensure_ollama(exe):
    try:
        with request_json(HOST + "/api/version", timeout=2) as response:
            print("Using running Ollama:", json.load(response), flush=True)
            return
    except (OSError, ValueError):
        pass
    WORK.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(OLLAMA_HOST="127.0.0.1:11434", OLLAMA_MODELS=str(RUNTIME / "models"), OLLAMA_NO_CLOUD="1")
    with (WORK / "ollama.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen([str(exe), "serve"], cwd=ROOT, env=env, stdout=log, stderr=log,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    (WORK / "ollama.pid").write_text(str(process.pid))
    for _ in range(30):
        try:
            with request_json(HOST + "/api/version", timeout=2):
                print("Ollama is ready.", flush=True)
                return
        except OSError:
            if process.poll() is not None:
                raise RuntimeError("Ollama failed to start; see .work/ollama.log")
            time.sleep(1)
    raise RuntimeError("Ollama startup timed out; see .work/ollama.log")


def pull_model():
    print(f"Fetching {MODEL} (approximately 2.6 GB on first setup)...", flush=True)
    last = None
    with request_json(HOST + "/api/pull", {"model": MODEL, "stream": True}, timeout=180) as response:
        for line in response:
            item = json.loads(line)
            if "error" in item:
                raise RuntimeError(item["error"])
            status = item.get("status", "")
            pct = int(100 * item.get("completed", 0) / item["total"]) if item.get("total") else None
            state = (status, None if pct is None else pct // 10)
            if state != last:
                print(status + (f" {pct}%" if pct is not None else ""), flush=True)
                last = state
    print("Setup complete. Set COMPANION_PROVIDER=ollama in .env, then run Start-Whale.cmd.", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        ensure_ollama(install_runtime())
        pull_model()
    except Exception as error:
        print(f"Setup failed: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
