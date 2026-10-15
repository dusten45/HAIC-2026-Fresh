"""Independent archive/OFF/timing/budget checks and fixed motion diagnostics."""
import argparse
import json
import math
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.fallback334_math import rotation,validate
from retry.fallback334_correspondence import stats


def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]


def run(R):
    D=R/'stage334';p=read(D/'plan.json');start,cpu=time.perf_counter(),time.process_time();assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    cfg=read(D/'configs-private.json');original=read(R/'stage330/artifacts-private.json');changes={}
    for kind,modes in cfg.items():
        assert modes['OFF']['members_sha256']==original[kind]['members_sha256']
        changed=[n for n in modes['OFF']['members_sha256'] if modes['OFF']['members_sha256'][n]!=modes['ON']['members_sha256'][n]];assert changed==['retry/temporal_agent.py'];changes[kind]=changed
    count=0;frames=0;motion=[];seen=set();first={}
    for case in p['cases']:
        F=D/case['key'];off=lines(F/'OFF-private.jsonl');on=lines(F/'ON-private.jsonl');recorded=lines(Path(case['folder'])/'trace-private.jsonl');gt={int(k):v for k,v in read(F/'GT-private.json').items()};obs=np.load(case['pixels'])['observations'];assert np.array_equal(obs[1:len(off),:3],obs[:len(off)-1,1:])
        first[case['key']]=next((a['index']+1 for a,b in zip(off,on) if a['action']!=b['action']),None)
        for i,(r,old) in enumerate(zip(off,recorded)):
            action=old['action'] if case['original_fields']=='collection' else old['original_calculated'] if case['original_fields']=='333' else old['calculated330'];memory=old['memory'] if case['original_fields']=='collection' else old['nominal_memory']
            assert r['action']==action and r['features']==old['features'] and r['nominal_memory']==memory;count+=1
            if i and i in gt and i-1 in gt:
                before,now=gt[i-1],gt[i];assert abs(now['time']-before['time']-.08)<1e-9
                import hashlib
                signature=hashlib.sha256(obs[i-1].tobytes()+obs[i].tobytes()+json.dumps(r['tracker']['before'],sort_keys=True).encode()).hexdigest()
                if case['group']=='N2' and signature in seen:continue
                if case['group']=='N2':seen.add(signature)
                t=r['tracker'];delta=.08*(t['previous_yaw']+t['current_yaw'])/2;angle=now['hull']['angle']-before['hull']['angle'];actual=math.atan2(math.sin(angle),math.cos(angle));yawerror=math.atan2(math.sin(delta-actual),math.cos(delta-actual));displacement=rotation(-before['hull']['angle'])@(np.array(now['hull']['position'])-before['hull']['position']);error=np.array([0.,t['current_speed']*.08])-displacement
                motion.append(dict(group=case['group'],road=case['road'],yaw_error=yawerror,lateral_displacement_error=float(error[0]),forward_displacement_error=float(error[1]),displacement_error_norm=float(np.linalg.norm(error))))
        frames+=len(off)
    assert count==1970 and frames==1970;algebra=validate();budget=read(R/'project-effective-budget-v342.json');before=read(R/'project-effective-budget-v341.json')
    for key in ['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']:assert budget[key]==before[key]
    assert budget['actual_cumulative_wrapper_actions']==1282127 and budget['research_remaining']==0 and budget['final_reserved_actions']==84000 and budget['final_reserve_used']==0
    assert sum(json.loads(s).get('stage')==334 for s in (R/'experiment-cost-lines.jsonl').read_text().splitlines())==1
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    diagnostic={g:{key:stats([abs(r[key]) for r in motion if r['group']==g],[r['road'] for r in motion if r['group']==g]) for key in ['yaw_error','lateral_displacement_error','forward_displacement_error','displacement_error_norm']} for g in ['original6','N2']}
    receipt=dict(passed=True,OFF_rows_independently_verified=count,archive_member_changes=changes,algebra=algebra,actual_GT_motion_intervals=len(motion),motion_diagnostic=diagnostic,first_any_cached_command_changes=first,
        fixed_formula_not_refit=True,new_native_actions=0,new_actor_calls=0,new_learning_fits=0,new_source_physics_ticks=0,budget_unchanged=True,visibility_truth_available=False,
        verification_wall_s=time.perf_counter()-start,verification_CPU_s=time.process_time()-cpu)
    save(D/'saved-evidence-verification.json',receipt);public=read(D/'summary-private.json');public['saved_evidence_verification']=receipt;public['next_minimal_closed_loop']['cached_N2_first_any_command_change']=first['N2_330_A'];public['next_minimal_closed_loop']['cached_prefix_actions_before_first_difference']=first['N2_330_A']-1;save(D/'summary-private.json',public);save(Path(__file__).resolve().parent/'fallback334_result.json',public)
    print(json.dumps(dict(passed=True,rows=count,motion_intervals=len(motion),first_command_changes=first,cost_CPU_s=receipt['verification_CPU_s'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)
