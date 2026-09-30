import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import torch

from bc.evaluate import ACTION_THRESHOLDS, POSITION_THRESHOLD, compare, main, rollout
from bc.contracts import BASELINE_CONDITIONS
from bc.model import BCPolicy
from oracle.recording import encode, execution_fingerprint


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
                self.step = len(actions)
                self.reset_count = 0

            def reset(self, observation):
                self.step = 0
                self.reset_count += 1

            def act(self, observation):
                action = self.actions[self.step]
                self.step += 1
                return action

        reference, teacher = rollout(1, 11, 8)
        samples = []
        policy = OracleReplay([r["action"] for r in reference])
        student, learner = rollout(1, 11, 8, policy, samples=samples)
        self.assertEqual(policy.reset_count, 1)
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

    def test_prefix_advances_policy_and_separates_prediction_from_execution(self):
        reference_samples = []
        reference, _ = rollout(1, 31, 8, samples=reference_samples)
        policy = BCPolicy(history_frames=8)
        policy.reset = Mock(wraps=policy.reset)
        policy.act = Mock(wraps=policy.act)
        policy.forward = Mock(return_value=torch.zeros(1, 3))
        samples = []
        student, _ = rollout(1, 31, 8, policy, samples=samples, oracle_prefix_steps=4)
        policy.reset.assert_called_once()
        self.assertEqual(policy.act.call_count, len(student))
        self.assertEqual([row["oracle_prefix"] for row in student], [True] * 4 + [False] * 4)
        history = [reference_samples[0][0][-1]] * 7
        for index, row in enumerate(student):
            self.assertEqual(row["predicted_action"], [0., 0., 0.])
            self.assertEqual(row["action"], row["oracle_action"] if index < 4 else row["predicted_action"])
            np.testing.assert_array_equal(policy.act.call_args_list[index].args[0], samples[index][0])
            history.append(samples[index][0][-1])
            np.testing.assert_array_equal(policy.forward.call_args_list[index].args[0][0].numpy(),
                                          np.stack(history[-8:]))
            if index <= 4:
                np.testing.assert_array_equal(samples[index][0], reference_samples[index][0])
                self.assertEqual(encode(row["pre_state"]), encode(reference[index]["pre_state"]))
        result = compare(reference, student)
        self.assertEqual(result["on_state_action"]["step"], 0)
        self.assertTrue(result["on_state_action"]["oracle_prefix"])
        self.assertEqual(result["handoff"]["step"], 4)
        self.assertEqual(result["handoff"]["student_action"], student[4]["predicted_action"])
        self.assertEqual(result["handoff"]["executed_action"], student[4]["action"])
        np.testing.assert_allclose(result["handoff"]["same_state_absolute_error"],
                                   np.abs(student[4]["oracle_action"]))
        self.assertEqual(result["after_handoff"]["on_state_action"]["step"], 4)
        self.assertFalse(result["after_handoff"]["on_state_action"]["oracle_prefix"])

    def test_full_prefix_has_no_handoff_but_keeps_prediction_errors(self):
        policy = Mock()
        policy.act.return_value = np.zeros(3, dtype=np.float32)
        student, _ = rollout(1, 31, 2, policy, oracle_prefix_steps=4)
        result = compare(student, student)
        self.assertEqual(policy.act.call_count, 2)
        self.assertIsNone(result["handoff"])
        self.assertEqual(result["after_handoff"],
                         {"reference_action": None, "on_state_action": None, "position": None})
        self.assertEqual(result["on_state_action"]["step"], 0)
        self.assertIsNone(result["position"])


class TestResume(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.checkpoint = root / "best.pt"
        self.checkpoint.write_bytes(b"mock checkpoint")
        self.output = root / "evaluation"
        self.output.mkdir()
        episode = {"track_id": 1, "geometry_seed": 31, "finished": False, "progress": .2}
        self.result = {"track_id": 1, "geometry_seed": 31,
                       "reference": {**episode, "finished": True}, "student": episode,
                       "first_deviations": {}}
        self.summary = {"checkpoint": str(self.checkpoint),
                        **execution_fingerprint(("bc/evaluate.py", "bc/model.py", "bc/contracts.py",
                                                 "oracle/recording.py", "oracle/oracle_controller.py",
                                                 "env_wrapper.py", "damage.py")),
                        "checkpoint_sha256": hashlib.sha256(self.checkpoint.read_bytes()).hexdigest(),
                        "steer_checkpoint_sha256": None, "split": "val", "max_steps": 2000,
                        "frame_skip": 4, "warmup": 50,
                        "conditions": dict(BASELINE_CONDITIONS),
                        "thresholds": {"action": list(ACTION_THRESHOLDS), "position": POSITION_THRESHOLD},
                        "episode_count": 1, "road_count": 1, "finish_count": 0,
                        "reference_finish_count": 1, "results": [self.result]}
        self.summary_path = self.output / "summary.json"
        self.summary_path.write_text(json.dumps(self.summary))
        for side in ("oracle", "student"):
            (self.output / f"track1_seed31.{side}.jsonl").write_text("completed trace\n")
        self.argv = ["--checkpoint", str(self.checkpoint), "--split", "val", "--track-ids", "1",
                     "--seeds", "31", "32", "--output", str(self.output), "--resume"]

    def test_completed_pairs_skipped_and_interrupted_traces_archived(self):
        original = self.summary_path.read_bytes()
        for side in ("oracle", "student"):
            (self.output / f"track1_seed32.{side}.jsonl").write_text(f"interrupted {side}\n")
        policy = Mock()

        def fake_rollout(track_id, seed, max_steps, policy=None, trace_path=None, samples=None, oracle_prefix_steps=0):
            self.assertEqual((track_id, seed), (1, 32))
            self.assertEqual(self.summary_path.read_bytes(), original)
            assert trace_path is not None
            with trace_path.open("x") as stream:
                stream.write("new trace\n")
            return [], {"track_id": track_id, "geometry_seed": seed,
                        "finished": policy is None, "progress": .3}

        with patch("bc.model.BCPolicy.from_checkpoint", return_value=policy), \
                patch("bc.evaluate.rollout", side_effect=fake_rollout) as run:
            main(self.argv)
        self.assertEqual(run.call_count, 2)
        self.assertIs(run.call_args_list[1].kwargs["policy"], policy)
        updated = json.loads(self.summary_path.read_text())
        self.assertEqual(updated["results"][0], self.result)
        self.assertEqual(updated["episode_count"], 2)
        self.assertEqual(updated["road_count"], 2)
        self.assertEqual(updated["finish_count"], 0)
        self.assertEqual(updated["reference_finish_count"], 2)
        self.assertEqual(updated["track_ids"], [1])
        self.assertEqual(updated["seeds"], [31, 32])
        self.assertEqual(updated["oracle_prefix_steps"], 0)
        self.assertFalse(updated["diagnostic_only"])
        archives = list((self.output / "interrupted_attempts").iterdir())
        self.assertEqual(len(archives), 1)
        self.assertEqual((archives[0] / "summary.json").read_bytes(), original)
        for side in ("oracle", "student"):
            self.assertEqual((archives[0] / f"track1_seed32.{side}.jsonl").read_text(),
                             f"interrupted {side}\n")
            self.assertEqual((self.output / f"track1_seed31.{side}.jsonl").read_text(), "completed trace\n")

    def test_incompatible_resume_rejected_without_changes(self):
        variants = [{"checkpoint_sha256": "different"}, {"steer_checkpoint_sha256": "different"},
                    {"source_sha256": {"bc/model.py": "different"}},
                    {"packages": {"torch": "different"}}, {"python": "different"},
                    {"conditions": {**BASELINE_CONDITIONS, "target_speed": 13}},
                    {"split": "train"}, {"max_steps": 100}, {"frame_skip": 1}, {"warmup": 0},
                    {"thresholds": {}}, {"track_ids": [1, 2], "seeds": [31, 32]},
                    {"track_ids": [1], "seeds": [31]},
                    {"results": [self.result, self.result]},
                    {"results": [{**self.result, "track_id": 2}]}, {"collect_recovery": True},
                    {"oracle_prefix_steps": 4}]
        for changes in variants:
            with self.subTest(changes=changes):
                self.summary_path.write_text(json.dumps({**self.summary, **changes}))
                before = {p.name: p.read_bytes() for p in self.output.iterdir()}
                with patch("bc.model.BCPolicy.from_checkpoint") as load, \
                        patch("bc.evaluate.rollout") as run, self.assertRaises(SystemExit) as error:
                    main(self.argv)
                self.assertEqual(error.exception.code, 2)
                load.assert_not_called()
                run.assert_not_called()
                self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()}, before)

    def test_nonzero_prefix_cannot_resume_legacy_default_zero(self):
        before = self.summary_path.read_bytes()
        with patch("bc.model.BCPolicy.from_checkpoint") as load, \
                patch("bc.evaluate.rollout") as run, self.assertRaises(SystemExit):
            main([*self.argv, "--oracle-prefix-steps", "4"])
        load.assert_not_called()
        run.assert_not_called()
        self.assertEqual(self.summary_path.read_bytes(), before)

    def test_matching_prefix_resume_forwarded_only_to_student(self):
        self.summary_path.write_text(json.dumps({**self.summary, "oracle_prefix_steps": 4}))

        def complete(track_id, seed, max_steps, policy=None, **kwargs):
            return [], {"track_id": track_id, "geometry_seed": seed,
                        "finished": policy is None, "progress": .2}

        with patch("bc.model.BCPolicy.from_checkpoint", return_value=Mock()), \
                patch("bc.evaluate.rollout", side_effect=complete) as run:
            main([*self.argv, "--oracle-prefix-steps", "4"])
        self.assertNotIn("oracle_prefix_steps", run.call_args_list[0].kwargs)
        self.assertEqual(run.call_args_list[1].kwargs["oracle_prefix_steps"], 4)
        summary = json.loads(self.summary_path.read_text())
        self.assertEqual(summary["oracle_prefix_steps"], 4)
        self.assertTrue(summary["diagnostic_only"])

    def test_negative_prefix_and_prefix_recovery_rejected_before_loading(self):
        for arguments in (["--oracle-prefix-steps", "-1"],
                          ["--oracle-prefix-steps", "4", "--collect-recovery", "--split", "train", "--seeds", "11"]):
            with self.subTest(arguments=arguments), patch("bc.model.BCPolicy.from_checkpoint") as load, \
                    patch("bc.evaluate.rollout") as run, self.assertRaises(SystemExit):
                main([*self.argv, *arguments])
            load.assert_not_called()
            run.assert_not_called()

    def test_existing_output_refused_by_default_and_resume_recovery_refused(self):
        before = self.summary_path.read_bytes()
        for argv in (self.argv[:-1], self.argv + ["--collect-recovery"]):
            with self.subTest(argv=argv), patch("bc.evaluate.rollout") as run, \
                    self.assertRaises(SystemExit) as error:
                main(argv)
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called()
            self.assertEqual(self.summary_path.read_bytes(), before)
            self.assertFalse((self.output / "interrupted_attempts").exists())

    def test_legacy_summary_without_fingerprint_requires_new_output_and_is_preserved(self):
        legacy = {key: value for key, value in self.summary.items()
                  if key not in ("source_sha256", "packages", "python")}
        self.summary_path.write_text(json.dumps(legacy))
        before = self.summary_path.read_bytes()
        with patch("bc.evaluate.rollout") as run, patch("bc.model.BCPolicy.from_checkpoint") as load, \
                patch("sys.stderr") as stderr, self.assertRaises(SystemExit):
            main(self.argv)
        message = "".join(call.args[0] for call in stderr.write.call_args_list)
        self.assertIn("verification impossible, use a new output directory", message)
        run.assert_not_called()
        load.assert_not_called()
        self.assertEqual(self.summary_path.read_bytes(), before)

    def test_interruption_before_first_pair_leaves_resumable_empty_summary(self):
        output = Path(self.temp.name) / "first_pair"
        argv = ["--checkpoint", str(self.checkpoint), "--split", "val", "--track-ids", "1",
                "--seeds", "31", "--output", str(output)]

        def interrupt(track_id, seed, max_steps, **kwargs):
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["results"], [])
            self.assertEqual(summary["episode_count"], 0)
            self.assertTrue((output / summary["source_snapshot"]).is_dir())
            kwargs["trace_path"].write_text("interrupted first oracle\n")
            raise RuntimeError("interrupted before first pair")

        with patch("bc.model.BCPolicy.from_checkpoint", return_value=Mock()), \
                patch("bc.evaluate.rollout", side_effect=interrupt):
            with self.assertRaisesRegex(RuntimeError, "before first pair"):
                main(argv)
        initial = (output / "summary.json").read_bytes()

        def complete(track_id, seed, max_steps, policy=None, **kwargs):
            kwargs["trace_path"].write_text("new trace\n")
            return [], {"track_id": track_id, "geometry_seed": seed,
                        "finished": policy is None, "progress": .2}

        with patch("bc.model.BCPolicy.from_checkpoint", return_value=Mock()), \
                patch("bc.evaluate.rollout", side_effect=complete), \
                patch("bc.evaluate.snapshot_sources") as snapshot:
            main([*argv, "--resume"])
        snapshot.assert_not_called()
        archive = next((output / "interrupted_attempts").iterdir())
        self.assertEqual((archive / "summary.json").read_bytes(), initial)
        self.assertEqual((archive / "track1_seed31.oracle.jsonl").read_text(), "interrupted first oracle\n")
        self.assertEqual(json.loads((output / "summary.json").read_text())["episode_count"], 1)


if __name__ == "__main__":
    unittest.main()
