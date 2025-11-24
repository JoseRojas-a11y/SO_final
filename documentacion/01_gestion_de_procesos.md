# 01 --- Gestión de Procesos

## 1. Introducción

La gestión de procesos constituye el núcleo funcional de cualquier
Sistema Operativo moderno.\
Un **proceso** es un programa en ejecución, compuesto por: - código
ejecutable, - contador de programa (PC), - pila, - datos globales, -
recursos asignados por el sistema.

## 2. Estados del proceso

Un proceso típico atraviesa los siguientes estados:

    NEW → READY → RUNNING → WAITING → READY → RUNNING → TERMINATED

Definición formal: - **NEW:** el proceso ha sido creado. - **READY:**
está listo para ejecutarse, pero la CPU está ocupada. - **RUNNING:**
actualmente ejecutándose en la CPU. - **WAITING/BLOCKED:** esperando
terminación de I/O o evento. - **TERMINATED:** finalizado.

## 3. Tabla de procesos

El kernel mantiene una **Process Table**, donde cada entrada representa
un PCB (Process Control Block).

## 4. PCB --- Process Control Block

Contiene: - PID - estado - PC - registros - punteros de pila -
prioridad - estadísticas de uso de CPU - mapa de memoria - archivos
abiertos - información de sincronización - hilos asociados

## 5. Cambio de contexto (Context Switch)

Ocurre cuando el SO: 1. guarda el estado del proceso actual en su PCB,
2. restaura el estado del próximo proceso, 3. actualiza tablas internas
y contadores, 4. transfiere control al nuevo proceso.

Coste simulado: N ticks.

## 6. Eventos que afectan procesos

-   interrupciones,
-   finalización de ráfaga de CPU,
-   solicitudes de I/O,
-   señales,
-   creación/terminación de procesos (fork/exec/exit),
-   temporizador (timer interrupt).

## 7. Modelo de hilos (threads)

Cada proceso puede contener uno o más hilos: - **User threads:**
gestionados por una biblioteca en espacio de usuario. - **Kernel
threads:** gestionados por el kernel.

Simulación incluye: - TID, - pila del hilo, - estado independiente del
proceso, - planificador a nivel de hilo.

## 8. IPC --- Comunicación entre procesos

Técnicas soportadas: - memoria compartida, - semáforos, - colas de
mensajes, - pipes, - locks y monitores, - variables de condición.

Cada mecanismo afecta estados y sincronización interna.
