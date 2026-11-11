# ADR-002 — Rate limiting en memoria con interfaz sustituible por Redis

**Estado:** Aceptada · **Fecha:** 11/11/2026

## Contexto

PROD-08 exige limitar intentos de autenticación. `slowapi` no estaba instalado
y añadir una dependencia no era imprescindible para una sola instancia.

## Decisión

Implementar `RateLimiter` en `app/core/ratelimit.py` con:

- ventana deslizante por `(bucket, IP)`;
- contador **solo de intentos fallidos** de login; los éxitos no consumen cuota;
- límites configurables (`LOGIN_RATE_LIMIT=10/60s`, `REFRESH_RATE_LIMIT=30/60s`);
- respuesta `429` con cabecera `Retry-After`.

La IP se toma de `X-Forwarded-For` **solo** si `TRUST_PROXY_HEADERS=true`.
Por defecto es `false`: si la API se expone directamente, la cabecera es
falsificable y permitiría saltarse el límite. Activar únicamente detrás de un
proxy propio que sobrescriba esa cabecera.

El punto de extensión es `RateLimiter.hit()`. Para varios workers o réplicas se
sustituye el diccionario por Redis manteniendo la misma firma.

## Consecuencias

- En despliegues multi-worker el límite es por proceso hasta migrar a Redis.
- Los tests usan `X-Forwarded-For` con IPs únicas para no contaminarse.
- `TestRateLimiting` verifica 401 → 429 y que un cliente limpio sigue pasando.
