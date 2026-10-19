"""One frozen dynamic joint-pair policy. No simulator imports."""
import numpy as np
from retry.pairs607_core import net
class PolicyStop(RuntimeError):pass
def make_pairs(base,modified):
    lock=np.float32(.9)
    if float(lock)<.9:lock=np.nextafter(lock,np.float32(1.))
    below=np.nextafter(lock,np.float32(0.))
    values=[-1+i/8 for i in range(17)]+[-float(lock),-float(below),net(base),net(modified)]
    unique={}
    for v in values:
        u=np.float32(v);u=np.float32(0.) if u==0 else u
        if not -1<=u<=1:raise ValueError('608_PEDAL_DOMAIN')
        unique[u.tobytes()]=float(u)
    grid=sorted(unique.values(),reverse=True)
    assert len(grid)<=21 and len(grid)<=24
    steers=sorted([('base',base[0]),('shifted',modified[0])],key=lambda q:float(q[1]))
    pairs=[];seen={}
    for row,s in steers:
        for u in grid:
            a=np.asarray([s,max(0.,u),max(0.,-u)],np.float32);bits=a.tobytes()
            if bits in seen:
                pairs[seen[bits]]['rows'].append(row)
            else:
                seen[bits]=len(pairs);pairs.append(dict(index=len(pairs),row=row,rows=[row],u=u,action=a))
    assert len(pairs)<=42 and len({q['action'].tobytes() for q in pairs})==len(pairs)
    return pairs,grid
def signature(pairs):return [(q['row'],q['u'],q['action'].tobytes().hex()) for q in pairs]
def zero(meta):return meta['offset']==0. and meta['pedal_residual']==0.
def select(entries,base,target):
    fallback=next((q for q in entries if 'base' in q['rows'] and q['action'].tobytes()==base.tobytes()),None)
    if fallback is None or not fallback['report']['ok']:raise PolicyStop('BASE_ROW_ORIGINAL_ACTION_NOT_SAFE')
    eligible=[q for q in entries if 'shifted' in q['rows'] and q['report']['ok']]
    if eligible:return min(eligible,key=lambda q:(abs(q['u']-target),-q['u'],q['index'])),'shifted'
    return fallback,'base_fallback'
def batch(base,modified,certify,reserve,record):
    pairs,grid=make_pairs(base,modified);entries=[]
    for i,q in enumerate(pairs):
        reserve(len(pairs)-i);a=q['action'].copy();bits=a.tobytes();report=certify(a)
        assert a.tobytes()==bits
        value=dict(q,report=report);entries.append(value);record(value)
    best,branch=select(entries,base,net(modified));reserve(0)
    a=best['action'].copy();bits=a.tobytes();final=certify(a)
    if not final['ok'] or a.tobytes()!=bits:raise RuntimeError('608_FRESH_FINAL_FAILURE')
    return a,final,entries,branch
def dispatch(original,modify,joint):
    a,report,frames=original()
    if a is None:raise PolicyStop('INCUMBENT_NO_ADMISSIBLE_ACTION')
    modified,meta=modify(a)
    if zero(meta):
        assert modified.tobytes()==a.tobytes()
        return a,report,frames,[], 'zero_residual_original_FINAL'
    return joint(a,modified,meta)
def pure_checks(restore,clone,reserve):
    a=np.asarray([.1,.54321,0.],np.float32);b=np.asarray([.11,.65432,0.],np.float32)
    pairs,grid=make_pairs(a,b);assert len(grid)==21 and len(pairs)==42
    other,gg=make_pairs(a,np.asarray([.11,.77777,0.],np.float32));assert net(b) not in gg and net(a) in gg
    seen=[];calls=[]
    def cert(x):seen.append(x.tobytes());return dict(ok=x.tobytes()==a.tobytes())
    chosen,final,entries,branch=batch(a,b,cert,lambda n:calls.append(n),lambda q:None)
    assert branch=='base_fallback' and chosen.tobytes()==a.tobytes() and len(seen)==43
    assert seen[:-1]==[q['action'].tobytes() for q in pairs] and calls==list(range(42,-1,-1))
    assert final is not next(q['report'] for q in entries if q['action'].tobytes()==a.tobytes())
    tie=[dict(rows=['shifted'],u=.25,index=4,action=b,report={'ok':True}),dict(rows=['shifted'],u=.75,index=2,action=b,report={'ok':True}),dict(rows=['shifted'],u=.75,index=1,action=b,report={'ok':True})]
    tie.append(dict(rows=['base'],u=net(a),index=0,action=a,report={'ok':True}))
    assert select(tie,a,.5)[0]['index']==1
    collapsed,cg=make_pairs(a,np.asarray([a[0],.65432,0.],np.float32));assert len(collapsed)==21 and all(q['rows']==['base','shifted'] for q in collapsed)
    called=[]
    def original():called.append('original');return a,{'ok':True},'frames'
    out=dispatch(original,lambda v:(v.copy(),dict(offset=0.,pedal_residual=0.)),lambda *v:called.append('BAD_BATCH'))
    assert out[0].tobytes()==a.tobytes() and called==['original']
    def failure():called.append('failed');raise RuntimeError('STUB_TECHNICAL')
    try:dispatch(failure,lambda v:called.append('BAD_MODIFY'),lambda *v:called.append('BAD_BATCH'))
    except RuntimeError:pass
    else:raise AssertionError('ERROR_SWALLOWED')
    assert called==['original','failed']
    restore();clone();reserve()
    return dict(passed=True,checks=['restore_raw160_all_fields_and_latch','one_original_call_and_error_whole_stop',
        'dynamic_current_pedal_grid_exact_dedup_and_order','actual_pair_before_certificate_fresh_FINAL',
        'closest_then_higher_pedal_then_fixed_index','base_fallback_only_freshly_safe_original_action',
        'zero_region_original_bytes_no_joint_batch','coincident_steer_dedup_membership_no_new_candidate',
        'independent_clones','next_call_replay_cleanup_reservations'],real_choose=0,model=0,force=0,geometry=0)
