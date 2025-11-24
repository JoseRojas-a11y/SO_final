import random
import time
from typing import Dict, List, Optional
from .models import Process
from .memory.manager import MemoryManager, AllocationResult, MemoryBlock
from .memory.strategies import FirstFitStrategy, BestFitStrategy, WorstFitStrategy
from .metrics import SimulationMetrics
from .scheduler import Scheduler, FCFS, SJF, SRTF, RoundRobin

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
            self.scheduler.add_process(p)
            self.log_interrupt(f"Process {p.name} created manually.")
        else:
            p.state = "TERMINATED"
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
            self.scheduler.add_process(p)
            self.log_interrupt(f"Process {p.name} created (Auto).")
        else:
            p.state = "TERMINATED" # Rejected due to memory
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
