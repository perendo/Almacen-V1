#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de arranque para el entorno de pruebas del WMS.

Levanta:
  1. Backend FastAPI (uvicorn) en http://127.0.0.1:8000
  2. Frontend Next.js (npm run dev) en http://localhost:3000
  3. Abre el navegador en http://localhost:3000 cuando ambos responden

Uso:
    env\\Scripts\\python.exe start_wms.py
    (o simplemente start.bat)
"""

import atexit
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# El entorno virtual del proyecto vive en H:\Almacen\env
VENV_DIR = PROJECT_ROOT / "env"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000

IS_WINDOWS = os.name == "nt"
NPM_CMD = "npm.cmd" if IS_WINDOWS else "npm"

# ---------------------------------------------------------------------------
# Procesos hijos (para poder terminarlos al salir)
# ---------------------------------------------------------------------------
processes: list[subprocess.Popen] = []


def _kill_tree(proc: subprocess.Popen) -> None:
    """Termina un proceso y todos sus hijos (uvicorn --reload y npm crean hijos)."""
    if proc.poll() is not None:
        return
    if IS_WINDOWS:
        # taskkill /T mata todo el árbol de procesos
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def cleanup() -> None:
    """Termina todos los procesos hijos al salir del script."""
    if not processes:
        return
    print("\n[INFO] Cerrando servidores...")
    for proc in processes:
        _kill_tree(proc)
    processes.clear()
    print("[INFO] Servidores detenidos.")


atexit.register(cleanup)


def check_requirements() -> bool:
    """Verifica que existan los directorios y ejecutables necesarios."""
    missing = []

    if not VENV_PYTHON.exists():
        missing.append(f"Python del entorno virtual: {VENV_PYTHON}")
    if not (BACKEND_DIR / "app" / "main.py").exists():
        missing.append(f"Backend app: {BACKEND_DIR / 'app' / 'main.py'}")
    if not (FRONTEND_DIR / "package.json").exists():
        missing.append(f"Frontend package.json: {FRONTEND_DIR / 'package.json'}")
    if not (FRONTEND_DIR / "node_modules").exists():
        missing.append(
            f"Dependencias del frontend: {FRONTEND_DIR / 'node_modules'} "
            "(ejecute: cd frontend && npm install)"
        )

    if missing:
        print("[ERROR] Faltan los siguientes archivos/directorios:")
        for m in missing:
            print(f"  - {m}")
        return False
    return True


def _is_up(url: str, timeout: float = 2.0) -> bool:
    """Devuelve True si la URL responde con HTTP 2xx/3xx/4xx (el servidor está vivo)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "wms-startup"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except urllib.error.HTTPError as exc:
        return 200 <= exc.code < 500
    except Exception:
        return False


def wait_for(url: str, label: str, timeout: int = 90) -> bool:
    """Espera hasta que la URL responda o se agote el tiempo."""
    start = time.time()
    while time.time() - start < timeout:
        # Si un proceso murió, no tiene sentido seguir esperando
        for proc in processes:
            if proc.poll() is not None:
                print(f"[ERROR] {label}: el proceso terminó (código {proc.returncode}).")
                return False
        if _is_up(url):
            elapsed = time.time() - start
            print(f"  [OK] {label} respondió en {elapsed:.1f}s ({url})")
            return True
        time.sleep(1)
    print(f"  [WARN] {label} no respondió en {timeout}s ({url})")
    return False


def start_process(name: str, cmd: list[str], cwd: Path) -> subprocess.Popen:
    """Lanza un proceso heredando la consola (sin pipes, evita bloqueos)."""
    print(f"[*] {name}: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0,
    )
    processes.append(proc)
    return proc


def main() -> None:
    if not check_requirements():
        sys.exit(1)

    print("=" * 60)
    print("  WMS - Iniciando entorno de pruebas")
    print("  Entorno virtual: " + str(VENV_DIR))
    print("=" * 60)

    # --- Backend ---
    print(f"\n[1/3] Iniciando backend FastAPI en {BACKEND_HOST}:{BACKEND_PORT} ...")
    start_process(
        "Backend",
        [
            str(VENV_PYTHON),
            "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", BACKEND_HOST,
            "--port", str(BACKEND_PORT),
        ],
        BACKEND_DIR,
    )

    # --- Frontend ---
    print(f"\n[2/3] Iniciando frontend Next.js en puerto {FRONTEND_PORT} ...")
    start_process("Frontend", [NPM_CMD, "run", "dev"], FRONTEND_DIR)

    # --- Esperar disponibilidad ---
    print("\n[3/3] Esperando a que los servidores estén listos ...")
    backend_ok = wait_for(
        f"http://{BACKEND_HOST}:{BACKEND_PORT}/health", "Backend FastAPI", timeout=90
    )
    frontend_ok = wait_for(
        f"http://localhost:{FRONTEND_PORT}", "Frontend Next.js", timeout=120
    )

    frontend_url = f"http://localhost:{FRONTEND_PORT}"

    if backend_ok and frontend_ok:
        print(f"\n[*] Abriendo navegador en {frontend_url} ...")
        webbrowser.open(frontend_url)
    else:
        print("\n[WARN] Algún servicio no respondió; no se abre el navegador automáticamente.")

    print("\n" + "=" * 60)
    print("  WMS en ejecución:")
    print(f"    Backend : http://{BACKEND_HOST}:{BACKEND_PORT}  (docs: /docs)")
    print(f"    Frontend: {frontend_url}")
    print("=" * 60)
    print("  Presione Ctrl+C para detener ambos servidores.")
    print("=" * 60)

    # Mantener el script vivo y vigilar los procesos
    try:
        while True:
            time.sleep(1)
            for proc in list(processes):
                if proc.poll() is not None:
                    print(
                        f"\n[ADVERTENCIA] Un proceso terminó inesperadamente "
                        f"(código {proc.returncode})."
                    )
                    processes.remove(proc)
                    if not processes:
                        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupción por usuario.")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
