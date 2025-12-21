from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QGroupBox, QDialog, QPushButton, QSpinBox, QFormLayout,
    QListWidget, QGridLayout, QCheckBox, QScrollArea, QLayoutItem, QAbstractItemView,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from ...simulation.engine import SimulationEngine
from ...simulation.reporter import SimulationReporter
from ..components.console import ConsoleWidget
from ..views.processes_view import ProcessesView
from ..views.memory_view import MemoryView
from ..views.architecture_view import ArchitectureView

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
        
        # Botón Finalizar Programa
        self.btn_finish = QPushButton("Finalizar Programa")
        self.btn_finish.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 5px;")
        self.btn_finish.clicked.connect(self.finish_simulation)
        right_layout.addWidget(self.btn_finish)

        # Checkboxes de Navegación
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

        if engine.architecture == "Modular":
            self.checkbox_flow = QCheckBox("Flujo entre Capas")
            self.checkbox_flow.stateChanged.connect(self.on_navigation_changed)
            nav_layout.addWidget(self.checkbox_flow)
        
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
            arch_control_group = QGroupBox("🔧 Módulos del Sistema")
            arch_control_layout = QVBoxLayout(arch_control_group)
            arch_control_layout.setSpacing(2)
            arch_control_layout.setContentsMargins(4, 4, 4, 4)
            
            self.modules_list = QListWidget()
            self.modules_list.setMaximumHeight(120)
            self.modules_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            # arch_control_layout.addWidget(QLabel("Módulos del Sistema")) # Eliminado por duplicidad
            arch_control_layout.addWidget(self.modules_list)
            
            right_layout.addWidget(arch_control_group)
            
            # Visualización gráfica de arquitectura con flujos (con scroll)
            self.architecture_view = ArchitectureView(engine=self.engine)
            # Crear ScrollArea para permitir desplazamiento
            self.scroll_flow = QScrollArea()
            self.scroll_flow.setWidget(self.architecture_view)
            self.scroll_flow.setWidgetResizable(True)
            # Scrollbars solo cuando sean necesarios
            self.scroll_flow.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.scroll_flow.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.scroll_flow.setFrameShape(QFrame.Shape.NoFrame)
            self.scroll_flow.setStyleSheet("QScrollArea { border: 1px solid #ccc; background-color: #f5f5f5; }")
            self.scroll_flow.setVisible(False)
            
            # Nota: La vista de arquitectura ahora se muestra en el panel principal al seleccionar "Flujo entre Capas"
            
            layer_flow_group = QGroupBox("📡 Flujo entre Capas (Modular)")
            layer_flow_layout = QVBoxLayout(layer_flow_group)
            layer_flow_layout.setSpacing(2)
            layer_flow_layout.setContentsMargins(4, 4, 4, 4)
            self.layer_flow_list = QListWidget()
            self.layer_flow_list.setMaximumHeight(120)
            self.layer_flow_list.setWordWrap(True)
            layer_flow_layout.addWidget(QLabel("Últimas interacciones (máx. 5):"))
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
        
        lbl_speed = QLabel("Duración de Tick (ms):")
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
        
        # Initial update
        self.update_architecture_view()

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
        if not hasattr(self, 'selection_order'):
            self.selection_order = []

        # Map checkboxes to IDs
        options = {
            'processes': self.checkbox_processes,
            'memory': self.checkbox_memory
        }
        if hasattr(self, 'checkbox_flow'):
            options['flow'] = self.checkbox_flow

        # Update selection order
        for key, checkbox in options.items():
            if checkbox.isChecked():
                if key not in self.selection_order:
                    self.selection_order.append(key)
            else:
                if key in self.selection_order:
                    self.selection_order.remove(key)
        
        # Limpiar layout de contenido
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if isinstance(child, QLayoutItem):
                aux = child.widget()
                if aux:
                    aux.setParent(None)
            
        # Ocultar todos los scrolls y página vacía
        self.scroll_processes.setVisible(False)
        self.scroll_memory.setVisible(False)
        if hasattr(self, 'scroll_flow'):
            self.scroll_flow.setVisible(False)
        self.page_empty.setVisible(False)
        
        if not self.selection_order:
            self.content_layout.addWidget(self.page_empty)
            self.page_empty.setVisible(True)
            return

        # Add widgets in order
        for i, key in enumerate(self.selection_order):
            # Add divider if not first
            if i > 0:
                div = QFrame()
                div.setFrameShape(QFrame.Shape.HLine)
                div.setFrameShadow(QFrame.Shadow.Sunken)
                div.setStyleSheet("background-color: white; border: 2px solid white;")
                div.setFixedHeight(3)
                self.content_layout.addWidget(div)

            if key == 'processes':
                self.content_layout.addWidget(self.scroll_processes, 1)
                self.scroll_processes.setVisible(True)
            elif key == 'memory':
                self.content_layout.addWidget(self.scroll_memory, 1)
                self.scroll_memory.setVisible(True)
            elif key == 'flow':
                self.content_layout.addWidget(self.scroll_flow, 1)
                self.scroll_flow.setVisible(True)

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
        
        # Obtener solo los últimos 5 eventos
        all_events = self.engine.layer_flow_events()
        events = all_events[-5:] if all_events else []
        
        # Reconstruir lista siempre para asegurar que se muestra lo último
        self.layer_flow_list.clear()
        
        for ev in events:
            # Formato mejorado con colores e información detallada
            tick = ev.get('tick', '?')
            source = ev.get('source', '?')
            target = ev.get('target', '?')
            action = ev.get('action', '?')
            
            # Parsear acción para mostrar información relevante
            action_display = action
            if ':' in action:
                action_type, action_data = action.split(':', 1)
                if action_type == 'alloc':
                    action_display = f"💾 Asignar memoria PID:{action_data}"
                elif action_type == 'dispatch':
                    action_display = f"▶️ Despachar proceso PID:{action_data}"
                elif action_type == 'ready':
                    action_display = f"✅ Marcar listo PID:{action_data}"
                elif action_type == 'syscall':
                    action_display = f"🔧 Syscall PID:{action_data}"
                elif action_type == 'io_req':
                    action_display = f"📥 Solicitud I/O PID:{action_data}"
                elif action_type == 'load':
                    action_display = f"⬆️ Cargar módulo: {action_data}"
                elif action_type == 'unload':
                    action_display = f"⬇️ Descargar módulo: {action_data}"
            
            item_text = f"[Tick {tick}] {source} → {target}\n   {action_display}"
            item = QListWidgetItem(item_text)
            
            # Forzar texto negro para asegurar contraste con fondos claros
            item.setForeground(QColor(0, 0, 0))
            
            # Color según el tipo de acción
            if 'alloc' in action or 'memory' in action.lower():
                item.setBackground(QColor(220, 237, 255))  # Azul claro para memoria
            elif 'dispatch' in action or 'ready' in action:
                item.setBackground(QColor(220, 255, 220))  # Verde claro para procesos
            elif 'io' in action.lower() or 'syscall' in action.lower():
                item.setBackground(QColor(255, 247, 220))  # Amarillo claro para I/O
            elif 'load' in action or 'unload' in action:
                item.setBackground(QColor(255, 220, 237))  # Rosa claro para módulos
            else:
                item.setBackground(QColor(245, 245, 245))  # Gris claro por defecto
            
            self.layer_flow_list.addItem(item)
        self.layer_flow_list.scrollToBottom()
        
    def update_architecture_view(self):
        """Actualiza la información de la arquitectura incluyendo visualización gráfica."""
        # Actualizar lista de módulos si es arquitectura Modular
        if hasattr(self, 'modules_list') and self.engine.architecture == "Modular":
            self.modules_list.clear()
            
            # Estructura jerárquica solicitada
            modules_structure = [
                ("Núcleo Base", "🔒", []),
                ("Procesos Core", "🔒", ["Planificador", "Despachador"]),
                ("Memoria Core", "🔒", ["Asignación", "Paginación"])
            ]
            
            for name, icon, submodules in modules_structure:
                # Módulo principal
                item = QListWidgetItem(f"{icon} {name}")
                self.modules_list.addItem(item)
                
                # Submódulos
                for sub in submodules:
                    sub_item = QListWidgetItem(f"    • {sub}")
                    self.modules_list.addItem(sub_item)
        
        # Actualizar vista gráfica de arquitectura
        if hasattr(self, 'architecture_view') and self.engine.architecture == "Modular":
            flow_events = self.engine.layer_flow_events()
            self.architecture_view.update_architecture(
                architecture="Modular",
                kernel_mode="modular",
                dynamic_modules=self.engine.dynamic_modules,
                flow_events=flow_events
            )
        
        # Actualizar estado de arquitectura
        if hasattr(self, 'arch_status_label'):
            self._update_arch_status()
            
    def _update_arch_status(self):
        """Actualiza el texto de estado de la arquitectura."""
        if not self.engine.is_running and self.engine.tick_count == 0:
            self.arch_status_label.setText("Esperando inicio de simulación...")
            return

        status = self.engine.get_module_status()
        arch = self.engine.architecture
        
        if arch == "Modular":
            text = "<b>📊 Estado Modular</b><br>"
            text += f"• Núcleo base: <b>ACTIVO</b><br>"
            text += f"• Módulos totales: <b>3</b><br>"
            text += f"• Submódulos totales: <b>4</b>"
        else:
            # Fallback a texto modular
            text = "<b>📊 Estado Modular</b><br>"
            text += f"• Núcleo base: <b>ACTIVO</b><br>"
            text += f"• Módulos totales: <b>{len(self.engine.dynamic_modules)}</b><br>"
        
        self.arch_status_label.setText(text)
        
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

    def finish_simulation(self):
        """Finaliza la simulación, genera reporte y cierra."""
        self.pause_simulation()
        
        try:
            reporter = SimulationReporter(self.engine)
            filename = reporter.generate()
            
            QMessageBox.information(
                self, 
                "Simulación Finalizada", 
                f"Se ha generado el reporte exitosamente:\n{filename}\n\nEl programa se cerrará."
            )
            self.close()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al generar el reporte: {str(e)}"
            )
