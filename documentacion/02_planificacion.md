# 02 --- Planificación de Procesos

## 1. Introducción

El planificador (scheduler) decide qué proceso ejecuta la CPU en cada
instante.

Tipos: - **Planificador a largo plazo:** controla admisión de
procesos. - **Planificador a corto plazo:** selección del siguiente
proceso listo. - **Planificador a mediano plazo:** swapping (opcional en
simulación).

## 2. Métricas fundamentales

-   **Throughput**
-   **Turnaround time**
-   **Waiting time**
-   **Response time**
-   **CPU Utilization**

## 3. Algoritmos de planificación incluidos

### 3.1 FCFS --- First Come First Served

-   no apropiativo,
-   implementado con cola FIFO.

### 3.2 SJF --- Shortest Job First

-   óptimo teórico para minimizar waiting time,
-   requiere predicción del CPU burst mediante media exponencial
    ponderada:

```{=html}
<!-- -->
```
    τ(n+1) = α · t(n) + (1−α) · τ(n)

### 3.3 SRTF --- Shortest Remaining Time First

-   versión apropiativa de SJF.

### 3.4 RR --- Round Robin

-   apropiativo,
-   requiere quantum,
-   balance entre overhead y tiempo de respuesta.

### 3.5 Priority Scheduling

-   apropiativo o no,
-   riesgo de inanición mitigado por **aging**.

### 3.6 MLFQ --- Multilevel Feedback Queue

Incluye: - múltiples colas con diferentes prioridades, - reglas de
subida/bajada, - prioridad a I/O-bound, - castigo a CPU-bound.

## 4. Multiprocesador y afinidad

Simulación soporta: - colas por CPU, - balanceo de carga, - afinidad
leve o estricta.

## 5. Interacción entre planificación e I/O

La planificación es un proceso reactivo a: - interrupciones, -
finalización de ráfagas, - retorno de I/O.

## 6. Cambios recientes en la implementación

Se ha actualizado el motor de simulación para incluir:

- Modularización del planificador en `scheduler.py`.
- Implementación de estrategias de planificación como Round Robin y SJF en `strategies.py`.
- Integración con un motor centralizado en `engine.py` para coordinar la planificación y ejecución de procesos.

Estos cambios mejoran la flexibilidad y permiten añadir nuevas políticas de planificación de manera sencilla.
