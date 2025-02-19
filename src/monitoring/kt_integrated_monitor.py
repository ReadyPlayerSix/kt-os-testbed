import psutil
import time
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import json
from pathlib import Path
import numpy as np
from dataclasses import dataclass

@dataclass
class KTParameters:
    """Parameters from the K(t) framework"""
    Lc: float = 8.0  # Critical cognitive threshold
    Lc_uncertainty: float = 0.3
    efficiency_coefficient: float = 0.80
    efficiency_uncertainty: float = 0.05
    sync_cost: float = 0.22

class KTIntegratedMonitor:
    """System monitor with integrated K(t) framework optimization"""
    
    def __init__(self, sampling_rate: float = 1.0, log_dir: str = "logs"):
        self.sampling_rate = sampling_rate
        self.kt_params = KTParameters()
        self.logger = logging.getLogger(__name__)
        
        # System discovery
        self.system_info = self._discover_system()
        
        # Set up logging
        self._setup_logging(log_dir)
        
        # Load baseline patterns
        self.baseline_patterns = self._load_baseline_patterns()
        
        # Initialize metrics store
        self.current_session = {
            'metrics': [],
            'patterns': [],
            'optimizations': []
        }
    
    def _discover_system(self) -> Dict:
        """Discover system capabilities"""
        return {
            'cpu_count': psutil.cpu_count(logical=False),
            'thread_count': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total,
            'has_smt': psutil.cpu_count(logical=True) > psutil.cpu_count(logical=False)
        }
    
    def _setup_logging(self, log_dir: str):
        """Set up logging with integrated K(t) metrics"""
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"kt_monitor_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger.info(f"System discovered: {json.dumps(self.system_info, indent=2)}")
    
    def _load_baseline_patterns(self) -> Dict:
        """Load baseline pattern data"""
        try:
            patterns = {
                'idle': {'efficiency': 0.016, 'stability': 0.864, 'memory': 0.213},
                'media': {'efficiency': 0.025, 'stability': 0.938, 'memory': 0.254},
                'light_gaming': {'efficiency': 0.078, 'stability': 0.719, 'memory': 0.272},
                'med_gaming': {'efficiency': 0.449, 'stability': 0.365, 'memory': 0.287}
            }
            return patterns
        except Exception as e:
            self.logger.error(f"Error loading baseline patterns: {str(e)}")
            return {}
    
    def _calculate_cognitive_load(self, metrics: Dict) -> float:
        """Calculate cognitive load using K(t) framework"""
        cpu_load = metrics['cpu']['overall_percent'] / 100.0
        memory_pressure = metrics['memory']['percent_used'] / 100.0
        
        # Base load calculation
        base_load = (cpu_load * 0.7 + memory_pressure * 0.3) * self.kt_params.Lc
        
        # Enhanced sync cost with better scaling
        sync_cost = self.kt_params.sync_cost * np.log2(cpu_load * 100 + 1)
        
        # Improved complexity scaling
        complexity_factor = 1 + np.sqrt(memory_pressure) * 0.025
        
        # Apply soft dampening
        load = (base_load + sync_cost) * complexity_factor
        dampening = max(0.1, 1 / (1 + np.exp((load - self.kt_params.Lc * 1.5) / 4)))
        
        return max(0.001, load * dampening)
    
    def _calculate_efficiency(self, metrics: Dict, cognitive_load: float) -> float:
        """Calculate system efficiency using K(t) framework"""
        cpu_efficiency = 1 - (metrics['cpu']['overall_percent'] / 100.0)
        memory_efficiency = 1 - (metrics['memory']['percent_used'] / 100.0)
        
        # K(t) framework efficiency calculation
        kt_efficiency = 1 / (1 + np.exp((cognitive_load - self.kt_params.Lc) / 
                                      self.kt_params.efficiency_coefficient))
        
        # Combined efficiency score
        return (cpu_efficiency * 0.4 + memory_efficiency * 0.3 + kt_efficiency * 0.3)
    
    def _detect_workload_type(self, metrics: Dict) -> Tuple[str, float]:
        """Detect current workload type based on patterns"""
        current_efficiency = metrics['patterns']['efficiency']
        
        # Calculate distance to each baseline pattern
        distances = {}
        for workload, pattern in self.baseline_patterns.items():
            distance = abs(pattern['efficiency'] - current_efficiency)
            distances[workload] = distance
        
        # Find closest match
        best_match = min(distances.items(), key=lambda x: x[1])
        return best_match[0], 1.0 - (best_match[1] / max(distances.values()))
    
    def get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics with K(t) framework integration"""
        try:
            # Get base metrics
            cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            memory = psutil.virtual_memory()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'overall_percent': sum(cpu_percent) / len(cpu_percent),
                    'per_cpu_percent': cpu_percent
                },
                'memory': {
                    'percent_used': memory.percent,
                    'available_bytes': memory.available,
                    'used_bytes': memory.used
                }
            }
            
            # Calculate K(t) framework metrics
            cognitive_load = self._calculate_cognitive_load(metrics)
            efficiency = self._calculate_efficiency(metrics, cognitive_load)
            
            # Add pattern analysis
            metrics['patterns'] = {
                'cognitive_load': cognitive_load,
                'efficiency': efficiency,
                'cpu_distribution': self._analyze_cpu_pattern(cpu_percent),
                'memory_pressure': memory.percent / 100.0
            }
            
            # Detect workload type
            workload_type, confidence = self._detect_workload_type(metrics)
            metrics['workload'] = {
                'type': workload_type,
                'confidence': confidence
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting metrics: {str(e)}")
            return {}
    
    def _analyze_cpu_pattern(self, cpu_percents: List[float]) -> Dict:
        """Analyze CPU usage patterns"""
        if not cpu_percents:
            return {}
            
        sorted_usage = sorted(cpu_percents)
        return {
            'distribution_score': sum(sorted_usage) / (len(sorted_usage) * 100),
            'imbalance_score': (max(sorted_usage) - min(sorted_usage)) / 100 if sorted_usage else 0,
            'active_cores': sum(1 for x in cpu_percents if x > 10) / len(cpu_percents)
        }
    
    def monitor_system(self, duration: int = 60) -> Dict:
        """Monitor system with K(t) framework integration"""
        print(f"\nCollecting system patterns for {duration} seconds...")
        print("Press Ctrl+C to stop early\n")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                metrics = self.get_system_metrics()
                self.current_session['metrics'].append(metrics)
                
                # Real-time display
                patterns = metrics['patterns']
                workload = metrics['workload']
                
                print(f"\rWorkload: {workload['type']:>12} ({workload['confidence']:>4.2f}) | "
                      f"Efficiency: {patterns['efficiency']:>5.2f} | "
                      f"Load: {patterns['cognitive_load']:>5.2f}", end='')
                
                time.sleep(self.sampling_rate)
        
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
        
        # Analyze session
        if self.current_session['metrics']:
            analysis = self._analyze_session()
            self._save_session(analysis)
            self._print_analysis(analysis)
            return analysis
            
        return {}
    
    def _analyze_session(self) -> Dict:
        """Analyze monitoring session"""
        metrics = self.current_session['metrics']
        
        return {
            'duration': len(metrics) * self.sampling_rate,
            'samples': len(metrics),
            'patterns': {
                'efficiency': {
                    'average': np.mean([m['patterns']['efficiency'] for m in metrics]),
                    'stability': 1 - np.std([m['patterns']['efficiency'] for m in metrics])
                },
                'cognitive_load': {
                    'average': np.mean([m['patterns']['cognitive_load'] for m in metrics]),
                    'stability': 1 - np.std([m['patterns']['cognitive_load'] for m in metrics])
                },
                'workload_distribution': self._analyze_workload_distribution()
            }
        }
    
    def _analyze_workload_distribution(self) -> Dict:
        """Analyze workload type distribution"""
        workloads = [m['workload']['type'] for m in self.current_session['metrics']]
        total = len(workloads)
        
        distribution = {}
        for workload in set(workloads):
            count = workloads.count(workload)
            distribution[workload] = count / total
        
        return distribution
    
    def _save_session(self, analysis: Dict):
        """Save session analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = Path('data')
        save_path.mkdir(exist_ok=True)
        
        with open(save_path / f'kt_session_{timestamp}.json', 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'system_info': self.system_info,
                'analysis': analysis
            }, f, indent=2)
    
    def _print_analysis(self, analysis: Dict):
        """Print user-friendly analysis"""
        patterns = analysis.get('patterns', {})
        efficiency = patterns.get('efficiency', {})
        cognitive_load = patterns.get('cognitive_load', {})
        workload_dist = patterns.get('workload_distribution', {})
        
        print("\n\nSession Analysis:")
        print(f"Duration: {analysis.get('duration', 0):.1f} seconds")
        print(f"Samples: {analysis.get('samples', 0)}")
        
        print("\nEfficiency:")
        print(f"Average: {efficiency.get('average', 0):.3f}")
        print(f"Stability: {efficiency.get('stability', 0):.3f}")
        
        print("\nCognitive Load:")
        print(f"Average: {cognitive_load.get('average', 0):.3f}")
        print(f"Stability: {cognitive_load.get('stability', 0):.3f}")
        
        print("\nWorkload Distribution:")
        for workload, percentage in workload_dist.items():
            print(f"{workload:>12}: {percentage:.1%}")

def main():
    """Run an integrated monitoring session"""
    monitor = KTIntegratedMonitor(sampling_rate=1.0)
    monitor.monitor_system(duration=30)

if __name__ == "__main__":
    main()