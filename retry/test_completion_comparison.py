import unittest

from retry.completion_comparison import compare_pairs, selection_key


def endpoint(done, lap=10000, progress=.5, damage=0):
    return dict(completed=done, lap_ms=lap if done else None,
                progress=progress, unique_tiles=round(100 * progress), damage=damage)


class CompletionComparisonTests(unittest.TestCase):
    def test_completion_loss_prevents_promotion_despite_speed_and_progress(self):
        result = compare_pairs([("a", endpoint(True), endpoint(False, progress=.99)),
                                ("b", endpoint(True), endpoint(True, lap=5000))])
        self.assertFalse(result["promising"])
        self.assertFalse(result["transfer_keep"])
        self.assertEqual(result["categories"]["lost_completion"], ["a"])

    def test_small_gain_survives_damage_and_mixed_transfer_closes(self):
        tiny = compare_pairs([("a", endpoint(True), endpoint(True, lap=9999, damage=4))])
        clean = compare_pairs([("a", endpoint(True), endpoint(True, lap=9999, damage=0))])
        self.assertTrue(tiny["promising"])
        self.assertTrue(tiny["transfer_keep"])
        self.assertEqual(selection_key("c", tiny), selection_key("c", clean))
        mixed = compare_pairs([("a", endpoint(True), endpoint(True, lap=9900)),
                               ("b", endpoint(False), endpoint(False, progress=.49))])
        self.assertTrue(mixed["promising"])
        self.assertFalse(mixed["transfer_keep"])


if __name__ == "__main__":
    unittest.main()
