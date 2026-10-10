import unittest
from retry.frozen_regression import stop_reason


def endpoint(completed, censored=False):
    return {"completed": completed, "terminal_observed": not censored, "censored": censored}


class RegressionStopTests(unittest.TestCase):
    def test_completion_loss_stops_but_common_dnf_does_not(self):
        self.assertEqual(stop_reason(endpoint(True), endpoint(False)), "FIRST_LOST_PRIOR_COMPLETION_STOP_UNLAUNCHED")
        self.assertIsNone(stop_reason(endpoint(False), endpoint(False)))
        self.assertIsNone(stop_reason(endpoint(False), endpoint(True)))
        self.assertIsNone(stop_reason(endpoint(True), endpoint(True)))

    def test_missing_endpoint_is_inconclusive_even_if_baseline_failed(self):
        self.assertEqual(stop_reason(endpoint(False), endpoint(False, True)), "MISSING_OFFICIAL_ENDPOINT")
        self.assertEqual(stop_reason(endpoint(True), endpoint(True, True)), "MISSING_OFFICIAL_ENDPOINT")


if __name__ == "__main__":
    unittest.main()
