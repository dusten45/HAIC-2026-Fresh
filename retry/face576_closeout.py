"""No-solve closeout after576 result I/O failure; direct contradiction proof."""
import shutil,time
from pathlib import Path
import numpy as np
from retry.algebra575_diagnose import ROOT,read,write,sha
from retry.algebra575_isolate import load
from retry.face576_math import active_face
from retry.causal575_rounding import effective_uncertainty,numerical_margin

PRIVATE=Path('/workspace/haic-response576-recovery-private')

def main():
    cpu,wall=time.process_time(),time.perf_counter();contract=read(ROOT/'retry/face576_contract.json');prior=read(ROOT/'retry/face576_cost.json');pre=read(ROOT/'retry/face576_preflight.json')
    # Do not relaunch the completed algebra or infer its non-durable solver status.
    assert (PRIVATE/'STARTED.json').exists() and not (PRIVATE/'ERROR-private.json').exists()
    assert not (PRIVATE/'raw-journal-private.jsonl').exists() and not (PRIVATE/'algebra-candidate-private.json').exists()
    assert prior['total']['ticks']==0 and prior['total']['force']==0
    p,fixed,q,box=active_face(load());_,_,mag=effective_uncertainty(p);N=264;G=132;row=2893;a=p['A'][row,:N];u=p['A'][row,N:];group=int(np.flatnonzero(u)[0]);end=2*(group+1);assert np.all(a[end:]==0) and np.count_nonzero(u)==1
    # ±z_j-t_j <= -q_j and causal monotonicity imply
    # |z_j|+q_j <= t_group. Fixed coordinates contribute exactly zero.
    free=~fixed[:end];coeff=abs(a[:end][free]).astype(np.longdouble);qq=q[:end][free].astype(np.longdouble);L=np.longdouble(u[group]);slope=L-sum(coeff);assert slope>0
    tmin=max(qq);lower=slope*tmin+coeff@qq
    gamma=400*np.finfo(float).eps/(1-400*np.finfo(float).eps);margin=float(abs(a)@q);numerical=float(numerical_margin(p['A'][row:row+1],p['b'][row:row+1],mag,gamma)[0]);rhs=np.longdouble(p['b'][row])-np.longdouble(margin)-np.longdouble(numerical)
    error=16*(end+8)*np.finfo(float).eps*(float(abs(L)*tmin+sum(coeff)*tmin+coeff@qq+abs(rhs))+1e-300);gap=lower-rhs
    proof=dict(row=row,global_raw=458,force_wheel_index=2,causal_controls=end,fixed_contribution=0.,error_coefficient=float(L),free_J_L1=float(sum(coeff)),positive_slope=float(slope),aux_lower_from_free_rounding=float(tmin),original_rhs=float(p['b'][row]),row_rounding_margin=margin,numerical_margin=numerical,tightened_rhs=float(rhs),relaxed_lhs_lower=float(lower),strict_gap=float(gap),conservative_arithmetic_allowance=error,verified_contradiction=bool(gap>error),formula='L*t+a*z >= (L-sum_free(abs(a)))*max_free(q)+sum_free(abs(a)*q) > b-margin-numerical. Fixedz=q=0;futureJacobian0. Numeric monotonic tightening only strengthens this relaxed proof.',LP_solves=0,source_ticks=0)
    assert proof['verified_contradiction'] and pre['all_pass'] and pre['same_predetermined_575_mask_exact']
    write(ROOT/'retry/face576_algebra_certificate.json',proof)
    checks=dict(source_hashes_match=all(sha(ROOT/s)==h for s,h in contract['source_sha256'].items()),input_hashes_match=all(sha(Path(s))==h for s,h in contract['input_sha256'].items()),frozen_contract_pin=sha(ROOT/'retry/face576_contract.json')==read(PRIVATE/'STARTED.json')['contract_sha256'])
    assert all(checks.values())
    shutil.copy2(ROOT/'retry/face576_cost.json',PRIVATE/'finally-before-storage-error-cost-private.json');shutil.copy2(Path('/workspace/face576-recovery-stdout-private.txt'),PRIVATE/'finalizer-error-stdout-private.txt')
    # One conservative second covers the separate0.206s read-only proof probe and
    # interpreter/startup work. The seven-second prior charge already includes the
    # original classification failure and both unit-test runs; do not add it twice.
    cost=dict(total=dict(ticks=0,force=0,geometry=0,CPU_s=prior['total']['CPU_s']+1+time.process_time()-cpu,wall_s=prior['total']['wall_s']+1+time.perf_counter()-wall),preflight_test_classification_CPU_wall_charge_s=7.,postprocess_probe_CPU_wall_charge_s=1.,initial_completed_algebra_cost=prior['total'])
    assert cost['total']['CPU_s']<120 and cost['total']['wall_s']<180
    result=dict(completed=True,stop_reason='ACTIVE_FACE_TUBE_DIRECT_CONTRADICTION_SOURCE0',execution_finalizer_error='FileExistsError: prior classification result was preserved but not moved before create-only final result writer. No algebra/source rerun.',execution_finalizer_error_preserved=True,solver_status_available=False,LP_count_exact_available=False,LP_solves=None,LP_solve_upper_bound=8,additional_LP_solves_for_closeout=0,algebra_returned_new_point=False,new_rounded_candidate_count=0,new_predicted_gain_s=None,seed_predicted_gain_s=0.,source_candidates=0,independent_replays=0,strict_verification_needed=False,source_ticks=0,actual_actions=0,HOLDOUT=0,SEALED=0,new_FD=0,new_calibrations=0,new_resets=0,new_worlds=0,new_seeds=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,active_face_count=1,fixed_count=40,exact_domain_endpoints=33,adjacent_float32_values=7,free_count=224,same_predetermined_575_mask_exact=True,safe_working_accept=False,official_promotion=False,official_incumbent_candidate_raw=660,official_incumbent_finish_s=13.20,seed_hull_s=13.19360251036074,direct_certificate=proof,cost=cost,**checks,scope='Single predetermined57540coordinateface. Nootherendpointcombination,roundingrepair,envelopereduction,ornewsource. Failureisconditionalmodeltubeconservatism,nottruesourcesafetyfailureororiginalfeasiblesetimpossibility.',closeout_source_sha256=sha(Path(__file__)))
    write(ROOT/'retry/face576_cost.json',cost);write(ROOT/'retry/face576_result.json',result);print(result)

if __name__=='__main__':main()
