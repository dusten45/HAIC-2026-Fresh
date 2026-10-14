"""One first-overlap action, cached timing gate then existing six TRAIN only."""
import argparse,datetime,json,time,zipfile,hashlib,subprocess,sys,os
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import diagnose


def package(p,D,label,on):
    G=Path(__file__).resolve().parent.parent;F=D/label;F.mkdir(mode=0o700)
    with zipfile.ZipFile(p['baseline296']['config']['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
    members['retry/shield319_base.py']=members['agent.py'];members['agent.py']=(G/'retry/shield319_agent.py').read_bytes()
    for n in ['shield319_geometry.py','hud248_features.py']:members['retry/'+n]=(G/'retry'/n).read_bytes()
    members['retry/shield319_constants.py']=('ENABLED='+repr(on)+'\n').encode()
    q=F/'policy.zip'
    with zipfile.ZipFile(q,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(members.items()):
            item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
    q.chmod(0o600)
    cfg=dict(p['baseline296']['config'],archive_path=str(q),archive_sha256=sha(q),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},
        worker_path=str(G/'retry/shield319_worker.py'),worker_sha256=sha(G/'retry/shield319_worker.py'))
    save(F/'candidate-config.json',cfg);return cfg


def prepare(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage319';assert not D.exists();D.mkdir(mode=0o700)
    v=read(R/'project-effective-budget-v324.json');assert v['research_remaining']==2969
    old=read(R/'stage313/plan.json')
    p=dict(stage=319,deadline_utc='2026-10-16T10:01:55+00:00',baseline296=old['baseline296'],base_controller_theta=old['base_controller_theta'],
        cases=old['cases'],initial_observations=old['initial_observations'],screen=old['screen'],sandbox_path=old['sandbox_path'],phase_caps=dict(screen=2969),native_cap=2969,
        rule='First sampled obstacle overlap consumes latch. Original steering and clipped +/-0.08 alternatives, exactties original/minus/plus. Only strictly improved clearance applies one action with gas0 and brake max(old,.5); executed steering memory updated, thereafter296. No threshold or parameter sweep.',
        model='Current ego xright/yforward. Physical tracked-obstacle origin already41.542/62.4475. HUD norm speed heldconstant, lateralvelocity0. Measured CCW yaw and front0 joint; front1 samejoint, rear0. Four20ms motor50/max3 updates, linearly interpolated joint8 samples/tick. Clockwise yaw=-HUDyaw+v/3.24*(tan(-joint)-tan(-initialjoint)); midpoint pose integration. Eight official polygon fixtures, skin.01,33pose samples. No tire/slip/damage/brake dynamics or collision/safety certification.',
        gate='OFF exact296 actions/features/memory. ON actual action change and at leastone first applied trigger strictly before cached first contact; else native0. Recorded callback collision is event label, not geometric overlap truth. No results-based threshold repair.',
        comparison='Six once vs cached2965/6. Count first/equal commonmean strictly lower. Additions/losses/time/damage/actual intervention/cost. No damage veto, minimum gain,DEV,promotion or extension.',
        budget_stop='Only remaining2969, preserve84000reserve. Actual ended/truncated only is terminal; budget cut is censor, not DNF. After an observed road, if remaining falls below measured baseline costs of pending roads, stop before new reset and report shortfall estimate, no extension.')
    p['off_config']=package(p,D,'off',False);p['on_config']=package(p,D,'on',True)
    names=['shield319_geometry.py','shield319_agent.py','shield319_worker.py','shield319_episode.py','shield319_stage.py','hud248_features.py']
    paths=[G/'retry'/n for n in names]+[G/'core/vendor/car_dynamics.py',Path(p['baseline296']['config']['archive_path']),Path(p['off_config']['archive_path']),Path(p['on_config']['archive_path']),R/'project-effective-budget-v324.json']
    p['hashes']={str(q):sha(q) for q in paths};save(D/'previous-current-champion.json',read(R/'current-champion.json'))
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,screen=0))
    print('319 fixed one-action shield registered; cache gate, native2969,no source physics',flush=True)


def verify(D):
    p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(q)==h,q
    return p


def preflight(R):
    from retry.frozen_composite_runtime import prepare as actor
    D=R/'stage319';p=verify(D);assert not (D/'preflight-opening.json').exists();save(D/'preflight-opening.json',dict(epoch=time.time()))
    records=[]
    for road in p['screen']:
        F=D/'preflight'/road;F.mkdir(parents=True,mode=0o700)
        cache=np.load(R/'stage306/collection'/road/'observations-actions-private.npz')
        rows=[json.loads(s) for s in (R/'stage306/collection'/road/'trace-private.jsonl').read_text().splitlines()]
        assert len(rows)==len(cache['observations'])==len(cache['actions'])
        first_contact=next((r['step'] for r in rows if r['collision']),None);workers=[];data=[];compute=[[],[]];ipc=[[],[]];cpu=[0.,0.]
        try:
            for k in ['off_config','on_config']:
                workers.append(actor(p[k],F/str(len(workers)),p['sandbox_path']));workers[-1].call('reset',cache['observations'][0])
            for obs,base,row in zip(cache['observations'],cache['actions'],rows):
                responses=[]
                for i,w in enumerate(workers):
                    x,ms=w.call('act',obs);responses.append(x);compute[i].append(x['act_compute_ms']);ipc[i].append(ms)
                    ack,_=w.call('commit',np.array(x['action'],np.float32));cpu[i]=ack['actor_cumulative_CPU_s']
                    assert np.float32(ack['memory'])==np.float32(x['action'][0])
                off,on=responses;assert off['action']==base.tolist() and off['features']==row['features'] and off['state']['previous_steer']==row['memory']
                data.append(dict(step=row['step'],off=off['shield_audit'],on=on['shield_audit'],action_changed=off['action']!=on['action'],actual_collision=row['collision']))
        finally:
            reaping=[w.close() for w in workers];assert all(r['process_reaped'] and r['actor_pids_absent'] for r in reaping)
        save(F/'comparisons-private.json',data)
        first_overlap=next((r['step'] for r in data if r['off']['first_overlap']),None)
        first_applied=next((r['step'] for r in data if r['on']['applied']),None)
        assert sum(r['on']['applied'] for r in data)<=1
        confusion={k:0 for k in ['TP','FP','FN','TN']}
        for r in data:
            warn=r['off']['predicted_overlap'];truth=r['actual_collision'];key='TP' if warn and truth else 'FP' if warn else 'FN' if truth else 'TN';confusion[key]+=1
        records.append(dict(road=road,actions=len(data),off_exact=True,on_action_changes=sum(r['action_changed'] for r in data),
            first_predicted_overlap=first_overlap,first_applied_trigger=first_applied,first_cached_contact=first_contact,
            applied_before_first_contact=first_applied is not None and first_contact is not None and first_applied<first_contact,
            interventions=sum(r['on']['applied'] for r in data),callback_event_confusion=confusion,
            sampling_half_gap_bound_max_m=max(r['off']['sampling_half_gap_bound_m'] for r in data),
            actor_compute_ms=[dict(p95=float(np.percentile(x,95)),max=float(max(x))) for x in compute],IPC_max_ms=[float(max(x)) for x in ipc],actor_CPU_s=cpu))
        print(json.dumps(records[-1]),flush=True)
    changed=sum(r['on_action_changes'] for r in records);early=sum(r['applied_before_first_contact'] for r in records)
    save(D/'preflight-receipt.json',dict(records=records,actual_action_changes=changed,early_trigger_roads=early,
        gate_passed=changed>0 and early>0,new_native=0,new_source_physics_ticks=0,wall_s=time.time()-read(D/'preflight-opening.json')['epoch']))


def run(R):
    D=R/'stage319';p=verify(D);pre=read(D/'preflight-receipt.json');assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()))
    results=[];error=None;shortfall=None
    if pre['gate_passed']:
        t=p['base_controller_theta'];base={r['road']:r for r in p['baseline296']['results']}
        for index,road in enumerate(p['screen']):
            remaining=2969-read(D/'budget.json')['actions'];pending=sum(base[r]['native_actions'] for r in p['screen'][index:])
            if remaining<pending:
                shortfall=dict(remaining=remaining,measured_baseline_pending_native=pending,estimated_increment=pending-remaining,pending_roads=p['screen'][index:]);break
            F=D/'evaluations'/road;assert not F.exists();F.mkdir(parents=True,mode=0o700)
            job=dict(private_stage=str(D),phase='screen',native_cap=remaining,road=road,case=p['cases'][road],config=p['on_config'],initial_observation_sha256=p['initial_observations'].get(road),ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2])))
            save(F/'job.json',job);log=(F/'driver-private.log').open('x');(F/'driver-private.log').chmod(0o600)
            proc=subprocess.Popen([sys.executable,'-m','retry.shield319_episode','--job',str(F/'job.json')],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
            rc=proc.wait();log.close()
            if not (F/'result.json').exists():error='Childexit'+str(rc)+':missing receipt, no replay';break
            result=read(F/'result.json');results.append(result);save(D/'screen-partial.json',results)
            print(json.dumps({k:result.get(k) for k in ['road','completed','actual_DNF','native_actions','lap_ms','technical_error','censored']}),flush=True)
            if result['technical_error'] or result['censored']:break
    save(D/'outcome-private.json',dict(results=results,technical_error=error,budget_shortfall_estimate=shortfall,
        unobserved=[r for r in p['screen'] if not any(x['road']==r and not x['technical_error'] and not x['censored'] for x in results)],wall_s=time.time()-read(D/'opening.json')['epoch']))
    print('319 execution closed; no promotion or extension',flush=True)


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage319';p=verify(D);o=read(D/'outcome-private.json');b=read(D/'budget.json');assert not (D/'cost.json').exists()
    rr=o['results'];signals=[]
    assert sum(r['native_actions'] for r in rr)==b['actions']<=2969
    for r in rr:
        assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
        rows=[json.loads(s) for s in (D/'evaluations'/r['road']/'trace-private.jsonl').read_text().splitlines()]
        assert len(rows)==r['native_actions'];applied=[x for x in rows if x['shield_audit']['applied']];assert len(applied)<=1
        for x in rows:
            g=x['shield_audit'];assert np.float32(g['executed_memory'])==np.float32(x['action'][0])
            if g['applied']:
                assert g['first_overlap'] and g['strict_improvement'] and x['action'][1]==0. and np.float32(x['action'][2])==np.float32(max(g['base'][2],.5))
            else:assert x['action']==g['base']
        signals.append(dict(road=r['road'],actions=len(rows),interventions=len(applied),first_applied=applied[0]['step'] if applied else None))
    prior=R/'project-effective-budget-v324.json';v=read(prior)
    cost=dict(stage=319,new_wrapper_actions=b['actions'],native_cap=2969,new_official_runs=len(rr),new_source_physics_ticks=0,new_fits_or_PPO=0,new_paid_resources=0,
        raw_step_ticks=sum(r['raw_step_ticks'] for r in rr),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in rr),runner_CPU_s=sum(r['runner_CPU_s'] for r in rr),actor_CPU_s=sum(r['actor_CPU_s'] for r in rr),total_native_wall_s=o['wall_s'],
        actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1350189)
    save(D/'cost.json',cost);v.update(version=325,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage319_new_wrapper_actions=b['actions'])
    assert not (R/'project-effective-budget-v325.json').exists();save(R/'project-effective-budget-v325.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==319 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json')
    base=[r for r in p['baseline296']['results'] if r['road'] in p['screen']];fully=len(rr)==6 and not any(r['technical_error'] or r['censored'] for r in rr)
    safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']}
    pub=dict(stage=319,rule=p['rule'],model=p['model'],gate=p['gate'],comparison=p['comparison'],preflight=read(D/'preflight-receipt.json'),
        results=[safe(r) for r in rr],baseline=[safe(r) for r in base],fully_observed=fully,diagnostic=diagnose(rr,base) if fully else None,signals=signals,
        unobserved=o['unobserved'],budget_shortfall_estimate=o['budget_shortfall_estimate'],technical_error=o['technical_error'],cost=cost,
        champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,automatic_extension=False)
    save(G/'retry/shield319_result.json',pub);print(json.dumps(dict(results=pub['results'],diagnostic=pub['diagnostic'],cost=cost)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','preflight','run','close']);a.add_argument('--private-root',type=Path,required=True);x=a.parse_args();globals()[x.phase](x.private_root.resolve())
