from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QFrame,
    QTableWidget, QHeaderView, QTableWidgetItem, QListWidget, QGridLayout,
    QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt


class ProcessesView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        root = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        arch_name = getattr(engine, "architecture_name", str(getattr(engine, "architecture", "")))
        header_layout.addWidget(QLabel(f"<b>Arquitectura:</b> {arch_name}"))
        root.addLayout(header_layout)

        # Tabla de procesos
        self.process_table = QTableWidget(0, 9)
        self.process_table.setMinimumHeight(300)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Nombre", "Estado", "CPU", "CPU %", "Mem MB",
            "Restante", "Espera", "Prioridad"
        ])
        header = self.process_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        root.addWidget(self._group("Procesos Activos", self.process_table))

        # Colas e interrupciones
        hl = QHBoxLayout()
        self.process_queue_list = QListWidget()
        self.process_queue_list.setMinimumHeight(240)
        self.process_queue_list.setMaximumHeight(240)
        self.process_queue_list.setMinimumWidth(420)
        hl.addWidget(self._group("Cola de procesos", self.process_queue_list), 0)

        self.interrupt_list = QListWidget()
        self.interrupt_list.setMinimumHeight(240)
        self.interrupt_list.setMaximumHeight(240)
        self.interrupt_list.setMinimumWidth(420)
        hl.addWidget(self._group("Registro de Interrupciones", self.interrupt_list), 0)

        wrap = QWidget()
        wrap.setLayout(hl)
        root.addWidget(wrap, 1)

        # Métricas Globales
        self.global_stats_label = QLabel("Métricas del Sistema: ...")
        root.addWidget(self._group("Métricas del Sistema", self.global_stats_label))

        
        # CPUs grid (2 columnas)
        cpu_group = QGroupBox("CPUs / Multihilos")
        grid = QGridLayout(cpu_group)
        self.cpu_blocks = []
        cpu_count = max(1, len(self.engine.cpus))
        for i in range(cpu_count):
            block = self._create_cpu_block(i)
            self.cpu_blocks.append(block)
            row = i // 2
            col = i % 2
            grid.addWidget(block, row, col)
        root.addWidget(cpu_group)

    def _group(self, title: str, w: QWidget) -> QGroupBox:
        g = QGroupBox(title)
        l = QVBoxLayout(g)
        l.addWidget(w)
        return g

    def _set_row(self, table: QTableWidget, row: int, values):
        for c, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, c, item)

    def refresh_all(self):
        self._refresh_cpu_status()
        self._refresh_process_table()
        self._refresh_interrupt_log()
        self._refresh_process_queue()
        self._refresh_global_stats()

    def _refresh_cpu_status(self):
        alg = self.engine.scheduling_alg_name
        for i, block in enumerate(self.cpu_blocks):
            cpu = self.engine.cpus[i]
            p = cpu.process
            title_label = block.findChild(QLabel, f"cpu_title_{i}")
            alg_label = block.findChild(QLabel, f"cpu_alg_{i}")
            thread_label = block.findChild(QLabel, f"cpu_threads_{i}")
            proc_label = block.findChild(QLabel, f"cpu_proc_{i}")
            alg_combo = block.findChild(QComboBox, f"cpu_alg_combo_{i}")
            thread_spin = block.findChild(QSpinBox, f"cpu_thread_spin_{i}")
            if title_label:
                title_label.setText(f"CPU {i + 1}")
            if alg_label:
                per_cpu_alg = None
                if hasattr(self.engine, "scheduler_names") and i < len(self.engine.scheduler_names):
                    per_cpu_alg = self.engine.scheduler_names[i]
                alg_label.setText(f"Algoritmo: {per_cpu_alg or alg}")
            if thread_label:
                thread_label.setText(f"Hilos: {cpu.threads_in_use}/{cpu.thread_capacity}")
            if alg_combo:
                current_alg = per_cpu_alg or alg
                idx = alg_combo.findText(current_alg)
                if idx >= 0:
                    alg_combo.setCurrentIndex(idx)
                # Disable while running
                alg_combo.setEnabled(not getattr(self.engine, 'is_running', False))
            if thread_spin:
                thread_spin.setValue(cpu.thread_capacity)
                thread_spin.setEnabled(not getattr(self.engine, 'is_running', False))
            if p is not None:
                speed_factor = max(1, cpu.threads_in_use)
                proc_label.setText(f"Proceso: {p.name} (PID {p.pid})\nRestante: {p.remaining_ticks} ticks\nFactor x{speed_factor}")
                block.setStyleSheet("QGroupBox {border:2px solid #0a0; border-radius:6px;} background:#102910; color:white;")
            else:
                proc_label.setText("Proceso: Idle")
                block.setStyleSheet("QGroupBox {border:2px solid #444; border-radius:6px;} background:#1e1e1e; color:#bbb;")

    def _create_cpu_block(self, idx: int) -> QGroupBox:
        box = QGroupBox()
        box.setObjectName(f"cpu_block_{idx}")
        box.setStyleSheet("QGroupBox {border:2px solid #444; border-radius:6px; margin-top:6px;} QGroupBox::title {subcontrol-origin: margin; left:8px; padding:0 4px;} background:#1e1e1e;")
        v = QVBoxLayout(box)
        title = QLabel(f"CPU {idx + 1}")
        title.setObjectName(f"cpu_title_{idx}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight:bold; font-size:14px;")
        v.addWidget(title)
        alg = QLabel("Algoritmo: -")
        alg.setObjectName(f"cpu_alg_{idx}")
        v.addWidget(alg)
        # Controls: per-CPU scheduler and threads
        ctrl_row = QHBoxLayout()
        alg_combo = QComboBox()
        alg_combo.setObjectName(f"cpu_alg_combo_{idx}")
        alg_combo.addItems(["FCFS", "SJF", "SRTF", "RR", "Priority", "PriorityRR"])
        alg_combo.currentTextChanged.connect(lambda name, i=idx: self._on_change_cpu_alg(i, name))
        ctrl_row.addWidget(alg_combo)
        thread_spin = QSpinBox()
        thread_spin.setObjectName(f"cpu_thread_spin_{idx}")
        thread_spin.setRange(1, 32)
        thread_spin.setValue(2)
        thread_spin.valueChanged.connect(lambda val, i=idx: self._on_change_cpu_threads(i, val))
        ctrl_row.addWidget(thread_spin)
        v.addLayout(ctrl_row)
        threads = QLabel("Hilos: 0/0")
        threads.setObjectName(f"cpu_threads_{idx}")
        v.addWidget(threads)
        proc = QLabel("Proceso: Idle")
        proc.setObjectName(f"cpu_proc_{idx}")
        proc.setAlignment(Qt.AlignmentFlag.AlignLeft)
        v.addWidget(proc)
        box.setFixedWidth(360)  # Para que quepan dos bloques en una fila (layout ancho ~720+)
        return box

    def _refresh_interrupt_log(self):
        # Mostrar siempre las últimas 10 interrupciones sin eliminar del log global
        self.interrupt_list.clear()
        total = len(self.engine.interrupt_log)
        # Encabezado con contador total
        self.interrupt_list.addItem(f"Total de interrupciones: {total}")
        # Últimas 10
        tail = self.engine.interrupt_log[-10:]
        for msg in tail:
            self.interrupt_list.addItem(msg)
        # Nota de ocultas si aplica
        if total > 10:
            hidden = total - 10
            self.interrupt_list.addItem(f"(Mostrando últimas 10, +{hidden} ocultas)")
        self.interrupt_list.scrollToBottom()

    def _refresh_process_queue(self):
        self.process_queue_list.clear()
        scheduler = self.engine.schedulers[0]  # Asumimos CPU 0 para la cola principal

        new_processes = [p for p in self.engine.processes.values() if p.state == "NEW"]
        self.process_queue_list.addItem("=== NUEVO (NEW) ===")
        if new_processes:
            for p in new_processes:
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}) - Tamaño: {p.size_mb} MB")
        else:
            self.process_queue_list.addItem("  (vacía)")

        # Ready Queue
        if hasattr(scheduler, 'rr_queue'):
            ready_processes = list(scheduler.rr_queue)
        elif hasattr(scheduler, 'priority_queues'):
            ready_processes = []
            for queue in scheduler.priority_queues.values():
                ready_processes.extend(list(queue))
        else:
            ready_processes = list(getattr(scheduler, 'ready_queue', []))

        self.process_queue_list.addItem("")
        self.process_queue_list.addItem("=== READY QUEUE ===")
        if ready_processes:
            for p in ready_processes:
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}) - Restante: {p.remaining_ticks}")
        else:
            self.process_queue_list.addItem("  (vacía)")

        # Running
        self.process_queue_list.addItem("")
        self.process_queue_list.addItem("=== RUNNING QUEUE ===")
        running_cpus = [cpu for cpu in self.engine.cpus if getattr(cpu, "process", None) is not None]
        if running_cpus:
            for i, cpu in enumerate(self.engine.cpus):
                p = getattr(cpu, "process", None)
                if p is not None:
                    self.process_queue_list.addItem(
                        f"  {p.name} (PID {p.pid}) - CPU {i} - Restante: {p.remaining_ticks} - Hilos {cpu.threads_in_use}/{cpu.thread_capacity}"
                    )
        else:
            self.process_queue_list.addItem("  (vacía)")

        # Waiting
        self.process_queue_list.addItem("")
        self.process_queue_list.addItem("=== WAITING QUEUE ===")
        waiting_processes = [p for p in self.engine.active_processes() if p.state == "WAITING"]
        if waiting_processes:
            for p in waiting_processes:
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}) - Restante: {p.remaining_ticks}")
        else:
            self.process_queue_list.addItem("  (vacía)")

        # Terminated
        self.process_queue_list.addItem("")
        self.process_queue_list.addItem("=== TERMINADO (TERMINATED) ===")
        terminated_processes = [p for p in self.engine.processes.values() if p.state == "TERMINATED"]
        if terminated_processes:
            for p in terminated_processes:
                finish_info = f" - Finalizado en tick {p.finish_tick}" if p.finish_tick else ""
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}){finish_info}")
        else:
            self.process_queue_list.addItem("  (vacía)")

    def _refresh_process_table(self):
        processes = self.engine.active_processes()
        processes.sort(key=lambda p: p.pid)
        self.process_table.setRowCount(len(processes))
        for r, p in enumerate(processes):
            cpu_str = str(p.cpu_id) if p.cpu_id is not None else "-"
            self._set_row(self.process_table, r, [
                p.pid,
                p.name,
                p.state,
                cpu_str,
                f"{p.cpu_usage:.1f}",
                p.memory_usage_mb,
                f"{p.remaining_ticks}/{p.duration_ticks}",
                p.waiting_ticks,
                p.priority,
            ])

    def _refresh_global_stats(self):
        m = self.engine.metrics
        avg_turnaround = m.total_turnaround_time / m.completed_processes if m.completed_processes else 0
        avg_waiting = m.total_waiting_time / m.completed_processes if m.completed_processes else 0
        busy_cpus = sum(1 for cpu in self.engine.cpus if getattr(cpu, "process", None) is not None)
        total_cpus = max(1, len(self.engine.cpus))
        cpu_util = (busy_cpus / total_cpus) * 100
        text = (
            f"<html><head/><body>"
            f"<p><b>Métricas del Sistema:</b></p>"
            f"<table border='0' cellspacing='5' cellpadding='3'>"
            f"<tr>"
            f"<td>Procesos Totales: {m.total_processes}</td>"
            f"<td>Completados: {m.completed_processes}</td>"
            f"<td>Turnaround Promedio: {avg_turnaround:.2f} ticks</td>"
            f"</tr>"
            f"<tr>"
            f"<td>Tiempo Espera Promedio: {avg_waiting:.2f} ticks</td>"
            f"<td>Utilización CPU Global: {cpu_util:.2f}%</td>"
            f"<td>Ticks CPU efectivos: {getattr(m, 'effective_cpu_ticks', 0)}</td>"
            f"</tr>"
            f"</table></body></html>"
        )
        self.global_stats_label.setText(text)

    def _on_change_cpu_alg(self, cpu_index: int, name: str):
        if hasattr(self.engine, "set_cpu_scheduler"):
            self.engine.set_cpu_scheduler(cpu_index, name)
        self._refresh_cpu_status()

    def _on_change_cpu_threads(self, cpu_index: int, threads: int):
        if hasattr(self.engine, "set_cpu_threads"):
            self.engine.set_cpu_threads(cpu_index, threads)
        self._refresh_cpu_status()
