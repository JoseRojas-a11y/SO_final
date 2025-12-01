import random
import hashlib
from typing import Dict, List, Optional
from types import SimpleNamespace

from ..os_core.architectures import ArchitectureFactory
from ..os_core.interrupts import Interrupt, InterruptController, InterruptType
from ..os_core.models import Process, CPU, MemoryBlock
from ..os_core.memory.manager import (
    MemoryManager,
    AllocationResult,
    PagedMemoryManager,
)
from ..os_core.memory.strategies import FirstFitStrategy, BestFitStrategy, WorstFitStrategy
from .metrics import SimulationMetrics
from ..os_core.scheduler import (
    Scheduler,
    FCFS,
    SJF,
    SRTF,
    RoundRobin,
    PriorityScheduler,
    PriorityRoundRobin,
)


def _deterministic_probability(pid: int, tick: int, salt: str) -> float:
    key = f"{pid}-{tick}-{salt}"
    h = hashlib.sha256(key.encode()).hexdigest()
    x = int(h[:8], 16)
    return x / 0xFFFFFFFF


def _deterministic_duration(pid: int, salt: str, minimum: int, maximum: int) -> int:
    minimum = max(1, minimum)
    maximum = max(minimum, maximum)
    key = f"{pid}-{salt}"
    h = hashlib.sha256(key.encode()).hexdigest()
    x = int(h[:8], 16)
    span = maximum - minimum + 1
    return minimum + (x % span)


class SimulationEngine:
    def __init__(
        self,
        architecture: str = "Modular",
        scheduling_alg: str = "FCFS",
        quantum: int = 4,
        num_cpus: int = 4,
        threads_per_cpu: int = 2,
        num_memory_units: int = 2,
        memory_unit_capacity_mb: int = 256,
    ) -> None:
        self.num_memory_units = max(1, int(num_memory_units))
        self.memory_unit_capacity_mb = max(1, int(memory_unit_capacity_mb))

        def strategy_for(name: str):
            if name == "best":
                return BestFitStrategy()
            if name == "worst":
                return WorstFitStrategy()
            return FirstFitStrategy()

        self.memory_units: List[SimpleNamespace] = []
        for i in range(self.num_memory_units):
            mu = SimpleNamespace(
                id=i,
                total_mb=self.memory_unit_capacity_mb,
                alloc_alg="first",
                page_alg="FIFO",
                manager=None,
                paged_manager=None,
            )
            mu.manager = MemoryManager(mu.total_mb, mu.alloc_alg, strategy_for(mu.alloc_alg))
            mu.paged_manager = PagedMemoryManager(mu.total_mb, page_size_mb=4, replacement_alg=mu.page_alg)
            self.memory_units.append(mu)

        self.managers: Dict[str, MemoryManager] = {"first": self.memory_units[0].manager}
        self.paged_managers: Dict[str, PagedMemoryManager] = {"FIFO": self.memory_units[0].paged_manager}

        self.processes: Dict[int, Process] = {}
        self.metrics = SimulationMetrics()
        self.tick_count = 0
        self.max_process_duration = 50
        self.terminated_cleanup_delay = 10
        self.new_state_delay = 2

        self.architecture_name = "Modular"
        self.architecture = self.architecture_name
        self.interrupt_log: List[str] = []
        self.interrupt_controller = InterruptController()
        self.arch = ArchitectureFactory.create(self.architecture_name, self.interrupt_controller)

        self.scheduling_alg_name = scheduling_alg
        self.quantum = quantum
        self.cpus: List[CPU] = [CPU(id=i, thread_capacity=threads_per_cpu) for i in range(max(1, int(num_cpus)))]
        self.schedulers: List[Scheduler] = [self._create_scheduler(self.scheduling_alg_name) for _ in self.cpus]
        self.scheduler_names: List[str] = [self.scheduling_alg_name for _ in self.cpus]

        self.auto_create_processes = True
        self.is_running: bool = False

        self.dynamic_modules: Dict[str, Dict] = {}
        if self.architecture_name == "Modular":
            self.dynamic_modules = {
                "process_core": {"name": "Gestor de Procesos Core", "removable": False, "status": "loaded"},
                "memory_core": {"name": "Gestor de Memoria Core", "removable": False, "status": "loaded"},
                "scheduler_mod": {"name": "Módulo de Planificación", "removable": True, "status": "loaded"},
                "interrupt_handler": {"name": "Manejador de Interrupciones", "removable": True, "status": "loaded"},
            }
        self._layer_flow: List[str] = []

    def _create_scheduler(self, name: str) -> Scheduler:
        normalized = (name or "").strip()
        if normalized == "SJF":
            return SJF()
        if normalized == "SRTF":
            return SRTF()
        if normalized == "RR":
            return RoundRobin(quantum=self.quantum)
        if normalized == "Priority":
            return PriorityScheduler()
        if normalized == "PriorityRR":
            return PriorityRoundRobin(quantum=self.quantum)
        return FCFS()

    def log_interrupt(self, message: str) -> None:
        ts = f"[Tick {self.tick_count}]"
        self.interrupt_log.append(f"{ts} {message}")
        if len(self.interrupt_log) > 200:
            self.interrupt_log.pop(0)

    def get_process(self, pid: int) -> Optional[Process]:
        return self.processes.get(pid)

    def set_process_waiting(self, process: Process, reason: str, duration: int) -> None:
        process.state = "WAITING"
        process.interrupt_type = reason
        process.io_remaining_ticks = max(1, int(duration))
        self.log_interrupt(f"Process {process.name} -> WAITING ({reason}) por {duration} ticks.")

    def handle_global_interrupt(self, interrupt: Interrupt) -> None:
        reason = interrupt.payload.get("reason", interrupt.interrupt_type.value)
        self.log_interrupt(f"Global interrupt: {reason}.")

    def preempt_process(self, process: Process, reason: str, requeue: bool = True) -> None:
        old_cpu = process.cpu_id
        process.state = "READY"
        process.quantum_used = 0
        self.log_interrupt(f"Process {process.name} preempted ({reason}).")
        if requeue:
            target = old_cpu if (old_cpu is not None and 0 <= old_cpu < len(self.schedulers)) else self._least_loaded_scheduler_index()
            self.schedulers[target].add_process(process)

    def _scheduler_queue_length(self, sched: Scheduler) -> int:
        if hasattr(sched, "rr_queue"):
            return len(getattr(sched, "rr_queue"))
        if hasattr(sched, "priority_queues"):
            return sum(len(q) for q in getattr(sched, "priority_queues").values())
        return len(getattr(sched, "ready_queue", []))

    def _least_loaded_scheduler_index(self) -> int:
        if not self.schedulers:
            return 0
        lengths = [self._scheduler_queue_length(s) for s in self.schedulers]
        return lengths.index(min(lengths))

    def _configure_process_behavior(self, process: Process) -> None:
        process.io_remaining_ticks = 0
        process.interrupt_type = None
        process.quantum_used = 0
        process.cpu_id = None
        process.waiting_ticks = 0
        process.memory_usage_mb = getattr(process, "size_mb", 0)

    def default_io_duration(self) -> int:
        return 3

    def default_syscall_duration(self) -> int:
        return 2

    def default_page_fault_duration(self) -> int:
        return 5

    def manual_create_process(self, size_mb: int, duration: int, priority: Optional[int] = None) -> Process:
        process = Process(
            name=f"P{len(self.processes) + 1}",
            size_mb=size_mb,
            cpu_usage=random.uniform(5, 40),
            duration_ticks=duration,
            remaining_ticks=duration,
        )
        process.arrival_tick = self.tick_count
        process.state = "NEW"
        self._configure_process_behavior(process)
        process.priority = max(0, min(9, priority)) if priority is not None else self._assign_priority(process)
        self.processes[process.pid] = process
        self.metrics.total_processes += 1
        self._try_allocate_in_any_unit(process)
        return process

    def create_process(self) -> Process:
        size = random.randint(4, 64)
        duration = random.randint(20, self.max_process_duration)
        process = Process(
            name=f"P{len(self.processes) + 1}",
            size_mb=size,
            cpu_usage=random.uniform(5, 40),
            duration_ticks=duration,
            remaining_ticks=duration,
        )
        process.arrival_tick = self.tick_count
        process.state = "NEW"
        self._configure_process_behavior(process)
        process.priority = self._assign_priority(process)
        self.processes[process.pid] = process
        self.metrics.total_processes += 1
        self._try_allocate_in_any_unit(process)
        return process

    def _try_allocate_in_any_unit(self, process: Process) -> None:
        allocated = False
        for idx in self._memory_units_by_free_desc():
            unit = self.memory_units[idx]
            result: AllocationResult = unit.manager.allocate(process)
            self.metrics.update(result)
            if result.success:
                process.memory_unit_id = unit.id
                unit.paged_manager.allocate(process, self.tick_count)
                allocated = True
                break
        if allocated:
            self.log_interrupt(f"Process {process.name} created (Priority: {process.priority}) - Estado: NEW.")
            if self.architecture == "Modular":
                self.log_layer_flow("Núcleo Base", "Gestor de Memoria Core", f"alloc:{process.pid}")
        else:
            process.state = "TERMINATED"
            process.finish_tick = self.tick_count
            for unit in self.memory_units:
                unit.manager.release(process)
                unit.paged_manager.release(process)

    def release_process(self, process: Process) -> None:
        if process.memory_unit_id is not None and 0 <= process.memory_unit_id < len(self.memory_units):
            unit = self.memory_units[process.memory_unit_id]
            unit.manager.release(process)
            unit.paged_manager.release(process)
        else:
            for unit in self.memory_units:
                unit.manager.release(process)
                unit.paged_manager.release(process)
        process.state = "TERMINATED"
        process.finish_tick = self.tick_count
        self.metrics.record_process_completion(process, self.tick_count)
        self.log_interrupt(f"Process {process.name} terminated.")

    def update_processes(self) -> None:
        self._cleanup_terminated_processes()
        self._move_new_processes_to_ready()
        self._update_waiting_processes()
        self._run_cpus()
        self.arch.process_pending_interrupts(self, self.tick_count)
        self._assign_idle_cpus()
        self._update_waiting_times()

    def tick(self) -> None:
        self.tick_count += 1
        self.arch.before_tick(self, self.tick_count)

        if self.auto_create_processes and random.random() < 0.3:
            self.create_process()

        for unit in self.memory_units:
            unit.manager.tick()
        for unit in self.memory_units:
            unit.paged_manager.tick(self.tick_count)

        self._maybe_raise_global_interrupts()
        self.update_processes()

        for cpu in self.cpus:
            process = cpu.process
            if process and random.random() < 0.1:
                max_page = max(0, (process.size_mb // 4) - 1)
                page_number = random.randint(0, max_page) if max_page > 0 else 0
                if process.memory_unit_id is not None and 0 <= process.memory_unit_id < len(self.memory_units):
                    unit = self.memory_units[process.memory_unit_id]
                    unit.paged_manager.access_page(process, page_number, self.tick_count)

        self.arch.after_tick(self, self.tick_count)

    def _cleanup_terminated_processes(self) -> None:
        for process in list(self.processes.values()):
            if process.state == "TERMINATED":
                if process.finish_tick is None or (self.tick_count - process.finish_tick) > self.terminated_cleanup_delay:
                    del self.processes[process.pid]

    def _move_new_processes_to_ready(self) -> None:
        for process in self.processes.values():
            if process.state == "NEW":
                if process.arrival_tick is not None and (self.tick_count - process.arrival_tick) >= self.new_state_delay:
                    process.state = "READY"
                    idx = self._least_loaded_scheduler_index()
                    self.schedulers[idx].add_process(process)
                    self.log_interrupt(f"Process {process.name} (PID {process.pid}) movido de NEW a READY.")
                    if self.architecture == "Modular":
                        self.log_layer_flow("Núcleo Base", "Gestor de Procesos Core", f"ready:{process.pid}")

    def _update_waiting_processes(self) -> None:
        for process in self.active_processes():
            if process.state != "WAITING":
                continue
            if process.io_remaining_ticks > 0:
                process.io_remaining_ticks -= 1
            if process.io_remaining_ticks <= 0:
                process.state = "READY"
                process.io_remaining_ticks = 0
                process.interrupt_type = None
                idx = self._least_loaded_scheduler_index()
                self.schedulers[idx].add_process(process)
                self.log_interrupt(f"Process {process.name} finalizó I/O y vuelve a READY.")

    def _run_cpus(self) -> None:
        for cpu in self.cpus:
            process = cpu.process
            if process is None:
                continue

            if process.state == "TERMINATED":
                cpu.release()
                continue

            if self._evaluate_process_interrupts(process):
                continue

            cpu.tick()
            self.metrics.cpu_busy_ticks += max(1, cpu.threads_in_use)
            self.metrics.effective_cpu_ticks += max(1, cpu.threads_in_use)

            if process.state == "TERMINATED":
                self.release_process(process)
                cpu.release()
                continue

            if self.scheduling_alg_name in {"RR", "PriorityRR"}:
                process.quantum_used += 1
                if process.quantum_used >= self.quantum:
                    self.preempt_process(process, "QUANTUM_EXPIRED")
                    continue

            if self.scheduling_alg_name == "Priority":
                sched = self.schedulers[cpu.id % len(self.schedulers)]
                ready_queue = getattr(sched, "ready_queue", [])
                if ready_queue:
                    ready_queue.sort(key=lambda proc: proc.priority)
                    highest = ready_queue[0]
                    if highest.priority < process.priority:
                        self.preempt_process(process, "HIGHER_PRIORITY")

    def _assign_idle_cpus(self) -> None:
        for cpu in self.cpus:
            if cpu.process is not None:
                continue
            sched = self.schedulers[cpu.id % len(self.schedulers)]
            sched.current_process = None
            next_process = sched.next_process(self.tick_count)
            if next_process is None:
                continue
            if next_process.start_tick is None:
                next_process.start_tick = self.tick_count
            cpu.assign(next_process)
            self.log_interrupt(f"Process {next_process.name} asignado a CPU {cpu.id} con {cpu.thread_capacity} hilos.")
            if self.architecture == "Modular":
                self.log_layer_flow("Módulo de Planificación", "Núcleo Base", f"dispatch:{next_process.pid}")

    def _update_waiting_times(self) -> None:
        for process in self.active_processes():
            if process.state == "READY":
                process.waiting_ticks += 1

    def _evaluate_process_interrupts(self, process: Process) -> bool:
        pid = process.pid
        if process.state != "RUNNING":
            return False
        sys_prob = _deterministic_probability(pid, self.tick_count, "syscall")
        if sys_prob < process.syscall_probability:
            duration = _deterministic_duration(pid, "syscall", 1, self.default_syscall_duration())
            self.interrupt_controller.raise_interrupt(
                Interrupt(InterruptType.SYSCALL, source="process", pid=pid, payload={"syscall_duration": duration})
            )
            process.state = "WAITING"
            process.interrupt_type = "SYSCALL"
            process.io_remaining_ticks = duration
            self.log_interrupt(f"Process {process.name} ejecuta SYSCALL por {duration} ticks.")
            if self.architecture == "Modular":
                self.log_layer_flow("Proceso", "Núcleo Base", f"syscall:{pid}")
            return True
        io_prob = _deterministic_probability(pid, self.tick_count, "io")
        if io_prob < process.io_probability:
            duration = _deterministic_duration(pid, "io", 2, self.default_io_duration() + 3)
            self.interrupt_controller.raise_interrupt(
                Interrupt(InterruptType.IO, source="process", pid=pid, payload={"io_duration": duration})
            )
            process.state = "WAITING"
            process.interrupt_type = "IO"
            process.io_remaining_ticks = duration
            self.log_interrupt(f"Process {process.name} entra a I/O por {duration} ticks.")
            if self.architecture == "Modular":
                self.log_layer_flow("Proceso", "Manejador de Interrupciones", f"io_req:{pid}")
            return True
        pf_prob = _deterministic_probability(pid, self.tick_count, "pagefault")
        if pf_prob < max(0.02, process.hardware_interrupt_probability):
            duration = _deterministic_duration(pid, "pf", 2, self.default_page_fault_duration() + 2)
            self.interrupt_controller.raise_interrupt(
                Interrupt(InterruptType.PAGE_FAULT, source="mmu", pid=pid, payload={"page_fault_duration": duration})
            )
            process.state = "WAITING"
            process.interrupt_type = "PAGE_FAULT"
            process.io_remaining_ticks = duration
            self.log_interrupt(f"Process {process.name} sufre PAGE FAULT ({duration} ticks).")
            return True
        return False

    def _maybe_raise_global_interrupts(self) -> None:
        if random.random() < 0.02:
            self.interrupt_controller.raise_interrupt(
                Interrupt(InterruptType.TIMER, source="timer", pid=None, payload={"reason": "timer"})
            )
            self.log_interrupt("Timer interrupt")

    def _assign_priority(self, process: Process) -> int:
        size_score = 1.0 - (process.size_mb / 64.0)
        duration_score = 1.0 - (process.duration_ticks / 100.0)
        cpu_score = 1.0 - (process.cpu_usage / 100.0)
        priority_score = (size_score * 0.3) + (duration_score * 0.4) + (cpu_score * 0.3)
        priority = int(priority_score * 9)
        priority += random.randint(-1, 1)
        return max(0, min(9, priority))

    def set_cpu_scheduler(self, index: int, name: str) -> None:
        if self.is_running:
            return
        if 0 <= index < len(self.schedulers):
            self.schedulers[index] = self._create_scheduler(name)
            self.scheduler_names[index] = name
            self.log_interrupt(f"CPU {index}: algoritmo -> {name}.")

    def set_cpu_quantum(self, index: int, quantum: int) -> None:
        if 0 <= index < len(self.schedulers):
            scheduler = self.schedulers[index]
            if hasattr(scheduler, 'quantum'):
                scheduler.quantum = quantum
                self.log_interrupt(f"CPU {index}: quantum -> {quantum}.")

    def set_cpu_threads(self, index: int, threads: int) -> None:
        if self.is_running:
            return
        if 0 <= index < len(self.cpus):
            self.cpus[index].thread_capacity = max(1, int(threads))
            self.log_interrupt(f"CPU {index}: hilos -> {self.cpus[index].thread_capacity}.")

    def _memory_units_by_free_desc(self) -> List[int]:
        freemap = []
        for unit in self.memory_units:
            used = sum(b.size for b in unit.manager.blocks if not b.free)
            free = unit.manager.total_mb - used
            freemap.append((unit.id, free))
        freemap.sort(key=lambda t: t[1], reverse=True)
        return [idx for idx, _ in freemap]

    def set_memory_unit_alloc_alg(self, index: int, name: str) -> None:
        if 0 <= index < len(self.memory_units):
            unit = self.memory_units[index]
            unit.alloc_alg = name
            unit.manager = MemoryManager(
                unit.total_mb,
                unit.alloc_alg,
                FirstFitStrategy() if name == "first" else BestFitStrategy() if name == "best" else WorstFitStrategy(),
            )
            self.log_interrupt(f"Unidad de memoria {index}: algoritmo de asignación -> {name}.")

    def set_memory_unit_page_alg(self, index: int, name: str) -> None:
        if 0 <= index < len(self.memory_units):
            unit = self.memory_units[index]
            unit.page_alg = name
            unit.paged_manager = PagedMemoryManager(unit.total_mb, page_size_mb=4, replacement_alg=unit.page_alg)
            self.log_interrupt(f"Unidad de memoria {index}: algoritmo de paginación -> {name}.")

    def memory_unit_summaries(self) -> List[Dict[str, object]]:
        out: List[Dict[str, object]] = []
        for unit in self.memory_units:
            used = sum(b.size for b in unit.manager.blocks if not b.free)
            out.append(
                {
                    "id": unit.id,
                    "total_mb": unit.manager.total_mb,
                    "used_mb": used,
                    "fragmentation": unit.manager.fragmentation_ratio(),
                    "efficiency": unit.manager.efficiency(),
                    "alloc_alg": unit.manager.algorithm,
                    "page_alg": unit.paged_manager.replacement_alg,
                    "page_faults": unit.paged_manager.page_faults,
                    "page_hits": unit.paged_manager.page_hits,
                    "fault_rate": unit.paged_manager.page_fault_rate(),
                    "mem_util": unit.paged_manager.memory_utilization(),
                }
            )
        return out

    def storage_overview(self) -> Dict[str, float]:
        total_mb = sum(u.manager.total_mb for u in self.memory_units)
        used_mb = sum(sum(b.size for b in u.manager.blocks if not b.free) for u in self.memory_units)
        total_faults = sum(u.paged_manager.page_faults for u in self.memory_units)
        total_hits = sum(u.paged_manager.page_hits for u in self.memory_units)
        total_accesses = total_faults + total_hits
        fault_rate = (total_faults / total_accesses) if total_accesses > 0 else 0.0
        avg_mem_util = 0.0
        if self.memory_units:
            avg_mem_util = sum(u.paged_manager.memory_utilization() for u in self.memory_units) / len(self.memory_units)
        return {
            "total_mb": total_mb,
            "used_mb": used_mb,
            "total_page_faults": total_faults,
            "total_hits": total_hits,
            "fault_rate": fault_rate,
            "avg_mem_util": avg_mem_util,
        }

    def active_processes(self) -> List[Process]:
        return [p for p in self.processes.values() if p.state != "TERMINATED"]

    def manager_snapshots(self) -> Dict[str, List[MemoryBlock]]:
        data: Dict[str, List[MemoryBlock]] = {}
        for unit in self.memory_units:
            data[f"unit_{unit.id}"] = unit.manager.snapshot_blocks()
        return data

    def algorithm_stats(self) -> Dict[str, Dict[str, float]]:
        stats: Dict[str, Dict[str, float]] = {}
        for unit in self.memory_units:
            stats[f"unit_{unit.id}"] = {
                "success_rate": self.metrics.success_rate("first"),
                "fragmentation": unit.manager.fragmentation_ratio(),
                "efficiency": unit.manager.efficiency(),
            }
        return stats

    def paging_stats(self) -> Dict[str, Dict[str, float]]:
        stats: Dict[str, Dict[str, float]] = {}
        for unit in self.memory_units:
            pm = unit.paged_manager
            stats[f"unit_{unit.id}"] = {
                "total_page_faults": pm.page_faults,
                "total_hits": pm.page_hits,
                "page_fault_rate": pm.page_fault_rate(),
                "memory_utilization": pm.memory_utilization(),
            }
        return stats

    def reset(self) -> None:
        self.processes.clear()
        self.metrics = SimulationMetrics()
        self.tick_count = 0
        # Re-init interrupts and architecture
        self.interrupt_log.clear()
        self.interrupt_controller = InterruptController()
        self.arch = ArchitectureFactory.create(self.architecture_name, self.interrupt_controller)
        # Rebuild CPUs preserving count and thread capacity
        count = len(self.cpus) if self.cpus else 1
        default_threads = self.cpus[0].thread_capacity if self.cpus else 2
        self.cpus = [CPU(id=i, thread_capacity=default_threads) for i in range(count)]
        self.schedulers = [self._create_scheduler(self.scheduling_alg_name) for _ in self.cpus]
        self.scheduler_names = [self.scheduling_alg_name for _ in self.cpus]
        # Rebuild memory units preserving algorithms
        new_units: List[SimpleNamespace] = []
        for i in range(self.num_memory_units):
            alloc_alg = self.memory_units[i].manager.algorithm if i < len(self.memory_units) else "first"
            page_alg = self.memory_units[i].paged_manager.replacement_alg if i < len(self.memory_units) else "FIFO"
            mgr = MemoryManager(
                self.memory_unit_capacity_mb,
                alloc_alg,
                FirstFitStrategy() if alloc_alg == "first" else BestFitStrategy() if alloc_alg == "best" else WorstFitStrategy(),
            )
            pm = PagedMemoryManager(self.memory_unit_capacity_mb, page_size_mb=4, replacement_alg=page_alg)
            mu = SimpleNamespace(
                id=i,
                total_mb=self.memory_unit_capacity_mb,
                alloc_alg=alloc_alg,
                page_alg=page_alg,
                manager=mgr,
                paged_manager=pm,
            )
            new_units.append(mu)
        self.memory_units = new_units
        self.managers = {"first": self.memory_units[0].manager}
        self.paged_managers = {"FIFO": self.memory_units[0].paged_manager}

    def layer_flow_events(self) -> List[str]:
        return list(self._layer_flow)

    def log_layer_flow(self, source: str, target: str, action: str) -> None:
        self._layer_flow.append(f"[Tick {self.tick_count}] {source} → {target}")
        if len(self._layer_flow) > 50:
            self._layer_flow.pop(0)

    def get_module_status(self) -> Dict:
        return {"ipc_enabled": False, "modules_loaded": len(self.dynamic_modules)}

    def load_module(self, module_id: str, module_name: str, removable: bool = True) -> bool:
        if module_id in self.dynamic_modules:
            return False
        self.dynamic_modules[module_id] = {"name": module_name, "removable": removable, "status": "loaded"}
        self.log_layer_flow("UI", "Kernel", f"load:{module_name}")
        return True

    def unload_module(self, module_id: str) -> bool:
        mod = self.dynamic_modules.get(module_id)
        if not mod:
            return False
        if not mod.get("removable", True):
            return False
        del self.dynamic_modules[module_id]
        self.log_layer_flow("UI", "Kernel", f"unload:{module_id}")
        return True
