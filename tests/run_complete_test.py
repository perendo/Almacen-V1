import subprocess
import time
import os
import json
import urllib.request
import urllib.error

backend_dir = r"H:\Almacen-V1\backend"
os.environ["PYTHONPATH"] = r"H:\Almacen\.venv\Lib\site-packages"

# Levantar servidor uvicorn en background
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

# Esperar a que el servidor esté listo
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
    sys.exit(1)

# Función helper para hacer peticiones (corregida: leer body una sola vez)
def api_request(method, path, token=None, body=None):
    url = f"http://127.0.0.1:8000{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body_bytes = resp.read()
            return resp.status, json.loads(body_bytes.decode()) if body_bytes else None
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            return e.code, json.loads(body_bytes.decode()) if body_bytes else None
        except:
            return e.code, body_bytes.decode() if body_bytes else None
    except Exception as e:
        return None, str(e)

# Ejecutar pruebas
print("\n=== EJECUTANDO PRUEBAS DE API ===\n")

# 1. Login superadmin
status, data = api_request("POST", "/api/v1/auth/login/json",
                          body={"email": "superadmin@demo.com", "password": "admin123"})
if status == 200:
    token = data["access_token"]
    print(f"✓ Login superadmin: OK")
else:
    print(f"✗ Login superadmin: FALLO - {status} {data}")
    token = None

# 2. /auth/me
if token:
    status, data = api_request("GET", "/api/v1/auth/me", token=token)
    if status == 200:
        print(f"✓ /auth/me: {data['email']} - Roles: {', '.join(data['roles'])}")
    else:
        print(f"✗ /auth/me: FALLO - {status} {data}")

# 3. GET /articles/
if token:
    status, data = api_request("GET", "/api/v1/articles/", token=token)
    if status == 200:
        print(f"✓ GET /articles/: {len(data)} registros")
    else:
        print(f"✗ GET /articles/: FALLO - {status} {data}")

# 4. GET /stock/
if token:
    status, data = api_request("GET", "/api/v1/stock/", token=token)
    if status == 200:
        print(f"✓ GET /stock/: {len(data)} registros")
    else:
        print(f"✗ GET /stock/: FALLO - {status} {data}")

# 5. Endpoints legales
for path in ["/terminos", "/privacidad", "/aviso-legal"]:
    status, data = api_request("GET", path)
    if status == 200:
        print(f"✓ GET {path}: {status}")
    else:
        print(f"✗ GET {path}: FALLO - {status} {data}")

# 6. 401 sin token
status, data = api_request("GET", "/api/v1/articles/")
if status == 401:
    print(f"✓ Sin token: 401 correcto")
else:
    print(f"✗ Sin token: código inesperado {status} {data}")

# 7. Login gerente + aislamiento multitenencia
status, data = api_request("POST", "/api/v1/auth/login/json",
                          body={"email": "gerente@demo.com", "password": "gerente123"})
if status == 200:
    gtoken = data["access_token"]
    print(f"✓ Login gerente: OK")
    
    # Gerente consultar empresa 999 -> debe ser 0
    status, data = api_request("GET", "/api/v1/articles/?company_id=999", token=gtoken)
    if status == 200 and len(data) == 0:
        print(f"✓ Aislamiento gerente/empresa 999: 0 registros (correcto)")
    else:
        print(f"✗ Aislamiento gerente/empresa 999: {len(data) if isinstance(data, list) else 'error'} registros (debe ser 0)")
else:
    print(f"✗ Login gerente: FALLO - {status} {data}")

# 8. Login operario
status, data = api_request("POST", "/api/v1/auth/login/json",
                          body={"email": "operario@demo.com", "password": "operario123"})
if status == 200:
    otoken = data["access_token"]
    status, data = api_request("GET", "/api/v1/auth/me", token=otoken)
    if status == 200:
        print(f"✓ Login operario: OK - Roles: {', '.join(data['roles'])}")
    else:
        print(f"✗ Login operario /me: FALLO - {status} {data}")
else:
    print(f"✗ Login operario: FALLO - {status} {data}")

# 9. Login auditor
status, data = api_request("POST", "/api/v1/auth/login/json",
                          body={"email": "auditor@demo.com", "password": "auditor123"})
if status == 200:
    atoken = data["access_token"]
    status, data = api_request("GET", "/api/v1/auth/me", token=atoken)
    if status == 200:
        print(f"✓ Login auditor: OK - Roles: {', '.join(data['roles'])}")
    else:
        print(f"✗ Login auditor /me: FALLO - {status} {data}")
else:
    print(f"✗ Login auditor: FALLO - {status} {data}")

print("\n=== PRUEBAS COMPLETADAS ===")

# Detener servidor
proc.kill()
proc.wait()
print("Servidor detenido.")
