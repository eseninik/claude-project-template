#!/usr/bin/env python3
"""
Codex Image Bridge — translate OpenAI Images API calls into Codex CLI invocations.

OpenClaw's openai image-generation-provider POSTs JSON to /v1/images/edits and
/v1/images/generations expecting {data: [{b64_json: "..."}]} responses. This
bridge listens on 127.0.0.1:PORT, accepts those POSTs, translates each request
into a `codex exec` invocation that uses Codex's built-in `image_gen` tool
(which works through ChatGPT OAuth — no OPENAI_API_KEY required), captures the
generated PNG from $CODEX_HOME/generated_images/<session>/*.png, base64-encodes
it, and returns it in OpenAI's JSON shape.

Deps: stdlib only.
Run:  python3 bridge.py        (defaults: 127.0.0.1:18799)
"""

import base64
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOG_LEVEL = os.environ.get("BRIDGE_LOG_LEVEL", "INFO")
HOST = os.environ.get("BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("BRIDGE_PORT", "18799"))
CODEX_BIN = os.environ.get("CODEX_BIN", "codex")
CODEX_MODEL = os.environ.get("CODEX_MODEL", "gpt-5.5")
CODEX_TIMEOUT_SEC = int(os.environ.get("CODEX_TIMEOUT_SEC", "300"))
CODEX_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
GENERATED_DIR = CODEX_HOME / "generated_images"
WORK_DIR = Path(os.environ.get("BRIDGE_WORKDIR", "/tmp/codex-image-bridge"))
WORK_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("bridge")

SESSION_ID_RE = re.compile(r"session id:\s*([0-9a-f-]{20,})", re.IGNORECASE)
DATA_URL_RE = re.compile(r"^data:(?P<mime>[^;,]+)(?P<params>(?:;[^,]+)*),(?P<payload>.+)$", re.DOTALL)


class BridgeError(Exception):
    pass


def decode_data_url(url: str) -> tuple[bytes, str]:
    log.debug("decode_data_url len=%d", len(url))
    m = DATA_URL_RE.match(url)
    if not m:
        raise BridgeError("image_url is not a data: URL")
    mime = m.group("mime") or "image/png"
    params = m.group("params") or ""
    payload = m.group("payload")
    if ";base64" in params:
        data = base64.b64decode(payload)
    else:
        from urllib.parse import unquote_to_bytes
        data = unquote_to_bytes(payload)
    log.debug("decoded image bytes=%d mime=%s", len(data), mime)
    return data, mime


def ext_for_mime(mime: str) -> str:
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
    }.get(mime.lower(), ".png")


def build_prompt_text(prompt: str, size: str | None, is_edit: bool) -> str:
    """Build a deterministic prompt that makes gpt-5.5 actually call image_gen."""
    size_hint = f"\n\nTarget size: {size}." if size else ""
    if is_edit:
        wrapper = (
            "Use the built-in image_gen tool to EDIT the attached input image "
            "according to the instructions below. Do not write any code, do not run "
            "shell or python commands, do not look up files. Call image_gen exactly "
            "once with the attached image as input_image and the instructions as the "
            "prompt. Then reply with a single short line, nothing else.\n\n"
            "--- EDIT INSTRUCTIONS ---\n"
        )
    else:
        wrapper = (
            "Use the built-in image_gen tool to GENERATE a new image from the prompt "
            "below. Do not write any code, do not run shell or python commands, do not "
            "look up files. Call image_gen exactly once. Then reply with a single short "
            "line, nothing else.\n\n"
            "--- IMAGE PROMPT ---\n"
        )
    return wrapper + prompt.strip() + size_hint + "\n"


def _snapshot_generated_dirs() -> set[str]:
    if not GENERATED_DIR.exists():
        return set()
    return {p.name for p in GENERATED_DIR.iterdir() if p.is_dir()}


def run_codex_once(prompt_text: str, input_image_path: Path | None, request_id: str) -> Path:
    """Spawn codex exec, return the generated PNG path.

    Identifies the resulting session by snapshotting GENERATED_DIR before/after.
    Survives the codex CLI suppressing its 'session id:' banner in non-TTY mode.
    """
    workdir = WORK_DIR / request_id
    workdir.mkdir(parents=True, exist_ok=True)
    prompt_file = workdir / "prompt.txt"
    prompt_file.write_text(prompt_text, encoding="utf-8")
    last_message_file = workdir / "last-message.txt"

    cmd = [
        CODEX_BIN, "exec",
        "--full-auto",
        "--skip-git-repo-check",
        "--color", "never",
        "-m", CODEX_MODEL,
        "-c", "sandbox_workspace_write.network_access=true",
        "-o", str(last_message_file),
    ]
    if input_image_path is not None:
        cmd.extend(["-i", str(input_image_path)])

    log.info("[%s] codex spawn: %s (input=%s, prompt_len=%d)",
             request_id, " ".join(cmd), input_image_path, len(prompt_text))

    before = _snapshot_generated_dirs()
    t0 = time.time()
    stdin_fh = prompt_file.open("rb")
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=stdin_fh,
            cwd=str(workdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    finally:
        stdin_fh.close()

    session_dir: Path | None = None
    early_png: Path | None = None
    deadline = t0 + CODEX_TIMEOUT_SEC
    poll = 0.4

    try:
        while True:
            if proc.poll() is not None:
                break
            after = _snapshot_generated_dirs()
            new_dirs = after - before
            if new_dirs and session_dir is None:
                session_dir = max(
                    (GENERATED_DIR / name for name in new_dirs),
                    key=lambda p: p.stat().st_mtime,
                )
                log.info("[%s] session dir appeared: %s (after %.1fs)",
                         request_id, session_dir.name, time.time() - t0)
            if session_dir is not None:
                pngs = sorted(session_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
                if pngs:
                    latest = pngs[-1]
                    if latest.stat().st_size > 0:
                        try:
                            with latest.open("rb") as fh:
                                head = fh.read(8)
                            if head.startswith(b"\x89PNG\r\n\x1a\n"):
                                early_png = latest
                                log.info("[%s] PNG detected (size=%d) — killing codex early at %.1fs",
                                         request_id, latest.stat().st_size, time.time() - t0)
                                proc.terminate()
                                try:
                                    proc.wait(timeout=2)
                                except subprocess.TimeoutExpired:
                                    proc.kill()
                                    proc.wait(timeout=2)
                                break
                        except OSError:
                            pass
            if time.time() > deadline:
                proc.kill()
                proc.wait(timeout=5)
                raise BridgeError(f"codex exec exceeded {CODEX_TIMEOUT_SEC}s")
            time.sleep(poll)
    except BridgeError:
        raise
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)

    elapsed = time.time() - t0
    try:
        stdout_bytes, stderr_bytes = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        stdout_bytes, stderr_bytes = b"", b""
    out = (stdout_bytes or b"").decode("utf-8", "replace")
    err = (stderr_bytes or b"").decode("utf-8", "replace")
    log.info("[%s] codex exit=%s elapsed=%.1fs stdout_len=%d early=%s",
             request_id, proc.returncode, elapsed, len(out), early_png is not None)

    if early_png is not None:
        log.info("[%s] generated png=%s size=%d", request_id, early_png, early_png.stat().st_size)
        return early_png

    if proc.returncode not in (0, None) and not session_dir:
        raise BridgeError(f"codex exec failed (code {proc.returncode}): {err[-300:]}")

    if session_dir is None:
        m = SESSION_ID_RE.search(out)
        if m:
            cand = GENERATED_DIR / m.group(1)
            if cand.exists():
                session_dir = cand
    if session_dir is None:
        raise BridgeError(
            "no new generated_images session created during codex run "
            "(codex may have refused to call image_gen — check stdout)"
        )

    grace = time.time() + 10
    while time.time() < grace:
        pngs = sorted(session_dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
        if pngs:
            latest = pngs[-1]
            log.info("[%s] generated png=%s size=%d", request_id, latest, latest.stat().st_size)
            return latest
        time.sleep(0.3)

    raise BridgeError(f"session dir {session_dir} created but no PNG inside")


def handle_image_request(payload: dict, is_edit: bool) -> dict:
    request_id = uuid.uuid4().hex[:10]
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise BridgeError("missing 'prompt'")
    n = int(payload.get("n", 1) or 1)
    size = payload.get("size") or None
    images_in = payload.get("images") or []

    log.info("[%s] request: edit=%s n=%d size=%s prompt_len=%d images_in=%d",
             request_id, is_edit, n, size, len(prompt), len(images_in))

    input_image_path: Path | None = None
    if is_edit:
        if not images_in:
            raise BridgeError("edit requires at least one input image")
        first = images_in[0]
        url = first.get("image_url") or first.get("url") or first
        if isinstance(url, dict):
            url = url.get("url") or url.get("image_url")
        if not isinstance(url, str):
            raise BridgeError("input image must carry image_url string")
        data, mime = decode_data_url(url)
        ext = ext_for_mime(mime)
        input_image_path = WORK_DIR / f"{request_id}-input{ext}"
        input_image_path.write_bytes(data)
        log.info("[%s] wrote input image %s (%d bytes)", request_id, input_image_path, len(data))

    prompt_text = build_prompt_text(prompt, size, is_edit)
    out_entries = []
    for i in range(n):
        sub_id = f"{request_id}-{i+1}"
        try:
            png_path = run_codex_once(prompt_text, input_image_path, sub_id)
        except BridgeError as e:
            log.error("[%s] sub %d failed: %s", request_id, i + 1, e)
            if not out_entries:
                raise
            break
        b64 = base64.b64encode(png_path.read_bytes()).decode("ascii")
        out_entries.append({"b64_json": b64})

    return {
        "created": int(time.time()),
        "data": out_entries,
    }


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "CodexImageBridge/0.1"

    def log_message(self, format: str, *args):  # noqa: A003
        log.info("http %s - %s", self.address_string(), format % args)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise BridgeError(f"invalid JSON body: {e}") from e

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str, code: str = "bridge_error"):
        log.warning("http error %d: %s", status, message)
        self._send_json(status, {"error": {"message": message, "type": code, "code": code}})

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "model": CODEX_MODEL})
            return
        self._send_error(404, f"unknown path {self.path}", "not_found")

    def do_POST(self):  # noqa: N802
        path = self.path.rstrip("/")
        is_edit = path.endswith("/v1/images/edits")
        is_gen = path.endswith("/v1/images/generations")
        if not (is_edit or is_gen):
            self._send_error(404, f"unknown path {self.path}", "not_found")
            return
        try:
            payload = self._read_json()
        except BridgeError as e:
            self._send_error(400, str(e), "bad_request")
            return
        try:
            result = handle_image_request(payload, is_edit=is_edit)
        except BridgeError as e:
            self._send_error(502, str(e), "codex_failed")
            return
        except Exception as e:
            log.exception("unhandled handler error")
            self._send_error(500, f"internal error: {e}", "internal_error")
            return
        self._send_json(200, result)


def main():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Codex Image Bridge starting on %s:%d (codex=%s model=%s timeout=%ss CODEX_HOME=%s)",
             HOST, PORT, CODEX_BIN, CODEX_MODEL, CODEX_TIMEOUT_SEC, CODEX_HOME)
    server = ThreadingHTTPServer((HOST, PORT), BridgeHandler)
    server.daemon_threads = True
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
