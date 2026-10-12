"""Rerank exactly238 fixed12global policies on6DEV roads, then2freshDEV screens.

Current240 has6cachedcompletions. Stopa policy afteractualDNF; skippedroads are
unknown, notfailed. Sharedtraining16400/screen1600, durable completedroadcache.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def key(theta):return '|'.join(float(0. if x==0 else x).hex() for x in theta)


def rank(c):return (c['mean_lap_ms'],float(np.dot(c['theta'],c['theta'])),c['theta'][0],c['theta'][1],c['order'])


def search(path):
    from retry import diagnose,frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import episode,sha,verify_files,native_window
    from retry.full_route_reproduction import truth
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip();verify_files(p['source_sha256']);verify_files(p['runtime_sha256']);native_window(p)
    D=path.parent;R=D.parent
    def read(q):return json.loads(q.read_text())
    def save(q,x,exclusive=False):
        payload=json.dumps(x,indent=2,allow_nan=False)+'\n'
        if exclusive:
            with q.open('x') as f:f.write(payload)
        else:
            temp=q.with_name(q.name+'.tmp');temp.write_text(payload);temp.chmod(0o600);temp.replace(q)
        q.chmod(0o600)
    if not (D/'opening.json').exists():save(D/'opening.json',dict(stage=243,start_epoch=time.time(),one_use=True),True)
    cache=read(D/'cache.json') if (D/'cache.json').exists() else {};records=read(D/'native-records.json') if (D/'native-records.json').exists() else [];hits=read(D/'cache-hits.json') if (D/'cache-hits.json').exists() else [];initials=read(D/'initial-pairs.json') if (D/'initial-pairs.json').exists() else {}
    sourcecache=read(R/'stage238/cache.json');current=p['policies'][p['incumbent_order']]
    # Exacttheta/archive old201 results reused; zeroF0 issemanticidentity232.
    for policy in p['policies']:
        for road,oldroad in [('O0','F0'),('O2','F2')]:
            r=sourcecache[key(policy['theta'])+'::'+oldroad];cache.setdefault(key(policy['theta'])+'::'+p['roads'][road]['id'],dict(r,source='238matchingthetaandold201condition',canonical_archive_sha256=policy['archive_sha256']))
    for road in ['N0','N1','N2','N3']:
        c=p['roads'][road];r=read(R/'stage241/runs'/(c['id']+'__C')/'result.json');assert r['archive_sha256']==current['archive_sha256'];initials.setdefault(c['id'],r['initial'])
        cache.setdefault(key(current['theta'])+'::'+c['id'],{**{k:r.get(k) for k in ['completed','censored','lap_ms','unique_tiles','total_tiles','damage','retire_reason','error']},'source':'241exact240archiveandreset','new_native_actions':0,'canonical_archive_sha256':current['archive_sha256']})
    save(D/'cache.json',cache)
    def used(phase):return sum(x['result']['charged_wrapper_actions'] for x in records if x['phase']==phase)
    def evaluate(policy,label,case,arm,phase):
        ck=key(policy['theta'])+'::'+case['id']
        if ck in cache:
            assert cache[ck]['canonical_archive_sha256']==policy['archive_sha256'];hits.append(dict(policy=policy['order'],road=label,phase=phase,source=cache[ck]['source']));save(D/'cache-hits.json',hits);return cache[ck]
        remain=min(p[phase+'_cap']-used(phase),18000-read(D/'budget.json')['actions'])
        if remain<=0:return None
        folder=D/'runs'/(case['id']+'__'+arm)
        if folder.exists():
            if not (folder/'result.json').exists():raise RuntimeError('Unfinishednative directory; no automaticreplay')
            r=read(folder/'result.json')
        else:
            cp=dict(p,max_steps=remain,arms={arm:policy['configuration']});factory,preparer=diagnose.make_env,runtime.prepare;rows=[];audits=[];compute=[]
            def observed_factory(*a,**kw):
                env=factory(*a,**kw);step=env.step
                def observed_step(action):
                    out=step(action);t=truth(env);rows.append(dict(action=len(rows)+1,speed_m_s=t['speed_m_s'],damage=t['damage'],visited=t['unique_tiles'],off_track_counter=t['off_track_counter'],collision=bool(out[4]['collision'])));return out
                env.step=observed_step;return env
            def observed_prepare(*a,**kw):
                actor=preparer(*a,**kw);call=actor.call
                def observed_call(op,ob):
                    response,ms=call(op,ob)
                    if op=='act':
                        a=response['scale_audit'];assert a['steering_unchanged'] and a['nominal_memory_preserved'];audits.append(a);compute.append(response['act_compute_ms'])
                    return response,ms
                actor.call=observed_call;return actor
            diagnose.make_env,runtime.prepare=observed_factory,observed_prepare
            try:r=episode(path,cp,case,arm,initials)
            finally:diagnose.make_env,runtime.prepare=factory,preparer
            save(folder/'diagnostic.json',dict(actual_steps=rows,audit=audits,full_Agent_compute_ms=compute,GT_to_policy=False),True)
        if r.get('initial'):
            if case['id'] in initials:assert initials[case['id']]==r['initial']
            initials[case['id']]=r['initial'];save(D/'initial-pairs.json',initials)
        summary={k:r.get(k) for k in ['completed','censored','lap_ms','unique_tiles','total_tiles','damage','retire_reason','error']};summary.update(new_native_actions=r['charged_wrapper_actions'],source='new243native',canonical_archive_sha256=policy['archive_sha256'],role=r['role'])
        cache[ck]=summary;save(D/'cache.json',cache)
        if not any(x['role']==r['role'] for x in records):records.append(dict(role=r['role'],phase=phase,road=label,policy_order=policy['order'],theta=policy['theta'],result=r));save(D/'native-records.json',records)
        print(json.dumps(dict(phase=phase,policy=policy['order'],road=label,completed=r['completed'],censored=r['censored'],lap_ms=r['lap_ms'],damage=r['damage'],native=r['charged_wrapper_actions'],total_native=read(D/'budget.json')['actions'],error=r.get('error'))),flush=True)
        if r.get('error'):raise RuntimeError(r['error'])
        return summary
    results=[];screens=[];winner=None;error=None
    try:
        order=[current]+[c for c in p['policies'] if c['order']!=current['order']]
        for policy in order:
            rr={};skipped={};reason=None
            for i,label in enumerate(p['road_order']):
                r=evaluate(policy,label,p['roads'][label],'p'+str(policy['order'])+'_'+label,'training')
                if r is None:
                    reason='trainingcap_unexecuted';skipped={x:'budget_not_evaluated' for x in p['road_order'][i:]};break
                rr[label]=r
                if r['censored']:
                    reason='trainingcap_censored_unknown';skipped={x:'budget_not_evaluated' for x in p['road_order'][i+1:]};break
                if not r['completed']:
                    reason='actualDNF_cannotbeat_current6';skipped={x:'ranking_impossible_after_observed_DNF_notfailure' for x in p['road_order'][i+1:]};break
            fully=len(rr)==6 and all(r['completed'] and not r['censored'] for r in rr.values())
            c=dict(order=policy['order'],theta=policy['theta'],scales=policy['scales'],results=rr,skipped=skipped,stop_reason=reason,observed_completed=sum(r['completed'] for r in rr.values()),observed_DNF=sum(not r['completed'] and not r['censored'] for r in rr.values()),censored=sum(r['censored'] for r in rr.values()),all6_completed=fully,mean_lap_ms=float(np.mean([r['lap_ms'] for r in rr.values()])) if fully else None)
            results.append(c);save(D/('policy'+str(policy['order'])+'-sixroad-result.json'),c)
        eligible=[c for c in results if c['all6_completed']];assert eligible
        winner=sorted(eligible,key=rank)[0];winnerpolicy=p['policies'][winner['order']]
        if (D/'winner-freeze.json').exists():assert read(D/'winner-freeze.json')==winner
        else:save(D/'winner-freeze.json',winner,True)
        # Screenonlyafterwinnerfreeze, A=current240/B=exactwinner.
        for i,case in enumerate(p['screen_cases']):
            pair={}
            for arm in case['arm_order']:
                pol=current if arm=='A' else winnerpolicy
                r=evaluate(pol,'S'+str(i),case,'screen'+str(i)+'_'+arm,'screen')
                pair[arm]=r
            screens.append(dict(screen='S'+str(i),order=case['arm_order'],A=pair['A'],B=pair['B'],same_policy_reused=winner['order']==current['order']))
        save(D/'search-results.json',dict(stage=243,policies=results,winner=winner,screens=screens,technical_error=None))
    except Exception as e:
        error=type(e).__name__+': '+str(e);save(D/'search-error.json',dict(error=error,policies=results,winner=winner,screens=screens))
    finally:
        ledger=read(D/'budget.json');assert ledger['actions']==sum(x['result']['charged_wrapper_actions'] for x in records)<=18000 and used('training')<=16400 and used('screen')<=1600
        save(D/'outcome.json',dict(stage=243,native_actions=ledger['actions'],training_native=used('training'),screen_native=used('screen'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],technical_error=error,new_native_runs=len(records),cache_hits=len(hits),all_workers_reaped=all(x['result']['reaping']['process_reaped'] and x['result']['reaping']['actor_pids_absent'] for x in records),champion_changed=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False))


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);search(a.parse_args().plan.resolve())
