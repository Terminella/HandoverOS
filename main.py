#!/usr/bin/env python3
"""
HandoverOS Application Launcher

Starts the FastAPI backend and Next.js frontend together from a single command.

Usage:
    python main.py
"""

import atexit
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

BACKEND_PORT = 8000
FRONTEND_PORT = 3000
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}"

BACKEND_CMD = [
    sys.executable, "-m", "uvicorn", "app.main:app",
    "--host", "127.0.0.1",
    "--port", str(BACKEND_PORT),
]

FRONTEND_CMD = "npm.cmd run dev"

backend_proc: subprocess.Popen | None = None
frontend_proc: subprocess.Popen | None = None


def log(message: str, prefix: str = "") -> None:
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {prefix}{message}", flush=True)


def check_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_service(url: str, name: str, timeout: float = 30.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def cleanup() -> None:
    global backend_proc, frontend_proc
    for proc, name in ((backend_proc, "backend"), (frontend_proc, "frontend")):
        if proc and proc.poll() is None:
            log(f"Shutting down {name} (PID {proc.pid})...")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log(f"{name} did not terminate gracefully; killing.", prefix="WARN: ")
                proc.kill()
                proc.wait()
            log(f"{name} stopped.")
    log("All services stopped.")


def start_backend() -> subprocess.Popen:
    global backend_proc
    if check_port_in_use(BACKEND_PORT):
        raise RuntimeError(
            f"Port {BACKEND_PORT} is already in use. "
            "Close the existing backend or change the port."
        )

    log(f"Starting backend from {BACKEND_DIR}")
    log(f"Command: {' '.join(BACKEND_CMD)}")

    backend_proc = subprocess.Popen(
        BACKEND_CMD,
        cwd=str(BACKEND_DIR),
        env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    import threading

    def stream_output():
        assert backend_proc.stdout is not None
        for line in backend_proc.stdout:
            print(f"[backend] {line.rstrip()}", flush=True)

    threading.Thread(target=stream_output, daemon=True).start()

    return backend_proc


def start_frontend() -> subprocess.Popen:
    global frontend_proc
    if check_port_in_use(FRONTEND_PORT):
        raise RuntimeError(
            f"Port {FRONTEND_PORT} is already in use. "
            "Close the existing frontend or change the port."
        )

    log(f"Starting frontend from {FRONTEND_DIR}")
    log(f"Command: {' '.join(FRONTEND_CMD)}")

    frontend_proc = subprocess.Popen(
        FRONTEND_CMD,
        cwd=str(FRONTEND_DIR),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=os.environ.copy(),
    )

    import threading

    def stream_output():
        assert frontend_proc.stdout is not None
        for line in frontend_proc.stdout:
            print(f"[frontend] {line.rstrip()}", flush=True)

    threading.Thread(target=stream_output, daemon=True).start()

    return frontend_proc


def main() -> None:
    global backend_proc, frontend_proc

    print("=" * 60)
    print("  HandoverOS — Intelligent Knowledge Handover Platform")
    print("  Launching backend and frontend...")
    print("=" * 60)

    if not BACKEND_DIR.is_dir():
        print(f"ERROR: Backend directory not found: {BACKEND_DIR}", file=sys.stderr)
        sys.exit(1)
    if not FRONTEND_DIR.is_dir():
        print(f"ERROR: Frontend directory not found: {FRONTEND_DIR}", file=sys.stderr)
        sys.exit(1)

    for port, name in ((BACKEND_PORT, "backend"), (FRONTEND_PORT, "frontend")):
        if check_port_in_use(port):
            print(
                f"ERROR: Port {port} is already in use. "
                f"Cannot start {name}.",
                file=sys.stderr,
            )
            sys.exit(1)

    atexit.register(cleanup)

    def handle_signal(signum, frame):
        log("Received interrupt signal; shutting down...")
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_signal)

    try:
        backend_proc = start_backend()

        log("Waiting for backend to become healthy...")
        backend_healthy = wait_for_service(
            f"{BACKEND_URL}/health", "backend", timeout=30
        )
        if backend_healthy:
            log("Backend is healthy at " + BACKEND_URL)
        else:
            log("WARNING: Backend did not respond to health check.", prefix="WARN: ")

        frontend_proc = start_frontend()

        log("Waiting for frontend to become available...")
        frontend_ready = wait_for_service(
            FRONTEND_URL, "frontend", timeout=60
        )
        if frontend_ready:
            log("Frontend is ready at " + FRONTEND_URL)
        else:
            log("WARNING: Frontend did not become available.", prefix="WARN: ")

        print("=" * 60)
        print("  HandoverOS is running.")
        print(f"  Backend API:  {BACKEND_URL}")
        print(f"  Frontend UI:  {FRONTEND_URL}")
        print("  Press Ctrl+C to stop both services.")
        print("=" * 60)

        while True:
            time.sleep(1)
            if backend_proc and backend_proc.poll() is not None:
                log(f"Backend process exited unexpectedly (code {backend_proc.returncode}).", prefix="ERROR: ")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                log(f"Frontend process exited unexpectedly (code {frontend_proc.returncode}).", prefix="ERROR: ")
                break

    except RuntimeError as exc:
        log(str(exc), prefix="ERROR: ")
        cleanup()
        sys.exit(1)
    except Exception as exc:
        log(f"Unexpected error: {exc}", prefix="ERROR: ")
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()