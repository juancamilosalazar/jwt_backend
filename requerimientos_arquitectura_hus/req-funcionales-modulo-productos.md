# Requerimientos Funcionales — Módulo de Ventas

**Proyecto:** Aplicación de Usuario  
**Stack:** Backend FastAPI  
**Versión:** 1.0  
**Fecha:** 2026-04-10  
**Estado:** Borrador  
**Dependencias:** Módulo de Productos (`req-funcionales-modulo-productos.md`)

---

## 1. Descripción General

El módulo de Ventas gestiona el proceso de compra de productos de tecnología por parte del usuario autenticado. Permite crear transacciones con múltiples productos (carrito), aplicar impuestos configurables por producto y gestionar el ciclo de vida de cada venta a través de sus estados.

---

## 2. Modelo de Datos

### 2.1 Entidad `Venta`

| Campo              | Tipo       | Requerido | Descripción                                          | Restricciones                              |
|--------------------|------------|-----------|------------------------------------------------------|--------------------------------------------|
| `id`               | `string`   | Sí        | Identificador único de la venta                      | Generado automáticamente (UUID v4), inmutable |
| `usuario_id`       | `string`   | Sí        | ID del usuario autenticado que realiza la compra     | Extraído del token JWT, no enviado por el cliente |
| `items`            | `array`    | Sí        | Lista de productos incluidos en la venta             | Al menos un ítem requerido                 |
| `subtotal`         | `float`    | Sí        | Suma de (`precio_unitario × cantidad`) por ítem      | Calculado por el servidor                  |
| `total_impuestos`  | `float`    | Sí        | Suma de impuestos aplicados sobre todos los ítems    | Calculado por el servidor                  |
| `total`            | `float`    | Sí        | `subtotal + total_impuestos`                         | Calculado por el servidor                  |
| `estado`           | `string`   | Sí        | Estado actual de la venta                            | Enum: `pendiente`, `confirmada`, `cancelada` |
| `fecha_creacion`   | `datetime` | Sí        | Fecha y hora de creación de la venta                 | Generada por el servidor (UTC)             |
| `fecha_actualizacion` | `datetime` | Sí     | Fecha y hora de la última modificación               | Actualizada automáticamente por el servidor |

### 2.2 Entidad `ItemVenta` (línea de producto dentro de una venta)

| Campo             | Tipo      | Requerido | Descripción                                              | Restricciones                              |
|-------------------|-----------|-----------|----------------------------------------------------------|--------------------------------------------|
| `id`              | `string`  | Sí        | Identificador único del ítem                             | Generado automáticamente (UUID v4)         |
| `producto_id`     | `string`  | Sí        | ID del producto referenciado del módulo de Productos     | Debe existir en el catálogo                |
| `cantidad`        | `integer` | Sí        | Unidades del producto a comprar                          | Mayor o igual a 1                          |
| `precio_unitario` | `float`   | Sí        | Precio del producto en el momento de la venta            | Capturado desde el catálogo al crear la venta |
| `impuesto_pct`    | `float`   | Sí        | Porcentaje de impuesto aplicable al producto             | Entre 0 y 100, configurable por producto   |
| `impuesto_valor`  | `float`   | Sí        | Valor monetario del impuesto (`precio_unitario × cantidad × impuesto_pct / 100`) | Calculado por el servidor |
| `subtotal_item`   | `float`   | Sí        | Total del ítem sin impuesto (`precio_unitario × cantidad`) | Calculado por el servidor               |
| `total_item`      | `float`   | Sí        | Total del ítem con impuesto (`subtotal_item + impuesto_valor`) | Calculado por el servidor            |

---

## 3. Ciclo de Vida de una Venta

```
[Creación] → PENDIENTE → CONFIRMADA
                      ↘ CANCELADA
     PENDIENTE → CANCELADA
```

| Transición                       | Endpoint responsable         | Descripción                                      |
|----------------------------------|------------------------------|--------------------------------------------------|
| Nueva venta → `pendiente`        | `POST /sales`                | Estado inicial al crear la venta                 |
| `pendiente` → `confirmada`       | `PATCH /sales/{id}/confirm`  | El usuario confirma la compra                    |
| `pendiente` → `cancelada`        | `PATCH /sales/{id}/cancel`   | El usuario cancela antes de confirmar            |
| `confirmada` → `cancelada`       | No permitido                 | Una venta confirmada no puede cancelarse         |

---

## 4. Requerimientos Funcionales

### RF-001 — Crear Venta (Carrito)

**Descripción:** El sistema debe permitir al usuario autenticado iniciar una venta enviando una lista de productos con sus cantidades.

**Endpoint:** `POST /sales`

**Cuerpo de la solicitud:**
```json
{
  "items": [
    {
      "producto_id": "uuid-del-producto",
      "cantidad": 2
    }
  ]
}
```

**Comportamiento esperado:**
- El sistema consulta el catálogo de Productos para obtener `precio_unitario` e `impuesto_pct` de cada ítem enviado.
- El sistema valida que cada `producto_id` exista y que el `stock_disponible` sea suficiente para la `cantidad` solicitada.
- El sistema calcula automáticamente `impuesto_valor`, `subtotal_item`, `total_item` por ítem, y `subtotal`, `total_impuestos` y `total` a nivel de venta.
- El `usuario_id` se extrae del token JWT; el cliente no lo envía.
- La venta se crea con estado inicial `pendiente`.
- Retorna el objeto `Venta` completo con código `201 Created`.

**Criterios de aceptación:**
- [ ] Se debe enviar al menos un ítem para crear la venta.
- [ ] Si algún `producto_id` no existe, el sistema retorna `404 Not Found` indicando qué producto no fue encontrado.
- [ ] Si el stock de algún producto es insuficiente, el sistema retorna `422 Unprocessable Entity` con detalle del producto afectado.
- [ ] El `precio_unitario` e `impuesto_pct` son capturados del catálogo en el momento de la creación y no cambian aunque el producto se actualice después.
- [ ] El stock del producto **no** se descuenta al crear la venta en estado `pendiente`; se descuenta al confirmar.
- [ ] El endpoint requiere autenticación; sin token válido responde `401 Unauthorized`.

---

### RF-002 — Listar Ventas del Usuario

**Descripción:** El sistema debe permitir al usuario autenticado consultar el historial de sus propias ventas.

**Endpoint:** `GET /sales`

**Comportamiento esperado:**
- Retorna únicamente las ventas asociadas al `usuario_id` extraído del token JWT.
- Soporta filtro opcional por `estado` (`pendiente`, `confirmada`, `cancelada`).
- Soporta parámetros opcionales de paginación: `page` (default: 1) y `limit` (default: 20, máximo: 100).
- Retorna `200 OK` con un arreglo de ventas (puede ser vacío `[]`).

**Criterios de aceptación:**
- [ ] El usuario solo puede ver sus propias ventas; no accede a ventas de otros usuarios.
- [ ] El filtro por estado es opcional; sin él se retornan todas las ventas del usuario.
- [ ] Cada objeto venta en el listado incluye el resumen de ítems, totales y estado.
- [ ] El endpoint requiere autenticación; sin token válido responde `401 Unauthorized`.

---

### RF-003 — Obtener Detalle de Venta por ID

**Descripción:** El sistema debe permitir al usuario autenticado consultar el detalle completo de una venta específica.

**Endpoint:** `GET /sales/{id}`

**Comportamiento esperado:**
- Retorna el objeto `Venta` completo con todos sus ítems y totales calculados con código `200 OK`.
- Si el `id` no existe, retorna `404 Not Found`.
- Si la venta existe pero pertenece a otro usuario, retorna `403 Forbidden`.

**Criterios de aceptación:**
- [ ] La respuesta incluye todos los campos de `Venta` e `ItemVenta`.
- [ ] Un usuario no puede consultar las ventas de otro usuario.
- [ ] El endpoint requiere autenticación; sin token válido responde `401 Unauthorized`.

---

### RF-004 — Confirmar Venta

**Descripción:** El sistema debe permitir al usuario autenticado confirmar una venta en estado `pendiente`, formalizando la compra.

**Endpoint:** `PATCH /sales/{id}/confirm`

**Comportamiento esperado:**
- Cambia el estado de la venta de `pendiente` a `confirmada`.
- El sistema descuenta el `stock_disponible` de cada producto según las cantidades de los ítems.
- Actualiza `fecha_actualizacion` al momento de la confirmación.
- Retorna el objeto `Venta` actualizado con código `200 OK`.
- Si la venta no está en estado `pendiente`, retorna `409 Conflict` con mensaje descriptivo.
- Si al confirmar el stock es insuficiente para algún producto, retorna `422 Unprocessable Entity`.

**Criterios de aceptación:**
- [ ] Solo las ventas en estado `pendiente` pueden confirmarse.
- [ ] El stock de cada producto se reduce exactamente en la `cantidad` de su ítem correspondiente.
- [ ] Si el stock es insuficiente al confirmar, no se aplica ningún descuento parcial (operación atómica).
- [ ] Solo el dueño de la venta puede confirmarla.
- [ ] El endpoint requiere autenticación; sin token válido responde `401 Unauthorized`.

---

### RF-005 — Cancelar Venta

**Descripción:** El sistema debe permitir al usuario autenticado cancelar una venta en estado `pendiente`.

**Endpoint:** `PATCH /sales/{id}/cancel`

**Comportamiento esperado:**
- Cambia el estado de la venta de `pendiente` a `cancelada`.
- Actualiza `fecha_actualizacion` al momento de la cancelación.
- Retorna el objeto `Venta` actualizado con código `200 OK`.
- Si la venta está en estado `confirmada`, retorna `409 Conflict` indicando que no es posible cancelar una venta ya confirmada.

**Criterios de aceptación:**
- [ ] Solo las ventas en estado `pendiente` pueden cancelarse.
- [ ] Una venta `confirmada` no puede ser cancelada bajo ninguna circunstancia.
- [ ] Solo el dueño de la venta puede cancelarla.
- [ ] El endpoint requiere autenticación; sin token válido responde `401 Unauthorized`.

---

### RF-006 — Eliminar Venta

**Descripción:** El sistema debe permitir al usuario autenticado eliminar permanentemente una venta en estado `cancelada`.

**Endpoint:** `DELETE /sales/{id}`

**Comportamiento esperado:**
- Elimina la venta y todos sus ítems asociados de forma permanente.
- Retorna `204 No Content` si la eliminación es exitosa.
- Solo permite eliminar ventas en estado `cancelada`.
- Si la venta está en estado `pendiente` o `confirmada`, retorna `409 Conflict`.

**Criterios de aceptación:**
- [ ] Solo las ventas en estado `cancelada` pueden eliminarse.
- [ ] Al eliminar la venta se eliminan también todos sus `ItemVenta` asociados.
- [ ] Solo el dueño de la venta puede eliminarla.
- [ ] El endpoint requiere autenticación; sin token válido responde `401 Unauthorized`.

---

## 5. Resumen de Endpoints

| Método   | Ruta                       | Descripción                              | Código éxito |
|----------|----------------------------|------------------------------------------|--------------|
| `POST`   | `/sales`                   | Crear nueva venta (carrito)              | `201`        |
| `GET`    | `/sales`                   | Listar ventas del usuario autenticado    | `200`        |
| `GET`    | `/sales/{id}`              | Obtener detalle de una venta             | `200`        |
| `PATCH`  | `/sales/{id}/confirm`      | Confirmar venta (pendiente → confirmada) | `200`        |
| `PATCH`  | `/sales/{id}/cancel`       | Cancelar venta (pendiente → cancelada)   | `200`        |
| `DELETE` | `/sales/{id}`              | Eliminar venta cancelada                 | `204`        |

---

## 6. Reglas de Negocio Transversales

- Todos los endpoints requieren Bearer Token / JWT válido.
- El `usuario_id` siempre se extrae del token; el cliente nunca lo envía en el cuerpo.
- El `precio_unitario` e `impuesto_pct` se capturan del catálogo al momento de crear la venta y son inmutables en el historial.
- El descuento de stock ocurre **únicamente** al confirmar la venta, no al crearla.
- Todas las operaciones de cálculo (subtotales, impuestos, totales) son responsabilidad del servidor.
- Un usuario solo puede operar sobre sus propias ventas.

---

## 7. Códigos de Respuesta HTTP

| Código | Situación                                              |
|--------|--------------------------------------------------------|
| `200`  | Operación exitosa (lectura, confirmación, cancelación) |
| `201`  | Venta creada exitosamente                              |
| `204`  | Venta eliminada exitosamente                           |
| `401`  | Usuario no autenticado                                 |
| `403`  | El usuario no es dueño del recurso                     |
| `404`  | Recurso no encontrado                                  |
| `409`  | Conflicto de estado (transición no permitida)          |
| `422`  | Error de validación en los datos enviados              |

---

*Documento generado por Arquitectura de Software — Módulo Ventas v1.0*
