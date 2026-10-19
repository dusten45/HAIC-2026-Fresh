"""Fixed pair construction/selection; no simulator imports."""
import numpy as np
def net(a):return float(a[1]) if a[1]>0 else -float(a[2])
def fixed_pairs(base,modified):
    steers=[('base',np.float32(base[0])),('shifted',np.float32(modified[0]))]
    steers.sort(key=lambda q:float(q[1]))
    if steers[0][1].tobytes()==steers[1][1].tobytes():raise ValueError('TWO_DISTINCT_STEERS_REQUIRED')
    lock=np.float32(.9)
    if float(lock)<.9:lock=np.nextafter(lock,np.float32(1.))
    below=np.nextafter(lock,np.float32(0.))
    values=[-1+i/8 for i in range(17)]+[-float(lock),-float(below),net(base),net(modified)]
    unique={}
    for v in values:
        u=np.float32(v);u=np.float32(0.) if u==0 else u
        if not -1<=u<=1:raise ValueError('PEDAL_DOMAIN')
        unique[u.tobytes()]=float(u)
    grid=sorted(unique.values(),reverse=True)
    if len(grid)>21 or len(grid)>24:raise ValueError('GRID_CAP')
    pairs=[]
    for row,steer in steers:
        for u in grid:
            a=np.asarray([steer,max(0.,u),max(0.,-u)],np.float32)
            pairs.append(dict(index=len(pairs),row=row,u=u,action=a))
    if len({q['action'].tobytes() for q in pairs})!=len(pairs):raise ValueError('DUPLICATE_PAIR')
    return pairs,grid
def select(entries,target):
    feasible=[q for q in entries if q['row']=='shifted' and q['report']['ok']]
    return min(feasible,key=lambda q:(abs(q['u']-target),-q['u'],q['index'])) if feasible else None
def search(pairs,target,certify,reserve,record):
    entries=[]
    for i,p in enumerate(pairs):
        reserve(len(pairs)-i)
        a=p['action'].copy();bits=a.tobytes();report=certify(a)
        if a.tobytes()!=bits:raise RuntimeError('CERTIFIER_MUTATED_PAIR')
        q=dict(p,report=report);entries.append(q);record(q)
    best=select(entries,target)
    if best is None:return entries,None,None
    reserve(0)
    a=best['action'].copy();bits=a.tobytes();final=certify(a)
    if a.tobytes()!=bits or not final['ok']:raise RuntimeError('FRESH_FINAL_FAILED_NO_RETRY')
    return entries,best,final
def pipeline(zero,joint):
    zero() # Any exception aborts before joint, no retry/fallback.
    return joint()
def pure_checks(reserve_stub):
    a=np.asarray([.1,.5,-0.],np.float32);b=np.asarray([.11,.625,0.],np.float32)
    pairs,grid=fixed_pairs(a,b)
    assert len(grid)<=21 and len(pairs)<=42 and len({p['action'].tobytes() for p in pairs})==len(pairs)
    assert sum(u==0 for u in grid)==1
    worst,wgrid=fixed_pairs(np.asarray([.1,.54321,0.],np.float32),np.asarray([.11,.65432,0.],np.float32))
    assert len(wgrid)==21 and len(worst)==42
    assert [q['u'] for q in pairs if q['row']=='base']==[q['u'] for q in pairs if q['row']=='shifted']
    seen=[];reservations=[]
    def cert(x):seen.append(x.tobytes());return dict(ok=True)
    entries,best,final=search(pairs,.625,cert,lambda n:reservations.append(n),lambda q:None)
    assert seen[:-1]==[p['action'].tobytes() for p in pairs] and seen[-1]==best['action'].tobytes()
    assert len(seen)==len(pairs)+1 and final is not entries[best['index']]['report']
    assert reservations==list(range(len(pairs),-1,-1))
    ties=[dict(row='shifted',u=.25,index=4,report={'ok':True}),dict(row='shifted',u=.75,index=3,report={'ok':True}),dict(row='shifted',u=.75,index=1,report={'ok':True})]
    assert select(ties,.5)['index']==1
    reserve_stub()
    called=[]
    def fail():called.append('zero');raise RuntimeError('STUB_INTEGRITY')
    try:pipeline(fail,lambda:called.append('FORBIDDEN_JOINT'))
    except RuntimeError:pass
    else:raise AssertionError('ERROR_SWALLOWED')
    assert called==['zero']
    calls=[]
    def fault(x):calls.append(1);raise RuntimeError('STUB_TECHNICAL')
    try:search(pairs,.625,fault,lambda n:None,lambda q:None)
    except RuntimeError:pass
    else:raise AssertionError('ERROR_RETRIED')
    assert len(calls)==1
    return dict(passed=True,checks=['exact_float32_dedup_and_maximum','same_grid_and_fixed_order_both_rows',
        'actual_final_pair_passed_to_certifier','fresh_FINAL_not_original_or_grid_report_reuse',
        'tie_distance_then_higher_u_then_index','whole_budget_reserved_before_zero',
        'technical_failure_aborts_all_no_retry'],real_choose=0,model=0,force=0,geometry=0)
