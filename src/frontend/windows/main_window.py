from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFrame, QGroupBox, QHeaderView, QDialog, QPushButton, QSpinBox, QFormLayout,
    QStackedWidget, QListWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from ...simulation.engine import SimulationEngine
from ..components.memory_bar import MemoryBar
from ..components.console import ConsoleWidget

class MainWindow(QMainWindow):
    def __init__(self, engine: SimulationEngine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle(f"Simulación SO - {engine.architecture} - {engine.scheduling_alg_name}")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central) # Main layout is horizontal: Menu | Content

        # Content Area (Stacked Widget)
        self.stack = QStackedWidget()
        
        # Page 1: Process Management
        self.page_processes = QWidget()
        proc_layout = QVBoxLayout(self.page_processes)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"<b>Arquitectura:</b> {engine.architecture}"))
        header_layout.addWidget(QLabel(f"<b>Planificador:</b> {engine.scheduling_alg_name}"))
        proc_layout.addLayout(header_layout)

        # CPU Status Panel
        cpu_group = QGroupBox("Estado de CPUs (Multiprocesador)")
        cpu_layout = QHBoxLayout(cpu_group)
        self.cpu_labels = []
        for i in range(4):
            lbl = QLabel(f"CPU {i}: Idle")
            lbl.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background-color: #333; color: white; font-weight: bold;")
            self.cpu_labels.append(lbl)
            cpu_layout.addWidget(lbl)
        proc_layout.addWidget(cpu_group)

        self.process_table = QTableWidget(0, 9)
        self.process_table.setHorizontalHeaderLabels(["PID","Nombre","Estado","CPU","CPU %","Mem MB","Restante","Espera","Prioridad"])
        header = self.process_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        proc_layout.addWidget(self.group_box("Procesos Activos", self.process_table))
        
        # Interrupt Log
        self.interrupt_list = QListWidget()
        self.interrupt_list.setMaximumHeight(150)
        proc_layout.addWidget(self.group_box("Registro de Interrupciones", self.interrupt_list))
        
        # Global Stats in Process Page
        self.global_stats_label = QLabel("Métricas Globales: ...")
        proc_layout.addWidget(self.group_box("Métricas del Sistema", self.global_stats_label))
        
        # Page 2: Memory Management
        self.page_memory = QWidget()
        mem_layout_page = QVBoxLayout(self.page_memory)
        
        self.memory_group = QWidget()
        mem_grid = QGridLayout(self.memory_group)
        mem_grid.setSpacing(10)
        self.memory_bars = {}
        for i, alg in enumerate(["first","best","worst"]):
            manager = engine.managers[alg]
            bar = MemoryBar(manager.snapshot_blocks(), manager.total_mb)
            self.memory_bars[alg] = bar
            
            info_layout = QVBoxLayout()
            info_layout.addWidget(QLabel(f"Algoritmo: {alg}"))
            info_layout.addWidget(bar)
            
            # Compact Button
            btn_compact = QPushButton("Compactar Memoria")
            btn_compact.clicked.connect(lambda checked, a=alg: self.compact_memory(a))
            info_layout.addWidget(btn_compact)
            
            stats_label = QLabel()
            stats_label.setObjectName(f"stats_{alg}")
            info_layout.addWidget(stats_label)
            
            box = self.group_box(f"Memoria {alg}", self.wrap_layout(info_layout))
            mem_grid.addWidget(box, i, 0)
        mem_layout_page.addWidget(self.memory_group)

        self.stats_table = QTableWidget(0,4)
        self.stats_table.setHorizontalHeaderLabels(["Algoritmo","Éxito %","Fragmentación %","Eficiencia %"])
        header_stats = self.stats_table.horizontalHeader()
        if header_stats:
            header_stats.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mem_layout_page.addWidget(self.group_box("Comparativa Memoria", self.stats_table))


        # Add pages to stack
        self.stack.addWidget(self.page_processes)
        self.stack.addWidget(self.page_memory)

        # Navigation & Console (Right Side)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.nav_list = QListWidget()
        self.nav_list.addItem("Gestión de Procesos")
        self.nav_list.addItem("Gestión de Memoria")
        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)
        
        right_layout.addWidget(self.nav_list)
        
        # Simulation Controls
        controls_group = QGroupBox("Control Simulación")
        controls_layout = QGridLayout(controls_group)
        
        self.btn_pause_resume = QPushButton("Activar")
        self.btn_pause_resume.setStyleSheet("background-color: #00AA00; color: white;")
        self.btn_pause_resume.clicked.connect(self.toggle_simulation)
        controls_layout.addWidget(self.btn_pause_resume, 0, 0)
        
        self.btn_restart = QPushButton("Reiniciar")
        self.btn_restart.setStyleSheet("background-color: #AA0000; color: white;")
        self.btn_restart.clicked.connect(self.restart_simulation)
        controls_layout.addWidget(self.btn_restart, 0, 1)
        
        lbl_speed = QLabel("Velocidad (ms):")
        controls_layout.addWidget(lbl_speed, 1, 0)
        
        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(10, 5000)
        self.spin_speed.setValue(1000)
        self.spin_speed.setSingleStep(50)
        self.spin_speed.setEnabled(True) # Only enabled when paused
        self.spin_speed.valueChanged.connect(self.set_speed)
        controls_layout.addWidget(self.spin_speed, 1, 1)
        
        right_layout.addWidget(controls_group)
        
        self.console = ConsoleWidget(self.engine, self)
        right_layout.addWidget(self.console)
        
        right_widget.setFixedWidth(300)

        # Add to main layout
        main_layout.addWidget(self.stack)
        main_layout.addWidget(right_widget)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)

    def group_box(self, title: str, widget: QWidget) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.addWidget(widget)
        return box

    def wrap_layout(self, layout: QVBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def on_tick(self):
        self.engine.tick()
        self.refresh_process_table()
        self.refresh_memory()
        self.refresh_stats_table()
        self.refresh_global_stats()
        self.refresh_cpu_status()
        self.refresh_interrupt_log()

    def refresh_cpu_status(self):
        for i, lbl in enumerate(self.cpu_labels):
            p = self.engine.cpus[i]
            if p:
                lbl.setText(f"CPU {i}: {p.name} (PID {p.pid})")
                lbl.setStyleSheet("background-color: #00AA00; color: white; font-weight: bold;")
            else:
                lbl.setText(f"CPU {i}: Idle")
                lbl.setStyleSheet("background-color: #333; color: white; font-weight: bold;")

    def refresh_interrupt_log(self):
        # Sync list widget with engine log
        # Simple approach: clear and refill if length differs or just refill always (inefficient but safe for small logs)
        if self.interrupt_list.count() != len(self.engine.interrupt_log):
            self.interrupt_list.clear()
            for msg in self.engine.interrupt_log:
                self.interrupt_list.addItem(msg)
            self.interrupt_list.scrollToBottom()

    def refresh_process_table(self):
        processes = self.engine.active_processes()
        # Sort by PID for stability
        processes.sort(key=lambda p: p.pid)
        
        self.process_table.setRowCount(len(processes))
        for r, p in enumerate(processes):
            cpu_str = str(p.cpu_id) if p.cpu_id is not None else "-"
            self.set_row(self.process_table, r, [
                p.pid,
                p.name,
                p.state,
                cpu_str,
                f"{p.cpu_usage:.1f}",
                p.memory_usage_mb,
                f"{p.remaining_ticks}/{p.duration_ticks}",
                p.waiting_ticks,
                p.priority
            ])

    def refresh_memory(self):
        for alg, bar in self.memory_bars.items():
            manager = self.engine.managers[alg]
            bar.set_blocks(manager.snapshot_blocks())
            frag = manager.fragmentation_ratio()*100
            eff = manager.efficiency()*100
            used = sum(b.size for b in manager.blocks if not b.free)
            stats_label: QLabel = self.memory_group.findChild(QLabel, f"stats_{alg}")
            if stats_label:
                stats_label.setText(f"Usado: {used} MB\nFrag: {frag:.2f}%\nEff: {eff:.2f}%")

    def refresh_stats_table(self):
        stats = self.engine.algorithm_stats()
        self.stats_table.setRowCount(len(stats))
        for r,(alg,s) in enumerate(stats.items()):
            self.set_row(self.stats_table, r, [
                alg,
                f"{s['success_rate']*100:.1f}",
                f"{s['fragmentation']*100:.2f}",
                f"{s['efficiency']*100:.2f}"
            ])
            
    def refresh_global_stats(self):
        m = self.engine.metrics
        avg_turnaround = m.total_turnaround_time / m.completed_processes if m.completed_processes else 0
        avg_waiting = m.total_waiting_time / m.completed_processes if m.completed_processes else 0 
        
        # CPU Util calculation (Instantaneous)
        busy_cpus = sum(1 for cpu in self.engine.cpus if cpu is not None)
        cpu_util = (busy_cpus / 4) * 100
        
        text = (
            f"<html><head/><body>"
            f"<p><b>Métricas del Sistema:</b></p>"
            f"<table border='0' cellspacing='5'>"
            f"<tr><td>Procesos Totales:</td><td>{m.total_processes}</td></tr>"
            f"<tr><td>Completados:</td><td>{m.completed_processes}</td></tr>"
            f"<tr><td>Turnaround Promedio:</td><td>{avg_turnaround:.2f} ticks</td></tr>"
            f"<tr><td>Tiempo Espera Promedio:</td><td>{avg_waiting:.2f} ticks</td></tr>"
            f"<tr><td>Utilización CPU Global:</td><td>{cpu_util:.2f}%</td></tr>"
            f"</table></body></html>"
        )
        self.global_stats_label.setText(text)

    def set_row(self, table: QTableWidget, row: int, values):
        for c, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, c, item)

    def create_manual_process(self):
        # Simple dialog to get size and duration
        d = QDialog(self)
        d.setWindowTitle("Crear Proceso")
        l = QFormLayout(d)
        sb_size = QSpinBox()
        sb_size.setRange(1, 128)
        sb_size.setValue(16)
        l.addRow("Tamaño (MB):", sb_size)
        
        sb_dur = QSpinBox()
        sb_dur.setRange(5, 200)
        sb_dur.setValue(50)
        l.addRow("Duración (ticks):", sb_dur)
        
        btn = QPushButton("Crear")
        btn.clicked.connect(d.accept)
        l.addRow(btn)
        
        if d.exec() == QDialog.DialogCode.Accepted:
            self.engine.manual_create_process(sb_size.value(), sb_dur.value())

    def compact_memory(self, alg: str):
        self.engine.managers[alg].compact()
        self.refresh_memory()

    def toggle_simulation(self):
        if self.timer.isActive():
            self.pause_simulation()
        else:
            self.resume_simulation()

    def pause_simulation(self):
        self.timer.stop()
        self.btn_pause_resume.setText("Reanudar")
        self.spin_speed.setEnabled(True)
        self.console.print_msg("Simulación pausada.")

    def resume_simulation(self):
        self.timer.start(self.spin_speed.value())
        self.btn_pause_resume.setText("Pausar")
        self.spin_speed.setEnabled(False)
        self.console.print_msg("Simulación reanudada.")

    def restart_simulation(self):
        self.pause_simulation()
        self.engine.reset()
        self.refresh_process_table()
        self.refresh_memory()
        self.refresh_stats_table()
        self.refresh_global_stats()
        self.refresh_cpu_status()
        self.refresh_interrupt_log()
        self.console.print_msg("Simulación reiniciada.")

    def set_speed(self, ms: int):
        self.timer.setInterval(ms)
        if self.spin_speed.value() != ms:
             self.spin_speed.blockSignals(True)
             self.spin_speed.setValue(ms)
             self.spin_speed.blockSignals(False)
