# Manual de Uso

Este manual explica cómo utilizar el Simulador de Sistema Operativo, desde la configuración inicial hasta la interpretación de los resultados y la generación de reportes.

## 1. Inicio y Configuración

Al ejecutar `python run.py`, se abrirá la ventana de **Configuración de Simulación**. Aquí podrás definir los parámetros del hardware y software simulado.

### Sección Hardware
*   **Número de CPUs:** Cantidad de procesadores físicos (1-8).
*   **Hilos por CPU:** Cantidad de hilos de ejecución por núcleo (Hyper-threading).
*   **Bancos de Memoria:** Número de unidades de memoria independientes.
*   **Capacidad por Banco (MB):** Tamaño de cada unidad de memoria.
*   **Tipo Almacenamiento (Swap):** Define la latencia de las operaciones de E/S (HDD, SSD, NVMe, Tape).
*   **Incluir TLB:** Activa la simulación del Translation Lookaside Buffer para acelerar la traducción de direcciones.

### Sección Software (Planificación y Memoria)
*   **Algoritmo de Planificación:**
    *   *FCFS (First-Come, First-Served):* Orden de llegada.
    *   *SJF (Shortest Job First):* El trabajo más corto primero (no expropiativo).
    *   *SRTF (Shortest Remaining Time First):* El tiempo restante más corto primero (expropiativo).
    *   *Round Robin:* Turnos rotativos con Quantum fijo.
    *   *Priority:* Basado en prioridad estática.
    *   *Priority Round Robin:* Colas de prioridad con Round Robin interno.
*   **Quantum (Ticks):** Tiempo máximo de CPU por turno (para algoritmos RR).
*   **Algoritmo de Asignación de Memoria:**
    *   *First Fit:* Primer hueco libre suficiente.
    *   *Best Fit:* El hueco que mejor se ajusta (menor desperdicio).
    *   *Worst Fit:* El hueco más grande disponible.
*   **Algoritmo de Paginación:** Estrategia de reemplazo de páginas (FIFO, LRU, Optimal).
*   **Tipo de Tabla de Páginas:** Estructura de la tabla (Un nivel, Dos niveles, Invertida).

Haz clic en **"Iniciar Simulación"** para comenzar.

## 2. Interfaz Principal

La ventana principal se divide en varias secciones:

### Panel Superior (Control)
*   **Botones de Control:** Iniciar, Pausar, Paso a Paso, Detener.
*   **Velocidad:** Deslizador para ajustar la velocidad de la simulación (ticks por segundo).
*   **Reloj:** Muestra el tiempo transcurrido en "Ticks".
*   **Finalizar Programa:** Detiene la simulación y genera el reporte PDF.

### Vistas Principales
La interfaz utiliza un diseño de pestañas o paneles para mostrar diferente información:

1.  **Vista de Procesos:**
    *   **Tabla de Procesos Activos:** Muestra PID, Estado, Uso de CPU, Memoria asignada, PC, Registros, etc.
    *   **Cola de Procesos (Ready):** Procesos esperando CPU.
    *   **Registro de Interrupciones:** Historial de eventos (Syscalls, I/O, Page Faults).

2.  **Vista de Memoria:**
    *   **Mapa de Memoria:** Representación visual de los bloques de memoria (Ocupado, Libre, Reservado SO).
    *   **Estadísticas:** Fragmentación, Eficiencia, Page Faults.
    *   **Almacenamiento (ROM/Swap):** Gráfico circular del uso del disco.

3.  **Vista de Arquitectura:**
    *   Diagrama visual de la arquitectura Modular, mostrando el flujo de datos entre componentes (Kernel, Drivers, Procesos).

4.  **Consola:**
    *   Terminal simulada para ingresar comandos manuales (ej. `create_process`, `kill`, `help`).

## 3. Interactuando con la Simulación

*   **Crear Procesos:** El sistema genera procesos automáticamente según una probabilidad, pero puedes forzar la creación usando la consola.
*   **Observar el Comportamiento:**
    *   Verás cómo los procesos cambian de estado (NEW -> READY -> RUNNING -> WAITING -> TERMINATED).
    *   Observa cómo la memoria se llena y se libera.
    *   Si la memoria se llena, verás actividad de paginación (Swap).
*   **Interrupciones:** Los procesos generarán interrupciones de E/S o fallos de página, liberando la CPU temporalmente.

## 4. Finalización y Reportes

Para terminar la sesión:
1.  Haz clic en el botón **"Finalizar Programa"** en la barra de herramientas superior.
2.  El sistema detendrá la simulación.
3.  Se generará automáticamente un archivo PDF llamado `reporte_simulacion.pdf` en la carpeta raíz del proyecto.
4.  Este reporte incluye:
    *   Resumen de la configuración.
    *   Métricas globales (Throughput, Tiempos de espera, Uso de CPU).
    *   Estadísticas de memoria (Fragmentación, Eficiencia).
    *   Detalle de procesos completados.
