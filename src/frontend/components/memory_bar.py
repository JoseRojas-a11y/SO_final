from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QMouseEvent
from PyQt6.QtCore import Qt
from typing import List
from ...os_core.models import MemoryBlock

class MemoryBar(QWidget):
    def __init__(self, blocks: List[MemoryBlock], total: int, parent=None):
        super().__init__(parent)
        self.blocks = blocks
        self.total = total
        self.setMinimumHeight(60)
        self.setMouseTracking(True)

    def set_blocks(self, blocks: List[MemoryBlock]):
        self.blocks = blocks
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        bar_h = h - 20 
        
        # Background
        painter.fillRect(0, 0, w, bar_h, QColor(240, 240, 240))
        
        if self.total > 0:
            scale = w / self.total
            
            # Draw Blocks
            for b in self.blocks:
                x = int(b.start * scale)
                bw = int(b.size * scale)
                if bw < 1: bw = 1
                
                if b.process_pid == 0:
                    # Bloque reservado del sistema operativo (SO)
                    brush = QBrush(QColor(30, 70, 160))
                elif b.free:
                    brush = QBrush(QColor(200, 200, 200))
                    brush.setStyle(Qt.BrushStyle.DiagCrossPattern)
                else:
                    brush = QBrush(QColor(0, 160, 80))
                
                painter.fillRect(x, 0, bw, bar_h, brush)
                painter.setPen(QColor(100, 100, 100))
                painter.drawRect(x, 0, bw, bar_h)
                
                if not b.free and bw > 20:
                    painter.setPen(Qt.GlobalColor.white)
                    label = "SO" if b.process_pid == 0 else f"P{b.process_pid}"
                    painter.drawText(x, 0, bw, bar_h, Qt.AlignmentFlag.AlignCenter, label)

            # Draw Addressing / Paging Grid
            painter.setPen(QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine))
            page_size = 32 # 32MB grid
            num_pages = self.total // page_size
            
            for i in range(num_pages + 1):
                mb = i * page_size
                x = int(mb * scale)
                painter.drawLine(x, 0, x, h)
                painter.setPen(QColor(0, 0, 0))
                # Draw text only if it fits
                if i <= num_pages:
                    painter.drawText(x + 2, h - 2, f"{mb}")
                painter.setPen(QPen(QColor(0, 0, 0, 100), 1, Qt.PenStyle.DashLine))

    def mouseMoveEvent(self, event: QMouseEvent):
        x = event.pos().x()
        w = self.width()
        if self.total > 0 and w > 0:
            mb_pos = (x / w) * self.total
            found = None
            for b in self.blocks:
                if b.start <= mb_pos < b.end:
                    found = b
                    break
            
            if found:
                if found.process_pid == 0:
                    status = "Reservado Sistema"
                else:
                    status = "Libre" if found.free else f"Proceso PID {found.process_pid}"
                self.setToolTip(f"Dirección: {int(mb_pos)} MB\nBloque: {found.start}-{found.end} MB\nEstado: {status}")
            else:
                self.setToolTip(f"Dirección: {int(mb_pos)} MB")
