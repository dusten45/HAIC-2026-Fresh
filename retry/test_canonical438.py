"""Strict stored437 adapter path and tamper controls, without any integration."""
import ast,copy,json,math,pickle,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from retry.canonical438 import canonical,compare,require_equal,CanonicalError
from retry.fixture438 import stored_env,adapter_values,check_adapter
from retry.receipt421_io import load_receipt
from retry.terminal410_model import from_actual_full
from retry.pedal331_run import plain
from retry.loss389_analyze import read
from retry.pilot420_backend import TechnicalStop
R=Path('/workspace/haic-private-retry-20261009');G=Path(__file__).resolve().parents[1]
class Canonical438(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.full=read(R/'stage437/actual_C0/final-private.json')
 def test_plain_supported_conversions_and_scalar_precision(self):
  a=dict(x=(np.float64(1.25),np.int64(2),np.bool_(True)),m=np.array([[1.,2.],[3.,4.]]));b=dict(x=[1.25,2,True],m=[[1.,2.],[3.,4.]]);self.assertEqual(plain(a),b);self.assertTrue(compare(a,b)['equal']);self.assertFalse(compare(np.float32(.1),.1)['equal']);self.assertFalse(compare(2**60,2**60+1)['equal'])
 def test_saved437_fixture_complete_real_capture_and_adapter_path(self):
  env=stored_env(self.full);ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(self.full['controller']));obs=np.zeros((4,84,84),np.float32);proxy,full,left,right=adapter_values(env,obs,ctrl);self.assertEqual(from_actual_full(full),from_actual_full(self.full));self.assertNotEqual(left['snapshot'],right['snapshot']);self.assertTrue(compare(left,right)['equal']);self.assertEqual([k for k in left['snapshot']['finish_tracker'] if left['snapshot']['finish_tracker'][k]!=right['snapshot']['finish_tracker'][k]],['center','forward'])
  with tempfile.TemporaryDirectory() as td:
   _,_,proof=check_adapter(env,obs,ctrl,td,'fixture');self.assertTrue(proof['equal']);self.assertFalse(list(Path(td).iterdir()))
 def test_actual_constructor_uses_tuple_center_and_forward(self):
  tree=ast.parse((G/'core/vendor/car_racing.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='FinishLineTracker'];self.assertEqual(len(calls),1);kv={x.arg:x.value for x in calls[0].keywords};self.assertIsInstance(kv['center'],ast.Tuple);self.assertIsInstance(kv['forward'],ast.Tuple)
 def test_saved_437_original_live_proxy_is_not_available_or_recertified(self):
  self.assertFalse((R/'stage437/C0_decision1-snapshot-mismatch-private.json').exists());self.assertEqual(read(R/'stage437/result.json')['status'],'ACTUAL_PAIR_CENSORED_STOP');self.assertEqual(read(R/'stage437/cost.json')['new_wrapper_actions'],118)
 def test_numeric_coordinate_time_tracker_memory_RNG_changes_rejected(self):
  env=stored_env(self.full);ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(self.full['controller']));_,_,a,b=adapter_values(env,np.zeros((4,84,84),np.float32),ctrl)
  for path in [('snapshot','physical','hull','position',0),('snapshot','physical','actual_time'),('snapshot','finish_tracker','previous_longitudinal'),('memory','C','s')]:
   x=copy.deepcopy(b);cursor=x
   for k in path[:-1]:cursor=cursor[k]
   cursor[path[-1]]+=1e-12;self.assertFalse(compare(a,x)['equal'],path)
  x=copy.deepcopy(b);x['RNG']['python_sha256']='changed';self.assertFalse(compare(a,x)['equal'])
 def test_field_deletion_extra_field_array_length_and_order_rejected(self):
  a=dict(x=[1.,2.],clock=3)
  for b in [dict(x=[1.,2.]),dict(x=[1.,2.],clock=3,extra=None),dict(x=[1.],clock=3),dict(x=[2.,1.],clock=3),dict(x=[[1.,2.]],clock=3)]:self.assertFalse(compare(a,b)['equal'])
 def test_empty_array_trailing_shape_not_lost_by_plain(self):
  self.assertEqual(plain(np.empty((0,2))),plain(np.empty((0,3))));self.assertFalse(compare(np.empty((0,2)),np.empty((0,3)))['equal']);self.assertFalse(compare(np.empty((0,2)),[])['equal']);self.assertTrue(compare(np.empty((0,2)),np.empty((0,2)))['equal'])
 def test_bool_int_float_and_signed_zero_not_conflated(self):
  for a,b in [(True,1),(1,1.),(0.,-0.)]:self.assertFalse(compare(a,b)['equal'])
 def test_nan_inf_both_sides_and_nested_array_rejected(self):
  for value in [float('nan'),float('inf'),float('-inf'),dict(x=np.array([float('nan')]))]:self.assertFalse(compare(value,value)['equal'])
 def test_nonstring_key_coercion_collision_and_unknown_dtype_rejected(self):
  for value in [{1:'x'},{1:'x','1':'y'},set([1]),np.array([1],dtype=object),np.array([1+2j])]:
   with self.assertRaises(CanonicalError):canonical(value)
 def test_mismatch_saves_both_lossless_originals_and_normalized_field_diff(self):
  a=dict(x=(1.,2.),memory=dict(last=1.),RNG='a');b=dict(x=[1.,2.001],memory=dict(last=1.),RNG='b')
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(TechnicalStop):require_equal(a,b,td,'case')
   q=load_receipt(Path(td)/'case-snapshot-mismatch-private.json');self.assertEqual(pickle.loads(q['original_left_pickle']),a);self.assertEqual(pickle.loads(q['original_right_pickle']),b);paths={x['path'] for x in q['normalized']['diffs']};self.assertEqual(paths,{'/x/1','/RNG'});self.assertFalse(q['normalized']['equal'])
 def test_nonfinite_original_preserved_without_json_coercion(self):
  a=dict(x=np.array([np.nan,np.inf]))
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(TechnicalStop):require_equal(a,a,td,'nan')
   q=load_receipt(Path(td)/'nan-snapshot-mismatch-private.json');raw=pickle.loads(q['original_left_pickle']);self.assertTrue(np.isnan(raw['x'][0]));self.assertTrue(np.isinf(raw['x'][1]));self.assertTrue(all(x['reason']=='canonicalization_rejected' for x in q['normalized']['diffs']))
 def test_end_to_end_fixture_physical_capture_tamper_records_exact_diff(self):
  env=stored_env(self.full);ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(self.full['controller']));_,_,a,b=adapter_values(env,np.zeros((4,84,84),np.float32),ctrl);a['snapshot']['physical']['hull']['position'][0]+=.001
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(TechnicalStop):require_equal(a,b,td,'physical')
   q=load_receipt(Path(td)/'physical-snapshot-mismatch-private.json');self.assertEqual(q['normalized']['diffs'][0]['path'],'/snapshot/physical/hull/position/0')
 def test_nested_representation_only_and_dictionary_order_ignored(self):
  self.assertTrue(compare(dict(a=(dict(x=np.array([1.,2.])),),b=np.int32(3)),dict(b=3,a=[dict(x=[1.,2.])]))['equal'])
