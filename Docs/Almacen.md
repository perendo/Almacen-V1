# Especificación Funcional: Módulo de Gestión de Almacén e Inventario (WMS)

## 1. Arquitectura Base y Control de Acceso

### 1.1. Multitenencia y Multiempresa
* **Aislamiento de Datos:** Estructura de base de datos con segregación lógica por empresa (`company_id`).
* **Configuración Independiente:** Moneda local, serie de documentos, ejercicios fiscales y plan contable independiente por cada empresa.
* **Consolidación de Inventario:** Vista global opcional para administradores para consultar stock consolidado entre diferentes empresas del grupo.

### 1.2. Multicentro y Multialmacén
* **Jerarquía Organizativa:** `Empresa` -> `Centro / Sucursal` -> `Almacén` -> `Zona` -> `Pasillo / Estantería / Hueco (Bin)`.
* **Tipología de Almacenes:**
  * Almacenes físicos de mercadería general.
  * Almacenes de mermas / productos defectuosos.
  * Almacenes en tránsito (para traspasos inter-centro).
  * Almacenes virtuales (depósito de clientes o consignación de proveedores).

### 1.3. Multiusuario y Roles (RBAC)
* **Gestión de Permisos:** Matriz de roles Granular por módulo y acción (Crear, Leer, Editar, Eliminar, Aprobar).
* **Roles Predefinidos:**
  * *SuperAdmin*: Acceso global multiempresa.
  * *Gerente de Almacén*: Gestión total de centros y aprobaciones de inventario.
  * *Operario de Almacén*: Operativa de recepción, picking, packing y recuento.
  * *Auditor*: Acceso en modo lectura a informes y trazabilidad.
* **Seguridad y Auditoría:** Registro exhaustivo de auditoría (*Audit Log*) registrando `usuario_id`, `timestamp`, `IP`, `acción` y `valores_previos/nuevos`.

---

## 2. Gestión de Maestros

### 2.1. Ficha Técnica de Artículo
* **Identificación:** Código interno, EAN-13/UPC, referencia del proveedor y descripción multilingüe.
* **Categorización:** Familia, subfamilia, marca y etiquetas personalizadas.
* **Unidades de Medida (UOM):** Unidad de compra, unidad de almacenamiento y unidad de venta con factores de conversión automáticos.
* **Parámetros Financieros:** Precios de coste (PMP, FIFO, Último precio), tarifas de venta y tipos de IVA/IGIC aplicables.
* **Control Físico:** Pesos, volúmenes (m³) y dimensiones para cálculo de cubicaje.

### 2.2. Trazabilidad Avanzada
* **Gestión de Lotes:** Número de lote obligatorio/opcional por familia, fecha de fabricación y fecha de caducidad / consumo preferente.
* **Números de Serie:** Seguimiento unitario de productos electrónicos o maquinaria desde la entrada hasta la venta.
* **Gestión de Ubicaciones (Bins):** Algoritmo de ubicación sugerida basado en rotación (ABC), volumen y compatibilidad de productos.

---

## 3. Operativa de Almacén (Flujos de Entrada y Salida)

### 3.1. Entradas y Recepciones (Inbound)
* **Recepciones contra Pedido de Compra:** Comprobación parcial o total del pedido de proveedor.
* **Control de Calidad (QC):** Bloqueo automático de lote recibido hasta aprobación de inspección visual/técnica.
* **Registro de Albarán de Entrada:** Generación automática de albarán de recepción e incremento de stock real.
* **Etiquetado:** Generación e impresión de etiquetas de código de barras/QR para bultos y ubicaciones en el momento del desembarque.

### 3.2. Salidas y Expedición (Outbound)
* **Reserva de Stock:** Descuento del stock disponible al confirmar pedido de cliente (distinguiendo entre *Stock Físico* y *Stock Disponible*).
* **Estrategias de Picking:**
  * *FIFO* (First In, First Out).
  * *FEFO* (First Expired, First Out - prioritario para perecederos).
  * Ordenación de ruta óptima de recogida dentro del almacén.
* **Packing y Consolidación:** Agrupación de items por caja/palé y preparación de documentación de transporte (*Packing List*).
* **Impresión de Documentos:** Albarán de entrega, etiquetas de envío para agencia de transportes.

### 3.3. Movimientos Internos
* **Traspasos Inter-Almacén:** Transferencia de mercancía entre diferentes centros con control de almacén de tránsito.
* **Reubicaciones Internas:** Movimiento manual o sugerido de artículos entre estanterías/pasillos.

---

## 4. Control de Inventario y Ajustes

### 4.1. Inventario Físico y Conteos
* **Inventarios Cíclicos:** Programación de recuentos periódicos por rotación ABC o zona.
* **Inventarios Generales:** Cierre temporal del almacén para recuento masivo de fin de ejercicio.
* **Gestión de Descuadres:** Registro de diferencias entre conteo físico y stock lógico con aprobación obligatoria por supervisores.

### 4.2. Ajustes y Regularizaciones
* **Bajas y Mermas:** Registro justificado de roturas, pérdidas, caducidad o deterioro.
* **Entradas/Salidas Extraordinarias:** Ajustes manuales motivados con imputación a cuentas de gasto/ingreso correspondientes.

---

## 5. Alertas y Reaprovisionamiento Inteligente

* **Punto de Pedido (Reorder Point):** Cálculo automático del nivel mínimo de stock para lanzar propuesta de compra.
* **Stock de Seguridad:** Reserva calculada para absorber desviaciones de demanda o retrasos de proveedores.
* **Gestión de Stock Máximo:** Control para evitar la sobresaturación de capacidad física en almacén.
* **Alertas Configurables:**
  * Alerta de lotes próximos a caducar.
  * Alerta de stock mínimo alcanzado.
  * Alerta de productos sin movimiento (Stock muerto / Obsoleto).

---

## 6. Informes y Cuadro de Mando (Analytics)

* **Valoración de Existencias:** Informe de valoración contable por PMP (Precio Medio Ponderado) y FIFO.
* **Rotación de Inventario:** Coeficiente de rotación por artículo, familia y almacén.
* **Trazabilidad Inversa y Directa:** Histórico completo de un número de serie o lote (dónde se compró, en qué ubicación estuvo y a qué cliente se vendió).
* **KPIs de Rendimiento:**
  * Exactitud de inventario (% de coincidencia en recuentos).
  * Tiempo medio de preparación de pedidos (*Order Cycle Time*).
  * Nivel de servicio de entregas (*OTIF - On Time In Full*).

---

## 7. Integraciones y API

* **Rest API / GraphQL:** Endpoints autenticados para integración con sistemas ERP externos, e-commerce (Shopify, WooCommerce) o terminales de radiofrecuencia (PDA / Barcode Scanners).
* **Exportación de Datos:** Descarga de informes y tablas en formatos estándar (CSV, Excel, PDF).