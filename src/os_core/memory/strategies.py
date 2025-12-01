from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import MemoryBlock

class AllocationStrategy(ABC):
    @abstractmethod
    def find_block(self, blocks: List[MemoryBlock], size: int) -> Optional[int]:
        pass

class FirstFitStrategy(AllocationStrategy):
    def find_block(self, blocks: List[MemoryBlock], size: int) -> Optional[int]:
        for i, b in enumerate(blocks):
            if b.free and b.size >= size:
                return i
        return None

class BestFitStrategy(AllocationStrategy):
    def find_block(self, blocks: List[MemoryBlock], size: int) -> Optional[int]:
        free_blocks = [b for b in blocks if b.free and b.size >= size]
        if not free_blocks:
            return None
        best_block = min(free_blocks, key=lambda b: b.size)
        return blocks.index(best_block)

class WorstFitStrategy(AllocationStrategy):
    def find_block(self, blocks: List[MemoryBlock], size: int) -> Optional[int]:
        free_blocks = [b for b in blocks if b.free and b.size >= size]
        if not free_blocks:
            return None
        worst_block = max(free_blocks, key=lambda b: b.size)
        return blocks.index(worst_block)
