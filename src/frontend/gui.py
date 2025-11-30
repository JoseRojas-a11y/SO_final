from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFrame, QSizePolicy, QGridLayout, QGroupBox, QHeaderView, QDialog, QComboBox, QPushButton, QSpinBox, QFormLayout,
    QStackedWidget, QListWidget, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPalette, QAction
from typing import List
from src.simulation.engine import SimulationEngine
from src.simulation.models import Process
from src.simulation.memory_manager import MemoryBlock

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Simulación")
        self.resize(300, 200)
        
        layout = QFormLayout(self)
        
        self.arch_combo = QComboBox()
        self.arch_combo.addItems(["Monolithic", "Microkernel", "Modular"])
        layout.addRow("Arquitectura SO:", self.arch_combo)
        
        self.sched_combo = QComboBox()
        self.sched_combo.addItems(["FCFS", "SJF", "SRTF", "RR"])
        self.sched_combo.currentTextChanged.connect(self.on_sched_change)
        layout.addRow("Algoritmo Planificación:", self.sched_combo)
        
        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 20)
        self.quantum_spin.setValue(4)
        self.quantum_spin.setEnabled(False) # Default disabled unless RR
        layout.addRow("Quantum (RR):", self.quantum_spin)
        
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Iniciar")
        ok_btn.clicked.connect(self.accept)
        btn_box.addWidget(ok_btn)
        layout.addRow(btn_box)
        
    def on_sched_change(self, text):
        self.quantum_spin.setEnabled(text == "RR")

    def get_config(self):
        return {
            "architecture": self.arch_combo.currentText(),
            "scheduling_alg": self.sched_combo.currentText(),
            "quantum": self.quantum_spin.value()
        }

class MemoryBar(QWidget):
    def __init__(self, blocks: List[MemoryBlock], total: int, parent=None):
        super().__init__(parent)
        self.blocks = blocks
        self.total = total
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0,0,0,0)
        self._layout.setSpacing(1)
        self.refresh()

    def set_blocks(self, blocks: List[MemoryBlock]):
        self.blocks = blocks
        self.refresh()

    def refresh(self):
        # clear
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for b in self.blocks:
            w = QFrame()
            w.setFrameShape(QFrame.Shape.StyledPanel)
            palette = w.palette()
            color = QColor(60,60,60) if b.free else QColor(0,160,80)
            palette.setColor(QPalette.ColorRole.Window, color)
            w.setAutoFillBackground(True)
            w.setPalette(palette)
            w.setMaximumHeight(20)
            
            # Tooltip with address info
            status = "Libre" if b.free else f"PID {b.process_pid}"
            w.setToolTip(f"Inicio: {b.start} MB\nFin: {b.end} MB\nTamaño: {b.size} MB\nEstado: {status}")
            
            self._layout.addWidget(w, b.size)
        self.update()

class MainWindow(QMainWindow):
    def __init__(self, engine: SimulationEngine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle(f"Simulación SO - {engine.architecture} - {engine.scheduling_alg_name}")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central) # Main layout is horizontal: Menu | Content

        # --- Navigation Menu (Right Side as requested, but standard is Left. User asked Right? "parte derecha") ---
        # User said "parte derecha" (right side).
        
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

        # Controls
        controls_layout = QHBoxLayout()
        self.btn_create_process = QPushButton("Crear Proceso Manual")
        self.btn_create_process.clicked.connect(self.create_manual_process)
        controls_layout.addWidget(self.btn_create_process)
        proc_layout.addLayout(controls_layout)

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
        
        # Queue and Interrupt Log (divided in two)
        queue_interrupt_layout = QHBoxLayout()
        
        # Cola de procesos
        self.process_queue_list = QListWidget()
        queue_interrupt_layout.addWidget(self.group_box("Cola de procesos", self.process_queue_list), 1)
        
        # Interrupt Log
        self.interrupt_list = QListWidget()
        queue_interrupt_layout.addWidget(self.group_box("Registro de Interrupciones", self.interrupt_list), 1)
        
        queue_interrupt_widget = QWidget()
        queue_interrupt_widget.setLayout(queue_interrupt_layout)
        proc_layout.addWidget(queue_interrupt_widget, 1)  # Factor de estiramiento para ocupar espacio disponible
        
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
        self.refresh_process_queue()

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

    def refresh_process_queue(self):
        """Actualiza la visualización de las colas de procesos (ready, running, waiting)"""
        self.process_queue_list.clear()
        
        scheduler = self.engine.scheduler
        
        # Ready Queue
        if hasattr(scheduler, 'rr_queue'):
            # RoundRobin usa rr_queue
            ready_processes = list(scheduler.rr_queue)
        else:
            # Otros schedulers usan ready_queue
            ready_processes = list(scheduler.ready_queue)
        
        self.process_queue_list.addItem("=== READY QUEUE ===")
        if ready_processes:
            for p in ready_processes:
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}) - Restante: {p.remaining_ticks}")
        else:
            self.process_queue_list.addItem("  (vacía)")
        
        # Running Queue (procesos en CPUs)
        self.process_queue_list.addItem("")
        self.process_queue_list.addItem("=== RUNNING QUEUE ===")
        running_processes = [p for p in self.engine.cpus if p is not None]
        if running_processes:
            for i, p in enumerate(self.engine.cpus):
                if p is not None:
                    self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}) - CPU {i} - Restante: {p.remaining_ticks}")
        else:
            self.process_queue_list.addItem("  (vacía)")
        
        # Waiting Queue (procesos en estado WAITING)
        self.process_queue_list.addItem("")
        self.process_queue_list.addItem("=== WAITING QUEUE ===")
        waiting_processes = [p for p in self.engine.active_processes() if p.state == "WAITING"]
        if waiting_processes:
            for p in waiting_processes:
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}) - Restante: {p.remaining_ticks}")
        else:
            self.process_queue_list.addItem("  (vacía)")

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
        avg_waiting = m.total_waiting_time / m.completed_processes if m.completed_processes else 0 # This is approx, ideally track all finished
        cpu_util = (m.cpu_busy_ticks / self.engine.tick_count * 100) if self.engine.tick_count else 0
        
        text = (f"Procesos Totales: {m.total_processes} | Completados: {m.completed_processes} | "
                f"Avg Turnaround: {avg_turnaround:.1f} ticks | Avg Waiting (completed): {avg_waiting:.1f} ticks | "
                f"CPU Util: {cpu_util:.1f}%")
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
        self.refresh_process_queue()
        self.console.print_msg("Simulación reiniciada.")

    def set_speed(self, ms: int):
        self.timer.setInterval(ms)
        if self.spin_speed.value() != ms:
             self.spin_speed.blockSignals(True)
             self.spin_speed.setValue(ms)
             self.spin_speed.blockSignals(False)

class ConsoleWidget(QWidget):
    def __init__(self, engine: SimulationEngine, main_window, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background-color: #1e1e1e; color: #00FF00; font-family: Consolas; font-size: 10pt;")
        layout.addWidget(self.output)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Escriba un comando (ej: help)...")
        self.input.setStyleSheet("background-color: #333; color: white; font-family: Consolas; font-size: 10pt;")
        self.input.returnPressed.connect(self.process_command)
        layout.addWidget(self.input)
        
        self.print_msg("=== Terminal de Control SO ===")
        self.print_msg("Escriba 'help' para ver la lista de comandos.")

    def print_msg(self, msg: str):
        self.output.append(msg)
        sb = self.output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def process_command(self):
        cmd_line = self.input.text().strip()
        if not cmd_line: return
        
        self.input.clear()
        self.print_msg(f"> {cmd_line}")
        
        parts = cmd_line.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        try:
            if cmd == "help":
                self.show_help()
            elif cmd == "create":
                self.cmd_create(args)
            elif cmd == "pause":
                self.main_window.pause_simulation()
                self.print_msg("Simulación pausada.")
            elif cmd == "star":
                self.main_window.active_simulation()
                self.print_msg("Simulación reanudada.")
            elif cmd == "speed":
                self.cmd_speed(args)
            elif cmd == "auto":
                self.cmd_auto(args)
            elif cmd == "clear":
                self.output.clear()
            else:
                self.print_msg(f"Error: Comando '{cmd}' desconocido.")
        except Exception as e:
            self.print_msg(f"Error ejecutando comando: {str(e)}")

    def show_help(self):
        help_text = """
Comandos Disponibles:
---------------------
create <size> <duration> [prio] : Crea un proceso manual (MB, ticks, 0-10)
pause                           : Pausa la simulación
star                            : Activa la simulación
speed <ms>                      : Cambia velocidad (ms por tick, min 10)
auto <on|off>                   : Activa/Desactiva creación automática
clear                           : Limpia la consola
help                            : Muestra esta ayuda
"""
        self.print_msg(help_text.strip())

    def cmd_create(self, args):
        if len(args) < 2:
            self.print_msg("Uso: create <size_mb> <duration_ticks> [priority]")
            return
        
        try:
            size = int(args[0])
            duration = int(args[1])
            priority = int(args[2]) if len(args) > 2 else 0
            
            # Engine manual_create_process doesn't take priority yet, but we can add it or ignore
            # The user asked for "configuración", so let's assume size/duration is enough for now
            # or update engine later. Engine.manual_create_process signature: (size_mb, duration)
            
            p = self.engine.manual_create_process(size, duration)
            p.priority = priority # Set priority manually if engine doesn't support it in init
            
            self.print_msg(f"Proceso {p.name} creado (PID {p.pid}, {size}MB, {duration}t, Prio {priority})")
        except ValueError:
            self.print_msg("Error: Los argumentos deben ser números enteros.")

    def cmd_speed(self, args):
        if not args:
            self.print_msg("Uso: speed <ms>")
            return
        try:
            ms = int(args[0])
            if ms < 10: ms = 10
            self.main_window.set_speed(ms)
            self.print_msg(f"Velocidad ajustada a {ms}ms por tick.")
        except ValueError:
            self.print_msg("Error: El valor debe ser un número entero.")

    def cmd_auto(self, args):
        if not args:
            status = "ON" if self.engine.auto_create_processes else "OFF"
            self.print_msg(f"Generación automática: {status}")
            return
        
        val = args[0].lower()
        if val == "on":
            self.engine.auto_create_processes = True
            self.print_msg("Generación automática ACTIVADA.")
        elif val == "off":
            self.engine.auto_create_processes = False
            self.print_msg("Generación automática DESACTIVADA.")
        else:
            self.print_msg("Uso: auto <on|off>")

def launch_gui():
    import sys
    app = QApplication(sys.argv)
    
    # Show Config Dialog
    dialog = ConfigDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        config = dialog.get_config()
        engine = SimulationEngine(
            total_memory_mb=256, 
            architecture=config["architecture"],
            scheduling_alg=config["scheduling_alg"],
            quantum=config["quantum"]
        )
        w = MainWindow(engine)
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    launch_gui()
