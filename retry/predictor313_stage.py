"""Single score-predictor alignment, saved-pixel preflight and six TRAIN only."""
import argparse
import datetime
import hashlib
from pathlib import Path
import json
import time
import zipfile

import numpy as np

from retry.path271_run import read, save, sha
from retry.completion297_search import diagnose


def package(p, D, label, on):
    G = Path(__file__).resolve().parent.parent
    F = D / label
    F.mkdir(mode=0o700)
    with zipfile.ZipFile(p['baseline296']['config']['archive_path']) as z:
        members = {n: z.read(n) for n in z.namelist()}
    original = members['retry/connected_agent.py']
    s = original.decode()
    old = 'target = route_target(candidate["path"], speed)'
    assert s.count(old) == 1
    s = s.replace(old, 'target = route_target(candidate["path"], speed, LOOKAHEAD_SCALE) if ALIGN_PREDICTOR else route_target(candidate["path"], speed)')
    old = 'np.arctan(3.24 * curvature)'
    assert s.count(old) == 1
    s = s.replace(old, 'np.arctan(3.24 * curvature * (STEERING_GAIN if ALIGN_PREDICTOR else 1.0))')
    s += '\nfrom retry.cem294_constants import LOOKAHEAD_SCALE, STEERING_GAIN\nALIGN_PREDICTOR = ' + repr(on) + '\n'
    members['retry/connected_agent.py'] = s.encode()
    members['retry/predictor313_original.py'] = original
    q = F / 'policy.zip'
    with zipfile.ZipFile(q, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for n, data in sorted(members.items()):
            item = zipfile.ZipInfo(n, date_time=(2026, 10, 9, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            z.writestr(item, data)
    q.chmod(0o600)
    cfg = dict(p['baseline296']['config'], archive_path=str(q), archive_sha256=sha(q),
        members_sha256={n: hashlib.sha256(b).hexdigest() for n, b in members.items()},
        worker_path=str(G/'retry/predictor313_worker.py'), worker_sha256=sha(G/'retry/predictor313_worker.py'))
    save(F/'candidate-config.json', cfg)
    return cfg


def prepare(R):
    G = Path(__file__).resolve().parent.parent
    D = R/'stage313'
    assert not D.exists(), 'Existing stage: inspect, do not duplicate'
    D.mkdir(mode=0o700)
    v = read(R/'project-effective-budget-v320.json')
    assert v['research_remaining'] == 3880 and v['final_reserved_actions'] == 84000
    old = read(R/'stage299/plan.json')
    p = dict(stage=313, deadline_utc='2026-10-16T10:01:55+00:00',
        baseline296=old['baseline296'], base_controller_theta=old['baseline296']['theta'],
        cases=old['cases'], initial_observations=old['initial_observations'],
        screen=['T2950','T2953','T2956','T2959','O0','O2'],
        sandbox_path=old['sandbox_path'], phase_caps=dict(screen=3000), native_cap=3000,
        rule='Only score predictor uses frozen296 target/lookahead/gain/clip/smoothing. Existing candidates, costs, tie order, anchor, controller, head and memory unchanged.',
        preflight_gate='OFF exact stored actions/features/memory. ON each candidate prediction equals copied actual controller output. Any same-input selected-path change suffices; no minimum road count.',
        comparison='Completion count first; equal count requires strictly lower common-completion mean time. Report additions/losses; no identical-set or 80ms gate. Six results only, no automatic extension/DEV/promotion.',
        changed_from312_before_results='Remove two-road preflight threshold, 80ms minimum, identical-completion-set and no-loss requirements, per 2026-10-14 19:02 KST instruction.',
        methodology_scope='Parent completed original documents; no new complete-original mapping claimed by this executor.',
        stop='Native cap3000/deadline/technical error/censor. Unobserved is not DNF; reserve unused.')
    p['off_config'] = package(p,D,'off',False)
    p['on_config'] = package(p,D,'on',True)
    names=['predictor313_stage.py','predictor313_worker.py','predictor313_episode.py','predictor313_jobs.py']
    paths=[G/'retry'/n for n in names]+[Path(p['baseline296']['config']['archive_path']),Path(p['off_config']['archive_path']),Path(p['on_config']['archive_path']),R/'project-effective-budget-v320.json']
    p['hashes']={str(q):sha(q) for q in paths}
    save(D/'previous-current-champion.json',read(R/'current-champion.json'))
    save(D/'plan.json',p)
    (D/'plan.sha256').write_text(sha(D/'plan.json')+'\n')
    (D/'plan.sha256').chmod(0o600)
    save(D/'budget.json',dict(actions=0,screen=0))
    print('313 registered: single candidate, six TRAIN, native cap3000',flush=True)


def verify(D):
    p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['hashes'].items():
        assert sha(q)==h,q
    return p


def preflight(R):
    from retry.frozen_composite_runtime import prepare as actor
    D=R/'stage313';p=verify(D)
    assert not (D/'preflight-opening.json').exists()
    save(D/'preflight-opening.json',dict(epoch=time.time()))
    records=[]
    for road in p['screen']:
        F=D/'preflight'/road;F.mkdir(parents=True,mode=0o700)
        cache=np.load(R/'stage306/collection'/road/'observations-actions-private.npz')
        rows=[json.loads(s) for s in (R/'stage306/collection'/road/'trace-private.jsonl').read_text().splitlines()]
        assert len(rows)==len(cache['observations'])==len(cache['actions'])
        workers=[];data=[];computes=[[],[]];ipc=[[],[]];cpu=[0.,0.]
        try:
            for k in ['off_config','on_config']:
                workers.append(actor(p[k],F/str(len(workers)),p['sandbox_path']))
                workers[-1].call('reset',cache['observations'][0])
            for obs,base,r in zip(cache['observations'],cache['actions'],rows):
                responses=[]
                for i,w in enumerate(workers):
                    x,ms=w.call('act',obs);responses.append(x)
                    computes[i].append(x['act_compute_ms']);ipc[i].append(ms)
                    ack,_=w.call('commit',np.array(x['action'],np.float32));cpu[i]=ack['actor_cumulative_CPU_s']
                off,on=responses;g=on['route_audit']
                assert off['action']==base.tolist() and off['features']==r['features'] and off['state']['previous_steer']==r['memory']
                assert not off['route_audit']['path_changed']
                assert g['aligned'] and g['candidates_verified']==g['candidate_count']
                if not on['features'][0]:
                    assert np.float32(g['selected_prediction'])==np.float32(on['action'][0])
                data.append(dict(step=r['step'],action_changed=on['action']!=off['action'],on_route_audit=g))
        finally:
            reaping=[w.close() for w in workers]
            assert all(r['process_reaped'] and r['actor_pids_absent'] for r in reaping)
        save(F/'comparisons-private.json',data)
        records.append(dict(road=road,actions=len(data),off_exact=True,
            on_action_changes=sum(x['action_changed'] for x in data),
            same_input_selected_path_changes=sum(x['on_route_audit']['path_changed'] for x in data),
            candidate_predictions_verified=sum(x['on_route_audit']['candidates_verified'] for x in data),
            actor_compute_ms=[dict(p95=float(np.percentile(x,95)),max=float(max(x))) for x in computes],
            IPC_ms=[dict(p95=float(np.percentile(x,95)),max=float(max(x))) for x in ipc],actor_CPU_s=cpu))
        print(json.dumps(records[-1]),flush=True)
    changed=sum(r['same_input_selected_path_changes'] for r in records)
    save(D/'preflight-receipt.json',dict(records=records,same_input_selected_path_changes=changed,
        actual_selection_change=changed>0,new_native=0,new_source_physics_ticks=0,
        wall_s=time.time()-read(D/'preflight-opening.json')['epoch']))


def run(R):
    from retry.predictor313_jobs import jobs
    D=R/'stage313';p=verify(D);pre=read(D/'preflight-receipt.json')
    assert not (D/'opening.json').exists()
    save(D/'opening.json',dict(epoch=time.time()))
    results=[];error=None
    try:
        if pre['actual_selection_change']:
            t=p['base_controller_theta']
            for road in p['screen']:
                entry=dict(folder=str(D/'evaluations/screen'/road),road=road,case=p['cases'][road],
                    initial_observation_sha256=p['initial_observations'].get(road),config=p['on_config'],
                    ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2])))
                out=jobs(D,p,[entry],'screen');results+=out
                save(D/'screen-partial.json',results)
                print(json.dumps([{k:r.get(k) for k in ['road','completed','native_actions','lap_ms','technical_error','censored']} for r in out]),flush=True)
                if not out or any(r['technical_error'] or r['censored'] for r in out):
                    break
    except BaseException as e:
        error=type(e).__name__+': '+str(e)
    base=[r for r in p['baseline296']['results'] if r['road'] in p['screen']]
    fully=len(results)==6 and not any(r['technical_error'] or r['censored'] for r in results)
    diag=diagnose(results,base) if fully else None
    nc=sum(r['completed'] for r in results)
    better=fully and (nc>5 or (nc==5 and diag['common_mean_delta_ms'] is not None and diag['common_mean_delta_ms']<0))
    save(D/'outcome-private.json',dict(results=results,fully_observed=fully,diagnostic=diag,screen_better=bool(better),
        technical_error=error,unobserved=[r for r in p['screen'] if not any(x['road']==r and not x['technical_error'] and not x['censored'] for x in results)],
        wall_s=time.time()-read(D/'opening.json')['epoch']))
    print('313 execution closed; no extension',flush=True)


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage313';p=verify(D)
    o=read(D/'outcome-private.json');b=read(D/'budget.json')
    assert not (D/'cost.json').exists()
    results=o['results'];assert sum(r['native_actions'] for r in results)==b['actions']<=3000
    signals=[]
    for r in results:
        F=D/'evaluations/screen'/r['road']
        assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
        rows=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        assert len(rows)==r['native_actions']
        assert all(x['route_audit']['candidates_verified']==x['route_audit']['candidate_count'] for x in rows)
        signals.append(dict(road=r['road'],actions=len(rows),same_input_selected_path_changes=sum(x['route_audit']['path_changed'] for x in rows),candidate_predictions_verified=sum(x['route_audit']['candidates_verified'] for x in rows)))
    prior=R/'project-effective-budget-v320.json';v=read(prior)
    cost=dict(stage=313,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        new_wrapper_actions=b['actions'],native_cap=3000,new_official_runs=len(results),
        new_source_physics_ticks=0,new_fits=0,new_paid_resources=0,
        raw_step_ticks=sum(x['raw_step_ticks'] for x in results),raw_reset_ticks=sum(x['raw_reset_ticks'] for x in results),
        runner_CPU_s=sum(x['runner_CPU_s'] for x in results),actor_CPU_s=sum(x['actor_CPU_s'] for x in results),
        total_native_wall_s=o['wall_s'],B_operating_cap=1330000,
        actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],
        research_remaining=v['research_remaining']-b['actions'],final_reserved_actions=84000,final_reserve_used=0)
    save(D/'cost.json',cost)
    v.update(version=321,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,
        cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),
        actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],
        research_remaining=cost['research_remaining'],stage313_new_wrapper_actions=b['actions'])
    assert not (R/'project-effective-budget-v321.json').exists()
    save(R/'project-effective-budget-v321.json',v)
    ledger=R/'experiment-cost-lines.jsonl'
    assert not any(json.loads(s).get('stage')==313 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:
        f.write(json.dumps(cost)+'\n')
    assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json')
    safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']}
    pub=dict(stage=313,rule=p['rule'],comparison=p['comparison'],changed_from312_before_results=p['changed_from312_before_results'],
        preflight=read(D/'preflight-receipt.json'),results=[safe(r) for r in results],
        baseline=[safe(r) for r in p['baseline296']['results'] if r['road'] in p['screen']],
        fully_observed=o['fully_observed'],diagnostic=o['diagnostic'],screen_better=o['screen_better'],
        unobserved=o['unobserved'],technical_error=o['technical_error'],signals=signals,cost=cost,
        champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,
        automatic_extension=False,promotion=False)
    save(G/'retry/predictor313_result.json',pub)
    print(json.dumps(dict(results=pub['results'],diagnostic=pub['diagnostic'],screen_better=pub['screen_better'],cost=cost)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('phase',choices=['prepare','preflight','run','close'])
    a.add_argument('--private-root',type=Path,required=True)
    x=a.parse_args()
    globals()[x.phase](x.private_root.resolve())
