"""Two generations of fixed conditional-brake CEMvariant, knownDEV only, durable cache.

Resume only after confirming no live process. Completed roads are cache hits;
a preexisting unfinished run directory is a technical stop, never replayed.
Ranking uses completion/officialtime/normalizedcoverage only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def key(theta):return '|'.join(float(0. if x==0 else x).hex() for x in theta)


def rank(candidate):
    s=candidate['score'];t=candidate['theta']
    return (-s['completions'],s['mean_lap_ms'] if s['completions']==2 else -s['mean_coverage'],
            float(np.dot(t,t)),float(t[0]),float(t[1]),candidate['order'])


def search(path):
    from retry import diagnose,frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import episode,sha,verify_files,native_window
    from retry.full_route_reproduction import truth
    from retry.conditional242_build import build
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    verify_files(p['source_sha256']);verify_files(p['runtime_sha256']);native_window(p)
    D=path.parent;R=D.parent;G=Path(__file__).resolve().parents[1]
    def read(q):return json.loads(q.read_text())
    def save(q,x,exclusive=False):
        payload=json.dumps(x,indent=2,allow_nan=False)+'\n'
        if exclusive:
            with q.open('x') as f:f.write(payload)
        else:
            temp=q.with_name(q.name+'.tmp');temp.write_text(payload);temp.chmod(0o600);temp.replace(q)
        q.chmod(0o600)
    if not (D/'opening.json').exists():save(D/'opening.json',dict(stage=242,start_epoch=time.time(),one_use=True),True)
    cache=read(D/'cache.json') if (D/'cache.json').exists() else {}
    initials=read(D/'initial-pairs.json') if (D/'initial-pairs.json').exists() else {}
    native_records=read(D/'native-records.json') if (D/'native-records.json').exists() else []
    configurations=read(D/'configurations.json') if (D/'configurations.json').exists() else {}
    cache_hits=read(D/'cache-hits.json') if (D/'cache-hits.json').exists() else []
    zero=key([0.,0.]);cases=p['cases']
    for road,case in cases.items():
        r=read(R/'stage241/runs'/(case['id']+'__C')/'result.json')
        assert r['archive_sha256']==p['base']['archive_sha256']
        cache.setdefault(zero+'::'+road,dict(completed=r['completed'],censored=r['censored'],lap_ms=r['lap_ms'],unique_tiles=r['unique_tiles'],total_tiles=r['total_tiles'],damage=r['damage'],retire_reason=r['retire_reason'],historical='241exact240baseline',new_native_actions=0))
        initials.setdefault(case['id'],r['initial'])
    save(D/'cache.json',cache)
    def remaining():return 10000-read(D/'budget.json')['actions']
    def config(theta):
        k=key(theta)
        if k in configurations:return configurations[k]
        tag=hashlib.sha256(k.encode()).hexdigest()[:16];archive=D/('scale-'+tag+'.zip')
        if archive.exists():raise RuntimeError('Existing unregistered archive; do not overwrite')
        b=build(Path(p['base']['archive_path']),theta,archive);archive.chmod(0o600)
        c=dict(p['base'],archive_path=str(archive),archive_sha256=b['archive_sha256'],members_sha256=b['members_sha256'],worker_path=str(G/'retry/conditional242_worker.py'),worker_sha256=sha(G/'retry/conditional242_worker.py'))
        configurations[k]=c;save(D/'configurations.json',configurations)
        return c
    def evaluate(theta,road,arm):
        ck=key(theta)+'::'+road
        if ck in cache:
            cache_hits.append(dict(request=arm,road=road,theta=theta,result_source=cache[ck].get('historical','previousnative')));save(D/'cache-hits.json',cache_hits)
            return cache[ck]
        if remaining()<=0:return None
        case=cases[road];folder=D/'runs'/(case['id']+'__'+arm)
        if folder.exists():
            if not (folder/'result.json').exists():raise RuntimeError('Unfinished native directory; no automatic replay')
            r=read(folder/'result.json')
        else:
            c=config(theta);cp=dict(p,max_steps=remaining(),arms={arm:c})
            rows=[];audits=[];compute=[]
            factory,preparer=diagnose.make_env,runtime.prepare
            def observed_factory(*a,**kw):
                env=factory(*a,**kw);step=env.step
                def observed_step(action):
                    output=step(action);t=truth(env);rows.append(dict(action=len(rows)+1,speed_m_s=t['speed_m_s'],damage=t['damage'],unique_tiles=t['unique_tiles'],off_track_counter=t['off_track_counter'],collision=bool(output[4]['collision'])))
                    return output
                env.step=observed_step;return env
            def observed_prepare(*a,**kw):
                actor=preparer(*a,**kw);call=actor.call
                def observed_call(op,observation):
                    response,ms=call(op,observation)
                    if op=='act':
                        q=response['conditional_audit'];assert q['nominal_memory_preserved'] and q['gas_steering_unchanged'];audits.append(q);compute.append(response['act_compute_ms'])
                    return response,ms
                actor.call=observed_call;return actor
            diagnose.make_env,runtime.prepare=observed_factory,observed_prepare
            start=time.perf_counter()
            try:r=episode(path,cp,case,arm,initials)
            finally:diagnose.make_env,runtime.prepare=factory,preparer
            save(folder/'scale-diagnostic.json',dict(actual_steps=rows,audit=audits,full_Agent_compute_ms=compute,wall_s=time.perf_counter()-start,GT_to_policy=False),True)
        if r.get('initial'):
            if case['id'] in initials:assert initials[case['id']]==r['initial']
            initials[case['id']]=r['initial'];save(D/'initial-pairs.json',initials)
        summary={k:r.get(k) for k in ['completed','censored','lap_ms','unique_tiles','total_tiles','damage','retire_reason','error']}
        summary.update(new_native_actions=r['charged_wrapper_actions'],role=r['role'],historical=None)
        cache[ck]=summary;save(D/'cache.json',cache)
        if not any(x['role']==r['role'] for x in native_records):native_records.append(dict(role=r['role'],road=road,theta=theta,result=r));save(D/'native-records.json',native_records)
        print(json.dumps(dict(job=arm,road=road,theta=theta,scales=np.exp(theta).tolist(),completed=r['completed'],censored=r['censored'],lap_ms=r['lap_ms'],damage=r['damage'],native=r['charged_wrapper_actions'],total_native=read(D/'budget.json')['actions'],error=r.get('error'))),flush=True)
        if r.get('error'):raise RuntimeError(r['error'])
        return summary
    rng=np.random.default_rng(242);generations=[];archive_candidates=[];error=None;unexecuted=[]
    try:
        for gen in [1,2]:
            proposal_path=D/('generation'+str(gen)+'-proposals.json')
            if proposal_path.exists():proposal=read(proposal_path);rng.bit_generator.state=proposal['rng_state_after']
            else:
                mean=np.zeros(2) if gen==1 else np.asarray(generations[-1]['updated_mean'])
                draw=rng.normal(mean,.15,size=(5 if gen==1 else 6,2));theta=np.clip(draw,-np.log(1.5),np.log(1.5))
                if gen==1:theta=np.vstack([np.zeros(2),theta])
                proposal=dict(generation=gen,mean=mean.tolist(),std=[.15,.15],theta=theta.tolist(),rng_state_after=rng.bit_generator.state)
                save(proposal_path,proposal,True)
            candidates=[]
            for slot,t in enumerate(proposal['theta']):
                results={}
                for road in ['F0','F3']:
                    r=evaluate(t,road,'g'+str(gen)+'p'+str(slot)+'_'+road)
                    if r is None:unexecuted.append(dict(generation=gen,slot=slot,road=road));break
                    results[road]=r
                complete=len(results)==2 and all(not r['censored'] and not r.get('error') for r in results.values())
                s=None
                if complete:
                    n=sum(r['completed'] for r in results.values());s=dict(completions=n,mean_lap_ms=float(np.mean([r['lap_ms'] for r in results.values()])) if n==2 else None,mean_coverage=float(np.mean([r['unique_tiles']/r['total_tiles'] for r in results.values()])))
                c=dict(generation=gen,slot=slot,order=(gen-1)*6+slot,theta=t,scales=np.exp(t).tolist(),results=results,fitness_observed=complete,score=s)
                candidates.append(c);save(D/('g'+str(gen)+'p'+str(slot)+'-score.json'),c)
                if not complete:break
            done=len(candidates)==6 and all(c['fitness_observed'] for c in candidates)
            if not done:
                generations.append(dict(generation=gen,complete=False,candidates=candidates));break
            ranked=sorted(candidates,key=rank);mean=np.mean([c['theta'] for c in ranked[:2]],axis=0).tolist()
            record=dict(generation=gen,complete=True,candidates=candidates,elite_slots=[c['slot'] for c in ranked[:2]],updated_mean=mean)
            save(D/('generation'+str(gen)+'-result.json'),record);generations.append(record);archive_candidates.extend(candidates)
        screens={};finalist=None
        if len(generations)==2 and all(g['complete'] for g in generations):
            finalist=sorted(archive_candidates,key=rank)[0]
            if (D/'finalist-freeze.json').exists():assert read(D/'finalist-freeze.json')==finalist
            else:save(D/'finalist-freeze.json',finalist,True)
            # Exactly one selected finalist; baselineF3 then fixedF1/F3 screen.
            for road in ['F1','F2']:
                r=evaluate(finalist['theta'],road,'screen_'+road)
                if r is None:unexecuted.append(dict(screen=road));continue
                screens[road]=r
        save(D/'search-results.json',dict(stage=242,generations=generations,finalist=finalist,screens=screens,unexecuted=unexecuted,technical_error=None))
    except Exception as e:
        error=type(e).__name__+': '+str(e);save(D/'search-error.json',dict(error=error,generations=generations,unexecuted=unexecuted))
    finally:
        ledger=read(D/'budget.json');assert ledger['actions']==sum(x['result']['charged_wrapper_actions'] for x in native_records)<=10000
        save(D/'outcome.json',dict(stage=242,native_actions=ledger['actions'],wall_s=time.time()-read(D/'opening.json')['start_epoch'],technical_error=error,new_native_runs=len(native_records),cache_hits=len(cache_hits),all_workers_reaped=all(x['result']['reaping']['process_reaped'] and x['result']['reaping']['actor_pids_absent'] for x in native_records),champion_changed=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False))


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);search(a.parse_args().plan.resolve())
