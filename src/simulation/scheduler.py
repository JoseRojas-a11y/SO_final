from abc import ABC, abstractmethod
from typing import List, Optional, Deque
from collections import deque
from .models import Process

class Dispatcher:
    def __init__(self):
        self.context_switch_count = 0

    def dispatch(self, current_process: Optional[Process], next_process: Optional[Process]):
        """
        Handles the context switch between the current process and the next process.
        """
        if current_process:
            # Save the state of the current process
            current_process.state = "READY"

        if next_process:
            # Load the state of the next process
            next_process.state = "RUNNING"

        # Increment the context switch counter
        self.context_switch_count += 1

# Update Scheduler to use Dispatcher
class Scheduler(ABC):
    def __init__(self):
        self.ready_queue: List[Process] = []
        self.current_process: Optional[Process] = None
        self.dispatcher = Dispatcher()

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

    def perform_context_switch(self, next_process: Optional[Process]):
        """
        Activates the dispatcher to handle the context switch.
        """
        self.dispatcher.dispatch(self.current_process, next_process)
        self.current_process = next_process

class FCFS(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        if self.current_process and self.current_process.state == "RUNNING":
            return self.current_process

        if self.ready_queue:
            next_proc = self.ready_queue.pop(0)
            self.perform_context_switch(next_proc)
            return next_proc
        return None

class SJF(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        if self.current_process and self.current_process.state == "RUNNING":
            return self.current_process

        if self.ready_queue:
            # Find process with shortest duration
            # Note: In real OS, this is estimated. Here we use actual duration.
            shortest = min(self.ready_queue, key=lambda p: p.duration_ticks)
            self.ready_queue.remove(shortest)
            self.perform_context_switch(shortest)
            return shortest
        return None

class SRTF(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        # Preemptive
        # Check if there is a process in ready queue with less remaining time than current
        
        candidate = self.current_process
        best_candidate = None

        if self.ready_queue:
            best_candidate = min(self.ready_queue, key=lambda p: p.remaining_ticks)

        if candidate and candidate.state == "RUNNING":
            if best_candidate and best_candidate.remaining_ticks < candidate.remaining_ticks:
                # Preempt
                candidate.state = "READY"
                self.ready_queue.append(candidate)
                self.ready_queue.remove(best_candidate)
                self.perform_context_switch(best_candidate)
                return best_candidate
            return candidate

        if best_candidate:
            self.ready_queue.remove(best_candidate)
            self.perform_context_switch(best_candidate)
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
        if self.rr_queue:
            next_proc = self.rr_queue.popleft()
            self.perform_context_switch(next_proc)
            return next_proc
        return None
