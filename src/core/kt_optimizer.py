# Copyright (c) 2025 isekAI
# SPDX-License-Identifier: Apache-2.0

import math
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    """Normalized system metrics from test harness"""
    cpu_efficiency: float    # CPU utilization efficiency (0-1)
    memory_pressure: float   # Memory pressure score (0-1)
    cores_active: float      # Percentage of cores actively used (0-1)
    stability_score: float   # System stability metric (0-1)

def calculate_optimal_batch(metrics: SystemMetrics, Lc: float = 8.0):
    """
    Calculate optimal batch size using K(t) Framework formulas
    
    Parameters:
    - metrics: Normalized system metrics from test harness
    - Lc: Critical cognitive threshold (default 8.0)
    """
    # Calculate base efficiency factor
    base_efficiency = metrics.cpu_efficiency * (1 - metrics.memory_pressure)
    
    # Enhanced complexity scaling that adapts to system capabilities
    complexity_factor = 1 + math.sqrt(metrics.cores_active) * 0.025
    
    # Calculate cognitive load threshold
    cognitive_load = base_efficiency * complexity_factor
    
    # Apply K(t) Framework dampening
    dampening = max(0.1, 1 / (1 + math.exp((cognitive_load - Lc) / 4)))
    
    # Calculate theoretical max batch size
    max_theoretical = int(Lc / (cognitive_load * dampening))
    
    # Apply stability adjustment
    stability_factor = 0.5 + (metrics.stability_score * 0.5)  # Range 0.5-1.0
    optimal_batch = int(max_theoretical * stability_factor)
    
    # Calculate efficiency score for this batch size
    efficiency = 1 / (1 + math.exp((cognitive_load - Lc) / base_efficiency))
    
    return {
        'optimal_batch_size': optimal_batch,
        'efficiency_score': efficiency,
        'load_factor': cognitive_load,
        'stability_rating': stability_factor
    }

# Example using metrics from test harness
test_metrics = SystemMetrics(
    cpu_efficiency=0.72,     # From CPU utilization patterns
    memory_pressure=0.25,    # From memory usage analysis
    cores_active=0.85,       # From core utilization tracking
    stability_score=0.93     # From pattern stability analysis
)

if __name__ == "__main__":
    results = calculate_optimal_batch(test_metrics)
    print("\nK(t) Framework Optimization Results:")
    print(f"Optimal Batch Size: {results['optimal_batch_size']}")
    print(f"Efficiency Score: {results['efficiency_score']:.3f}")
    print(f"System Load Factor: {results['load_factor']:.3f}")
    print(f"Stability Rating: {results['stability_rating']:.3f}")
