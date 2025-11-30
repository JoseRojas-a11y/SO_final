from dataclasses import dataclass, field
from typing import Optional
import itertools
import random

_process_id_counter = itertools.count(1)

@dataclass
class Process:
    name: str
    size_mb: int
    cpu_usage: float = 0.0  # porcentaje 0-100
    memory_usage_mb: int = 0  # asignado real
    duration_ticks: int = 0
    remaining_ticks: int = 0
    pid: int = field(default_factory=lambda: next(_process_id_counter))
    state: str = "NEW"  # NEW, READY, RUNNING, WAITING, TERMINATED
    
    # Scheduling attributes
    priority: int = 0  # Lower is higher priority (or vice versa, we'll define)
    arrival_tick: int = 0
    start_tick: Optional[int] = None
    finish_tick: Optional[int] = None
    waiting_ticks: int = 0
    cpu_id: Optional[int] = None  # ID of the CPU running this process
    quantum_used: int = 0 # Ticks used in current quantum (for RR)
    
    def tick(self):
        if self.state == "TERMINATED":
            return
            
        if self.state == "RUNNING":
            self.remaining_ticks -= 1
            if self.remaining_ticks <= 0:
                self.remaining_ticks = 0
                self.state = "TERMINATED"

        # Simular fluctuación CPU
        self.cpu_usage = max(0.0, min(100.0, self.cpu_usage + random.uniform(-10, 10)))
        # Logic moved to Engine/Scheduler to control execution flow


@dataclass
class MemoryBlock:
    start: int
    end: int
    process_pid: Optional[int] = None

    @property
    def size(self) -> int:
        return self.end - self.start

    @property
    def free(self) -> bool:
        return self.process_pid is None


@dataclass
class Page:
    """Representa una página de memoria física."""
    frame_number: int  # Número de frame físico
    process_pid: Optional[int] = None  # Proceso que la ocupa
    page_number: Optional[int] = None  # Número de página lógica del proceso
    last_accessed: int = 0  # Tick de último acceso (para LRU)
    loaded_tick: int = 0  # Tick cuando se cargó (para FIFO)
    referenced: bool = False  # Bit de referencia (para algoritmos de reemplazo)
    modified: bool = False  # Bit de modificación (dirty bit)

    @property
    def free(self) -> bool:
        return self.process_pid is None


@dataclass
class PageTableEntry:
    """Entrada en la tabla de páginas de un proceso."""
    page_number: int  # Número de página lógica
    frame_number: Optional[int] = None  # Frame físico asignado (None = no en memoria)
    valid: bool = False  # Bit válido (presente en memoria física)
    referenced: bool = False
    modified: bool = False
    loaded_tick: int = 0
    last_accessed: int = 0