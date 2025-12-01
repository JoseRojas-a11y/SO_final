from PyQt6.QtWidgets import QApplication, QDialog
from ..simulation.engine import SimulationEngine
from .windows.config_dialog import ConfigDialog
from .windows.main_window import MainWindow

def launch_gui():
    import sys
    app = QApplication(sys.argv)
    
    # Show Config Dialog
    dialog = ConfigDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        config = dialog.get_config()
        engine = SimulationEngine(
            architecture="Modular",
            scheduling_alg=config["scheduling_alg"],
            quantum=config["quantum"],
            num_cpus=config["cpu_count"],
            threads_per_cpu=config["threads_per_cpu"],
            num_memory_units=config.get("memory_units", 2),
            memory_unit_capacity_mb=config.get("memory_unit_capacity_mb", 256),
        )
        w = MainWindow(engine)
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    launch_gui()
