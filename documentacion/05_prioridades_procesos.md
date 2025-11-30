# 05 --- Prioridades de Procesos

## 1. Introducción

La planificación por prioridades es un mecanismo fundamental en los Sistemas Operativos modernos que permite asignar diferentes niveles de importancia a los procesos. Este documento describe la implementación del sistema de prioridades en el simulador, incluyendo asignación automática, algoritmos de planificación basados en prioridades y mecanismos de aging para evitar inanición.

## 2. Concepto de Prioridad

### 2.1 Definición

La **prioridad** es un valor numérico que indica la importancia relativa de un proceso. En el simulador:

- **Rango:** 0-9 (donde 0 es la mayor prioridad y 9 es la menor).
- **Menor número = Mayor prioridad:** un proceso con prioridad 0 tiene mayor importancia que uno con prioridad 9.

### 2.2 Uso en Planificación

Los algoritmos de planificación utilizan la prioridad para decidir qué proceso ejecutar cuando hay múltiples procesos listos. Los procesos de mayor prioridad (menor número) se ejecutan antes que los de menor prioridad.

## 3. Asignación Automática de Prioridades

### 3.1 Algoritmo de Asignación

El simulador asigna prioridades automáticamente a todos los procesos generados aleatoriamente basándose en tres factores:

1. **Tamaño del proceso (30%):** procesos más pequeños reciben mayor prioridad.
2. **Duración del proceso (40%):** procesos más cortos reciben mayor prioridad.
3. **Uso de CPU (30%):** procesos menos intensivos en CPU reciben mayor prioridad.

### 3.2 Cálculo de Prioridad

El algoritmo normaliza cada factor y calcula un score ponderado:

```
priority_score = (size_score × 0.3) + (duration_score × 0.4) + (cpu_score × 0.3)
priority = int(priority_score × 9) + variación_aleatoria
```

Donde:
- `size_score`: inversamente proporcional al tamaño (procesos pequeños = mayor score).
- `duration_score`: inversamente proporcional a la duración (procesos cortos = mayor score).
- `cpu_score`: inversamente proporcional al uso de CPU (menos intensivo = mayor score).

### 3.3 Variación Aleatoria

Se agrega una variación aleatoria de ±1 para simular diferentes tipos de procesos y evitar que todos los procesos similares tengan exactamente la misma prioridad.

### 3.4 Procesos Manuales

Los procesos creados manualmente pueden:
- Especificar una prioridad explícita (0-9).
- Usar asignación automática si no se especifica prioridad.

## 4. Algoritmos de Planificación con Prioridades

### 4.1 Modificación de Algoritmos Existentes

Todos los algoritmos de planificación existentes han sido modificados para considerar prioridades:

#### 4.1.1 FCFS (First Come First Served)

- Ordena primero por prioridad, luego por orden de llegada.
- Procesos de mayor prioridad se ejecutan primero, independientemente de cuándo llegaron.

#### 4.1.2 SJF (Shortest Job First)

- Considera prioridad primero, luego duración más corta.
- Entre procesos de igual prioridad, selecciona el de menor duración.

#### 4.1.3 SRTF (Shortest Remaining Time First)

- Considera prioridad y tiempo restante.
- Un proceso de mayor prioridad puede preemptar uno de menor prioridad.
- Entre procesos de igual prioridad, selecciona el de menor tiempo restante.

#### 4.1.4 Round Robin (RR)

- Ordena la cola por prioridad antes de seleccionar.
- Procesos de mayor prioridad se ejecutan primero.
- El quantum se aplica dentro de cada nivel de prioridad.

### 4.2 Priority Scheduler

Algoritmo dedicado de planificación por prioridades con las siguientes características:

#### 4.2.1 Funcionamiento

- **Preemptivo:** un proceso de mayor prioridad puede interrumpir uno de menor prioridad en ejecución.
- **Cola ordenada:** mantiene la cola de procesos listos ordenada por prioridad.
- **Selección:** siempre selecciona el proceso de mayor prioridad disponible.

#### 4.2.2 Aging

Implementa un mecanismo de **aging** (envejecimiento) para evitar inanición:

- **Intervalo de aging:** cada 10 ticks se revisan los procesos en espera.
- **Condición:** procesos que esperan más de 20 ticks ven aumentada su prioridad.
- **Efecto:** la prioridad se reduce en 1 (aumenta la importancia) por cada ciclo de aging aplicado.
- **Límite:** la prioridad no puede bajar de 0.

#### 4.2.3 Preemption

Cuando un proceso de mayor prioridad llega a la cola:
1. El proceso actual en ejecución es preemptado.
2. Se mueve a la cola de procesos listos.
3. El nuevo proceso de mayor prioridad toma la CPU.

### 4.3 Priority Round Robin

Implementa Round Robin con múltiples colas de prioridad:

#### 4.3.1 Estructura

- **Múltiples colas:** una cola por cada nivel de prioridad (0-9).
- **Round Robin por nivel:** dentro de cada nivel de prioridad, se aplica Round Robin.
- **Procesamiento por prioridad:** se procesan primero las colas de mayor prioridad.

#### 4.3.2 Funcionamiento

1. Busca desde la cola de mayor prioridad (0) hacia la menor (9).
2. Si encuentra procesos en una cola, selecciona el siguiente según Round Robin.
3. Solo procesa colas de menor prioridad cuando las de mayor prioridad están vacías.

## 5. Integración en el Simulador

### 5.1 Motor de Simulación

El `SimulationEngine` integra el sistema de prioridades:

- **Asignación automática:** todos los procesos generados automáticamente reciben prioridad.
- **Soporte multiprocesador:** la preemption por prioridad funciona en sistemas con múltiples CPUs.
- **Logging:** registra eventos de preemption por prioridad en el log de interrupciones.

### 5.2 Interfaz Gráfica

La interfaz muestra:

- **Columna de prioridad:** en la tabla de procesos activos.
- **Mensajes de preemption:** en el registro de interrupciones cuando ocurre preemption por prioridad.
- **Selección de algoritmos:** permite elegir entre Priority y PriorityRR en el diálogo de configuración.

### 5.3 Consola de Comandos

El comando `create` acepta un parámetro opcional de prioridad:

```
create <size_mb> <duration_ticks> [priority]
```

Ejemplos:
- `create 16 50 0` - Crea proceso con prioridad 0 (alta).
- `create 16 50 5` - Crea proceso con prioridad 5 (media).
- `create 16 50` - Crea proceso con prioridad automática.

## 6. Ventajas y Consideraciones

### 6.1 Ventajas

- **Flexibilidad:** permite dar preferencia a procesos importantes.
- **Eficiencia:** procesos críticos se ejecutan más rápido.
- **Control:** el usuario puede especificar prioridades manualmente.

### 6.2 Consideraciones

- **Inanición:** procesos de baja prioridad pueden esperar indefinidamente (mitigado por aging).
- **Overhead:** mantener colas ordenadas por prioridad tiene un costo computacional.
- **Justicia:** puede ser injusto con procesos de baja prioridad si no hay aging.

### 6.3 Aging como Solución

El mecanismo de aging garantiza que:

- Procesos que esperan mucho tiempo eventualmente aumentan su prioridad.
- Se evita la inanición completa de procesos de baja prioridad.
- El sistema mantiene cierto grado de justicia.

## 7. Métricas y Observación

### 7.1 Métricas Disponibles

El simulador permite observar:

- **Prioridad de cada proceso:** visible en la tabla de procesos.
- **Tiempo de espera:** cuánto tiempo ha esperado cada proceso.
- **Eventos de preemption:** registrados en el log de interrupciones.
- **Efecto del aging:** cambios en prioridad de procesos que esperan mucho.

### 7.2 Cómo Verificar el Funcionamiento

1. **Seleccionar algoritmo Priority o PriorityRR** en el diálogo de configuración.
2. **Observar la columna Prioridad** en la tabla de procesos.
3. **Crear procesos con diferentes prioridades** usando la consola.
4. **Verificar preemption** en el registro de interrupciones.
5. **Observar aging** en procesos que esperan más de 20 ticks.

## 8. Implementación en el código

### 8.1 Estructura de archivos

```
src/simulation/
├── models.py                    # Modelo Process con atributo priority
├── scheduler.py                 # Schedulers: PriorityScheduler, PriorityRoundRobin
└── engine.py                    # Asignación automática y integración

src/frontend/
├── windows/
│   ├── config_dialog.py        # Selección de algoritmos Priority/PriorityRR
│   └── main_window.py          # Visualización de prioridades en tabla
└── components/
    └── console.py               # Comando create con parámetro priority
```

### 8.2 Clases principales

#### 8.2.1 Modelo Process (`src/simulation/models.py`)

**`Process`** (dataclass)
- Representa un proceso en el sistema.

**Atributo de prioridad:**
- `priority: int = 0` - Prioridad del proceso (0-9, donde 0 es mayor prioridad)

**Otros atributos relacionados:**
- `waiting_ticks: int = 0` - Tiempo de espera (usado para aging)

#### 8.2.2 Schedulers (`src/simulation/scheduler.py`)

**`PriorityScheduler`** (clase)
- Planificador por prioridades con preemption y aging.

**Métodos principales:**
- `__init__(preemptive=True, aging_enabled=True, aging_interval=10)`
  - Inicializa con opciones de preemption y aging.
- `add_process(process: Process)`
  - Agrega proceso y mantiene cola ordenada por prioridad.
- `next_process(current_tick: int) -> Optional[Process]`
  - Selecciona proceso de mayor prioridad, aplica aging si corresponde.
- `_apply_aging()`
  - Aumenta prioridad de procesos que esperan mucho tiempo.

**Atributos importantes:**
- `preemptive: bool` - Activa/desactiva preemption
- `aging_enabled: bool` - Activa/desactiva aging
- `aging_interval: int` - Intervalo en ticks para aplicar aging
- `last_aging_tick: int` - Último tick en que se aplicó aging
- `ready_queue: List[Process]` - Cola ordenada por prioridad

**`PriorityRoundRobin`** (clase)
- Round Robin con múltiples colas de prioridad.

**Métodos principales:**
- `__init__(quantum: int = 4)`
  - Inicializa con quantum para Round Robin.
- `add_process(process: Process)`
  - Agrega proceso a la cola correspondiente a su prioridad.
- `next_process(current_tick: int) -> Optional[Process]`
  - Selecciona proceso desde cola de mayor prioridad disponible.

**Atributos importantes:**
- `quantum: int` - Quantum para Round Robin
- `priority_queues: Dict[int, Deque[Process]]` - Una cola por nivel de prioridad (0-9)

**Algoritmos modificados:**

**`FCFS`** (clase)
- Modificado: `next_process()` ordena por prioridad antes de seleccionar.

**`SJF`** (clase)
- Modificado: `next_process()` considera prioridad primero, luego duración.

**`SRTF`** (clase)
- Modificado: `next_process()` considera prioridad y tiempo restante.

**`RoundRobin`** (clase)
- Modificado: `next_process()` ordena cola por prioridad antes de seleccionar.

#### 8.2.3 Engine (`src/simulation/engine.py`)

**`SimulationEngine`** (clase)

**Métodos relacionados con prioridades:**
- `_assign_priority(process: Process) -> int`
  - Calcula y asigna prioridad automática basada en características del proceso.
  - Considera: tamaño (30%), duración (40%), uso CPU (30%).
  - Retorna valor entre 0-9.
- `create_process() -> Process`
  - Crea proceso y asigna prioridad automáticamente llamando a `_assign_priority()`.
- `manual_create_process(size_mb, duration, priority=None) -> Process`
  - Crea proceso manual.
  - Si `priority` es `None`, usa asignación automática.
  - Si se especifica, usa la prioridad proporcionada.
- `update_processes()`
  - Maneja preemption por prioridad en sistemas multiprocesador.
  - Para algoritmo Priority, verifica si hay proceso de mayor prioridad en cola.

**Inicialización de schedulers:**
- En `__init__()`, se inicializa scheduler según `scheduling_alg`:
  - `"Priority"` → `PriorityScheduler()`
  - `"PriorityRR"` → `PriorityRoundRobin(quantum=quantum)`

#### 8.2.4 Interfaz Gráfica

**`ConfigDialog`** (`src/frontend/windows/config_dialog.py`)
- Diálogo de configuración inicial.

**Modificaciones:**
- `sched_combo`: Agregados "Priority" y "PriorityRR" a las opciones.
- `on_sched_change()`: Habilita quantum para PriorityRR además de RR.

**`MainWindow`** (`src/frontend/windows/main_window.py`)
- Ventana principal de la aplicación.

**Modificaciones:**
- `process_table`: Columna "Prioridad" muestra `p.priority` de cada proceso.
- `refresh_process_table()`: Incluye prioridad en la fila de cada proceso.

**`ConsoleWidget`** (`src/frontend/components/console.py`)
- Consola de comandos integrada.

**Modificaciones:**
- `cmd_create()`: Acepta parámetro opcional `priority` (0-9).
- Si se especifica, pasa la prioridad a `engine.manual_create_process()`.
- Si no se especifica, usa `None` para asignación automática.

### 8.3 Flujo de ejecución

1. **Creación de proceso:**
   - `engine.create_process()` o `engine.manual_create_process()`.
   - Se llama a `_assign_priority()` si no se especifica prioridad.
   - Se asigna la prioridad al atributo `process.priority`.

2. **Agregar a scheduler:**
   - `scheduler.add_process(process)`.
   - PriorityScheduler: ordena cola por prioridad.
   - PriorityRoundRobin: agrega a cola correspondiente a su prioridad.

3. **Selección de proceso:**
   - `scheduler.next_process(current_tick)`.
   - PriorityScheduler: aplica aging si corresponde, selecciona mayor prioridad.
   - PriorityRoundRobin: busca desde prioridad 0 hacia 9.

4. **Preemption:**
   - En `engine.update_processes()`, para algoritmo Priority:
     - Verifica si hay proceso de mayor prioridad en cola.
     - Si existe, preempta proceso actual.

5. **Aging:**
   - Cada `aging_interval` ticks (10 por defecto):
     - `PriorityScheduler._apply_aging()` revisa procesos en espera.
     - Procesos que esperan >20 ticks ven aumentada su prioridad.

6. **Visualización:**
   - GUI muestra prioridad en tabla de procesos.
   - Log de interrupciones muestra eventos de preemption por prioridad.

### 8.4 Ejemplo de uso en código

```python
# Crear proceso con prioridad automática
process = engine.create_process()  # Prioridad asignada automáticamente

# Crear proceso con prioridad específica
process = engine.manual_create_process(size_mb=16, duration=50, priority=0)

# Usar PriorityScheduler
scheduler = PriorityScheduler(preemptive=True, aging_enabled=True)
scheduler.add_process(process)
next_proc = scheduler.next_process(current_tick=100)

# Usar PriorityRoundRobin
scheduler = PriorityRoundRobin(quantum=4)
scheduler.add_process(process)
next_proc = scheduler.next_process(current_tick=100)
```

## 9. Cambios recientes en la implementación

Se ha implementado un sistema completo de prioridades de procesos que incluye:

- **Asignación automática de prioridades** (`_assign_priority()` en `src/simulation/engine.py`) basada en características del proceso (tamaño, duración, uso de CPU) con variación aleatoria.
- **PriorityScheduler** (`src/simulation/scheduler.py`): algoritmo dedicado de planificación por prioridades con preemption y aging.
- **PriorityRoundRobin** (`src/simulation/scheduler.py`): Round Robin con múltiples colas de prioridad.
- **Modificación de algoritmos existentes** (`src/simulation/scheduler.py`): FCFS, SJF, SRTF, RR ahora consideran prioridades en la selección de procesos.
- **Integración en el motor de simulación** (`src/simulation/engine.py`) con soporte para preemption por prioridad en sistemas multiprocesador.
- **Actualización de la interfaz gráfica** (`src/frontend/windows/config_dialog.py`, `src/frontend/windows/main_window.py`) para mostrar prioridades y permitir selección de algoritmos basados en prioridades.
- **Consola de comandos mejorada** (`src/frontend/components/console.py`) para crear procesos con prioridades específicas.

Estos cambios permiten una simulación más realista de sistemas operativos modernos y facilitan el estudio de los efectos de las prioridades en el rendimiento del sistema.

