from __future__ import annotations
from typing import List, Optional, Dict, Deque
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
    def __init__(self, total_mb: int, algorithm_name: str, strategy: AllocationStrategy, auto_compact: bool = True, compact_threshold: float = 0.3):
        self.total_mb = total_mb
        self.algorithm = algorithm_name
        self.strategy = strategy
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
        if process.pid not in self.allocated_processes:
            return
        for b in self.blocks:
            if b.process_pid == process.pid:
                b.process_pid = None
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
            self.blocks = [MemoryBlock(0, self.total_mb, None)]
            self.ticks_since_compact = 0
            return
        new_blocks = []
        current_pos = 0
        for block in allocated_blocks:
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

class PagedAllocationResult:
    def __init__(self, success: bool, page_faults: int, algorithm: str, pages_allocated: int = 0):
        self.success = success
        self.page_faults = page_faults
        self.algorithm = algorithm
        self.pages_allocated = pages_allocated

class PagedMemoryManager:
    def __init__(self, total_mb: int, page_size_mb: int = 4, replacement_alg: str = "FIFO"):
        self.total_mb = total_mb
        self.page_size_mb = page_size_mb
        self.replacement_alg = replacement_alg
        self.num_frames = total_mb // page_size_mb
        self.frames: List[Page] = [Page(frame_number=i) for i in range(self.num_frames)]
        self.page_tables: Dict[int, List[PageTableEntry]] = {}
        self.fifo_queue: Deque[int] = deque()
        self.page_faults = 0
        self.page_hits = 0
        self.total_accesses = 0
        self.allocated_processes: Dict[int, int] = {}
        self.access_history: Dict[int, List[int]] = {}

    def allocate(self, process: Process, current_tick: int) -> PagedAllocationResult:
        size_mb = process.size_mb
        num_pages_needed = (size_mb + self.page_size_mb - 1) // self.page_size_mb
        page_table = []
        page_faults = 0
        for page_num in range(num_pages_needed):
            free_frame = self._find_free_frame()
            if free_frame is not None:
                frame = self.frames[free_frame]
                frame.process_pid = process.pid
                frame.page_number = page_num
                frame.loaded_tick = current_tick
                frame.last_accessed = current_tick
                entry = PageTableEntry(
                    page_number=page_num,
                    frame_number=free_frame,
                    valid=True,
                    loaded_tick=current_tick,
                    last_accessed=current_tick
                )
                page_table.append(entry)
                self.fifo_queue.append(free_frame)
            else:
                victim_frame = self._select_victim_frame(process.pid, current_tick)
                if victim_frame is None:
                    return PagedAllocationResult(False, page_faults, self.replacement_alg, len(page_table))
                old_page = self.frames[victim_frame]
                if old_page.process_pid:
                    if old_page.process_pid in self.page_tables:
                        for entry in self.page_tables[old_page.process_pid]:
                            if entry.frame_number == victim_frame:
                                entry.valid = False
                                entry.frame_number = None
                frame = self.frames[victim_frame]
                frame.process_pid = process.pid
                frame.page_number = page_num
                frame.loaded_tick = current_tick
                frame.last_accessed = current_tick
                frame.referenced = True
                frame.modified = False
                entry = PageTableEntry(
                    page_number=page_num,
                    frame_number=victim_frame,
                    valid=True,
                    loaded_tick=current_tick,
                    last_accessed=current_tick
                )
                page_table.append(entry)
                page_faults += 1
                self.page_faults += 1
                if victim_frame in self.fifo_queue:
                    self.fifo_queue.remove(victim_frame)
                self.fifo_queue.append(victim_frame)
        self.page_tables[process.pid] = page_table
        self.allocated_processes[process.pid] = num_pages_needed
        process.memory_usage_mb = num_pages_needed * self.page_size_mb
        self.total_accesses += num_pages_needed
        return PagedAllocationResult(True, page_faults, self.replacement_alg, num_pages_needed)

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
                victim = max(candidates, key=lambda x: current_tick - x[1].last_accessed)
                return victim[0]
        return None

    def access_page(self, process: Process, page_number: int, current_tick: int) -> bool:
        self.total_accesses += 1
        if process.pid not in self.page_tables:
            return False
        page_table = self.page_tables[process.pid]
        if page_number >= len(page_table):
            return False
        entry = page_table[page_number]
        if entry.valid and entry.frame_number is not None:
            self.page_hits += 1
            entry.last_accessed = current_tick
            entry.referenced = True
            frame = self.frames[entry.frame_number]
            frame.last_accessed = current_tick
            frame.referenced = True
            return True
        else:
            self.page_faults += 1
            free_frame = self._find_free_frame()
            if free_frame is not None:
                frame = self.frames[free_frame]
                frame.process_pid = process.pid
                frame.page_number = page_number
                frame.loaded_tick = current_tick
                frame.last_accessed = current_tick
                entry.frame_number = free_frame
                entry.valid = True
                entry.loaded_tick = current_tick
                entry.last_accessed = current_tick
                self.fifo_queue.append(free_frame)
            else:
                victim_frame = self._select_victim_frame(process.pid, current_tick)
                if victim_frame is not None:
                    old_page = self.frames[victim_frame]
                    if old_page.process_pid and old_page.process_pid in self.page_tables:
                        for e in self.page_tables[old_page.process_pid]:
                            if e.frame_number == victim_frame:
                                e.valid = False
                                e.frame_number = None
                    frame = self.frames[victim_frame]
                    frame.process_pid = process.pid
                    frame.page_number = page_number
                    frame.loaded_tick = current_tick
                    frame.last_accessed = current_tick
                    entry.frame_number = victim_frame
                    entry.valid = True
                    entry.loaded_tick = current_tick
                    entry.last_accessed = current_tick
                    if victim_frame in self.fifo_queue:
                        self.fifo_queue.remove(victim_frame)
                    self.fifo_queue.append(victim_frame)
            return True

    def release(self, process: Process):
        if process.pid not in self.page_tables:
            return
        page_table = self.page_tables[process.pid]
        for entry in page_table:
            if entry.valid and entry.frame_number is not None:
                frame = self.frames[entry.frame_number]
                frame.process_pid = None
                frame.page_number = None
                frame.last_accessed = 0
                frame.loaded_tick = 0
                frame.referenced = False
                frame.modified = False
                if entry.frame_number in self.fifo_queue:
                    self.fifo_queue.remove(entry.frame_number)
        del self.page_tables[process.pid]
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

    def get_page_table(self, pid: int) -> Optional[List[PageTableEntry]]:
        return self.page_tables.get(pid)

    def tick(self, current_tick: int):
        pass
