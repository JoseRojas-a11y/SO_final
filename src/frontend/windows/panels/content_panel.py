"""
Content Panel - Panel de contenido principal.
Principio SRP: Solo maneja el área de contenido principal.
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt


class ContentPanel(QWidget):
    """
    Panel contenedor del área de contenido principal.
    Principio SRP: Solo gestiona el contenedor de contenido.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(5, 5, 5, 5)
        self._content_layout.setSpacing(5)
        
    def get_layout(self) -> QVBoxLayout:
        """Retorna el layout para agregar widgets."""
        return self._content_layout


class EmptyPage(QWidget):
    """
    Página vacía que se muestra cuando no hay selección.
    Principio SRP: Solo muestra el mensaje de página vacía.
    """
    
    def __init__(
        self, 
        message: str = "Seleccione una opción para comenzar",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._setup_ui(message)
        
    def _setup_ui(self, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.addStretch()
        
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #666;")
        layout.addWidget(label)
        
        layout.addStretch()


class ScrollAreaFactory:
    """
    Factory para crear scroll areas consistentes.
    Principio SRP: Solo crea scroll areas.
    Principio OCP: Fácil de extender para diferentes estilos.
    """
    
    @staticmethod
    def create(
        widget: QWidget,
        visible: bool = False,
        frame_shape: QFrame.Shape = QFrame.Shape.NoFrame
    ) -> QScrollArea:
        """
        Crea un ScrollArea configurado consistentemente.
        
        Args:
            widget: Widget a envolver
            visible: Visibilidad inicial
            frame_shape: Forma del marco
            
        Returns:
            QScrollArea configurado
        """
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setVisible(visible)
        scroll.setFrameShape(frame_shape)
        return scroll
        
    @staticmethod
    def create_with_scrollbars(
        widget: QWidget,
        visible: bool = False,
        style: str = "QScrollArea { border: 1px solid #ccc; background-color: #f5f5f5; }"
    ) -> QScrollArea:
        """
        Crea un ScrollArea con scrollbars configuradas.
        
        Args:
            widget: Widget a envolver
            visible: Visibilidad inicial
            style: Estilo CSS
            
        Returns:
            QScrollArea configurado con scrollbars
        """
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(style)
        scroll.setVisible(visible)
        return scroll
