import psutil
import time
from typing import Dict, List, Optional
import logging
from datetime import datetime
import json
from pathlib import Path
import uuid

class KtSystemMonitor:
    """Universal system monitor for K(t) framework optimization with session management"""
    
    def __init__(self, sampling_rate: float = 1.0):
        self.sampling_rate = sampling_rate
        self.session_id = str(uuid.uuid4())[:8]  # Generate unique session ID
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create session-specific directories
        self.session_dir = self._create_session_directory()
        self.logger = self._setup_logging()
        
        # System capabilities discovery
        self.system_info = self._discover_system()
        self._log_system_info()
        
        # Initialize pattern storage
        self.observed_patterns = []
    
    def _create_session_directory(self) -> Path:
        """Create a unique directory for this monitoring session"""
        base_dir = Path('kt_monitor_sessions')
        session_dir = base_dir / f"{self.timestamp}_{self.session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (session_dir / 'logs').mkdir(exist_ok=True)
        (session_dir / 'data').mkdir(exist_ok=True)
        
        return session_dir
    
    def _setup_logging(self) -> logging.Logger:
        """Set up session-specific logging"""
        logger = logging.getLogger(f"kt_monitor_{self.session_id}")
        logger.setLevel(logging.INFO)
        
        # Create formatters and handlers
        file_formatter = logging.Formatter('%(asctime)s - %(message)s')
        console_formatter = logging.Formatter('%(message)s')
        
        # File handler
        file_handler = logging.FileHandler(
            self.session_dir / 'logs' / f'monitor_{self.session_id}.log'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _discover_system(self) -> Dict:
        """Discover system capabilities without assumptions"""
        return {
            'cpu_count': psutil.cpu_count(logical=False),
            'thread_count': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total,
            'has_smt': psutil.cpu_count(logical=True) > psutil.cpu_count(logical=False),
            'platform': psutil.sys_info() if hasattr(psutil, 'sys_info') else None,
            'session_info': {
                'id': self.session_id,
                'timestamp': self.timestamp
            }
        }
    
    def _log_system_info(self):
        """Log system information for this session"""
        self.logger.info("Session started")
        self.logger.info(f"Session ID: {self.session_id}")
        self.logger.info(f"System discovered: {json.dumps(self.system_info, indent=2)}")
    
    def get_system_metrics(self) -> Dict:
        """Get universal system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_freq = psutil.cpu_freq(percpu=True) if hasattr(psutil, 'cpu_freq') else None
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # System load
            load = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'cpu': {
                    'overall_percent': sum(cpu_percent) / len(cpu_percent),
                    'per_cpu_percent': cpu_percent,
                    'frequencies': cpu_freq,
                    'load': load
                },
                'memory': {
                    'percent_used': memory.percent,
                    'available_bytes': memory.available,
                    'used_bytes': memory.used
                },
                'patterns': {
                    'cpu_distribution': self._analyze_cpu_pattern(cpu_percent),
                    'memory_pressure': memory.percent / 100.0
                }
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
    
    def monitor_system(self, duration: int = 60, description: str = "") -> Dict:
        """
        Monitor system and collect pattern data
        
        Args:
            duration: Monitoring duration in seconds
            description: Optional description of the monitoring session
        """
        if description:
            self.logger.info(f"Monitoring session description: {description}")
            
        print(f"\nCollecting system patterns for {duration} seconds...")
        print(f"Session ID: {self.session_id}")
        print("Press Ctrl+C to stop early\n")
        
        samples = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                metrics = self.get_system_metrics()
                samples.append(metrics)
                
                # Real-time pattern indicators
                patterns = metrics.get('patterns', {})
                distribution = patterns.get('cpu_distribution', {})
                
                print(f"\rEfficiency: {distribution.get('distribution_score', 0):>5.2f} | "
                      f"Balance: {1 - distribution.get('imbalance_score', 0):>5.2f} | "
                      f"Load: {metrics['cpu']['overall_percent']:>5.1f}%", end='')
                
                time.sleep(self.sampling_rate)
        
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            self.logger.info("Monitoring stopped by user")
        
        # Analyze patterns
        if samples:
            analysis = self._analyze_patterns(samples)
            self._save_patterns(analysis)
            self._print_analysis(analysis)
            return analysis
            
        return {}
    
    def _analyze_patterns(self, samples: List[Dict]) -> Dict:
        """Analyze collected patterns"""
        cpu_distributions = [s['patterns']['cpu_distribution']['distribution_score'] 
                           for s in samples if 'patterns' in s]
        memory_pressure = [s['patterns']['memory_pressure'] 
                          for s in samples if 'patterns' in s]
        
        analysis = {
            'session_id': self.session_id,
            'timestamp': self.timestamp,
            'duration': len(samples) * self.sampling_rate,
            'samples': len(samples),
            'patterns': {
                'cpu_efficiency': {
                    'average': sum(cpu_distributions) / len(cpu_distributions),
                    'stability': 1 - (max(cpu_distributions) - min(cpu_distributions))
                },
                'memory_patterns': {
                    'average_pressure': sum(memory_pressure) / len(memory_pressure),
                    'pressure_stability': 1 - (max(memory_pressure) - min(memory_pressure))
                }
            }
        }
        
        # Save raw samples for detailed analysis
        self._save_raw_samples(samples)
        
        return analysis
    
    def _save_raw_samples(self, samples: List[Dict]):
        """Save raw sample data for detailed analysis"""
        samples_file = self.session_dir / 'data' / f'raw_samples_{self.session_id}.json'
        with open(samples_file, 'w') as f:
            json.dump(samples, f, indent=2)
    
    def _save_patterns(self, analysis: Dict):
        """Save pattern analysis"""
        analysis_file = self.session_dir / 'data' / f'pattern_analysis_{self.session_id}.json'
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
    
    def _print_analysis(self, analysis: Dict):
        """Print user-friendly analysis"""
        patterns = analysis.get('patterns', {})
        cpu_patterns = patterns.get('cpu_efficiency', {})
        memory_patterns = patterns.get('memory_patterns', {})
        
        print("\n\nSystem Pattern Analysis:")
        print(f"Session ID: {analysis.get('session_id')}")
        print(f"Duration: {analysis.get('duration', 0):.1f} seconds")
        print(f"Samples: {analysis.get('samples', 0)}")
        
        print("\nCPU Patterns:")
        print(f"Efficiency Score: {cpu_patterns.get('average', 0):.2f}")
        print(f"Stability Score: {cpu_patterns.get('stability', 0):.2f}")
        
        print("\nMemory Patterns:")
        print(f"Pressure Level: {memory_patterns.get('average_pressure', 0):.2f}")
        print(f"Stability: {memory_patterns.get('pressure_stability', 0):.2f}")
        
        print(f"\nDetailed logs and data saved in: {self.session_dir}")

def main():
    """Run a monitoring session"""
    monitor = KtSystemMonitor(sampling_rate=1.0)
    monitor.monitor_system(
        duration=30,
        description="General system monitoring with media playback and browser"
    )

if __name__ == "__main__":
    main()