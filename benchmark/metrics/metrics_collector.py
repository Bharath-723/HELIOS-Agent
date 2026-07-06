import json
import csv
from pathlib import Path
from benchmark.metrics.resource_monitor import ResourceMonitor
from benchmark.metrics.latency_profiler import LatencyProfiler
from benchmark.metrics.routing_statistics import RoutingStatistics
from benchmark.metrics.execution_statistics import ExecutionStatistics

class MetricsCollector:
    def __init__(self, output_dir: str = "benchmark/metrics"):
        self.output_dir = Path(__file__).parent.parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.resource_monitor = ResourceMonitor()
        self.latency_profiler = LatencyProfiler()
        self.routing_stats = RoutingStatistics()
        self.exec_stats = ExecutionStatistics()
        self.metrics_log = []

    def record_metric(self, prompt_id: str, observed: dict, expected: dict, duration_ms: float):
        resources = self.resource_monitor.get_metrics()
        
        obs_route = observed["route"]
        obs_model = observed["model"]
        confidence = observed.get("confidence", 1.0)
        
        self.routing_stats.log_decision(obs_route, obs_model, confidence)
        self.exec_stats.log_execution(obs_route == expected["route"])
        
        entry = {
            "prompt_id": prompt_id,
            "execution_time_ms": duration_ms,
            "resources": resources,
            "observed_route": obs_route,
            "observed_model": obs_model,
            "expected_route": expected["route"],
            "expected_intent": expected["intent"]
        }
        self.metrics_log.append(entry)

    def save_metrics(self):
        # Save metrics.json
        with open(self.output_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(self.metrics_log, f, indent=2)
        
        # Save routing_statistics.json
        with open(self.output_dir / "routing_statistics.json", "w", encoding="utf-8") as f:
            json.dump(self.routing_stats.get_summary(), f, indent=2)
            
        # Save execution_statistics.json
        with open(self.output_dir / "execution_statistics.json", "w", encoding="utf-8") as f:
            json.dump(self.exec_stats.get_summary(), f, indent=2)
            
        # Save metrics.csv
        if self.metrics_log:
            csv_path = self.output_dir / "metrics.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["prompt_id", "execution_time_ms", "observed_route", "observed_model", "expected_route", "expected_intent"])
                writer.writeheader()
                for row in self.metrics_log:
                    writer.writerow({
                        "prompt_id": row["prompt_id"],
                        "execution_time_ms": row["execution_time_ms"],
                        "observed_route": row["observed_route"],
                        "observed_model": row["observed_model"],
                        "expected_route": row["expected_route"],
                        "expected_intent": row["expected_intent"]
                    })
