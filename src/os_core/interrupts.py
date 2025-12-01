from __future__ import annotations

import itertools
import heapq
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - referenced for type checking only
    from ..simulation.engine import SimulationEngine
    from .models import Process


class InterruptType(str, Enum):
    """Tipos de interrupciones soportadas en la simulación."""

    IO = "IO"
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    SYSCALL = "SYSCALL"
    TIMER = "TIMER"
    PAGE_FAULT = "PAGE_FAULT"


@dataclass
class Interrupt:
    """Representa una interrupción generada durante la simulación."""

    interrupt_type: InterruptType
    source: str
    pid: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Valores bajos = mayor prioridad


class InterruptController:
    """Centraliza la gestión de interrupciones pendientes."""

    def __init__(self) -> None:
        self._pending: List[Tuple[int, int, Interrupt]] = []
        self._sequence = itertools.count()

    def raise_interrupt(self, interrupt: Interrupt) -> None:
        heapq.heappush(self._pending, (interrupt.priority, next(self._sequence), interrupt))

    def fetch_next(self) -> Optional[Interrupt]:
        if not self._pending:
            return None
        _, _, interrupt = heapq.heappop(self._pending)
        return interrupt

    def has_pending(self) -> bool:
        return bool(self._pending)

    def clear(self) -> None:
        self._pending.clear()


class InterruptHandler:
    """Cadena de responsabilidad para atender interrupciones."""

    def __init__(self, successor: Optional["InterruptHandler"] = None) -> None:
        self._successor = successor

    def handle(self, interrupt: Interrupt, engine: "SimulationEngine") -> None:
        if self.can_handle(interrupt):
            self.process(interrupt, engine)
        elif self._successor is not None:
            self._successor.handle(interrupt, engine)

    def can_handle(self, interrupt: Interrupt) -> bool:
        raise NotImplementedError

    def process(self, interrupt: Interrupt, engine: "SimulationEngine") -> None:
        raise NotImplementedError


class IOInterruptHandler(InterruptHandler):
    """Gestiona interrupciones de entrada/salida."""

    def can_handle(self, interrupt: Interrupt) -> bool:
        return interrupt.interrupt_type in {InterruptType.IO}

    def process(self, interrupt: Interrupt, engine: "SimulationEngine") -> None:
        if interrupt.pid is None:
            return
        process = engine.get_process(interrupt.pid)
        if process is None:
            return

        duration = interrupt.payload.get("io_duration", engine.default_io_duration())
        reason = interrupt.payload.get("reason", interrupt.interrupt_type.value)
        engine.set_process_waiting(process, reason, duration)


class SyscallInterruptHandler(InterruptHandler):
    """Gestiona interrupciones de software o syscalls."""

    def can_handle(self, interrupt: Interrupt) -> bool:
        return interrupt.interrupt_type in {InterruptType.SYSCALL, InterruptType.SOFTWARE}

    def process(self, interrupt: Interrupt, engine: "SimulationEngine") -> None:
        if interrupt.pid is None:
            return
        process = engine.get_process(interrupt.pid)
        if process is None:
            return

        duration = interrupt.payload.get("syscall_duration", engine.default_syscall_duration())
        reason = interrupt.payload.get("reason", interrupt.interrupt_type.value)
        engine.set_process_waiting(process, reason, duration)


class HardwareInterruptHandler(InterruptHandler):
    """Gestiona interrupciones de hardware (timer, fallos de página, etc.)."""

    def can_handle(self, interrupt: Interrupt) -> bool:
        return interrupt.interrupt_type in {
            InterruptType.HARDWARE,
            InterruptType.TIMER,
            InterruptType.PAGE_FAULT,
        }

    def process(self, interrupt: Interrupt, engine: "SimulationEngine") -> None:
        if interrupt.pid is None:
            engine.handle_global_interrupt(interrupt)
            return

        process = engine.get_process(interrupt.pid)
        if process is None:
            return

        if interrupt.interrupt_type == InterruptType.PAGE_FAULT:
            duration = interrupt.payload.get("page_fault_duration", engine.default_page_fault_duration())
            reason = interrupt.payload.get("reason", "PAGE_FAULT")
            engine.set_process_waiting(process, reason, duration)
        else:
            reason = interrupt.payload.get("reason", interrupt.interrupt_type.value)
            requeue = interrupt.payload.get("requeue", True)
            engine.preempt_process(process, reason, requeue=bool(requeue))


def build_default_handler_chain() -> InterruptHandler:
    """Construye una cadena de handlers con prioridad IO -> Syscall -> Hardware."""

    return IOInterruptHandler(SyscallInterruptHandler(HardwareInterruptHandler()))
