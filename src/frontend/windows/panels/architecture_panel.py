"""
Architecture Panels - Paneles relacionados con la visualización de arquitectura.
Principio SRP: Cada panel tiene una única responsabilidad de visualización.
Principio ISP: Interfaces específicas para cada tipo de panel.
"""
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QListWidget, 
    QListWidgetItem, QAbstractItemView
)
from PyQt6.QtGui import QColor


class ArchitectureStatusPanel(QWidget):
    """
    Panel que muestra el estado actual de la arquitectura.
    Principio SRP: Solo muestra información de estado.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.group = QGroupBox("📊 Estado de Arquitectura")
        group_layout = QVBoxLayout(self.group)
        group_layout.setSpacing(2)
        group_layout.setContentsMargins(4, 4, 4, 4)
        
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 10px;")
        group_layout.addWidget(self.status_label)
        
        layout.addWidget(self.group)
        
    def update_status(self, text: str) -> None:
        """Actualiza el texto de estado."""
        self.status_label.setText(text)
        
    def set_waiting_status(self) -> None:
        """Muestra estado de espera."""
        self.status_label.setText("Esperando inicio de simulación...")
        
    def set_modular_status(self, modules_count: int = 3, submodules_count: int = 4) -> None:
        """Configura el estado para arquitectura modular."""
        text = "<b>📊 Estado Modular</b><br>"
        text += f"• Núcleo base: <b>ACTIVO</b><br>"
        text += f"• Módulos totales: <b>{modules_count}</b><br>"
        text += f"• Submódulos totales: <b>{submodules_count}</b>"
        self.status_label.setText(text)
        
    def set_generic_status(self, modules_count: int) -> None:
        """Configura el estado genérico."""
        text = "<b>📊 Estado Modular</b><br>"
        text += f"• Núcleo base: <b>ACTIVO</b><br>"
        text += f"• Módulos totales: <b>{modules_count}</b><br>"
        self.status_label.setText(text)


class ModulesPanel(QWidget):
    """
    Panel que muestra la lista de módulos del sistema.
    Principio SRP: Solo muestra la lista de módulos.
    """
    
    def __init__(self, title: str = "🔧 Módulos del Sistema", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.group = QGroupBox(self.title)
        group_layout = QVBoxLayout(self.group)
        group_layout.setSpacing(2)
        group_layout.setContentsMargins(4, 4, 4, 4)
        
        self.modules_list = QListWidget()
        self.modules_list.setMaximumHeight(120)
        self.modules_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        group_layout.addWidget(self.modules_list)
        
        layout.addWidget(self.group)
        
    def clear(self) -> None:
        """Limpia la lista de módulos."""
        self.modules_list.clear()
        
    def add_module(self, name: str, icon: str = "🔒", submodules: Optional[List[str]] = None) -> None:
        """
        Agrega un módulo con sus submódulos opcionales.
        Principio OCP: Permite agregar módulos sin modificar la estructura.
        """
        item = QListWidgetItem(f"{icon} {name}")
        self.modules_list.addItem(item)
        
        if submodules:
            for sub in submodules:
                sub_item = QListWidgetItem(f"    • {sub}")
                self.modules_list.addItem(sub_item)
                
    def set_modules_structure(self, structure: List[tuple]) -> None:
        """
        Establece la estructura completa de módulos.
        
        Args:
            structure: Lista de tuplas (nombre, icono, [submódulos])
        """
        self.clear()
        for name, icon, submodules in structure:
            self.add_module(name, icon, submodules)


class ExternalModulesPanel(QWidget):
    """
    Panel para módulos externos (Microkernel).
    Principio SRP: Solo muestra módulos externos.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.group = QGroupBox("🔌 Módulos Externos")
        group_layout = QVBoxLayout(self.group)
        group_layout.setSpacing(2)
        group_layout.setContentsMargins(4, 4, 4, 4)
        
        group_layout.addWidget(QLabel("Servicios Externos:"))
        
        self.modules_list = QListWidget()
        self.modules_list.setMaximumHeight(70)
        group_layout.addWidget(self.modules_list)
        
        layout.addWidget(self.group)
        
    def clear(self) -> None:
        """Limpia la lista."""
        self.modules_list.clear()
        
    def add_module(self, name: str) -> None:
        """Agrega un módulo externo."""
        self.modules_list.addItem(name)


class LayerFlowPanel(QWidget):
    """
    Panel que muestra el flujo entre capas (arquitectura modular).
    Principio SRP: Solo muestra el flujo entre capas.
    """
    
    MAX_EVENTS = 5
    
    # Mapeo de colores por tipo de acción
    ACTION_COLORS = {
        'alloc': QColor(220, 237, 255),      # Azul claro - memoria
        'memory': QColor(220, 237, 255),
        'dispatch': QColor(220, 255, 220),   # Verde claro - procesos
        'ready': QColor(220, 255, 220),
        'io': QColor(255, 247, 220),         # Amarillo claro - I/O
        'syscall': QColor(255, 247, 220),
        'load': QColor(255, 220, 237),       # Rosa claro - módulos
        'unload': QColor(255, 220, 237),
        'default': QColor(245, 245, 245)     # Gris claro
    }
    
    # Mapeo de iconos por tipo de acción
    ACTION_ICONS = {
        'alloc': '💾',
        'dispatch': '▶️',
        'ready': '✅',
        'syscall': '🔧',
        'io_req': '📥',
        'load': '⬆️',
        'unload': '⬇️'
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.group = QGroupBox("📡 Flujo entre Capas (Modular)")
        group_layout = QVBoxLayout(self.group)
        group_layout.setSpacing(2)
        group_layout.setContentsMargins(4, 4, 4, 4)
        
        group_layout.addWidget(QLabel("Últimas interacciones (máx. 5):"))
        
        self.flow_list = QListWidget()
        self.flow_list.setMaximumHeight(120)
        self.flow_list.setWordWrap(True)
        group_layout.addWidget(self.flow_list)
        
        layout.addWidget(self.group)
        
    def clear(self) -> None:
        """Limpia la lista de eventos."""
        self.flow_list.clear()
        
    def _format_action(self, action: str) -> str:
        """Formatea la acción para mostrar información relevante."""
        if ':' not in action:
            return action
            
        action_type, action_data = action.split(':', 1)
        
        action_labels = {
            'alloc': f"Asignar memoria PID:{action_data}",
            'dispatch': f"Despachar proceso PID:{action_data}",
            'ready': f"Marcar listo PID:{action_data}",
            'syscall': f"Syscall PID:{action_data}",
            'io_req': f"Solicitud I/O PID:{action_data}",
            'load': f"Cargar módulo: {action_data}",
            'unload': f"Descargar módulo: {action_data}"
        }
        
        icon = self.ACTION_ICONS.get(action_type, '')
        label = action_labels.get(action_type, action)
        
        return f"{icon} {label}" if icon else label
        
    def _get_action_color(self, action: str) -> QColor:
        """Obtiene el color según el tipo de acción."""
        action_lower = action.lower()
        
        for key, color in self.ACTION_COLORS.items():
            if key in action_lower:
                return color
                
        return self.ACTION_COLORS['default']
        
    def update_events(self, events: List[Dict[str, Any]]) -> None:
        """
        Actualiza la lista de eventos.
        
        Args:
            events: Lista de eventos con keys: tick, source, target, action
        """
        self.clear()
        
        # Tomar solo los últimos MAX_EVENTS eventos
        recent_events = events[-self.MAX_EVENTS:] if events else []
        
        for ev in recent_events:
            tick = ev.get('tick', '?')
            source = ev.get('source', '?')
            target = ev.get('target', '?')
            action = ev.get('action', '?')
            
            action_display = self._format_action(action)
            item_text = f"[Tick {tick}] {source} → {target}\n   {action_display}"
            
            item = QListWidgetItem(item_text)
            item.setForeground(QColor(0, 0, 0))  # Texto negro
            item.setBackground(self._get_action_color(action))
            
            self.flow_list.addItem(item)
            
        self.flow_list.scrollToBottom()
