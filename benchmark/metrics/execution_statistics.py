class ExecutionStatistics:
    def __init__(self):
        self.total = 0
        self.successes = 0
        self.failures = 0

    def log_execution(self, success: bool):
        self.total += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1

    def get_summary(self) -> dict:
        rate = self.successes / self.total if self.total > 0 else 0.0
        return {
            "total_tasks": self.total,
            "success_rate": rate,
            "failure_rate": 1.0 - rate
        }
