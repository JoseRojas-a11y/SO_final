"""
Navigation Controller - Maneja la lógica de navegación entre vistas.
Principio SRP: Solo se encarga de la navegación y selección de vistas.
"""
from typing import Dict, List, Callable, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox, QFrame, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt


class NavigationController:
    """
    Controlador de navegación que gestiona la selección y visualización de vistas.
    Sigue el principio de responsabilidad única (SRP).
    """
    
    def __init__(self, content_layout: QVBoxLayout, on_change_callback: Optional[Callable] = None):
        self.content_layout = content_layout
        self.on_change_callback = on_change_callback
        self.selection_order: List[str] = []
        self.checkboxes: Dict[str, QCheckBox] = {}
        self.scroll_areas: Dict[str, QScrollArea] = {}
        self.page_empty: Optional[QWidget] = None
        
    def set_empty_page(self, page: QWidget) -> None:
        """Establece la página vacía inicial."""
        self.page_empty = page
        
    def register_view(self, key: str, checkbox: QCheckBox, scroll_area: QScrollArea) -> None:
        """
        Registra una vista con su checkbox y scroll area asociados.
        Principio OCP: Permite agregar nuevas vistas sin modificar el código existente.
        """
        self.checkboxes[key] = checkbox
        self.scroll_areas[key] = scroll_area
        checkbox.stateChanged.connect(lambda: self._on_checkbox_changed(key))
        
    def _on_checkbox_changed(self, key: str) -> None:
        """Maneja el cambio de estado de un checkbox."""
        checkbox = self.checkboxes.get(key)
        if not checkbox:
            return
            
        if checkbox.isChecked():
            if key not in self.selection_order:
                self.selection_order.append(key)
        else:
            if key in self.selection_order:
                self.selection_order.remove(key)
                
        self._update_content_layout()
        
        if self.on_change_callback:
            self.on_change_callback()
            
    def _clear_layout(self) -> None:
        """Limpia el layout de contenido."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child:
                widget = child.widget()
                if widget:
                    widget.setParent(None)
                    
    def _hide_all_views(self) -> None:
        """Oculta todas las vistas registradas."""
        for scroll_area in self.scroll_areas.values():
            scroll_area.setVisible(False)
        if self.page_empty:
            self.page_empty.setVisible(False)
            
    def _create_divider(self) -> QFrame:
        """Crea un separador visual entre secciones."""
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: white; border: 2px solid white;")
        divider.setFixedHeight(3)
        return divider
        
    def _update_content_layout(self) -> None:
        """Actualiza el layout de contenido según las selecciones."""
        self._clear_layout()
        self._hide_all_views()
        
        if not self.selection_order:
            if self.page_empty:
                self.content_layout.addWidget(self.page_empty)
                self.page_empty.setVisible(True)
            return
            
        for i, key in enumerate(self.selection_order):
            # Agregar divisor si no es el primero
            if i > 0:
                self.content_layout.addWidget(self._create_divider())
                
            scroll_area = self.scroll_areas.get(key)
            if scroll_area:
                self.content_layout.addWidget(scroll_area, 1)
                scroll_area.setVisible(True)
                
    def get_selected_views(self) -> List[str]:
        """Retorna la lista de vistas seleccionadas en orden."""
        return self.selection_order.copy()
        
    def is_view_selected(self, key: str) -> bool:
        """Verifica si una vista está seleccionada."""
        return key in self.selection_order


class NavigationPanelBuilder:
    """
    Builder para construir el panel de navegación.
    Principio SRP: Solo se encarga de construir el panel de navegación.
    """
    
    @staticmethod
    def build(options: List[tuple[str, str]], controller: NavigationController) -> QGroupBox:
        """
        Construye el panel de navegación con las opciones especificadas.
        
        Args:
            options: Lista de tuplas (key, label) para cada opción
            controller: Controlador de navegación
            
        Returns:
            QGroupBox con los checkboxes de navegación
        """
        nav_group = QGroupBox("Opciones")
        nav_layout = QVBoxLayout(nav_group)
        nav_layout.setSpacing(2)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        
        for key, label in options:
            checkbox = QCheckBox(label)
            nav_layout.addWidget(checkbox)
            # El registro con scroll_area se hace externamente
            controller.checkboxes[key] = checkbox
            
        return nav_group
