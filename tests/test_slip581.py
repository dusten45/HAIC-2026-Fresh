"""Source-free formula, prefix adapter, cost and hold-stop checks."""
import copy,math,json
from collections import Counter
from types import SimpleNamespace
import numpy as np
import pytest
import retry.slip581_model as s
from retry.slip581_math import alignment,branch_equal

@pytest.fixture(autouse=True)
def forbid_source(monkeypatch):
    def no(*a,**k):raise AssertionError('UNEXPECTED_SOURCE_OR_FORCE')
    monkeypatch.setattr(s.d,'source_tick',no);monkeypatch.setattr(s.d,'force_rows',no)


def root(v=(0.,10.),angle=0.,offsets=((0.,0.),(0.,0.))):
    return {'planar':{'angle':angle,'yaw':0.,'joints':[0.,0.,0.,0.],'rates':[0.,0.,0.,0.],'linear':{'velocity':v,'wheels':[{'offset':z,'heading':0.,'friction':400.} for z in (*offsets,(0.,0.),(0.,0.))]}}}


def test_sign_and_angle_once():
    a=alignment(root(angle=.2),[.3,0.]);assert a[0]==np.float32(.2) and a[1]==np.float32(.3) and a[2]==0
    a=alignment(root(v=(-1.,10.)),[0.,.125]);assert a[0]<0


def test_each_wheel_offset_and_circular_mean():
    r=root(offsets=((3.,0.),(-1.,0.)));a=alignment(r,[0.,0.]);theta=[math.atan2(-3.,10.),math.atan2(1.,10.)];expected=-math.atan2(sum(math.sin(t) for t in theta),sum(math.cos(t) for t in theta))
    assert a[0]==np.float32(expected) and a[0]!=0
    assert alignment(root(angle=1.),[0.,0.])[0]==np.float32(.4)


def test_zero_or_singular_velocity_domain():
    with pytest.raises(RuntimeError,match='VELOCITY'):alignment(root(v=(0.,0.)),[0.,0.])
    with pytest.raises(RuntimeError,match='MEAN'):alignment(root(offsets=((0.,0.),(0.,-20.))),[0.,0.])
    with pytest.raises(RuntimeError):alignment(root(v=(math.nan,1.)),[0.,0.])


def test_stored_parent_formula_matches_pure580_and_pedals_unchanged():
    prefix=s.d.rd(s.INPUTS['prefix']);tape=s.d.rd(s.INPUTS['tape']);p=prefix['expected_available_end_state']['root'];pedals=next(r['action'][1:] for r in tape['commands'] if r['index']==32);a=alignment(p,pedals)
    assert np.asarray(a[1:],np.float32).tobytes()==np.asarray(pedals,np.float32).tobytes()
    assert np.all(np.isfinite(a)) and abs(a[0])<=np.float32(.4)
    # Evaluate geometry formula only, never the state transition/force.
    angles=[math.atan2(-(p['planar']['linear']['velocity'][0]+w['offset'][0]),p['planar']['linear']['velocity'][1]+w['offset'][1]) for w in p['planar']['linear']['wheels'][:2]]
    theta=math.atan2(sum(map(math.sin,angles)),sum(map(math.cos,angles)));q=math.atan2(math.sin(theta-p['planar']['angle']),math.cos(theta-p['planar']['angle']))
    assert a[0]==np.float32(-max(-.4,min(.4,q)))


def test_prefix_adapter_normalizes_tuple_json_and_detects_mismatch():
    p=s.d.rd(s.INPUTS['prefix']);e=p['branch_expected_rows'][0];t=s.d.rd(s.INPUTS['tape'])['rows'][96]
    row=dict(action=e['action'],index=e['context']['index'],raw=e['context']['raw'],global_raw_before=e['context']['global_raw'],global_raw_after=e['context']['global_raw']+1,episode_before_s=t['episode_before_s'],episode_after_s=t['episode_after_s'])
    for key,other in [('before_root_without_roads','before'),('root_without_roads','after'),('forces','forces'),('tracking_history_before','history_before'),('proposed_history','history'),('progress','progress'),('margin','margin'),('path_error','path_error'),('reference_overspeed','reference_overspeed'),('body','body')]:row[key]=copy.deepcopy(e[other])
    row['before_root_without_roads']['center']=tuple(row['before_root_without_roads']['center'])
    assert branch_equal(row,e,t)
    row['proposed_history'][0]+=1;assert not branch_equal(row,e,t)


def toy_owner(monkeypatch,fail=None):
    x=object.__new__(s.Study);x.result={'holds':[]};x.guard=lambda **k:None;monkeypatch.setattr(s,'diagnostic',lambda r:{'yaw':r.get('yaw',0)})
    monkeypatch.setattr(s.d,'short',lambda r:r)
    state={'root':{'yaw':0},'global_raw':124,'progress':121.,'tracking':[0,112],'launch':[55,384]};seen=[]
    def raw(st,action,index,k,phase):
        seen.append((index,k,action.tobytes()));row={'index':index,'raw':k,'global_raw_before':st['global_raw']}
        if k==fail:return row,'FORCE'
        st['global_raw']+=1;st['progress']+=1;return row,None
    x.raw=raw;return x,state,seen


def test_hold_fixed_four_raw_and_absolute_index(monkeypatch):
    x,state,seen=toy_owner(monkeypatch);a=np.array([.1,.2,0],np.float32);rows,failure=x.hold(state,a,32,None)
    assert failure is None and len(rows)==4 and all(z[0]==32 and z[2]==a.tobytes() for z in seen) and state['global_raw']==128


def test_first_failure_stops_before_further_tick(monkeypatch):
    x,state,seen=toy_owner(monkeypatch,fail=2);rows,failure=x.hold(state,np.zeros(3,np.float32),32,None)
    assert failure=='FORCE' and len(rows)==len(seen)==2 and state['global_raw']==125


def test_actual_force_call_accounting_without_integrator():
    x=object.__new__(s.Study);x.counts=Counter();x.stage_counts={};x.bucket='intervention';x.guard=lambda **k:None
    for _ in range(4):x.wheel_call('external_force',lambda:None)
    assert x.counts['external_force']==4 and x.counts['internal_force']==x.counts['completed_model_ticks']==0


def test_replay_checkpoint_content_not_road_object_identity():
    static=s.d.rd(s.INPUTS['static']);owner=SimpleNamespace(static=static,ledger=s.d.rd(s.INPUTS['ledger']),paths=s.d.rd(s.INPUTS['paths']));a=s.d.Study.initial(owner);b=s.d.Study.initial(owner)
    assert a['root'].roads is not b['root'].roads and s.d.canonical(s.d.Study.checkpoint(owner,a))==s.d.canonical(s.d.Study.checkpoint(owner,b))


def test_future_stage_reserve_does_not_consume_current_stage_allowance():
    x=object.__new__(s.Study);x.contract=s.d.rd(s.INPUTS['proposal']);x.counts=Counter(attempted_raw=124,completed_model_ticks=124,external_force=496,internal_force=496,geometry_checks=124);x.bucket='prefix';x.stage_counts={'prefix':Counter(attempted_raw=124)};x.elapsed=lambda:{'CPU_s':4.,'wall_s':4.};x.phase_times=lambda:{'prefix':{'CPU_s':2.,'wall_s':2.}}
    x.reserve(140,11,16)
    assert x.counts['attempted_raw']==124
    with pytest.raises(s.b.BudgetStop):x.reserve(200,11,16)
