import random
import time
import hashlib
from typing import Dict, List, Optional
from .models import Process
from .memory.manager import MemoryManager, AllocationResult, MemoryBlock, PagedMemoryManager, PagedAllocationResult
from .memory.strategies import FirstFitStrategy, BestFitStrategy, WorstFitStrategy
from .metrics import SimulationMetrics
from .scheduler import Scheduler, FCFS, SJF, SRTF, RoundRobin, PriorityScheduler, PriorityRoundRobin

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
        # Gestores de memoria paginada
        self.paged_managers: Dict[str, PagedMemoryManager] = {
            'FIFO': PagedMemoryManager(total_memory_mb, page_size_mb=4, replacement_alg='FIFO'),
            'LRU': PagedMemoryManager(total_memory_mb, page_size_mb=4, replacement_alg='LRU'),
            'Optimal': PagedMemoryManager(total_memory_mb, page_size_mb=4, replacement_alg='Optimal')
        }
        self.processes: Dict[int, Process] = {}
        self.metrics = SimulationMetrics()
        self.tick_count = 0
        self.max_process_duration = 50  # ticks
        
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
        elif scheduling_alg == "Priority":
            self.scheduler = PriorityScheduler()
        elif scheduling_alg == "PriorityRR":
            self.scheduler = PriorityRoundRobin(quantum=quantum)
        else:
            self.scheduler = FCFS() # Default

    def log_interrupt(self, message: str):
        timestamp = f"[Tick {self.tick_count}]"
        self.interrupt_log.append(f"{timestamp} {message}")
        if len(self.interrupt_log) > 50:
            self.interrupt_log.pop(0)

    def _assign_priority(self, process: Process) -> int:
        """Asigna prioridad automáticamente basada en características del proceso."""
        # Prioridad basada en: tamaño (30%), duración (40%), uso CPU (30%)
        # Menor número = mayor prioridad (0-9)
        
        # Normalizar valores (invertir para que menor = mejor)
        size_score = 1.0 - (process.size_mb / 64.0)  # Procesos más pequeños = mayor prioridad
        duration_score = 1.0 - (process.duration_ticks / 100.0)  # Procesos más cortos = mayor prioridad
        cpu_score = 1.0 - (process.cpu_usage / 100.0)  # Menos intensivo = mayor prioridad
        
        # Ponderación
        priority_score = (size_score * 0.3) + (duration_score * 0.4) + (cpu_score * 0.3)
        
        # Convertir a rango 0-9
        priority = int(priority_score * 9)
        
        # Agregar variación aleatoria para simular diferentes tipos de procesos
        priority += random.randint(-1, 1)
        priority = max(0, min(9, priority))
        
        return priority

    def manual_create_process(self, size_mb: int, duration: int, priority: Optional[int] = None) -> Process:
        p = Process(name=f"P{len(self.processes)+1}", size_mb=size_mb, cpu_usage=random.uniform(5,40), duration_ticks=duration, remaining_ticks=duration)
        p.arrival_tick = self.tick_count
        p.state = "NEW"
        
        # Asignar prioridad
        if priority is None:
            p.priority = self._assign_priority(p)
        else:
            p.priority = max(0, min(9, priority))
        
        self.processes[p.pid] = p
        self.metrics.total_processes += 1
        
        allocated = False
        for alg, manager in self.managers.items():
            result = manager.allocate(p)
            self.metrics.update(result)
            if alg == 'first' and result.success:
                allocated = True
        
        # Asignar también en gestores paginados
        for alg, paged_manager in self.paged_managers.items():
            paged_result = paged_manager.allocate(p, self.tick_count)
            # No fallamos si paginación falla, solo registramos
        
        if allocated:
            self.scheduler.add_process(p)
            self.log_interrupt(f"Process {p.name} created manually (Priority: {p.priority}).")
        else:
            p.state = "TERMINATED"
            self.log_interrupt(f"Process {p.name} creation failed (Memory Full).")
            # Release memory from any manager that might have allocated (e.g. best/worst) even if first failed
            for manager in self.managers.values():
                manager.release(p)
            for paged_manager in self.paged_managers.values():
                paged_manager.release(p)
            
        return p

    def create_process(self) -> Process:
        size = random.randint(4, 64)  # MB
        duration = random.randint(20, self.max_process_duration)
        p = Process(name=f"P{len(self.processes)+1}", size_mb=size, cpu_usage=random.uniform(5,40), duration_ticks=duration, remaining_ticks=duration)
        p.arrival_tick = self.tick_count
        p.state = "NEW"
        
        # Asignar prioridad automáticamente
        p.priority = self._assign_priority(p)
        
        self.processes[p.pid] = p
        self.metrics.total_processes += 1
        
        allocated = False
        for alg, manager in self.managers.items():
            result = manager.allocate(p)
            self.metrics.update(result)
            if alg == 'first' and result.success:
                allocated = True
        
        # Asignar también en gestores paginados
        for alg, paged_manager in self.paged_managers.items():
            paged_result = paged_manager.allocate(p, self.tick_count)
            # No fallamos si paginación falla, solo registramos
        
        if allocated:
            self.scheduler.add_process(p)
            self.log_interrupt(f"Process {p.name} created (Auto, Priority: {p.priority}).")
        else:
            p.state = "TERMINATED" # Rejected due to memory
            # Release memory from any manager that might have allocated (e.g. best/worst) even if first failed
            for manager in self.managers.values():
                manager.release(p)
            for paged_manager in self.paged_managers.values():
                paged_manager.release(p)
            
        return p

    def release_process(self, p: Process):
        for manager in self.managers.values():
            manager.release(p)
        for paged_manager in self.paged_managers.values():
            paged_manager.release(p)
        p.state = "TERMINATED"
        p.finish_tick = self.tick_count
        self.metrics.record_process_completion(p, self.tick_count)
        self.log_interrupt(f"Process {p.name} terminated.")

    def update_processes(self):
        # Multiprocessor Scheduling Logic
        # We have 4 CPUs. We need to fill them from the scheduler.
        
        # 0. Update processes in WAITING state (I/O operations)
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
                elif self.scheduling_alg_name == "RR" or self.scheduling_alg_name == "PriorityRR":
                    p.quantum_used += 1
                    if p.quantum_used >= self.quantum:
                        # Preempt process
                        p.state = "READY"
                        p.quantum_used = 0
                        p.cpu_id = None
                        self.scheduler.add_process(p)
                        self.cpus[i] = None
                        self.log_interrupt(f"Process {p.name} preempted (Quantum expired).")
                elif self.scheduling_alg_name == "Priority":
                    # Priority scheduler maneja preemption internamente
                    # Verificar si hay proceso de mayor prioridad
                    if self.scheduler.ready_queue:
                        self.scheduler.ready_queue.sort(key=lambda proc: proc.priority)
                        highest = self.scheduler.ready_queue[0]
                        if highest.priority < p.priority:
                            # Preempt
                            p.state = "READY"
                            p.cpu_id = None
                            self.scheduler.add_process(p)
                            self.cpus[i] = None
                            self.log_interrupt(f"Process {p.name} preempted (Higher priority process).")

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
        
        # Actualizar gestores de memoria (autocompactación)
        for manager in self.managers.values():
            manager.tick()
        
        # Actualizar gestores paginados
        for paged_manager in self.paged_managers.values():
            paged_manager.tick(self.tick_count)
        
        # Simular accesos a páginas de procesos en ejecución
        for cpu in self.cpus:
            if cpu and random.random() < 0.1:  # 10% chance de acceso a página
                page_num = random.randint(0, max(0, (cpu.size_mb // 4) - 1))
                for paged_manager in self.paged_managers.values():
                    paged_manager.access_page(cpu, page_num, self.tick_count)
        
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

    def paging_stats(self):
        """Retorna estadísticas de los algoritmos de paginación."""
        stats = {}
        for alg, paged_manager in self.paged_managers.items():
            stats[alg] = {
                'total_page_faults': paged_manager.page_faults,
                'total_hits': paged_manager.page_hits,
                'page_fault_rate': paged_manager.page_fault_rate(),
                'memory_utilization': paged_manager.memory_utilization()
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
        
        # Reset paged managers
        total_mb = self.managers['first'].total_mb
        self.paged_managers = {
            'FIFO': PagedMemoryManager(total_mb, page_size_mb=4, replacement_alg='FIFO'),
            'LRU': PagedMemoryManager(total_mb, page_size_mb=4, replacement_alg='LRU'),
            'Optimal': PagedMemoryManager(total_mb, page_size_mb=4, replacement_alg='Optimal')
        }
            
        # Reset scheduler
        if self.scheduling_alg_name == "FCFS":
            self.scheduler = FCFS()
        elif self.scheduling_alg_name == "SJF":
            self.scheduler = SJF()
        elif self.scheduling_alg_name == "SRTF":
            self.scheduler = SRTF()
        elif self.scheduling_alg_name == "RR":
            self.scheduler = RoundRobin(quantum=self.quantum)
        elif self.scheduling_alg_name == "Priority":
            self.scheduler = PriorityScheduler()
        elif self.scheduling_alg_name == "PriorityRR":
            self.scheduler = PriorityRoundRobin(quantum=self.quantum)
        else:
            self.scheduler = FCFS()
            
        self.log_interrupt("Simulation reset.")
