import unittest

from bc.evaluate import compare, rollout


class TestDeviation(unittest.TestCase):
    def test_first_action_and_pose_mismatch_separated(self):
        oracle = [{"action": [0, .2, 0], "pre_state": {"position": [0, 0]}}] * 3
        def row(step, position, action, teacher):
            return {"step": step, "pre_state": {"position": position, "speed": 12},
                    "action": action, "oracle_action": teacher,
                    "teacher_diagnostics": {"curvature": .01},
                    "nearest_obstacle_distance": 10., "post_state": {"speed": 12},
                    "progress": .1, "collision": False}
        student = [row(0, [0, 0], [0, .2, 0], [0, .2, 0]),
                   row(1, [1, 0], [.1, .2, 0], [0, .2, 0]),
                   row(2, [3, 0], [0, .2, 0], [.15, .2, 0])]
        result = compare(oracle, student)
        self.assertEqual(result["reference_action"]["step"], 1)
        self.assertEqual(result["reference_action"]["component"], "steer")
        self.assertEqual(result["on_state_action"]["step"], 1)
        self.assertEqual(result["position"]["step"], 2)

    def test_student_oracle_replay_is_identical_on_short_rollout(self):
        class OracleReplay:
            def __init__(self, actions):
                self.actions = actions
                self.step = 0

            def act(self, observation):
                action = self.actions[self.step]
                self.step += 1
                return action

        reference, teacher = rollout(1, 11, 8)
        samples = []
        student, learner = rollout(1, 11, 8, OracleReplay([r["action"] for r in reference]),
                                   samples=samples)
        self.assertEqual(len(samples), 8)
        self.assertEqual(samples[0][0].shape, (4, 84, 84))
        self.assertEqual(samples[0][1].tolist(), reference[0]["action"])
        self.assertEqual(learner["progress"], teacher["progress"])
        self.assertEqual(learner["finished"], teacher["finished"])
        self.assertEqual([r["action"] for r in student], [r["action"] for r in reference])
        deviations = compare(reference, student)
        self.assertIsNone(deviations["reference_action"])
        self.assertIsNone(deviations["on_state_action"])
        self.assertIsNone(deviations["position"])

    def test_reference_exhaustion_is_not_action_difference(self):
        reference = [{"action": [0, .2, 0], "pre_state": {"position": [0, 0]}}]
        student = [{"step": 1, "pre_state": {"position": [3, 0], "speed": 0},
                    "action": [.5, 0, .5], "oracle_action": [0, .2, 0],
                    "teacher_diagnostics": {"curvature": 0},
                    "nearest_obstacle_distance": 4., "post_state": {"speed": 0},
                    "progress": .1, "collision": False}]
        result = compare(reference, student)
        self.assertIsNone(result["reference_action"])
        self.assertEqual(result["on_state_action"]["step"], 1)


if __name__ == "__main__":
    unittest.main()
