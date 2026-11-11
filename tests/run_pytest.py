import subprocess
import time
import os
import sys
import urllib.request
import urllib.error

backend_dir = r"H:\Almacen-V1\backend"
os.environ["PYTHONPATH"] = r"H:\Almacen\.venv\Lib\site-packages"

# Levantar servidor uvicorn
print("Levantando servidor uvicorn...")
proc = subprocess.Popen(
    [r"H:\Almacen\.venv\Scripts\python.exe", "-m", "uvicorn", "app.main:app",
     "--host", "127.0.0.1", "--port", "8000"],
    cwd=backend_dir,
    env={**os.environ, "PYTHONPATH": r"H:\Almacen\.venv\Lib\site-packages"},
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print(f"Servidor PID: {proc.pid}")

# Esperar a que esté listo
server_ready = False
for i in range(15):
    time.sleep(2)
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                print(f"Servidor listo después de {(i+1)*2} segundos")
                server_ready = True
                break
    except Exception:
        pass

if not server_ready:
    print("ERROR: El servidor no respondió después de 30 segundos")
    proc.kill()
    proc.wait()
    stdout, stderr = proc.communicate()
    print("STDOUT:", stdout[-1000:] if stdout else "(vacío)")
    print("STDERR:", stderr[-1000:] if stderr else "(vacío)")
    sys.exit(1)

# Ejecutar pytest
print("\n=== EJECUTANDO pytest ===")
result = subprocess.run(
    [r"H:\Almacen\.venv\Scripts\python.exe", "-m", "pytest", "tests_integration.py", "-v"],
    cwd=backend_dir,
    env={**os.environ, "PYTHONPATH": r"H:\Almacen\.venv\Lib\site-packages"},
    capture_output=True,
    text=True,
    timeout=120
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[-2000:])

print(f"\nCódigo de salida de pytest: {result.returncode}")

# Detener servidor
proc.kill()
proc.wait()
print("Servidor detenido.")

sys.exit(result.returncode)
