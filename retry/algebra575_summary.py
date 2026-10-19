"""Source0 final evidence, including analytic one-row-plus-box lower bounds."""
import shutil
import numpy as np
from retry.algebra575_diagnose import ROOT,PRIVATE,Budget,read,write,sha
from retry.algebra575_isolate import load

def row_lower_bound(p,box,index):
    """Relax to one physical row, its causal norm, and control box. No solve."""
    a=p['A'][index,:264];c=p['A'][index,264:];ids=np.flatnonzero(c)
    if len(ids)!=1 or c[ids[0]]<=0:return None
    group=int(ids[0]);end=2*(group+1)
    if np.any(a[end:]!=0):return None
    L=float(c[group]);bounds=box[:end];nearest=np.maximum(bounds[:,0],np.minimum(0.,bounds[:,1]));lo=float(max(abs(nearest)));hi=float(box[264+group,1]);knots=np.unique(np.r_[lo,hi,abs(bounds).ravel()]);knots=knots[(knots>=lo)&(knots<=hi)]
    values=[]
    for t in knots:
        z=np.clip(-np.sign(a[:end])*t,bounds[:,0],bounds[:,1]);values.append(np.longdouble(a[:end])@z.astype(np.longdouble)+np.longdouble(L)*t)
    k=int(np.argmin(values));error=16*(end+8)*np.finfo(float).eps*(float(np.sum(abs(a[:end])*np.max(abs(bounds),axis=1)))+abs(L)*hi+abs(p['b'][index])+1e-300)
    return dict(row=index,causal_group=group,causal_controls=end,minimum_LHS=float(values[k]),original_RHS=float(p['b'][index]),minimizing_aux=float(knots[k]),strict_gap=float(values[k]-p['b'][index]),conservative_arithmetic_allowance=error,verified_contradiction=bool(values[k]-p['b'][index]>error),breakpoint_count=len(knots))

def main():
    budget=Budget()
    try:
        p=load();diag=read(ROOT/'retry/algebra575_diagnosis.json');iso=read(ROOT/'retry/algebra575_isolation.json');again=read(ROOT/'retry/algebra575_recheck.json');oldcontract=read(ROOT/'retry/wide574_contract.json')
        original=np.load(PRIVATE/'expanded-tube-private.npz');box=original['bounds'];zero_excluded=np.flatnonzero((box[:264,0]>0)|(box[:264,1]<0))
        rows=[row_lower_bound(p,box,i) for i in [2426,2893]]
        const=diag['branches']['tail']['negative_constant_rows']
        proof=dict(row=const[0]['row'],exact_fixed_LHS=0.,tightened_RHS=-const[0]['violation'],original_RHS=const[0]['original_rhs'],rounding_margin=const[0]['rounding'],numerical_margin=const[0]['numerical'],verified_contradiction=const[0]['violation']>0)
        sources=['retry/algebra575_diagnose.py','retry/algebra575_isolate.py','retry/algebra575_recheck.py','retry/algebra575_summary.py','retry/causal575_rounding.py','tests/test_algebra575.py']
        out=dict(completed=True,source_ticks=0,force_evaluations=0,new_FD=0,new_calibrations=0,candidates_executed=0,actual_actions=0,HOLDOUT=0,SEALED=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0,implementation_corrections=1,unit_tests_passed=6,unit_tests_failed=0,unit_tests_real_LP_calls=0,tests_included_in_preflight_charge_s=5,
                 exact_seed_passes_both_original_branches=True,new_rounded_candidate_count=0,new_predicted_gain=None,seed_predicted_gain_s=0.,official_incumbent_raw=660,official_incumbent_s=13.20,seed_hull_s=13.19360251036074,
                 tail_old_constant_contradiction_count=len(const),tail_old_one_row_certificate=proof,expanded_negative_constant_rows=len(diag['branches']['expanded']['negative_constant_rows']),zero_direction_excluded_by_inward_control_bounds=int(len(zero_excluded)),inward_empty=False,expanded_single_physical_row_relaxations=rows,
                 old_sources_unchanged=all(sha(ROOT/k)==h for k,h in oldcontract['source_sha256'].items()),source_sha256={s:sha(ROOT/s) for s in sources},saved_input_hashes_unchanged=all(sha(__import__('pathlib').Path(k))==h for k,h in diag['reconstruction']['inputs'].items()),
                 solve_count=sum(len(v['solves']) for v in [diag,iso,again]),corrected_branches={name:dict(status=v['result']['solver_status'],seed_pass=v['static']['seed']['pass_all'],negative_constant_rows=len(v['static']['negative_constant_rows']),certificate_rows=v['certificate']['row_count'],certificate_gap=v['certificate']['strict_gap'],certificate_error=v['certificate']['conservative_arithmetic_allowance'],certificate_verified=v['certificate']['verified_contradiction']) for name,v in again['branches'].items()},
                 all_certificates_verified=all([proof['verified_contradiction'],again['original_expanded_reduced_certificate']['verified_contradiction'],again['inward_only_certificate']['verified_contradiction']]+[v['certificate']['verified_contradiction'] for v in again['branches'].values()]))
        # Keep detailed original evidence private; public result retains counts and
        # a minimal constant witness rather than hundreds of repeated zero rows.
        shutil.copy2(ROOT/'retry/algebra575_diagnosis.json',PRIVATE/'diagnosis-full-private.json')
        for value in diag['branches'].values():
            full=value['negative_constant_rows'];value['negative_constant_row_count']=len(full);value['negative_constant_rows']=full[:1]
        write(ROOT/'retry/algebra575_diagnosis.json',diag)
        write(ROOT/'retry/algebra575_result.json',out)
    finally:budget.close()
    print(out)

if __name__=='__main__':main()
