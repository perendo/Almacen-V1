# ADR-001 — Auditoría explícita en cada mutación

**Estado:** Aceptada · **Fecha:** 11/11/2026

## Contexto

`auditoria.md` (CODE-02) detectó que la tabla `audit_logs` existía pero ningún
endpoint escribía en ella. Un middleware transversal no puede conocer el diff
de la entidad ni el usuario de forma fiable.

## Decisión

Toda mutación crítica llama a `log_audit_event()` (`app/core/audit.py`) **antes**
del `db.commit()`, de forma que mutación y evento son atómicos. El helper:

- redacta campos sensibles (`password`, `token`, `secret`, `jti`);
- serializa fechas a ISO-8601;
- toma la IP de `X-Forwarded-For` o del cliente;
- no hace commit por sí mismo.

La API de auditoría es de solo lectura (`GET /audit-logs`); `POST/PUT/DELETE`
responden 405/404.

## Consecuencias

- Cada endpoint nuevo debe instrumentarse explícitamente (checklist en PR).
- El audit trail crece con cada operación; se aplica retención configurable
  (`AUDIT_RETENTION_DAYS`, 5 años por defecto).
- Tests: `TestAudit` verifica creación, login y redacción de contraseñas.
