"""Synthetic aggregation contracts; no policies, environments or protected data."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from retry.road_keep_holdout_aggregate import aggregate


class PairedSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.cases = []

    def add_pair(self, pair, a, b):
        for arm, record in [('v2', a), ('student', b)]:
            name = 'synthetic_' + str(pair) + '_' + arm
            directory = self.directory / name
            directory.mkdir()
            directory.joinpath('result.json').write_text(json.dumps(record))
            if arm == 'student' and record['status'] != 'UNEXECUTED':
                directory.joinpath('student-result.json').write_text(json.dumps(record))
            self.cases.append({'id': name, 'pair_id': pair, 'arm': arm})

    @staticmethod
    def result(status, lap=None, tiles=100, damage=0, gap=0):
        executed = status != 'UNEXECUTED'
        return {'status': status, 'completed': status == 'COMPLETE',
                'episode_count': int(executed), 'official_lap_ms': lap,
                'unique_tiles': tiles, 'total_tiles': 100, 'damage': damage,
                'charged_wrapper_actions': (2 + gap) if executed else 0,
                'successful_wrapper_steps': 2 if executed else 0,
                'cold_start_ms': 4, 'reset_including_IPC_ms': 1,
                'worker_reaping': {'close_ms': .5},
                'supervisor_peak_rss_bytes': 1000}

    @staticmethod
    def verify(_directory, case, result):
        start = {'initial': {'time': 1.02}, 'initial_observation_sha256': 'same',
                 'geometry_sha256': str(case['pair_id']), 'obstacles_sha256': 'same'}
        n = result['successful_wrapper_steps']
        return start, {'rows': n, 'frames': n + 1,
                       'native_endpoints': int(result['status'] in ('COMPLETE', 'DNF')),
                       'mask_records_verified': int(case['arm'] == 'student'), 'latency': [2] * n}

    def summarize(self):
        with patch('retry.road_keep_holdout_aggregate._verify', side_effect=self.verify):
            return aggregate(self.directory, self.cases)

    def test_paired_subsets_and_no_individual_output(self):
        r = self.result
        self.add_pair(0, r('COMPLETE', 1000, damage=.2), r('COMPLETE', 1100, damage=.4))
        self.add_pair(1, r('COMPLETE', 2000, damage=.6), r('COMPLETE', 1800, damage=.2))
        self.add_pair(2, r('DNF', tiles=20), r('COMPLETE', 500, damage=.1))
        self.add_pair(3, r('COMPLETE', 3000), r('DNF', tiles=30, damage=.2))
        self.add_pair(4, r('DNF', tiles=25, damage=.3), r('DNF', tiles=35, damage=.3))
        output = self.summarize()
        a = output['aggregate']
        self.assertEqual(a['completion_2x2'], {'both': 2, 'student_only': 1, 'v2_only': 1, 'neither': 1})
        self.assertEqual(a['common_completed_absolute_lap_ms']['v2']['mean'], 1500)
        self.assertEqual(a['common_completed_absolute_lap_ms']['student']['mean'], 1450)
        self.assertEqual(a['common_completed_lap_delta_summary_ms']['mean'], -50)
        self.assertEqual(a['common_completed_damage_warnings']['pairs'], 2)
        self.assertEqual(a['paired_native_endpoint_damage_warnings']['student_higher'], 3)
        self.assertAlmostEqual(a['both_failed_unique_progress_delta']['student_minus_v2_unique_progress']['mean'], .1)
        self.assertEqual(a['arms']['student']['closing_ms']['count'], 5)
        text = json.dumps(output)
        self.assertNotIn('paired_lap_delta_ms', text)
        for case in self.cases:
            self.assertNotIn(case['id'], text)
        # Fractions from mismatched roads must never be paired silently.
        path = self.directory / self.cases[1]['id'] / 'result.json'
        value = json.loads(path.read_text()); value['total_tiles'] = 101
        path.write_text(json.dumps(value))
        path.with_name('student-result.json').write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'aggregate withheld'):
            self.summarize()

    def test_censor_and_unexecuted_remain_unknown(self):
        r = self.result
        self.add_pair(0, r('COMPLETE', 1000), r('RESOURCE_CENSORED', tiles=40, gap=1))
        self.add_pair(1, r('DNF', tiles=20), r('UNEXECUTED'))
        output = self.summarize()
        a = output['aggregate']
        self.assertEqual(a['normal_endpoint_pairs'], 0)
        self.assertEqual(a['indeterminate_pairs'], 2)
        self.assertEqual(a['completion_2x2']['neither'], 0)
        arm = a['arms']['student']
        self.assertEqual(arm['censored_count'], 1)
        self.assertEqual(arm['unexecuted_count'], 1)
        self.assertEqual(arm['native_failure_count'], 0)
        self.assertEqual(arm['censored_observed_unique_progress']['mean'], .4)
        self.assertEqual(arm['charged_minus_successful_steps'], 1)
        self.assertEqual(arm['runs_with_incomplete_charged_actions'], 1)
        self.assertEqual(output['mechanical_receipt']['audited_runs'], 3)


if __name__ == '__main__':
    unittest.main()
