from __future__ import annotations
from typing import List, Optional, Dict, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import collections
from ..models import PageTableEntry

@dataclass
class TLBEntry:
    page_number: int
    frame_number: int
    pid: int
    last_accessed: int = 0

class TLB:
    def __init__(self, size: int = 16, enabled: bool = True):
        self.size = size
        self.enabled = enabled
        self.entries: List[TLBEntry] = []
        self.hits = 0
        self.misses = 0

    def lookup(self, pid: int, page_number: int, current_tick: int) -> Optional[int]:
        if not self.enabled:
            return None
            
        for entry in self.entries:
            if entry.pid == pid and entry.page_number == page_number:
                self.hits += 1
                entry.last_accessed = current_tick
                return entry.frame_number
        
        self.misses += 1
        return None

    def update(self, pid: int, page_number: int, frame_number: int, current_tick: int):
        if not self.enabled:
            return

        # Check if already exists to update
        for entry in self.entries:
            if entry.pid == pid and entry.page_number == page_number:
                entry.frame_number = frame_number
                entry.last_accessed = current_tick
                return

        # Replace if full (LRU)
        if len(self.entries) >= self.size:
            victim = min(self.entries, key=lambda e: e.last_accessed)
            self.entries.remove(victim)
        
        self.entries.append(TLBEntry(pid, page_number, frame_number, current_tick))

    def flush_process(self, pid: int):
        self.entries = [e for e in self.entries if e.pid != pid]

    def flush_all(self):
        self.entries.clear()

class PageTable(ABC):
    @abstractmethod
    def add_entry(self, entry: PageTableEntry):
        pass

    @abstractmethod
    def remove_entry(self, page_number: int):
        pass

    @abstractmethod
    def get_entry(self, page_number: int) -> Optional[PageTableEntry]:
        pass

    @abstractmethod
    def get_all_entries(self) -> List[PageTableEntry]:
        pass

class SingleLevelPageTable(PageTable):
    def __init__(self):
        self.entries: Dict[int, PageTableEntry] = {}

    def add_entry(self, entry: PageTableEntry):
        self.entries[entry.page_number] = entry

    def remove_entry(self, page_number: int):
        if page_number in self.entries:
            del self.entries[page_number]

    def get_entry(self, page_number: int) -> Optional[PageTableEntry]:
        return self.entries.get(page_number)

    def get_all_entries(self) -> List[PageTableEntry]:
        return list(self.entries.values())

class TwoLevelPageTable(PageTable):
    def __init__(self, directory_size: int = 1024):
        # Level 1: Directory -> Level 2: Table -> Entry
        self.directory: Dict[int, Dict[int, PageTableEntry]] = {}
        self.directory_size = directory_size

    def _get_indexes(self, page_number: int):
        dir_idx = page_number // self.directory_size
        table_idx = page_number % self.directory_size
        return dir_idx, table_idx

    def add_entry(self, entry: PageTableEntry):
        dir_idx, table_idx = self._get_indexes(entry.page_number)
        if dir_idx not in self.directory:
            self.directory[dir_idx] = {}
        self.directory[dir_idx][table_idx] = entry

    def remove_entry(self, page_number: int):
        dir_idx, table_idx = self._get_indexes(page_number)
        if dir_idx in self.directory and table_idx in self.directory[dir_idx]:
            del self.directory[dir_idx][table_idx]
            if not self.directory[dir_idx]:
                del self.directory[dir_idx]

    def get_entry(self, page_number: int) -> Optional[PageTableEntry]:
        dir_idx, table_idx = self._get_indexes(page_number)
        if dir_idx in self.directory:
            return self.directory[dir_idx].get(table_idx)
        return None

    def get_all_entries(self) -> List[PageTableEntry]:
        all_entries = []
        for table in self.directory.values():
            all_entries.extend(table.values())
        return all_entries

class HashedPageTable(PageTable):
    def __init__(self, table_size: int = 127):
        self.table_size = table_size
        self.table: Dict[int, List[PageTableEntry]] = collections.defaultdict(list)

    def _hash(self, page_number: int) -> int:
        return page_number % self.table_size

    def add_entry(self, entry: PageTableEntry):
        h = self._hash(entry.page_number)
        # Remove existing if present to avoid duplicates
        self.remove_entry(entry.page_number)
        self.table[h].append(entry)

    def remove_entry(self, page_number: int):
        h = self._hash(page_number)
        self.table[h] = [e for e in self.table[h] if e.page_number != page_number]
        if not self.table[h]:
            del self.table[h]

    def get_entry(self, page_number: int) -> Optional[PageTableEntry]:
        h = self._hash(page_number)
        for entry in self.table[h]:
            if entry.page_number == page_number:
                return entry
        return None

    def get_all_entries(self) -> List[PageTableEntry]:
        all_entries = []
        for bucket in self.table.values():
            all_entries.extend(bucket)
        return all_entries

class InvertedPageTable(PageTable):
    # Note: In a real OS, Inverted Page Table is global. 
    # Here, for simulation simplicity per process view, we might wrap it or treat it distinctively.
    # However, to fit the interface 'per process' requested (RAM vs ROM view per process usually implies owned tables),
    # we'll implement a per-process view of it OR a shared global structure simulation.
    # Given the requirements "guardando referencias que mediantes tablas de paginación... puedan encontrar la dirección física",
    # we will implement it such that it behaves correctly for the interface.
    
    def __init__(self, pid: int):
        self.pid = pid
        self.entries: Dict[int, PageTableEntry] = {}

    def add_entry(self, entry: PageTableEntry):
        self.entries[entry.page_number] = entry

    def remove_entry(self, page_number: int):
        if page_number in self.entries:
            del self.entries[page_number]

    def get_entry(self, page_number: int) -> Optional[PageTableEntry]:
        return self.entries.get(page_number)

    def get_all_entries(self) -> List[PageTableEntry]:
        return list(self.entries.values())

class MMU:
    def __init__(self, memory_manager, tlb_enabled: bool = True, page_table_type: str = "SingleLevel"):
        self.memory_manager = memory_manager
        self.tlb = TLB(enabled=tlb_enabled)
        self.page_table_type = page_table_type
        # Inverted table effectively is often global, but we store per-pid for simulation object management
        self.page_tables: Dict[int, PageTable] = {} 

    def create_page_table(self, pid: int) -> PageTable:
        if self.page_table_type == "SingleLevel":
            return SingleLevelPageTable()
        elif self.page_table_type == "TwoLevel":
            return TwoLevelPageTable()
        elif self.page_table_type == "Hashed":
            return HashedPageTable()
        elif self.page_table_type == "Inverted":
            return InvertedPageTable(pid)
        return SingleLevelPageTable()

    def get_process_table(self, pid: int) -> Optional[PageTable]:
        return self.page_tables.get(pid)

    def allocate_page_table(self, pid: int):
        self.page_tables[pid] = self.create_page_table(pid)

    def release_process_resources(self, pid: int):
        self.tlb.flush_process(pid)
        if pid in self.page_tables:
            del self.page_tables[pid]

    def translate(self, pid: int, page_number: int, current_tick: int) -> Union[int, str]:
        # 1. TLB Lookup
        frame = self.tlb.lookup(pid, page_number, current_tick)
        if frame is not None:
            return frame # TLB Hit

        # 2. Page Table Walk
        table = self.page_tables.get(pid)
        if not table:
            return "SEGMENTATION_FAULT"
        
        entry = table.get_entry(page_number)
        if not entry:
             return "PAGE_FAULT"
        
        if not entry.valid:
            return "PAGE_FAULT"

        # 3. Update TLB
        if entry.frame_number is not None:
             self.tlb.update(pid, page_number, entry.frame_number, current_tick)
             entry.last_accessed = current_tick
             return entry.frame_number

        return "PAGE_FAULT"
