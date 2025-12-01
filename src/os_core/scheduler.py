from abc import ABC, abstractmethod
from typing import List, Optional, Deque, Dict
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
            current_process.state = "READY"

        if next_process:
            next_process.state = "RUNNING"

        self.context_switch_count += 1

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
        pass

    def on_tick(self):
        pass

    def perform_context_switch(self, next_process: Optional[Process]):
        self.dispatcher.dispatch(self.current_process, next_process)
        self.current_process = next_process

class FCFS(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        if self.current_process and self.current_process.state == "RUNNING":
            return self.current_process

        if self.ready_queue:
            self.ready_queue.sort(key=lambda p: (p.priority, p.arrival_tick))
            next_proc = self.ready_queue.pop(0)
            self.perform_context_switch(next_proc)
            return next_proc
        return None

class SJF(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        if self.current_process and self.current_process.state == "RUNNING":
            return self.current_process

        if self.ready_queue:
            shortest = min(self.ready_queue, key=lambda p: (p.priority, p.duration_ticks))
            self.ready_queue.remove(shortest)
            self.perform_context_switch(shortest)
            return shortest
        return None

class SRTF(Scheduler):
    def next_process(self, current_tick: int) -> Optional[Process]:
        candidate = self.current_process
        best_candidate = None

        if self.ready_queue:
            best_candidate = min(self.ready_queue, key=lambda p: (p.priority, p.remaining_ticks))

        if candidate and candidate.state == "RUNNING":
            candidate_key = (candidate.priority, candidate.remaining_ticks)
            if best_candidate:
                best_key = (best_candidate.priority, best_candidate.remaining_ticks)
                if best_key < candidate_key:
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
            sorted_queue = sorted(self.rr_queue, key=lambda p: p.priority)
            self.rr_queue = deque(sorted_queue)
            next_proc = self.rr_queue.popleft()
            self.perform_context_switch(next_proc)
            return next_proc
        return None

class PriorityScheduler(Scheduler):
    def __init__(self, preemptive: bool = True, aging_enabled: bool = True, aging_interval: int = 10):
        super().__init__()
        self.preemptive = preemptive
        self.aging_enabled = aging_enabled
        self.aging_interval = aging_interval
        self.last_aging_tick = 0

    def add_process(self, process: Process):
        process.state = "READY"
        self.ready_queue.append(process)
        self.ready_queue.sort(key=lambda p: p.priority)

    def next_process(self, current_tick: int) -> Optional[Process]:
        if self.aging_enabled and current_tick - self.last_aging_tick >= self.aging_interval:
            self._apply_aging()
            self.last_aging_tick = current_tick

        if not self.ready_queue:
            return None

        if self.preemptive and self.current_process and self.current_process.state == "RUNNING":
            self.ready_queue.sort(key=lambda p: p.priority)
            highest_priority = self.ready_queue[0]
            if highest_priority.priority < self.current_process.priority:
                self.current_process.state = "READY"
                self.ready_queue.append(self.current_process)
                self.ready_queue.sort(key=lambda p: p.priority)
                self.ready_queue.remove(highest_priority)
                self.perform_context_switch(highest_priority)
                return highest_priority
            else:
                return self.current_process

        self.ready_queue.sort(key=lambda p: p.priority)
        next_proc = self.ready_queue.pop(0)
        self.perform_context_switch(next_proc)
        return next_proc

    def _apply_aging(self):
        for process in self.ready_queue:
            if process.waiting_ticks > 20:
                process.priority = max(0, process.priority - 1)

class PriorityRoundRobin(Scheduler):
    def __init__(self, quantum: int = 4):
        super().__init__()
        self.quantum = quantum
        self.priority_queues: Dict[int, Deque[Process]] = {i: deque() for i in range(10)}

    def add_process(self, process: Process):
        process.state = "READY"
        priority = max(0, min(9, process.priority))
        self.priority_queues[priority].append(process)

    def next_process(self, current_tick: int) -> Optional[Process]:
        for priority in range(10):
            if self.priority_queues[priority]:
                next_proc = self.priority_queues[priority].popleft()
                self.perform_context_switch(next_proc)
                return next_proc
        return None
