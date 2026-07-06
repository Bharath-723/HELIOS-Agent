import time

class LatencyProfiler:
    def __init__(self):
        self.stages = {}

    def start_stage(self, name: str):
        self.stages[name] = time.perf_counter()

    def end_stage(self, name: str) -> float:
        if name in self.stages:
            duration = (time.perf_counter() - self.stages[name]) * 1000.0
            return duration
        return 0.0
