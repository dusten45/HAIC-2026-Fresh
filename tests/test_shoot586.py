"""Source-free representability, incomplete constraints, FD, cache and reserve checks."""
import json,math
from collections import Counter
from types import SimpleNamespace as NS
import numpy as np
import pytest
import retry.shoot586_model as s
from retry.shoot586_math import *

@pytest.fixture(autouse=True)
def forbid_source(monkeypatch):
    def no(*a,**k):raise AssertionError('UNEXPECTED_SOURCE_OR_FORCE')
    monkeypatch.setattr(s.d,'source_tick',no);monkeypatch.setattr(s.d,'force_rows',no)

def test_incumbent_all50_individual_coordinates_representable():
    tape=s.d.rd(s.INPUTS['tape']);cmd={q['index']:np.array(q['action'],np.float32) for q in tape['commands']};x=seed_controls(cmd)
    assert x.shape==(50,) and np.array_equal(canonical(np.zeros(50),x),x)
    assert all(action(x,i).tobytes()==cmd[i].tobytes() for i in range(25,50))
    for j in range(50):
        y,h,sign=fd_point(x,j);assert h==(y[j]-x[j])/SCALE[j] and h!=0 and np.count_nonzero(y!=x)==1
        assert command_key(y)!=command_key(x)

def test_signed_pedal_domain_and_quantized_cache_key():
    seed=np.zeros(50);x=canonical(np.full(50,1e6),seed);assert np.array_equal(x,DOMAIN)
    assert action(x,25)[1]==1 and action(x,25)[2]==0
    x[1]=-1;assert action(x,25)[1]==0 and action(x,25)[2]==1
    assert command_key(canonical(np.zeros(50),seed))==command_key(canonical(np.full(50,1e-50),seed))
    y,h,sign=fd_point(DOMAIN.copy(),0);assert sign==-1 and h<0 and abs(y[0])<=DOMAIN[0]

def test_fixed_dimension_unobserved_constraints_are_inadmissible():
    row=dict(global_raw_before=96,forces=[{'ratio':.5}]*4,proposed_history=[0,4])
    g=residuals([row],False,False).reshape(-1)
    assert len(g)==1718 and all(g[:4]==1.059-.5) and g[4]==1 and all(g[5:]==-1)
    assert objective(False,None,4.95,1)>5.95

def test_full_seed_residuals_not_excluded_by_surrogate_tube():
    rows=s.d.rd(s.INPUTS['tape'])['rows'][96:252];g=residuals(rows,True,True)
    assert min(g)>=0 and len(g)==1718 and g[-1]==g[-2]==1
    bad=[dict(rows[0],body=100.)];assert residuals(bad,False,False)[10]==0
    # Strict eligibility is separate, never inferred from g>=0 alone.
    assert not (bad[0]['body']<100.)

def test_continuous_improvement_numeric_resolution_not_performance_gate():
    assert faster(4.95-1e-8,4.95) and not faster(math.nextafter(4.95,-math.inf),4.95)
    assert numeric_resolution(4.95,4.95)==32*math.ulp(4.95)

def test_cache_hit_precedes_source_call_cap():
    x=object.__new__(s.Study);controls=np.zeros(50);case={'safe':True};x.cache={command_key(controls):case};x.cache_requests=0;x.cache_hits=0;x.cases=128
    assert x.evaluate_x(controls,'FD') is case and x.cache_hits==1
    other=controls.copy();other[0]=.1
    with pytest.raises(s.OptimizationStop,match='SUFFIX_CALL_CAP'):x.evaluate_x(other,'proposal')

def test_reserved_whole_replay_does_not_consume_positive_stage_allowance():
    x=object.__new__(s.Study);x.guard=lambda **k:None;x.counts=Counter(attempted_raw=252,completed_model_ticks=252,external_force=1008,internal_force=1008,geometry_checks=253);x.elapsed=lambda:{'CPU_s':10.,'wall_s':10.};before=x.counts.copy();x.reserve(1480,1483,65,105);assert x.counts==before
    x.counts['attempted_raw']=22000-1479
    with pytest.raises(s.b.BudgetStop,match='RESERVE_attempted_raw'):x.reserve(1480,1483,65,105)

def test_checkpoint_clone_full_mutable_isolation():
    static=s.d.rd(s.INPUTS['static']);x=NS(static=static,paths=s.d.rd(s.INPUTS['paths']),ledger=s.d.rd(s.INPUTS['ledger']));a=s.d.Study.initial(x);b=s.clone(a);s.isolated(a,[b]);s.immutable(a['root']);assert s.d.canonical(s.d.Study.checkpoint(x,a))==s.d.canonical(s.d.Study.checkpoint(x,b));b['tracking'][0]=99;assert a['tracking'][0]==0

def test_body100_case_rejection_after_exactly_one_completed_toy_step(monkeypatch):
    class Log:
        def __init__(self):self.rows=[]
        def append(self,kind,**data):self.rows.append(kind);return str(len(self.rows))
    owner=NS(journal=Log(),count=lambda *a:None);phase=s.Phase(owner,'test');root={'r':1};after={'r':2};monkeypatch.setattr(s.d,'short',lambda r:r);monkeypatch.setattr(s.d,'source_tick',lambda *a:after);monkeypatch.setattr(s.b.base,'body',lambda r:100.)
    phase.pending=dict(root_id=s.digest(root),action=[0,0,0],event='e',context={},identity={})
    with pytest.raises(s.BodyStop) as exc:phase.tick(root,0.,0.,None,phase.counter)
    assert exc.value.after is after and owner.journal.rows==['BEFORE_TICK','AFTER_TICK'] and phase.pending is None

def test_pure_solver_warmup_uses_no_source():
    result=s.warm_solver();assert result['pure_numerical'] and result['source_ticks']==0 and result['minimize_calls']==1


def test_nonfinite_proposal_and_residual_are_hard_expression_errors():
    with pytest.raises(ExpressionStop,match='NONFINITE_CONTROL'):canonical(np.full(50,np.nan),np.zeros(50))
    row=dict(global_raw_before=96,forces=[{'ratio':math.inf}]*4,proposed_history=[0,4])
    with pytest.raises(ExpressionStop,match='NONFINITE_RESIDUAL'):residuals([row],False,False)
