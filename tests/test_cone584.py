"""Source-free physical cone identities, float32 projection and execution bounds."""
import copy,math,atexit,json,os
from pathlib import Path
from types import SimpleNamespace as NS
from collections import Counter
import numpy as np
import pytest
import retry.cone584_model as s
from retry.cone584_math import cone,virtual_ratio,select,wheel_formula,COUNTS,LawStop

if os.environ.get('CONE584_TEST_COUNTS'):
    atexit.register(lambda:Path(os.environ['CONE584_TEST_COUNTS']).write_text(json.dumps(dict(COUNTS))))

@pytest.fixture(autouse=True)
def forbid_source(monkeypatch):
    def no(*a,**k):raise AssertionError('UNEXPECTED_SOURCE_OR_FORCE')
    monkeypatch.setattr(s.d,'source_tick',no);monkeypatch.setattr(s.d,'force_rows',no)

def root():
    return {'planar':{'angle':0.,'yaw':0.,'joints':[0.]*4,'rates':[0.]*4,'linear':{'velocity':[0.,10.],'engine_multiplier':1.,'wheels':[{'omega':10/.54,'gas':0.,'heading':0.,'friction':400.,'offset':[0.,0.]} for _ in range(4)]}}}

def test_exact_force_circle_cone_and_inward_float32_projection():
    r=root();p=r['planar'];p['linear']['velocity']=[0.,20.]
    for wheel in p['linear']['wheels']:wheel['omega']=20/.54
    w=p['linear']['wheels'][0];a,d=select(r,np.array([-.4,.2,0],np.float32));q=-float(a[0])
    assert 0<q<.4 and a[1:].tobytes()==np.array([.2,0],np.float32).tobytes()
    assert max(d['virtual_target_force_ratios'])<=1 and all(x<=q<=y for z in d['front_intervals_rad'] for x,y in z)
    V=20.;expected=2*math.asin((400/82)/(2*V));assert abs(d['common_intervals_rad'][0][1]-expected)<1e-14

def test_sign_geometry_nearest_and_current_force_independent_of_command():
    r=root();a,d=select(r,np.array([.1,0,0],np.float32));assert a[0]==np.float32(.1) and d['projected_distance_rad']==0
    p=r['planar'];w=p['linear']['wheels'][0];before=wheel_formula(p,w,0,0,0);p['steer']=.4;assert wheel_formula(p,w,0,0,0)==before

def test_negative_rolling_zero_and_wrap_components():
    r=root();p=r['planar'];w=p['linear']['wheels'][0]
    assert cone(p,w,-10)==[] and cone(p,w,0)==[]
    p['linear']['velocity']=[0.,0.];assert cone(p,w,0)==[(-.4,.4)]
    p['linear']['velocity']=[0.,10.];p['angle']=math.pi
    # Negative rolling aligns opposite velocity, giving a cone around joint0.
    z=cone(p,w,-10);assert len(z)==1 and z[0][0]<0<z[0][1]
    p['angle']=0;w['friction']=82*19.9;z=cone(p,w,-10);assert len(z)==2 and z[0][1]<z[1][0]

def test_pedal_engine_memory_and_lock_discontinuity():
    r=root();p=r['planar'];w=p['linear']['wheels'][2];w['gas']=.5
    z=wheel_formula(p,w,2,0,0);assert z['omega_braked']==w['omega']
    z=wheel_formula(p,w,2,1,0);expected=w['omega']+.02*40000*.6/1.6/(abs(w['omega'])+5);assert z['omega_braked']==expected
    z=wheel_formula(p,w,0,0,.9);assert z['omega_braked']==0 and abs(z['ratio']-82*10/400)<1e-14

def test_empty_and_nonfinite_are_stops_not_alternative_laws():
    r=root();r['planar']['linear']['wheels'][0]['omega']=1000
    with pytest.raises(LawStop,match='EMPTY_CURRENT'):select(r,np.zeros(3,np.float32))
    r=root();r['planar']['linear']['wheels'][0]['friction']=math.nan
    with pytest.raises(LawStop,match='DOMAIN'):select(r,np.zeros(3,np.float32))
    with pytest.raises(LawStop,match='ACTION_DOMAIN'):select(root(),np.array([0,1,1],np.float32))

def test_frozen_servo_segment_in_same_connected_cone():
    r=root();a,d=select(r,np.array([-.4,0,0],np.float32));target=-float(a[0]);q=0.;lo,hi=d['selected_interval_rad']
    for _ in range(4):q+=max(-.06,min(.06,target-q));assert lo<=q<=hi
    assert 0<q<=target
    for _ in range(4):q+=max(-.06,min(.06,target-q))
    assert q==target

def test_stored_initial_case_formula_only():
    cp=s.d.rd(Path('/workspace/haic-response583-private/prefix-checkpoint-private.json'));static=s.d.rd(s.INPUTS['static']);r=s.d.load_root(dict(cp['root_without_roads'],roads=static['root']['roads']));nominal=s.policy.nominal(r,s.d.rd(s.INPUTS['paths'])['candidate'],cp['progress']);a,d=select(cp['root_without_roads'],nominal)
    assert -float(a[0])==.1409490555524826 and d['path_joint_target_rad']==.3630639314651489 and d['nominal_pedals_unchanged']

def test_future_reservation_does_not_consume_prefix_allowance():
    x=object.__new__(s.Study);x.guard=lambda **k:None;x.counts=Counter(attempted_raw=132,completed_model_ticks=132,external_force=528,internal_force=528,geometry_checks=132);x.pure_work=lambda:350;x.elapsed=lambda:{'CPU_s':6,'wall_s':7};before=x.counts.copy();x.reserve(184,168,20,27);assert x.counts==before
    with pytest.raises(s.b.BudgetStop,match='RESERVE_external'):x.reserve(500,2016,20,27)

def test_hold_stops_first_failure_and_keeps_same_command():
    x=object.__new__(s.Study);x.guard=lambda **k:None;seen=[]
    def raw(st,a,i,k,phase):seen.append((i,k,a.tobytes()));st['global_raw']+=1;return {'raw':k},'PATH' if k==3 else None
    x.raw=raw;state={'global_raw':132};a=np.zeros(3,np.float32);rows,why=x.hold(state,a,34,None)
    assert why=='PATH' and len(rows)==len(seen)==3 and state['global_raw']==135 and all(z[0]==34 and z[2]==a.tobytes() for z in seen)

def test_checkpoint_contents_and_inherited_histories():
    static=s.d.rd(s.INPUTS['static']);x=NS(static=static,ledger=s.d.rd(s.INPUTS['ledger']),paths=s.d.rd(s.INPUTS['paths']));a=s.d.Study.initial(x);b=s.d.Study.initial(x)
    assert a['root'].roads is not b['root'].roads and s.d.canonical(s.d.Study.checkpoint(x,a))==s.d.canonical(s.d.Study.checkpoint(x,b))
