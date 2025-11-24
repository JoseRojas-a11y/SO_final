# Simulación de un Sistema Operativo

Este proyecto es una simulación detallada del funcionamiento interno de un Sistema Operativo (SO), diseñada para estudiar y experimentar con conceptos clave como la gestión de procesos, planificación, arquitectura del kernel, manejo de interrupciones, sincronización, gestión de memoria y dispositivos simulados.

## Características principales

- **Gestión de procesos:** Simulación de estados, transiciones, PCB y cambio de contexto.
- **Planificación:** Implementación de algoritmos como Round Robin, SJF y MLFQ.
- **Arquitectura modular:** Separación de componentes en módulos independientes para facilitar la extensibilidad.
- **Interfaz gráfica:** Visualización en tiempo real del estado del sistema operativo.

## Requisitos previos

- Python 3.8 o superior.
- Librerías especificadas en `requirements.txt`.

## Instrucciones de uso

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/JoseRojas-a11y/SO_final.git
   cd SO_final
   ```

2. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Ejecutar el programa:

   ```bash
   python run.py
   ```

## Estructura del proyecto

- `src/`: Contiene el código fuente del simulador.
  - `simulation/`: Lógica principal de la simulación.
  - `frontend/`: Componentes de la interfaz gráfica.
- `documentacion/`: Archivos de documentación detallada.
- `requirements.txt`: Dependencias necesarias para ejecutar el proyecto.
- `run.py`: Punto de entrada principal para ejecutar la simulación.

## Objetivo del proyecto

El objetivo es proporcionar una herramienta educativa para comprender los conceptos fundamentales de los sistemas operativos y experimentar con diferentes configuraciones y algoritmos.
