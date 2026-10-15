"""Single fixed six-TRAIN comparison after cache admission, no policy search."""
import argparse
import datetime
import json
import time
from pathlib import Path

import numpy as np

from retry.h1_329_stage import verify
from retry.path271_run import read,save,sha


def run(R):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=R/'stage329';p=verify(D);assert read(D/'cache-receipt.json')['passed']
    assert not (D/'native-opening.json').exists();save(D/'native-opening.json',dict(epoch=time.time(),script_sha256=sha(Path(__file__))))
    configs=read(D/'artifacts-private.json');baseline={r['road']:r for r in p['baseline296']['results']};results=[];shortfall=None
    for index,road in enumerate(p['roads']):
        budget=read(D/'native-budget.json');pending=sum(baseline[r]['native_actions'] for r in p['roads'][index:])
        if budget['cap']-budget['actions']<pending:
            shortfall=dict(remaining=budget['cap']-budget['actions'],pending_roads=p['roads'][index:],measured_baseline_pending=pending);break
        F=D/'evaluation'/road;assert not F.exists();F.mkdir(parents=True,mode=0o700);worker=env=None;rawticks=0;actorcpu=0.;steps=0;terminal=complete=False;error=None;infos={};frames=[];actions=[];events=[];reset=0
        start,cpu=time.perf_counter(),time.process_time()
        try:
            worker=prepare(configs[road],F/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped
            assert sha_bytes(obs.tobytes())==p['initial_observations'][road];assert sha_bytes(np.asarray(raw.track,dtype='<f8').tobytes())==case['road_geometry_sha256']
            t0=raw.t;reset=round(t0*50);worker.call('reset',obs);frames.append(obs.copy());journal=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
            try:
                while not terminal:
                    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
                    budget=read(D/'native-budget.json')
                    if budget['actions']>=budget['cap']:break
                    r,ms=worker.call('act',obs);assert ms<=5000 and not r['python_audit_denied_events'];action=np.array(r['action'],np.float32);audit=r['delta_audit']
                    assert audit['action']==action.tolist() and action[0]==np.float32(audit['base'][0]) and audit['nominal_memory_preserved']
                    if audit['changed']:assert audit['selected_supported'] and audit['chosen_error']<audit['baseline_error']
                    if r['features'][0]:assert not audit['changed']
                    c,_=worker.call('commit',action);assert np.float32(c['memory'])==action[0] and c['history'][-1]==action.tolist();actorcpu=c['actor_cumulative_CPU_s']
                    budget['actions']+=1;save(D/'native-budget.json',budget);before=raw.t;obs,_,ended,truncated,infos=env.step(action);rawticks+=round((raw.t-before)*50);steps+=1
                    terminal=bool(ended or truncated);complete=raw.finish_time_s is not None;frames.append(obs.copy());actions.append(action.copy())
                    row=dict(step=steps,action=action.tolist(),features=r['features'],audit=audit,memory=c['memory'],collision=bool(infos['collision']),damage=float(env.damage.damage),terminal=terminal)
                    journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush();events.append(row)
            finally:journal.close()
            result=dict(road=road,completed=complete,actual_DNF=bool(terminal and not complete),censored=not terminal,technical_error=None,native_actions=steps,
                        lap_ms=round((raw.finish_time_s-t0)*1000) if complete else None,damage=float(env.damage.damage),retire_reason=None if complete else infos.get('retire_reason') or 'budget_cut',
                        raw_step_ticks=rawticks,raw_reset_ticks=reset,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,
                        archive_sha256=configs[road]['archive_sha256'],new_source_physics_ticks=0)
        except BaseException as exception:
            error=type(exception).__name__+': '+str(exception);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
            result=dict(road=road,completed=False,actual_DNF=False,censored=False,technical_error=error,native_actions=steps,lap_ms=None,damage=events[-1]['damage'] if events else 0.,
                        raw_step_ticks=rawticks,raw_reset_ticks=reset,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,new_source_physics_ticks=0)
        finally:
            if worker:reaping=worker.close();result['reaping']=reaping
            if env:env.close()
        if frames:
            q=F/'raw-pixels-actions-private.npz';np.savez_compressed(q,observations=np.array(frames,np.float32),actions=np.array(actions,np.float32));q.chmod(0o600)
        save(F/'result.json',result);results.append(result);save(D/'native-partial-private.json',results)
        print(json.dumps({k:result.get(k) for k in ['road','completed','actual_DNF','lap_ms','native_actions','damage','censored','technical_error']}),flush=True)
        if error or result['censored']:break
    save(D/'native-outcome-private.json',dict(results=results,shortfall=shortfall,unobserved=[r for r in p['roads'] if not any(x['road']==r and not x['technical_error'] and not x['censored'] for x in results)],wall_s=time.time()-read(D/'native-opening.json')['epoch']))
    print('329singlecandidatecollectionclosed; no furthersearch orDEV',flush=True)


def sha_bytes(data):return __import__('hashlib').sha256(data).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    run(parser.parse_args().private_root.resolve())
