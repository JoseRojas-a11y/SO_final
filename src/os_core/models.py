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
    memory_unit_id: Optional[int] = None  # unidad de memoria asignada
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
    io_probability: float = 0.15  # Probabilidad de solicitar I/O en un tick
    syscall_probability: float = 0.05  # Probabilidad de generar una interrupción de software
    hardware_interrupt_probability: float = 0.02  # Sensibilidad a interrupciones de hardware
    last_interrupt_tick: Optional[int] = None
    
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
class CPU:
    """Representa una CPU lógica con soporte de hilos internos."""
    id: int
    thread_capacity: int = 2  # Número máximo de hilos paralelos
    threads_in_use: int = 0
    process: Optional[Process] = None

    def assign(self, process: Process):
        self.process = process
        self.threads_in_use = self.thread_capacity if process is not None else 0
        if process is not None:
            process.cpu_id = self.id
            process.state = "RUNNING"
            process.quantum_used = 0

    def release(self):
        if self.process:
            self.process.cpu_id = None
        self.process = None
        self.threads_in_use = 0

    def tick(self):
        """Avanza la ejecución del proceso usando los hilos disponibles."""
        if not self.process:
            return
        p = self.process
        if p.state != "RUNNING":
            return
        # Consumir tantos ticks como hilos activos (aceleración lineal)
        p.remaining_ticks -= max(1, self.threads_in_use)
        if p.remaining_ticks <= 0:
            p.remaining_ticks = 0
            p.state = "TERMINATED"
        # Ajuste de uso de CPU simulado
        p.cpu_usage = max(0.0, min(100.0, p.cpu_usage + random.uniform(-5, 5)))


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
