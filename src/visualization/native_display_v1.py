import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTabWidget, QPushButton, QLabel)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import psutil
from datetime import datetime
import json

class KTVisualizationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("K(t) Framework Monitor")
        self.resize(1000, 600)
        
        # Initialize data storage
        self.cpu_data = []
        self.memory_data = []
        self.max_data_points = 60  # Store 1 minute of data
        
        # Setup UI
        self.setup_ui()
        
        # Setup charts
        self.setup_charts()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(1000)  # Update every second

    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Monitoring tab
        monitoring_tab = QWidget()
        monitoring_layout = QVBoxLayout(monitoring_tab)
        self.chart_view = QChartView()
        monitoring_layout.addWidget(self.chart_view)
        
        # Add status label
        self.status_label = QLabel("Initializing...")
        monitoring_layout.addWidget(self.status_label)
        
        self.tabs.addTab(monitoring_tab, "System Monitor")
        
        # Control panel
        control_layout = QVBoxLayout()
        start_button = QPushButton("Start Monitoring")
        start_button.clicked.connect(self.start_monitoring)
        control_layout.addWidget(start_button)
        
        stop_button = QPushButton("Stop Monitoring")
        stop_button.clicked.connect(self.stop_monitoring)
        control_layout.addWidget(stop_button)
        
        layout.addLayout(control_layout)

    def setup_charts(self):
        # Create chart
        self.chart = QChart()
        self.chart.setTitle("System Metrics")
        
        # CPU series
        self.cpu_series = QLineSeries()
        self.cpu_series.setName("CPU Usage")
        
        # Memory series
        self.memory_series = QLineSeries()
        self.memory_series.setName("Memory Usage")
        
        # Add series to chart
        self.chart.addSeries(self.cpu_series)
        self.chart.addSeries(self.memory_series)
        
        # Setup axes
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Time (s)")
        self.axis_x.setRange(0, 60)
        
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Usage %")
        self.axis_y.setRange(0, 100)
        
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        
        self.cpu_series.attachAxis(self.axis_x)
        self.cpu_series.attachAxis(self.axis_y)
        self.memory_series.attachAxis(self.axis_x)
        self.memory_series.attachAxis(self.axis_y)
        
        # Set the chart on the view
        self.chart_view.setChart(self.chart)

    @Slot()
    def update_metrics(self):
        # Get current metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Update data storage
        current_time = len(self.cpu_data)
        self.cpu_data.append((current_time, cpu_percent))
        self.memory_data.append((current_time, memory_percent))
        
        # Maintain fixed window of data
        if len(self.cpu_data) > self.max_data_points:
            self.cpu_data.pop(0)
            self.memory_data.pop(0)
        
        # Update series
        self.cpu_series.clear()
        self.memory_series.clear()
        
        for time, value in self.cpu_data:
            self.cpu_series.append(time, value)
        for time, value in self.memory_data:
            self.memory_series.append(time, value)
        
        # Update status
        status_msg = f"CPU: {cpu_percent:.1f}% | Memory: {memory_percent:.1f}%"
        self.status_label.setText(status_msg)

    @Slot()
    def start_monitoring(self):
        self.update_timer.start()
        self.status_label.setText("Monitoring Started")

    @Slot()
    def stop_monitoring(self):
        self.update_timer.stop()
        self.status_label.setText("Monitoring Stopped")

def main():
    app = QApplication(sys.argv)
    window = KTVisualizationWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()