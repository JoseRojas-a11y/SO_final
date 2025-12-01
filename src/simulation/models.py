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
    io_remaining_ticks: int = 0  # Ticks restantes de I/O cuando está en WAITING
    io_total_ticks: int = 0  # Ticks totales de I/O asignados
    interrupt_type: Optional[str] = None  # Tipo de interrupción actual (IO, SEMAPHORE_BLOCK, etc.)
    
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
