from __future__ import annotations
from typing import List, Optional, Dict, Deque, Union
from collections import deque
from ..models import MemoryBlock, Process, Page, PageTableEntry
from .strategies import AllocationStrategy

class AllocationResult:
    def __init__(self, success: bool, fragmentation: float, efficiency: float, algorithm: str):
        self.success = success
        self.fragmentation = fragmentation
        self.efficiency = efficiency
        self.algorithm = algorithm

class MemoryManager:
    def __init__(self, total_mb: int, algorithm_name: str, strategy: AllocationStrategy, auto_compact: bool = True, compact_threshold: float = 0.3, system_reserved_mb: int = 0):
        self.total_mb = total_mb
        self.algorithm = algorithm_name
        self.strategy = strategy
        self.system_reserved_mb = max(0, min(system_reserved_mb, total_mb))
        # Crear bloque reservado del sistema si aplica
        if self.system_reserved_mb > 0:
            sys_block = MemoryBlock(0, self.system_reserved_mb, 0)  # PID 0 = SO
            remainder = MemoryBlock(self.system_reserved_mb, total_mb, None)
            self.blocks: List[MemoryBlock] = [sys_block, remainder]
        else:
            self.blocks: List[MemoryBlock] = [MemoryBlock(0, total_mb, None)]
        self.allocated_processes: Dict[int, int] = {}  # pid -> size
        self.auto_compact = auto_compact
        self.compact_threshold = compact_threshold
        self.ticks_since_compact = 0
        self.compact_interval = 50

    def allocate(self, process: Process) -> AllocationResult:
        size = process.size_mb
        candidate_index = self.strategy.find_block(self.blocks, size)
        if candidate_index is None:
            return AllocationResult(False, self.fragmentation_ratio(), self.efficiency(), self.algorithm)
        block = self.blocks[candidate_index]
        if block.size == size:
            block.process_pid = process.pid
        else:
            new_block = MemoryBlock(block.start, block.start + size, process.pid)
            remainder = MemoryBlock(block.start + size, block.end, None)
            self.blocks[candidate_index] = new_block
            self.blocks.insert(candidate_index + 1, remainder)
        self.allocated_processes[process.pid] = size
        process.memory_usage_mb = size
        return AllocationResult(True, self.fragmentation_ratio(), self.efficiency(), self.algorithm)

    def release(self, process: Process):
        # Allow release even if not in allocated_processes map (safety sweep)
        blocks_cleared = 0
        for b in self.blocks:
            if b.process_pid == process.pid:
                b.process_pid = None
                blocks_cleared += 1
        
        if process.pid in self.allocated_processes:
            del self.allocated_processes[process.pid]
            
        process.memory_usage_mb = 0
        self.merge_free()
        if self.auto_compact:
            self.check_and_compact()

    def merge_free(self):
        merged: List[MemoryBlock] = []
        for block in self.blocks:
            if not merged:
                merged.append(block)
                continue
            last = merged[-1]
            if last.free and block.free:
                merged[-1] = MemoryBlock(last.start, block.end, None)
            else:
                merged.append(block)
        self.blocks = merged

    def fragmented_free_space(self) -> int:
        free_blocks = [b.size for b in self.blocks if b.free]
        if not free_blocks:
            return 0
        largest = max(free_blocks)
        return sum(s for s in free_blocks if s != largest)

    def fragmentation_ratio(self) -> float:
        frag = self.fragmented_free_space()
        return frag / self.total_mb

    def efficiency(self) -> float:
        used = sum(b.size for b in self.blocks if not b.free)
        fragmentation_penalty = self.fragmentation_ratio()
        return (used / self.total_mb) * (1 - fragmentation_penalty)

    def snapshot_blocks(self) -> List[MemoryBlock]:
        return list(self.blocks)

    def compact(self):
        allocated_blocks = [b for b in self.blocks if not b.free]
        if not allocated_blocks:
            # Preservar bloque del sistema si existe
            if self.system_reserved_mb > 0:
                sys_block = MemoryBlock(0, self.system_reserved_mb, 0)
                self.blocks = [sys_block, MemoryBlock(self.system_reserved_mb, self.total_mb, None)]
            else:
                self.blocks = [MemoryBlock(0, self.total_mb, None)]
            self.ticks_since_compact = 0
            return
        new_blocks = []
        current_pos = 0
        # Conservar bloque del sistema al inicio
        if self.system_reserved_mb > 0:
            new_blocks.append(MemoryBlock(0, self.system_reserved_mb, 0))
            current_pos = self.system_reserved_mb
        for block in allocated_blocks:
            if block.process_pid == 0:  # Saltar bloque sistema ya añadido
                continue
            size = block.size
            new_b = MemoryBlock(current_pos, current_pos + size, block.process_pid)
            new_blocks.append(new_b)
            current_pos += size
        if current_pos < self.total_mb:
            new_blocks.append(MemoryBlock(current_pos, self.total_mb, None))
        self.blocks = new_blocks
        self.ticks_since_compact = 0

    def check_and_compact(self):
        frag_ratio = self.fragmentation_ratio()
        self.ticks_since_compact += 1
        should_compact = False
        if frag_ratio >= self.compact_threshold:
            should_compact = True
        elif self.ticks_since_compact >= self.compact_interval and frag_ratio > 0.1:
            should_compact = True
        if should_compact:
            self.compact()
            return True
        return False

    def tick(self):
        if self.auto_compact:
            self.check_and_compact()

    # Expansión monótona del bloque reservado del sistema (nunca reduce)
    def expand_system_reserved(self, required_mb: int):
        required_mb = max(0, min(required_mb, self.total_mb))
        if required_mb <= self.system_reserved_mb:
            return False
        # Buscar bloque sistema al inicio
        if not self.blocks or self.blocks[0].process_pid != 0:
            return False
        sys_block = self.blocks[0]
        growth = required_mb - self.system_reserved_mb
        # Verificar espacio libre inmediato
        if len(self.blocks) > 1 and self.blocks[1].free and (sys_block.end + growth) <= self.blocks[1].end:
            # Ajustar sistema y bloque libre restante
            new_sys_end = sys_block.end + growth
            remainder_end = self.blocks[1].end
            self.blocks[0] = MemoryBlock(0, new_sys_end, 0)
            self.blocks[1] = MemoryBlock(new_sys_end, remainder_end, None)
            self.system_reserved_mb = required_mb
            return True
        # Si no hay espacio contiguo suficiente intentar compactar y reintentar
        self.compact()
        if self.blocks and self.blocks[0].process_pid == 0 and self.blocks[0].end == self.system_reserved_mb:
            # Después de compactar, intentar de nuevo
            if len(self.blocks) > 1 and self.blocks[1].free and (self.blocks[0].end + growth) <= self.blocks[1].end:
                new_sys_end = self.blocks[0].end + growth
                remainder_end = self.blocks[1].end
                self.blocks[0] = MemoryBlock(0, new_sys_end, 0)
                self.blocks[1] = MemoryBlock(new_sys_end, remainder_end, None)
                self.system_reserved_mb = required_mb
                return True
        return False

class PagedAllocationResult:
    def __init__(self, success: bool, page_faults: int, algorithm: str, pages_allocated: int = 0):
        self.success = success
        self.page_faults = page_faults
        self.algorithm = algorithm
        self.pages_allocated = pages_allocated

from .mmu import MMU, PageTable

class PagedMemoryManager:
    def __init__(self, total_mb: int, page_size_mb: int = 4, replacement_alg: str = "FIFO", 
                 tlb_enabled: bool = True, page_table_type: str = "SingleLevel"):
        self.total_mb = total_mb
        self.page_size_mb = page_size_mb
        self.replacement_alg = replacement_alg
        self.num_frames = total_mb // page_size_mb
        self.frames: List[Page] = [Page(frame_number=i) for i in range(self.num_frames)]
        
        # Integración MMU
        self.mmu = MMU(self, tlb_enabled=tlb_enabled, page_table_type=page_table_type)
        
        self.fifo_queue: Deque[int] = deque()
        self.page_faults = 0
        self.page_hits = 0
        self.total_accesses = 0
        self.allocated_processes: Dict[int, int] = {}
        self.access_history: Dict[int, List[int]] = {}

        # Simulación de almacenamiento "ROM" backing store
        # Mapea PID -> Lista de PageTableEntries que representan todo el proceso en disco
        self.backing_store: Dict[int, List[PageTableEntry]] = {}

    def allocate(self, process: Process, current_tick: int) -> PagedAllocationResult:
        size_mb = process.size_mb
        num_pages_needed = (size_mb + self.page_size_mb - 1) // self.page_size_mb
        
        # Inicializar Page Table en MMU
        self.mmu.allocate_page_table(process.pid)
        page_table_obj = self.mmu.get_process_table(process.pid) 
        
        # Crear entradas "en disco" (backing store)
        backing_entries = []
        for page_num in range(num_pages_needed):
            entry = PageTableEntry(
                page_number=page_num,
                frame_number=None,
                valid=False, # Inicialmente no cargado en RAM (Demanda)
                loaded_tick=0,
                last_accessed=0
            )
            backing_entries.append(entry)
            # También añadir a la page table del MMU como inválidas
            page_table_obj.add_entry(entry)

        self.backing_store[process.pid] = backing_entries
        self.allocated_processes[process.pid] = num_pages_needed
        process.memory_usage_mb = 0 # Inicialmente 0 en RAM física

        # Cargar algunas páginas iniciales (Pre-paging opcional, o pure demand paging)
        # Vamos a cargar la página 0 obligatoriamente para que pueda arrancar
        if num_pages_needed > 0:
             self.resolve_fault(process.pid, 0, current_tick)

        return PagedAllocationResult(True, 0, self.replacement_alg, num_pages_needed)

    def resolve_fault(self, pid: int, page_number: int, current_tick: int) -> bool:
        """Carga una página desde el backing store a un frame físico."""
        if pid not in self.backing_store:
            return False
            
        page_table_obj = self.mmu.get_process_table(pid)
        if not page_table_obj:
            return False

        entry = page_table_obj.get_entry(page_number)
        if not entry: # Should be in backing store/table even if invalid
             # Fallback check backing store logic if somehow desynced
             return False
        
        if entry.valid and entry.frame_number is not None:
            return True # Ya está cargada

        # Buscar frame libre o víctima
        free_frame = self._find_free_frame()
        victim_frame = None
        
        if free_frame is None:
            victim_frame = self._select_victim_frame(pid, current_tick)
            if victim_frame is None:
                return False # No hay memoria
            
            # Desalojar víctima
            old_page = self.frames[victim_frame]
            if old_page.process_pid:
                old_pt = self.mmu.get_process_table(old_page.process_pid)
                if old_pt and old_page.page_number is not None:
                     old_entry = old_pt.get_entry(old_page.page_number)
                     if old_entry:
                         old_entry.valid = False
                         old_entry.frame_number = None
                         # Update TLB invalidate
                         # self.mmu.tlb.flush_process(old_page.process_pid) # Simplificado

            free_frame = victim_frame
        
        # Cargar frame
        frame = self.frames[free_frame]
        frame.process_pid = pid
        frame.page_number = page_number
        frame.loaded_tick = current_tick
        frame.last_accessed = current_tick
        frame.referenced = True
        frame.modified = False
        
        # Actualizar Page Table Entry
        entry.valid = True
        entry.frame_number = free_frame
        entry.loaded_tick = current_tick
        entry.last_accessed = current_tick
        
        # Actualizar TLB explícitamente si se desea, o dejar que el próximo acceso lo haga (Miss handled)
        self.mmu.tlb.update(pid, page_number, free_frame, current_tick)
        
        # Mantener cola FIFO
        if free_frame in self.fifo_queue:
            self.fifo_queue.remove(free_frame)
        self.fifo_queue.append(free_frame)
        
        return True

    def _find_free_frame(self) -> Optional[int]:
        for i, frame in enumerate(self.frames):
            if frame.free:
                return i
        return None

    def _select_victim_frame(self, requesting_pid: int, current_tick: int) -> Optional[int]:
        if self.replacement_alg == "FIFO":
            if self.fifo_queue:
                return self.fifo_queue[0]
            for i, frame in enumerate(self.frames):
                if not frame.free:
                    return i
        elif self.replacement_alg == "LRU":
            candidates = [(i, f) for i, f in enumerate(self.frames) if not f.free]
            if candidates:
                victim = min(candidates, key=lambda x: x[1].last_accessed)
                return victim[0]
        elif self.replacement_alg == "Optimal":
            candidates = [(i, f) for i, f in enumerate(self.frames) if not f.free]
            if candidates:
                # Simplificado: el que hace más tiempo se cargó si no tenemos oráculo
                victim = min(candidates, key=lambda x: x[1].loaded_tick)
                return victim[0]
        return None

    def access_page(self, process: Process, page_number: int, current_tick: int) -> Union[bool, str]:
        """Retorna True si éxito, 'PAGE_FAULT' si fallo de página."""
        self.total_accesses += 1
        
        # Usar MMU para traducir
        result = self.mmu.translate(process.pid, page_number, current_tick)
        
        if result == "PAGE_FAULT":
            self.page_faults += 1
            return "PAGE_FAULT"
        
        if result == "SEGMENTATION_FAULT":
            return False
            
        if isinstance(result, int):
            # Éxito: result es frame number
            self.page_hits += 1
            frame = self.frames[result]
            frame.last_accessed = current_tick
            frame.referenced = True
            
            # Actualizar entrada en Page Table (Reference bit)
            pt = self.mmu.get_process_table(process.pid)
            if pt:
                entry = pt.get_entry(page_number)
                if entry:
                    entry.referenced = True
                    entry.last_accessed = current_tick
            return True
            
        return False

    def release(self, process: Process):
        self.mmu.release_process_resources(process.pid)
        if process.pid in self.backing_store:
            del self.backing_store[process.pid]
            
        # Liberar frames físicos
        for frame in self.frames:
            if frame.process_pid == process.pid:
                frame.process_pid = None
                frame.page_number = None
                frame.last_accessed = 0
                frame.loaded_tick = 0
                frame.referenced = False
                frame.modified = False
                if frame.frame_number in self.fifo_queue:
                    self.fifo_queue.remove(frame.frame_number)
        
        if process.pid in self.allocated_processes:
            del self.allocated_processes[process.pid]
        process.memory_usage_mb = 0

    def page_fault_rate(self) -> float:
        if self.total_accesses == 0:
            return 0.0
        return self.page_faults / self.total_accesses

    def memory_utilization(self) -> float:
        used_frames = sum(1 for f in self.frames if not f.free)
        return used_frames / self.num_frames if self.num_frames > 0 else 0.0

    def snapshot_frames(self) -> List[Page]:
        return list(self.frames)
    
    # Método para compatibilidad con main view que espera lista de entradas
    # PERO, con diferentes tipos de tabla, esto puede ser complejo.
    # Vamos a devolver la lista plana de todas las entradas válidas/inválidas conocidas
    def get_page_table(self, pid: int) -> Optional[List[PageTableEntry]]:
        table = self.mmu.get_process_table(pid)
        if table:
            return table.get_all_entries()
        return None

    def tick(self, current_tick: int):
        pass
