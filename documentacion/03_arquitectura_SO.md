03 --- Arquitectura del Sistema Operativo
1. Arquitectura del kernel

Modelos incluidos:

Monolítico: todas las funcionalidades en espacio kernel.

Microkernel: solo funciones esenciales; servicios en espacio usuario.

Modular: híbrido, permite módulos cargables dinámicamente.

2. Modo de ejecución

El simulador reproduce:

modo kernel,

modo usuario,

transiciones mediante interrupciones, traps y syscalls.

3. Interrupciones

En la simulación existen:

3.1 Tipos principales

Interrupciones de hardware

Timer interrupt → usada para preempción (RR, SRTF, MLFQ).

I/O interrupt → notifica finalización de operaciones de dispositivos.

Interrupciones externas simuladas (red, sensores virtuales, etc.).

Interrupciones de software

Traps (errores: división entre cero, acceso inválido).

Syscalls (llamadas explícitas al SO).

Señales simuladas (kill, stop, continue, alarm).

Interrupciones pseudoaleatorias basadas en hashing

Para simular hardware con comportamiento variable, la simulación introduce un mecanismo hash determinístico que, dado un (PID, tick), produce:

si habrá interrupción,

qué tipo de interrupción ocurre,

si el proceso pasará a WAITING,

tiempo estimado de bloqueo.

3.2 Mecanismo hash del simulador

El objetivo es introducir no determinismo controlado, útil para:

pruebas repetibles,

procesos con comportamientos diferentes,

simulación de entornos I/O-bound vs CPU-bound.

Se implementa con:

mezcla de operaciones XOR, rotaciones y multiplicadores primos,

reducción modular para clasificar eventos.

3.3 Función hash de interrupciones (definición de la simulación)
def interrupt_hash(pid: int, tick: int) -> dict:
    x = pid ^ (tick * 0x45d9f3b)
    x = (x ^ (x >> 16)) * 0x119de1f3
    x = x ^ (x >> 13)

    t = abs(x) % 100            # rango 0–99 para clasificar probabilidades

    if t < 10:
        tipo = "IO_INTERRUPT"          # 10%
    elif t < 15:
        tipo = "TIMER_OVERRUN"         # 5%
    elif t < 17:
        tipo = "PAGE_FAULT"            # 2%
    elif t < 18:
        tipo = "SOFTWARE_TRAP"         # 1%
    else:
        tipo = None                    # 82% → no ocurre interrupción

    # Duración típica del bloqueo (solo si aplica)
    wait_ticks = (abs(x) % 8) + 1

    return {"tipo": tipo, "wait_ticks": wait_ticks}

3.4 Interrupciones que provocan WAITING

Un proceso entra en WAITING si su interrupción pertenece a:

IO_INTERRUPT

PAGE_FAULT

SOFTWARE_TRAP que requiere handler prolongado

syscalls bloqueantes: read(), sleep(), wait()

Interrupciones que NO envían al proceso a WAITING:

TIMER (solo preempción)

señales ligeras

traps recuperables

3.5 Integración con el ciclo del simulador

Cada tick:

La CPU ejecuta instrucción.

Scheduler decrementa quantum (si existe).

Se evalúa interrupt_hash(pid, tick).

Si se genera interrupción:

se invoca handler,

el proceso puede bloquearse,

se actualizan colas (READY → WAITING).

Si el dispositivo completa I/O → genera interrupción que devuelve procesos a READY.

4. Syscalls

Simuladas:

fork(), exec(), wait(), exit()

read(), write()

sleep()

modificaciones de prioridad

creación/destrucción de hilos

Cada syscall puede:

provocar context switch,

bloquear procesos (ej: read(), wait()),

generar interrupciones software.

5. Gestión de memoria (simplificada)

Modelos soportados:

base/limit

paginación simple

fallos de página simulados (usando el mecanismo hash de interrupciones)

asignación de marcos proporcional

Simulación incluye:

page table mínima,

latencia de page-fault con interrupción PAGE_FAULT,

reactivación del proceso tras resolver el fallo.

6. Sistema de archivos (conceptual)

Soporta:

estructura jerárquica de directorios,

tabla de archivos abiertos (por proceso),

operaciones básicas: open, close, read, write,

uso de bloques lógicos simulados.

Operaciones read/write pueden generar IO_INTERRUPT, enviando al proceso a WAITING.

7. I/O y controladores

Cada dispositivo posee:

cola propia

latencia

driver simulado

interrupción de finalización

Flujo típico:

Proceso realiza read() → pasa a WAITING.

Dispositivo registra operación y latencia.

Tras X ticks, dispositivo genera interrupción.

El kernel mueve el proceso a READY.

El comportamiento y los tiempos pueden depender del hash (PID, tick) para emular variabilidad realista.