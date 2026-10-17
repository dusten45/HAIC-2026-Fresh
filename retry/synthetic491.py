"""Synthetic source regression + JSON scalar gate, no file/world/profile use."""
import json,math
import numpy as np
from retry.projection491 import canonical_projection,terms,CoherentExecutor491
from retry.signed417_executor import canonical_projection as old,CoherentExecutor,ExecutorDomainError

def plain(x):
    if isinstance(x,np.ndarray):return plain(x.tolist())
    if isinstance(x,np.generic):return plain(x.item())
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [plain(v) for v in x]
    return x

def run(charge):
    tests=[]
    obj=dict(i=np.int64(7),u=np.uint64(9),f=np.float64(.5),b=np.bool_(True),a=np.array([1.,-0.]),zero_dim=np.array(3))
    decoded=json.loads(json.dumps(plain(obj),allow_nan=False));assert type(decoded['i']) is int and type(decoded['b']) is bool and decoded['zero_dim']==3 and math.copysign(1,decoded['a'][1])==-1
    for x in [np.float64(float('nan')),np.float64(float('inf'))]:
        try:json.dumps(plain(x),allow_nan=False)
        except ValueError:pass
        else:raise AssertionError('nonfinite JSON accepted')
    tests.append('JSON_numpy_integer_float_bool_array_signedzero_nonfinite_gate')
    def call(fn,line,pos,phase='FIRST_LAP'):
        charge('fixed_calls' if fn is canonical_projection else 'original_calls')
        try:return fn(line,pos,[1.,0.],phase),None
        except ExecutorDomainError as e:return None,str(e)
    tri=np.array([[101.,101.],[102.,99.],[100.,100.]])
    for phase in ['LAUNCH','FIRST_LAP','FINISH_CONFIRM']:
        before,err=call(old,tri,tri[0],phase);after,why=call(canonical_projection,tri,tri[0],phase)
        assert err=='Distinct_or_nonadjacent_projection_ambiguity' and why is None
        assert after['index']==(0 if phase=='LAUNCH' else 2) and after['u']==(0 if phase=='LAUNCH' else 1)
    tests+=['normsquare_endpoint_roundoff_reproduced','closed_seam_all_three_phases']
    charge('term_audits');z=terms(tri,tri[0],[1.,0.]);assert z['raw_u'][-1]<1 and z['u'][-1]==1 and np.array_equal(z['feet'][-1],tri[0])
    dot=np.sum(z['edges']*z['edges'],axis=1);assert np.any(dot!=z['denominator'])
    tests.append('ds_squared_dot_difference_kept_separate')
    tri2=np.roll(tri,1,axis=0);q,e=call(canonical_projection,tri2,tri2[1]);assert e is None and q['index']==1 and q['u']==0
    tests.append('nonseam_shared_vertex_outgoing')
    signed=np.array([[-0.,0.],[4.,0.],[0.,4.]])
    owner=signed.tobytes();q,e=call(canonical_projection,signed,[0.,-0.],'LAUNCH');assert e is None and q['index']==0 and signed.tobytes()==owner
    tests.append('signedzero_numeric_identity_owner_bytes_unchanged')
    # Different closest points, intersecting nonadjacent interiors and
    # adjacent-but-distinct feet must all remain ambiguous.
    fixtures=[(np.array([[-4.,-1.],[4.,-1.],[4.,1.],[-4.,1.]]),[0.,0.]),(np.array([[-2.,-2.],[2.,2.],[-2.,2.],[2.,-2.]]),[0.,0.]),(np.array([[0.,0.],[4.,0.],[0.,4.]]),[1.,1.])]
    for line,pos in fixtures:
        for fn in [old,canonical_projection]:q,e=call(fn,line,pos);assert e=='Distinct_or_nonadjacent_projection_ambiguity'
    tests+=['distinct_nonadjacent_minimizers_rejected','crossing_interiors_rejected','adjacent_distinct_feet_rejected']
    duplicate=np.array([[-0.,0.],[2.,0.],[2.,2.],[0.,-0.],[-2.,2.]])
    q,e=call(canonical_projection,duplicate,[2.,1.]);assert e=='Duplicate_numeric_vertex491'
    tests.append('global_duplicate_vertex_ids_including_signedzero_rejected')
    q,e=call(old,signed,[2.,-.25]);r,f=call(canonical_projection,signed,[2.,-.25]);assert e is f is None and q==r
    tests.append('true_interior_output_unchanged')
    for line,pos in [(np.array([[0.,0.],[1e308,0.],[0.,1.]]),[0.,0.]),(np.array([[0.,0.],[1e-200,0.],[0.,1e-200]]),[0.,0.]),(signed,[float('nan'),0.])]:
        q,e=call(canonical_projection,line,pos);assert e is not None
    tests+=['overflow_underflow_nonfinite_failclosed']
    assert CoherentExecutor491.act.__code__ is CoherentExecutor.act.__code__ and CoherentExecutor.act.__globals__['canonical_projection'] is old
    tests.append('optin_act_code_identity_original_global_unchanged')
    return dict(passed=True,tests=tests,count=len(tests),profile_world_step_reset_seed=0)
