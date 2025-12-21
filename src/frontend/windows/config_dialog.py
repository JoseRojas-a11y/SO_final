from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QHBoxLayout, QPushButton, QLabel, QVBoxLayout, QGroupBox, QCheckBox

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Simulación")
        self.resize(400, 550)
        
        main_layout = QVBoxLayout(self)
        
        # --- BLOQUE 1: HARDWARE ---
        hw_group = QGroupBox("Configuración de Hardware")
        hw_layout = QFormLayout(hw_group)
        
        # CPUs
        self.cpu_count_spin = QSpinBox()
        self.cpu_count_spin.setRange(1, 8)
        self.cpu_count_spin.setValue(4)
        hw_layout.addRow("Número de CPUs:", self.cpu_count_spin)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 8)
        self.threads_spin.setValue(2)
        hw_layout.addRow("Hilos por CPU:", self.threads_spin)
        
        # Memoria Física
        self.mem_units_spin = QSpinBox()
        self.mem_units_spin.setRange(1, 8)
        self.mem_units_spin.setValue(1)
        hw_layout.addRow("Bancos de Memoria (Unidades):", self.mem_units_spin)

        self.mem_capacity_spin = QSpinBox()
        self.mem_capacity_spin.setRange(64, 4096)
        self.mem_capacity_spin.setSingleStep(64)
        self.mem_capacity_spin.setValue(1024)
        hw_layout.addRow("Capacidad por Banco (MB):", self.mem_capacity_spin)

        # Almacenamiento
        self.storage_type_combo = QComboBox()
        self.storage_type_combo.addItems(["HDD", "SSD", "NVMe", "Tape"])
        self.storage_type_combo.setCurrentText("HDD")
        hw_layout.addRow("Tipo Almacenamiento (Swap):", self.storage_type_combo)
        
        # MMU Hardware
        self.tlb_check = QCheckBox("Incluir TLB (Translation Lookaside Buffer)")
        self.tlb_check.setChecked(True)
        hw_layout.addRow(self.tlb_check)
        
        main_layout.addWidget(hw_group)

        # --- BLOQUE 2: SOFTWARE (SO) ---
        sw_group = QGroupBox("Configuración de Software (SO)")
        sw_layout = QFormLayout(sw_group)
        
        sw_layout.addRow(QLabel("<i>* 64 MB reservados para el Kernel.</i>"))

        # Gestión de Memoria
        self.alloc_alg_combo = QComboBox()
        self.alloc_alg_combo.addItems(["first", "best", "worst"])
        self.alloc_alg_combo.setCurrentText("first")
        sw_layout.addRow("Algoritmo de Asignación:", self.alloc_alg_combo)

        self.page_alg_combo = QComboBox()
        self.page_alg_combo.addItems(["FIFO", "LRU", "Optimal"])
        self.page_alg_combo.setCurrentText("FIFO")
        sw_layout.addRow("Algoritmo de Paginación:", self.page_alg_combo)
        
        self.pt_type_combo = QComboBox()
        self.pt_type_combo.addItems(["SingleLevel", "TwoLevel", "Hashed", "Inverted"])
        self.pt_type_combo.setCurrentText("SingleLevel")
        sw_layout.addRow("Tipo Tabla de Páginas:", self.pt_type_combo)

        main_layout.addWidget(sw_group)
        
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Iniciar Simulación")
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
            "allocation_algorithm": self.alloc_alg_combo.currentText(),
            "paging_algorithm": self.page_alg_combo.currentText(),
            "tlb_enabled": self.tlb_check.isChecked(),
            "page_table_type": self.pt_type_combo.currentText(),
            "storage_type": self.storage_type_combo.currentText(),
        }
