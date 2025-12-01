from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QTableWidget,
    QHeaderView, QTableWidgetItem, QComboBox
)
from PyQt6.QtCore import Qt
from ..components.memory_bar import MemoryBar


class MemoryView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        root = QVBoxLayout(self)

        # Barras y controles por unidad de memoria
        self.units_group = QWidget()
        units_layout = QVBoxLayout(self.units_group)
        units_layout.setSpacing(10)
        self.unit_bars = {}
        self.unit_stats_labels = {}
        for i, unit in enumerate(getattr(self.engine, 'memory_units', [])):
            bar = MemoryBar(unit.manager.snapshot_blocks(), unit.manager.total_mb)
            self.unit_bars[i] = bar

            info_layout = QVBoxLayout()
            header = QLabel(f"Unidad {i+1} - {unit.manager.total_mb} MB")
            header.setStyleSheet("font-weight:bold;")
            info_layout.addWidget(header)

            # Controles de algoritmos
            ctrl = QHBoxLayout()
            alloc_label = QLabel("Asignación:")
            alloc_combo = QComboBox()
            alloc_combo.setObjectName(f"alloc_combo_{i}")
            alloc_combo.addItems(["first", "best", "worst"])
            idx = alloc_combo.findText(unit.manager.algorithm)
            if idx >= 0:
                alloc_combo.setCurrentIndex(idx)
            alloc_combo.currentTextChanged.connect(lambda name, idx=i: self._on_change_alloc_alg(idx, name))
            ctrl.addWidget(alloc_label)
            ctrl.addWidget(alloc_combo)

            page_label = QLabel("Paginación:")
            page_combo = QComboBox()
            page_combo.setObjectName(f"page_combo_{i}")
            page_combo.addItems(["FIFO", "LRU", "Optimal"])
            idxp = page_combo.findText(unit.paged_manager.replacement_alg)
            if idxp >= 0:
                page_combo.setCurrentIndex(idxp)
            page_combo.currentTextChanged.connect(lambda name, idx=i: self._on_change_page_alg(idx, name))
            ctrl.addWidget(page_label)
            ctrl.addWidget(page_combo)
            info_layout.addLayout(ctrl)

            info_layout.addWidget(bar)

            stats_label = QLabel()
            stats_label.setObjectName(f"unit_stats_{i}")
            self.unit_stats_labels[i] = stats_label
            info_layout.addWidget(stats_label)

            box = self._group(f"Memoria - Unidad {i+1}", info_layout)
            units_layout.addWidget(box)

        root.addWidget(self.units_group)

        # Tabla comparativa entre unidades
        self.units_table = QTableWidget(0, 11)
        self.units_table.setMinimumHeight(len(getattr(self.engine, 'memory_units', [])) * 30 + 50)
        self.units_table.setHorizontalHeaderLabels([
            "Unidad", "Total MB", "Usado MB", "Fragmentación %", "Eficiencia %",
            "Alg Asig.", "Alg Pagin.", "Faults", "Hits", "Fault Rate %", "Utilización %"
        ])
        header_units = self.units_table.horizontalHeader()
        if header_units:
            header_units.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        root.addWidget(self._group("Comparativa Unidades de Memoria", self.units_table))

        # Resumen general de almacenamiento
        self.storage_summary = QLabel()
        root.addWidget(self._group("Rendimiento del Sistema de Almacenamiento", self.storage_summary))

    def _group(self, title: str, content) -> QGroupBox:
        g = QGroupBox(title)
        l = QVBoxLayout(g)
        if isinstance(content, QVBoxLayout):
            w = QWidget()
            w.setLayout(content)
            l.addWidget(w)
        else:
            l.addWidget(content)
        return g

    def _set_row(self, table: QTableWidget, row: int, values):
        for c, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, c, item)

    def refresh_all(self):
        self._refresh_units()
        self._refresh_units_table()
        self._refresh_storage_summary()

    def _refresh_units(self):
        for i, unit in enumerate(getattr(self.engine, 'memory_units', [])):
            bar = self.unit_bars.get(i)
            if bar:
                bar.set_blocks(unit.manager.snapshot_blocks())
            frag = unit.manager.fragmentation_ratio() * 100
            eff = unit.manager.efficiency() * 100
            used = sum(b.size for b in unit.manager.blocks if not b.free)
            pm = unit.paged_manager
            stats_label: QLabel = self.units_group.findChild(QLabel, f"unit_stats_{i}")
            if stats_label:
                stats_label.setText(
                    f"Usado: {used} MB   Frag: {frag:.2f}%   Eff: {eff:.2f}%   "
                    f"Faults: {pm.page_faults}   Hits: {pm.page_hits}   FaultRate: {pm.page_fault_rate()*100:.2f}%   Utilización: {pm.memory_utilization()*100:.1f}%"
                )
            # activar/desactivar controles según estado de ejecución
            alloc_combo = self.units_group.findChild(QComboBox, f"alloc_combo_{i}")
            page_combo = self.units_group.findChild(QComboBox, f"page_combo_{i}")
            if alloc_combo:
                alloc_combo.setCurrentText(unit.manager.algorithm)
                alloc_combo.setEnabled(not getattr(self.engine, 'is_running', False))
            if page_combo:
                page_combo.setCurrentText(unit.paged_manager.replacement_alg)
                page_combo.setEnabled(not getattr(self.engine, 'is_running', False))

    def _refresh_units_table(self):
        stats = self.engine.memory_unit_summaries()
        self.units_table.setRowCount(len(stats))
        for r, s in enumerate(stats):
            self._set_row(self.units_table, r, [
                f"Unidad {int(s['id'])+1}",
                int(s['total_mb']),
                int(s['used_mb']),
                f"{s['fragmentation']*100:.2f}",
                f"{s['efficiency']*100:.2f}",
                s['alloc_alg'],
                s['page_alg'],
                int(s['page_faults']),
                int(s['page_hits']),
                f"{s['fault_rate']*100:.2f}",
                f"{s['mem_util']*100:.1f}",
            ])

    def _refresh_storage_summary(self):
        s = self.engine.storage_overview()
        text = (
            f"<html><body>"
            f"<table border='0' cellspacing='5' cellpadding='3'>"
            f"<tr><td>Total Memoria:</td><td>{int(s['total_mb'])} MB</td><td>Memoria Usada:</td><td>{int(s['used_mb'])} MB</td></tr>"
            f"<tr><td>Page Faults:</td><td>{int(s['total_page_faults'])}</td><td>Page Hits:</td><td>{int(s['total_hits'])}</td></tr>"
            f"<tr><td>Tasa Faults:</td><td>{s['fault_rate']*100:.2f}%</td><td>Utilización Promedio:</td><td>{s['avg_mem_util']*100:.1f}%</td></tr>"
            f"</table>"
            f"</body></html>"
        )
        self.storage_summary.setText(text)

    def _on_change_alloc_alg(self, unit_index: int, name: str):
        if hasattr(self.engine, 'set_memory_unit_alloc_alg'):
            self.engine.set_memory_unit_alloc_alg(unit_index, name)
        self.refresh_all()

    def _on_change_page_alg(self, unit_index: int, name: str):
        if hasattr(self.engine, 'set_memory_unit_page_alg'):
            self.engine.set_memory_unit_page_alg(unit_index, name)
        self.refresh_all()
