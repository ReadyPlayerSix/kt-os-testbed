# Copyright (c) 2025 isekAI
# SPDX-License-Identifier: Apache-2.0

import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional, Dict

from visualization.native_display_v2 import KTVisualizationWindow
from visualization.data_handler import KTDataHandler
from tests.performance.kt_test_harness import KTTestHarness

class KTCoordinator:
    """Coordinates K(t) Framework testing and visualization"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self._setup_logging()
        
        # Initialize components
        self.data_handler = KTDataHandler(self.base_path / "data")
        self.test_harness = KTTestHarness(self.base_path / "test_data")
        self.visualization: Optional[KTVisualizationWindow] = None
        
        self.logger.info("K(t) Framework coordinator initialized")

    def _setup_logging(self):
        """Configure logging"""
        log_dir = self.base_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"kt_coordinator_{datetime.now():%Y%m%d}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def start_visualization(self):
        """Start the visualization component"""
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication(sys.argv)
            
            self.visualization = KTVisualizationWindow()
            self.visualization.data_handler = self.data_handler  # Use shared data handler
            self.visualization.show()
            
            return app.exec()
            
        except Exception as e:
            self.logger.error(f"Error starting visualization: {e}")
            raise

    def run_test_scenario(self, scenario: str, visualize: bool = True):
        """Run a test scenario with optional visualization"""
        try:
            # Start visualization if requested
            if visualize and not self.visualization:
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance() or QApplication(sys.argv)
                self.visualization = KTVisualizationWindow()
                self.visualization.show()
            
            # Run test scenario
            self.logger.info(f"Starting test scenario: {scenario}")
            metrics = self.test_harness.run_test_scenario(scenario)
            
            # Update visualization if active
            if self.visualization:
                for metric in metrics:
                    self.data_handler.add_metrics(metric)
                    if hasattr(self.visualization, 'update_metrics'):
                        self.visualization.update_metrics()
            
            # Save results
            self._save_test_results(scenario, metrics)
            
            self.logger.info(f"Completed test scenario: {scenario}")
            
            # Keep visualization running if requested
            if visualize and self.visualization:
                return app.exec()
                
        except Exception as e:
            self.logger.error(f"Error in test scenario {scenario}: {e}")
            raise

    def run_all_tests(self, visualize: bool = True):
        """Run all test scenarios"""
        for scenario in self.test_harness.test_scenarios:
            self.run_test_scenario(scenario, visualize)

    def _save_test_results(self, scenario: str, metrics: Dict):
        """Save test results to both test and visualization data"""
        # Save to test harness format
        self.test_harness._save_scenario_results(scenario, metrics)
        
        # Save to visualization format
        self.data_handler.add_metrics({
            "scenario": scenario,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })

def main():
    """Run the K(t) Framework coordinator"""
    coordinator = KTCoordinator()
    
    # Example usage
    try:
        # Run with visualization
        coordinator.run_all_tests(visualize=True)
        
    except KeyboardInterrupt:
        print("\nStopping K(t) Framework coordinator...")
    except Exception as e:
        print(f"Error running coordinator: {e}")

if __name__ == "__main__":
    main()