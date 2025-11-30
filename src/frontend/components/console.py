from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit
from ...simulation.engine import SimulationEngine

class ConsoleWidget(QWidget):
    def __init__(self, engine: SimulationEngine, main_window, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.main_window = main_window
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background-color: #1e1e1e; color: #00FF00; font-family: Consolas; font-size: 10pt;")
        layout.addWidget(self.output)
        
        self.input = QLineEdit()
        self.input.setPlaceholderText("Escriba un comando (ej: help)...")
        self.input.setStyleSheet("background-color: #333; color: white; font-family: Consolas; font-size: 10pt;")
        self.input.returnPressed.connect(self.process_command)
        layout.addWidget(self.input)
        
        self.print_msg("=== Terminal de Control SO ===")
        self.print_msg("Escriba 'help' para ver la lista de comandos.")

    def print_msg(self, msg: str):
        self.output.append(msg)
        sb = self.output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def process_command(self):
        cmd_line = self.input.text().strip()
        if not cmd_line: return
        
        self.input.clear()
        self.print_msg(f"> {cmd_line}")
        
        parts = cmd_line.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        try:
            if cmd == "help":
                self.show_help()
            elif cmd == "create":
                self.cmd_create(args)
            elif cmd == "pause":
                self.main_window.pause_simulation()
                self.print_msg("Simulación pausada.")
            elif cmd == "star":
                self.main_window.active_simulation()
                self.print_msg("Simulación reanudada.")
            elif cmd == "speed":
                self.cmd_speed(args)
            elif cmd == "auto":
                self.cmd_auto(args)
            elif cmd == "clear":
                self.output.clear()
            else:
                self.print_msg(f"Error: Comando '{cmd}' desconocido.")
        except Exception as e:
            self.print_msg(f"Error ejecutando comando: {str(e)}")

    def show_help(self):
        help_text = """
Comandos Disponibles:
---------------------
create <size> <duration> [prio] : Crea un proceso manual (MB, ticks, 0-10)
pause                           : Pausa la simulación
star                            : Activa la simulación
speed <ms>                      : Cambia velocidad (ms por tick, min 10)
auto <on|off>                   : Activa/Desactiva creación automática
clear                           : Limpia la consola
help                            : Muestra esta ayuda
"""
        self.print_msg(help_text.strip())

    def cmd_create(self, args):
        if len(args) < 2:
            self.print_msg("Uso: create <size_mb> <duration_ticks> [priority]")
            return
        
        try:
            size = int(args[0])
            duration = int(args[1])
            priority = int(args[2]) if len(args) > 2 else 0
            
            p = self.engine.manual_create_process(size, duration)
            p.priority = priority 
            
            self.print_msg(f"Proceso {p.name} creado (PID {p.pid}, {size}MB, {duration}t, Prio {priority})")
        except ValueError:
            self.print_msg("Error: Los argumentos deben ser números enteros.")

    def cmd_speed(self, args):
        if not args:
            self.print_msg("Uso: speed <ms>")
            return
        try:
            ms = int(args[0])
            if ms < 10: ms = 10
            self.main_window.set_speed(ms)
            self.print_msg(f"Velocidad ajustada a {ms}ms por tick.")
        except ValueError:
            self.print_msg("Error: El valor debe ser un número entero.")

    def cmd_auto(self, args):
        if not args:
            status = "ON" if self.engine.auto_create_processes else "OFF"
            self.print_msg(f"Generación automática: {status}")
            return
        
        val = args[0].lower()
        if val == "on":
            self.engine.auto_create_processes = True
            self.print_msg("Generación automática ACTIVADA.")
        elif val == "off":
            self.engine.auto_create_processes = False
            self.print_msg("Generación automática DESACTIVADA.")
        else:
            self.print_msg("Uso: auto <on|off>")
