"""Pure/mock tests only: no physical source/native call permitted."""
import copy,math
from dataclasses import dataclass
from types import SimpleNamespace
from collections import Counter
import numpy as np
import pytest
import retry.beam579_math as m
import retry.beam579_model as b

@pytest.fixture(autouse=True)
def no_simulator(monkeypatch):
    def no(*a,**k):raise AssertionError('UNEXPECTED_SOURCE_OR_NATIVE')
    monkeypatch.setattr(b.d,'source_tick',no);monkeypatch.setattr(b.d,'force_rows',no)


def state():return dict(root=SimpleNamespace(roads=()),visited={1},tracker=b.d.FinishLineTracker(**dict(center=(0,0),forward=(1,0),half_width=10)))

def make_state():
    tracker=SimpleNamespace(value=1)
    return dict(root=(),visited={1},tracker=tracker,launch=[1,4],tracking=[0,0],elapsed=1.92,global_raw=96,progress=80.)


def test_integer_gate_no_epsilon():
    spec={'baseline_before_raw':192,'minimum_raw_gain':5,'minimum_interpolated_COM_speed_m_s':79.}
    hit={'eligible':True,'after_raw':187,'COM_speed_m_s':79.}
    assert m.passes(hit,spec)
    assert not m.passes(dict(hit,after_raw=188),spec)
    assert not m.passes(dict(hit,COM_speed_m_s=np.nextafter(79.,-math.inf)),spec)
    assert m.passes(dict(hit,after_raw=243),dict(spec,baseline_before_raw=247,minimum_raw_gain=4))


def test_vector_velocity_interpolation():
    row=dict(before_root_without_roads={'center':[-1,0],'planar':{'linear':{'velocity':[3,0]}}},root_without_roads={'center':[1,0],'planar':{'linear':{'velocity':[0,4]}}},global_raw_before=186,global_raw_after=187,episode_before_s=3.72,episode_after_s=3.74,progress=200.,path_error=3.)
    hit=m.crossing(row,{'center':[0,0],'forward_normal':[1,0],'station_m':200.})
    assert hit['COM_speed_m_s']==2.5 and hit['before_raw']==186 and hit['after_raw']==187
    assert not m.crossing(dict(row,progress=210.0001),{'center':[0,0],'forward_normal':[1,0],'station_m':200.})['eligible']


def test_action_dedup_keeps_factual_tag(monkeypatch):
    monkeypatch.setattr(m,'project',lambda *a:{'s':0.})
    monkeypatch.setattr(m,'point_at',lambda *a:(0.,10.))
    root=SimpleNamespace(center=(0,0),planar=SimpleNamespace(angle=0.,linear=SimpleNamespace(velocity=(0,0))))
    path={'length':40.,'ds':[20.,20.],'arcs':[0.,20.,40.],'points':[[0.,0.],[0.,20.]]}
    out=m.actions({'root':root,'progress':0.},path,np.array([0.,1.,0.],np.float32))
    factual=[q for q in out if q['factual_action']]
    assert len(out)==12 and len(factual)==1 and factual[0]['id']==4


def test_frozen_root_proof_rejects_nested_list():
    @dataclass(frozen=True)
    class X:value:object
    m.immutable(X((1.,2.)))
    with pytest.raises(RuntimeError):m.immutable(X([1.,2.]))


def test_clone_mutable_independence():
    # Use the real tracker class from stored static parameters, without a world.
    static=b.d.rd(b.INPUTS['static']);ledger=b.d.rd(b.INPUTS['ledger']);owner=SimpleNamespace(static=static,ledger=ledger,paths=b.d.rd(b.INPUTS['paths']))
    parent=b.d.Study.initial(owner);child=m.clone(parent);sibling=m.clone(parent);m.isolated(child,[parent,sibling])
    before=copy.deepcopy(b.d.Study.checkpoint(owner,parent));child['visited'].add(999999);child['launch'][0]+=1;child['tracking'][1]+=4
    child['tracker'].finish_time_s=1.
    assert b.d.Study.checkpoint(owner,parent)==before and sibling['tracker'].finish_time_s!=1.
    m.immutable(parent['root'])


def fake_owner(monkeypatch,reject_raw=None,cross_raw=1):
    s=object.__new__(b.Study);s.best_prefix=None;s.factual_equal=lambda row:None
    parent=make_state();parent['root']=SimpleNamespace(roads=())
    # clone uses real tracker serialization, so use deepcopy only in this toy test.
    monkeypatch.setattr(b,'clone',copy.deepcopy)
    # Preserve the proven immutable roads object.
    def raw(state,action,index,k,phase):
        state['global_raw']+=1;state['progress']+=1;state['elapsed']+=.02
        row={'k':k}
        return row,'FORCE' if k==reject_raw else None
    s.raw=raw
    monkeypatch.setattr(b,'crossing',lambda row,plane:{'after_raw':row['k']} if row['k']==cross_raw else None)
    return s,parent


def test_crossing_hold_late_failure_discards_terminal(monkeypatch):
    s,parent=fake_owner(monkeypatch,reject_raw=4)
    edge=s.hold(parent,np.array([0,0,0],np.float32),25,None,plane={})
    assert edge['failure']=='FORCE' and edge['crossing'] is None
    assert parent['global_raw']==96


def test_first_crossing_fixed_and_full_hold(monkeypatch):
    s,parent=fake_owner(monkeypatch)
    monkeypatch.setattr(b,'crossing',lambda row,plane:{'after_raw':row['k']})
    edge=s.hold(parent,np.array([0,0,0],np.float32),25,None,plane={})
    assert len(edge['rows'])==4 and edge['crossing']['after_raw']==1 and edge['state']['global_raw']==100


def test_factual_rejection_hard_stop(monkeypatch):
    s,parent=fake_owner(monkeypatch,reject_raw=2)
    with pytest.raises(RuntimeError,match='FACTUAL_REJECTED'):s.hold(parent,np.array([0,0,0],np.float32),25,None,factual=True)


def test_actual_wheel_invocation_counter():
    s=object.__new__(b.Study);s.counts=Counter();s.stage_counts={};s.bucket='search';s.guard=lambda **k:None
    assert s.wheel_call('external_force',lambda:7)==7
    with pytest.raises(ValueError):s.wheel_call('internal_force',lambda:(_ for _ in ()).throw(ValueError()))
    assert s.counts=={'external_force':1,'internal_force':1}


def test_alias_detection():
    a=make_state();other=copy.deepcopy(a);m.isolated(other,[a]);other['visited']=a['visited']
    with pytest.raises(RuntimeError,match='BRANCH_MUTABLE_ALIAS'):m.isolated(other,[a])


def test_replay_checkpoint_content_independent_roads_identity():
    static=b.d.rd(b.INPUTS['static']);ledger=b.d.rd(b.INPUTS['ledger']);owner=SimpleNamespace(static=static,ledger=ledger,paths=b.d.rd(b.INPUTS['paths']))
    a=b.d.Study.initial(owner);c=b.d.Study.initial(owner)
    assert a['root'].roads is not c['root'].roads
    assert b.d.canonical(b.d.Study.checkpoint(owner,a))==b.d.canonical(b.d.Study.checkpoint(owner,c))


def test_factual_parent_all_actions_and_terminal_before_pruning(monkeypatch):
    s=object.__new__(b.Study);s.contract={'gates':{'A':{'max_holds':1,'baseline_before_raw':192,'minimum_raw_gain':5,'minimum_interpolated_COM_speed_m_s':79.},'planes':[{}]}};s.path={};s.commands={25:np.zeros(3,np.float32)};s.best=None;s.result={};s.isolation_checks=0;s.guard=lambda **k:None;s.cost=lambda:{};s.journal=SimpleNamespace(append=lambda *a,**k:None)
    s.fingerprint=lambda st:(st['global_raw'],st['progress'],tuple(sorted(st['visited'])),tuple(st['launch']),tuple(st['tracking']))
    s.node_summary=lambda n:{'crossing':n['crossing'],'progress':n['state']['progress']}
    monkeypatch.setattr(b,'actions',lambda *a:[{'id':i,'action':np.array([0.,0.,0.],np.float32),'factual_action':i==0} for i in range(13)])
    monkeypatch.setattr(b,'rank_key',lambda n,p:(-n['state']['progress'],tuple(n['ids'])))
    monkeypatch.setattr(b,'atomic_write',lambda *a,**k:None)
    monkeypatch.setattr(b.d.Study,'checkpoint',lambda self,st:{'progress':st['progress']})
    seen=[]
    def hold(parent,action,index,phase,plane,factual):
        i=len(seen);seen.append((i,factual));st=copy.deepcopy(parent);st['global_raw']+=4;st['progress']=float(i)
        hit={'eligible':True,'after_raw':187,'COM_speed_m_s':80.} if i==1 else None
        return {'state':st,'rows':[],'failure':None,'crossing':hit}
    s.hold=hold;start={'state':make_state(),'rows':[],'commands':[],'ids':[],'factual':True,'crossing':None}
    terminal=s.stage('A',start)
    assert len(seen)==13 and sum(f for _,f in seen)==1
    assert terminal['ids']==[1] and s.result['A']['passing_terminals']==1
    assert s.result['A']['depths'][0]['live']==4


def test_preforce_rejection_attempt_external_only(monkeypatch):
    s=object.__new__(b.Study);s.counts=Counter();s.stage_counts={};s.bucket='search';s.guard=lambda **k:None;s.journal=SimpleNamespace(append=lambda *a,**k:'event')
    monkeypatch.setattr(b.d,'short',lambda root:{'root':1})
    def fakeforce(*a):
        s.count('external_force',4)
        return [{'ratio':2.,'clipped':True} for _ in range(4)]
    monkeypatch.setattr(b.d,'force_rows',fakeforce)
    phase=b.Phase(s,'search');v=phase.evaluate(None,np.zeros(3,np.float32),[0,0],{},1.059,.1,True)
    assert v['gate']=='FORCE' and s.counts['attempted_raw']==1 and s.counts['external_force']==4 and s.counts['internal_force']==s.counts['completed_model_ticks']==0
