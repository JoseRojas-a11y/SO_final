# 04 --- Gestión Avanzada de Memoria

## 1. Introducción

La gestión de memoria es uno de los componentes más críticos de un Sistema Operativo. Este documento describe las implementaciones avanzadas de gestión de memoria en el simulador, incluyendo autocompactación y sistemas de paginación con algoritmos de reemplazo.

## 2. Autocompactación de Memoria

### 2.1 Concepto

La **autocompactación** es un mecanismo que reorganiza automáticamente la memoria física para reducir la fragmentación externa. Consiste en mover todos los bloques de memoria asignados hacia el inicio del espacio de memoria, dejando todo el espacio libre contiguo al final.

### 2.2 Implementación

El simulador implementa autocompactación en el `MemoryManager` con las siguientes características:

- **Activación automática:** se ejecuta cuando la fragmentación supera un umbral configurable (por defecto 30%).
- **Compactación periódica:** se realiza cada N ticks (por defecto 50) si hay fragmentación significativa (>10%).
- **Compactación tras liberación:** después de liberar memoria de un proceso, se verifica si es necesario compactar.

### 2.3 Parámetros Configurables

- `auto_compact`: activar/desactivar la autocompactación (por defecto: `True`).
- `compact_threshold`: umbral de fragmentación para activar compactación (0.0-1.0, por defecto: 0.3).
- `compact_interval`: intervalo en ticks para compactación periódica (por defecto: 50).

### 2.4 Algoritmo de Compactación

1. Identificar todos los bloques de memoria asignados.
2. Reorganizar los bloques moviéndolos al inicio del espacio de memoria.
3. Consolidar todo el espacio libre en un único bloque al final.
4. Actualizar las referencias de los procesos a sus nuevos bloques.

### 2.5 Beneficios

- Reduce la fragmentación externa.
- Mejora la eficiencia de asignación de memoria.
- Permite asignar procesos que de otra forma no cabrían debido a fragmentación.

## 3. Sistema de Paginación

### 3.1 Concepto

La **paginación** es una técnica de gestión de memoria que divide la memoria física en frames de tamaño fijo y la memoria lógica de los procesos en páginas del mismo tamaño. Elimina la fragmentación externa y permite una gestión más eficiente de la memoria.

### 3.2 Componentes del Sistema

#### 3.2.1 Página (Page)

Representa un frame físico de memoria con:
- Número de frame físico.
- Proceso que lo ocupa (PID).
- Número de página lógica del proceso.
- Información de acceso: último acceso, tick de carga, bits de referencia y modificación.

#### 3.2.2 Tabla de Páginas (Page Table)

Cada proceso tiene su propia tabla de páginas que mapea:
- Páginas lógicas → Frames físicos.
- Bits de validez (presente en memoria física).
- Información de acceso y modificación.

### 3.3 Algoritmos de Reemplazo

El simulador implementa tres algoritmos de reemplazo de páginas que se ejecutan en paralelo para comparar su rendimiento:

#### 3.3.1 FIFO (First In First Out)

- Reemplaza la página que ha estado en memoria por más tiempo.
- Implementado mediante una cola que mantiene el orden de carga.
- Simple pero puede tener problemas con el fenómeno de Belady.

#### 3.3.2 LRU (Least Recently Used)

- Reemplaza la página que no ha sido accedida por más tiempo.
- Mantiene un registro del último acceso a cada página.
- Mejor rendimiento que FIFO en la mayoría de casos.

#### 3.3.3 Optimal (Óptimo)

- Heurística que intenta aproximar el algoritmo óptimo teórico.
- Selecciona la página que se usará más tarde (o la que no se ha usado recientemente).
- En la práctica, requiere conocimiento del futuro, por lo que se usa una aproximación basada en tiempo desde último acceso.

### 3.4 Page Faults

Un **page fault** ocurre cuando un proceso intenta acceder a una página que no está en memoria física. El sistema debe:

1. Detectar el page fault.
2. Si hay frames libres, cargar la página.
3. Si no hay frames libres, seleccionar una víctima usando el algoritmo de reemplazo.
4. Cargar la página solicitada en el frame seleccionado.
5. Actualizar la tabla de páginas del proceso.

### 3.5 Estadísticas de Paginación

El simulador registra las siguientes métricas para cada algoritmo:

- **Total de Page Faults:** número de fallos de página ocurridos.
- **Total de Page Hits:** número de accesos exitosos a páginas en memoria.
- **Tasa de Page Faults:** porcentaje de accesos que resultan en page fault.
- **Utilización de Memoria:** porcentaje de frames físicos utilizados.

### 3.6 Configuración

- **Tamaño de página:** 4 MB por defecto.
- **Memoria total:** configurable al inicializar el simulador (por defecto 256 MB).
- **Número de frames:** calculado como `total_mb / page_size_mb`.

## 4. Integración en el Simulador

### 4.1 Gestores de Memoria

El simulador mantiene dos tipos de gestores de memoria en paralelo:

1. **Gestores de bloques:** First Fit, Best Fit, Worst Fit (gestión contigua).
2. **Gestores paginados:** FIFO, LRU, Optimal (gestión paginada).

Cada proceso se asigna en ambos sistemas para permitir comparación de rendimiento.

### 4.2 Simulación de Accesos

Durante la ejecución, los procesos acceden aleatoriamente a sus páginas (10% de probabilidad por tick), lo que genera:

- Page hits cuando la página está en memoria.
- Page faults cuando es necesario cargar o reemplazar páginas.

### 4.3 Visualización

La interfaz gráfica muestra:

- **Barras de memoria:** visualización de bloques asignados y libres (gestión contigua).
- **Tabla de estadísticas de paginación:** métricas de los tres algoritmos de reemplazo.
- **Comparativa:** permite evaluar el rendimiento de cada algoritmo.

## 5. Ventajas y Desventajas

### 5.1 Autocompactación

**Ventajas:**
- Elimina fragmentación externa.
- Mejora la eficiencia de asignación.
- Automática, sin intervención del usuario.

**Desventajas:**
- Overhead computacional al reorganizar memoria.
- Puede causar latencia si se ejecuta frecuentemente.

### 5.2 Paginación

**Ventajas:**
- Elimina fragmentación externa.
- Permite gestión eficiente de memoria virtual.
- Facilita el intercambio de procesos.

**Desventajas:**
- Overhead de las tablas de páginas.
- Posibles page faults que ralentizan la ejecución.
- Complejidad adicional en la gestión.

## 6. Implementación en el código

### 6.1 Estructura de archivos

```
src/simulation/
├── models.py                    # Modelos de datos: Page, PageTableEntry
├── memory/
│   └── manager.py              # MemoryManager, PagedMemoryManager
└── engine.py                    # Integración y uso de gestores
```

### 6.2 Clases principales

#### 6.2.1 Modelos de datos (`src/simulation/models.py`)

**`Page`** (dataclass)
- Representa un frame físico de memoria.
- Atributos:
  - `frame_number: int` - Número de frame físico
  - `process_pid: Optional[int]` - Proceso que ocupa el frame
  - `page_number: Optional[int]` - Número de página lógica
  - `last_accessed: int` - Tick de último acceso (para LRU)
  - `loaded_tick: int` - Tick cuando se cargó (para FIFO)
  - `referenced: bool` - Bit de referencia
  - `modified: bool` - Bit de modificación
- Propiedades:
  - `free: bool` - Indica si el frame está libre

**`PageTableEntry`** (dataclass)
- Representa una entrada en la tabla de páginas de un proceso.
- Atributos:
  - `page_number: int` - Número de página lógica
  - `frame_number: Optional[int]` - Frame físico asignado
  - `valid: bool` - Bit válido (presente en memoria)
  - `referenced: bool` - Bit de referencia
  - `modified: bool` - Bit de modificación
  - `loaded_tick: int` - Tick cuando se cargó
  - `last_accessed: int` - Tick de último acceso

#### 6.2.2 MemoryManager (`src/simulation/memory/manager.py`)

**`MemoryManager`** (clase)
- Gestor de memoria contigua con autocompactación.

**Métodos principales:**
- `__init__(total_mb, algorithm_name, strategy, auto_compact=True, compact_threshold=0.3)`
  - Inicializa el gestor con parámetros de autocompactación.
- `allocate(process: Process) -> AllocationResult`
  - Asigna memoria a un proceso usando la estrategia especificada.
- `release(process: Process)`
  - Libera memoria de un proceso y verifica autocompactación.
- `compact()`
  - Compacta memoria moviendo bloques asignados al inicio.
- `check_and_compact() -> bool`
  - Verifica si se debe compactar según umbral y tiempo.
- `tick()`
  - Llamado cada tick para verificar autocompactación periódica.
- `fragmentation_ratio() -> float`
  - Calcula el ratio de fragmentación.
- `efficiency() -> float`
  - Calcula la eficiencia de uso de memoria.

**Atributos importantes:**
- `auto_compact: bool` - Activa/desactiva autocompactación
- `compact_threshold: float` - Umbral de fragmentación (0.0-1.0)
- `compact_interval: int` - Intervalo en ticks para compactación periódica
- `ticks_since_compact: int` - Contador de ticks desde última compactación

#### 6.2.3 PagedMemoryManager (`src/simulation/memory/manager.py`)

**`PagedMemoryManager`** (clase)
- Gestor de memoria paginada con algoritmos de reemplazo.

**Métodos principales:**
- `__init__(total_mb, page_size_mb=4, replacement_alg="FIFO")`
  - Inicializa el gestor paginado con algoritmo de reemplazo.
- `allocate(process: Process, current_tick: int) -> PagedAllocationResult`
  - Asigna memoria paginada a un proceso.
- `access_page(process: Process, page_number: int, current_tick: int) -> bool`
  - Simula acceso a una página (genera hits o faults).
- `release(process: Process)`
  - Libera todas las páginas de un proceso.
- `_find_free_frame() -> Optional[int]`
  - Encuentra un frame libre.
- `_select_victim_frame(requesting_pid: int, current_tick: int) -> Optional[int]`
  - Selecciona frame víctima según algoritmo de reemplazo.
- `page_fault_rate() -> float`
  - Calcula la tasa de page faults.
- `memory_utilization() -> float`
  - Calcula el porcentaje de memoria utilizada.
- `snapshot_frames() -> List[Page]`
  - Obtiene snapshot de todos los frames.
- `get_page_table(pid: int) -> Optional[List[PageTableEntry]]`
  - Obtiene la tabla de páginas de un proceso.
- `tick(current_tick: int)`
  - Actualiza estado interno cada tick.

**Atributos importantes:**
- `frames: List[Page]` - Lista de frames físicos
- `page_tables: Dict[int, List[PageTableEntry]]` - Tablas de páginas por proceso
- `fifo_queue: Deque[int]` - Cola para algoritmo FIFO
- `page_faults: int` - Contador de page faults
- `page_hits: int` - Contador de page hits
- `total_accesses: int` - Total de accesos a páginas

#### 6.2.4 Integración en Engine (`src/simulation/engine.py`)

**`SimulationEngine`** (clase)

**Atributos relacionados:**
- `managers: Dict[str, MemoryManager]` - Gestores de memoria contigua (first, best, worst)
- `paged_managers: Dict[str, PagedMemoryManager]` - Gestores paginados (FIFO, LRU, Optimal)

**Métodos relacionados:**
- `create_process() -> Process`
  - Crea proceso y lo asigna en gestores contiguos y paginados.
- `manual_create_process(size_mb, duration, priority=None) -> Process`
  - Crea proceso manual y lo asigna en ambos sistemas.
- `release_process(process: Process)`
  - Libera memoria en todos los gestores.
- `tick()`
  - Actualiza gestores de memoria (llama a `tick()` en cada uno).
  - Simula accesos a páginas de procesos en ejecución.
- `paging_stats() -> Dict[str, Dict]`
  - Retorna estadísticas de los algoritmos de paginación.

### 6.3 Flujo de ejecución

1. **Inicialización:**
   - Se crean 3 gestores contiguos (first, best, worst) en `engine.__init__()`.
   - Se crean 3 gestores paginados (FIFO, LRU, Optimal) en `engine.__init__()`.

2. **Asignación de memoria:**
   - Al crear un proceso, se asigna en los 3 gestores contiguos.
   - Simultáneamente se asigna en los 3 gestores paginados.

3. **Ejecución:**
   - Cada tick, se llama a `manager.tick()` para verificar autocompactación.
   - Cada tick, se llama a `paged_manager.tick()` para actualizar estado.
   - Procesos en ejecución acceden aleatoriamente a sus páginas (10% probabilidad).

4. **Liberación:**
   - Al terminar un proceso, se libera en todos los gestores.
   - Los gestores contiguos verifican autocompactación tras liberar.

5. **Visualización:**
   - La GUI llama a `engine.paging_stats()` para obtener estadísticas.
   - Se muestran en la tabla "Estadísticas de Paginación".

## 7. Cambios recientes en la implementación

Se ha implementado un sistema completo de gestión avanzada de memoria que incluye:

- **Autocompactación automática** en `MemoryManager` (`src/simulation/memory/manager.py`) con parámetros configurables y verificación periódica.
- **Sistema de paginación completo** con `PagedMemoryManager` (`src/simulation/memory/manager.py`) que implementa tres algoritmos de reemplazo (FIFO, LRU, Optimal).
- **Modelos de datos** `Page` y `PageTableEntry` (`src/simulation/models.py`) para representar la estructura de paginación.
- **Integración en el motor de simulación** (`src/simulation/engine.py`) para asignar procesos en ambos sistemas de gestión.
- **Visualización en la interfaz gráfica** (`src/frontend/windows/main_window.py`) con tabla de estadísticas de paginación que muestra métricas en tiempo real.

Estos cambios permiten una simulación más realista de la gestión de memoria y facilitan la comparación de diferentes estrategias de asignación y reemplazo.

