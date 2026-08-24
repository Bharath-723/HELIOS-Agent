"""
HELIOS v2 - Strategy Ranker
Sorts alternative strategies by utility score, using a strict, deterministic tie-breaker hierarchy for absolute reproducibility.
"""
from typing import List
from functools import cmp_to_key
from core.reasoning.reasoning_models import PlanningStrategy

class StrategyRanker:
    def _compare_strategies(self, s1: PlanningStrategy, s2: PlanningStrategy) -> int:
        u1 = s1.evaluation_metrics.utility_score
        u2 = s2.evaluation_metrics.utility_score

        # Higher utility is better
        if u1 != u2:
            return 1 if u1 > u2 else -1

        # Tie-breaker 1: Lowest cost
        c1 = s1.evaluation_metrics.cost
        c2 = s2.evaluation_metrics.cost
        if c1 != c2:
            return 1 if c1 < c2 else -1

        # Tie-breaker 2: Lowest latency
        lat1 = s1.evaluation_metrics.latency
        lat2 = s2.evaluation_metrics.latency
        if lat1 != lat2:
            return 1 if lat1 < lat2 else -1

        # Tie-breaker 3: Lowest failure probability (risk)
        r1 = s1.evaluation_metrics.failure_probability
        r2 = s2.evaluation_metrics.failure_probability
        if r1 != r2:
            return 1 if r1 < r2 else -1

        # Tie-breaker 4: Alphabetical by strategy name
        if s1.name != s2.name:
            return 1 if s1.name < s2.name else -1

        return 0

    def rank(self, strategies: List[PlanningStrategy]) -> List[PlanningStrategy]:
        """
        Sorts strategies in descending order of preference.
        """
        # Python cmp_to_key: returning positive means s1 > s2, i.e. s1 comes first (descending).
        # We negate the comparison value because standard sort sorts ascending.
        def custom_cmp(s1, s2):
            val = self._compare_strategies(s1, s2)
            # return negative if s1 should come before s2 (meaning s1 is better)
            return -val

        return sorted(strategies, key=cmp_to_key(custom_cmp))
