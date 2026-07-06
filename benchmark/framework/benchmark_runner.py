import time
import json
from pathlib import Path
from typing import List, Dict, Any
from agent import HELIOSAgent
from benchmark.framework.benchmark_loader import BenchmarkPrompt

class BenchmarkRunner:
    def __init__(self, agent: HELIOSAgent = None):
        self.agent = agent if agent else HELIOSAgent()

    def run_prompt(self, prompt_obj: BenchmarkPrompt) -> Dict[str, Any]:
        t0 = time.perf_counter()
        
        parsed_intent = self.agent.router.parse(prompt_obj.prompt)
        
        snapshot = {}
        snapshot_path = Path("data/diagnostics/decision_snapshot.json")
        if snapshot_path.exists():
            try:
                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        execution_time = (time.perf_counter() - t0) * 1000.0
        observed_model = snapshot.get("selected_model", "gemma3")
        observed_route = "CLOUD" if ("gemini" in observed_model or "gpt" in observed_model) else "LOCAL"
        
        return {
            "prompt_id": prompt_obj.id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_time_ms": execution_time,
            "observed_intent": parsed_intent.get("action", "general_chat"),
            "observed_parameters": parsed_intent.get("params", {}),
            "observed_route": observed_route,
            "observed_model": observed_model,
            "snapshot": snapshot
        }
