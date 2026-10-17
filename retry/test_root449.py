"""Native root provenance and stop-channel negatives, no integration."""
import copy,json,unittest
from dataclasses import replace
from pathlib import Path
from retry.root449 import load_root449,validate_native449
from retry.planner419_model_ledger import ForecastLedger
R=Path('/workspace/haic-private-retry-20261009')

class Root449Tests(unittest.TestCase):
    def fixture(self):
        data=load_root449(R,'nominal')
        row=json.loads((R/'stage448/actual_nominal/trace-private.jsonl').read_text().splitlines()[-1])
        return data,row
    def check(self,data,row,**changes):
        return validate_native449(changes.get('full',data['full']),row,changes.get('ledger',data['ledger']),changes.get('original',data['original']),changes.get('blob',data['RNG_blob']))
    def test_both_observed_native_roots_and_whole_wrapper_clocks(self):
        a,b=load_root449(R,'nominal'),load_root449(R,'fullgas')
        self.assertEqual(a['native_prefix_ticks'],80);self.assertEqual(b['native_prefix_ticks'],64)
        self.assertEqual(a['original'],b['original']);self.assertNotEqual(a['ledger'].last_clock_tick,b['ledger'].last_clock_tick)
        self.assertNotEqual(a['ledger'].digest(),b['ledger'].digest())
    def test_forecast_channel_is_not_an_observed_native_root(self):
        d,row=self.fixture()
        with self.assertRaises(Exception):self.check(d,row,ledger=ForecastLedger.fork(d['ledger']))
    def test_controller_memory_must_be_last_native_observation(self):
        d,row=self.fixture();full=copy.deepcopy(d['full']);full['controller']['C']['s']+=.001
        with self.assertRaises(Exception):self.check(d,row,full=full)
    def test_native_clock_cannot_be_shifted(self):
        d,row=self.fixture()
        with self.assertRaises(Exception):self.check(d,row,ledger=replace(d['ledger'],last_clock_tick=d['ledger'].last_clock_tick+1))
    def test_progress_cannot_be_reanchored_at_exactly60m(self):
        d,row=self.fixture()
        with self.assertRaises(Exception):self.check(d,row,ledger=replace(d['ledger'],progress_m=d['original']['progress_m']+60))
    def test_global_RNG_requires_native_end_hash(self):
        d,row=self.fixture();full=copy.deepcopy(d['full']);full['RNG']['python_sha256']='0'*64
        with self.assertRaises(Exception):self.check(d,row,full=full)
        full=copy.deepcopy(d['full']);full['RNG']['numpy_sha256']='0'*64
        with self.assertRaises(Exception):self.check(d,row,full=full)
    def test_original_clock_cannot_follow_native_endpoint(self):
        d,row=self.fixture();old=copy.deepcopy(d['original']);old['last_clock_tick']=d['ledger'].last_clock_tick+1
        with self.assertRaises(Exception):self.check(d,row,original=old)
