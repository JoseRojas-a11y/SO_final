# Manual de Instalación

Este documento describe los pasos necesarios para instalar y configurar el entorno de ejecución del Simulador de Sistema Operativo.

## Requisitos del Sistema

*   **Sistema Operativo:** Windows 10/11, macOS o Linux.
*   **Python:** Versión 3.8 o superior.
*   **Espacio en disco:** Mínimo 100 MB.
*   **Memoria RAM:** Mínimo 4 GB (recomendado 8 GB para simulaciones complejas).

## Pasos de Instalación

### 1. Obtener el Código Fuente

Si tienes acceso al repositorio git:
```bash
git clone https://github.com/JoseRojas-a11y/SO_final.git
cd SO_final
```

Si tienes el código en un archivo comprimido (.zip), extráelo en una carpeta de tu elección.

### 2. Crear un Entorno Virtual (Recomendado)

Es recomendable utilizar un entorno virtual para aislar las dependencias del proyecto.

**En Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

El proyecto utiliza las siguientes librerías principales:
*   `PyQt6`: Para la interfaz gráfica de usuario.
*   `reportlab`: Para la generación de reportes en PDF.
*   `rich`: Para formateo de texto en consola (opcional/desarrollo).

Instala todas las dependencias ejecutando:

```bash
pip install -r requirements.txt
```

### 4. Verificación de la Instalación

Para verificar que todo se ha instalado correctamente, ejecuta el script principal:

```bash
python run.py
```

Debería aparecer una ventana de configuración titulada "Configuración de Simulación".

## Solución de Problemas Comunes

*   **Error `ModuleNotFoundError: No module named 'PyQt6'`**:
    Asegúrate de haber activado el entorno virtual antes de instalar las dependencias y de que el comando `pip install` finalizó sin errores.

*   **Error al generar PDF**:
    Verifica que tienes permisos de escritura en la carpeta del proyecto, ya que el reporte se guarda en el directorio raíz.

*   **La interfaz se ve muy pequeña/grande**:
    PyQt suele adaptarse a la resolución, pero si usas escalado de pantalla en Windows (ej. 150%), podría verse diferente. Intenta ajustar la configuración de pantalla de tu sistema operativo.
