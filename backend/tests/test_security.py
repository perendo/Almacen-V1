"""Suite de pruebas de seguridad y aislamiento del WMS.

Cubre los hallazgos de `auditoria.md` que no estaban verificados:

* SEC-01 — aislamiento multitenencia (lectura, escritura y borrado cruzados).
* SEC-02/SEC-03 — escalada de privilegios en usuarios/roles.
* PROD-08 — rate limiting en autenticación.
* CODE-02 — escritura real en ``audit_logs`` y su inmutabilidad vía API.
* DATA-03 — restricciones CHECK de stock.
* INTEG-01/INTEG-02 — contratos de ``/stock/movements`` y ``/stock/{article_id}``.
* QA-03 — rotación, reuso y revocación de refresh tokens.
* QA-05 — límites de paginación.
* QA-06 — informes reales y exportación.

Requiere el servidor levantado y la base de datos sembrada:

    cd backend
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    pytest tests_security.py -v

Las pruebas se ejecutan contra la API real (PostgreSQL), no contra mocks.
"""

from __future__ import annotations

import concurrent.futures
import os
import uuid

import httpx
import pytest

BASE_URL = os.getenv("WMS_BASE_URL", "http://127.0.0.1:8000")
API = f"{BASE_URL}/api/v1"

USERS = {
    "superadmin": ("superadmin@demo.com", "admin123"),
    "gerente": ("gerente@demo.com", "gerente123"),
    "operario": ("operario@demo.com", "operario123"),
    "auditor": ("auditor@demo.com", "auditor123"),
}

# Recursos con GET /{id} y su clave en el fixture de recursos de la empresa A.
READ_RESOURCES = [
    ("centers", "center"),
    ("warehouses", "warehouse"),
    ("zones", "zone"),
    ("aisles", "aisle"),
    ("shelves", "shelf"),
    ("bins", "bin"),
    ("articles", "article"),
    ("lots", "lot"),
    ("article-families", "family"),
]

# Recursos con PUT y DELETE.
WRITE_RESOURCES = [
    ("centers", "center"),
    ("warehouses", "warehouse"),
    ("zones", "zone"),
    ("aisles", "aisle"),
    ("shelves", "shelf"),
    ("bins", "bin"),
    ("articles", "article"),
]

# Listados que un usuario de la empresa B nunca debe ver con datos de A.
LIST_RESOURCES = [
    ("centers", "center"),
    ("warehouses", "warehouse"),
    ("zones", "zone"),
    ("aisles", "aisle"),
    ("shelves", "shelf"),
    ("bins", "bin"),
    ("articles", "article"),
    ("lots", "lot"),
    ("serials", "serial"),
    ("uoms", "uom"),
    ("article-families", "family"),
    ("article-brands", "brand"),
    ("stock", "stock"),
    ("stock/movements", "movement"),
    ("adjustments", "adjustment"),
    ("inventory-counts", "count"),
]


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _login(client: httpx.Client, email: str, password: str, ip: str | None = None) -> dict:
    extra = {"X-Forwarded-For": ip} if ip else {}
    response = client.post(
        f"{API}/auth/login/json",
        json={"email": email, "password": password},
        headers=extra,
    )
    assert response.status_code == 200, f"Login fallido para {email}: {response.text}"
    return response.json()


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0, follow_redirects=False) as c:
        yield c


@pytest.fixture(scope="session")
def tokens(client):
    return {role: _login(client, email, password) for role, (email, password) in USERS.items()}


@pytest.fixture(scope="session")
def auth(tokens):
    return {role: _headers(data["access_token"]) for role, data in tokens.items()}


@pytest.fixture(scope="session")
def company_a_id(client, auth):
    response = client.get(f"{API}/auth/me", headers=auth["superadmin"])
    assert response.status_code == 200
    return response.json()["company_id"]


@pytest.fixture(scope="session")
def tenant_b(client, auth):
    """Crea una segunda empresa con su propio gerente y la elimina al final."""
    suffix = uuid.uuid4().hex[:8]
    name = f"Tenant B Test {suffix}"
    email = f"gerente-{suffix}@example.com"

    company = client.post(
        f"{API}/companies/",
        json={"name": name, "currency": "EUR"},
        headers=auth["superadmin"],
    )
    assert company.status_code == 201, company.text
    company_id = company.json()["id"]

    roles = client.get(f"{API}/users/roles", headers=auth["superadmin"])
    assert roles.status_code == 200
    gerente_role = next(r for r in roles.json() if r["name"] == "Gerente de Almacén")

    user = client.post(
        f"{API}/users/",
        json={
            "email": email,
            "password": "tenant-b-pass-123",
            "full_name": "Gerente Tenant B",
            "company_id": company_id,
            "role_ids": [gerente_role["id"]],
        },
        headers=auth["superadmin"],
    )
    assert user.status_code == 201, user.text
    user_id = user.json()["id"]

    login = _login(client, email, "tenant-b-pass-123")
    data = {
        "company_id": company_id,
        "user_id": user_id,
        "email": email,
        "headers": _headers(login["access_token"]),
    }
    yield data

    client.delete(f"{API}/users/{user_id}", headers=auth["superadmin"])
    client.delete(f"{API}/companies/{company_id}", headers=auth["superadmin"])


@pytest.fixture(scope="session")
def resources_a(client, auth, company_a_id):
    """Recursos propios de la empresa A, creados por su gerente."""
    headers = auth["gerente"]
    suffix = uuid.uuid4().hex[:8].upper()

    def first(path: str) -> dict:
        response = client.get(f"{API}/{path}/", headers=headers)
        assert response.status_code == 200, f"{path}: {response.text}"
        assert response.json(), f"La empresa A no tiene datos sembrados en {path}"
        return response.json()[0]

    center = first("centers")
    warehouse = first("warehouses")
    zone = first("zones")
    aisle = first("aisles")
    shelf = first("shelves")
    bin_ = first("bins")
    uom = first("uoms")
    family = first("article-families")
    brand = first("article-brands")

    article = client.post(
        f"{API}/articles/",
        json={"internal_code": f"SEC-{suffix}", "ean13": None},
        headers=headers,
    )
    assert article.status_code == 201, article.text
    article = article.json()

    lot = client.post(
        f"{API}/lots/",
        json={"lot_number": f"LOT-{suffix}", "article_id": article["id"]},
        headers=headers,
    )
    assert lot.status_code == 201, lot.text
    lot = lot.json()

    serial = client.post(
        f"{API}/serials/",
        json={"serial_number": f"SN-{suffix}", "article_id": article["id"]},
        headers=headers,
    )
    assert serial.status_code == 201, serial.text
    serial = serial.json()

    adjustment = client.post(
        f"{API}/adjustments/",
        json={
            "warehouse_id": warehouse["id"],
            "adjustment_type": "shrinkage",
            "reason": "Prueba de aislamiento",
            "quantity": 1,
            "uom_id": uom["id"],
            "article_id": article["id"],
        },
        headers=headers,
    )
    assert adjustment.status_code == 201, adjustment.text
    adjustment = adjustment.json()

    count = client.post(
        f"{API}/inventory-counts/",
        json={"warehouse_id": warehouse["id"], "count_type": "cycle"},
        headers=headers,
    )
    assert count.status_code == 201, count.text
    count = count.json()

    entry = client.post(
        f"{API}/stock/entry",
        json={
            "warehouse_id": warehouse["id"],
            "bin_id": bin_["id"],
            "article_id": article["id"],
            "quantity": 10,
            "uom_id": uom["id"],
            "notes": "Entrada de prueba de seguridad",
        },
        headers=headers,
    )
    assert entry.status_code == 201, entry.text
    entry_body = entry.json()
    stock = entry_body["stock"]
    movement = entry_body["movement"]

    data = {
        "center": center,
        "warehouse": warehouse,
        "zone": zone,
        "aisle": aisle,
        "shelf": shelf,
        "bin": bin_,
        "uom": uom,
        "family": family,
        "brand": brand,
        "article": article,
        "lot": lot,
        "serial": serial,
        "adjustment": adjustment,
        "count": count,
        "stock": stock,
        "movement": movement,
    }

    yield data

    client.delete(f"{API}/articles/{article['id']}", headers=headers)


@pytest.fixture(scope="session")
def resources_b(client, tenant_b):
    """Recursos propios de la empresa B (para probar que el filtro devuelve solo B)."""
    headers = tenant_b["headers"]
    suffix = uuid.uuid4().hex[:8].upper()

    center = client.post(
        f"{API}/centers/",
        json={
            "name": f"Centro B {suffix}",
            "code": f"CB{suffix[:6]}",
            "company_id": tenant_b["company_id"],
        },
        headers=headers,
    )
    assert center.status_code == 201, center.text
    center = center.json()
    return {"center": center}


# ============================================================
# SEC-01 — Aislamiento multitenencia
# ============================================================


class TestTenantIsolation:
    @pytest.mark.parametrize("resource,key", READ_RESOURCES)
    def test_get_foreign_resource_returns_404(self, client, tenant_b, resources_a, resource, key):
        resource_id = resources_a[key]["id"]
        response = client.get(f"{API}/{resource}/{resource_id}", headers=tenant_b["headers"])
        assert response.status_code == 404, (
            f"FUGA: empresa B pudo leer {resource}/{resource_id} de la empresa A"
        )

    @pytest.mark.parametrize(
        "resource,key",
        WRITE_RESOURCES,
    )
    def test_update_foreign_resource_returns_404(self, client, tenant_b, resources_a, resource, key):
        resource_id = resources_a[key]["id"]
        valid_body = {
            "centers": {"name": "Intruso", "code": "INTR"},
            "warehouses": {"name": "Intruso", "code": "INTR"},
            "zones": {"name": "Intruso", "code": "INTR"},
            "aisles": {"name": "Intruso", "code": "INTR"},
            "shelves": {"name": "Intruso", "code": "INTR", "level": 1},
            "bins": {"code": "INTR"},
            "articles": {"internal_code": "INTRUSO"},
        }[resource]
        response = client.put(
            f"{API}/{resource}/{resource_id}",
            json=valid_body,
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404, (
            f"FUGA: empresa B pudo modificar {resource}/{resource_id} de la empresa A"
        )

    @pytest.mark.parametrize("resource,key", WRITE_RESOURCES)
    def test_delete_foreign_resource_returns_404(self, client, tenant_b, resources_a, resource, key):
        resource_id = resources_a[key]["id"]
        response = client.delete(f"{API}/{resource}/{resource_id}", headers=tenant_b["headers"])
        assert response.status_code == 404, (
            f"FUGA: empresa B pudo borrar {resource}/{resource_id} de la empresa A"
        )

    def test_update_foreign_lot_returns_404(self, client, tenant_b, resources_a):
        response = client.put(
            f"{API}/lots/{resources_a['lot']['id']}",
            json={"lot_number": "HACKED"},
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_read_foreign_article_translations_returns_404(self, client, tenant_b, resources_a):
        response = client.get(
            f"{API}/articles/{resources_a['article']['id']}/translations",
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.parametrize("resource,key", LIST_RESOURCES)
    def test_list_does_not_leak_foreign_rows(self, client, tenant_b, resources_a, resource, key):
        expected_id = resources_a[key]["id"]
        url = f"{API}/{resource}" if resource.endswith("movements") else f"{API}/{resource}/"
        response = client.get(url, headers=tenant_b["headers"])
        assert response.status_code == 200, response.text
        returned_ids = {row["id"] for row in response.json()}
        assert expected_id not in returned_ids, (
            f"FUGA: el listado {resource} de la empresa B contiene el id {expected_id} de A"
        )

    def test_company_a_list_only_contains_company_a(self, client, auth, resources_b):
        response = client.get(f"{API}/centers/", headers=auth["gerente"])
        assert response.status_code == 200
        ids = {row["id"] for row in response.json()}
        assert resources_b["center"]["id"] not in ids

    def test_company_b_list_only_contains_company_b(self, client, tenant_b, resources_b):
        response = client.get(f"{API}/centers/", headers=tenant_b["headers"])
        assert response.status_code == 200
        ids = {row["id"] for row in response.json()}
        assert ids == {resources_b["center"]["id"]}

    def test_superadmin_can_query_other_company_explicitly(self, client, auth, tenant_b, resources_b):
        response = client.get(
            f"{API}/centers/?company_id={tenant_b['company_id']}",
            headers=auth["superadmin"],
        )
        assert response.status_code == 200
        ids = {row["id"] for row in response.json()}
        assert ids == {resources_b["center"]["id"]}

    def test_non_superadmin_cannot_switch_company(self, client, auth, tenant_b, resources_b):
        """El company_id del cliente se ignora para roles que no son SuperAdmin."""
        response = client.get(
            f"{API}/centers/?company_id={tenant_b['company_id']}",
            headers=auth["gerente"],
        )
        assert response.status_code == 200
        ids = {row["id"] for row in response.json()}
        assert resources_b["center"]["id"] not in ids

    @pytest.mark.parametrize(
        "path,payload,parent_key",
        [
            ("warehouses", {"name": "WX", "code": "WX", "type": "general"}, "center_id"),
            ("zones", {"name": "ZX", "code": "ZX", "type": "storage"}, "warehouse_id"),
            ("aisles", {"name": "AX", "code": "AX"}, "zone_id"),
            ("shelves", {"name": "SX", "code": "SX", "level": 1}, "aisle_id"),
            ("bins", {"code": "BX"}, "shelf_id"),
        ],
    )
    def test_create_child_in_foreign_parent_returns_404(
        self, client, tenant_b, resources_a, path, payload, parent_key
    ):
        body = dict(payload)
        if path == "warehouses":
            body[parent_key] = resources_a["center"]["id"]
        elif path == "zones":
            body[parent_key] = resources_a["warehouse"]["id"]
        elif path == "aisles":
            body[parent_key] = resources_a["zone"]["id"]
        elif path == "shelves":
            body[parent_key] = resources_a["aisle"]["id"]
        else:
            body[parent_key] = resources_a["shelf"]["id"]

        response = client.post(f"{API}/{path}/", json=body, headers=tenant_b["headers"])
        assert response.status_code == 404, (
            f"FUGA: empresa B pudo crear {path} dentro de un padre de la empresa A"
        )

    def test_create_subfamily_in_foreign_family_returns_404(self, client, tenant_b, resources_a):
        response = client.post(
            f"{API}/article-subfamilies/",
            json={
                "family_id": resources_a["family"]["id"],
                "name": "Subfamilia intrusa",
                "code": "INTRUSA",
            },
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_create_lot_for_foreign_article_returns_404(self, client, tenant_b, resources_a):
        response = client.post(
            f"{API}/lots/",
            json={"lot_number": "LOT-INTRUSA", "article_id": resources_a["article"]["id"]},
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_create_serial_for_foreign_article_returns_404(self, client, tenant_b, resources_a):
        response = client.post(
            f"{API}/serials/",
            json={"serial_number": "SN-INTRUSA", "article_id": resources_a["article"]["id"]},
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_stock_entry_on_foreign_article_returns_404(self, client, tenant_b, resources_a):
        response = client.post(
            f"{API}/stock/entry",
            json={
                "warehouse_id": resources_a["warehouse"]["id"],
                "article_id": resources_a["article"]["id"],
                "quantity": 1,
                "uom_id": resources_a["uom"]["id"],
            },
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_stock_exit_on_foreign_article_returns_404(self, client, tenant_b, resources_a):
        response = client.post(
            f"{API}/stock/exit",
            json={
                "warehouse_id": resources_a["warehouse"]["id"],
                "article_id": resources_a["article"]["id"],
                "quantity": 1,
                "uom_id": resources_a["uom"]["id"],
            },
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_internal_transfer_from_foreign_warehouse_returns_404(
        self, client, tenant_b, resources_a
    ):
        response = client.post(
            f"{API}/stock/internal-transfer",
            json={
                "from_warehouse_id": resources_a["warehouse"]["id"],
                "to_warehouse_id": resources_a["warehouse"]["id"],
                "article_id": resources_a["article"]["id"],
                "quantity": 1,
                "uom_id": resources_a["uom"]["id"],
            },
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_adjustment_on_foreign_article_returns_404(self, client, tenant_b, resources_a):
        response = client.post(
            f"{API}/adjustments/",
            json={
                "warehouse_id": resources_a["warehouse"]["id"],
                "adjustment_type": "shrinkage",
                "reason": "intruso",
                "quantity": 1,
                "uom_id": resources_a["uom"]["id"],
                "article_id": resources_a["article"]["id"],
            },
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404

    def test_inventory_count_on_foreign_warehouse_returns_404(self, client, tenant_b, resources_a):
        response = client.post(
            f"{API}/inventory-counts/",
            json={"warehouse_id": resources_a["warehouse"]["id"], "count_type": "cycle"},
            headers=tenant_b["headers"],
        )
        assert response.status_code == 404


# ============================================================
# SEC-02 / SEC-03 — Privilegios
# ============================================================


class TestPrivileges:
    def test_manager_cannot_create_users(self, client, auth):
        response = client.post(
            f"{API}/users/",
            json={
                "email": "intruso@demo.com",
                "password": "intruso123",
                "full_name": "Intruso",
                "role_ids": [],
            },
            headers=auth["gerente"],
        )
        assert response.status_code == 403

    def test_manager_cannot_create_companies(self, client, auth):
        response = client.post(
            f"{API}/companies/", json={"name": "Empresa pirata"}, headers=auth["gerente"]
        )
        assert response.status_code == 403

    def test_manager_cannot_modify_superadmin(self, client, auth):
        response = client.put(
            f"{API}/users/1",
            json={"full_name": "Secuestrado"},
            headers=auth["gerente"],
        )
        assert response.status_code == 403

    def test_manager_cannot_assign_superadmin_role(self, client, auth):
        response = client.post(
            f"{API}/user-roles/",
            json={"user_id": 3, "role_id": 1, "company_id": 1},
            headers=auth["gerente"],
        )
        assert response.status_code == 403

    def test_operator_cannot_create_articles(self, client, auth):
        response = client.post(
            f"{API}/articles/",
            json={"internal_code": "OPERARIO-HACK"},
            headers=auth["operario"],
        )
        assert response.status_code == 403

    def test_operator_cannot_list_companies(self, client, auth):
        response = client.get(f"{API}/companies/", headers=auth["operario"])
        assert response.status_code == 403

    def test_auditor_cannot_create_articles(self, client, auth):
        response = client.post(
            f"{API}/articles/",
            json={"internal_code": "AUDITOR-HACK"},
            headers=auth["auditor"],
        )
        assert response.status_code == 403

    def test_auditor_cannot_read_audit_logs_of_other_company(
        self, client, auth, tenant_b
    ):
        response = client.get(
            f"{API}/audit-logs/?company_id={tenant_b['company_id']}",
            headers=auth["auditor"],
        )
        assert response.status_code == 200
        companies = {row["company_id"] for row in response.json()}
        assert tenant_b["company_id"] not in companies

    @pytest.mark.parametrize(
        "method,path",
        [
            ("get", "/users/"),
            ("get", "/articles/"),
            ("get", "/stock/"),
            ("get", "/audit-logs/"),
            ("post", "/stock/entry"),
        ],
    )
    def test_unauthenticated_requests_return_401(self, client, method, path):
        kwargs = {"json": {}} if method == "post" else {}
        response = getattr(client, method)(f"{API}{path}", **kwargs)
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        response = client.get(
            f"{API}/auth/me", headers={"Authorization": "Bearer token-invalido"}
        )
        assert response.status_code == 401


# ============================================================
# QA-03 — Refresh tokens
# ============================================================


class TestRefreshTokens:
    def test_refresh_rotation_and_reuse_detection(self, client):
        initial = _login(client, *USERS["operario"])
        first_refresh = initial["refresh_token"]

        rotated = client.post(f"{API}/auth/refresh", params={"refresh_token": first_refresh})
        assert rotated.status_code == 200, rotated.text
        second_refresh = rotated.json()["refresh_token"]
        assert second_refresh != first_refresh

        reused = client.post(f"{API}/auth/refresh", params={"refresh_token": first_refresh})
        assert reused.status_code == 401, "El refresh token reutilizado debe rechazarse"

        still_valid = client.post(f"{API}/auth/refresh", params={"refresh_token": second_refresh})
        assert still_valid.status_code == 200

    def test_logout_revokes_refresh_token(self, client):
        session = _login(client, *USERS["auditor"])
        headers = _headers(session["access_token"])

        logout = client.post(
            f"{API}/auth/logout",
            params={"refresh_token": session["refresh_token"]},
            headers=headers,
        )
        assert logout.status_code == 200, logout.text

        reused = client.post(
            f"{API}/auth/refresh", params={"refresh_token": session["refresh_token"]}
        )
        assert reused.status_code == 401, "El refresh token debe quedar revocado tras logout"

    def test_refresh_with_garbage_returns_401(self, client):
        response = client.post(f"{API}/auth/refresh", params={"refresh_token": "no-es-un-jwt"})
        assert response.status_code == 401

    def test_refresh_token_cannot_be_used_as_access_token(self, client):
        session = _login(client, *USERS["auditor"])
        response = client.get(
            f"{API}/auth/me",
            headers=_headers(session["refresh_token"]),
        )
        assert response.status_code == 401, "Un refresh token no debe autenticar la API"

    def test_access_token_is_revoked_on_logout(self, client):
        session = _login(client, *USERS["operario"])
        headers = _headers(session["access_token"])
        assert client.get(f"{API}/auth/me", headers=headers).status_code == 200

        logout = client.post(f"{API}/auth/logout", headers=headers)
        assert logout.status_code == 200

        after = client.get(f"{API}/auth/me", headers=headers)
        assert after.status_code == 401, "El access token debe quedar revocado tras logout"

    def test_refresh_accepts_json_body(self, client):
        """Contrato usado por el interceptor 401 del frontend Next.js."""
        initial = _login(client, *USERS["auditor"])
        rotated = client.post(
            f"{API}/auth/refresh", json={"refresh_token": initial["refresh_token"]}
        )
        assert rotated.status_code == 200, rotated.text
        assert rotated.json()["access_token"]

    def test_logout_accepts_json_body(self, client):
        """El frontend envía el refresh token en el cuerpo al cerrar sesión."""
        session = _login(client, *USERS["operario"])
        logout = client.post(
            f"{API}/auth/logout",
            json={"refresh_token": session["refresh_token"]},
            headers=_headers(session["access_token"]),
        )
        assert logout.status_code == 200, logout.text

        reused = client.post(
            f"{API}/auth/refresh", json={"refresh_token": session["refresh_token"]}
        )
        assert reused.status_code == 401


# ============================================================
# INTEG-01 / INTEG-02 — Contratos de stock
# ============================================================


class TestStockContracts:
    def test_movements_route_is_not_shadowed(self, client, auth):
        response = client.get(f"{API}/stock/movements", headers=auth["operario"])
        assert response.status_code == 200, response.text
        assert isinstance(response.json(), list)

    def test_stock_by_article_returns_list(self, client, auth, resources_a):
        response = client.get(
            f"{API}/stock/{resources_a['article']['id']}", headers=auth["operario"]
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert any(row["article_id"] == resources_a["article"]["id"] for row in body)

    def test_stock_by_unknown_article_returns_404(self, client, auth):
        response = client.get(f"{API}/stock/999999999", headers=auth["operario"])
        assert response.status_code == 404


# ============================================================
# QA-04 — Concurrencia y saldos
# ============================================================


class TestStockConcurrency:
    def test_concurrent_exits_cannot_overdraw_stock(self, client, auth, resources_a):
        article_id = resources_a["article"]["id"]
        warehouse_id = resources_a["warehouse"]["id"]
        bin_id = resources_a["bin"]["id"]
        uom_id = resources_a["uom"]["id"]

        stock_before = client.get(f"{API}/stock/{article_id}", headers=auth["gerente"]).json()
        current = max((float(row["quantity"]) for row in stock_before), default=0.0)

        # Garantizar al menos 2 unidades y dejar la fila en un estado conocido.
        if current < 2:
            entry = client.post(
                f"{API}/stock/entry",
                json={
                    "warehouse_id": warehouse_id,
                    "bin_id": bin_id,
                    "article_id": article_id,
                    "quantity": 2 - current,
                    "uom_id": uom_id,
                    "notes": "Reposición para prueba de concurrencia",
                },
                headers=auth["gerente"],
            )
            assert entry.status_code == 201, entry.text
            current = 2.0

        # Cada salida pide más de la mitad del stock: solo una puede prosperar.
        exit_quantity = int(current // 2) + 1

        def do_exit() -> int:
            with httpx.Client(base_url=BASE_URL, timeout=30.0, follow_redirects=False) as c:
                response = c.post(
                    f"{API}/stock/exit",
                    json={
                        "warehouse_id": warehouse_id,
                        "from_bin_id": bin_id,
                        "article_id": article_id,
                        "quantity": exit_quantity,
                        "uom_id": uom_id,
                        "notes": "Salida concurrente",
                    },
                    headers=auth["gerente"],
                )
                return response.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(lambda _: do_exit(), range(2)))

        assert sorted(statuses) == [201, 400], f"Debe prosperar solo una salida: {statuses}"

        stock_after = client.get(f"{API}/stock/{article_id}", headers=auth["gerente"]).json()
        quantities = [float(row["quantity"]) for row in stock_after]
        assert quantities and min(quantities) >= 0, "El stock nunca puede ser negativo"
        assert min(quantities) == current - exit_quantity

    def test_exit_over_available_returns_400(self, client, auth, resources_a):
        response = client.post(
            f"{API}/stock/exit",
            json={
                "warehouse_id": resources_a["warehouse"]["id"],
                "from_bin_id": resources_a["bin"]["id"],
                "article_id": resources_a["article"]["id"],
                "quantity": 10_000_000,
                "uom_id": resources_a["uom"]["id"],
            },
            headers=auth["gerente"],
        )
        assert response.status_code == 400
        assert "insuficiente" in response.json()["detail"].lower()

    def test_entry_creates_movement_and_audit(self, client, auth, resources_a):
        response = client.post(
            f"{API}/stock/entry",
            json={
                "warehouse_id": resources_a["warehouse"]["id"],
                "bin_id": resources_a["bin"]["id"],
                "article_id": resources_a["article"]["id"],
                "quantity": 1,
                "uom_id": resources_a["uom"]["id"],
            },
            headers=auth["gerente"],
        )
        assert response.status_code == 201

        movements = client.get(
            f"{API}/stock/movements", headers=auth["auditor"]
        )
        assert movements.status_code == 200
        assert any(
            row["article_id"] == resources_a["article"]["id"]
            for row in movements.json()
        )


# ============================================================
# CODE-02 — Auditoría activa
# ============================================================


class TestAudit:
    def test_mutations_write_audit_events(self, client, auth, resources_a):
        response = client.get(
            f"{API}/audit-logs/",
            params={"entity_type": "Article", "action": "create"},
            headers=auth["superadmin"],
        )
        assert response.status_code == 200
        entity_ids = {row["entity_id"] for row in response.json()}
        assert resources_a["article"]["id"] in entity_ids

    def test_login_writes_audit_event(self, client, auth):
        _login(client, *USERS["auditor"])
        response = client.get(
            f"{API}/audit-logs/",
            params={"action": "login", "limit": 50},
            headers=auth["superadmin"],
        )
        assert response.status_code == 200
        assert response.json(), "El login debe generar un evento de auditoría"

    def test_audit_payload_redacts_passwords(self, client, auth):
        response = client.get(
            f"{API}/audit-logs/",
            params={"entity_type": "User", "action": "create", "limit": 50},
            headers=auth["superadmin"],
        )
        assert response.status_code == 200
        for row in response.json():
            for field in ("old_values", "new_values"):
                assert "tenant-b-pass-123" not in (row.get(field) or "")

    def test_audit_logs_are_read_only(self, client, auth):
        assert client.post(f"{API}/audit-logs/", json={}, headers=auth["superadmin"]).status_code == 405
        # Sin rutas de mutación por ID: 404 o 405 son aceptables mientras no exista escritura.
        assert client.put(f"{API}/audit-logs/1", json={}, headers=auth["superadmin"]).status_code in (404, 405)
        assert client.delete(f"{API}/audit-logs/1", headers=auth["superadmin"]).status_code in (404, 405)

    def test_operator_cannot_read_audit_logs(self, client, auth):
        response = client.get(f"{API}/audit-logs/", headers=auth["operario"])
        assert response.status_code == 403


# ============================================================
# QA-05 — Paginación
# ============================================================


class TestPagination:
    @pytest.mark.parametrize(
        "params", [{"limit": 1001}, {"limit": 0}, {"skip": -1}, {"skip": "abc"}]
    )
    def test_invalid_pagination_is_rejected(self, client, auth, params):
        response = client.get(f"{API}/articles/", params=params, headers=auth["auditor"])
        assert response.status_code == 422

    def test_limit_respected(self, client, auth):
        response = client.get(f"{API}/articles/?limit=1", headers=auth["auditor"])
        assert response.status_code == 200
        assert len(response.json()) <= 1

    def test_audit_logs_pagination_limit(self, client, auth):
        response = client.get(f"{API}/audit-logs/?limit=5000", headers=auth["superadmin"])
        assert response.status_code == 422


# ============================================================
# QA-06 — Informes
# ============================================================


class TestReports:
    @pytest.mark.parametrize("path", ["valuation", "rotation", "kpis"])
    def test_reports_return_real_structure(self, client, auth, path):
        response = client.get(f"{API}/reports/{path}", headers=auth["auditor"])
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["report_type"] == path
        assert body.get("generated_at")

    def test_valuation_never_returns_fake_zero(self, client, auth, resources_a):
        response = client.get(f"{API}/reports/valuation", headers=auth["auditor"])
        assert response.status_code == 200
        body = response.json()
        # El fixture dio entrada al menos a 10 unidades del artículo de prueba.
        assert any(item["article_id"] == resources_a["article"]["id"] for item in body["items"])

    def test_export_csv(self, client, auth):
        response = client.get(
            f"{API}/reports/export", params={"report_type": "valuation"}, headers=auth["auditor"]
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "TOTAL" in response.text

    def test_unimplemented_export_returns_501(self, client, auth):
        response = client.get(
            f"{API}/reports/export", params={"report_type": "rotation"}, headers=auth["auditor"]
        )
        assert response.status_code == 501

    def test_operator_cannot_read_reports(self, client, auth):
        response = client.get(f"{API}/reports/kpis", headers=auth["operario"])
        assert response.status_code == 403

    @pytest.mark.parametrize("params", [{"days": 0}, {"days": 4000}])
    def test_rotation_rejects_invalid_windows(self, client, auth, params):
        response = client.get(f"{API}/reports/rotation", params=params, headers=auth["auditor"])
        assert response.status_code == 422


# ============================================================
# PROD-08 — Rate limiting
# ============================================================


class TestRateLimiting:
    def test_failed_logins_are_rate_limited(self, client):
        # IP única por ejecución: el limitador vive en memoria del servidor y
        # no debe contaminar ejecuciones sucesivas de la suite.
        ip = f"198.51.100.{uuid.uuid4().int % 250 + 2}"
        statuses = []
        for _ in range(15):
            response = client.post(
                f"{API}/auth/login/json",
                json={"email": "nadie@demo.com", "password": "wrongpass"},
                headers={"X-Forwarded-For": ip},
            )
            statuses.append(response.status_code)

        assert 401 in statuses
        assert 429 in statuses, f"El rate limiting no se activó: {statuses}"

    def test_rate_limit_is_per_client(self, client):
        response = client.post(
            f"{API}/auth/login/json",
            json={"email": USERS["gerente"][0], "password": USERS["gerente"][1]},
            headers={"X-Forwarded-For": "203.0.113.241"},
        )
        assert response.status_code == 200, "Un cliente limpio no debe estar bloqueado"


# ============================================================
# Hardening HTTP y legal
# ============================================================


class TestHardening:
    def test_security_headers(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Content-Security-Policy" in response.headers
        assert response.headers.get("X-Request-ID")

    def test_request_id_is_echoed(self, client):
        response = client.get("/health", headers={"X-Request-ID": "test-correlation-id"})
        assert response.headers["X-Request-ID"] == "test-correlation-id"

    def test_unknown_host_is_rejected(self, client):
        response = client.get("/health", headers={"Host": "atacante.example.com"})
        assert response.status_code == 400

    @pytest.mark.parametrize("path", ["/terminos", "/privacidad", "/aviso-legal"])
    def test_legal_endpoints(self, client, path):
        response = client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["version"]
        assert len(body["contenido"]) > 100
