import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QPushButton, QLabel)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import json
import numpy as np
from datetime import datetime
from ..core.kt_optimizer import KTParameters
from ..monitoring.kt_integrated_monitor import KtSystemMonitor

class KTVisualizationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("K(t) Framework System Monitor")
        self.resize(1200, 800)
        
        # Initialize K(t) components
        self.kt_params = KTParameters()
        self.monitor = KtSystemMonitor()
        
        # Setup UI
        self.setup_ui()
        
        # Setup data structures
        self.cpu_series = QLineSeries()
        self.memory_series = QLineSeries()
        self.efficiency_series = QLineSeries()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(1000)  # Update every second
        
        # Load historical data
        self.load_historical_data()

    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Real-time monitoring tab
        realtime_tab = QWidget()
        realtime_layout = QHBoxLayout(realtime_tab)
        
        # CPU Chart
        cpu_chart = QChart()
        cpu_chart.setTitle("CPU Utilization")
        cpu_view = QChartView(cpu_chart)
        cpu_view.setMinimumSize(400, 300)
        realtime_layout.addWidget(cpu_view)
        
        # Memory Chart
        memory_chart = QChart()
        memory_chart.setTitle("Memory Usage")
        memory_view = QChartView(memory_chart)
        memory_view.setMinimumSize(400, 300)
        realtime_layout.addWidget(memory_view)
        
        tabs.addTab(realtime_tab, "Real-time Monitoring")
        
        # Pattern Analysis tab
        pattern_tab = QWidget()
        pattern_layout = QVBoxLayout(pattern_tab)
        
        # Efficiency Chart
        efficiency_chart = QChart()
        efficiency_chart.setTitle("K(t) Framework Efficiency")
        efficiency_view = QChartView(efficiency_chart)
        pattern_layout.addWidget(efficiency_view)
        
        tabs.addTab(pattern_tab, "Pattern Analysis")
        
        # Control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # Add controls
        start_button = QPushButton("Start Monitoring")
        start_button.clicked.connect(self.start_monitoring)
        control_layout.addWidget(start_button)
        
        stop_button = QPushButton("Stop Monitoring")
        stop_button.clicked.connect(self.stop_monitoring)
        control_layout.addWidget(stop_button)
        
        export_button = QPushButton("Export Data")
        export_button.clicked.connect(self.export_data)
        control_layout.addWidget(export_button)
        
        layout.addWidget(control_panel)
        
        # Status bar
        self.statusBar().showMessage("K(t) Framework Monitor Ready")

    def load_historical_data(self):
        try:
            with open('data/raw/pattern_analysis_idle.json', 'r') as f:
                idle_data = json.load(f)
            with open('data/raw/pattern_analysis_med_gaming.json', 'r') as f:
                load_data = json.load(f)
                
            # Process historical data for baseline comparison
            self.baseline_patterns = {
                'idle': idle_data['patterns'],
                'load': load_data['patterns']
            }
            
        except Exception as e:
            self.statusBar().showMessage(f"Warning: Could not load historical data - {str(e)}")

    @Slot()
    def update_metrics(self):
        # Get current metrics from monitor
        metrics = self.monitor.get_system_metrics()
        
        # Update charts
        self.update_cpu_chart(metrics['cpu'])
        self.update_memory_chart(metrics['memory'])
        self.update_efficiency_chart(metrics['patterns'])
        
        # Update status
        status_msg = (f"CPU: {metrics['cpu']['overall_percent']:.1f}% | "
                     f"Memory: {metrics['memory']['percent_used']:.1f}% | "
                     f"Efficiency: {metrics['patterns']['cpu_distribution']['distribution_score']:.3f}")
        self.statusBar().showMessage(status_msg)

    def update_cpu_chart(self, cpu_metrics):
        timestamp = datetime.now().timestamp()
        self.cpu_series.append(timestamp, cpu_metrics['overall_percent'])
        
        # Remove old data points to prevent memory buildup
        if self.cpu_series.count() > 100:
            self.cpu_series.remove(0)

    def update_memory_chart(self, memory_metrics):
        timestamp = datetime.now().timestamp()
        self.memory_series.append(timestamp, memory_metrics['percent_used'])
        
        if self.memory_series.count() > 100:
            self.memory_series.remove(0)

    def update_efficiency_chart(self, pattern_metrics):
        timestamp = datetime.now().timestamp()
        efficiency = pattern_metrics['cpu_distribution']['distribution_score']
        self.efficiency_series.append(timestamp, efficiency)
        
        if self.efficiency_series.count() > 100:
            self.efficiency_series.remove(0)

    @Slot()
    def start_monitoring(self):
        self.update_timer.start()
        self.statusBar().showMessage("Monitoring Started")

    @Slot()
    def stop_monitoring(self):
        self.update_timer.stop()
        self.statusBar().showMessage("Monitoring Stopped")

    @Slot()
    def export_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/raw/kt_monitor_export_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'cpu_data': self.export_series_data(self.cpu_series),
                    'memory_data': self.export_series_data(self.memory_series),
                    'efficiency_data': self.export_series_data(self.efficiency_series)
                }, f, indent=2)
            self.statusBar().showMessage(f"Data exported to {filename}")
        except Exception as e:
            self.statusBar().showMessage(f"Export failed: {str(e)}")

    def export_series_data(self, series):
        return [{'timestamp': point.x(), 'value': point.y()} 
                for point in series.points()]

def main():
    app = QApplication(sys.argv)
    window = KTVisualizationWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()