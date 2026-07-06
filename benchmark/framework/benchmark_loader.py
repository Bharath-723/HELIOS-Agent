import json
from pathlib import Path
from typing import List, Dict, Any

class BenchmarkPrompt:
    def __init__(self, data: Dict[str, Any]):
        self.id = data["id"]
        self.prompt = data["prompt"]
        self.category = data["category"]
        self.difficulty = data["difficulty"]
        self.expected_intent = data["expected_intent"]
        self.expected_parameters = data["expected_parameters"]
        self.expected_module = data["expected_module"]
        self.expected_route = data["expected_route"]
        self.expected_model_type = data["expected_model_type"]
        self.requires_internet = data["requires_internet"]
        self.privacy_level = data["privacy_level"]
        self.complexity_level = data.get("complexity_level", 0.5)

class BenchmarkLoader:
    def __init__(self, filepath: str = "benchmark/dataset/benchmark_dataset.json"):
        self.filepath = Path(filepath)

    def load(self) -> List[BenchmarkPrompt]:
        if not self.filepath.exists():
            raise FileNotFoundError(f"Dataset not found at {self.filepath}")
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [BenchmarkPrompt(p) for p in data]
