import random
import time
import hashlib
from typing import Dict, List, Optional
from .models import Process
from .memory.manager import MemoryManager, AllocationResult, MemoryBlock
from .memory.strategies import FirstFitStrategy, BestFitStrategy, WorstFitStrategy
from .metrics import SimulationMetrics
from .scheduler import Scheduler, FCFS, SJF, SRTF, RoundRobin

INTERRUPCIONES_WAITING = [
    "IO",
    "SEMAPHORE_BLOCK",
    "JOIN_WAIT",
    "COND_WAIT",
    "PAGE_FAULT",
]

def probabilidad_interrupcion(pid: int, tick: int) -> float:
    """Calcula la probabilidad de interrupción basada en hash del PID y tick."""
    key = f"{pid}-{tick}"
    h = hashlib.sha256(key.encode()).hexdigest()
    x = int(h[:8], 16)   # tomamos 32 bits del hash
    return x / 0xFFFFFFFF

def tiempo_io(pid: int, min_io: int = 3, max_io: int = 15) -> int:
    """Calcula el tiempo de I/O basado en hash del PID."""
    h = hashlib.sha256(str(pid).encode()).hexdigest()
    x = int(h[:8], 16)                      # 32 bits del hash
    r = x % (max_io - min_io + 1)
    return min_io + r

def tipo_interrupcion(pid: int, tick: int, seed: int = 0) -> str:
    """
    Devuelve determinísticamente un tipo de interrupción
    que enviará al proceso a la cola Waiting.
    """
    # Mezcla PID, tick y semilla
    clave = f"{pid}-{tick}-{seed}"
    
    # Hash SHA-256 (determinista)
    h = hashlib.sha256(clave.encode()).hexdigest()
    
    # Usamos 32 bits del hash para pseudoaleatoriedad
    x = int(h[:8], 16)
    
    # Seleccionamos un tipo de interrupción en la lista
    idx = x % len(INTERRUPCIONES_WAITING)
    
    return INTERRUPCIONES_WAITING[idx]

INTERRUPCIONES_WAITING = [
    "IO",
    "SEMAPHORE_BLOCK",
    "JOIN_WAIT",
    "COND_WAIT",
    "PAGE_FAULT",
]

def probabilidad_interrupcion(pid: int, tick: int) -> float:
    """Calcula la probabilidad de interrupción basada en hash del PID y tick."""
    key = f"{pid}-{tick}"
    h = hashlib.sha256(key.encode()).hexdigest()
    x = int(h[:8], 16)   # tomamos 32 bits del hash
    return x / 0xFFFFFFFF

def tiempo_io(pid: int, min_io: int = 3, max_io: int = 15) -> int:
    """Calcula el tiempo de I/O basado en hash del PID."""
    h = hashlib.sha256(str(pid).encode()).hexdigest()
    x = int(h[:8], 16)                      # 32 bits del hash
    r = x % (max_io - min_io + 1)
    return min_io + r

def tipo_interrupcion(pid: int, tick: int, seed: int = 0) -> str:
    """
    Devuelve determinísticamente un tipo de interrupción
    que enviará al proceso a la cola Waiting.
    """
    # Mezcla PID, tick y semilla
    clave = f"{pid}-{tick}-{seed}"
    
    # Hash SHA-256 (determinista)
    h = hashlib.sha256(clave.encode()).hexdigest()
    
    # Usamos 32 bits del hash para pseudoaleatoriedad
    x = int(h[:8], 16)
    
    # Seleccionamos un tipo de interrupción en la lista
    idx = x % len(INTERRUPCIONES_WAITING)
    
    return INTERRUPCIONES_WAITING[idx]

class SimulationEngine:
    def __init__(self, total_memory_mb: int = 256, architecture: str = "Monolithic", scheduling_alg: str = "FCFS", quantum: int = 4):
        self.managers: Dict[str, MemoryManager] = {
            'first': MemoryManager(total_memory_mb, 'first', FirstFitStrategy()),
            'best': MemoryManager(total_memory_mb, 'best', BestFitStrategy()),
            'worst': MemoryManager(total_memory_mb, 'worst', WorstFitStrategy())
        }
        self.processes: Dict[int, Process] = {}
        self.metrics = SimulationMetrics()
        self.tick_count = 0
        self.max_process_duration = 50  # ticks
        self.terminated_cleanup_delay = 10  # ticks que un proceso terminado permanece antes de ser eliminado
        self.new_state_delay = 2  # ticks que un proceso permanece en NEW antes de pasar a READY (para visibilidad)
        
        self.architecture = architecture
        self.scheduling_alg_name = scheduling_alg
        self.quantum = quantum
        self.auto_create_processes = True
        
        # Multiprocessor: 4 CPUs
        self.cpus: List[Optional[Process]] = [None] * 4
        self.interrupt_log: List[str] = []
        
        # Initialize Scheduler
        if scheduling_alg == "FCFS":
            self.scheduler = FCFS()
        elif scheduling_alg == "SJF":
            self.scheduler = SJF()
        elif scheduling_alg == "SRTF":
            self.scheduler = SRTF()
        elif scheduling_alg == "RR":
            self.scheduler = RoundRobin(quantum=quantum)
        else:
            self.scheduler = FCFS() # Default

    def log_interrupt(self, message: str):
        timestamp = f"[Tick {self.tick_count}]"
        self.interrupt_log.append(f"{timestamp} {message}")
        if len(self.interrupt_log) > 50:
            self.interrupt_log.pop(0)

    def manual_create_process(self, size_mb: int, duration: int) -> Process:
        p = Process(name=f"P{len(self.processes)+1}", size_mb=size_mb, cpu_usage=random.uniform(5,40), duration_ticks=duration, remaining_ticks=duration)
        p.arrival_tick = self.tick_count
        p.state = "NEW"
        self.processes[p.pid] = p
        self.metrics.total_processes += 1
        
        allocated = False
        for alg, manager in self.managers.items():
            result = manager.allocate(p)
            self.metrics.update(result)
            if alg == 'first' and result.success:
                allocated = True
        
        if allocated:
<<<<<<< HEAD
            # El proceso permanece en NEW hasta el siguiente tick, cuando se moverá a READY
            # No llamamos a scheduler.add_process aquí, se hará en update_processes
            self.log_interrupt(f"Process {p.name} created manually (Priority: {p.priority}) - Estado: NEW.")
=======
            self.scheduler.add_process(p)
            self.log_interrupt(f"Process {p.name} created manually.")
>>>>>>> 18b1958ee925fa5f293a0219bb80f68dc7a53770
        else:
            p.state = "TERMINATED"
            p.finish_tick = self.tick_count  # Establecer finish_tick para que pueda ser eliminado después
            self.log_interrupt(f"Process {p.name} creation failed (Memory Full).")
            # Release memory from any manager that might have allocated (e.g. best/worst) even if first failed
            for manager in self.managers.values():
                manager.release(p)
            
        return p

    def create_process(self) -> Process:
        size = random.randint(4, 64)  # MB
        duration = random.randint(20, self.max_process_duration)
        p = Process(name=f"P{len(self.processes)+1}", size_mb=size, cpu_usage=random.uniform(5,40), duration_ticks=duration, remaining_ticks=duration)
        p.arrival_tick = self.tick_count
        p.state = "NEW"
        
        self.processes[p.pid] = p
        self.metrics.total_processes += 1
        
        allocated = False
        for alg, manager in self.managers.items():
            result = manager.allocate(p)
            self.metrics.update(result)
            if alg == 'first' and result.success:
                allocated = True
        
        if allocated:
<<<<<<< HEAD
            # El proceso permanece en NEW hasta el siguiente tick, cuando se moverá a READY
            # No llamamos a scheduler.add_process aquí, se hará en update_processes
            self.log_interrupt(f"Process {p.name} created (Auto, Priority: {p.priority}) - Estado: NEW.")
=======
            self.scheduler.add_process(p)
            self.log_interrupt(f"Process {p.name} created (Auto).")
>>>>>>> 18b1958ee925fa5f293a0219bb80f68dc7a53770
        else:
            p.state = "TERMINATED" # Rejected due to memory
            p.finish_tick = self.tick_count  # Establecer finish_tick para que pueda ser eliminado después
            # Release memory from any manager that might have allocated (e.g. best/worst) even if first failed
            for manager in self.managers.values():
                manager.release(p)
            
        return p

    def release_process(self, p: Process):
        for manager in self.managers.values():
            manager.release(p)
        p.state = "TERMINATED"
        p.finish_tick = self.tick_count
        self.metrics.record_process_completion(p, self.tick_count)
        self.log_interrupt(f"Process {p.name} terminated.")

    def update_processes(self):
        # Multiprocessor Scheduling Logic
        # We have 4 CPUs. We need to fill them from the scheduler.
        
<<<<<<< HEAD
        # 0. Cleanup terminated processes (eliminar de la cola TERMINATED después de un tiempo)
        terminated_to_remove = []
        for pid, p in list(self.processes.items()):
            if p.state == "TERMINATED":
                # Usar finish_tick si está disponible, sino usar arrival_tick como fallback
                termination_tick = p.finish_tick if p.finish_tick is not None else p.arrival_tick
                ticks_since_termination = self.tick_count - termination_tick
                if ticks_since_termination >= self.terminated_cleanup_delay:
                    terminated_to_remove.append(pid)
        
        for pid in terminated_to_remove:
            p = self.processes[pid]
            del self.processes[pid]
            self.log_interrupt(f"Process {p.name} (PID {p.pid}) eliminado de la cola TERMINATED.")
        
        # 0.1. Move NEW processes to READY (transición de NEW a READY después de un delay)
        for p in list(self.processes.values()):
            if p.state == "NEW":
                # Calcular cuántos ticks ha estado en NEW
                ticks_in_new = self.tick_count - p.arrival_tick
                # Solo mover a READY después del delay para que sea visible
                if ticks_in_new >= self.new_state_delay:
                    # Mover proceso de NEW a READY y agregarlo al scheduler
                    p.state = "READY"
                    self.scheduler.add_process(p)
                    self.log_interrupt(f"Process {p.name} (PID {p.pid}) movido de cola NEW a READY.")
        
        # 0.2. Update processes in WAITING state (I/O operations)
=======
        # 0. Update processes in WAITING state (I/O operations)
>>>>>>> 18b1958ee925fa5f293a0219bb80f68dc7a53770
        for p in self.active_processes():
            if p.state == "WAITING":
                if p.io_remaining_ticks > 0:
                    p.io_remaining_ticks -= 1
                if p.io_remaining_ticks <= 0:
                    # I/O completed, return to READY
                    interrupt_type = p.interrupt_type or "WAITING"
                    p.state = "READY"
                    p.io_remaining_ticks = 0
                    p.interrupt_type = None  # Clear interrupt type
                    self.scheduler.add_process(p)
                    self.log_interrupt(f"Process {p.name} {interrupt_type} completed, returning to READY queue.")
        
        # 1. Check running processes on CPUs
        for i in range(len(self.cpus)):
            p = self.cpus[i]
            if p:
                # If process finished or preempted (logic depends on scheduler, but here we simplify)
                # For RR, we need to check quantum. For SRTF, preemption.
                # The current Scheduler classes are single-threaded logic (current_process).
                # We need to adapt or bypass the single 'current_process' logic of the scheduler 
                # and just use it as a queue manager.
                
                # Let's treat scheduler.next_process as "get next from queue".
                # But standard schedulers like RR need to know who is running to manage quantum.
                # For simplicity in this multiprocessor step:
                # - If process is running, let it run unless it finishes.
                # - If CPU is free, ask scheduler for next.
                
                # Note: This is a simplification. Real MP scheduling is complex.
                
                if p.state == "TERMINATED":
                    self.cpus[i] = None
                    continue
                
                # Check for random interruption based on hash
                prob = probabilidad_interrupcion(p.pid, self.tick_count)
                if prob > 0.95:  # 5% chance of interruption (top 5% of hash values)
                    # Interrupt process and send to WAITING
                    interrupt_type = tipo_interrupcion(p.pid, self.tick_count)
                    io_time = tiempo_io(p.pid)
                    p.state = "WAITING"
                    p.io_remaining_ticks = io_time
                    p.io_total_ticks = io_time
                    p.interrupt_type = interrupt_type
                    p.cpu_id = None
                    p.quantum_used = 0  # Reset quantum if interrupted
                    self.cpus[i] = None
                    self.log_interrupt(f"Process {p.name} interrupted ({interrupt_type}).")
                    continue
                
                # Check if it should yield (e.g. RR quantum)
                # We'll implement a simple quantum check here for RR since Scheduler class is single-CPU
                if self.scheduling_alg_name == "RR":
                    # We need to track quantum per CPU or per process?
                    # Let's assume simple FCFS/SJF for MP for now, or simple RR without strict quantum enforcement per CPU in this iteration
                    # to avoid rewriting the whole Scheduler hierarchy for MP.
                    pass

                p.tick()
                self.metrics.cpu_busy_ticks += 1 # This might need scaling for 4 CPUs
                
                if p.state == "TERMINATED":
                    self.release_process(p)
                    self.cpus[i] = None
                elif self.scheduling_alg_name == "RR":
                    p.quantum_used += 1
                    if p.quantum_used >= self.quantum:
                        # Preempt process
                        p.state = "READY"
                        p.quantum_used = 0
                        p.cpu_id = None
                        self.scheduler.add_process(p)
                        self.cpus[i] = None
                        self.log_interrupt(f"Process {p.name} preempted (Quantum expired).")

        # 2. Fill empty CPUs
        for i in range(len(self.cpus)):
            if self.cpus[i] is None:
                # Ask scheduler for next
                # We need to ensure next_process doesn't return a process already running on another CPU
                # But our scheduler removes from ready_queue when returning next_process (except FCFS/SJF peek?)
                # Let's check Scheduler implementation.
                # FCFS: pop(0). SJF: remove(shortest). RR: popleft().
                # So they remove from queue. Safe to call multiple times.
                
                # However, the Scheduler classes I wrote earlier use 'self.current_process' which is single.
                # We should ignore 'self.current_process' in Scheduler and just use it to pop from queue.
                
                # We need to modify Scheduler to not rely on single current_process or just use the queue directly here?
                # Let's use the scheduler's method but we might need to reset its current_process to None to force it to pick new?
                # Or better: The scheduler logic `next_process` was designed for single CPU context switch.
                # Let's just peek/pop from `scheduler.ready_queue` directly or use `next_process` carefully.
                
                # Hack: Set scheduler.current_process to None before asking, so it thinks CPU is free and gives us one from queue.
                self.scheduler.current_process = None 
                next_p = self.scheduler.next_process(self.tick_count)
                
                if next_p:
                    self.cpus[i] = next_p
                    next_p.cpu_id = i
                    if next_p.start_tick is None:
                        next_p.start_tick = self.tick_count
                    next_p.state = "RUNNING"
                    self.log_interrupt(f"Process {next_p.name} assigned to CPU {i}.")

        # 3. Update waiting time
        for p in self.active_processes():
            if p.state == "READY":
                p.waiting_ticks += 1

    def tick(self):
        self.tick_count += 1
        # probability create new process
        if self.auto_create_processes and random.random() < 0.3:  # 30% chance
            self.create_process()
        self.update_processes()


    def active_processes(self) -> List[Process]:
        return [p for p in self.processes.values() if p.state != "TERMINATED"]


    def manager_snapshots(self):
        data = {}
        for alg, manager in self.managers.items():
            data[alg] = manager.snapshot_blocks()
        return data

    def algorithm_stats(self):
        stats = {}
        for alg in self.managers.keys():
            stats[alg] = {
                'success_rate': self.metrics.success_rate(alg),
                'fragmentation': self.managers[alg].fragmentation_ratio(),
                'efficiency': self.managers[alg].efficiency()
            }
        return stats

    def reset(self):
        self.processes.clear()
        self.metrics = SimulationMetrics()
        self.tick_count = 0
        self.cpus = [None] * 4
        self.interrupt_log.clear()
        
        # Reset memory managers
        for manager in self.managers.values():
            manager.blocks = [MemoryBlock(0, manager.total_mb, None)]
            manager.allocated_processes.clear()
            
        # Reset scheduler
        if self.scheduling_alg_name == "FCFS":
            self.scheduler = FCFS()
        elif self.scheduling_alg_name == "SJF":
            self.scheduler = SJF()
        elif self.scheduling_alg_name == "SRTF":
            self.scheduler = SRTF()
        elif self.scheduling_alg_name == "RR":
            self.scheduler = RoundRobin(quantum=self.quantum)
        else:
            self.scheduler = FCFS()
            
        self.log_interrupt("Simulation reset.")
