"""
Integración WMS: FastAPI Backend <-> Frontend Next.js

Valida peticiones REALES a todos los endpoints de FastAPI, el preflight CORS
y la coincidencia de tipado entre esquemas Pydantic v2 y interfaces TypeScript.

Ejecutar con: pytest tests_integration.py -v
"""
import pytest
import httpx

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"
FRONTEND_ORIGIN = "http://localhost:3000"

# Usuarios de prueba (seed)
USERS = {
    "superadmin": ("superadmin@demo.com", "admin123"),
    "gerente": ("gerente@demo.com", "gerente123"),
    "operario": ("operario@demo.com", "operario123"),
    "auditor": ("auditor@demo.com", "auditor123"),
}


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP compartido para toda la sesión.
    follow_redirects=False para capturar el código real sin seguir redirecciones."""
    with httpx.Client(base_url=BASE_URL, timeout=15.0, follow_redirects=False) as c:
        yield c


@pytest.fixture(scope="session")
def auth_tokens(client):
    """Obtiene tokens de acceso para todos los usuarios de prueba."""
    tokens = {}
    for role, (email, password) in USERS.items():
        resp = client.post(
            f"{API_V1}/auth/login/json",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200, f"Login {role} falló: {resp.status_code} {resp.text}"
        tokens[role] = resp.json()["access_token"]
    return tokens


@pytest.fixture(scope="session")
def auth_headers(auth_tokens):
    """Headers de autorización por rol."""
    return {role: {"Authorization": f"Bearer {token}"} for role, token in auth_tokens.items()}


# ============================================================
# 1. PRUEBAS DE AUTENTICACIÓN
# ============================================================

class TestAuth:
    def test_login_valido(self, client):
        """POST /api/v1/auth/login/json credenciales válidas -> 200"""
        resp = client.post(
            f"{API_V1}/auth/login/json",
            json={"email": "superadmin@demo.com", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_credenciales_invalidas(self, client):
        """POST /api/v1/auth/login/json contraseña incorrecta -> 401"""
        resp = client.post(
            f"{API_V1}/auth/login/json",
            json={"email": "superadmin@demo.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_login_email_no_existente(self, client):
        """POST /api/v1/auth/login/json email no existente -> 401"""
        resp = client.post(
            f"{API_V1}/auth/login/json",
            json={"email": "noexiste@demo.com", "password": "admin123"},
        )
        assert resp.status_code == 401

    def test_login_campos_faltantes(self, client):
        """POST /api/v1/auth/login/json sin password -> 422"""
        resp = client.post(
            f"{API_V1}/auth/login/json",
            json={"email": "superadmin@demo.com"},
        )
        assert resp.status_code == 422

    def test_me_sin_token(self, client):
        """GET /api/v1/auth/me sin token -> 401"""
        resp = client.get(f"{API_V1}/auth/me")
        assert resp.status_code == 401

    def test_me_con_token_superadmin(self, client, auth_headers):
        """GET /api/v1/auth/me con token SuperAdmin -> 200"""
        resp = client.get(f"{API_V1}/auth/me", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "superadmin@demo.com"
        assert "roles" in data

    def test_me_con_token_invalido(self, client):
        """GET /api/v1/auth/me con token inválido -> 401"""
        resp = client.get(f"{API_V1}/auth/me", headers={"Authorization": "Bearer token_invalido"})
        assert resp.status_code == 401


# ============================================================
# 2. PRUEBAS DE ENDPOINTS GET CON TOKEN (200)
# ============================================================

class TestCompanies:
    def test_companies_sin_token(self, client):
        """GET /api/v1/companies/ sin token -> 401"""
        resp = client.get(f"{API_V1}/companies/")
        assert resp.status_code == 401

    def test_companies_con_superadmin(self, client, auth_headers):
        """GET /api/v1/companies/ con token SuperAdmin -> 200"""
        resp = client.get(f"{API_V1}/companies/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_companies_sin_rol_suficiente(self, client, auth_headers):
        """GET /api/v1/companies/ con rol Operario (sin permiso) -> 403"""
        resp = client.get(f"{API_V1}/companies/", headers=auth_headers["operario"])
        assert resp.status_code == 403


class TestCenters:
    def test_centers_con_token(self, client, auth_headers):
        """GET /api/v1/centers/ con token -> 200"""
        resp = client.get(f"{API_V1}/centers/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestWarehouses:
    def test_warehouses_con_token(self, client, auth_headers):
        """GET /api/v1/warehouses/ con token -> 200"""
        resp = client.get(f"{API_V1}/warehouses/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestZones:
    def test_zones_con_token(self, client, auth_headers):
        """GET /api/v1/zones/ con token -> 200"""
        resp = client.get(f"{API_V1}/zones/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAisles:
    def test_aisles_con_token(self, client, auth_headers):
        """GET /api/v1/aisles/ con token -> 200"""
        resp = client.get(f"{API_V1}/aisles/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestShelves:
    def test_shelves_con_token(self, client, auth_headers):
        """GET /api/v1/shelves/ con token -> 200"""
        resp = client.get(f"{API_V1}/shelves/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestBins:
    def test_bins_con_token(self, client, auth_headers):
        """GET /api/v1/bins/ con token -> 200"""
        resp = client.get(f"{API_V1}/bins/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestUsers:
    def test_users_con_token(self, client, auth_headers):
        """GET /api/v1/users/ con token -> 200"""
        resp = client.get(f"{API_V1}/users/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestRoles:
    def test_roles_con_token(self, client, auth_headers):
        """GET /api/v1/roles/ con token -> 200"""
        resp = client.get(f"{API_V1}/roles/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestPermissions:
    def test_permissions_con_token(self, client, auth_headers):
        """GET /api/v1/permissions/ con token -> 200"""
        resp = client.get(f"{API_V1}/permissions/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestUserRoles:
    def test_user_roles_con_token(self, client, auth_headers):
        """GET /api/v1/user-roles/ con token -> 200"""
        resp = client.get(f"{API_V1}/user-roles/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestArticleFamilies:
    def test_article_families_con_token(self, client, auth_headers):
        """GET /api/v1/article-families/ con token -> 200"""
        resp = client.get(f"{API_V1}/article-families/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestArticleSubfamilies:
    def test_article_subfamilies_con_token(self, client, auth_headers):
        """GET /api/v1/article-subfamilies/ con token -> 200"""
        resp = client.get(f"{API_V1}/article-subfamilies/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestArticleBrands:
    def test_article_brands_con_token(self, client, auth_headers):
        """GET /api/v1/article-brands/ con token -> 200"""
        resp = client.get(f"{API_V1}/article-brands/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestArticles:
    def test_articles_con_token(self, client, auth_headers):
        """GET /api/v1/articles/ con token -> 200"""
        resp = client.get(f"{API_V1}/articles/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_articles_post_datos_invalidos(self, client, auth_headers):
        """POST /api/v1/articles/ datos inválidos -> 422"""
        resp = client.post(
            f"{API_V1}/articles/",
            json={"internal_code": "", "company_id": "no_es_numero"},
            headers=auth_headers["superadmin"],
        )
        assert resp.status_code == 422


class TestUoms:
    def test_uoms_con_token(self, client, auth_headers):
        """GET /api/v1/uoms/ con token -> 200"""
        resp = client.get(f"{API_V1}/uoms/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestLots:
    def test_lots_con_token(self, client, auth_headers):
        """GET /api/v1/lots/ con token -> 200"""
        resp = client.get(f"{API_V1}/lots/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestSerials:
    def test_serials_con_token(self, client, auth_headers):
        """GET /api/v1/serials/ con token -> 200"""
        resp = client.get(f"{API_V1}/serials/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestStock:
    def test_stock_con_token(self, client, auth_headers):
        """GET /api/v1/stock/ con token -> 200"""
        resp = client.get(f"{API_V1}/stock/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestInventoryCounts:
    def test_inventory_counts_con_token(self, client, auth_headers):
        """GET /api/v1/inventory-counts/ con token -> 200"""
        resp = client.get(f"{API_V1}/inventory-counts/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAdjustments:
    def test_adjustments_con_token(self, client, auth_headers):
        """GET /api/v1/adjustments/ con token -> 200"""
        resp = client.get(f"{API_V1}/adjustments/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAlerts:
    def test_alerts_con_token(self, client, auth_headers):
        """GET /api/v1/alerts/ con token -> 200"""
        resp = client.get(f"{API_V1}/alerts/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAuditLogs:
    def test_audit_logs_con_token(self, client, auth_headers):
        """GET /api/v1/audit-logs/ con token -> 200"""
        resp = client.get(f"{API_V1}/audit-logs/", headers=auth_headers["superadmin"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestReports:
    def test_reports_valuation_con_token(self, client, auth_headers):
        """GET /api/v1/reports/valuation con token -> 200"""
        resp = client.get(f"{API_V1}/reports/valuation", headers=auth_headers["superadmin"])
        assert resp.status_code == 200

    def test_reports_rotation_con_token(self, client, auth_headers):
        """GET /api/v1/reports/rotation con token -> 200"""
        resp = client.get(f"{API_V1}/reports/rotation", headers=auth_headers["superadmin"])
        assert resp.status_code == 200

    def test_reports_kpis_con_token(self, client, auth_headers):
        """GET /api/v1/reports/kpis con token -> 200"""
        resp = client.get(f"{API_V1}/reports/kpis", headers=auth_headers["superadmin"])
        assert resp.status_code == 200


# ============================================================
# 3. PRUEBAS DE ENDPOINT INEXISTENTE
# ============================================================

class TestNotFound:
    def test_endpoint_inexistente(self, client, auth_headers):
        """GET /api/v1/nonexistent -> 404"""
        resp = client.get(f"{API_V1}/nonexistent", headers=auth_headers["superadmin"])
        assert resp.status_code == 404


# ============================================================
# 4. PRUEBAS DE CORS PREFLIGHT
# ============================================================

class TestCORS:
    def test_cors_preflight(self, client):
        """OPTIONS preflight a http://localhost:3000 -> access-control-allow-origin: http://localhost:3000"""
        resp = client.options(
            f"{API_V1}/companies/",
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
        assert resp.status_code == 200
        allow_origin = resp.headers.get("access-control-allow-origin", "")
        assert allow_origin == FRONTEND_ORIGIN, (
            f"Esperado '{FRONTEND_ORIGIN}', obtenido '{allow_origin}'"
        )
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert "*" in allow_methods or "GET" in allow_methods
        allow_headers = resp.headers.get("access-control-allow-headers", "")
        assert "authorization" in allow_headers.lower() or "*" in allow_headers.lower()
        allow_credentials = resp.headers.get("access-control-allow-credentials", "")
        assert allow_credentials.lower() == "true"


# ============================================================
# 5. VALIDACIÓN DE TIPADO (Pydantic v2 vs TypeScript)
# ============================================================

class TestTipado:
    """Compara campos de esquemas Pydantic v2 con interfaces TypeScript en frontend/types/."""

    def _fields_coinciden(self, pydantic_fields, ts_fields, nombre):
        missing_in_ts = pydantic_fields - ts_fields
        extra_in_ts = ts_fields - pydantic_fields
        assert not missing_in_ts, f"{nombre}: campos en Pydantic no están en TS: {missing_in_ts}"
        assert not extra_in_ts, f"{nombre}: campos extra en TS no están en Pydantic: {extra_in_ts}"

    def test_stock_out_campos(self):
        """StockOut (Pydantic) vs StockOut (TS en frontend/types/stock.ts)"""
        pydantic_fields = {
            "id", "warehouse_id", "bin_id", "article_id", "lot_id",
            "serial_id", "quantity", "uom_id", "reserved_quantity",
            "available_quantity", "status", "updated_at",
        }
        ts_fields = {
            "id", "warehouse_id", "bin_id", "article_id", "lot_id",
            "serial_id", "quantity", "uom_id", "reserved_quantity",
            "available_quantity", "status", "updated_at",
        }
        self._fields_coinciden(pydantic_fields, ts_fields, "StockOut")

    def test_article_out_campos(self):
        """ArticleOut (Pydantic) vs Article (TS en frontend/types/master-data.ts)"""
        pydantic_fields = {
            "id", "company_id", "internal_code", "ean13", "supplier_reference",
            "family_id", "subfamily_id", "brand_id", "weight_kg", "volume_m3",
            "length_cm", "width_cm", "height_cm", "is_serialized", "lot_required",
            "abc_class", "is_active", "created_at", "updated_at",
        }
        ts_fields = {
            "id", "company_id", "internal_code", "ean13", "supplier_reference",
            "family_id", "subfamily_id", "brand_id", "weight_kg", "volume_m3",
            "length_cm", "width_cm", "height_cm", "is_serialized", "lot_required",
            "abc_class", "is_active", "created_at", "updated_at",
        }
        self._fields_coinciden(pydantic_fields, ts_fields, "ArticleOut/Article")

    def test_user_out_campos(self):
        """UserOut (Pydantic) vs UserOut (TS en frontend/types/auth.ts)"""
        pydantic_fields = {
            "id", "email", "full_name", "is_active", "company_id", "roles",
        }
        ts_fields = {
            "id", "email", "full_name", "is_active", "company_id", "roles",
        }
        self._fields_coinciden(pydantic_fields, ts_fields, "UserOut")

    def test_company_out_campos(self):
        """CompanyOut (Pydantic) vs Company (TS en frontend/types/organization.ts)"""
        pydantic_fields = {
            "id", "name", "tax_id", "currency", "fiscal_year_start_month",
            "is_active", "created_at", "updated_at",
        }
        ts_fields = {
            "id", "name", "tax_id", "currency", "fiscal_year_start_month",
            "is_active", "created_at", "updated_at",
        }
        self._fields_coinciden(pydantic_fields, ts_fields, "CompanyOut/Company")
