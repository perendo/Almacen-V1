# ADR-004 — Aislamiento multitenencia centralizado

**Estado:** Aceptada · **Fecha:** 11/11/2026

## Contexto

SEC-01 solo estaba corregido en 4 módulos. Repetir el filtro `company_id` en
cada endpoint provocaba omisiones y código divergente.

## Decisión

Un único módulo `app/core/tenancy.py`:

- `scope_query()` aplica la empresa del usuario o la solicitada por SuperAdmin;
- para modelos sin `company_id` usa una cadena declarativa de joins
  (`_SCOPE_JOINS`);
- `tenant_get()` devuelve **404** si el recurso no existe o es de otra empresa;
- `ensure_parent_in_tenant()` valida el padre en altas jerárquicas.

Regla de revisión: si un endpoint filtra `company_id` a mano, se rechaza el PR.

## Consecuencias

- 17 módulos corregidos además de los 4 originales.
- Nuevos modelos deben declarar su entrada en `_SCOPE_JOINS` o tener
  `company_id` propio.
- `tests_security.py` cubre la matriz completa con dos empresas reales.
