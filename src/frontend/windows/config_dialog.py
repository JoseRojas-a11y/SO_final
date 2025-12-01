from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QHBoxLayout, QPushButton, QLabel

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Simulación")
        self.resize(320, 220)
        
        layout = QFormLayout(self)
        
        # Número de CPUs
        self.cpu_count_spin = QSpinBox()
        self.cpu_count_spin.setRange(1, 16)
        self.cpu_count_spin.setValue(4)
        layout.addRow("Número de CPUs:", self.cpu_count_spin)

        # Hilos por CPU (valor por defecto)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 8)
        self.threads_spin.setValue(2)
        layout.addRow("Hilos por CPU (def):", self.threads_spin)

        # Quantum para RR / PriorityRR
        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 20)
        self.quantum_spin.setValue(4)
        layout.addRow("Quantum (RR/PriorityRR):", self.quantum_spin)

        # Memoria: unidades y capacidad por unidad
        self.mem_units_spin = QSpinBox()
        self.mem_units_spin.setRange(1, 8)
        self.mem_units_spin.setValue(2)
        layout.addRow("Unidades de memoria:", self.mem_units_spin)

        self.mem_capacity_spin = QSpinBox()
        self.mem_capacity_spin.setRange(64, 4096)
        self.mem_capacity_spin.setSingleStep(64)
        self.mem_capacity_spin.setValue(256)
        layout.addRow("Capacidad por unidad (MB):", self.mem_capacity_spin)
        
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Iniciar")
        ok_btn.clicked.connect(self.accept)
        btn_box.addWidget(ok_btn)
        layout.addRow(btn_box)
        
    def on_sched_change(self, text):
        pass

    def get_config(self):
        return {
            "architecture": "Modular",
            "scheduling_alg": "FCFS",  # valor inicial, se puede cambiar por CPU en la vista
            "quantum": self.quantum_spin.value(),
            "cpu_count": self.cpu_count_spin.value(),
            "threads_per_cpu": self.threads_spin.value(),
            "memory_units": self.mem_units_spin.value(),
            "memory_unit_capacity_mb": self.mem_capacity_spin.value(),
        }
