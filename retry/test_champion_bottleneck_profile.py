import unittest

from retry.champion_bottleneck_profile import profile


def row(step, before, after, tiles, speed=4, near=False, steer=0,
        centerline=3, missing=False, collision=False):
    return {"step": step, "before_time": before, "after_time": after,
            "unique_tiles": tiles, "action": [steer, 0, 0], "collision": collision,
            "policy": {"speed_estimate": speed, "hazard_near": near,
                       "centerline_points": centerline, "path_points": 5,
                       "route_target_missing": missing}}


class ChampionBottleneckProfileTests(unittest.TestCase):
    def test_real_durations_overlapping_flags_and_distinct_missing_events(self):
        result = profile([
            row(1, 1.02, 1.10, 2, near=True, steer=.30, centerline=0),
            row(2, 1.10, 1.16, 3, near=True, missing=True),
            row(3, 1.16, 1.24, 4, steer=-.4),
            row(4, 1.24, 1.28, 4),
        ])
        self.assertAlmostEqual(result["elapsed_s"], .26)
        expected = {"obstacle_avoidance": .14, "strong_steer": .16,
                    "road_recognition_missing": .08, "route_target_missing": .06,
                    "recovery": .04, "stall": 0, "progress_stall": 0}
        for flag, seconds in expected.items():
            self.assertAlmostEqual(result["flag_seconds"][flag], seconds)
            self.assertAlmostEqual(result["flag_shares"][flag], seconds / .26)
        self.assertAlmostEqual(result["union_seconds"], .26)
        self.assertAlmostEqual(result["sum_flag_seconds"], .48)
        self.assertGreater(result["sum_flag_shares"], 1)
        run = result["max_continuous_runs"]["obstacle_avoidance"]
        self.assertEqual((run["start_step"], run["end_step"]), (1, 2))
        self.assertAlmostEqual(run["duration_s"], .14)
        self.assertFalse(result["intervals"][1]["flags"]["road_recognition_missing"])
        self.assertTrue(result["intervals"][1]["flags"]["route_target_missing"])

    def test_stall_age_uses_before_time_and_recovery_starts_next_interval(self):
        result = profile([
            row(1, 1.02, 1.42, 2, speed=1),
            row(2, 1.42, 1.81, 2, speed=1),
            row(3, 1.81, 1.84, 2, speed=1),
            row(4, 1.84, 1.94, 2, speed=3),
            row(5, 1.94, 2.04, 3, speed=1),
            row(6, 2.04, 2.14, 4),
            row(7, 2.14, 2.24, 4),
            row(8, 2.24, 2.34, 4, collision=True),
            row(9, 2.34, 2.44, 4),
            row(10, 2.44, 2.54, 5),
            row(11, 2.54, 2.64, 5),
        ])
        events = [item["flags"] for item in result["intervals"]]
        self.assertFalse(events[2]["progress_stall"])
        self.assertTrue(events[3]["progress_stall"])
        self.assertFalse(events[3]["stall"])
        self.assertTrue(events[4]["stall"])
        self.assertFalse(events[5]["recovery"])
        self.assertEqual([i + 1 for i, event in enumerate(events) if event["recovery"]], [7, 11])
        self.assertTrue(result["intervals"][7]["anomaly"])
        self.assertFalse(events[8]["recovery"])
        self.assertEqual(result["recovery_count"], 2)
        self.assertAlmostEqual(result["recoveries"][0]["start_time"], 2.14)
        self.assertAlmostEqual(result["recoveries"][1]["start_time"], 2.54)
        self.assertAlmostEqual(result["flag_seconds"]["progress_stall"], .20)
        self.assertAlmostEqual(result["flag_seconds"]["stall"], .10)
        self.assertAlmostEqual(result["flag_seconds"]["recovery"], .20)


if __name__ == "__main__":
    unittest.main()
