from typing import Dict
from .memory_manager import AllocationResult
from .models import Process

class SimulationMetrics:
    def __init__(self):
        self.alloc_attempts: Dict[str, int] = {"first":0, "best":0, "worst":0}
        self.alloc_success: Dict[str, int] = {"first":0, "best":0, "worst":0}
        self.fragmentation: Dict[str, float] = {"first":0.0, "best":0.0, "worst":0.0}
        self.efficiency: Dict[str, float] = {"first":0.0, "best":0.0, "worst":0.0}
        
        # Process metrics
        self.total_processes = 0
        self.completed_processes = 0
        self.total_turnaround_time = 0
        self.total_waiting_time = 0
        self.cpu_busy_ticks = 0

    def update(self, result: AllocationResult):
        alg = result.algorithm
        self.alloc_attempts[alg] += 1
        if result.success:
            self.alloc_success[alg] += 1
        # moving average simple
        self.fragmentation[alg] = (self.fragmentation[alg]*0.9) + (result.fragmentation*0.1)
        self.efficiency[alg] = (self.efficiency[alg]*0.9) + (result.efficiency*0.1)
        
    def record_process_completion(self, p: Process, current_tick: int):
        self.completed_processes += 1
        turnaround = current_tick - p.arrival_tick
        self.total_turnaround_time += turnaround
        self.total_waiting_time += p.waiting_ticks

    def success_rate(self, alg: str) -> float:
        attempts = self.alloc_attempts[alg]
        if attempts == 0:
            return 0.0
        return self.alloc_success[alg] / attempts
