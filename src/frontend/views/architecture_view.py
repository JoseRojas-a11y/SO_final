from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from typing import Dict, Optional

class ArchitectureView(QWidget):
    """Componente visual que muestra la arquitectura modular del sistema operativo."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.architecture = "Modular"
        self.kernel_mode = "modular"
        self.dynamic_modules: Dict[str, Dict] = {}
        self.setMinimumHeight(200)
        self.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc;")
        
    def update_architecture(self, architecture: str = "Modular", kernel_mode: str = "modular",
                            dynamic_modules: Optional[Dict] = None, **_: object):
        """Actualiza la visualización (modo Modular únicamente)."""
        # Forzamos modo Modular e ignoramos parámetros ajenos
        self.architecture = "Modular"
        self.kernel_mode = "modular"
        self.dynamic_modules = dynamic_modules or {}
        self.update()
        
    def paintEvent(self, event):
        """Dibuja la representación visual (solo arquitectura modular)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Fondo
        painter.fillRect(0, 0, w, h, QColor(245, 245, 245))
        self._draw_modular(painter, w, h)
            
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

