from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .interrupts import (
    Interrupt,
    InterruptController,
    InterruptHandler,
    InterruptType,
    build_default_handler_chain,
)

if TYPE_CHECKING:  # pragma: no cover - referenced for type checking only
    from ..simulation.engine import SimulationEngine


class OSArchitecture:
    """Define la interfaz pública para las arquitecturas del simulador."""

    def __init__(
        self,
        name: str,
        controller: InterruptController,
        handler: Optional[InterruptHandler] = None,
    ) -> None:
        self.name = name
        self.controller = controller
        self.handler = handler or build_default_handler_chain()

    def before_tick(self, engine: "SimulationEngine", current_tick: int) -> None:
        """Hook opcional ejecutado antes de procesar un tick."""

    def after_tick(self, engine: "SimulationEngine", current_tick: int) -> None:
        """Procesa interrupciones pendientes tras ejecutar el tick."""
        self.process_pending_interrupts(engine, current_tick)

    def process_pending_interrupts(self, engine: "SimulationEngine", current_tick: int) -> None:
        while self.controller.has_pending():
            interrupt = self.controller.fetch_next()
            if interrupt is None:
                break
            self.handle_interrupt(interrupt, engine, current_tick)

    def handle_interrupt(
        self,
        interrupt: Interrupt,
        engine: "SimulationEngine",
        current_tick: int,
    ) -> None:
        self.handler.handle(interrupt, engine)


class MonolithicArchitecture(OSArchitecture):
    """Atiende interrupciones de forma inmediata en modo kernel."""

    def __init__(self, controller: InterruptController) -> None:
        super().__init__("Monolithic", controller)


class MicrokernelArchitecture(OSArchitecture):
    """Ajusta la duración de servicio al delegar en servidores de espacio usuario."""

    def __init__(self, controller: InterruptController, kernel_latency: int = 2) -> None:
        super().__init__("Microkernel", controller)
        self.kernel_latency = max(1, kernel_latency)

    def handle_interrupt(
        self,
        interrupt: Interrupt,
        engine: "SimulationEngine",
        current_tick: int,
    ) -> None:
        if interrupt.pid is not None:
            if interrupt.interrupt_type == InterruptType.IO:
                base = interrupt.payload.get("io_duration", engine.default_io_duration())
                interrupt.payload["io_duration"] = base + self.kernel_latency
            elif interrupt.interrupt_type in {InterruptType.SYSCALL, InterruptType.SOFTWARE}:
                base = interrupt.payload.get("syscall_duration", engine.default_syscall_duration())
                interrupt.payload["syscall_duration"] = base + self.kernel_latency
            elif interrupt.interrupt_type == InterruptType.PAGE_FAULT:
                base = interrupt.payload.get(
                    "page_fault_duration", engine.default_page_fault_duration()
                )
                interrupt.payload["page_fault_duration"] = base + self.kernel_latency
        engine.log_interrupt(
            f"[Microkernel] Atendiendo interrupción {interrupt.interrupt_type.value} con latencia adicional de {self.kernel_latency} ticks."
        )
        super().handle_interrupt(interrupt, engine, current_tick)


class ModularArchitecture(OSArchitecture):
    """Modelo híbrido que aplica penalización ligera a interrupciones de hardware."""

    def __init__(self, controller: InterruptController, hardware_delay: int = 1) -> None:
        super().__init__("Modular", controller)
        self.hardware_delay = max(0, hardware_delay)

    def handle_interrupt(
        self,
        interrupt: Interrupt,
        engine: "SimulationEngine",
        current_tick: int,
    ) -> None:
        if (
            interrupt.pid is not None
            and interrupt.interrupt_type in {InterruptType.HARDWARE, InterruptType.TIMER, InterruptType.PAGE_FAULT}
        ):
            base = interrupt.payload.get(
                "page_fault_duration", engine.default_page_fault_duration()
            )
            if interrupt.interrupt_type == InterruptType.PAGE_FAULT:
                interrupt.payload["page_fault_duration"] = base + self.hardware_delay
            else:
                interrupt.payload["reason"] = interrupt.payload.get("reason", interrupt.interrupt_type.value)
                interrupt.payload["hardware_delay"] = self.hardware_delay
        engine.log_interrupt(
            f"[Modular] Interrupción {interrupt.interrupt_type.value} gestionada con retardo de {self.hardware_delay} ticks."
        )
        super().handle_interrupt(interrupt, engine, current_tick)


class ArchitectureFactory:
    """Fábrica para crear arquitecturas según configuración del usuario."""

    @staticmethod
    def create(name: str, controller: InterruptController) -> OSArchitecture:
        # Forzamos arquitectura Modular para simplificar y evitar ramas legacy
        return ModularArchitecture(controller)
