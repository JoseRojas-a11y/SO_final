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
        self.terminated_cleanup_delay = 10  # ticks que un proceso terminado permanece antes de ser eliminado
        self.new_state_delay = 2  # ticks que un proceso permanece en NEW antes de pasar a READY (para visibilidad)
        
        self.architecture = architecture
        self.scheduling_alg_name = scheduling_alg
        self.quantum = quantum
        self.auto_create_processes = True
        
        # Multiprocessor: 4 CPUs
        self.cpus: List[Optional[Process]] = [None] * 4
        self.interrupt_log: List[str] = []
        self.layer_flow_log: List[str] = []
        
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
        
        # Atributos para arquitecturas Microkernel y Modular
        self.external_modules: Dict[str, Dict] = {}  # Módulos externos (Microkernel)
        self.dynamic_modules: Dict[str, Dict] = {}  # Módulos dinámicos (Modular)
        self.ipc_messages: List[Dict] = []  # Mensajes IPC (Microkernel)
        
        # Inicializar arquitectura seleccionada
        # Este método de control invoca el método adecuado según la arquitectura seleccionada
        self.init_architecture(architecture)
        
    def init_architecture(self, architecture: str):
        """
        Método de control que invoca el método adecuado según la arquitectura seleccionada.
        Captura la selección y ejecuta el comportamiento del sistema operativo adecuado.
        """
        if architecture == "Monolithic":
            self.init_monolithic()  # Equivalente a initMonolithicOS()
        elif architecture == "Microkernel":
            self.init_microkernel()  # Equivalente a initMicrokernelOS()
        elif architecture == "Modular":
            self.init_modular()  # Equivalente a initModularOS()
        else:
            self.log_interrupt(f"Arquitectura desconocida: {architecture}. Usando Monolithic por defecto.")
            self.init_monolithic()

    def log_interrupt(self, message: str):
        timestamp = f"[Tick {self.tick_count}]"
        self.interrupt_log.append(f"{timestamp} {message}")
        if len(self.interrupt_log) > 50:
            self.interrupt_log.pop(0)

    def log_layer_flow(self, source: str, target: str, action: str):
        """Registra el flujo de peticiones entre capas (solo arquitectura Modular)."""
        if self.architecture != "Modular":
            return
        timestamp = f"[Tick {self.tick_count}]"
        entry = f"{timestamp} {source} → {target}: {action}"
        self.layer_flow_log.append(entry)
        if len(self.layer_flow_log) > 50:
            self.layer_flow_log.pop(0)

    def init_monolithic(self):
        """
        Inicializa la arquitectura Monolítica.
        El núcleo gestiona todos los recursos (memoria, procesos, tareas) de manera centralizada
        sin separación de módulos.
        Equivalente a initMonolithicOS() según especificaciones.
        """
        self.log_interrupt("Arquitectura Monolítica inicializada: Núcleo único gestionando todos los recursos.")
        self.log_interrupt("Gestión centralizada de procesos, memoria y tareas activada.")
        
        # Configurar arquitectura monolítica
        self.kernel_mode = "monolithic"
        self.centralized_memory_management = True
        self.centralized_process_management = True
        
        # Inicializar componentes según especificaciones
        self.setup_monolithic_memory()
        self.setup_monolithic_processes()
        self.setup_monolithic_devices()
        
    def setup_monolithic_memory(self):
        """Configura la gestión de memoria en arquitectura Monolítica."""
        # En Monolithic, la memoria se gestiona directamente desde el núcleo
        # Los gestores de memoria ya están inicializados en __init__
        self.log_interrupt("Gestión de memoria Monolítica: Todo centralizado en el núcleo.")
        
    def setup_monolithic_processes(self):
        """Configura la gestión de procesos en arquitectura Monolítica."""
        # En Monolithic, los procesos se gestionan directamente desde el núcleo
        # El scheduler ya está inicializado en __init__
        self.log_interrupt("Gestión de procesos Monolítica: Todo centralizado en el núcleo.")
        
    def setup_monolithic_devices(self):
        """Configura la gestión de dispositivos en arquitectura Monolítica."""
        # En Monolithic, los dispositivos se gestionan directamente desde el núcleo
        self.log_interrupt("Gestión de dispositivos Monolítica: Todo centralizado en el núcleo.")
        
    def init_microkernel(self):
        """
        Inicializa la arquitectura Microkernel.
        El núcleo solo gestiona funciones básicas (procesos e IPC).
        Los servicios como gestión de memoria son manejados por módulos externos.
        Equivalente a initMicrokernelOS() según especificaciones.
        """
        self.log_interrupt("Arquitectura Microkernel inicializada: Núcleo básico activado.")
        
        # Configurar arquitectura microkernel
        self.kernel_mode = "microkernel"
        self.centralized_memory_management = False
        self.centralized_process_management = True
        
        # Inicializar componentes según especificaciones
        self.setup_microkernel()
        self.setup_microkernel_modules()
        
    def setup_microkernel(self):
        """Configura el microkernel mínimo con funciones básicas."""
        # El núcleo solo gestiona procesos e IPC
        self.log_interrupt("Microkernel configurado: Gestión de procesos y IPC activada.")
        
        # Inicializar sistema IPC (Inter-Process Communication)
        self.ipc_messages = []
        self.ipc_enabled = True
        self.log_interrupt("Sistema IPC (Inter-Process Communication) activado.")
        
    def setup_microkernel_modules(self):
        """Configura los módulos externos del microkernel."""
        # Inicializar módulos externos para servicios
        self.external_modules = {
            "memory_service": {
                "name": "Servicio de Memoria",
                "status": "active",
                "initialized": True,
                "managers": self.managers,  # Los gestores de memoria están en módulo externo
                "paged_managers": self.paged_managers
            },
            "file_service": {
                "name": "Servicio de Archivos",
                "status": "active",
                "initialized": True
            },
            "device_service": {
                "name": "Servicio de Dispositivos",
                "status": "active",
                "initialized": True
            },
            "network_service": {
                "name": "Servicio de Red",
                "status": "active",
                "initialized": True
            }
        }
        
        self.log_interrupt("Módulos externos inicializados: Memoria, Archivos, Dispositivos, Red.")
        self.log_interrupt("Los módulos externos gestionan sus propios recursos de forma independiente.")
        
    def init_modular(self):
        """
        Inicializa la arquitectura Modular.
        El núcleo gestiona recursos básicos y los módulos pueden ser agregados o eliminados dinámicamente.
        Equivalente a initModularOS() según especificaciones.
        """
        self.log_interrupt("Arquitectura Modular inicializada: Núcleo básico activado.")
        
        # Configurar arquitectura modular
        self.kernel_mode = "modular"
        self.centralized_memory_management = True
        self.centralized_process_management = True
        
        # Inicializar componentes según especificaciones
        self.setup_modular_kernel()
        self.add_initial_modules()
        
    def setup_modular_kernel(self):
        """Configura el núcleo base de la arquitectura Modular."""
        self.log_interrupt("Núcleo Modular configurado: Gestión de recursos básicos activada.")
        
        # Inicializar módulos base que siempre están presentes (no removibles)
        self.dynamic_modules = {
            "core_process_manager": {
                "name": "Gestor de Procesos Core",
                "status": "loaded",
                "removable": False,
                "initialized": True,
                "type": "core"
            },
            "core_memory_manager": {
                "name": "Gestor de Memoria Core",
                "status": "loaded",
                "removable": False,
                "initialized": True,
                "type": "core",
                "managers": self.managers,
                "paged_managers": self.paged_managers
            }
        }
        
        self.log_interrupt("Módulos core cargados: Gestor de Procesos, Gestor de Memoria.")
        
    def add_initial_modules(self):
        """Agrega los módulos iniciales opcionales en arquitectura Modular."""
        # Cargar módulos opcionales iniciales
        self.load_module("scheduler_module", "Módulo de Planificación", removable=True)
        self.load_module("interrupt_handler", "Manejador de Interrupciones", removable=True)
        self.load_module("device_driver", "Controlador de Dispositivos", removable=True)
        
        self.log_interrupt("Módulos opcionales iniciales cargados: Planificación, Interrupciones, Dispositivos.")
        
    def load_module(self, module_id: str, module_name: str, removable: bool = True):
        """
        Carga un módulo dinámicamente en arquitectura Modular.
        
        Args:
            module_id: Identificador único del módulo
            module_name: Nombre descriptivo del módulo
            removable: Si el módulo puede ser eliminado dinámicamente
        """
        if module_id in self.dynamic_modules:
            self.log_interrupt(f"Módulo '{module_name}' ya está cargado.")
            return False
        
        self.dynamic_modules[module_id] = {
            "name": module_name,
            "status": "loaded",
            "removable": removable,
            "initialized": True,
            "load_tick": self.tick_count
        }
        
        self.log_interrupt(f"Módulo '{module_name}' cargado dinámicamente.")
        self.log_layer_flow("Núcleo Base", module_name, "Integración de módulo dinámico")
        return True
        
    def unload_module(self, module_id: str):
        """
        Descarga un módulo dinámicamente en arquitectura Modular.
        
        Args:
            module_id: Identificador único del módulo a descargar
        """
        if module_id not in self.dynamic_modules:
            self.log_interrupt(f"Módulo '{module_id}' no encontrado.")
            return False
        
        module = self.dynamic_modules[module_id]
        
        if not module.get("removable", False):
            self.log_interrupt(f"Módulo '{module['name']}' no puede ser eliminado (módulo core).")
            return False
        
        module_name = module["name"]
        del self.dynamic_modules[module_id]
        self.log_interrupt(f"Módulo '{module_name}' descargado dinámicamente.")
        self.log_layer_flow(module_name, "Núcleo Base", "Desconexión de módulo dinámico")
        return True
        
    def get_module_status(self) -> Dict:
        """
        Retorna el estado de los módulos según la arquitectura.
        """
        if self.architecture == "Monolithic":
            return {
                "architecture": "Monolithic",
                "kernel_mode": "monolithic",
                "modules": "Todo integrado en núcleo único"
            }
        elif self.architecture == "Microkernel":
            return {
                "architecture": "Microkernel",
                "kernel_mode": "microkernel",
                "external_modules": {k: {"name": v["name"], "status": v["status"]} 
                                    for k, v in self.external_modules.items()},
                "ipc_enabled": self.ipc_enabled
            }
        elif self.architecture == "Modular":
            return {
                "architecture": "Modular",
                "kernel_mode": "modular",
                "dynamic_modules": {k: {"name": v["name"], "status": v["status"], 
                                     "removable": v.get("removable", False)} 
                                   for k, v in self.dynamic_modules.items()}
            }
        return {}

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
        
        # Gestión de memoria según arquitectura
        allocated = self._allocate_memory(p)
        
        if allocated:
            # El proceso permanece en NEW hasta el siguiente tick, cuando se moverá a READY
            # No llamamos a scheduler.add_process aquí, se hará en update_processes
            arch_prefix = f"[{self.architecture.upper()}]"
            if self.architecture == "Monolithic":
                self.log_interrupt(f"{arch_prefix} Process {p.name} creado - Gestionado centralizadamente por el núcleo único (Priority: {p.priority})")
            elif self.architecture == "Microkernel":
                self.log_interrupt(f"{arch_prefix} Process {p.name} creado - Gestionado por el microkernel (Priority: {p.priority})")
            else:  # Modular
                self.log_interrupt(f"{arch_prefix} Process {p.name} creado - Gestionado por módulo 'Gestor de Procesos Core' (Priority: {p.priority})")
                self.log_layer_flow("Núcleo Base", "Gestor de Procesos Core", f"Registrar proceso {p.name}")
        else:
            p.state = "TERMINATED"
            p.finish_tick = self.tick_count  # Establecer finish_tick para que pueda ser eliminado después
            self.log_interrupt(f"Process {p.name} creation failed (Memory Full).")
            # Release memory from any manager that might have allocated (e.g. best/worst) even if first failed
            self._release_memory(p)
            
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
        
        # Gestión de memoria según arquitectura
        allocated = self._allocate_memory(p)
        
        if allocated:
            # El proceso permanece en NEW hasta el siguiente tick, cuando se moverá a READY
            # No llamamos a scheduler.add_process aquí, se hará en update_processes
            arch_prefix = f"[{self.architecture.upper()}]"
            if self.architecture == "Monolithic":
                self.log_interrupt(f"{arch_prefix} Process {p.name} creado automáticamente - Gestionado centralizadamente por el núcleo único (Priority: {p.priority})")
            elif self.architecture == "Microkernel":
                self.log_interrupt(f"{arch_prefix} Process {p.name} creado automáticamente - Gestionado por el microkernel (Priority: {p.priority})")
            else:  # Modular
                self.log_interrupt(f"{arch_prefix} Process {p.name} creado automáticamente - Gestionado por módulo 'Gestor de Procesos Core' (Priority: {p.priority})")
                self.log_layer_flow("Núcleo Base", "Gestor de Procesos Core", f"Registrar proceso {p.name}")
        else:
            p.state = "TERMINATED" # Rejected due to memory
            p.finish_tick = self.tick_count  # Establecer finish_tick para que pueda ser eliminado después
            # Release memory from any manager that might have allocated (e.g. best/worst) even if first failed
            self._release_memory(p)
            
        return p

    def release_process(self, p: Process):
        # Liberar memoria según arquitectura
        self._release_memory(p)
        p.state = "TERMINATED"
        p.finish_tick = self.tick_count
        self.metrics.record_process_completion(p, self.tick_count)
        self.log_interrupt(f"Process {p.name} terminated.")
        
    def _allocate_memory(self, process: Process) -> bool:
        """
        Asigna memoria a un proceso según la arquitectura del sistema.
        En Monolithic y Modular: asignación directa desde el núcleo.
        En Microkernel: asignación a través del módulo externo de memoria.
        """
        allocated = False
        
        if self.architecture == "Microkernel":
            # En microkernel, la memoria se gestiona a través del módulo externo
            if "memory_service" in self.external_modules:
                memory_module = self.external_modules["memory_service"]
                managers = memory_module.get("managers", self.managers)
                paged_managers = memory_module.get("paged_managers", self.paged_managers)
                
                self.log_interrupt(f"[MICROKERNEL] Asignando memoria a {process.name} a través del módulo externo 'Servicio de Memoria'")
                
                for alg, manager in managers.items():
                    result = manager.allocate(process)
                    self.metrics.update(result)
                    if alg == 'first' and result.success:
                        allocated = True
                        self.log_interrupt(f"[MICROKERNEL] Memoria asignada: {process.size_mb}MB para {process.name} (gestionado por módulo externo)")
                
                # Asignar también en gestores paginados
                for alg, paged_manager in paged_managers.items():
                    paged_result = paged_manager.allocate(process, self.tick_count)
        elif self.architecture == "Monolithic":
            # Monolithic: asignación directa desde el núcleo único
            self.log_interrupt(f"[MONOLITHIC] Asignando memoria a {process.name} directamente desde el núcleo único")
            
            for alg, manager in self.managers.items():
                result = manager.allocate(process)
                self.metrics.update(result)
                if alg == 'first' and result.success:
                    allocated = True
                    self.log_interrupt(f"[MONOLITHIC] Memoria asignada: {process.size_mb}MB para {process.name} (gestionado centralizadamente)")
            
            # Asignar también en gestores paginados
            for alg, paged_manager in self.paged_managers.items():
                paged_result = paged_manager.allocate(process, self.tick_count)
        else:  # Modular
            # Modular: asignación directa desde el núcleo (pero con estructura modular)
            self.log_interrupt(f"[MODULAR] Asignando memoria a {process.name} desde el núcleo base (módulo 'Gestor de Memoria Core')")
            
            for alg, manager in self.managers.items():
                result = manager.allocate(process)
                self.metrics.update(result)
                if alg == 'first' and result.success:
                    allocated = True
                    self.log_interrupt(f"[MODULAR] Memoria asignada: {process.size_mb}MB para {process.name} (gestionado por módulo core)")
            
            # Asignar también en gestores paginados
            for alg, paged_manager in self.paged_managers.items():
                paged_result = paged_manager.allocate(process, self.tick_count)
            
            if allocated:
                self.log_layer_flow("Núcleo Base", "Gestor de Memoria Core", f"Asignar {process.size_mb}MB a {process.name}")
        
        return allocated
        
    def _release_memory(self, process: Process):
        """
        Libera memoria de un proceso según la arquitectura del sistema.
        """
        if self.architecture == "Microkernel":
            # En microkernel, la memoria se libera a través del módulo externo
            if "memory_service" in self.external_modules:
                memory_module = self.external_modules["memory_service"]
                managers = memory_module.get("managers", self.managers)
                paged_managers = memory_module.get("paged_managers", self.paged_managers)
                
                self.log_interrupt(f"[MICROKERNEL] Liberando memoria de {process.name} a través del módulo externo 'Servicio de Memoria'")
                
                for manager in managers.values():
                    manager.release(process)
                for paged_manager in paged_managers.values():
                    paged_manager.release(process)
        elif self.architecture == "Monolithic":
            # Monolithic: liberación directa desde el núcleo único
            self.log_interrupt(f"[MONOLITHIC] Liberando memoria de {process.name} directamente desde el núcleo único")
            
            for manager in self.managers.values():
                manager.release(process)
            for paged_manager in self.paged_managers.values():
                paged_manager.release(process)
        else:
            # Modular: liberación directa desde el núcleo (pero con módulos)
            self.log_interrupt(f"[MODULAR] Liberando memoria de {process.name} desde el módulo 'Gestor de Memoria Core'")
            
            for manager in self.managers.values():
                manager.release(process)
            for paged_manager in self.paged_managers.values():
                paged_manager.release(process)
            
            self.log_layer_flow("Gestor de Memoria Core", "Núcleo Base", f"Liberar memoria de {process.name}")
                
    def send_ipc_message(self, from_pid: int, to_pid: int, message: str):
        """
        Envía un mensaje IPC entre procesos (solo en arquitectura Microkernel).
        """
        if self.architecture != "Microkernel" or not self.ipc_enabled:
            return False
        
        ipc_msg = {
            "from_pid": from_pid,
            "to_pid": to_pid,
            "message": message,
            "tick": self.tick_count
        }
        self.ipc_messages.append(ipc_msg)
        
        # Mantener solo los últimos 100 mensajes
        if len(self.ipc_messages) > 100:
            self.ipc_messages.pop(0)
        
        self.log_interrupt(f"[MICROKERNEL] IPC: El microkernel coordina comunicación entre Proceso {from_pid} -> {to_pid}: {message}")
        return True

    def update_processes(self):
        # Multiprocessor Scheduling Logic
        # We have 4 CPUs. We need to fill them from the scheduler.
        
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
        
        # Gestión de recursos según arquitectura
        if self.architecture == "Microkernel":
            # En microkernel, los servicios externos se actualizan independientemente
            self._update_external_services()
        elif self.architecture == "Modular":
            # En modular, los módulos dinámicos pueden actualizarse
            self._update_dynamic_modules()
        
        # probability create new process
        if self.auto_create_processes and random.random() < 0.3:  # 30% chance
            self.create_process()
        
        # Actualizar gestores de memoria según arquitectura
        self._update_memory_managers()
        
        # Simular accesos a páginas de procesos en ejecución
        for cpu in self.cpus:
            if cpu and random.random() < 0.1:  # 10% chance de acceso a página
                page_num = random.randint(0, max(0, (cpu.size_mb // 4) - 1))
                self._access_pages(cpu, page_num)
        
        self.update_processes()
        
    def _update_memory_managers(self):
        """Actualiza los gestores de memoria según la arquitectura."""
        if self.architecture == "Microkernel":
            # En microkernel, la memoria se gestiona a través del módulo externo
            if "memory_service" in self.external_modules:
                memory_module = self.external_modules["memory_service"]
                managers = memory_module.get("managers", self.managers)
                paged_managers = memory_module.get("paged_managers", self.paged_managers)
                
                for manager in managers.values():
                    manager.tick()
                for paged_manager in paged_managers.values():
                    paged_manager.tick(self.tick_count)
        else:
            # Monolithic y Modular: actualización directa
            for manager in self.managers.values():
                manager.tick()
            for paged_manager in self.paged_managers.values():
                paged_manager.tick(self.tick_count)
                
    def _access_pages(self, process: Process, page_num: int):
        """Accede a páginas según la arquitectura."""
        if self.architecture == "Microkernel":
            if "memory_service" in self.external_modules:
                memory_module = self.external_modules["memory_service"]
                paged_managers = memory_module.get("paged_managers", self.paged_managers)
                for paged_manager in paged_managers.values():
                    paged_manager.access_page(process, page_num, self.tick_count)
        else:
            for paged_manager in self.paged_managers.values():
                paged_manager.access_page(process, page_num, self.tick_count)
                
    def _update_external_services(self):
        """Actualiza los servicios externos en arquitectura Microkernel."""
        for module_id, module in self.external_modules.items():
            if module.get("status") == "active":
                # Simular actividad del servicio
                if module_id == "memory_service":
                    # El servicio de memoria ya se actualiza en _update_memory_managers
                    pass
                elif module_id == "file_service":
                    # Simular operaciones de archivos
                    if random.random() < 0.05:  # 5% chance
                        self.log_interrupt(f"Servicio de Archivos: Operación completada.")
                elif module_id == "device_service":
                    # Simular operaciones de dispositivos
                    if random.random() < 0.05:  # 5% chance
                        self.log_interrupt(f"Servicio de Dispositivos: I/O completado.")
                        
    def _update_dynamic_modules(self):
        """Actualiza los módulos dinámicos en arquitectura Modular."""
        for module_id, module in self.dynamic_modules.items():
            if module.get("status") == "loaded":
                # Simular actividad del módulo
                if "scheduler" in module_id.lower() or "planificación" in module.get("name", "").lower():
                    # El módulo de planificación ya está activo
                    pass
                elif "interrupt" in module_id.lower() or "interrupcion" in module.get("name", "").lower():
                    # Módulo de interrupciones activo
                    pass
                elif "device" in module_id.lower() or "dispositivo" in module.get("name", "").lower():
                    # Módulo de dispositivos activo
                    if random.random() < 0.03:  # 3% chance
                        self.log_interrupt(f"Módulo {module.get('name', module_id)}: Operación completada.")
                        self.log_layer_flow(module.get("name", module_id), "Núcleo Base", "Reporta operación completada")


    def active_processes(self) -> List[Process]:
        return [p for p in self.processes.values() if p.state != "TERMINATED"]


    def manager_snapshots(self):
        data = {}
        for alg, manager in self.managers.items():
            data[alg] = manager.snapshot_blocks()
        return data

    def layer_flow_events(self) -> List[str]:
        """Retorna el log actual de flujo de peticiones entre capas."""
        return list(self.layer_flow_log)

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
        self.layer_flow_log.clear()
        
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
        
        # Reinicializar arquitectura usando el método de control
        self.init_architecture(self.architecture)
            
        self.log_interrupt("Simulation reset.")
