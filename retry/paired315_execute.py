"""Conditional fixed paired1NN, saved-input identity and six TRAIN once only."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time
import zipfile

import numpy as np

from retry.path271_run import read, save, sha
from retry.completion297_search import diagnose


def package(p,D,label,on):
    G=Path(__file__).resolve().parent.parent;F=D/label;F.mkdir(mode=0o700)
    with zipfile.ZipFile(p['baseline296']['config']['archive_path']) as z:
        members={n:z.read(n) for n in z.namelist()}
    members['retry/paired315_base.py']=members['agent.py']
    members['agent.py']=(G/'retry/paired315_agent.py').read_bytes()
    a=np.load(D/'paired-index-private.npz')
    source='import numpy as np\n'
    for key,name in [('mean','MEAN'),('std','STD'),('x','X'),('y','Y')]:
        source+=name+'=np.array('+repr(a[key].tolist())+',dtype=np.float64)\n'
    source+='ENABLED='+repr(on)+'\n'
    members['retry/paired315_model.py']=source.encode()
    q=F/'policy.zip'
    with zipfile.ZipFile(q,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(members.items()):
            item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,data)
    q.chmod(0o600)
    cfg=dict(p['baseline296']['config'],archive_path=str(q),archive_sha256=sha(q),
        members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},
        worker_path=str(G/'retry/paired315_worker.py'),worker_sha256=sha(G/'retry/paired315_worker.py'))
    save(F/'candidate-config.json',cfg)
    return cfg


def prepare(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage315'
    assert read(D/'cache-receipt.json')['offline_gate_passed']
    assert not (D/'execution-plan.json').exists()
    old=read(R/'stage313/plan.json');v=read(R/'project-effective-budget-v321.json')
    assert v['research_remaining']==3880
    p=dict(stage=315,deadline_utc='2026-10-16T10:01:55+00:00',
        baseline296=old['baseline296'],base_controller_theta=old['base_controller_theta'],
        cases=old['cases'],initial_observations=old['initial_observations'],screen=old['screen'],
        sandbox_path=old['sandbox_path'],phase_caps=dict(screen=3880),native_cap=3880,
        comparison='Completion count first; equal count strictly lower common-completion mean; additions/losses and damage diagnostic. No minimum margin, loss/damage veto or extra roads.',
        source_recipe_plan_sha256=sha(D/'plan.json'))
    p['off_config']=package(p,D,'off',False);p['on_config']=package(p,D,'on',True)
    files=[G/'retry'/n for n in ['paired315_agent.py','paired315_worker.py','paired315_episode.py','paired315_jobs.py','paired315_execute.py']]
    files += [Path(p['off_config']['archive_path']),Path(p['on_config']['archive_path']),D/'paired-index-private.npz',D/'plan.json',R/'project-effective-budget-v321.json']
    p['hashes']={str(q):sha(q) for q in files}
    save(D/'previous-current-champion.json',read(R/'current-champion.json'))
    save(D/'execution-plan.json',p)
    (D/'execution-plan.sha256').write_text(sha(D/'execution-plan.json')+'\n');(D/'execution-plan.sha256').chmod(0o600)
    # Generic executor expects plan.json. Preserve the first registration verbatim.
    (D/'recipe-plan.json').write_bytes((D/'plan.json').read_bytes());(D/'recipe-plan.json').chmod(0o600)
    (D/'recipe-plan.sha256').write_bytes((D/'plan.sha256').read_bytes());(D/'recipe-plan.sha256').chmod(0o600)
    p['hashes'].pop(str(D/'plan.json'))
    p['hashes'][str(D/'recipe-plan.json')]=sha(D/'recipe-plan.json')
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n')
    save(D/'budget.json',dict(actions=0,screen=0))
    print('315 single candidate frozen; conditional sixTRAIN cap3880',flush=True)


def verify(D):
    p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['hashes'].items():
        assert sha(q)==h,q
    return p


def preflight(R):
    from retry.frozen_composite_runtime import prepare as actor
    D=R/'stage315';p=verify(D);assert not (D/'preflight-opening.json').exists()
    save(D/'preflight-opening.json',dict(epoch=time.time()))
    index=np.load(D/'paired-index-private.npz');records=[]
    for road in p['screen']:
        F=D/'preflight'/road;F.mkdir(parents=True,mode=0o700)
        cache=np.load(R/'stage306/collection'/road/'observations-actions-private.npz')
        rows=[json.loads(s) for s in (R/'stage306/collection'/road/'trace-private.jsonl').read_text().splitlines()]
        assert len(rows)==len(cache['observations'])==len(cache['actions'])
        workers=[];comp=[];times=[[],[]];ipc=[[],[]];cpu=[0.,0.]
        try:
            for k in ['off_config','on_config']:
                workers.append(actor(p[k],F/str(len(workers)),p['sandbox_path']));workers[-1].call('reset',cache['observations'][0])
            for obs,base,r in zip(cache['observations'],cache['actions'],rows):
                responses=[]
                for i,w in enumerate(workers):
                    x,ms=w.call('act',obs);responses.append(x);times[i].append(x['act_compute_ms']);ipc[i].append(ms)
                    ack,_=w.call('commit',np.array(x['action'],np.float32));cpu[i]=ack['actor_cumulative_CPU_s']
                off,on=responses
                assert off['action']==base.tolist() and off['features']==r['features'] and off['state']['previous_steer']==r['memory']
                assert on['features']==off['features'] and on['action'][0]==off['action'][0]
                # Executor history records returned pedals; it is not a policy
                # input. Nominal controller/tracker memory must remain exact.
                assert all(on['state'][k]==off['state'][k] for k in off['state'] if k!='history_sha256')
                query=(np.array(on['features'])-index['mean'])/index['std']
                nearest=int(np.argmin(np.sum((index['x']-query)**2,axis=1)))
                assert nearest==on['delta_audit']['nearest_index']
                assert np.array_equal(index['y'][nearest].astype(np.float32),np.array(on['action'][1:],np.float32))
                comp.append(dict(step=r['step'],action_changed=on['action']!=off['action'],nearest_index=nearest))
        finally:
            reaping=[w.close() for w in workers];assert all(r['process_reaped'] and r['actor_pids_absent'] for r in reaping)
        save(F/'comparisons-private.json',comp)
        records.append(dict(road=road,actions=len(rows),off_exact=True,steer_features_memory_exact=True,
            paired_retrieval_verified=len(rows),on_action_changes=sum(x['action_changed'] for x in comp),
            actor_compute_ms=[dict(p95=float(np.percentile(x,95)),max=float(max(x))) for x in times],
            IPC_ms=[dict(p95=float(np.percentile(x,95)),max=float(max(x))) for x in ipc],actor_CPU_s=cpu))
        print(json.dumps(records[-1]),flush=True)
    changed=sum(r['on_action_changes'] for r in records)
    save(D/'preflight-receipt.json',dict(records=records,actual_action_changes=changed,actual_change=changed>0,
        new_native=0,wall_s=time.time()-read(D/'preflight-opening.json')['epoch']))


def run(R):
    from retry.paired315_jobs import jobs
    D=R/'stage315';p=verify(D);pre=read(D/'preflight-receipt.json')
    assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()))
    results=[];error=None
    try:
        if pre['actual_change']:
            t=p['base_controller_theta']
            for road in p['screen']:
                entry=dict(folder=str(D/'evaluations/screen'/road),road=road,case=p['cases'][road],
                    initial_observation_sha256=p['initial_observations'].get(road),config=p['on_config'],
                    ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2])))
                out=jobs(D,p,[entry],'screen');results+=out;save(D/'screen-partial.json',results)
                print(json.dumps([{k:r.get(k) for k in ['road','completed','native_actions','lap_ms','technical_error','censored']} for r in out]),flush=True)
                if not out or any(r['technical_error'] or r['censored'] for r in out):
                    break
    except BaseException as e:
        error=type(e).__name__+': '+str(e)
    fully=len(results)==6 and not any(r['technical_error'] or r['censored'] for r in results)
    base=[r for r in p['baseline296']['results'] if r['road'] in p['screen']]
    diag=diagnose(results,base) if fully else None;count=sum(r['completed'] for r in results)
    better=fully and (count>5 or (count==5 and diag['common_mean_delta_ms'] is not None and diag['common_mean_delta_ms']<0))
    save(D/'outcome-private.json',dict(results=results,fully_observed=fully,diagnostic=diag,screen_better=bool(better),technical_error=error,
        unobserved=[r for r in p['screen'] if not any(x['road']==r and not x['technical_error'] and not x['censored'] for x in results)],
        wall_s=time.time()-read(D/'opening.json')['epoch']))
    print('315 closed; no extra roads or DEV',flush=True)


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage315';p=verify(D);o=read(D/'outcome-private.json');b=read(D/'budget.json')
    assert not (D/'cost.json').exists()
    rr=o['results'];assert sum(r['native_actions'] for r in rr)==b['actions']<=3880
    signals=[]
    for r in rr:
        F=D/'evaluations/screen'/r['road'];assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
        rows=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        assert len(rows)==r['native_actions']
        assert all(x['pair_audit']['memory_preserved'] and x['pair_audit']['after']==x['action'] for x in rows)
        signals.append(dict(road=r['road'],actions=len(rows),pedals_changed=sum(x['pair_audit']['before'][1:]!=x['action'][1:] for x in rows),both_pedals_positive=sum(x['action'][1]>0 and x['action'][2]>0 for x in rows)))
    prior=R/'project-effective-budget-v321.json';v=read(prior)
    cost=dict(stage=315,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=b['actions'],native_cap=3880,
        new_official_runs=len(rr),new_source_physics_ticks=0,new_teacher_queries=0,new_paid_resources=0,
        raw_step_ticks=sum(x['raw_step_ticks'] for x in rr),raw_reset_ticks=sum(x['raw_reset_ticks'] for x in rr),
        runner_CPU_s=sum(x['runner_CPU_s'] for x in rr),actor_CPU_s=sum(x['actor_CPU_s'] for x in rr),total_native_wall_s=o['wall_s'],
        actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],
        final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1330000)
    save(D/'cost.json',cost)
    v.update(version=322,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,
        cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],
        research_remaining=cost['research_remaining'],stage315_new_wrapper_actions=b['actions'])
    assert not (R/'project-effective-budget-v322.json').exists();save(R/'project-effective-budget-v322.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==315 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json')
    safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']}
    pub=read(D/'cache-receipt.json')
    pub.update(preflight=read(D/'preflight-receipt.json'),results=[safe(r) for r in rr],
        baseline=[safe(r) for r in p['baseline296']['results'] if r['road'] in p['screen']],
        fully_observed=o['fully_observed'],diagnostic=o['diagnostic'],screen_better=o['screen_better'],
        unobserved=o['unobserved'],technical_error=o['technical_error'],signals=signals,native_cost=cost)
    save(G/'retry/paired315_result.json',pub)
    print(json.dumps(dict(results=pub['results'],diagnostic=pub['diagnostic'],screen_better=pub['screen_better'],cost=cost)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','preflight','run','close']);a.add_argument('--private-root',type=Path,required=True)
    x=a.parse_args();globals()[x.phase](x.private_root.resolve())
