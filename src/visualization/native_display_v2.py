# Copyright (c) 2025 isekAI
# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path
from datetime import datetime
import json
import math
import psutil
import uuid
from typing import Dict, List, Any, Tuple
import pandas as pd

try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QTabWidget, QPushButton, QLabel, QHBoxLayout, QMenuBar,
                                QMenu, QFileDialog, QMessageBox)
    from PySide6.QtCore import Qt, QTimer, Slot
    from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
except ImportError:
    print("Error: PySide6 packages not found. Please ensure PySide6 is installed.")
    sys.exit(1)

from data_handler import KTDataHandler

class KTVisualizationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("K(t) Framework Monitor")
        self.resize(1200, 800)
        
        # Initialize data handler
        self.data_handler = KTDataHandler()
        
        # Initialize data storage
        self.cpu_data = []
        self.memory_data = []
        self.efficiency_data = []
        self.max_data_points = 60
        
        # Discover system capabilities
        self.system_info = self.discover_system()
        self.data_handler.add_system_info(self.system_info)
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        
        # Initialize baseline based on historical data
        self.initialize_baselines()
        
        # Setup charts
        self.setup_performance_chart()
        self.setup_efficiency_chart()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(1000)

    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        export_json = file_menu.addAction("Export Session (JSON)")
        export_json.triggered.connect(self.export_session_json)
        
        export_csv = file_menu.addAction("Export Session (CSV)")
        export_csv.triggered.connect(self.export_session_csv)
        
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Analysis menu
        analysis_menu = menubar.addMenu("Analysis")
        
        load_session = analysis_menu.addAction("Load Previous Session")
        load_session.triggered.connect(self.load_previous_session)
        
        view_baselines = analysis_menu.addAction("View Baseline Patterns")
        view_baselines.triggered.connect(self.view_baselines)

    @Slot()
    def export_session_json(self):
        try:
            filepath = self.data_handler.export_session(format="json")
            QMessageBox.information(self, "Export Successful", 
                                  f"Session exported to:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    @Slot()
    def export_session_csv(self):
        try:
            metrics_file, patterns_file = self.data_handler.export_session(format="csv")
            QMessageBox.information(self, "Export Successful", 
                                  f"Metrics exported to:\n{metrics_file}\n\n"
                                  f"Patterns exported to:\n{patterns_file}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    @Slot()
    def load_previous_session(self):
        session_id, ok = QFileDialog.getOpenFileName(
            self, "Select Session File", 
            str(self.data_handler.processed_path),
            "JSON files (*.json)")
            
        if ok:
            try:
                session_data = self.data_handler.load_session(
                    Path(session_id).stem.split('_')[1])
                self.load_session_data(session_data)
                QMessageBox.information(self, "Load Successful", 
                                      "Session data loaded successfully")
            except Exception as e:
                QMessageBox.warning(self, "Load Failed", str(e))

    def load_session_data(self, session_data: Dict):
        # Clear current data
        self.cpu_data.clear()
        self.memory_data.clear()
        self.efficiency_data.clear()
        
        # Load metrics
        for metric in session_data["metrics"]:
            self.cpu_data.append((len(self.cpu_data), metric["cpu_percent"]))
            self.memory_data.append((len(self.memory_data), metric["memory_percent"]))
            self.efficiency_data.append((len(self.efficiency_data), metric["efficiency"]))
            
        # Update charts
        self.update_charts()

    def update_charts(self):
        # Update performance series
        self.cpu_series.clear()
        self.memory_series.clear()
        for time, value in self.cpu_data:
            self.cpu_series.append(time, value)
        for time, value in self.memory_data:
            self.memory_series.append(time, value)
        
        # Update efficiency series
        self.efficiency_series.clear()
        for time, value in self.efficiency_data:
            self.efficiency_series.append(time, value)

    @Slot()
    def view_baselines(self):
        baselines = self.data_handler.get_baseline_patterns()
        if not baselines:
            QMessageBox.information(self, "Baselines", "No baseline patterns found")
            return
            
        message = "Baseline Patterns:\n\n"
        for category, pattern in baselines.items():
            message += f"{category.title()}:\n"
            message += f"- Efficiency: {pattern.get('efficiency', 0):.3f}\n"
            message += f"- Stability: {pattern.get('stability', 0):.3f}\n\n"
            
        QMessageBox.information(self, "Baseline Patterns", message)

    def calculate_efficiency(self, cpu_percent: float, active_cores: int) -> float:
        # Enhanced K(t) framework efficiency calculation
        base_load = cpu_percent / 100.0
        complexity_factor = 1 + math.sqrt(active_cores) * 0.025
        
        # Calculate core distribution factor
        core_ratio = active_cores / self.system_info['thread_count']
        distribution_factor = 1 - abs(0.5 - core_ratio)  # Optimal at 50% core usage
        
        efficiency = base_load * complexity_factor * distribution_factor
        
        # Apply soft dampening
        dampening = max(0.1, 1 / (1 + math.exp((efficiency - 0.8) / 4)))
        return max(0.001, efficiency * dampening)

    @Slot()
    def update_metrics(self):
        # Get current metrics
        cpu_percent = psutil.cpu_percent()
        cpu_per_core = psutil.cpu_percent(percpu=True)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Calculate K(t) metrics
        active_cores = sum(1 for x in cpu_per_core if x > 10)
        efficiency = self.calculate_efficiency(cpu_percent, active_cores)
        
        # Store metrics
        metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "active_cores": active_cores,
            "efficiency": efficiency,
            "cpu_per_core": cpu_per_core
        }
        self.data_handler.add_metrics(metrics)
        
        # Update pattern detection
        if len(self.efficiency_data) >= 10:  # Analyze patterns every 10 seconds
            pattern = self.detect_pattern(efficiency)
            self.data_handler.add_pattern(pattern)
        
        # Update UI data
        self.update_ui_data(metrics)

    def detect_pattern(self, current_efficiency: float) -> Dict:
        """Detect system behavior pattern"""
        recent_efficiencies = [e[1] for e in self.efficiency_data[-10:]]
        avg_efficiency = sum(recent_efficiencies) / len(recent_efficiencies)
        stability = 1 - (max(recent_efficiencies) - min(recent_efficiencies))
        
        pattern = {
            "type": self.classify_pattern(avg_efficiency),
            "efficiency": avg_efficiency,
            "stability": stability,
            "duration": len(recent_efficiencies)
        }
        
        return pattern

    def classify_pattern(self, efficiency: float) -> str:
        """Classify system behavior pattern"""
        if efficiency < self.baseline_idle * 1.5:
            return "idle"
        elif efficiency < self.baseline_load * 0.5:
            return "light_load"
        elif efficiency < self.baseline_load * 0.8:
            return "medium_load"
        else:
            return "heavy_load"

    def update_ui_data(self, metrics: Dict):
        # Update data storage
        current_time = len(self.cpu_data)
        self.cpu_data.append((current_time, metrics["cpu_percent"]))
        self.memory_data.append((current_time, metrics["memory_percent"]))
        self.efficiency_data.append((current_time, metrics["efficiency"]))
        
        # Maintain fixed window
        if len(self.cpu_data) > self.max_data_points:
            self.cpu_data.pop(0)
            self.memory_data.pop(0)
            self.efficiency_data.pop(0)
        
        # Update charts
        self.update_charts()
        
        # Update labels
        pattern_type = self.classify_pattern(metrics["efficiency"])
        self.efficiency_label.setText(f"Efficiency Score: {metrics['efficiency']:.3f}")
        self.pattern_label.setText(f"Pattern: {pattern_type}")
        self.status_label.setText(
            f"CPU: {metrics['cpu_percent']:.1f}% | Memory: {metrics['memory_percent']:.1f}% | "
            f"Active Cores: {metrics['active_cores']}/{len(metrics['cpu_per_core'])}")

    def discover_system(self):
        """Discover system capabilities without assumptions"""
        info = {
            'cpu_count': psutil.cpu_count(logical=False),
            'thread_count': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total,
            'has_smt': psutil.cpu_count(logical=True) > psutil.cpu_count(logical=False)
        }
        
        # Get CPU frequency if available
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                info['cpu_base_freq'] = cpu_freq.current
                info['cpu_max_freq'] = cpu_freq.max
        except Exception:
            info['cpu_base_freq'] = None
            info['cpu_max_freq'] = None
            
        return info

    def initialize_baselines(self):
        """Initialize baseline patterns based on system capabilities"""
        # Calculate theoretical baselines based on discovered system
        threads_factor = self.system_info['thread_count'] / 16.0  # Normalize to common thread count
        memory_factor = self.system_info['memory_total'] / (32 * 1024 * 1024 * 1024)  # Normalize to 32GB
        
        # Adjust baselines based on system capabilities
        self.baseline_idle = 0.016 * threads_factor
        self.baseline_load = min(0.449 * threads_factor * memory_factor, 0.95)  # Cap at 95% for safety
        
        print(f"System discovered: {len(self.system_info)} characteristics")
        print(f"Initialized baselines - Idle: {self.baseline_idle:.3f}, Load: {self.baseline_load:.3f}")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Performance monitoring tab
        perf_tab = QWidget()
        perf_layout = QVBoxLayout(perf_tab)
        self.perf_chart_view = QChartView()
        perf_layout.addWidget(self.perf_chart_view)
        self.tabs.addTab(perf_tab, "Performance Monitor")
        
        # K(t) Framework tab
        kt_tab = QWidget()
        kt_layout = QVBoxLayout(kt_tab)
        self.kt_chart_view = QChartView()
        kt_layout.addWidget(self.kt_chart_view)
        
        # Add K(t) metrics panel
        metrics_panel = QWidget()
        metrics_layout = QHBoxLayout(metrics_panel)
        
        self.efficiency_label = QLabel("Efficiency Score: --")
        metrics_layout.addWidget(self.efficiency_label)
        
        self.pattern_label = QLabel("Pattern Match: --")
        metrics_layout.addWidget(self.pattern_label)
        
        kt_layout.addWidget(metrics_panel)
        self.tabs.addTab(kt_tab, "K(t) Framework Analysis")
        
        # Control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        start_button = QPushButton("Start Monitoring")
        start_button.clicked.connect(self.start_monitoring)
        control_layout.addWidget(start_button)
        
        stop_button = QPushButton("Stop Monitoring")
        stop_button.clicked.connect(self.stop_monitoring)
        control_layout.addWidget(stop_button)
        
        self.status_label = QLabel("Initializing...")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_panel)

    def setup_performance_chart(self):
        self.perf_chart = QChart()
        self.perf_chart.setTitle("System Performance")
        
        # Setup series
        self.cpu_series = QLineSeries()
        self.cpu_series.setName("CPU Usage")
        
        self.memory_series = QLineSeries()
        self.memory_series.setName("Memory Usage")
        
        # Add series to chart
        self.perf_chart.addSeries(self.cpu_series)
        self.perf_chart.addSeries(self.memory_series)
        
        # Setup axes
        self.perf_axis_x = QValueAxis()
        self.perf_axis_x.setTitleText("Time (s)")
        self.perf_axis_x.setRange(0, 60)
        
        self.perf_axis_y = QValueAxis()
        self.perf_axis_y.setTitleText("Usage %")
        self.perf_axis_y.setRange(0, 100)
        
        self.perf_chart.addAxis(self.perf_axis_x, Qt.AlignBottom)
        self.perf_chart.addAxis(self.perf_axis_y, Qt.AlignLeft)
        
        self.cpu_series.attachAxis(self.perf_axis_x)
        self.cpu_series.attachAxis(self.perf_axis_y)
        self.memory_series.attachAxis(self.perf_axis_x)
        self.memory_series.attachAxis(self.perf_axis_y)
        
        self.perf_chart_view.setChart(self.perf_chart)

    def setup_efficiency_chart(self):
        self.kt_chart = QChart()
        self.kt_chart.setTitle("K(t) Framework Efficiency")
        
        # Setup efficiency series
        self.efficiency_series = QLineSeries()
        self.efficiency_series.setName("Efficiency Score")
        
        # Add baseline indicators
        self.idle_series = QLineSeries()
        self.idle_series.setName("Idle Baseline")
        self.load_series = QLineSeries()
        self.load_series.setName("Load Baseline")
        
        # Add all series
        self.kt_chart.addSeries(self.efficiency_series)
        self.kt_chart.addSeries(self.idle_series)
        self.kt_chart.addSeries(self.load_series)
        
        # Setup axes
        self.kt_axis_x = QValueAxis()
        self.kt_axis_x.setTitleText("Time (s)")
        self.kt_axis_x.setRange(0, 60)
        
        self.kt_axis_y = QValueAxis()
        self.kt_axis_y.setTitleText("Efficiency")
        self.kt_axis_y.setRange(0, 1)
        
        self.kt_chart.addAxis(self.kt_axis_x, Qt.AlignBottom)
        self.kt_chart.addAxis(self.kt_axis_y, Qt.AlignLeft)
        
        # Attach series to axes
        self.efficiency_series.attachAxis(self.kt_axis_x)
        self.efficiency_series.attachAxis(self.kt_axis_y)
        self.idle_series.attachAxis(self.kt_axis_x)
        self.idle_series.attachAxis(self.kt_axis_y)
        self.load_series.attachAxis(self.kt_axis_x)
        self.load_series.attachAxis(self.kt_axis_y)
        
        # Add baseline lines
        for i in range(61):
            self.idle_series.append(i, self.baseline_idle)
            self.load_series.append(i, self.baseline_load)
        
        self.kt_chart_view.setChart(self.kt_chart)

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