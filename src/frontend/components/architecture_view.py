from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from typing import Dict, List, Optional

class ArchitectureView(QWidget):
    """Componente visual que muestra la arquitectura del sistema operativo."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.architecture = "Monolithic"
        self.kernel_mode = "monolithic"
        self.external_modules: Dict[str, Dict] = {}
        self.dynamic_modules: Dict[str, Dict] = {}
        self.ipc_enabled = False
        self.setMinimumHeight(200)
        self.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc;")
        
    def update_architecture(self, architecture: str, kernel_mode: str, 
                           external_modules: Dict = None, 
                           dynamic_modules: Dict = None,
                           ipc_enabled: bool = False):
        """Actualiza la visualización con la información de la arquitectura."""
        self.architecture = architecture
        self.kernel_mode = kernel_mode
        self.external_modules = external_modules or {}
        self.dynamic_modules = dynamic_modules or {}
        self.ipc_enabled = ipc_enabled
        self.update()
        
    def paintEvent(self, event):
        """Dibuja la representación visual de la arquitectura."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Fondo
        painter.fillRect(0, 0, w, h, QColor(245, 245, 245))
        
        if self.architecture == "Monolithic":
            self._draw_monolithic(painter, w, h)
        elif self.architecture == "Microkernel":
            self._draw_microkernel(painter, w, h)
        elif self.architecture == "Modular":
            self._draw_modular(painter, w, h)
            
    def _draw_monolithic(self, painter: QPainter, w: int, h: int):
        """Dibuja la arquitectura monolítica."""
        # Núcleo único centralizado
        kernel_x = w // 2 - 100
        kernel_y = h // 2 - 40
        kernel_w = 200
        kernel_h = 80
        
        # Dibujar núcleo monolítico
        painter.setBrush(QBrush(QColor(70, 130, 180)))  # Steel blue
        painter.setPen(QPen(QColor(50, 100, 150), 2))
        painter.drawRoundedRect(kernel_x, kernel_y, kernel_w, kernel_h, 10, 10)
        
        # Texto del núcleo
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(kernel_x, kernel_y, kernel_w, kernel_h, 
                        Qt.AlignmentFlag.AlignCenter, "NÚCLEO\nMONOLÍTICO")
        
        # Etiquetas de funcionalidades integradas
        font_small = QFont("Arial", 9)
        painter.setFont(font_small)
        painter.setPen(QColor(50, 50, 50))
        
        labels = ["Procesos", "Memoria", "Dispositivos", "Sistema de Archivos"]
        label_y = kernel_y + kernel_h + 10
        label_spacing = w // (len(labels) + 1)
        
        for i, label in enumerate(labels):
            x = label_spacing * (i + 1) - 30
            painter.drawText(x, label_y, 60, 20, Qt.AlignmentFlag.AlignCenter, label)
            # Línea conectando al núcleo
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
            painter.drawLine(x + 30, label_y, kernel_x + kernel_w // 2, kernel_y + kernel_h)
            painter.setPen(QColor(50, 50, 50))
            
    def _draw_microkernel(self, painter: QPainter, w: int, h: int):
        """Dibuja la arquitectura microkernel."""
        # Núcleo mínimo en el centro
        kernel_x = w // 2 - 60
        kernel_y = h // 2 - 30
        kernel_w = 120
        kernel_h = 60
        
        # Dibujar núcleo mínimo
        painter.setBrush(QBrush(QColor(34, 139, 34)))  # Forest green
        painter.setPen(QPen(QColor(20, 100, 20), 2))
        painter.drawRoundedRect(kernel_x, kernel_y, kernel_w, kernel_h, 8, 8)
        
        # Texto del núcleo
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(kernel_x, kernel_y, kernel_w, kernel_h, 
                        Qt.AlignmentFlag.AlignCenter, "MICROKERNEL\n(Procesos + IPC)")
        
        # Dibujar módulos externos alrededor
        modules = list(self.external_modules.values())
        if not modules:
            modules = [
                {"name": "Servicio de Memoria", "status": "active"},
                {"name": "Servicio de Archivos", "status": "active"},
                {"name": "Servicio de Dispositivos", "status": "active"}
            ]
        
        num_modules = len(modules)
        angle_step = 360 / num_modules if num_modules > 0 else 0
        radius = min(w, h) // 3
        
        for i, module in enumerate(modules):
            angle = i * angle_step
            rad = angle * 3.14159 / 180
            
            # Posición del módulo
            mod_x = w // 2 + int(radius * 0.7 * (1 if i % 2 == 0 else -1)) - 50
            mod_y = h // 2 + int(radius * 0.5 * (1 if i < num_modules // 2 else -1)) - 30
            
            # Dibujar módulo externo
            status_color = QColor(50, 150, 50) if module.get("status") == "active" else QColor(150, 150, 150)
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(QColor(30, 100, 30), 2))
            painter.drawRoundedRect(mod_x, mod_y, 100, 60, 8, 8)
            
            # Texto del módulo
            painter.setPen(QColor(255, 255, 255))
            font_small = QFont("Arial", 8)
            painter.setFont(font_small)
            name = module.get("name", "Módulo")
            painter.drawText(mod_x, mod_y, 100, 60, Qt.AlignmentFlag.AlignCenter, 
                           name.replace("Servicio de ", ""))
            
            # Línea conectando al núcleo
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
            painter.drawLine(mod_x + 50, mod_y + 30, kernel_x + kernel_w // 2, kernel_y + kernel_h // 2)
        
        # Indicador IPC
        if self.ipc_enabled:
            painter.setPen(QColor(255, 140, 0))
            painter.setBrush(QBrush(QColor(255, 140, 0, 100)))
            painter.drawEllipse(kernel_x + kernel_w - 15, kernel_y - 15, 30, 30)
            painter.setPen(QColor(255, 255, 255))
            font_tiny = QFont("Arial", 7, QFont.Weight.Bold)
            painter.setFont(font_tiny)
            painter.drawText(kernel_x + kernel_w - 15, kernel_y - 15, 30, 30,
                           Qt.AlignmentFlag.AlignCenter, "IPC")
            
    def _draw_modular(self, painter: QPainter, w: int, h: int):
        """Dibuja la arquitectura modular."""
        # Núcleo base en el centro
        kernel_x = w // 2 - 70
        kernel_y = h // 2 - 35
        kernel_w = 140
        kernel_h = 70
        
        # Dibujar núcleo base
        painter.setBrush(QBrush(QColor(138, 43, 226)))  # Blue violet
        painter.setPen(QPen(QColor(100, 30, 160), 2))
        painter.drawRoundedRect(kernel_x, kernel_y, kernel_w, kernel_h, 8, 8)
        
        # Texto del núcleo
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(kernel_x, kernel_y, kernel_w, kernel_h,
                        Qt.AlignmentFlag.AlignCenter, "NÚCLEO\nBASE")
        
        # Dibujar módulos dinámicos
        modules = list(self.dynamic_modules.values())
        if not modules:
            modules = [
                {"name": "Gestor de Procesos", "status": "loaded", "removable": False},
                {"name": "Gestor de Memoria", "status": "loaded", "removable": False},
                {"name": "Planificación", "status": "loaded", "removable": True},
                {"name": "Interrupciones", "status": "loaded", "removable": True}
            ]
        
        # Módulos core (no removibles) arriba
        core_modules = [m for m in modules if not m.get("removable", True)]
        # Módulos opcionales (removibles) abajo
        optional_modules = [m for m in modules if m.get("removable", False)]
        
        # Dibujar módulos core
        y_offset_core = kernel_y - 50
        spacing = w // (len(core_modules) + 1) if core_modules else w // 2
        for i, module in enumerate(core_modules):
            mod_x = spacing * (i + 1) - 45
            mod_y = y_offset_core
            
            # Módulo core (azul más oscuro)
            painter.setBrush(QBrush(QColor(75, 0, 130)))  # Indigo
            painter.setPen(QPen(QColor(50, 0, 90), 2))
            painter.drawRoundedRect(mod_x, mod_y, 90, 40, 6, 6)
            
            painter.setPen(QColor(255, 255, 255))
            font_small = QFont("Arial", 7)
            painter.setFont(font_small)
            name = module.get("name", "Core").replace("Gestor de ", "").replace(" Core", "")
            painter.drawText(mod_x, mod_y, 90, 40, Qt.AlignmentFlag.AlignCenter, name)
            
            # Línea al núcleo
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.SolidLine))
            painter.drawLine(mod_x + 45, mod_y + 40, kernel_x + kernel_w // 2, kernel_y)
        
        # Dibujar módulos opcionales
        y_offset_opt = kernel_y + kernel_h + 10
        spacing_opt = w // (len(optional_modules) + 1) if optional_modules else w // 2
        for i, module in enumerate(optional_modules):
            mod_x = spacing_opt * (i + 1) - 45
            mod_y = y_offset_opt
            
            # Módulo opcional (púrpura más claro)
            status_color = QColor(186, 85, 211) if module.get("status") == "loaded" else QColor(200, 200, 200)
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(QColor(140, 60, 160), 2))
            painter.drawRoundedRect(mod_x, mod_y, 90, 40, 6, 6)
            
            painter.setPen(QColor(255, 255, 255))
            font_small = QFont("Arial", 7)
            painter.setFont(font_small)
            name = module.get("name", "Módulo").replace("Módulo de ", "").replace("Manejador de ", "")
            painter.drawText(mod_x, mod_y, 90, 40, Qt.AlignmentFlag.AlignCenter, name)
            
            # Indicador removible
            painter.setPen(QColor(255, 200, 0))
            painter.drawText(mod_x + 75, mod_y + 5, 15, 15, Qt.AlignmentFlag.AlignCenter, "⚡")
            
            # Línea al núcleo
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
            painter.drawLine(mod_x + 45, mod_y, kernel_x + kernel_w // 2, kernel_y + kernel_h)

