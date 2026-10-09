"""One fixed legal representation contrast and a matched-compute speed control."""

from retry.factorial_agent import FactorialMemoryAgent


class SeparatedMemoryRiskAgent(FactorialMemoryAgent):
    """Confirmed path beliefs and recent risk alerts have separate roles."""

    def __init__(self, speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe):
        super().__init__(speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe,
            "confirmed", "original")


class MatchedSlowdownAgent(FactorialMemoryAgent):
    """Original path and uniformly conservative speed, same estimator workload."""

    def __init__(self, speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe):
        super().__init__(speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe,
            "original", "always_safe")
