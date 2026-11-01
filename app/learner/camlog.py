"""A log of the camera and the microphone side by side (testing phase, allowed by the user on 2026-10-31).

Why: the recorder and the lip mirror each measure the sound for themselves, and they disagreed (the mirror ticked "hum" before anyone hummed;
the recorder missed the vowel). To see where, both write what they measured, about ten times a second, on the same clock (epoch milliseconds):
  mirror: gap and width of the lips, closed or not, the sound level, share of low pitch, voice test, the stage the coach was in
  mic:    the sound level, voice test, high/low ratio, the two sounds counted, why the recording ended
Only these numbers are kept, never a picture of the face and never the sound. One line of JSON per turn in logs/camera.jsonl.

The browser cannot write a file, and a post to Streamlit itself would rerun the page in the middle of a recording, so this starts a tiny server of its own
on the same machine (127.0.0.1 only) that appends what the two components post. Remove this log when the testing phase is over.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import streamlit as st

PORT = 8503
PATH = Path(__file__).resolve().parents[1] / "logs" / "camera.jsonl"
_lock = threading.Lock()


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        try:
            size = min(int(self.headers.get("Content-Length", "0")), 4_000_000)
            entry = json.loads(self.rfile.read(size).decode("utf-8"))
            entry["received"] = round(time.time() * 1000)
            PATH.parent.mkdir(parents=True, exist_ok=True)
            with _lock, PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except (ValueError, OSError):
            pass
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        for k, v in (("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Methods", "POST"), ("Access-Control-Allow-Headers", "*")):
            self.send_header(k, v)
        self.end_headers()

    def log_message(self, *args) -> None:       # no line per request on the console
        pass


@st.cache_resource
def _start() -> str | None:
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    except OSError:                              # the port is taken: the log is simply off
        return None
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{PORT}/log"


def url() -> str | None:
    """Where the components post their numbers, or None when the log is off."""
    return _start()
