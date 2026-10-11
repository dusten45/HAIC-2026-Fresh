"""Historical-reuse gate and one-candidate outcome retention, with no physics."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from retry.global_cap_probe import run


class HistoricalCandidateTests(unittest.TestCase):
    def prepare(self, root, cached=True):
        plan={'cases':[{'id':'candidate','coefficient':7}], 'global_cap':40,
              'max_actions':2000,'stage_budgets':{'candidate':2000},
              'B_operating_cap':646000,'research_remaining_before':3427,
              'source_sha256':{},'reference_sha256':{}}
        path=root/'plan.json'; path.write_text(json.dumps(plan))
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        (root/'plan.sha256').write_text(sha)
        (root/'preflight.json').write_text(json.dumps({'status':'PASS','plan_sha256':sha,
            'historical_baseline_comparable':True,'cached_baseline_reproduction_pass':cached}))
        (root/'candidate').mkdir()
        return path

    def test_one_candidate_native_dnf_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); path=self.prepare(root)
            outcome={'status':'DNF','completed':False,'official_lap_ms':None,
                     'unique_tiles':139,'damage':.8,'charged_wrapper_actions':400}
            with patch('retry.global_cap_probe.native.available'), patch(
                    'retry.global_cap_probe.execute',return_value=(outcome,False)) as execute:
                result, stopped=run(path)
            self.assertEqual(execute.call_count,1)
            self.assertEqual(result['status'],'DNF')
            self.assertEqual(result['unique_tiles'],139)
            self.assertIsNone(result['official_lap_ms'])
            self.assertFalse(stopped)
            self.assertFalse(result['historical_baseline_episode_rerun'])
            self.assertEqual(len(json.loads((root/'cohort-results.json').read_text())['results']),1)

    def test_cached_reproduction_failure_blocks_native_start(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); path=self.prepare(root,cached=False)
            with patch('retry.global_cap_probe.execute') as execute:
                with self.assertRaises(AssertionError):run(path)
            execute.assert_not_called()
            self.assertFalse((root/'execution-claim.json').exists())


if __name__=='__main__':unittest.main()
