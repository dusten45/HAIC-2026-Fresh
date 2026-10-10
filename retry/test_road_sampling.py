"""Count matching must preserve short failed episodes and their endpoints."""
import unittest
import numpy as np
from retry.road_sampling import matched_road_indices


class RoadSamplingTests(unittest.TestCase):
    def test_short_source_not_discarded_or_duplicated(self):
        chosen = matched_road_indices([2, 8, 8], 12, seed=37)
        self.assertEqual([len(x) for x in chosen], [2, 5, 5])
        for indices, length in zip(chosen, [2, 8, 8]):
            self.assertEqual(len(np.unique(indices)), len(indices))
            self.assertEqual(indices[-1], length-1)
        again = matched_road_indices([2, 8, 8], 12, seed=37)
        for a, b in zip(chosen, again):
            np.testing.assert_array_equal(a, b)

    def test_impossible_total_is_rejected(self):
        for total in [2, 19]:
            with self.assertRaises(ValueError):
                matched_road_indices([2, 8, 8], total, seed=37)


if __name__ == '__main__':
    unittest.main()
