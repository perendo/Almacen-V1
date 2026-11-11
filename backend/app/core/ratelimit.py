"""Rate limiting en memoria para endpoints de autenticación.

Suficiente para un despliegue de una sola instancia. Para varios workers o
réplicas, sustituir el almacén por Redis manteniendo esta interfaz
(``RateLimiter.hit``).
"""

import threading
import time
from typing import Dict, List, Tuple

from fastapi import HTTPException, Request, status

from app.core.config import settings


class RateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[Tuple[str, str], List[float]] = {}
        self._lock = threading.Lock()

    def _client_key(self, request: Request) -> str:
        if settings.TRUST_PROXY_HEADERS:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return getattr(getattr(request, "client", None), "host", None) or "unknown"

    def hit(self, request: Request, bucket: str, limit: int, window_seconds: int) -> None:
        """Registra un intento o lanza 429 si se supera el límite."""
        if not settings.RATE_LIMIT_ENABLED:
            return

        now = time.monotonic()
        key = (bucket, self._client_key(request))

        with self._lock:
            timestamps = [ts for ts in self._hits.get(key, []) if now - ts < window_seconds]
            if len(timestamps) >= limit:
                retry_after = max(1, int(window_seconds - (now - timestamps[0])))
                self._hits[key] = timestamps
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiados intentos. Inténtelo de nuevo más tarde.",
                    headers={"Retry-After": str(retry_after)},
                )
            timestamps.append(now)
            self._hits[key] = timestamps

    def reset(self) -> None:
        """Vacía el almacén (usado por las pruebas)."""
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()
