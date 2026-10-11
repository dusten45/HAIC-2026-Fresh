"""Transfer failures stay visible and block only the conditional combination."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from retry.cap_validation_probe import admitted


class CombinationAdmissionTests(unittest.TestCase):
    def prepare(self, root, stage, completed=(True,True), verified=(True,True)):
        bundle=root/'contract.json';bundle.write_text(json.dumps({'max_actions':6000,'max_actions_each':2000,'candidate_archive_sha256':'frozen'}))
        budget=root/'effective.json';budget.write_text(json.dumps({'B_operating_cap':650000,'final_reserved_actions':84000,'research_remaining':4000}))
        preceding=[]
        for number,done,valid in zip((96,97),completed,verified):
            if number>=stage:continue
            path=root/f'{number}.json';path.write_text(json.dumps({'stage':number,'all_required_evidence_verified':valid,'pair':{'both_completed_verified':done}}));preceding.append(str(path))
        return {'stage':stage,'bundle_contract_path':str(bundle),'bundle_contract_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),
                'candidate':{'archive_sha256':'frozen'},'effective_budget_path':str(budget),'preceding_comparisons':preceding}

    def test_first_transfer_dnf_does_not_hide_second_transfer(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan=self.prepare(Path(temporary),97,completed=(False,True))
            self.assertEqual(admitted(plan)['status'],'PASS')

    def test_combination_requires_both_completed(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan=self.prepare(Path(temporary),98,completed=(True,False))
            with self.assertRaises(AssertionError):admitted(plan)

    def test_missing_qualification_blocks_combination(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan=self.prepare(Path(temporary),98,verified=(False,True))
            with self.assertRaises(AssertionError):admitted(plan)

    def test_two_qualified_completions_admit_combination(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan=self.prepare(Path(temporary),98)
            self.assertEqual(admitted(plan)['status'],'PASS')


if __name__=='__main__':unittest.main()
