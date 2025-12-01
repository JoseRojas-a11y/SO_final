# Referencias de Implementación y Valores Asumidos

## Valores Asumidos
- SO base: `16 MB` por unidad → núcleo, tablas de procesos, estructuras de interrupciones.
- SO por proceso: `2 MB` adicionales por proceso activo (READY/RUNNING/WAITING) → PCB extendido, colas IPC, buffers.
- Tamaño de página: `4 MB` → reducción de ruido visual y simple cálculo.
- Extensión virtual: `1.5×` memoria física → simplificación para reporte.
- Quantum por defecto: `4 ticks` en RR/PriorityRR.

## Ubicaciones en Código
- Reserva inicial del SO: `src/simulation/engine.py` (constructor de unidades y `reset`), `src/os_core/memory/manager.py` (constructor con `system_reserved_mb`).
- Expansión SO: `engine._update_system_reserved_memory` y `MemoryManager.expand_system_reserved`.
- Preservación en compactación: `MemoryManager.compact` (bloque PID 0 al inicio).
- Traducción virtual: `engine.translate_virtual_address` + `PagedMemoryManager.get_page_table`.
- Tail de flujo: `engine.log_layer_flow` (limita a 10).

## Relaciones Clave
- Engine ⇄ Schedulers: despacho por CPU, RR/PriorityRR usan quantum y colas internas.
- Engine ⇄ Memoria: contigua para asignación inicial; paginada para páginas; ambos por unidad.
- Engine ⇄ Interrupciones: generadas determinísticamente; liberan CPU al entrar WAITING.
- UI ⇄ Engine: `QTimer` invoca `tick`, refresca vistas.

## Métricas y Reportes
- `memory_unit_summaries`: agrega `system_reserved_mb`.
- `storage_overview`: agrega `virtual_total_mb` y `system_reserved_mb` global.
- `processes_view`: muestra estado por CPU y colas.
- `memory_view`: barras por unidad y tabla comparativa con SO.
