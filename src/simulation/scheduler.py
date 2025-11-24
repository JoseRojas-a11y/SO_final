from abc import ABC, abstractmethod
from typing import List, Optional, Deque
from collections import deque
from .models import Process

class Scheduler(ABC):
    def __init__(self):
        self.ready_queue: List[Process] = []
        self.current_process: Optional[Process] = None

    def add_process(self, process: Process):
        process.state = "READY"
        self.ready_queue.append(process)

    @abstractmethod
    def next_process(self, current_tick: int) -> Optional[Process]:
        """Decides which process to run next."""
        pass

    def on_tick(self):
        """Optional hook for things like aging or quantum updates."""
        pass

class FCFS(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        # Non-preemptive: if current is running and not finished, keep it.
        # But engine handles "finished". Here we just say who should run.
        # If current is None or Terminated (handled by engine), pick next.
        
        if self.current_process and self.current_process.state == "RUNNING":
            return self.current_process
        
        if self.ready_queue:
            # First in list is first arrived (append adds to end)
            return self.ready_queue.pop(0)
        return None

class SJF(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        # Non-preemptive
        if self.current_process and self.current_process.state == "RUNNING":
            return self.current_process
        
        if self.ready_queue:
            # Find process with shortest duration
            # Note: In real OS, this is estimated. Here we use actual duration.
            shortest = min(self.ready_queue, key=lambda p: p.duration_ticks)
            self.ready_queue.remove(shortest)
            return shortest
        return None

class SRTF(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        # Preemptive
        # Check if there is a process in ready queue with less remaining time than current
        
        candidate = self.current_process
        
        # If current is running, put it back in consideration (conceptually)
        # But we need to compare it against ready queue.
        
        best_candidate = None
        if self.ready_queue:
            best_candidate = min(self.ready_queue, key=lambda p: p.remaining_ticks)
        
        if candidate and candidate.state == "RUNNING":
            if best_candidate and best_candidate.remaining_ticks < candidate.remaining_ticks:
                # Preempt
                candidate.state = "READY"
                self.ready_queue.append(candidate)
                self.ready_queue.remove(best_candidate)
                return best_candidate
            return candidate
        
        if best_candidate:
            self.ready_queue.remove(best_candidate)
            return best_candidate
            
        return None

class RoundRobin(Scheduler):
    def __init__(self, quantum: int = 4):
        super().__init__()
        self.quantum = quantum
        self.rr_queue: Deque[Process] = deque()

    def add_process(self, process: Process):
        process.state = "READY"
        self.rr_queue.append(process)

    def next_process(self, current_tick: int) -> Optional[Process]:
        # Engine handles preemption. We just return next in queue.
        if self.rr_queue:
            return self.rr_queue.popleft()
        return None
