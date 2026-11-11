# ADR-003 — Licencia MIT con doble licenciamiento comercial

**Estado:** Aceptada · **Fecha:** 11/11/2026

## Contexto

El proyecto es una herramienta WMS que puede usarse en entornos regulados
(GxP, trazabilidad alimentaria, RGPD). Se quiere adoptar ampliamente sin
prometer cumplimiento normativo automático.

## Decisión

- Código bajo **MIT** (`LICENSE`), sin garantías.
- Módulos de cumplimiento y soporte ofrecidos bajo **licencia comercial**
  separada.
- Documentos legales: `TERMS.md`, `DISCLAIMER.md`, política de privacidad y
  aviso legal publicados también en la UI (`/terminos`, `/privacidad`,
  `/aviso-legal`).
- Posicionamiento explícito: “herramienta; el cliente valida y cumple
  GxP/RGPD”. La organización usuaria es la responsable del tratamiento.

## Consecuencias

- El usuario acepta que el software se entrega “tal cual”.
- El cliente asume copias de seguridad, validación y cumplimiento sectorial.
- Jurisdicción: España / Unión Europea (RGPD + LOPDGDD).
