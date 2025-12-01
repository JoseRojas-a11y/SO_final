from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFrame, QGroupBox, QHeaderView, QDialog, QPushButton, QSpinBox, QFormLayout,
    QListWidget, QGridLayout, QCheckBox, QScrollArea, QLayoutItem
)
from PyQt6.QtCore import Qt, QTimer
from ...simulation.engine import SimulationEngine
from ..components.console import ConsoleWidget
from ..views.processes_view import ProcessesView
from ..views.memory_view import MemoryView

class MainWindow(QMainWindow):
    def __init__(self, engine: SimulationEngine):
        super().__init__()
        self.engine = engine
        arch_name = getattr(engine, "architecture_name", str(getattr(engine, "architecture", "")))
        self.setWindowTitle(f"Simulación SO - {arch_name} - {engine.scheduling_alg_name}")
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
        
        # Vistas separadas
        self.processes_view = ProcessesView(engine)
        self.memory_view = MemoryView(engine)

        # Crear ScrollAreas para procesos y memoria
        self.scroll_processes = QScrollArea()
        self.scroll_processes.setWidget(self.processes_view)
        self.scroll_processes.setWidgetResizable(True)
        self.scroll_processes.setVisible(False)
        self.scroll_processes.setFrameShape(QFrame.Shape.NoFrame)
        
        self.scroll_memory = QScrollArea()
        self.scroll_memory.setWidget(self.memory_view)
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
        right_layout.setSpacing(3)
        right_layout.setContentsMargins(2, 2, 2, 2)
        
        # Checkboxes en lugar de ListWidget
        nav_group = QGroupBox("Opciones")
        nav_layout = QVBoxLayout(nav_group)
        nav_layout.setSpacing(2)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        
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
        arch_status_layout.setSpacing(2)
        arch_status_layout.setContentsMargins(4, 4, 4, 4)
        self.arch_status_label = QLabel()
        self.arch_status_label.setWordWrap(True)
        self.arch_status_label.setStyleSheet("font-size: 10px;")
        arch_status_layout.addWidget(self.arch_status_label)
        right_layout.addWidget(arch_status_group)
        
        # Panel de Control de Módulos (visible según arquitectura)
        if engine.architecture == "Modular":
            arch_control_group = QGroupBox("🔧 Control de Módulos Dinámicos")
            arch_control_layout = QVBoxLayout(arch_control_group)
            arch_control_layout.setSpacing(2)
            arch_control_layout.setContentsMargins(4, 4, 4, 4)
            
            self.modules_list = QListWidget()
            self.modules_list.setMaximumHeight(70)
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
            layer_flow_layout.setSpacing(2)
            layer_flow_layout.setContentsMargins(4, 4, 4, 4)
            self.layer_flow_list = QListWidget()
            self.layer_flow_list.setMaximumHeight(90)
            layer_flow_layout.addWidget(QLabel("Últimas interacciones:"))
            layer_flow_layout.addWidget(self.layer_flow_list)
            right_layout.addWidget(layer_flow_group)
        elif engine.architecture == "Microkernel":
            # Panel de Módulos Externos para Microkernel
            ext_modules_group = QGroupBox("🔌 Módulos Externos")
            ext_modules_layout = QVBoxLayout(ext_modules_group)
            ext_modules_layout.setSpacing(2)
            ext_modules_layout.setContentsMargins(4, 4, 4, 4)
            self.ext_modules_list = QListWidget()
            self.ext_modules_list.setMaximumHeight(70)
            ext_modules_layout.addWidget(QLabel("Servicios Externos:"))
            ext_modules_layout.addWidget(self.ext_modules_list)
            right_layout.addWidget(ext_modules_group)
        
        # Simulation Controls
        controls_group = QGroupBox("Control Simulación")
        controls_layout = QGridLayout(controls_group)
        controls_layout.setSpacing(2)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        
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
        right_layout.addWidget(self.console, 1)
        
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
            if isinstance(child, QLayoutItem):
                aux = child.widget()
                if aux:
                    aux.setParent(None)
            
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
        self.processes_view.refresh_all()
        self.memory_view.refresh_all()
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
        
        # Arquitectura Microkernel eliminada en modo Modular-only
        
        # Actualizar estado de arquitectura
        if hasattr(self, 'arch_status_label'):
            self._update_arch_status()
            
    def _update_arch_status(self):
        """Actualiza el texto de estado de la arquitectura."""
        status = self.engine.get_module_status()
        arch = self.engine.architecture
        
        if arch == "Modular":
            text = "<b>📊 Estado Modular</b><br>"
            text += f"• Núcleo base: <b>ACTIVO</b><br>"
            text += f"• Módulos totales: <b>{len(self.engine.dynamic_modules)}</b><br>"
            core_count = sum(1 for m in self.engine.dynamic_modules.values() if not m.get('removable', True))
            optional_count = len(self.engine.dynamic_modules) - core_count
            text += f"• Módulos core: <b>{core_count}</b> (no removibles)<br>"
            text += f"• Módulos opcionales: <b>{optional_count}</b> (removibles)<br>"
            text += f"• Gestión dinámica: <b>ACTIVA</b>"
        else:
            # Fallback a texto modular
            text = "<b>📊 Estado Modular</b><br>"
            text += f"• Núcleo base: <b>ACTIVO</b><br>"
            text += f"• Módulos totales: <b>{len(self.engine.dynamic_modules)}</b><br>"
        
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
        self.engine.is_running = False
        # Refresh views to enable per-CPU controls while paused
        self.processes_view.refresh_all()
        self.memory_view.refresh_all()

    def resume_simulation(self):
        self.timer.start(self.spin_speed.value())
        self.btn_pause_resume.setText("Pausar")
        self.spin_speed.setEnabled(False)
        self.console.print_msg("Simulación reanudada.")
        self.engine.is_running = True
        # Refresh views to disable per-CPU controls while running
        self.processes_view.refresh_all()
        self.memory_view.refresh_all()

    def restart_simulation(self):
        self.pause_simulation()
        self.engine.reset()
        self.processes_view.refresh_all()
        self.memory_view.refresh_all()
        self.console.print_msg("Simulación reiniciada.")
        self.engine.is_running = False

    def set_speed(self, ms: int):
        self.timer.setInterval(ms)
        if self.spin_speed.value() != ms:
             self.spin_speed.blockSignals(True)
             self.spin_speed.setValue(ms)
             self.spin_speed.blockSignals(False)
