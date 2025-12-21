from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QTableWidget,
    QHeaderView, QTableWidgetItem, QProgressBar, QScrollArea, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from ..components.memory_bar import MemoryBar

class StorageUsageWidget(QWidget):
    def __init__(self, total_virtual_mb, allocated_virtual_mb):
        super().__init__()
        self.total = total_virtual_mb
        self.used = allocated_virtual_mb
        self.setMinimumHeight(120) 
    
    def update_values(self, total, used):
        self.total = total
        self.used = used
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Pie Chart
        size = min(w, h) - 10
        rect_x = 10
        rect_y = (h - size) // 2
        
        if self.total > 0:
            angle = int((self.used / self.total) * 360 * 16)
        else:
            angle = 0
            
        painter.setBrush(QColor(50, 50, 150)) # Used
        painter.drawPie(rect_x, rect_y, size, size, 90 * 16, -angle)
        
        painter.setBrush(QColor(200, 200, 200)) # Free
        painter.drawPie(rect_x, rect_y, size, size, 90 * 16 - angle, -(360 * 16 - angle))
        
        # Legend
        text_x = rect_x + size + 20
        painter.drawText(text_x, 30, f"Total ROM: {self.total} MB")
        
        painter.setBrush(QColor(50, 50, 150))
        painter.drawRect(text_x, 45, 10, 10)
        painter.drawText(text_x + 15, 55, f"Usado: {self.used} MB")
        
        painter.setBrush(QColor(200, 200, 200))
        painter.drawRect(text_x, 65, 10, 10)
        painter.drawText(text_x + 15, 75, f"Libre: {self.total - self.used} MB")

class MemoryView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        
        layout = QVBoxLayout(self)
        
        # --- SECTION 1: RAM Blocks ---
        self.ram_group = QGroupBox("Memoria Principal (RAM)")
        self.ram_layout = QVBoxLayout(self.ram_group)
        self.unit_bars = {}
        self.unit_labels = {}
        
        # Dynamic container for bars
        self.bars_container = QWidget()
        self.bars_layout = QVBoxLayout(self.bars_container)
        self.bars_layout.setContentsMargins(0, 0, 0, 0)
        self.ram_layout.addWidget(self.bars_container)
        
        # Initialize bars based on engine units
        self._init_ram_bars()
        
        layout.addWidget(self.ram_group, stretch=2)
        
        # --- SECTION 2: Info & Stats (MMU + ROM) ---
        mid_layout = QHBoxLayout()
        
        # MMU/Config Stats
        self.mmu_group = QGroupBox("Gestión MMU & Estadísticas")
        mmu_layout = QVBoxLayout(self.mmu_group)
        
        self.config_label = QLabel()
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        self.config_label.setStyleSheet("font-weight: bold; color: #333;")
        
        mmu_layout.addWidget(self.config_label)
        mmu_layout.addWidget(self.stats_label)
        mmu_layout.addStretch()
        
        mid_layout.addWidget(self.mmu_group, stretch=1)
        
        # Storage Pie Chart
        self.rom_group = QGroupBox("Almacenamiento (Swap/ROM)")
        rom_layout = QVBoxLayout(self.rom_group)
        self.storage_widget = StorageUsageWidget(1000, 0)
        rom_layout.addWidget(self.storage_widget)
        
        mid_layout.addWidget(self.rom_group, stretch=1)
        
        layout.addLayout(mid_layout, stretch=1)

        # --- SECTION 3: Logs ---
        log_group = QGroupBox("Bitácora de Traducción y Fallos de Página")
        log_layout = QVBoxLayout(log_group)
        
        self.log_area = QLabel("Esperando actividad...")
        self.log_area.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.log_area.setStyleSheet("padding: 5px; font-family: Consolas; font-size: 11px;")
        self.log_area.setWordWrap(True)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.log_area)
        
        log_layout.addWidget(scroll)
        layout.addWidget(log_group, stretch=2)

    def _init_ram_bars(self):
        # Clear existing
        for i in reversed(range(self.bars_layout.count())): 
            self.bars_layout.itemAt(i).widget().setParent(None)
        
        self.unit_bars = {}
        self.unit_labels = {}
        
        for i, unit in enumerate(getattr(self.engine, 'memory_units', [])):
            container = QWidget()
            l = QVBoxLayout(container)
            l.setContentsMargins(0, 5, 0, 5)
            
            header = QLabel(f"Unidad {i+1} ({unit.manager.total_mb} MB)")
            header.setStyleSheet("font-weight: bold;")
            l.addWidget(header)
            
            bar = MemoryBar(unit.manager.snapshot_blocks(), unit.manager.total_mb)
            bar.setMinimumHeight(60)
            l.addWidget(bar)
            
            stats = QLabel("...")
            l.addWidget(stats)
            
            self.unit_bars[i] = bar
            self.unit_labels[i] = stats
            
            self.bars_layout.addWidget(container)

    def refresh_all(self):
        # Update RAM Bars
        # If unit count changed (reset), re-init
        if len(self.unit_bars) != len(self.engine.memory_units):
            self._init_ram_bars()

        for i, unit in enumerate(self.engine.memory_units):
            bar = self.unit_bars.get(i)
            if bar:
                blocks = unit.manager.snapshot_blocks()
                bar.set_blocks(blocks)
                bar.repaint() # Force repaint
            
            label = self.unit_labels.get(i)
            if label:
                used = sum(b.size for b in unit.manager.blocks if not b.free)
                pm = unit.paged_manager
                label.setText(
                    f"Usado: {used}MB | Frag: {unit.manager.fragmentation_ratio()*100:.1f}% | "
                    f"Faults: {pm.page_faults} | Hits: {pm.page_hits}"
                )

        # Update MMU Stats
        s = self.engine.storage_overview()
        
        # Obtener configuración actual (asumiendo homogénea o tomando la primera unidad)
        alloc_alg = self.engine.memory_units[0].alloc_alg if self.engine.memory_units else "N/A"
        page_alg = self.engine.memory_units[0].page_alg if self.engine.memory_units else "N/A"
        storage_type = getattr(self.engine, 'storage_type', 'HDD')
        access_time = getattr(self.engine, 'storage_access_times', {}).get(storage_type, 15)
        
        self.config_label.setText(
            f"Gestión RAM: {alloc_alg} | Paginación: {page_alg}\n"
            f"TLB: {'ON' if self.engine.tlb_enabled else 'OFF'} | "
            f"Tabla Páginas: {self.engine.page_table_type}"
        )
        
        self.stats_label.setText(
            f"Total Faults: {s['total_page_faults']} | Total Hits: {s['total_hits']}\n"
            f"Tasa Fallos Global: {s['fault_rate']*100:.2f}%\n"
            f"Utilización Promedio RAM: {s['avg_mem_util']*100:.1f}%\n"
            f"Almacenamiento: {storage_type} (Latencia Swap: {access_time} ticks)"
        )
        
        # Update ROM
        self.rom_group.setTitle(f"Almacenamiento Secundario ({storage_type})")
        self.storage_widget.update_values(s['virtual_total_mb'], s['used_mb'])

        # Update Logs
        # Filter interrupt log for MMU related events
        logs = [line for line in self.engine.interrupt_log 
                if "PAGE FAULT" in line or "Resolved" in line or "NO_TABLE" in line]
        text = "\n".join(reversed(logs[-15:])) if logs else "Sin actividad reciente de MMU."
        self.log_area.setText(text)
