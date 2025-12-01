# Estado Actual del Proyecto

Este documento resume el estado funcional, las decisiones de diseño, los algoritmos empleados y los flujos principales del simulador de Sistema Operativo (SO). Está pensado como base para convertirlo posteriormente a un documento Word.

## Objetivos Principales
- Arquitectura exclusivamente Modular (Modular-only).
- Planificación por CPU con selección de algoritmo y multihilos.
- Simulación de interrupciones (timer, syscall, I/O, page fault) determinística.
- Gestión de memoria con múltiples unidades, particionado contiguo y memoria paginada.
- Reserva de memoria para el SO (bloque no expropiable, PID 0).
- Memoria virtual y traducción de direcciones.
- UI con vistas separadas de procesos y memoria; flujo entre capas limitado a últimos 10 eventos.

## Decisiones y Supuestos Clave
- Arquitectura: solo `Modular`. Se eliminaron ramas visuales y lógicas de Monolithic/Microkernel.
- Bloque SO: consumo base de `16 MB` más `2 MB` por proceso activo (READY/RUNNING/WAITING). Motivo: 16 MB cubre núcleo, tablas base y manejadores; 2 MB por proceso cubre estructuras de control (PCB extendido, tablas IPC, contadores, buffers).
- Memoria virtual: se asume un factor de extensión del 1.5× sobre la memoria física total para la capacidad virtual agregada en reportes.
- Tamaño de página: `4 MB` para simplicidad visual y cálculo (coherente con el PagedMemoryManager).
- Interrupciones determinísticas: probabilidades basadas en hash de `pid`, `tick` y `salt` para reproducibilidad.
- Flujo entre capas: se conserva solo el tail (últimos 10) para evitar saturación visual.

## Estructura de Carpetas
- `src/simulation/engine.py`: Núcleo de simulación (arquitectura Modular, CPUs, memoria, interrupciones, métricas).
- `src/os_core/`: Modelos (`models.py`), planificadores (`scheduler.py`), memoria (`memory/manager.py`, `strategies.py`), arquitecturas (`architectures.py`), interrupciones (`interrupts.py`).
- `src/frontend/`: UI PyQt6 (ventana principal, vistas de procesos y memoria, componentes).
- `documentacion/`: Documentos de referencia (este y complementarios).

## Módulos Principales
- Planificación: FCFS, SJF, SRTF, RR, Priority, PriorityRR (por CPU; quantum configurable en RR/PriorityRR).
- Memoria contigua: First Fit, Best Fit, Worst Fit; compactación automática basada en umbral de fragmentación.
- Memoria paginada: FIFO, LRU, Optimal; tablas por proceso y contadores de page faults/hits.
- Interrupciones: controlador central con tipos SYSCALL, IO, PAGE_FAULT, TIMER.
- Métricas: turnaround, waiting, utilización CPU global y ticks efectivos.

## Archivo Relevantes y Relaciones
- `engine.py` usa `models.py` (Process, CPU), `scheduler.py` (por CPU), `memory/manager.py` y `strategies.py` (por unidad), `interrupts.py` (controlador/Tipos), y reporta a UI.
- UI (`main_window.py`, `processes_view.py`, `memory_view.py`) consulta estado y ejecuta `tick()` del `engine` vía timer.

## Parámetros Configurables (actuales)
- CPUs: por defecto 4 con 2 hilos cada una.
- Algoritmos por CPU: seleccionables desde UI (bloqueados cuando corre).
- Memoria: múltiples unidades; capacidad por unidad (p.ej. 256 MB), estrategias de asignación y reemplazo de página por unidad.
- Quantum: visible y aplicable en RR/PriorityRR.

## Compatibilidad y Estabilidad
- El sistema evita retener CPUs con procesos en WAITING: se libera la CPU al entrar SYSCALL/IO/PAGE_FAULT.
- La compactación preserva siempre el bloque del SO al inicio y no reduce su tamaño.
- Tail de flujo entre capas recorta eventos a últimos 10.

## Próximos Ajustes Sugeridos
- Hacer configurables: base SO, per-proceso SO, tamaño de página, factor de memoria virtual.
- Añadir tests unitarios para RR/PriorityRR y compactación con bloque SO.
