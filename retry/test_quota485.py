"""Real reservation/atomic-file tests; no seed, scene, world or step calls."""
import json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
from retry.quota485 import RunQuota,QuotaStop,MIB

class Quota485Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='haic-quota485-test-');self.root=Path(self.tmp.name)
        self.q=RunQuota(self.root/'model',self.root/'native',free_bytes=lambda p:8*1024**3)
    def tearDown(self):self.tmp.cleanup()
    def test_actual_contract_constants(self):
        self.assertEqual((self.q.MODEL_FILES,self.q.NATIVE_FILES),(3596,3264))
        self.assertEqual((self.q.MODEL_BYTES,self.q.NATIVE_BYTES),(392471929,648961335))
        self.assertEqual((self.q.STATE_OBJECTS,self.q.NONSTATE_MODEL_BYTES),(508,95813632))
    def test_all_model_slots_reserved_before_any_creation(self):
        n=self.q.MODEL_FILES-self.q.CONTROL_FILES['model']
        for i in range(n):self.q.reserve(self.q.model_dir/f'data{i}.json',1)
        with self.assertRaises(QuotaStop):self.q.reserve(self.q.model_dir/'overflow.json',1)
        for i in range(self.q.CONTROL_FILES['model']):self.q.reserve(self.q.model_dir/f'{i}-cleanup-stop-private.json',1)
        with self.assertRaises(QuotaStop):self.q.reserve(self.q.model_dir/'result.json',1)
        self.assertEqual(self.q.summary()['files']['model'],3596)
        self.assertFalse(any(self.q.model_dir.iterdir()))
    def test_all_native_slots_include_nested_observations(self):
        n=self.q.NATIVE_FILES-self.q.CONTROL_FILES['native']
        for i in range(n):self.q.reserve(self.q.native_dir/'caseA'/f'obs{i}.png',1)
        with self.assertRaises(QuotaStop):self.q.reserve(self.q.native_dir/'caseB'/'obs.png',1)
        self.q.reserve(self.q.native_dir/'result.json',1)
        self.assertEqual(self.q.summary()['files']['native'],3249)
    def test_termination_bytes_are_unspendable_by_data(self):
        budgets={**self.q.CONTROL_BYTES,'native':64}
        with patch.object(RunQuota,'NATIVE_BYTES',256),patch.object(RunQuota,'CONTROL_BYTES',budgets):
            self.q.write_bytes(self.q.native_dir/'data.bin',b'x'*192)
            with self.assertRaises(QuotaStop):self.q.write_bytes(self.q.native_dir/'more.bin',b'x')
            self.assertFalse((self.q.native_dir/'more.bin').exists())
            self.q.write_bytes(self.q.native_dir/'result.json',b'x'*64)
            self.assertEqual(self.q.summary()['bytes']['native'],256)
            with self.assertRaises(QuotaStop):self.q.write_bytes(self.q.native_dir/'stop-private.json',b'x')
    def test_native_atomic_publish_overwrite_exclusive_and_abort(self):
        p=self.q.native_dir/'caseA'/'raw.json'
        self.q.save(p,{'value':1});first=p.read_bytes();self.q.save(p,{'value':2})
        self.assertEqual(self.q.summary()['files']['native'],1)
        with self.assertRaises(FileExistsError):self.q.write_bytes(p,b'x',exclusive=True)
        self.assertEqual(json.loads(p.read_bytes()),{'value':2});self.assertEqual(self.q.summary()['pending'],0)
        self.assertEqual(self.q.temporary_bytes,0);self.assertFalse(list(p.parent.glob('*.tmp')))
        self.assertNotEqual(first,p.read_bytes())
    def test_workspace_allowlist_and_byte_control_reserve(self):
        p=self.root/'workspace'/'new.json'
        with self.assertRaises(QuotaStop):self.q.save(p,{})
        self.q.register_workspace(p);self.q.save(p,{'new':True})
        with self.assertRaises(QuotaStop):self.q.save(p.parent/'old.json',{})
        self.assertEqual(self.q.summary()['files']['workspace'],1)
        p.write_bytes(b'changed')
        with self.assertRaises(QuotaStop):self.q.save(p,{})
    def test_temp_reserve_and_nonfinite_rejected_before_create(self):
        p=self.q.native_dir/'data.bin'
        with self.assertRaises(QuotaStop):self.q.reserve(p,32*MIB+1)
        self.q.free_bytes=lambda volume:512*MIB
        with self.assertRaises(QuotaStop):self.q.write_bytes(p,b'x')
        self.assertFalse(p.exists());self.assertEqual(self.q.summary()['pending'],0)
        with self.assertRaises(ValueError):self.q.save(self.q.native_dir/'bad.json',{'x':float('nan')})
    def test_allocation_decision_state_caps_are_enforced(self):
        for name,size in [('allocation-input-001.json',4097),('allocation-proof-001.json',8193),('decision-001.json',65537),('state-a.json',393217)]:
            with self.assertRaises(QuotaStop):self.q.reserve(self.q.model_dir/name,size)
        for i in range(508):self.q.reserve(self.q.model_dir/f'state-{i}.json',1)
        with self.assertRaises(QuotaStop):self.q.reserve(self.q.model_dir/'state-over.json',1)
    def test_alias_install_preserves_codec_and_routes_all_retained_files(self):
        import retry.io481 as codec
        model=self.q.model_quota();probe=types.ModuleType('retry.quota485_probe')
        original_reader=codec.ORIGINAL_READ
        probe.save=model.original_save;probe.receipt=model.original_receipt
        probe.read=codec.ORIGINAL_READ;probe.load=codec.ORIGINAL_LOAD
        sys.modules[probe.__name__]=probe
        originals=[]
        old=(model.original_save,model.original_receipt,codec.ORIGINAL_READ,codec.ORIGINAL_LOAD)
        for name,module in list(sys.modules.items()):
            if name.startswith('retry.') and module is not None:
                for key,value in list(vars(module).items()):
                    if any(value is f for f in old):originals.append((module,key,value))
        try:
            model.install();p=self.q.model_dir/'alias.json'
            probe.save(p,{'a':1});self.assertEqual(probe.read(p),{'a':1})
            self.assertEqual(self.q.summary()['files']['model'],1)
            self.assertIs(codec.ORIGINAL_READ,original_reader)
            with patch.object(RunQuota,'MODEL_FILES',self.q.CONTROL_FILES['model']+1):
                with self.assertRaises(QuotaStop):probe.receipt(self.q.model_dir/'overflow.json',{})
            self.assertFalse((self.q.model_dir/'overflow.json').exists())
            self.assertEqual(self.q.summary()['pending'],0)
        finally:
            for module,key,value in originals:setattr(module,key,value)
            del sys.modules[probe.__name__]
    def test_failed_postpublish_validation_still_accounts_actual_bytes(self):
        p=self.q.native_dir/'journal.json';self.q.write_bytes(p,b'old')
        with patch.object(self.q,'commit',side_effect=RuntimeError('injected validation failure')):
            with self.assertRaises(RuntimeError):self.q.write_bytes(p,b'new-longer')
        self.assertEqual(self.q.summary()['bytes']['native'],10)
        self.assertEqual(self.q.summary()['pending'],0)
        self.assertEqual(self.q.summary()['temporary_bytes'],0)
    def test_codec_roundtrip_and_state_files_use_central_counter(self):
        # Loading frozen class definitions creates no world. Poison construction
        # and step before attaching or exercising the unchanged serializer.
        import retry.io481 as codec
        from retry.terminal410_model import TerminalVehicleTransition
        with patch.object(TerminalVehicleTransition,'__init__',side_effect=AssertionError('physics forbidden')),patch.object(TerminalVehicleTransition,'step',side_effect=AssertionError('physics forbidden')):
            model=self.q.model_quota()
            value={'state':{'physical':{'v':1.0},'finish_tracker':{},'elapsed_raw_steps':0},'RNG':b'bytes'}
            p=self.q.model_dir/'context-001.json';model.save_receipt(p,value)
            self.assertEqual(codec.load_receipt(p),value)
            self.assertEqual(self.q.summary()['files']['model'],2)
            self.assertEqual(len(list(self.q.model_dir.glob('state-*.json'))),1)
            self.assertEqual(self.q.summary()['pending'],0)
            state=next(self.q.model_dir.glob('state-*.json'));state.write_text('{}')
            with self.assertRaises(Exception):codec.load_receipt(p)

if __name__=='__main__':unittest.main()
