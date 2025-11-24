# 03 --- Arquitectura del Sistema Operativo

## 1. Arquitectura del kernel

Modelos incluidos: - **Monolítico:** todas las funcionalidades en el
espacio kernel. - **Microkernel:** solo funciones esenciales, resto en
espacio usuario. - **Modular:** híbrido con módulos cargables
dinámicamente.

## 2. Modo de ejecución

El simulador reproduce: - **modo kernel**, - **modo usuario**, -
transiciones mediante interrupciones y syscalls.

## 3. Interrupciones

Tipos: - de hardware (timer, I/O), - de software (traps, syscalls).

Flujo:

    CPU → interrupción → tabla de vectores → handler → retorno

## 4. Syscalls

Simular llamadas: - fork() - exec() - wait() - exit() - read/write -
sleep()

Generan cambios de contexto y afectación de colas.

## 5. Gestión de memoria (simplificada)

Modelos soportados: - base/limit, - paginación simple, - fallos de
página simulados, - asignación de marcos proporcional.

## 6. Sistema de archivos (conceptual)

Incluye: - estructura de directorios, - tabla de archivos abiertos por
proceso, - operaciones: open, close, read, write.

## 7. I/O y controladores

Cada dispositivo posee: - cola propia, - latencia, - interrupciones al
completar operaciones.

## 8. Cambios recientes en la implementación

La arquitectura del simulador ha sido actualizada para incluir:

- Un diseño modular que separa la lógica de memoria, planificación y simulación en archivos independientes.
- Un motor de simulación (`engine.py`) que centraliza la ejecución y coordinación de los componentes.
- Una interfaz gráfica mejorada y modularizada para visualizar el estado del sistema operativo.

Estos cambios permiten una simulación más realista y una arquitectura más cercana a sistemas operativos reales.
