# README --- Simulación de un Sistema Operativo en Python

Este repositorio contiene una simulación detallada del funcionamiento
interno de un Sistema Operativo (SO), estructurada para facilitar su
estudio, ampliación e implementación.\
Incluye modelos de **gestión de procesos**, **planificación**,
**arquitectura del kernel**, **manejo de interrupciones**,
**sincronización**, **gestión de memoria simplificada** y **dispositivos
simulados**.

## Estructura del proyecto

-   `01_gestion_de_procesos.md` --- Definición formal de procesos,
    hilos, PCB, estados, transiciones y mecanismos de cambio de
    contexto.
-   `02_planificacion.md` --- Políticas de planificación, algoritmos,
    colas, análisis matemáticos y su impacto en el sistema.
-   `03_arquitectura_SO.md` --- Arquitectura de un sistema operativo:
    monolítico, microkernel, modular; control de interrupciones,
    syscalls, memoria y dispositivos.
-   Código fuente (a desarrollar):\
    `kernel/`, `cpu/`, `scheduler/`, `devices/`, `mmu/`,
    `user_programs/`.

## Objetivo del proyecto

Crear una simulación ejecutable en Python que permita observar y
medir: - comportamiento de algoritmos de planificación, - interacción
entre CPU, procesos y dispositivos, - manejo de interrupciones y cambios
de contexto, - impacto del quantum, prioridades y cargas mixtas, -
diferencias entre hilos y procesos, - arquitectura interna del SO.

## Partes del proyecto

1. Conceptos básicos que la simulación debe modelar
•	Proceso: programa en ejecución — incluye PC (program counter), registros, pila, espacio de memoria lógico, identificador (PID) y estado. 
 
•	Estado de proceso: típicos: new → ready → running → waiting/blocked → terminated. Debes modelar transiciones y triggers (I/O, syscalls, timer, fork/exec, signals). 
 
•	Hilo (thread): unidad de ejecución ligera: comparte espacio de direcciones pero tiene su propio PC, pila, registros y TID. Soporta user threads y kernel threads (impactan planificación y cambio de contexto). 
 
•	Bloque de Control de Proceso (PCB): estructura que almacena estado, contexto (registros/PC), prioridad, contadores de uso, punteros a memoria, listas de archivos abiertos, padre/hijos, contabilidad (CPU bursts, I/O counts), y puntero a hilos. Fundamental para el cambio de contexto. 
 
________________________________________
2. Estructuras de datos principales (diseño para Python)
Clases sugeridas y campos clave (puedes usar dataclasses):
1.	Process / PCB
o	pid, ppid, state, pc, registers (dict), stack (simulado), memory_map (range or pages), priority, cpu_burst_estimate, accum_cpu, io_count, creation_time, last_scheduled_time, children, threads (list). 
 
2.	Thread (opcional, si modelas hilos)
o	tid, parent_pid, state, pc, registers, stack, affinity.
3.	Colas y listas
o	job_queue (todos los procesos), ready_queue (estructura según algoritmo: FIFO, min-heap por CPU-burst, multiple queues), device_queues (por dispositivo), wait_queues (por evento). 
 
4.	Scheduler (módulo con políticas)
o	estrategia (FCFS, SJF, Priority, RR, MLFQ), quantum (para RR), aging_params, per-CPU queues si simulas multiprocesador.
5.	Dispatcher / CPU
o	representa la CPU lógica: método dispatch(pcb), realiza cambio de contexto (guardar cargar), cuenta latencia del despachador. 
 
6.	Device y IOController (simulados)
o	modelo de latencias, uso de interrupciones o polling, y notificación que despierta procesos bloqueados. Soporte para DMA-like behavior si quieres modelar transferencias asíncronas. 
 
7.	MMU (opcional simplificado)
o	base/limit o tabla de páginas simulada, para modelar protección de memoria y page-faults. 
 
________________________________________
3. Mecanismos centrales y su modelado
3.1 Cambio de contexto (context switch)
•	Qué implica: salvar registros/PC en PCB del proceso saliente, actualizar estado, cargar registros/PC del proceso entrante, actualizar bit de modo si corresponde, contabilizar overhead (tiempo). Simula un coste en “unidades de tiempo” que afecte métricas. 
 
3.2 Planificador / despachador
•	Planificadores:
o	FCFS: cola FIFO. Simple, alto waiting time. 
 
o	SJF / SRTF: requiere estimaciones de CPU-burst. Óptimo para wait time si se conoce el burst. Implementa estimación exponencial ponderada (α) para predicción. 
 
o	Round Robin: quantum y rotación; modela overhead por context switch y el efecto del quantum en turnaround/response. 
 
o	Priority (con aging): prioridad estática o dinámica; evita starvation con aging. 
 
o	Multilevel Queue / Multilevel Feedback Queue (MLFQ): varias colas con reglas de promoción/descenso (útil para simular interacción CPU-bound vs I/O-bound). 
 
•	Eventos que disparan scheduling: bloqueo por I/O, llegada de nuevo proceso, finalización de proceso, tick del timer (preemption), señales. 
 
3.3 Interrupciones y syscalls
•	Modelar timer interrupt para RR y preemption: cada tick decrementa quantum; al agotarse, se genera una interrupción que invoca al planificador. 
 
•	Syscall/trap: transfiere control al kernel (cambia modo), actualiza PCB y puede bloquear proceso o generar I/O. Implementa un handler que en la simulación produce eventos (lectura archivo → genera latencia y pone proceso en device queue). 
 
3.4 Comunicación y sincronización (IPC)
•	Memoria compartida y message passing: para la simulación incluye primitivas: send(pid,msg), recv(), shared_memory segments (simple locks). 
 
•	Bloqueos y sincronización: semáforos, mutexes, condition variables; modela bloqueo y wakeup sobre wait_queues. Considera implementación de deadlock detection (resource allocation graph) opcional. 
 
________________________________________
4. Métricas y observabilidad (útil para validar la simulación)
•	CPU utilization, throughput, turnaround time, waiting time, response time, context switch count, dispatcher latency, I/O wait times. Implementa trazas (logs) y gráfico de Gantt para procesos. Estos indicadores mostrarán impacto de parámetros (quantum, aging, número de colas). 
 
________________________________________
5. Diseño del motor de simulación (arquitectura del app)
1.	Event-driven loop: simula tiempo en ticks discretos. Los eventos pueden ser: tick, I/O complete, new_process, syscall, timer. Un priority queue de eventos temporizados es útil.
2.	Time unit: define unidad base (por ejemplo 1 tick = 1 ms simulado). Context switch consume N ticks.
3.	Componente Scheduler: decide on next() cada vez que se ejecuta scheduling (invocado por eventos definidos).
4.	Modelado de CPU(s): si simulas multiprocesador, mantener una cola por CPU o una cola global con afinidad de procesador. 
 
5.	Módulo de dispositivos: simula latencias y genera eventos de interrupción al completar I/O. 
 
6.	API para procesos de usuario (en la simulación): funciones para fork(), exec(), exit(), wait(), read()/write() que interactúan con kernel-simulado. 
 
________________________________________
6. Algoritmos y detalles a implementar (prioritarios)
•	Implementar primero: estructura PCB, ready queue (FIFO), dispatcher y cambio de contexto, timer interrupt y RR; esto permite ver interacción básica. 
 
•	Siguientes: SJF (y SRTF), Priority with aging, MLFQ. Para SJF/SRTF implementa predicción de CPU-burst (α-weighted avg).
•	Opcionales/avanzados: per-CPU scheduling, processor affinity, load balancing, I/O scheduling interplay, thread-level scheduling (user vs kernel threads). 
 
________________________________________
7. Sugerencia de API / esqueleto en Python (alto nivel)
@dataclass
class PCB:
    pid: int
    state: str
    pc: int
    registers: Dict[str,int]
    priority: int
    cpu_est: float
    accum_cpu: int
    # ...

class Scheduler:
    def __init__(self, policy='RR', quantum=5): ...
    def add(self, pcb): ...
    def next(self): -> PCB or None: ...
    def preempt_check(self, cpu): ...

class CPU:
    def tick(self):
        # decrement quantum, run instruction (simulate cpu-burst units),
        # handle context switches
(Este bloque es una guía; el detalle lo defines según la granularidad de tu simulador.)
________________________________________
8. Visualización y pruebas
•	Gantt chart por tick para ver asignaciones CPU.
•	Dashboards con métricas en tiempo real (matplotlib o simples tablas).
•	Escenarios de prueba: mezcla de CPU-bound e I/O-bound; medir efecto del quantum y de MLFQ; comparar FCFS vs RR vs SJF. 
 
________________________________________
9. Extensiones posibles (futuro)
•	Simular protección y MMU (base/limit o paginación) y page-faults; syscalls reales mapeadas a acciones simuladas. 
 
•	Micronúcleo vs monolítico: simula servicios como procesos en espacio de usuario (microkernel) o como funciones del kernel (monolítico) para comparar rendimiento/seguridad. 
 
•	Simulación de máquinas virtuales / hypervisor (si quieres modelar más capas). 
 
________________________________________
10. Resumen operativo rápido — Prioridades de implementación (roadmap mínimo)
1.	Definir clases PCB, Scheduler, CPU, Device. 

2.	Implementar event loop + ready queue (RR). Medir métricas básicas. 
 
3.	Añadir SJF y Priority; comparar por métricas. 
 
4.	Implementar threads (user vs kernel) y probar con multiprocesador sencillo. 
 
5.	Añadir visualización (gráficos de Gantt) y trazas.



## Cómo usar este README

Este documento sirve como punto de partida y mapa general.\
Cada archivo de la serie detalla en profundidad los mecanismos internos.

