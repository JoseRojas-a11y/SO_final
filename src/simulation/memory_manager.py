from __future__ import annotations
from typing import List, Optional, Dict
from .models import MemoryBlock, Process

class AllocationResult:
    def __init__(self, success: bool, fragmentation: float, efficiency: float, algorithm: str):
        self.success = success
        self.fragmentation = fragmentation
        self.efficiency = efficiency
        self.algorithm = algorithm

class MemoryManager:
    def __init__(self, total_mb: int, algorithm: str):
        self.total_mb = total_mb
        self.algorithm = algorithm  # 'first', 'best', 'worst'
        self.blocks: List[MemoryBlock] = [MemoryBlock(0, total_mb, None)]
        self.allocated_processes: Dict[int, int] = {}  # pid -> size

    def allocate(self, process: Process) -> AllocationResult:
        size = process.size_mb
        candidate_index = None
        free_blocks = [b for b in self.blocks if b.free and b.size >= size]

        if not free_blocks:
            return AllocationResult(False, self.fragmentation_ratio(), self.efficiency(), self.algorithm)

        if self.algorithm == 'first':
            for i, b in enumerate(self.blocks):
                if b.free and b.size >= size:
                    candidate_index = i
                    break
        elif self.algorithm == 'best':
            best_block = min(free_blocks, key=lambda b: b.size)
            candidate_index = self.blocks.index(best_block)
        elif self.algorithm == 'worst':
            worst_block = max(free_blocks, key=lambda b: b.size)
            candidate_index = self.blocks.index(worst_block)
        else:
            raise ValueError('Unknown algorithm')

        if candidate_index is None:
            # fallback safety, shouldn't happen because free_blocks not empty and algorithm handled
            return AllocationResult(False, self.fragmentation_ratio(), self.efficiency(), self.algorithm)

        block = self.blocks[candidate_index]
        if block.size == size:
            block.process_pid = process.pid
        else:
            # split
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

    def merge_free(self):
        merged: List[MemoryBlock] = []
        for block in self.blocks:
            if not merged:
                merged.append(block)
                continue
            last = merged[-1]
            if last.free and block.free:
                # merge
                merged[-1] = MemoryBlock(last.start, block.end, None)
            else:
                merged.append(block)
        self.blocks = merged

    def fragmented_free_space(self) -> int:
        # external fragmentation: sum of free blocks smaller than largest alloc request possible? Here we treat all free blocks except largest
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
        """Compacts memory by moving all allocated blocks to the start."""
        allocated_blocks = [b for b in self.blocks if not b.free]
        if not allocated_blocks:
            # All free, just one big block
            self.blocks = [MemoryBlock(0, self.total_mb, None)]
            return

        new_blocks = []
        current_pos = 0
        
        for block in allocated_blocks:
            size = block.size
            # Create new block at current_pos
            new_b = MemoryBlock(current_pos, current_pos + size, block.process_pid)
            new_blocks.append(new_b)
            current_pos += size
            
        # Add remaining free space
        if current_pos < self.total_mb:
            new_blocks.append(MemoryBlock(current_pos, self.total_mb, None))
            
        self.blocks = new_blocks

