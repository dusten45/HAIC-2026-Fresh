"""Integrated zero-world gate: real SourceC read-only phases, mocks and codec auth."""
import ast,copy,hashlib,io,json,pickle,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
import retry.online481 as online
from retry.io481 import Quota,read,load_receipt,canonical,CODEC_KEY
from retry.history481 import validate_history,HistoryStop481
from retry.test_history481 import HistoryFinite481Tests
from retry.law477 import root_inputs477
from retry.paired417_common import SourceC
from retry.pilot420_backend import fingerprint
from retry.loss389_analyze import read as oldread
from retry.receipt421_io import load_receipt as oldload
ROOT=Path('/workspace/haic-private-retry-20261009')
G=Path(__file__).resolve().parents[1]

class Gate481Tests(unittest.TestCase):
    def test_codec_roundtrip_shared_state_and_tamper(self):
        with tempfile.TemporaryDirectory(prefix='haic481-static-') as folder:
            d=Path(folder);q=Quota(d,1364580771,16*1024**2)
            state=dict(physical={'x':[1.,2.]},finish_tracker={'event':None},elapsed_raw_steps=4)
            v=dict(state=state,nested=[copy.deepcopy(state)],RNG=b'fixture')
            p=d/'fixture.json';q.save_receipt(p,v)
            self.assertEqual(load_receipt(p),v);self.assertEqual(len(q.objects),1)
            obj=next(d.glob('state-*.json'));data=json.loads(obj.read_text());data['full_state']['elapsed_raw_steps']=5;obj.write_text(json.dumps(data))
            with self.assertRaises(Exception):load_receipt(p)
    def test_codec_missing_ref_and_outside_ref_rejected(self):
        with tempfile.TemporaryDirectory(prefix='haic481-static-') as folder:
            d=Path(folder);q=Quota(d,1364580771,16*1024**2)
            p=d/'fixture.json';q.save_receipt(p,dict(state=dict(physical={},finish_tracker={},elapsed_raw_steps=0)))
            obj=next(d.glob('state-*.json'));obj.unlink()
            with self.assertRaises(FileNotFoundError):load_receipt(p)
            value=json.loads(p.read_text());value['payload']['state']['__haic_full_state_ref481__']='../escape';p.write_text(json.dumps(value))
            with self.assertRaises(Exception):load_receipt(p)
    def test_real_context_codec_size_and_exact_full_payload(self):
        ctx=oldload(ROOT/'stage479/root47-full-prepared-private.json');blob=ctx['RNG']
        ctx['RNG']={'global_pickle':blob,'digest':hashlib.sha256(blob).hexdigest()}
        ctx.update(allocation_number=1,label='fixture',allocation_input_path='/tmp/allocation-input-001.json',allocation_input_sha256='a'*64,allocation_proof_path='/tmp/allocation-proof-001.json',allocation_proof_sha256='b'*64)
        with tempfile.TemporaryDirectory(prefix='haic481-static-') as folder:
            d=Path(folder);q=Quota(d,1364580771,16*1024**2);p=d/'context-001-private.json';q.save_receipt(p,ctx)
            self.assertEqual(load_receipt(p),ctx);self.assertLess(p.stat().st_size,16384)
            self.assertTrue(all(f.stat().st_size<=393216 for f in d.glob('state-*.json')))
    def test_complete_command_dedup(self):
        opts,_=online.commands([0.,.5,0.],[0.,.5,0.]);self.assertEqual(len(opts),2)
        opts,_=online.commands([-0.,0.,0.],[-0.,0.,0.]);self.assertEqual(len(opts),1)
        self.assertNotEqual(online.key([-0.,0.,0.]),online.key([0.,0.,0.]))
    def test_sourceC_real_pre23_and_pending_without_world(self):
        p=oldread(ROOT/'stage479-plan-durable-private.json');fixed=oldread(p['fixed_plan']);pace=np.asarray(oldread(p['pace_path'])['frozen268']);nodes=np.asarray(oldread(p['projection_path'])['projected_nodes'])
        state,memory,*_=root_inputs477(ROOT);stop=oldload(ROOT/'stage435/P_decision55-context-stop-private.json')
        for state,memory,expected in [(state,memory,'FIRST_LAP'),(stop['live_parent'],stop['memory_before_nominal'],'FINISH_CONFIRM')]:
            physical=copy.deepcopy(state);h=physical['physical']['hull'];w=physical['physical']['wheels']
            model=NS(t=physical['physical']['actual_time'],car=NS(hull=NS(position=h['position'],linearVelocity=h['velocity'],angle=h['angle'],angularVelocity=h['angular_velocity']),wheels=[NS(joint=NS(angle=z['joint']['angle']),tiles=z['tiles']) for z in w]),finish_line_tracker=NS(**physical['finish_tracker']),finished=False)
            ctrl=SourceC(fixed,pace,copy.deepcopy(memory));ctrl.policy.nodes=nodes.copy();before=copy.deepcopy(ctrl.memory());cmd=ctrl.act(model)
            self.assertEqual(ctrl.phase(),expected);self.assertEqual(state,physical);self.assertEqual(cmd.dtype,np.float32);self.assertNotEqual(before,ctrl.memory())
    def test_nominal_once_and_prepared_reuse_AST(self):
        tree=ast.parse((G/'retry/online481.py').read_text());prepare=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='act' for n in ast.walk(prepare)),1)
        for node in tree.body:
            if isinstance(node,ast.FunctionDef) and node.name!='prepare':self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='act' for n in ast.walk(node)))
        shadow=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Shadow');text=ast.unparse(shadow)
        self.assertLess(text.index('self.ledger ='),text.index('self.stream ='))
    def test_caps_and_lossless_bound(self):
        from retry.meter481 import Meter481
        self.assertEqual((Meter481.HARD_TICKS,Meter481.HARD_WORLDS),(4840,812))
        self.assertLess(Quota.STATE_MAX*Quota.STATES_MAX+Quota.NONSTATE_MODEL_MAX,1364580771)
        self.assertIn('self.charged_ticks+=4',(G/'retry/meter481.py').read_text())
        self.assertIn('>=402',(G/'retry/live481.py').read_text())
    def test_score_nonfinite_and_partial_official_hold(self):
        row=dict(predicted=dict(raw_ticks=1),tires=[dict(force_ratio=1.25)]*4);self.assertEqual(online.score(row),.25)
        row['tires'][0]={'force_ratio':float('nan')}
        with self.assertRaises(Exception):online.score(row)
    def test_selected_once_each_repeat_and_isolation(self):
        for badrepeat,mutation in [(False,False),(True,False),(False,True)]:
            parent=NS(label='mock',meter=NS(d=Path('/tmp')),rows=[],policy481='policy',stream=NS(child_id='parent'),version=0)
            ctx=dict(nominal=[0.,1.,0.],qstar=[0.,.5,0.],index=0,allocation_number=1)
            made=[]
            def create(c,ctx,label,binding):
                if mutation:c.version+=1
                child=NS(label=label,closed=False,status='ACTIVE',rows=[],ledger=NS(deadline_missed=False),stream=NS(posts=[]))
                child.signature=lambda:child.rows;made.append(label);return child
            def apply(child,ctx,command,tag):
                ratio=1.+float(command[1])+(1. if badrepeat and 'repeat' in child.label else 0.)
                row=dict(predicted=dict(raw_ticks=4,terminal=False),tires=[dict(force_ratio=ratio)]*16,memory_after={'C':{'phase':'FIRST_LAP'}},safety=[])
                child.rows.append(row);return row
            with patch.object(online,'stamp',lambda c:c.version),patch.object(online,'fresh',create),patch.object(online,'apply',apply),patch.object(online,'closed',lambda c:(c.label,'a'*64)),patch.object(online,'base_auth',lambda *args:{'mode':'online'}),patch.object(online,'persist_decision',lambda c,ctx,auth,*args:auth):
                if badrepeat or mutation:
                    with self.assertRaises(Exception):online.select(parent,ctx,None)
                else:
                    selected,summary=online.select(parent,ctx,None);self.assertEqual(len(made),4);self.assertEqual(summary['aliases'],['zero']);self.assertTrue(np.array_equal(selected['command'],[0.,0.,0.]))
    def test_live_history_full_context_chain_and_corruption(self):
        import retry.history481 as hist
        ctx=oldload(ROOT/'stage479/root47-full-prepared-private.json')
        ctx['allocation_number']=ctx['pending'][2];blob=ctx['RNG'];ctx['RNG']={'global_pickle':blob,'digest':hashlib.sha256(blob).hexdigest()}
        trace=oldread(ROOT/'stage479/root47_qstar_1-private.json');obs=oldread(ROOT/'stage479/root47_qstar_1-observer-private.json')
        ctx.update(context_path='/context',context_sha256='a'*64,label='static-parent',index=0,allocation_input_path='/allocation-input',allocation_input_sha256='e'*64,allocation_proof_path='/allocation-proof',allocation_proof_sha256='f'*64)
        parent=NS(policy481='c'*64,stream=NS(child_id='fixture-parent'),rows=[])
        k=online.key(ctx['qstar']);cmds={k:{'command':np.asarray(ctx['qstar'],np.float32)}}
        auth=online.base_auth(parent,ctx,ctx['qstar'],cmds,k,'baseline')
        receipt={'authorization':copy.deepcopy(auth),'options':{},'selected_repeat_proof':None}
        auth.update(decision_path='/decision',decision_sha256='b'*64)
        lookup={'/context':ctx,'/decision':receipt,'/allocation-input':dict(number=ctx['allocation_number'],label=ctx['label'],action=1,phase=ctx['after']['C']['phase'],nominal=ctx['nominal'],current_wheels=ctx['wheels']),'/allocation-proof':dict(number=ctx['allocation_number'],label=ctx['label'],action=1,phase=ctx['after']['C']['phase'],command=ctx['qstar'])}
        p=oldread(ROOT/'stage479-plan-durable-private.json');fixed=oldread(p['fixed_plan'])
        with patch.object(hist,'checked',lambda path,digest:lookup[str(path)]):
            proof=validate_history(ctx['state'],ctx['ledger'],obs['posts'],obs['actions'],[auth],trace['final_state'],trace['controller_memory'],trace['model_ledger'],fixed['line'],'c'*64)
            self.assertEqual(proof['actions'],1)
            bad=copy.deepcopy(auth);bad['state_before_digest']='d'*64
            with self.assertRaises(HistoryStop481):validate_history(ctx['state'],ctx['ledger'],obs['posts'],obs['actions'],[bad],trace['final_state'],trace['controller_memory'],trace['model_ledger'],fixed['line'],'c'*64)
    def test_frozen435_complete_history_authentication(self):
        stop,h=online.saved_history(ROOT);full=oldread(ROOT/'stage435/parent_P-private.json')['model_ledger'];obs=oldread(ROOT/'stage435/parent_P-observer-private.json');n=obs['link']['world_number']
        paths=[ROOT/x for x in ['stage435/P_decision55-context-stop-private.json','stage435/parent_P-private.json','stage435/parent_P-observer-private.json',f'stage435/world{n}-before-constructor-private.json']]
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};auth=[dict(mode='historical435',sources=sources,history_path=str(paths[2]),history_sha256=sources[str(paths[2])])]
        p=oldread(ROOT/'stage479-plan-durable-private.json');fixed=oldread(p['fixed_plan'])
        proof=validate_history(h['root'],h['ledger'],h['posts'],h['actions'],auth,stop['live_parent'],stop['memory_before_nominal'],full,fixed['line'],'f'*64,historical=True)
        self.assertTrue(proof['pending']);self.assertFalse(proof['actual_DONE_allowed'])
        mutated=copy.deepcopy(h['actions']);mutated[-1]['command']=[0.,0.,0.]
        with self.assertRaises(HistoryStop481):validate_history(h['root'],h['ledger'],h['posts'],mutated,auth,stop['live_parent'],stop['memory_before_nominal'],full,fixed['line'],'f'*64,historical=True)

def run():
    from retry.pilot420_backend import TerminalVehicleTransition
    # Imports/class definitions are permitted; constructors or world/step APIs
    # are poisoned for every test, including the real SourceC stub phase check.
    stream=io.StringIO();suite=unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Gate481Tests));suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(HistoryFinite481Tests))
    with patch.object(TerminalVehicleTransition,'__init__',side_effect=AssertionError('STATIC_WORLD_FORBIDDEN')),patch.object(TerminalVehicleTransition,'step',side_effect=AssertionError('STATIC_PHYSICS_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    return dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=stream.getvalue(),new_worlds=0,new_physics=0)

if __name__=='__main__':
    result=run();print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
