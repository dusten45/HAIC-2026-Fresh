"""Run the two preregistered privileged H24 DEV episodes once, no training.

The private --plan binds frozen221 assets, prefixes, flags, known road IDs and
budget. H12 is historical221 only. The original12-action execution lifecycle
is retained; only forecasts and endpoint evaluation extend to24.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np


def run(path):
    from retry import receding_horizon_oracle as rh
    from retry import horizon233_teacher as teacher
    from retry.frozen_paired_evaluation import write,sha,verify_files
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    verify_files(p['source_sha256']);verify_files(p['runtime_sha256'])
    assert p['labels']==['F0','F1'] and p['max_actions']==1200 and p['oracle']['horizon_actions']==12
    assert p['oracle']['evaluation_horizon_actions']==24 and p['offline_gt_wall_timing']
    directory=path.parent.parent
    write(path.parent/'budget.json',dict(started_epoch=time.time(),actions=0,stages={}),exclusive=True)
    write(directory/'opening.json',dict(stage=233,native_before=0,one_use=True,labels=p['labels']),exclusive=True)
    forecast,endpoint=rh.forecast_pool,rh.endpoint
    audit=[];current_label=None
    def horizon_endpoint(rows,horizon,initial_tiles):
        assert horizon==12
        return endpoint(rows,24,initial_tiles)
    def observed_forecast(*a,**kw):
        q,specs,retained,commands=teacher.forecast_pool(*a,**kw)
        assert len(q['candidates']) in (43,44)
        assert all(len(xs)<=12 for xs in commands.values())
        if retained:assert retained['expires_before']==retained['origin_step']+12
        audit.append(dict(road=current_label,before_action=a[3],candidate_count=len(q['candidates']),R_remaining=retained['remaining_actions'] if retained else 0,R_expires_before=retained['expires_before'] if retained else None,initialization_all_exact=all(all(v['initialization'].values()) for v in q['candidates'].values()),feedback_control_CPU_s=sum(v['control_CPU_s'] for v in q['candidates'].values()),feedback_control_wall_s=sum(v['control_wall_s'] for v in q['candidates'].values()),prefix_definitions_asserted=True))
        if (a[3]-1)%30==0:print(json.dumps(dict(road=current_label,before_action=a[3],candidates=len(q['candidates']),model_ticks=q['model_physics_ticks'])),flush=True)
        return q,specs,retained,commands
    rh.forecast_pool,rh.endpoint=observed_forecast,horizon_endpoint
    start=time.perf_counter();records={};error=None
    try:
        for current_label,case in zip(p['labels'],p['cases']):
            cp=dict(p,max_steps=500)
            r,d=rh.oracle_episode(path,cp,case,'C',{})
            records[current_label]=r
            print(json.dumps(dict(road=current_label,native=r['charged_wrapper_actions'],completed=r['completed'],lap_ms=r['lap_ms'],damage=r['damage'],reason=r['retire_reason'],error=r.get('error'))),flush=True)
            if r.get('error'):error=r['error'];break
    except Exception as e:error=type(e).__name__+': '+str(e)
    finally:
        rh.forecast_pool,rh.endpoint=forecast,endpoint
        ledger=json.loads((path.parent/'budget.json').read_text())
        assert ledger['actions']==sum(r['charged_wrapper_actions'] for r in records.values())<=1200
        write(directory/'forecast-audit.json',dict(records=audit),exclusive=True)
        write(directory/'outcome.json',dict(stage=233,records=records,native_actions=ledger['actions'],wall_s=time.perf_counter()-start,technical_error=error,unexecuted=[l for l in p['labels'] if l not in records],all_workers_reaped=all(r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'] for r in records.values()),champion_changed=False,student_training=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False),exclusive=True)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
