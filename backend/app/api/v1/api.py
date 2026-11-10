from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.companies import router as companies_router
from app.api.v1.endpoints.centers import router as centers_router
from app.api.v1.endpoints.warehouses import router as warehouses_router
from app.api.v1.endpoints.zones import router as zones_router
from app.api.v1.endpoints.aisles import router as aisles_router
from app.api.v1.endpoints.shelves import router as shelves_router
from app.api.v1.endpoints.bins import router as bins_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.permissions import router as permissions_router
from app.api.v1.endpoints.user_roles import router as user_roles_router
from app.api.v1.endpoints.article_families import router as article_families_router
from app.api.v1.endpoints.article_subfamilies import router as article_subfamilies_router
from app.api.v1.endpoints.article_brands import router as article_brands_router
from app.api.v1.endpoints.articles import router as articles_router
from app.api.v1.endpoints.article_translations import router as article_translations_router
from app.api.v1.endpoints.uoms import router as uoms_router
from app.api.v1.endpoints.lots import router as lots_router
from app.api.v1.endpoints.serials import router as serials_router
from app.api.v1.endpoints.stock import router as stock_router
from app.api.v1.endpoints.inventory_counts import router as inventory_counts_router
from app.api.v1.endpoints.adjustments import router as adjustments_router
from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.audit_logs import router as audit_logs_router
from app.api.v1.endpoints.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(companies_router, prefix="/companies", tags=["companies"])
api_router.include_router(centers_router, prefix="/centers", tags=["centers"])
api_router.include_router(warehouses_router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(zones_router, prefix="/zones", tags=["zones"])
api_router.include_router(aisles_router, prefix="/aisles", tags=["aisles"])
api_router.include_router(shelves_router, prefix="/shelves", tags=["shelves"])
api_router.include_router(bins_router, prefix="/bins", tags=["bins"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(roles_router, prefix="/roles", tags=["roles"])
api_router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
api_router.include_router(user_roles_router, prefix="/user-roles", tags=["user-roles"])
api_router.include_router(article_families_router, prefix="/article-families", tags=["article-families"])
api_router.include_router(article_subfamilies_router, prefix="/article-subfamilies", tags=["article-subfamilies"])
api_router.include_router(article_brands_router, prefix="/article-brands", tags=["article-brands"])
api_router.include_router(articles_router, prefix="/articles", tags=["articles"])
api_router.include_router(article_translations_router, prefix="/articles", tags=["article-translations"])
api_router.include_router(uoms_router, prefix="/uoms", tags=["uoms"])
api_router.include_router(lots_router, prefix="/lots", tags=["lots"])
api_router.include_router(serials_router, prefix="/serials", tags=["serials"])
api_router.include_router(stock_router, prefix="/stock", tags=["stock"])
api_router.include_router(inventory_counts_router, prefix="/inventory-counts", tags=["inventory-counts"])
api_router.include_router(adjustments_router, prefix="/adjustments", tags=["adjustments"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])