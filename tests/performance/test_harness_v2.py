# Copyright (c) 2025 isekAI
# SPDX-License-Identifier: Apache-2.0

import psutil
import platform
import os
import time
import json
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import sys

class KTTestHarness:
    """Test harness for K(t) Framework OS-level testing"""
    
    def __init__(self, data_dir: str = "test_data"):
        self.running = True
        self.current_scenario = None
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)
        
        # Ensure absolute path for data directory
        script_dir = Path(__file__).parent.absolute()
        self.data_dir = script_dir / data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize test session
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.info(f"Initializing test session: {self.session_id}")
        self.logger.info(f"Data directory: {self.data_dir}")
        
        # Discover system capabilities
        self.system_info = self._discover_system()
        self._save_system_info()
        
        # Initialize metrics collection
        self.metrics: List[Dict] = []
        self.test_scenarios = {
            "idle": {"duration": 30, "description": "System idle baseline"},
            "cpu_intensive": {"duration": 30, "description": "High CPU usage"},
            "memory_intensive": {"duration": 30, "description": "High memory usage"},
            "mixed_load": {"duration": 30, "description": "Combined CPU and memory load"}
        }
        
        self._save_test_scenarios()

    def handle_interrupt(self, signum, frame):
        """Handle interrupt signals"""
        print("\nReceived interrupt signal. Cleaning up...")
        self.running = False
        if self.current_scenario:
            print(f"Stopping scenario: {self.current_scenario}")
        sys.exit(0)

    def _setup_logging(self):
        """Configure logging for test harness"""
        log_file = self.data_dir / f"test_harness_{datetime.now():%Y%m%d}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _save_test_scenarios(self):
        """Save test scenarios configuration"""
        scenarios_file = self.data_dir / "test_scenarios.json"
        with open(scenarios_file, 'w') as f:
            json.dump(self.test_scenarios, f, indent=2)
        self.logger.info(f"Saved test scenarios to {scenarios_file}")

    def run_test_scenario(self, scenario: str):
        """Run a specific test scenario"""
        if not self.running or scenario not in self.test_scenarios:
            return
        
        self.current_scenario = scenario
        scenario_config = self.test_scenarios[scenario]
        duration = scenario_config['duration']
        
        print(f"\nStarting scenario: {scenario}")
        print(f"Duration: {duration} seconds")
        print(f"Description: {scenario_config['description']}")
        
        start_time = time.time()
        scenario_metrics = []
        
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Start metric collection
                future_metrics = executor.submit(
                    self._collect_metrics, 
                    duration
                )
                
                # Start workload
                future_workload = executor.submit(
                    self._generate_workload,
                    scenario
                )
                
                # Show progress while waiting
                while (time.time() - start_time) < duration and self.running:
                    elapsed = int(time.time() - start_time)
                    remaining = duration - elapsed
                    print(f"\rProgress: {elapsed}/{duration} seconds remaining: {remaining}s", end='')
                    time.sleep(1)
                
                print("\nCollecting final metrics...")
                scenario_metrics = future_metrics.result()
                
        except KeyboardInterrupt:
            print("\nScenario interrupted by user")
            self.running = False
            return
        
        except Exception as e:
            self.logger.error(f"Error in test scenario {scenario}: {e}")
            print(f"\nError in scenario {scenario}: {e}")
            return
        
        finally:
            if scenario_metrics:
                self._save_scenario_results(scenario, scenario_metrics)
            self.current_scenario = None
        
        if self.running:
            print(f"\nCompleted scenario: {scenario}")

    def _collect_metrics(self, duration: int) -> List[Dict]:
        """Collect system metrics for specified duration"""
        metrics = []
        end_time = time.time() + duration
        
        while time.time() < end_time and self.running:
            try:
                metrics.append(self._get_current_metrics())
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                
        return metrics

    def _get_current_metrics(self) -> Dict:
        """Get current system metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(percpu=True),
                'freq': psutil.cpu_freq(percpu=True) if hasattr(psutil, 'cpu_freq') else None,
            },
            'memory': {
                'virtual': dict(psutil.virtual_memory()._asdict()),
                'swap': dict(psutil.swap_memory()._asdict())
            }
        }

    def _save_scenario_results(self, scenario: str, metrics: List[Dict]):
        """Save scenario metrics to file"""
        try:
            results_file = self.data_dir / f"scenario_{scenario}_{self.session_id}.json"
            results = {
                'scenario': scenario,
                'timestamp': datetime.now().isoformat(),
                'system_info': self.system_info,
                'metrics': metrics
            }
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"Saved scenario results to {results_file}")
            print(f"Results saved to: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            print(f"Error saving results: {e}")

    def _discover_system(self) -> Dict:
        """Enhanced system capability discovery"""
        info = {
            'hardware': {
                'cpu': {
                    'physical_cores': psutil.cpu_count(logical=False),
                    'logical_cores': psutil.cpu_count(logical=True),
                    'frequencies': self._get_cpu_frequencies(),
                    'cache_sizes': self._get_cache_info()
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'swap': psutil.swap_memory().total
                }
            },
            'os': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine()
            }
        }
        return info

    def _get_cpu_frequencies(self) -> Dict:
        """Get detailed CPU frequency information"""
        try:
            cpu_freq = psutil.cpu_freq(percpu=True)
            if cpu_freq:
                return {
                    'current': [getattr(freq, 'current', 0) for freq in cpu_freq],
                    'min': [getattr(freq, 'min', 0) for freq in cpu_freq],
                    'max': [getattr(freq, 'max', 0) for freq in cpu_freq]
                }
        except Exception as e:
            self.logger.warning(f"Could not get CPU frequencies: {e}")
        return {}

    def _get_cache_info(self) -> Dict:
        """Get CPU cache information"""
        cache_info = {}
        try:
            # Linux-specific cache info
            if platform.system() == 'Linux':
                cache_path = Path('/sys/devices/system/cpu/cpu0/cache')
                if cache_path.exists():
                    for level in cache_path.glob('index*'):
                        size = (level / 'size').read_text().strip()
                        type = (level / 'type').read_text().strip()
                        cache_info[f"L{level.name[-1]}_{type}"] = size
        except Exception as e:
            self.logger.warning(f"Could not get cache information: {e}")
        return cache_info

    def _save_system_info(self):
        """Save system information to file"""
        info_file = self.data_dir / f"system_info_{self.session_id}.json"
        with open(info_file, 'w') as f:
            json.dump(self.system_info, f, indent=2)
        self.logger.info(f"Saved system information to {info_file}")

def main():
    """Run a test session with all scenarios"""
    harness = KTTestHarness()
    
    print("\nK(t) Framework Test Harness")
    print("---------------------------")
    print("Press Ctrl+C at any time to stop testing\n")
    
    for scenario in harness.test_scenarios:
        if not harness.running:
            break
        harness.run_test_scenario(scenario)
    
    if harness.running:
        print("\nAll test scenarios completed")
    else:
        print("\nTesting stopped by user")

if __name__ == "__main__":
    main()