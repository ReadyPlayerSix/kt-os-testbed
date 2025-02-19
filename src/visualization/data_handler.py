# Copyright (c) 2025 isekAI
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from datetime import datetime
import json
import uuid
from typing import Dict, List, Any, Tuple
import pandas as pd

class KTDataHandler:
    """Handles data persistence and export for K(t) Framework visualization"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"
        
        # Create directory structure if it doesn't exist
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize data storage
        self.current_session = {
            "session_id": uuid.uuid4().hex[:8],
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "system_info": {},
            "metrics": [],
            "patterns": []
        }

    def add_system_info(self, system_info: dict):
        """Store system information for the current session"""
        self.current_session["system_info"] = system_info
        
        # Save initial system info
        self._save_json(
            self.raw_path / f"system_info_{self.current_session['session_id']}.json",
            system_info
        )

    def add_metrics(self, metrics: dict):
        """Add metrics data point to current session"""
        metrics["timestamp"] = datetime.now().isoformat()
        self.current_session["metrics"].append(metrics)
        
        # Periodic save of raw metrics (every 60 samples)
        if len(self.current_session["metrics"]) % 60 == 0:
            self._save_raw_metrics()

    def add_pattern(self, pattern: dict):
        """Add detected pattern to current session"""
        pattern["timestamp"] = datetime.now().isoformat()
        self.current_session["patterns"].append(pattern)
        
        # Save pattern immediately
        self._save_pattern(pattern)

    def export_session(self, format: str = "json") -> str:
        """Export current session data in specified format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = self.current_session["session_id"]
        
        if format == "json":
            filepath = self.processed_path / f"session_{session_id}_{timestamp}.json"
            self._save_json(filepath, self.current_session)
            return str(filepath)
        
        elif format == "csv":
            # Export metrics as CSV
            metrics_file = self.processed_path / f"metrics_{session_id}_{timestamp}.csv"
            df = pd.DataFrame(self.current_session["metrics"])
            df.to_csv(metrics_file, index=False)
            
            # Export patterns as CSV
            patterns_file = self.processed_path / f"patterns_{session_id}_{timestamp}.csv"
            df = pd.DataFrame(self.current_session["patterns"])
            df.to_csv(patterns_file, index=False)
            
            return str(metrics_file), str(patterns_file)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def load_session(self, session_id: str) -> dict:
        """Load a previous session by ID"""
        # Look for session file in processed directory
        session_files = list(self.processed_path.glob(f"session_{session_id}_*.json"))
        
        if not session_files:
            raise FileNotFoundError(f"No session found with ID: {session_id}")
            
        # Load the most recent file if multiple exist
        latest_file = max(session_files, key=lambda x: x.stat().st_mtime)
        return self._load_json(latest_file)

    def get_baseline_patterns(self) -> dict:
        """Load and analyze baseline patterns from historical data"""
        pattern_files = list(self.raw_path.glob("pattern_analysis_*.json"))
        
        if not pattern_files:
            return {}
            
        baselines = {
            "idle": [],
            "media": [],
            "gaming": []
        }
        
        for file in pattern_files:
            data = self._load_json(file)
            if "idle" in file.name:
                baselines["idle"].append(data)
            elif "media" in file.name:
                baselines["media"].append(data)
            elif "gaming" in file.name:
                baselines["gaming"].append(data)
        
        # Calculate average patterns
        return {
            category: self._average_patterns(patterns)
            for category, patterns in baselines.items()
            if patterns
        }

    def _save_raw_metrics(self):
        """Save current batch of raw metrics"""
        metrics_file = self.raw_path / f"metrics_{self.current_session['session_id']}.json"
        self._save_json(metrics_file, self.current_session["metrics"])

    def _save_pattern(self, pattern: dict):
        """Save individual pattern data"""
        pattern_file = self.raw_path / f"pattern_{self.current_session['session_id']}.json"
        
        # Load existing patterns if file exists
        existing_patterns = []
        if pattern_file.exists():
            existing_patterns = self._load_json(pattern_file)
            
        # Append new pattern and save
        existing_patterns.append(pattern)
        self._save_json(pattern_file, existing_patterns)

    def _average_patterns(self, patterns: List[dict]) -> dict:
        """Calculate average pattern metrics"""
        if not patterns:
            return {}
            
        avg_pattern = {}
        for key in patterns[0].keys():
            if isinstance(patterns[0][key], (int, float)):
                avg_pattern[key] = sum(p[key] for p in patterns) / len(patterns)
            else:
                avg_pattern[key] = patterns[0][key]
                
        return avg_pattern

    def _save_json(self, filepath: Path, data: Any):
        """Save data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_json(self, filepath: Path) -> Any:
        """Load data from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)