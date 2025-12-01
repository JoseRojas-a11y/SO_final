from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFrame, QGroupBox, QHeaderView, QDialog, QPushButton, QSpinBox, QFormLayout,
    QListWidget, QGridLayout, QCheckBox, QScrollArea, QLineEdit
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

        # Estado de selección
        self.processes_selected = False
        self.memory_selected = False
        self.first_selected = None  # 'processes' o 'memory'

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central) # Main layout is horizontal: Menu | Content

        # Content Area - Widget contenedor principal
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        
        # Page vacía inicial
        self.page_empty = QWidget()
        empty_layout = QVBoxLayout(self.page_empty)
        empty_layout.addStretch()
        empty_label = QLabel("Seleccione una opción para comenzar")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("font-size: 18px; color: #666;")
        empty_layout.addWidget(empty_label)
        empty_layout.addStretch()
        
        # Page 1: Process Management (contenido completo)
        self.page_processes_content = QWidget()
        proc_layout = QVBoxLayout(self.page_processes_content)
        
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
        
        # Page 2: Memory Management (contenido completo)
        self.page_memory_content = QWidget()
        mem_layout_page = QVBoxLayout(self.page_memory_content)
        
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

        # Tabla de estadísticas de paginación
        self.paging_table = QTableWidget(0, 5)
        self.paging_table.setHorizontalHeaderLabels(["Algoritmo", "Page Faults", "Page Hits", "Tasa Faults %", "Utilización %"])
        header_paging = self.paging_table.horizontalHeader()
        if header_paging:
            header_paging.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mem_layout_page.addWidget(self.group_box("Estadísticas de Paginación", self.paging_table))

        # Crear ScrollAreas para procesos y memoria
        self.scroll_processes = QScrollArea()
        self.scroll_processes.setWidget(self.page_processes_content)
        self.scroll_processes.setWidgetResizable(True)
        self.scroll_processes.setVisible(False)
        self.scroll_processes.setFrameShape(QFrame.Shape.NoFrame)
        
        self.scroll_memory = QScrollArea()
        self.scroll_memory.setWidget(self.page_memory_content)
        self.scroll_memory.setWidgetResizable(True)
        self.scroll_memory.setVisible(False)
        self.scroll_memory.setFrameShape(QFrame.Shape.NoFrame)

        # Separador visual entre secciones
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setFrameShadow(QFrame.Shadow.Sunken)
        self.divider.setLineWidth(2)
        self.divider.setStyleSheet("background-color: white; border: 2px solid white;")
        self.divider.setFixedHeight(3)
        self.divider.setVisible(False)

        # Mostrar página vacía inicialmente
        self.content_layout.addWidget(self.page_empty)

        # Navigation & Console (Right Side)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Checkboxes en lugar de ListWidget
        nav_group = QGroupBox("Opciones")
        nav_layout = QVBoxLayout(nav_group)
        
        self.checkbox_processes = QCheckBox("Gestión de Procesos")
        self.checkbox_processes.stateChanged.connect(self.on_navigation_changed)
        nav_layout.addWidget(self.checkbox_processes)
        
        self.checkbox_memory = QCheckBox("Gestión de Memoria")
        self.checkbox_memory.stateChanged.connect(self.on_navigation_changed)
        nav_layout.addWidget(self.checkbox_memory)
        
        right_layout.addWidget(nav_group)
        
        # Panel de Estado de Arquitectura (siempre visible)
        arch_status_group = QGroupBox("📊 Estado de Arquitectura")
        arch_status_layout = QVBoxLayout(arch_status_group)
        self.arch_status_label = QLabel()
        self.arch_status_label.setWordWrap(True)
        self.arch_status_label.setStyleSheet("font-size: 10px;")
        arch_status_layout.addWidget(self.arch_status_label)
        right_layout.addWidget(arch_status_group)
        
        # Panel de Control de Módulos (visible según arquitectura)
        if engine.architecture == "Modular":
            arch_control_group = QGroupBox("🔧 Control de Módulos Dinámicos")
            arch_control_layout = QVBoxLayout(arch_control_group)
            
            self.modules_list = QListWidget()
            self.modules_list.setMaximumHeight(120)
            arch_control_layout.addWidget(QLabel("Módulos Cargados:"))
            arch_control_layout.addWidget(self.modules_list)
            
            btn_layout = QHBoxLayout()
            self.btn_load_module = QPushButton("➕ Cargar Módulo")
            self.btn_load_module.clicked.connect(self.load_module_dialog)
            btn_layout.addWidget(self.btn_load_module)
            
            self.btn_unload_module = QPushButton("➖ Descargar")
            self.btn_unload_module.clicked.connect(self.unload_selected_module)
            btn_layout.addWidget(self.btn_unload_module)
            arch_control_layout.addLayout(btn_layout)
            
            right_layout.addWidget(arch_control_group)
            
            layer_flow_group = QGroupBox("📡 Flujo entre Capas (Modular)")
            layer_flow_layout = QVBoxLayout(layer_flow_group)
            self.layer_flow_list = QListWidget()
            self.layer_flow_list.setMaximumHeight(150)
            layer_flow_layout.addWidget(QLabel("Últimas interacciones:"))
            layer_flow_layout.addWidget(self.layer_flow_list)
            right_layout.addWidget(layer_flow_group)
        elif engine.architecture == "Microkernel":
            # Panel de Módulos Externos para Microkernel
            ext_modules_group = QGroupBox("🔌 Módulos Externos")
            ext_modules_layout = QVBoxLayout(ext_modules_group)
            self.ext_modules_list = QListWidget()
            self.ext_modules_list.setMaximumHeight(120)
            ext_modules_layout.addWidget(QLabel("Servicios Externos:"))
            ext_modules_layout.addWidget(self.ext_modules_list)
            right_layout.addWidget(ext_modules_group)
        
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
        main_layout.addWidget(self.content_widget)
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

    def on_navigation_changed(self):
        """Maneja los cambios en la selección de opciones de navegación"""
        processes_checked = self.checkbox_processes.isChecked()
        memory_checked = self.checkbox_memory.isChecked()
        
        # Determinar qué se seleccionó primero (solo si no hay ninguno seleccionado previamente)
        if processes_checked and not self.processes_selected:
            if not self.memory_selected:
                self.first_selected = 'processes'
        elif memory_checked and not self.memory_selected:
            if not self.processes_selected:
                self.first_selected = 'memory'
        
        # Si se deseleccionan ambos, resetear first_selected
        if not processes_checked and not memory_checked:
            self.first_selected = None
        
        # Actualizar estado
        self.processes_selected = processes_checked
        self.memory_selected = memory_checked
        
        # Limpiar layout de contenido
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        # Ocultar todos los scrolls, página vacía y separador
        self.scroll_processes.setVisible(False)
        self.scroll_memory.setVisible(False)
        self.page_empty.setVisible(False)
        self.divider.setVisible(False)
        
        # Lógica de visualización
        if not processes_checked and not memory_checked:
            # Ninguna seleccionada: mostrar página vacía
            self.content_layout.addWidget(self.page_empty)
            self.page_empty.setVisible(True)
        elif processes_checked and not memory_checked:
            # Solo procesos
            self.content_layout.addWidget(self.scroll_processes)
            self.scroll_processes.setVisible(True)
        elif memory_checked and not processes_checked:
            # Solo memoria
            self.content_layout.addWidget(self.scroll_memory)
            self.scroll_memory.setVisible(True)
        else:
            # Ambos seleccionados: dividir pantalla según orden con separador
            if self.first_selected == 'processes':
                # Procesos arriba, memoria abajo
                self.content_layout.addWidget(self.scroll_processes, 1)
                self.content_layout.addWidget(self.divider)
                self.content_layout.addWidget(self.scroll_memory, 1)
            else:
                # Memoria arriba, procesos abajo
                self.content_layout.addWidget(self.scroll_memory, 1)
                self.content_layout.addWidget(self.divider)
                self.content_layout.addWidget(self.scroll_processes, 1)
            
            self.scroll_processes.setVisible(True)
            self.scroll_memory.setVisible(True)
            self.divider.setVisible(True)

    def on_tick(self):
        self.engine.tick()
        self.refresh_process_table()
        self.refresh_memory()
        self.refresh_stats_table()
        self.refresh_paging_table()
        self.refresh_global_stats()
        self.refresh_cpu_status()
        self.refresh_interrupt_log()
        self.refresh_process_queue()
        self.update_architecture_view()
        self.refresh_layer_flow()

    def refresh_layer_flow(self):
        """Actualiza el panel de flujo entre capas (solo Modular)."""
        if not hasattr(self, 'layer_flow_list'):
            return
        events = self.engine.layer_flow_events()
        if self.layer_flow_list.count() != len(events):
            self.layer_flow_list.clear()
            for ev in events:
                self.layer_flow_list.addItem(ev)
            self.layer_flow_list.scrollToBottom()
        
    def update_architecture_view(self):
        """Actualiza la información de la arquitectura (sin visualización gráfica)."""
        # Actualizar lista de módulos si es arquitectura Modular
        if hasattr(self, 'modules_list') and self.engine.architecture == "Modular":
            self.modules_list.clear()
            for module_id, module in self.engine.dynamic_modules.items():
                removable = "⚡" if module.get("removable", False) else "🔒"
                status_icon = "✓" if module.get("status") == "loaded" else "✗"
                self.modules_list.addItem(f"{status_icon} {removable} {module.get('name', module_id)}")
        
        # Actualizar lista de módulos externos si es arquitectura Microkernel
        if hasattr(self, 'ext_modules_list') and self.engine.architecture == "Microkernel":
            self.ext_modules_list.clear()
            for module_id, module in self.engine.external_modules.items():
                status_icon = "🟢" if module.get("status") == "active" else "🔴"
                self.ext_modules_list.addItem(f"{status_icon} {module.get('name', module_id)}")
        
        # Actualizar estado de arquitectura
        if hasattr(self, 'arch_status_label'):
            self._update_arch_status()
            
    def _update_arch_status(self):
        """Actualiza el texto de estado de la arquitectura."""
        status = self.engine.get_module_status()
        arch = self.engine.architecture
        
        if arch == "Monolithic":
            text = "<b>📊 Estado Monolítico</b><br>"
            text += f"• Núcleo único: <b>ACTIVO</b><br>"
            text += f"• Gestión centralizada: <b>ACTIVA</b><br>"
            text += f"• Memoria: Gestionada desde núcleo<br>"
            text += f"• Procesos: Gestionados desde núcleo<br>"
            text += f"• Módulos separados: <b>NO</b>"
        elif arch == "Microkernel":
            text = "<b>📊 Estado Microkernel</b><br>"
            text += f"• Núcleo mínimo: <b>ACTIVO</b> (Procesos + IPC)<br>"
            text += f"• Módulos externos: <b>{len(self.engine.external_modules)}</b><br>"
            text += f"• IPC: <b>{'✅ Habilitado' if status.get('ipc_enabled') else '❌ Deshabilitado'}</b><br>"
            text += f"• Memoria: Gestionada por módulo externo<br>"
            text += f"• Coordinación: Microkernel coordina módulos"
        elif arch == "Modular":
            text = "<b>📊 Estado Modular</b><br>"
            text += f"• Núcleo base: <b>ACTIVO</b><br>"
            text += f"• Módulos totales: <b>{len(self.engine.dynamic_modules)}</b><br>"
            core_count = sum(1 for m in self.engine.dynamic_modules.values() if not m.get('removable', True))
            optional_count = len(self.engine.dynamic_modules) - core_count
            text += f"• Módulos core: <b>{core_count}</b> (no removibles)<br>"
            text += f"• Módulos opcionales: <b>{optional_count}</b> (removibles)<br>"
            text += f"• Gestión dinámica: <b>ACTIVA</b>"
        
        self.arch_status_label.setText(text)
        
    def load_module_dialog(self):
        """Diálogo para cargar un módulo dinámicamente."""
        if self.engine.architecture != "Modular":
            return
            
        d = QDialog(self)
        d.setWindowTitle("Cargar Módulo")
        l = QFormLayout(d)
        
        from PyQt6.QtWidgets import QLineEdit
        name_input = QLineEdit()
        name_input.setPlaceholderText("Nombre del módulo")
        l.addRow("Nombre:", name_input)
        
        btn = QPushButton("Cargar")
        btn.clicked.connect(d.accept)
        l.addRow(btn)
        
        if d.exec() == QDialog.DialogCode.Accepted:
            module_name = name_input.text().strip()
            if module_name:
                module_id = module_name.lower().replace(" ", "_")
                success = self.engine.load_module(module_id, module_name, removable=True)
                if success:
                    self.console.print_msg(f"Módulo '{module_name}' cargado exitosamente.")
                    self.update_architecture_view()
                    self.refresh_layer_flow()
                else:
                    self.console.print_msg(f"Error: No se pudo cargar el módulo '{module_name}'.")
                    
    def unload_selected_module(self):
        """Descarga el módulo seleccionado."""
        if self.engine.architecture != "Modular":
            return
            
        current_item = self.modules_list.currentItem()
        if not current_item:
            self.console.print_msg("Por favor, seleccione un módulo para descargar.")
            return
        
        # Extraer el ID del módulo del texto
        text = current_item.text()
        # Buscar el módulo por nombre
        for module_id, module in self.engine.dynamic_modules.items():
            if module.get('name', module_id) in text:
                success = self.engine.unload_module(module_id)
                if success:
                    self.console.print_msg(f"Módulo '{module.get('name', module_id)}' descargado exitosamente.")
                    self.update_architecture_view()
                    self.refresh_layer_flow()
                else:
                    self.console.print_msg(f"Error: No se pudo descargar el módulo.")
                return
        
        self.console.print_msg("Error: Módulo no encontrado.")

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
        """Actualiza la visualización de las colas de procesos (new, ready, running, waiting, terminated)"""
        self.process_queue_list.clear()
        
        scheduler = self.engine.scheduler
        
        # New Queue (procesos en estado NEW)
        new_processes = [p for p in self.engine.processes.values() if p.state == "NEW"]
        self.process_queue_list.addItem("=== NUEVO (NEW) ===")
        if new_processes:
            for p in new_processes:
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}) - Tamaño: {p.size_mb} MB")
        else:
            self.process_queue_list.addItem("  (vacía)")
        
        # Ready Queue
        if hasattr(scheduler, 'rr_queue'):
            # RoundRobin usa rr_queue
            ready_processes = list(scheduler.rr_queue)
        elif hasattr(scheduler, 'priority_queues'):
            # PriorityRoundRobin usa priority_queues
            ready_processes = []
            for queue in scheduler.priority_queues.values():
                ready_processes.extend(list(queue))
        else:
            # Otros schedulers usan ready_queue
            ready_processes = list(scheduler.ready_queue)
        
        self.process_queue_list.addItem("")
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
        
        # Terminated Queue (procesos en estado TERMINATED)
        self.process_queue_list.addItem("")
        self.process_queue_list.addItem("=== TERMINADO (TERMINATED) ===")
        terminated_processes = [p for p in self.engine.processes.values() if p.state == "TERMINATED"]
        if terminated_processes:
            for p in terminated_processes:
                finish_info = f" - Finalizado en tick {p.finish_tick}" if p.finish_tick else ""
                self.process_queue_list.addItem(f"  {p.name} (PID {p.pid}){finish_info}")
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
    
    def refresh_paging_table(self):
        """Actualiza la tabla de estadísticas de paginación."""
        stats = self.engine.paging_stats()
        self.paging_table.setRowCount(len(stats))
        for r, (alg, s) in enumerate(stats.items()):
            self.set_row(self.paging_table, r, [
                alg,
                s['total_page_faults'],
                s['total_hits'],
                f"{s['page_fault_rate']*100:.2f}",
                f"{s['memory_utilization']*100:.1f}"
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
        self.refresh_paging_table()
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
