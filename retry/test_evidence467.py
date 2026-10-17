"""467 injected IO integration and fault tests. Synthetic state, physics forbidden."""
import ast,copy,hashlib,inspect,json,uuid,textwrap,unittest
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from retry.evidence467_io import Evidence467,Evidence467Error
from retry.integration467 import IOCapture467,Completion467
from retry.boundary434 import Completion434,decode,encoded,ProtocolStop
from retry.test_boundary434 import fixture
from retry.pilot420_json import json_ready,restore_bytes
from retry.loss389_analyze import sha

BASE=Path('/tmp/haic-retry-stage467-private/fixtures')

class Evidence467Tests(unittest.TestCase):
 def newroot(self,label):
  BASE.mkdir(parents=True,exist_ok=True)
  return BASE/(label+'-'+uuid.uuid4().hex)
 def io(self,label,**kw):return Evidence467(self.newroot(label),**kw)
 def chain(self,label='chain',event=52):
  ctx,a,b,t=fixture(event);io=self.io(label);store=IOCapture467(io)
  store.source_record(a);store.constructor_proof(ctx,a);store.runtime_link(b);key=store.seal(b,ctx,a)
  return ctx,a,b,t,io,store,key

 def test_actual_injected_chain_restore_factual_reader_and_completion_no_physics(self):
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  from retry import diagnose
  import Box2D
  with ExitStack() as stack:
   forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('467_FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('467_FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('467_FORBIDDEN_WORLD'))))
   for event in (52,40):
    ctx,a,b,t,io,store,key=self.chain(event=event)
    restored=store.restore_inputs(store.constructor);state,memory,rng=ctx.parent.fork_inputs();self.assertEqual(restored,dict(state=state,memory=memory,rng=rng,ledger=ctx.ledger))
    sealed=store.pending[b.child_id][1];factual=store.factual_rows(sealed)
    self.assertEqual(factual['posts'],decode(b.posts_bytes));self.assertEqual(factual['actions'],decode(b.actions_bytes));self.assertEqual(factual['snapshot'],decode(b.snapshot_bytes));self.assertEqual(factual['memory'],decode(b.memory_bytes))
    self.assertIs(type(factual['rng']['global_pickle']),bytes)
    payload=io.read_receipt(sealed)
    for name in ('context_bytes','snapshot_bytes','memory_bytes','RNG_bytes','ledger_bytes','posts_bytes','actions_bytes'):self.assertEqual(payload[name],getattr(b,name))
    store.begin_continuation(b.child_id,key);completion=store.complete(b,t,ctx,a);self.assertEqual((completion.finish_ticks.lo,completion.finish_ticks.hi),(event-1,event))
    self.assertFalse(completion.actual_DONE_allowed);self.assertFalse(completion.actual_execution_allowed);self.assertFalse(completion.promotion_allowed);self.assertIs(completion.authenticate(ctx),completion)
    self.assertTrue(all(event['physical_readback_verified'] and event['descriptor_readback_verified'] for event in io.events));self.assertEqual(len(io.events),5)
    self.assertFalse(any(p.suffix=='.json' and not p.name.endswith('.descriptor.json') and p.name!='_root467.json' for p in io.directory.iterdir()))
   for forbidden_call in forbidden:forbidden_call.assert_not_called()

 def test_semantic_continuation_validation_matches434_exact_AST(self):
  def semantic(method):
   tree=ast.parse(textwrap.dedent(inspect.getsource(method)));body=tree.body[0].body
   start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Tuple) and ast.unparse(n.targets[0])=='(tracker, times, ledger)')
   return ast.dump(ast.Module(body=body[start:],type_ignores=[]),include_attributes=False)
  self.assertEqual(semantic(Completion434.authenticate),semantic(Completion467.authenticate))

 def test_readonly_reopen_real_restore_completion_and_JSONL_factual_reader(self):
  ctx,a,b,t,io,store,key=self.chain('reopen');store.begin_continuation(b.child_id,key);completion=store.complete(b,t,ctx,a)
  rows=decode(b.actions_bytes);rows[0]['synthetic_bytes']=bytes(range(256));rows[0]['text']='first\nsecond\u2028third'
  descriptor=store.write_factual_jsonl('factual-rows',rows);empty=io.write_jsonl('empty-rows',[])
  before={p.name:sha(p) for p in io.directory.iterdir() if p.is_file()};reader=Evidence467.open_readonly(io.directory);store.io=reader
  self.assertEqual(store.read_factual_jsonl(descriptor),rows);self.assertEqual(reader.read_jsonl(empty),[])
  self.assertEqual(store.restore_inputs(store.constructor)['ledger'],ctx.ledger);reopened=replace(completion,io=reader);self.assertEqual(reopened.finish_ticks,completion.finish_ticks)
  with self.assertRaises(Evidence467Error):reader.write_receipt('forbidden',{})
  with self.assertRaises(Evidence467Error):reader.write_jsonl('forbidden-lines',[])
  with self.assertRaises(Evidence467Error):reader.read_receipt(descriptor)
  with self.assertRaises(Evidence467Error):reader.read_jsonl(store.constructor)
  self.assertEqual(before,{p.name:sha(p) for p in io.directory.iterdir() if p.is_file()})

 def test_exact_nested_binary_codec_and_existing_root_or_duplicate_never_overwritten(self):
  io=self.io('binary');value=dict(allbytes=bytes(range(256)),nested=[dict(payload=b'\x00\xff\x80\n')],empty=b'')
  descriptor=io.write_receipt('binary',value);self.assertEqual(io.read_receipt(descriptor),value)
  path=io.directory/descriptor['physical_relative_path'];before=sha(path)
  with self.assertRaises(Evidence467Error):io.write_receipt('binary',dict(replacement=True))
  self.assertEqual(sha(path),before)
  with self.assertRaises(Evidence467Error):Evidence467(io.directory)

 def test_seal_order_duplicate_and_unsafe_tail_are_fail_closed(self):
  ctx,a,b,t=fixture();io=self.io('order');store=IOCapture467(io)
  with self.assertRaises(ProtocolStop):store.seal(b,ctx,a)
  store.source_record(a);store.constructor_proof(ctx,a);store.runtime_link(b);key=store.seal(b,ctx,a)
  with self.assertRaises(ProtocolStop):store.seal(b,ctx,a)
  store.begin_continuation(b.child_id,key)
  with self.assertRaises(ProtocolStop):store.begin_continuation(b.child_id,key)
  posts=decode(t.posts_bytes);posts[-1]['damage']=1.
  with self.assertRaises(ProtocolStop):store.complete(b,replace(t,posts_bytes=encoded(posts)),ctx,a)
  self.assertNotIn(b.child_id,store.closed);self.assertIsNone(b.finish_ticks)
  self.assertTrue((io.directory/(b.child_id+'-tail.descriptor.json')).exists())

 def test_corrupt_and_truncated_gzip_or_descriptor_are_rejected(self):
  for kind in ('flip','truncate','descriptor'):
   io=self.io(kind);descriptor=io.write_receipt('payload',dict(raw=b'private-synthetic'*100));path=io.directory/descriptor['physical_relative_path']
   if kind=='flip':
    data=bytearray(path.read_bytes());data[len(data)//2]^=1;path.write_bytes(data)
   elif kind=='truncate':path.write_bytes(path.read_bytes()[:-5])
   else:(io.directory/descriptor['descriptor_relative_path']).write_text('{}')
   with self.assertRaises((Evidence467Error,ValueError,EOFError,OSError)):io.read_receipt(descriptor)

 def test_gzip_CRC_logical_hash_receipt_hash_and_descriptor_schema_are_independent(self):
  for kind in ('CRC','logical','receipt','missing_field'):
   io=self.io('independent-'+kind);descriptor=io.write_receipt('payload',dict(binary=b'\x00\xff'*64));descriptor=copy.deepcopy(descriptor)
   if kind=='CRC':
    path=io.directory/descriptor['physical_relative_path'];data=bytearray(path.read_bytes());data[-8]^=1;path.write_bytes(data);descriptor['stored_sha256']=hashlib.sha256(data).hexdigest()
   elif kind=='logical':descriptor['logical_sha256']='0'*64
   elif kind=='receipt':descriptor['receipt_digest']='0'*64
   else:descriptor.pop('logical_sha256')
   published=io.directory/'payload.descriptor.json';published.write_text(json.dumps(descriptor))
   with self.assertRaises((Evidence467Error,ValueError,EOFError,OSError)):io.read_receipt(descriptor)

 def test_corruption_at_live_runtime_and_seal_boundaries_cannot_advance_state(self):
  ctx,a,b,t=fixture();io=self.io('preseal');store=IOCapture467(io);store.source_record(a);store.constructor_proof(ctx,a);descriptor=store.runtime_link(b)
  path=io.directory/descriptor['physical_relative_path'];path.write_bytes(path.read_bytes()[:-1])
  with self.assertRaises((Evidence467Error,OSError,EOFError)):store.seal(b,ctx,a)
  self.assertEqual(store.pending,{});self.assertEqual(store.started,set())
  ctx,a,b,t,io,store,key=self.chain('prebegin');descriptor=store.pending[b.child_id][1];path=io.directory/descriptor['physical_relative_path'];path.write_bytes(path.read_bytes()[:-1])
  with self.assertRaises((Evidence467Error,OSError,EOFError)):store.begin_continuation(b.child_id,key)
  self.assertEqual(store.started,set());self.assertEqual(store.closed,set())

 def test_reserve_guard_failure_creates_no_root_or_descriptor(self):
  root=self.newroot('reserve')
  with patch('retry.evidence467_io.shutil.disk_usage',return_value=SimpleNamespace(free=512*1024**2-1)):
   with self.assertRaises(Evidence467Error):Evidence467(root)
  self.assertFalse(root.exists())

 def test_ancestor_source_or_constructor_corruption_blocks_seal(self):
  for ancestor in ('source','constructor'):
   ctx,a,b,t=fixture();io=self.io('ancestor-'+ancestor);store=IOCapture467(io)
   store.source_record(a);store.constructor_proof(ctx,a);store.runtime_link(b)
   descriptor=getattr(store,ancestor);path=io.directory/descriptor['physical_relative_path']
   path.write_bytes(path.read_bytes()[:-1])
   with self.assertRaises((Evidence467Error,OSError,EOFError)):store.seal(b,ctx,a)
   self.assertEqual(store.pending,{});self.assertEqual(store.started,set())

 def test_fsync_and_publish_faults_retain_artifacts_without_success_descriptor(self):
  for stage in ('fsync','descriptor_publish'):
   def fault(where,details):
    if where==stage:raise OSError('467_injected_'+stage)
   io=self.io(stage,fault_hook=fault)
   with self.assertRaises(OSError):io.write_receipt('payload',dict(raw=bytes(range(256))*8))
   self.assertFalse((io.directory/'payload.descriptor.json').exists());self.assertTrue(list(io.directory.iterdir()));self.assertEqual(io.events,[])

 def test_partial_write_retains_partial_and_cannot_publish_success(self):
  io=self.io('partial')
  def partial(raw,data,kind):
   raw.write(data[:max(1,len(data)//2)]);raw.flush();raise Evidence467Error('467_injected_short_write')
  with patch.object(io,'_write',side_effect=partial):
   with self.assertRaises(Evidence467Error):io.write_receipt('payload',dict(raw=bytes(range(256))*8))
  self.assertFalse((io.directory/'payload.descriptor.json').exists());self.assertTrue(list(io.directory.glob('*.partial')));self.assertEqual(io.events,[])
