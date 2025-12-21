from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPolygon
from typing import Dict, Optional, List
from math import sqrt, atan2, cos, sin

class ArchitectureView(QWidget):
    """Componente visual que muestra la arquitectura modular del sistema operativo."""
    
    def __init__(self, parent=None, engine=None):
        super().__init__(parent)
        self.engine = engine
        self.architecture = "Modular"
        self.kernel_mode = "modular"
        self.dynamic_modules = {}
        self.flow_events = []
        self.active_flows = []
        
        # Configuración de tamaño
        self.setMinimumSize(600, 400)
        self.resize(600, 400)
        
        # Timer para animar flujos
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(30)
        
        self.module_positions = {}
        self._processed_event_keys = set()
    
    def sizeHint(self):
        """Retorna el tamaño preferido del widget."""
        return self.minimumSizeHint()
    
    def minimumSizeHint(self):
        """Retorna el tamaño mínimo recomendado."""
        from PyQt6.QtCore import QSize
        return QSize(600, 400)
        
    def update_architecture(self, architecture: str = "Modular", kernel_mode: str = "modular",
                            dynamic_modules: Optional[Dict] = None, flow_events: Optional[List[Dict]] = None, **_: object):
        """Actualiza la visualización (modo Modular únicamente)."""
        # Forzamos modo Modular e ignoramos parámetros ajenos
        self.architecture = "Modular"
        self.kernel_mode = "modular"
        self.dynamic_modules = dynamic_modules or {}
        
        # Actualizar flujos activos si hay nuevos eventos
        if flow_events is not None:
            self._update_active_flows(flow_events)
        
        self.update()
    
    def _update_active_flows(self, new_events: List[Dict]):
        """Actualiza los flujos activos basándose en los nuevos eventos."""
        if not new_events:
            return
        
        # Procesar los últimos 5 eventos para asegurar que no perdemos nada importante
        recent_events = new_events[-5:]
        
        for event in recent_events:
            event_key = (
                event.get("tick", ""),
                event.get("source", ""),
                event.get("target", ""),
                event.get("action", "")
            )
            
            if event_key not in self._processed_event_keys:
                flow = {
                    "source": event.get("source", ""),
                    "target": event.get("target", ""),
                    "action": event.get("action", ""),
                    "progress": 0.0,
                    "age": 0,
                    "speed": 0.05,
                    "opacity": 1.0
                }
                
                # Ajustar velocidad
                action = event.get("action", "").lower()
                if "alloc" in action: flow["speed"] = 0.04
                elif "dispatch" in action: flow["speed"] = 0.05
                else: flow["speed"] = 0.05
                
                self.active_flows.append(flow)
                self._processed_event_keys.add(event_key)
        
        # Limpiar cache
        if len(self._processed_event_keys) > 100:
            sorted_keys = sorted(list(self._processed_event_keys), key=lambda x: str(x[0]), reverse=True)
            self._processed_event_keys = set(sorted_keys[:50])
        
        # Limitar flujos activos
        if len(self.active_flows) > 5:
            self.active_flows = self.active_flows[-5:]
    
    def _update_animation(self):
        """Actualiza el progreso de la animación."""
        if not self.active_flows:
            return
        
        flows_to_remove = []
        for flow in self.active_flows:
            flow["progress"] += flow.get("speed", 0.05)
            flow["age"] += 1
            
            if flow["progress"] > 0.90:
                flow["opacity"] = max(0.0, 1.0 - ((flow["progress"] - 0.90) / 0.10))
            
            if flow["progress"] > 1.0 or flow["age"] > 100:
                flows_to_remove.append(flow)
        
        for flow in flows_to_remove:
            self.active_flows.remove(flow)
        
        self.update()
        
    def paintEvent(self, event):
        """Dibuja la representación visual (solo arquitectura modular)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Fondo
        painter.fillRect(0, 0, w, h, QColor(245, 245, 245))
        self._draw_modular(painter, w, h)
            
    def _draw_modular(self, painter: QPainter, w: int, h: int):
        """Dibuja la arquitectura modular estilo diagrama de flujo."""
        self.module_positions.clear()
        
        # Configuración de estilo
        pen_border = QPen(QColor(0, 0, 0), 2)
        font_bold = QFont("Arial", 9, QFont.Weight.Bold)
        font_normal = QFont("Arial", 8)
        
        # Dimensiones de los círculos
        radius = 35
        
        # Coordenadas X (Columnas)
        col_1_x = int(w * 0.15)
        col_2_x = int(w * 0.5)
        col_3_x = int(w * 0.85)
        
        # Coordenadas Y (Filas calculadas para alineación)
        # Grupo Procesos (Arriba)
        y_plan = int(h * 0.2)
        y_desp = int(h * 0.4)
        y_proc_core = int((y_plan + y_desp) / 2)
        
        # Grupo Memoria (Abajo)
        y_pag = int(h * 0.6)
        y_asig = int(h * 0.8)
        y_mem_core = int((y_pag + y_asig) / 2)
        
        # Núcleo (Centro vertical)
        y_kernel = int(h * 0.5)
        
        # Definir nodos y conexiones
        # Estructura: (Nombre, X, Y, Color, [Conexiones a...])
        c_blue = QColor(173, 216, 230)  # Light Blue
        c_green = QColor(154, 205, 50)  # Yellow Green
        c_red = QColor(250, 128, 114)   # Salmon
        
        nodes = {
            "Planificador": {"x": col_1_x, "y": y_plan, "color": c_blue, "to": ["Proceso Core"]},
            "Despachador": {"x": col_1_x, "y": y_desp, "color": c_blue, "to": ["Proceso Core"]},
            "Paginación": {"x": col_1_x, "y": y_pag, "color": c_blue, "to": ["Memoria Core"]},
            "Asignación": {"x": col_1_x, "y": y_asig, "color": c_blue, "to": ["Memoria Core"]},
            
            "Proceso Core": {"x": col_2_x, "y": y_proc_core, "color": c_green, "to": ["Núcleo Base"]},
            "Memoria Core": {"x": col_2_x, "y": y_mem_core, "color": c_green, "to": ["Núcleo Base"]},
            
            "Núcleo Base": {"x": col_3_x, "y": y_kernel, "color": c_red, "to": []}
        }
        
        # 1. Dibujar Conexiones (Flechas)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        for name, data in nodes.items():
            start_x, start_y = data["x"], data["y"]
            for target_name in data["to"]:
                if target_name in nodes:
                    target = nodes[target_name]
                    end_x, end_y = target["x"], target["y"]
                    
                    # Vector dirección
                    dx = end_x - start_x
                    dy = end_y - start_y
                    dist = sqrt(dx*dx + dy*dy)
                    if dist == 0: continue
                    
                    # Offset del radio para que la línea empiece/termine en el borde
                    off_x = (dx / dist) * radius
                    off_y = (dy / dist) * radius
                    
                    p1 = QPoint(int(start_x + off_x), int(start_y + off_y))
                    p2 = QPoint(int(end_x - off_x), int(end_y - off_y))
                    
                    painter.drawLine(p1, p2)
                    self._draw_arrow_head(painter, p1, p2)

        # 2. Dibujar Nodos (Círculos)
        for name, data in nodes.items():
            cx, cy = data["x"], data["y"]
            color = data["color"]
            
            # Guardar posición para animaciones
            self.module_positions[name] = (cx, cy)
            
            # Círculo
            painter.setBrush(QBrush(color))
            painter.setPen(pen_border)
            painter.drawEllipse(QPoint(cx, cy), radius, radius)
            
            # Texto
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(font_bold if "Core" in name or "Núcleo" in name else font_normal)
            
            # Rect para texto debajo del círculo
            text_rect = QRect(cx - 60, cy + radius + 5, 120, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, name)

        # Dibujar flujos activos animados al final (encima de todo)
        self._draw_active_flows(painter)

    def _draw_arrow_head(self, painter, p1, p2):
        """Dibuja una punta de flecha en p2 apuntando desde p1."""
        arrow_size = 10
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        angle = atan2(dy, dx)
        
        p3 = QPoint(
            int(p2.x() - arrow_size * cos(angle - 0.5)),
            int(p2.y() - arrow_size * sin(angle - 0.5))
        )
        p4 = QPoint(
            int(p2.x() - arrow_size * cos(angle + 0.5)),
            int(p2.y() - arrow_size * sin(angle + 0.5))
        )
        
        painter.drawPolygon(QPolygon([p2, p3, p4]))
    
    def _draw_active_flows(self, painter: QPainter):
        """Dibuja los flujos activos de información entre módulos (mejorado visualmente)."""
        if not self.active_flows:
            return
        
        # Dibujar flujos animados
        for flow in self.active_flows:
            source_name = flow.get("source", "")
            target_name = flow.get("target", "")
            progress = flow.get("progress", 0.0)
            opacity = flow.get("opacity", 1.0)
            
            source_pos = self.module_positions.get(source_name)
            target_pos = self.module_positions.get(target_name)
            
            if source_pos and target_pos:
                # Calcular posición del paquete animado
                x1, y1 = source_pos
                x2, y2 = target_pos
                
                # Interpolar posición basada en el progreso
                packet_x = x1 + (x2 - x1) * progress
                packet_y = y1 + (y2 - y1) * progress
                
                # Determinar color según el tipo de acción (mejorado con más diferenciación)
                action = flow.get("action", "")
                if "alloc" in action.lower():
                    # Azul más intenso para asignación de memoria (ingreso de proceso)
                    flow_color = QColor(33, 150, 243)  # Azul brillante
                    flow_type = "MEM"
                elif "memory" in action.lower():
                    flow_color = QColor(66, 133, 244)  # Azul estándar
                    flow_type = "MEM"
                elif "dispatch" in action.lower():
                    # Verde más vibrante para despacho
                    flow_color = QColor(46, 125, 50)  # Verde oscuro vibrante
                    flow_type = "EXEC"
                elif "ready" in action.lower():
                    # Verde claro para procesos listos
                    flow_color = QColor(76, 175, 80)  # Verde claro
                    flow_type = "READY"
                elif "io" in action.lower() or "io_req" in action.lower():
                    # Amarillo/naranja para I/O
                    flow_color = QColor(255, 152, 0)  # Naranja
                    flow_type = "I/O"
                elif "syscall" in action.lower():
                    # Amarillo para syscalls
                    flow_color = QColor(251, 188, 5)  # Amarillo
                    flow_type = "SYS"
                else:
                    flow_color = QColor(234, 67, 53)  # Rojo por defecto
                    flow_type = "?"
                
                # Aplicar opacidad al color
                flow_color.setAlphaF(opacity)
                
                # Dibujar línea de flujo activa (con opacidad y brillo)
                # Primero dibujar una línea más gruesa y tenue como resplandor
                glow_color = QColor(flow_color)
                glow_color.setAlphaF(opacity * 0.3)
                pen_glow = QPen(glow_color, 5)
                pen_glow.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen_glow)
                painter.drawLine(x1, y1, x2, y2)
                
                # Luego la línea principal
                pen = QPen(flow_color, 3)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawLine(x1, y1, x2, y2)
                
                # Dibujar paquete animado (tamaño variable según tipo de acción)
                # Para alloc (ingreso de proceso), hacer más visible
                if "alloc" in action.lower():
                    packet_size = 10  # Más grande para ingreso de procesos
                else:
                    packet_size = 8
                
                # Dibujar círculo exterior con resplandor para alloc
                if "alloc" in action.lower():
                    glow_packet = QColor(flow_color)
                    glow_packet.setAlphaF(opacity * 0.4)
                    painter.setBrush(QBrush(glow_packet))
                    painter.setPen(QPen(QColor(255, 255, 255, 0), 0))
                    painter.drawEllipse(int(packet_x - packet_size // 2 - 2), 
                                      int(packet_y - packet_size // 2 - 2), 
                                      packet_size + 4, packet_size + 4)
                
                # Dibujar paquete principal
                painter.setBrush(QBrush(flow_color))
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.drawEllipse(int(packet_x - packet_size // 2), 
                                  int(packet_y - packet_size // 2), 
                                  packet_size, packet_size)
                
                # Etiqueta mejorada con más información (rango extendido para mejor legibilidad)
                if progress > 0.20 and progress < 0.80:
                    font_label = QFont("Arial", 7, QFont.Weight.Bold)
                    painter.setFont(font_label)
                    
                    # Extraer PID de la acción
                    action_text = action.split(":")[-1] if ":" in action else ""
                    label_text = ""
                    
                    # Determinar texto a mostrar según tipo
                    if "alloc" in action.lower() and action_text:
                        # Para ingreso de proceso, mostrar PID más destacado con tamaño si está disponible
                        process_info = ""
                        try:
                            pid_int = int(action_text)
                            # Intentar obtener información del proceso si el engine está disponible
                            if self.engine and hasattr(self.engine, 'get_process'):
                                process = self.engine.get_process(pid_int)
                                if process and hasattr(process, 'size_mb'):
                                    process_info = f" {process.size_mb}MB"
                        except (ValueError, AttributeError):
                            pass
                        
                        label_text = f"PID:{action_text}{process_info}"
                    elif action_text:
                        # Para otros casos, mostrar tipo y PID
                        label_text = f"{flow_type}:{action_text}"
                    
                    if label_text:
                        # Calcular tamaño del texto
                        fm = painter.fontMetrics()
                        text_w = fm.horizontalAdvance(label_text)
                        text_h = fm.height()
                        
                        bg_rect_x = int(packet_x + 8)
                        bg_rect_y = int(packet_y - 10)
                        bg_rect_w = text_w + 8
                        bg_rect_h = text_h + 4
                        
                        # Fondo oscuro para mejor contraste en cualquier tema
                        painter.fillRect(bg_rect_x, bg_rect_y, bg_rect_w, bg_rect_h, 
                                       QColor(40, 40, 40, int(230 * opacity)))
                        
                        # Borde del color del flujo
                        painter.setPen(QPen(flow_color, 1))
                        painter.drawRect(bg_rect_x, bg_rect_y, bg_rect_w, bg_rect_h)
                        
                        # Texto blanco
                        painter.setPen(QPen(QColor(255, 255, 255, int(255 * opacity)), 1))
                        painter.drawText(bg_rect_x, bg_rect_y, bg_rect_w, bg_rect_h, 
                                       Qt.AlignmentFlag.AlignCenter, label_text)
                
                # Dibujar flecha al final si está cerca del destino
                if progress > 0.7:
                    self._draw_arrow(painter, packet_x, packet_y, x2, y2, flow_color)
    
    def _draw_arrow(self, painter: QPainter, x1: int, y1: int, x2: int, y2: int, color: QColor):
        """Dibuja una flecha apuntando de (x1,y1) hacia (x2,y2)."""
        angle = atan2(y2 - y1, x2 - x1)
        arrow_size = 8
        arrow_angle = 0.5
        
        # Calcular puntos de la flecha
        arrow_x = x2 - arrow_size * cos(angle)
        arrow_y = y2 - arrow_size * sin(angle)
        
        arrow_x1 = arrow_x - arrow_size * cos(angle - arrow_angle)
        arrow_y1 = arrow_y - arrow_size * sin(angle - arrow_angle)
        arrow_x2 = arrow_x - arrow_size * cos(angle + arrow_angle)
        arrow_y2 = arrow_y - arrow_size * sin(angle + arrow_angle)
        
        # Dibujar flecha
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 2))
        polygon = QPolygon([QPoint(x2, y2), QPoint(int(arrow_x1), int(arrow_y1)), QPoint(int(arrow_x2), int(arrow_y2))])
        painter.drawPolygon(polygon)
