"""Source-free lineage, original selector delegation and accounting checks."""
from collections import Counter
from types import SimpleNamespace as NS
import copy
import numpy as np
import pytest
import retry.return583_model as s
from retry.return583_math import cache_accounting,bracket_comparison

@pytest.fixture(autouse=True)
def forbid_source(monkeypatch):
    def no(*a,**k):raise AssertionError('UNEXPECTED_SOURCE_OR_FORCE')
    monkeypatch.setattr(s.d,'source_tick',no);monkeypatch.setattr(s.d,'force_rows',no)

class Log:
    def __init__(self):self.rows=[]
    def append(self,kind,**data):self.rows.append((kind,data));return str(len(self.rows))

def owner():
    x=object.__new__(s.Study);x.counts=Counter();x.stage_counts={};x.mode_counts={};x.bucket='continuation';x.mode='forecast';x.choice_index=1;x.choice_calls=[];x.journal=Log();x.guard=lambda **k:None
    return x

def test_history_lineage_independent_candidates_and_rejected_force(monkeypatch):
    x=owner();p=s.Phase(x,'continuation');r=NS(planar=NS(linear=object()));p.seed(dict(root=r,tracking=[3,144],global_raw=132));seen=[]
    def evaluate(root,a,history,context,peak,clip,check):
        seen.append((history.copy(),context,peak));return dict(history=[history[0]+1,history[1]+4],forces=['rejected'],gate='FORCE')
    p.evaluate=evaluate;a=np.zeros(3,np.float32)
    assert p.force(r,a)==['rejected'] and p.force(r,a)==['rejected']
    assert seen[0][0]==seen[1][0]==[3,144] and seen[0][2]==s.policy.ADMISSION
    assert p.seed_history==[3,144] and p.last_forecast_history==[4,148]
    with pytest.raises(RuntimeError,match='LINEAGE'):p.force(NS(planar=NS(linear=object())),a)
    p.histories[id(r.planar.linear)]=(object(),[0,0])
    with pytest.raises(RuntimeError,match='LINEAGE'):p.force(r,a)

def test_tick_counter_pending_and_new_lineage(monkeypatch):
    x=owner();p=s.Phase(x,'continuation');r=NS(planar=NS(linear=object()));after=NS(planar=NS(linear=object()));p.seed(dict(root=r,tracking=[0,144],global_raw=132))
    with pytest.raises(RuntimeError,match='ALIAS'):p.tick(r,0.,0.,None,[0])
    with pytest.raises(RuntimeError,match='REJECTION'):p.tick(r,0.,0.,None,p.counter)
    p.pending=dict(gate='FORCE',history=[0,148])
    with pytest.raises(RuntimeError,match='REJECTION'):p.tick(r,0.,0.,None,p.counter)
    p.pending=dict(gate=None,history=[0,148])
    def toy_tick(self,*args):self.pending=None;return after
    monkeypatch.setattr(s.b.Phase,'tick',toy_tick)
    assert p.tick(r,0.,0.,None,p.counter) is after and p.histories[id(after.planar.linear)]==(after.planar.linear,[0,148])

def choose_toy(monkeypatch,kind):
    x=owner();p=s.Phase(x,'continuation');p.seed(dict(root=NS(planar=NS(linear=object())),tracking=[2,144],global_raw=132));x.active_phase=p;x.original_choose=s.policy.choose
    calls=[]
    def orig_factory(*args,**kwargs):
        def certify(a):
            # Pure mock: no force or integration, emulate original report shape.
            calls.append(a.copy());assert p.last_forecast_history==[2,144]
            ok=kind=='high' or (kind in ['search','finalfail'] and float(a[1])<=.5 and a[2]==0)
            if kind=='finalfail' and len(calls)>20 and np.array_equal(a,calls[-2]):ok=False
            return dict(ok=ok,reason='OK' if ok else 'FORCE_PEAK',clipped=2,samples=144,first_hold={'progress_gain':float(a[1]-a[2])} if ok else None)
        return certify
    x.orig_factory=orig_factory
    monkeypatch.setattr(s.policy,'nominal',lambda *a:np.array([.1,.3,0],np.float32));monkeypatch.setattr(s.policy,'backup',lambda *a:np.array([.1,0,.2],np.float32));monkeypatch.setattr(s.policy,'certifier',x.factory)
    action,detail=x.original_choose(None,None,None,0,p.counter,p.cost,65000,geometry={})
    accounting=cache_accounting(detail,x.choice_calls)
    assert accounting['actual_certification_calls']==len(calls)<=32
    assert accounting['cache_hits']>=0 and accounting['sample_cache_misses']==sum(c['role']=='SAMPLE' for c in x.choice_calls)
    assert p.seed_history==[2,144]
    return x,action,detail,accounting

@pytest.mark.parametrize('kind',['high','search','none'])
def test_original_choose_cache_and_fresh_final(monkeypatch,kind):
    x,a,detail,c=choose_toy(monkeypatch,kind)
    if kind=='none':assert a is None and detail['mode']=='NO_ADMISSIBLE_ACTION' and c['fresh_FINAL_calls']==0
    else:assert a is not None and c['fresh_FINAL_calls']==1 and x.choice_calls[-1]['role']=='FINAL'
    if kind=='high':assert c['evaluate_requests']==1 and c['sample_cache_misses']==1
    else:assert c['cache_hits']>=1

def test_final_failure_metadata_without_coarse_detail():
    c=cache_accounting({'mode':'FINAL_CERTIFICATION_FAILED'},[dict(role='SAMPLE',report={'ok':False}),dict(role='FINAL',report={'ok':False},evaluate_requests=23)])
    assert c['evaluate_requests']==23 and c['fresh_FINAL_calls']==1

def test_reserve_does_not_charge_or_apply_prefix_stage_limit():
    x=owner();x.bucket='prefix';x.elapsed=lambda:{'CPU_s':4.,'wall_s':4.};before=copy.deepcopy(x.counts)
    x.reserve(1832,1864,27,43);assert x.counts==before
    x.counts['geometry_checks']=s.CAPS['geometry_checks']-1863
    with pytest.raises(s.b.BudgetStop,match='RESERVE_geometry'):x.reserve(1832,1864,27,43)

def test_current_root_geometry_count_and_delegation(monkeypatch):
    x=owner();x.active_phase=NS(current_certificate=1);x.orig_margin=lambda *args:-.2;monkeypatch.setattr(s.d,'short',lambda r:{'r':r})
    assert x.geometry(7,'unchanged')==-.2 and x.counts['geometry_checks']==1
    assert [z[0] for z in x.journal.rows]==['BEFORE_GEOMETRY','GEOMETRY_VERDICT']

def test_hold_failure_and_four_raw_fixed_action():
    x=owner();x.hits={};seen=[]
    def raw(st,a,i,k,p):
        seen.append((i,k,a.tobytes()));st['global_raw']+=1;return {'raw':k},'FORCE' if k==2 else None
    x.raw=raw;state={'global_raw':132};a=np.zeros(3,np.float32);rows,reason=x.hold(state,a,34,None)
    assert reason=='FORCE' and len(rows)==len(seen)==2 and state['global_raw']==134
    assert all(z[0]==34 and z[2]==a.tobytes() for z in seen)

def test_negative_gain_is_reported_not_vetoed():
    a=dict(before_raw=210,after_raw=211,COM_speed_m_s=40,interpolated={'yaw':1},margin_after_raw_m=2)
    b=dict(before_raw=192,after_raw=193,COM_speed_m_s=42,interpolated={'yaw':2},margin_after_raw_m=3)
    q=bracket_comparison(a,b);assert q['gain_lower_raw']==-19 and q['gain_upper_raw']==-17 and q['COM_speed_delta_m_s']==-2

def test_checkpoint_contents_from_separate_initial_objects():
    static=s.d.rd(s.INPUTS['static']);x=NS(static=static,ledger=s.d.rd(s.INPUTS['ledger']),paths=s.d.rd(s.INPUTS['paths']));a=s.d.Study.initial(x);b=s.d.Study.initial(x)
    assert a['root'].roads is not b['root'].roads and s.d.canonical(s.d.Study.checkpoint(x,a))==s.d.canonical(s.d.Study.checkpoint(x,b))
