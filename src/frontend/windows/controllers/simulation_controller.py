"""
Simulation Controller - Maneja el control de la simulación.
Principio SRP: Solo se encarga del control de la simulación (pause, resume, restart, speed).
"""
from typing import Callable, Optional, List
from PyQt6.QtCore import QTimer


class SimulationController:
    """
    Controlador que gestiona el estado y flujo de la simulación.
    Sigue el principio de responsabilidad única (SRP).
    """
    
    def __init__(self, engine, timer: QTimer):
        self.engine = engine
        self.timer = timer
        self._tick_callbacks: List[Callable] = []
        self._state_change_callbacks: List[Callable[[bool], None]] = []
        self._log_callback: Optional[Callable[[str], None]] = None
        
        # Conectar el timer al tick
        self.timer.timeout.connect(self._on_tick)
        
    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """Establece el callback para logging de mensajes."""
        self._log_callback = callback
        
    def add_tick_callback(self, callback: Callable) -> None:
        """
        Agrega un callback que se ejecutará en cada tick.
        Principio OCP: Permite agregar comportamiento sin modificar la clase.
        """
        self._tick_callbacks.append(callback)
        
    def remove_tick_callback(self, callback: Callable) -> None:
        """Elimina un callback de tick."""
        if callback in self._tick_callbacks:
            self._tick_callbacks.remove(callback)
            
    def add_state_change_callback(self, callback: Callable[[bool], None]) -> None:
        """Agrega un callback que se ejecuta cuando cambia el estado de la simulación."""
        self._state_change_callbacks.append(callback)
        
    def _on_tick(self) -> None:
        """Ejecuta un tick de la simulación y notifica a los observers."""
        self.engine.tick()
        for callback in self._tick_callbacks:
            callback()
            
    def _notify_state_change(self, is_running: bool) -> None:
        """Notifica a los observers sobre el cambio de estado."""
        for callback in self._state_change_callbacks:
            callback(is_running)
            
    def _log(self, message: str) -> None:
        """Loguea un mensaje si hay callback configurado."""
        if self._log_callback:
            self._log_callback(message)
            
    @property
    def is_running(self) -> bool:
        """Retorna si la simulación está corriendo."""
        return self.timer.isActive()
        
    def start(self, interval_ms: int = 1000) -> None:
        """Inicia la simulación con el intervalo especificado."""
        self.timer.start(interval_ms)
        self.engine.is_running = True
        self._log("Simulación iniciada.")
        self._notify_state_change(True)
        
    def pause(self) -> None:
        """Pausa la simulación."""
        self.timer.stop()
        self.engine.is_running = False
        self._log("Simulación pausada.")
        self._notify_state_change(False)
        
    def resume(self, interval_ms: Optional[int] = None) -> None:
        """Reanuda la simulación."""
        if interval_ms:
            self.timer.start(interval_ms)
        else:
            self.timer.start()
        self.engine.is_running = True
        self._log("Simulación reanudada.")
        self._notify_state_change(True)
        
    def toggle(self, interval_ms: int = 1000) -> None:
        """Alterna entre pausar y reanudar la simulación."""
        if self.is_running:
            self.pause()
        else:
            self.resume(interval_ms)
            
    def restart(self) -> None:
        """Reinicia la simulación."""
        self.pause()
        self.engine.reset()
        self._log("Simulación reiniciada.")
        
    def set_speed(self, interval_ms: int) -> None:
        """Establece la velocidad de la simulación (intervalo del timer)."""
        self.timer.setInterval(interval_ms)
        
    def get_interval(self) -> int:
        """Retorna el intervalo actual del timer."""
        return self.timer.interval()
