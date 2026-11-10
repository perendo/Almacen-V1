"""Verificacion rapida de permisos por rol contra la API en ejecucion."""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"

USERS = {
    "SuperAdmin": ("superadmin@demo.com", "admin123"),
    "Gerente": ("gerente@demo.com", "gerente123"),
    "Operario": ("operario@demo.com", "operario123"),
    "Auditor": ("auditor@demo.com", "auditor123"),
}

TESTS = [
    ("GET", "/stock", None),
    ("GET", "/companies", None),
    ("GET", "/centers", None),
    ("GET", "/users", None),
    ("GET", "/audit-logs", None),
    ("GET", "/reports/kpis", None),
    ("POST", "/stock/entry", {"article_id": 1, "warehouse_id": 1, "bin_id": 1, "quantity": 1, "uom_id": 1}),
]


def call(method, path, body, token=None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f"ERR:{e}"


tokens = {}
for role, (email, pwd) in USERS.items():
    st, _ = 0, None
    data = json.dumps({"email": email, "password": pwd}).encode()
    req = urllib.request.Request(
        BASE + "/auth/login/json", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        tokens[role] = json.loads(r.read())["access_token"]

print(f"{'endpoint':<28}" + "".join(f"{r:<12}" for r in USERS))
for method, path, body in TESTS:
    row = f"{method + ' ' + path:<28}"
    for role in USERS:
        row += f"{str(call(method, path, body, tokens[role])):<12}"
    print(row)
