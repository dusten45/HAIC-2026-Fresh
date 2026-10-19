"""Read-only audit of model feasibility and frozen-tail/feedback transfer."""
import json,time
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write
from retry.path569_design import capsule,sha

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response569-private');rd=lambda p:json.loads(p.read_text())

def main():
    cpu,wall=time.process_time(),time.perf_counter();result=rd(G/'retry/path569_result.json');cache=rd(D/'stored-model-private.json');linear={k:np.asarray(v) for k,v in cache['linear'].items()};env={k:np.asarray(v) for k,v in cache['envelope'].items() if k!='rule'};seed=cache['seed'];x0=np.asarray(seed['x']);p0=np.asarray(seed['P']);g0=np.asarray(seed['g']);labels=np.asarray(cache['labels']);tape=rd(Path('/workspace/haic-response565-private/final-tape-private.json'));commands={q['index']:np.asarray(q['action']) for q in tape['commands']};items=[]
    for e in result['events']:
        if not e.get('source_evaluated'):continue
        label=e['label'];probe=rd(D/(label+'-diagnostic-private.json'));fb=rd(D/(label+'-feedback-private.json'));dx=np.asarray(probe['x'])-x0;scale=np.tile([.003,.03],20);t=float(max(abs(dx/scale)));p=np.asarray([r['root_without_roads']['center'] for r in probe['rows']]);ppred=p0+np.einsum('ijk,k->ij',linear['P'],dx);position_excess=np.linalg.norm(p-ppred,axis=1)-env['position']*t;scalar_excess=g0+linear['J']@dx-probe['g']-env['g']*t
        violations={str(k):int(sum(scalar_excess[labels==k]>1e-8)) for k in set(labels) if k!='path'}
        excess_max={str(k):float(max(0.,max(scalar_excess[labels==k]))) for k in set(labels) if k!='path'}
        changed_steer=changed_pedal=0;maxsteer=maxpedal=0.
        for q in fb['commands']:
            old=commands[q['index']];new=np.asarray(q['action']);changed_steer+=int(old[0]!=new[0]);changed_pedal+=int(any(old[1:]!=new[1:]));maxsteer=max(maxsteer,abs(float(old[0]-new[0])));maxpedal=max(maxpedal,float(max(abs(old[1:]-new[1:]))))
        allrows=probe['rows'][:80]+fb['rows'];stats=dict(min_footprint_margin=min(r['margin'] for r in allrows),max_path_distance=max(r['path_error'] for r in allrows),max_force_ratio=max(f['ratio'] for r in allrows for f in r['forces']),max_reference_overspeed=max(r['reference_overspeed'] for r in allrows),max_body=max(r['body'] for r in allrows),final_tracking_history=fb['checkpoint']['tracking'])
        items.append(dict(label=label,zero_step_seed_included=e['model']['precheck']['exact_seed_included'],model_capsule_residual=e['model']['capsule_model_violation'],predicted_hull_gain_ms=e['model']['predicted_gain_ms'],actual_saved_tail_gain_ms=1000*(result['seed_times']['hull_finish']-probe['times']['hull_finish']),fresh_feedback_gain_ms=e.get('diagnostic_gain_ms'),feedback_minus_saved_tail_ms=1000*(e['actual_times']['hull_finish']-probe['times']['hull_finish']),position_envelope_excess_max_m=float(max(position_excess)),scalar_envelope_exceedances=violations,scalar_envelope_excess_max_by_label=excess_max,closed_loop_commands_changed=dict(steering=changed_steer,pedal=changed_pedal,max_abs_steer_delta=maxsteer,max_abs_pedal_delta=maxpedal),exact_safety=stats,official_candidate_raw=e['official_candidate_raw'],confirmation_raw=e['confirmation_raw']))
    modes={}
    with open(D/'raw-journal-private.jsonl') as f:
        for line in f:
            r=json.loads(line)
            if r['kind']=='SOURCE_PATH_RECHECK':
                key='diagnostic' if r['diagnostic'] else 'strict_candidate';v=modes.setdefault(key,dict(raws=0,active_segment_changes=0,frozen_ineligible=0,path_failures=0));v['raws']+=1;v['active_segment_changes']+=int(r.get('segment_changed',False));v['frozen_ineligible']+=int(r.get('frozen_segment_eligible') is False);v['path_failures']+=int(not r['path_pass'])
    contract=rd(G/'retry/path569_contract.json');audit=rd(G/'retry/path569_audit.json');checks=dict(source_hashes_match=all(sha(G/p)==h for p,h in contract['source_sha256'].items()),verification_source_matches=sha(G/'retry/path569_verify.py')==audit['validation_source_sha256'],all_model_zero_steps_seed_feasible=all(q['zero_step_seed_included'] for q in items),all_new_candidates_safe_finish=all(e.get('safe_finish',False) for e in result['events'] if e.get('source_evaluated')),new_safe_candidate_full_replay_exact=result['independent_verification']['fullstate_force_history_tracker_exact'],existing_seed_whole_not_repeated=not result['existing_whole_replay_repeated'])
    out=dict(checks=checks,candidates=items,source_projection_rechecks=modes,inference='Finite-segment/vector path repair admitted two globally safe programs and safe actual existing-feedback finishes. The frozen-tail diagnostic gains did not transfer to the recomputed feedback controls from the same altered handoff. No source official raw improvement or working acceptance. This isolates frozen-policy-to-feedback value mismatch as the next issue; it is not a proof of control-direction infeasibility.',empirical_error_note='Displacement envelopes preserve the exact seed and avoid impossible fixed margins. They remain empirical, not certified bounds; any exceedances are recorded above and exact source safety remains authoritative.',model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    atomic_write(G/'retry/path569_analysis.json',out);ledger=rd(G/'retry/path569_cost.json');ledger['read_only_analysis']=dict(ticks=0,CPU_s=out['CPU_s'],wall_s=out['wall_s']);atomic_write(G/'retry/path569_cost.json',ledger,True);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
