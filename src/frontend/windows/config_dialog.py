from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QHBoxLayout, QPushButton, QLabel, QVBoxLayout, QGroupBox

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Simulación")
        self.resize(350, 300)
        
        main_layout = QVBoxLayout(self)
        
        # --- Configuración de CPUs ---
        cpu_group = QGroupBox("Configuración de CPUs")
        cpu_layout = QFormLayout(cpu_group)
        
        # Número de CPUs
        self.cpu_count_spin = QSpinBox()
        # Límite: mínimo 1, máximo 8 CPUs
        self.cpu_count_spin.setRange(1, 8)
        self.cpu_count_spin.setValue(4)
        cpu_layout.addRow("Número de CPUs:", self.cpu_count_spin)

        # Hilos por CPU (valor por defecto)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 8)
        self.threads_spin.setValue(2)
        cpu_layout.addRow("Hilos por CPU (def):", self.threads_spin)
        
        main_layout.addWidget(cpu_group)

        # --- Configuración de Memoria ---
        mem_group = QGroupBox("Configuración de Memoria")
        mem_layout = QFormLayout(mem_group)
        
        mem_layout.addRow(QLabel("Ten en cuenta que 16 MB están reservados para el sistema."))

        # Memoria: unidades y capacidad por unidad
        self.mem_units_spin = QSpinBox()
        # Límite: mínimo 1, máximo 8 unidades de memoria
        self.mem_units_spin.setRange(1, 8)
        self.mem_units_spin.setValue(2)
        mem_layout.addRow("Unidades de memoria:", self.mem_units_spin)

        self.mem_capacity_spin = QSpinBox()
        self.mem_capacity_spin.setRange(64, 4096)
        self.mem_capacity_spin.setSingleStep(64)
        self.mem_capacity_spin.setValue(256)
        mem_layout.addRow("Capacidad por unidad (MB):", self.mem_capacity_spin)
        
        main_layout.addWidget(mem_group)
        
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Iniciar")
        ok_btn.clicked.connect(self.accept)
        btn_box.addWidget(ok_btn)
        main_layout.addLayout(btn_box)
        
    def on_sched_change(self, text):
        pass

    def get_config(self):
        return {
            "architecture": "Modular",
            "scheduling_alg": "FCFS",  # valor inicial, se puede cambiar por CPU en la vista
            "quantum": 4, # Valor por defecto, se cambiará en la vista si es necesario
            "cpu_count": self.cpu_count_spin.value(),
            "threads_per_cpu": self.threads_spin.value(),
            "memory_units": self.mem_units_spin.value(),
            "memory_unit_capacity_mb": self.mem_capacity_spin.value(),
        }
