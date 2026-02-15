"""
Main Window - Orquestador principal de la interfaz.
Principio SRP: Coordina los componentes pero delega la lógica a controladores y paneles.
Principio DIP: Depende de abstracciones (controladores y paneles), no de implementaciones concretas.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QDialog, QPushButton, QSpinBox, QFormLayout,
    QMessageBox, QCheckBox
)
from PyQt6.QtCore import QTimer

from ...simulation.engine import SimulationEngine
from ...simulation.reporter import SimulationReporter
from ..components.console import ConsoleWidget
from ..views.processes_view import ProcessesView
from ..views.memory_view import MemoryView
from ..views.architecture_view import ArchitectureView

# Importar controladores
from .controllers.navigation_controller import NavigationController
from .controllers.simulation_controller import SimulationController

# Importar paneles
from .panels.architecture_panel import (
    ArchitectureStatusPanel,
    ModulesPanel,
    ExternalModulesPanel,
    LayerFlowPanel
)
from .panels.control_panel import SimulationControlPanel, FinishButton
from .panels.content_panel import ContentPanel, EmptyPage, ScrollAreaFactory


class MainWindow(QMainWindow):
    """
    Ventana principal que actúa como orquestador de la aplicación.
    Coordina los diferentes componentes siguiendo el patrón de composición.
    """
    
    def __init__(self, engine: SimulationEngine):
        super().__init__()
        self.engine = engine
        self._setup_window()
        self._init_timer()
        self._init_controllers()
        self._init_views()
        self._init_panels()
        self._setup_layout()
        self._connect_signals()
        self._initial_update()

    def _setup_window(self) -> None:
        """Configura las propiedades básicas de la ventana."""
        arch_name = getattr(
            self.engine, 
            "architecture_name", 
            str(getattr(self.engine, "architecture", ""))
        )
        self.setWindowTitle(f"Simulación SO - {arch_name} - {self.engine.scheduling_alg_name}")
        self.resize(1200, 800)

    def _init_timer(self) -> None:
        """Inicializa el timer para la simulación."""
        self.timer = QTimer(self)

    def _init_controllers(self) -> None:
        """Inicializa los controladores."""
        # Controlador de simulación
        self.sim_controller = SimulationController(self.engine, self.timer)
        
    def _init_views(self) -> None:
        """Inicializa las vistas principales."""
        self.processes_view = ProcessesView(self.engine)
        self.memory_view = MemoryView(self.engine)
        
        # Vista de arquitectura solo para Modular
        if self.engine.architecture == "Modular":
            self.architecture_view = ArchitectureView(engine=self.engine)

    def _init_panels(self) -> None:
        """Inicializa los paneles de la interfaz."""
        # Panel de contenido principal
        self.content_panel = ContentPanel()
        
        # Página vacía
        self.page_empty = EmptyPage()
        
        # Scroll areas para las vistas
        self.scroll_processes = ScrollAreaFactory.create(self.processes_view)
        self.scroll_memory = ScrollAreaFactory.create(self.memory_view)
        
        if self.engine.architecture == "Modular":
            self.scroll_flow = ScrollAreaFactory.create_with_scrollbars(
                self.architecture_view
            )
        
        # Controlador de navegación
        self.nav_controller = NavigationController(
            self.content_panel.get_layout(),
            on_change_callback=self._on_navigation_changed
        )
        self.nav_controller.set_empty_page(self.page_empty)
        
        # Panel de estado de arquitectura
        self.arch_status_panel = ArchitectureStatusPanel()
        
        # Panel de control de simulación
        self.control_panel = SimulationControlPanel(
            on_toggle=self._toggle_simulation,
            on_restart=self._restart_simulation,
            on_speed_changed=self._set_speed
        )
        
        # Botón finalizar
        self.finish_button = FinishButton(on_finish=self._finish_simulation)
        
        # Paneles específicos por arquitectura
        if self.engine.architecture == "Modular":
            self.modules_panel = ModulesPanel()
            self.layer_flow_panel = LayerFlowPanel()
        elif self.engine.architecture == "Microkernel":
            self.ext_modules_panel = ExternalModulesPanel()

    def _setup_layout(self) -> None:
        """Configura el layout principal de la ventana."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Área de contenido (izquierda)
        self._setup_content_area()
        main_layout.addWidget(self.content_panel)
        
        # Panel derecho (navegación, controles, consola)
        right_widget = self._build_right_panel()
        right_widget.setFixedWidth(300)
        main_layout.addWidget(right_widget)

    def _setup_content_area(self) -> None:
        """Configura el área de contenido con la página vacía inicial."""
        self.content_panel.get_layout().addWidget(self.page_empty)

    def _build_right_panel(self) -> QWidget:
        """Construye el panel derecho con todos sus componentes."""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(3)
        right_layout.setContentsMargins(2, 2, 2, 2)
        
        # Botón finalizar
        right_layout.addWidget(self.finish_button)
        
        # Panel de navegación
        nav_group = self._build_navigation_panel()
        right_layout.addWidget(nav_group)
        
        # Panel de estado de arquitectura
        right_layout.addWidget(self.arch_status_panel)
        
        # Paneles específicos por arquitectura
        if self.engine.architecture == "Modular":
            right_layout.addWidget(self.modules_panel)
            right_layout.addWidget(self.layer_flow_panel)
        elif self.engine.architecture == "Microkernel":
            right_layout.addWidget(self.ext_modules_panel)
        
        # Panel de control
        right_layout.addWidget(self.control_panel)
        
        # Consola
        self.console = ConsoleWidget(self.engine, self)
        right_layout.addWidget(self.console, 1)
        
        return right_widget

    def _build_navigation_panel(self) -> QGroupBox:
        """Construye el panel de opciones de navegación."""
        nav_group = QGroupBox("Opciones")
        nav_layout = QVBoxLayout(nav_group)
        nav_layout.setSpacing(2)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        
        # Checkbox Gestión de Procesos
        self.checkbox_processes = QCheckBox("Gestión de Procesos")
        nav_layout.addWidget(self.checkbox_processes)
        
        # Checkbox Gestión de Memoria
        self.checkbox_memory = QCheckBox("Gestión de Memoria")
        nav_layout.addWidget(self.checkbox_memory)
        
        # Registrar en el controlador de navegación
        self.nav_controller.register_view(
            'processes', 
            self.checkbox_processes, 
            self.scroll_processes
        )
        self.nav_controller.register_view(
            'memory', 
            self.checkbox_memory, 
            self.scroll_memory
        )
        
        # Flujo entre capas (solo Modular)
        if self.engine.architecture == "Modular":
            self.checkbox_flow = QCheckBox("Flujo entre Capas")
            nav_layout.addWidget(self.checkbox_flow)
            self.nav_controller.register_view(
                'flow',
                self.checkbox_flow,
                self.scroll_flow
            )
        
        return nav_group

    def _connect_signals(self) -> None:
        """Conecta las señales y callbacks entre componentes."""
        # Configurar logging en el controlador de simulación
        self.sim_controller.set_log_callback(self.console.print_msg)
        
        # Agregar callbacks de tick
        self.sim_controller.add_tick_callback(self._on_tick)
        
        # Callback de cambio de estado de simulación
        self.sim_controller.add_state_change_callback(self._on_simulation_state_changed)

    def _initial_update(self) -> None:
        """Realiza la actualización inicial de la interfaz."""
        self._update_architecture_view()

    # ==================== Handlers de Eventos ====================
    
    def _on_navigation_changed(self) -> None:
        """Callback cuando cambia la navegación."""
        # Se puede agregar lógica adicional si es necesario
        pass

    def _on_tick(self) -> None:
        """Callback ejecutado en cada tick de la simulación."""
        self.processes_view.refresh_all()
        self.memory_view.refresh_all()
        self._update_architecture_view()
        self._refresh_layer_flow()

    def _on_simulation_state_changed(self, is_running: bool) -> None:
        """Callback cuando cambia el estado de la simulación."""
        if is_running:
            self.control_panel.set_running_state()
        else:
            self.control_panel.set_paused_state()
        
        # Refrescar vistas para habilitar/deshabilitar controles por CPU
        self.processes_view.refresh_all()
        self.memory_view.refresh_all()

    # ==================== Control de Simulación ====================
    
    def _toggle_simulation(self) -> None:
        """Alterna entre pausar y reanudar la simulación."""
        self.sim_controller.toggle(self.control_panel.get_speed())

    def _restart_simulation(self) -> None:
        """Reinicia la simulación."""
        self.sim_controller.restart()
        self.processes_view.refresh_all()
        self.memory_view.refresh_all()
        self.control_panel.set_initial_state()

    def _set_speed(self, ms: int) -> None:
        """Establece la velocidad de la simulación."""
        self.sim_controller.set_speed(ms)

    def _finish_simulation(self) -> None:
        """Finaliza la simulación, genera reporte y cierra."""
        self.sim_controller.pause()
        
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

    # ==================== Actualización de Vistas ====================
    
    def _update_architecture_view(self) -> None:
        """Actualiza la información de la arquitectura."""
        # Actualizar panel de módulos (Modular)
        if hasattr(self, 'modules_panel') and self.engine.architecture == "Modular":
            self._update_modules_panel()
        
        # Actualizar vista gráfica de arquitectura
        if hasattr(self, 'architecture_view') and self.engine.architecture == "Modular":
            self._update_architecture_graphic()
        
        # Actualizar estado de arquitectura
        self._update_arch_status()

    def _update_modules_panel(self) -> None:
        """Actualiza el panel de módulos."""
        modules_structure = [
            ("Núcleo Base", "🔒", []),
            ("Procesos Core", "🔒", ["Planificador", "Despachador"]),
            ("Memoria Core", "🔒", ["Asignación", "Paginación"])
        ]
        self.modules_panel.set_modules_structure(modules_structure)

    def _update_architecture_graphic(self) -> None:
        """Actualiza la vista gráfica de arquitectura."""
        flow_events = self.engine.layer_flow_events()
        self.architecture_view.update_architecture(
            architecture="Modular",
            kernel_mode="modular",
            dynamic_modules=self.engine.dynamic_modules,
            flow_events=flow_events
        )

    def _update_arch_status(self) -> None:
        """Actualiza el texto de estado de la arquitectura."""
        if not self.engine.is_running and self.engine.tick_count == 0:
            self.arch_status_panel.set_waiting_status()
            return

        if self.engine.architecture == "Modular":
            self.arch_status_panel.set_modular_status()
        else:
            modules_count = len(self.engine.dynamic_modules)
            self.arch_status_panel.set_generic_status(modules_count)

    def _refresh_layer_flow(self) -> None:
        """Actualiza el panel de flujo entre capas."""
        if not hasattr(self, 'layer_flow_panel'):
            return
        
        events = self.engine.layer_flow_events()
        self.layer_flow_panel.update_events(events)

    # ==================== Métodos Auxiliares ====================
    
    def create_manual_process(self) -> None:
        """Crea un proceso manualmente a través de un diálogo."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Crear Proceso")
        layout = QFormLayout(dialog)
        
        sb_size = QSpinBox()
        sb_size.setRange(1, 128)
        sb_size.setValue(16)
        layout.addRow("Tamaño (MB):", sb_size)
        
        sb_dur = QSpinBox()
        sb_dur.setRange(5, 200)
        sb_dur.setValue(50)
        layout.addRow("Duración (ticks):", sb_dur)
        
        btn = QPushButton("Crear")
        btn.clicked.connect(dialog.accept)
        layout.addRow(btn)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.engine.manual_create_process(sb_size.value(), sb_dur.value())

    # ==================== Métodos de Compatibilidad ====================
    # Estos métodos mantienen compatibilidad con código existente (como ConsoleWidget)
    
    def toggle_simulation(self) -> None:
        """Método de compatibilidad."""
        self._toggle_simulation()

    def pause_simulation(self) -> None:
        """Método de compatibilidad."""
        self.sim_controller.pause()
        self.control_panel.set_paused_state()

    def resume_simulation(self) -> None:
        """Método de compatibilidad."""
        self.sim_controller.resume(self.control_panel.get_speed())
        self.control_panel.set_running_state()

    def restart_simulation(self) -> None:
        """Método de compatibilidad."""
        self._restart_simulation()

    def set_speed(self, ms: int) -> None:
        """Método de compatibilidad."""
        self._set_speed(ms)
        self.control_panel.set_speed(ms)

    def finish_simulation(self) -> None:
        """Método de compatibilidad."""
        self._finish_simulation()
