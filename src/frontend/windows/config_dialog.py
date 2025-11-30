from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QHBoxLayout, QPushButton

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
