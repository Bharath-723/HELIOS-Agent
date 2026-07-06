import psutil
import os
import time

class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())

    def get_metrics(self) -> dict:
        ram = self.process.memory_info().rss / (1024 * 1024)
        cpu = psutil.cpu_percent()
        threads = len(self.process.threads())
        handles = self.process.num_handles() if hasattr(self.process, 'num_handles') else 0
        return {
            "timestamp": time.time(),
            "cpu_percent": cpu,
            "ram_mb": ram,
            "thread_count": threads,
            "handle_count": handles
        }
