"""
Control Panel - Panel de control de simulación.
Principio SRP: Solo maneja los controles de la simulación.
"""
from typing import Callable, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout,
    QPushButton, QSpinBox, QLabel
)


class SimulationControlPanel(QWidget):
    """
    Panel con los controles de simulación (pause, resume, restart, speed).
    Principio SRP: Solo maneja la interfaz de controles.
    Principio DIP: Depende de callbacks, no de implementaciones concretas.
    """
    
    def __init__(
        self,
        on_toggle: Optional[Callable] = None,
        on_restart: Optional[Callable] = None,
        on_speed_changed: Optional[Callable[[int], None]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._on_toggle = on_toggle
        self._on_restart = on_restart
        self._on_speed_changed = on_speed_changed
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.group = QGroupBox("Control Simulación")
        controls_layout = QGridLayout(self.group)
        controls_layout.setSpacing(2)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        
        # Botón Pausar/Reanudar
        self.btn_toggle = QPushButton("Activar")
        self.btn_toggle.setStyleSheet("background-color: #00AA00; color: white;")
        self.btn_toggle.clicked.connect(self._handle_toggle)
        controls_layout.addWidget(self.btn_toggle, 0, 0)
        
        # Botón Reiniciar
        self.btn_restart = QPushButton("Reiniciar")
        self.btn_restart.setStyleSheet("background-color: #AA0000; color: white;")
        self.btn_restart.clicked.connect(self._handle_restart)
        controls_layout.addWidget(self.btn_restart, 0, 1)
        
        # Control de velocidad
        lbl_speed = QLabel("Duración de Tick (ms):")
        controls_layout.addWidget(lbl_speed, 1, 0)
        
        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(10, 5000)
        self.spin_speed.setValue(1000)
        self.spin_speed.setSingleStep(50)
        self.spin_speed.setEnabled(True)
        self.spin_speed.valueChanged.connect(self._handle_speed_changed)
        controls_layout.addWidget(self.spin_speed, 1, 1)
        
        layout.addWidget(self.group)
        
    def _handle_toggle(self) -> None:
        """Maneja el click en el botón toggle."""
        if self._on_toggle:
            self._on_toggle()
            
    def _handle_restart(self) -> None:
        """Maneja el click en el botón restart."""
        if self._on_restart:
            self._on_restart()
            
    def _handle_speed_changed(self, value: int) -> None:
        """Maneja el cambio de velocidad."""
        if self._on_speed_changed:
            self._on_speed_changed(value)
            
    def set_running_state(self) -> None:
        """Actualiza la UI para estado 'corriendo'."""
        self.btn_toggle.setText("Pausar")
        self.spin_speed.setEnabled(False)
        
    def set_paused_state(self) -> None:
        """Actualiza la UI para estado 'pausado'."""
        self.btn_toggle.setText("Reanudar")
        self.spin_speed.setEnabled(True)
        
    def set_initial_state(self) -> None:
        """Actualiza la UI para estado inicial."""
        self.btn_toggle.setText("Activar")
        self.spin_speed.setEnabled(True)
        
    def get_speed(self) -> int:
        """Retorna la velocidad actual en ms."""
        return self.spin_speed.value()
        
    def set_speed(self, ms: int) -> None:
        """Establece la velocidad sin disparar el callback."""
        self.spin_speed.blockSignals(True)
        self.spin_speed.setValue(ms)
        self.spin_speed.blockSignals(False)


class FinishButton(QWidget):
    """
    Botón para finalizar la simulación.
    Principio SRP: Solo maneja la acción de finalizar.
    """
    
    def __init__(self, on_finish: Optional[Callable] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._on_finish = on_finish
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn = QPushButton("Finalizar Programa")
        self.btn.setStyleSheet(
            "background-color: #d32f2f; color: white; font-weight: bold; padding: 5px;"
        )
        self.btn.clicked.connect(self._handle_click)
        layout.addWidget(self.btn)
        
    def _handle_click(self) -> None:
        """Maneja el click en el botón."""
        if self._on_finish:
            self._on_finish()
