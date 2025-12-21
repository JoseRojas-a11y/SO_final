from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import datetime

class SimulationReporter:
    def __init__(self, engine, filename="reporte_simulacion.pdf"):
        self.engine = engine
        self.filename = filename
        self.styles = getSampleStyleSheet()
        self.elements = []

    def generate(self):
        # Title
        title_style = self.styles['Title']
        self.elements.append(Paragraph("Reporte de Simulación de Sistema Operativo", title_style))
        self.elements.append(Spacer(1, 0.2 * inch))

        # Date/Time
        normal_style = self.styles['Normal']
        start_time_str = self.engine.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.elements.append(Paragraph(f"<b>Inicio de Simulación:</b> {start_time_str}", normal_style))
        self.elements.append(Paragraph(f"<b>Fin de Simulación:</b> {end_time_str}", normal_style))
        self.elements.append(Spacer(1, 0.2 * inch))

        # Configuration
        self._add_configuration_section()
        self.elements.append(Spacer(1, 0.2 * inch))

        # Global Performance
        self._add_global_performance_section()
        self.elements.append(Spacer(1, 0.2 * inch))

        # Detailed Performance
        self._add_detailed_performance_section()

        # Build PDF
        doc = SimpleDocTemplate(self.filename, pagesize=letter)
        doc.build(self.elements)
        return self.filename

    def _add_configuration_section(self):
        h2_style = self.styles['Heading2']
        self.elements.append(Paragraph("Configuración del Sistema", h2_style))
        self.elements.append(Spacer(1, 0.1 * inch))

        # Hardware Data
        hw_data = [
            ["Parámetro", "Valor"],
            ["Arquitectura", self.engine.architecture],
            ["CPUs", str(len(self.engine.cpus))],
            ["Hilos por CPU", str(self.engine.cpus[0].thread_capacity) if self.engine.cpus else "N/A"],
            ["Unidades de Memoria", str(self.engine.num_memory_units)],
            ["Capacidad por Unidad", f"{self.engine.memory_unit_capacity_mb} MB"],
            ["Almacenamiento (Swap)", self.engine.storage_type],
            ["TLB", "Habilitado" if self.engine.tlb_enabled else "Deshabilitado"],
        ]
        
        # Software Data
        sw_data = [
            ["Parámetro", "Valor"],
            ["Algoritmo Planificación", self.engine.scheduling_alg_name],
            ["Quantum", str(self.engine.quantum)],
            ["Algoritmo Asignación Memoria", self.engine.memory_units[0].alloc_alg if self.engine.memory_units else "N/A"],
            ["Algoritmo Paginación", self.engine.memory_units[0].page_alg if self.engine.memory_units else "N/A"],
            ["Tipo Tabla de Páginas", self.engine.page_table_type],
        ]

        self._create_table(hw_data, "Hardware")
        self.elements.append(Spacer(1, 0.1 * inch))
        self._create_table(sw_data, "Software")

    def _add_global_performance_section(self):
        h2_style = self.styles['Heading2']
        self.elements.append(Paragraph("Rendimiento Global", h2_style))
        self.elements.append(Spacer(1, 0.1 * inch))

        metrics = self.engine.metrics
        
        # Calculate some derived metrics
        total_ticks = self.engine.tick_count
        cpu_util = (metrics.cpu_busy_ticks / (total_ticks * len(self.engine.cpus) * self.engine.cpus[0].thread_capacity)) * 100 if total_ticks > 0 else 0
        
        perf_data = [
            ["Métrica", "Valor"],
            ["Tiempo Total Simulado (Ticks)", str(total_ticks)],
            ["Procesos Completados", str(metrics.completed_processes)],
            ["Utilización CPU Global", f"{cpu_util:.2f}%"],
            ["Throughput (Proc/Tick)", f"{metrics.throughput(total_ticks):.4f}"],
            ["Tiempo Promedio Retorno", f"{metrics.average_turnaround_time():.2f} ticks"],
            ["Tiempo Promedio Espera", f"{metrics.average_waiting_time():.2f} ticks"],
        ]

        self._create_table(perf_data, "Métricas Globales")

    def _add_detailed_performance_section(self):
        h2_style = self.styles['Heading2']
        self.elements.append(Paragraph("Rendimiento Detallado por Módulo", h2_style))
        self.elements.append(Spacer(1, 0.1 * inch))

        # CPU Details
        self.elements.append(Paragraph("<b>CPUs:</b>", self.styles['Heading3']))
        cpu_data = [["CPU ID", "Hilos", "Estado Actual"]]
        for cpu in self.engine.cpus:
            status = "Ocioso"
            if cpu.process:
                status = f"Ejecutando PID {cpu.process.pid}"
            cpu_data.append([f"CPU {cpu.id}", str(cpu.thread_capacity), status])
        self._create_table(cpu_data, "Detalle CPUs")
        self.elements.append(Spacer(1, 0.1 * inch))

        # Memory Details
        self.elements.append(Paragraph("<b>Memoria:</b>", self.styles['Heading3']))
        mem_data = [["Unidad", "Usado (MB)", "Libre (MB)", "Fragmentación", "Page Faults", "Page Hits"]]
        for unit in self.engine.memory_units:
            used = sum(b.size for b in unit.manager.blocks if not b.free)
            free = unit.total_mb - used
            frag = unit.manager.fragmentation_ratio() * 100
            faults = unit.paged_manager.page_faults
            hits = unit.paged_manager.page_hits
            mem_data.append([
                f"Unidad {unit.id}", 
                f"{used}", 
                f"{free}", 
                f"{frag:.2f}%", 
                str(faults), 
                str(hits)
            ])
        self._create_table(mem_data, "Detalle Memoria")
        
        # Storage Overview
        s = self.engine.storage_overview()
        self.elements.append(Spacer(1, 0.1 * inch))
        self.elements.append(Paragraph(f"<b>Almacenamiento ({self.engine.storage_type}):</b>", self.styles['Normal']))
        self.elements.append(Paragraph(f"Total Virtual: {s['virtual_total_mb']} MB | Usado Swap: {s['used_mb']} MB", self.styles['Normal']))
        self.elements.append(Paragraph(f"Tasa de Fallos Global: {s['fault_rate']*100:.2f}%", self.styles['Normal']))

    def _create_table(self, data, title):
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        self.elements.append(t)
