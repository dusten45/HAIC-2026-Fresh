"""Fixed three-road steering-only/brake-only causal ablation; no selection."""
import argparse,datetime,hashlib,json,time,zipfile,subprocess,sys,os
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha


def package(cfg,D,arm):
    G=Path(__file__).resolve().parent.parent;F=D/arm;F.mkdir(mode=0o700)
    with zipfile.ZipFile(cfg['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
    members['agent.py']=(G/'retry/pulse321_agent.py').read_bytes()
    members['retry/shield319_constants.py']=('ENABLED=True\nARM='+repr(arm)+'\n').encode()
    q=F/'policy.zip'
    with zipfile.ZipFile(q,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,b in sorted(members.items()):
            item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
    q.chmod(0o600)
    out=dict(cfg,archive_path=str(q),archive_sha256=sha(q),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()})
    save(F/'candidate-config.json',out);return out


def prepare(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage321';assert not D.exists();D.mkdir(mode=0o700)
    old=read(R/'stage319/plan.json');prior=R/'project-effective-budget-v327.json';v=read(prior);assert v['research_remaining']==456
    roads=['T2950','N2','T2954'];base={r['road']:r for r in old['baseline296']['results']};joint={}
    for r in roads:joint[r]=read(R/('stage319' if r=='T2950' else 'stage320')/'evaluations'/r/'result.json')
    estimate=2*sum(max(base[r]['native_actions'],joint[r]['native_actions']) for r in roads)
    cap=estimate+6*20;increment=cap-v['research_remaining'];assert (estimate,cap,increment)==(2084,2204,1748)
    grant=dict(stage=321,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_or_joint_max_three=sum(max(base[r]['native_actions'],joint[r]['native_actions']) for r in roads),
        two_arm_expected_native=estimate,measured319_max_extra_per_run=20,uncertainty_allowance=120,planned_native_cap=cap,
        additional_research=increment,research_after=cap,B_after=1354420,scope='Explicit selected3 x2 ablation only; reasonable research extension, no reserve or automatic extra policies')
    save(D/'budget-extension.json',grant);v.update(version=328,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=increment,
        B_operating_cap=1354420,research_remaining=cap,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'))
    assert not (R/'project-effective-budget-v328.json').exists();save(R/'project-effective-budget-v328.json',v)
    p=dict(stage=321,deadline_utc=old['deadline_utc'],roads=roads,baseline={r:base[r] for r in roads},joint=joint,
        cases=old['cases'],initial_observations=old['initial_observations'],base_controller_theta=old['base_controller_theta'],sandbox_path=old['sandbox_path'],
        phase_caps=dict(evaluation=cap),native_cap=cap,
        order=[dict(road=r,arm=a) for i,r in enumerate(roads) for a in (['A','B'] if i%2==0 else ['B','A'])],
        rule='Same exact319 geometry/trigger/latch/horizon/numbers. A steering-only retains originalgas/brake; B retains originalsteering and gas0/brakefloor.5. At mostone action, then296 with actual memory. No modified trigger, threshold or source model.',
        judgment='Selected after320 outcomes; causal diagnostic set, not generalization. Observe allsix once, no settings/checkpoint changes or skipped arms after losses. Report each road/arm completion,time,damage,firstcontact and actualpulse; cached296/joint reuse. No promotion,DEV,HOLDOUT,SEALED.',
        stop='Official ended/truncated only; cap or technical error is unobserved, notDNF. No native replay. Budget shortfall reported separately.')
    p['configs']={a:package(old['on_config'],D,a) for a in ['A','B']}
    paths=[G/'retry/pulse321_stage.py',G/'retry/pulse321_agent.py',G/'retry/pulse321_episode.py',R/'stage319/plan.json',R/'project-effective-budget-v328.json']
    for a in ['A','B']:paths.append(Path(p['configs'][a]['archive_path']))
    for r in roads:
        F=R/('stage319' if r=='T2950' else 'stage320')/'evaluations'/r;paths.extend([F/'result.json',F/'trace-private.jsonl'])
    paths += [Path(old['on_config']['archive_path']),Path(old['on_config']['worker_path'])]
    p['hashes']={str(q):sha(q) for q in paths}
    save(D/'previous-current-champion.json',read(R/'current-champion.json'));save(D/'plan.json',p)
    (D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,evaluation=0))
    print(json.dumps(grant),flush=True)


def verify(D):
    p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(q)==h,q
    return p


def run(R):
    D=R/'stage321';p=verify(D);assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()))
    results=[];error=None;theta=p['base_controller_theta']
    for item in p['order']:
        road,arm=item['road'],item['arm'];remaining=p['native_cap']-read(D/'budget.json')['actions']
        if remaining<=0:break
        F=D/'evaluations'/(arm+'_'+road);assert not F.exists();F.mkdir(parents=True,mode=0o700)
        save(F/'job.json',dict(private_stage=str(D),phase='evaluation',native_cap=remaining,road=road,arm=arm,case=p['cases'][road],config=p['configs'][arm],
            initial_observation_sha256=p['initial_observations'].get(road),ceiling=float(45*np.exp(theta[5])),steering_gain=float(np.exp(theta[2]))))
        log=(F/'driver-private.log').open('x');(F/'driver-private.log').chmod(0o600)
        proc=subprocess.Popen([sys.executable,'-m','retry.pulse321_episode','--job',str(F/'job.json')],stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        rc=proc.wait();log.close()
        if not (F/'result.json').exists():error='Childexit'+str(rc)+':missing receipt, no replay';break
        r=dict(read(F/'result.json'),arm=arm);results.append(r);save(D/'partial-private.json',results)
        print(json.dumps({k:r.get(k) for k in ['arm','road','completed','actual_DNF','native_actions','lap_ms','damage','technical_error','censored']}),flush=True)
        if r['technical_error'] or r['censored']:break
    save(D/'outcome-private.json',dict(results=results,technical_error=error,
        unobserved=[x for x in p['order'] if not any(r['road']==x['road'] and r['arm']==x['arm'] and not r['technical_error'] and not r['censored'] for r in results)],
        wall_s=time.time()-read(D/'opening.json')['epoch']))
    print('321 sixarm execution closed; no parameter change',flush=True)


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage321';p=verify(D);o=read(D/'outcome-private.json');rr=o['results'];b=read(D/'budget.json');assert not (D/'cost.json').exists()
    assert sum(r['native_actions'] for r in rr)==b['actions']<=p['native_cap'];details=[];events={}
    for r in rr:
        assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
        rows=[json.loads(s) for s in (D/'evaluations'/(r['arm']+'_'+r['road'])/'trace-private.jsonl').read_text().splitlines()]
        assert len(rows)==r['native_actions'];applied=[x for x in rows if x['shield_audit']['applied']];assert len(applied)<=1
        first=applied[0]['step'] if applied else None
        reference=R/('stage319' if r['road']=='T2950' else 'stage320')/'evaluations'/r['road']/'trace-private.jsonl'
        old=[json.loads(s) for s in reference.read_text().splitlines()]
        expected=next((x['step'] for x in old if x['shield_audit']['applied']),None);assert first==expected
        for x,y in zip(rows[:first-1],old[:first-1]):
            assert x['action']==y['action'] and x['features']==y['features'] and x['memory']==y['memory']
        if first:
            event=applied[0];g=event['shield_audit'];og=old[first-1]['shield_audit'];assert event['features']==old[first-1]['features']
            for k in ['base','tracked_obstacles','HUD_speed','HUD_yaw','HUD_joint','original_margin_m','choices','selected_index']:
                assert g[k]==og[k],k
            a=np.array(event['action'],np.float32);base=np.array(g['base'],np.float32);chosen=g['choices'][g['selected_index']]['steering']
            if r['arm']=='A':assert a[0]==np.float32(chosen) and np.array_equal(a[1:],base[1:])
            else:assert a[0]==base[0] and a[1]==0 and a[2]==np.float32(max(float(base[2]),.5))
            events[(r['road'],r['arm'])]=event
        for x in rows:
            if not x['shield_audit']['applied']:assert x['action']==x['shield_audit']['base']
            assert np.float32(x['memory'])==np.float32(x['action'][0])
        details.append(dict(road=r['road'],arm=r['arm'],interventions=len(applied),actual_changed_actions=sum(x['action']!=x['shield_audit']['base'] for x in rows),
            first_applied=first,first_contact=next((x['step'] for x in rows if x['collision']),None),
            pulse_base=applied[0]['shield_audit']['base'] if applied else None,pulse_action=applied[0]['action'] if applied else None,
            exact_joint_prefix=True,trigger_input_and_model_exact=True))
    pairchecks=[]
    for road in p['roads']:
        if (road,'A') not in events or (road,'B') not in events:continue
        ga=events[(road,'A')]['shield_audit'];gb=events[(road,'B')]['shield_audit']
        assert ga['observation_sha256']==gb['observation_sha256'] and ga['policy_state_before']==gb['policy_state_before']
        pairchecks.append(dict(road=road,pixel_and_full_policy_prestate_exact=True,trigger_step=events[(road,'A')]['step']))
    prior=R/'project-effective-budget-v328.json';v=read(prior)
    cost=dict(stage=321,new_wrapper_actions=b['actions'],native_cap=p['native_cap'],new_official_runs=len(rr),reused_baseline_and_joint_runs=6,
        raw_step_ticks=sum(r['raw_step_ticks'] for r in rr),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in rr),
        runner_CPU_s=sum(r['runner_CPU_s'] for r in rr),actor_CPU_s=sum(r['actor_CPU_s'] for r in rr),total_native_wall_s=o['wall_s'],
        additional_research=1748,new_source_physics_ticks=0,new_fits_or_PPO=0,new_paid_resources=0,
        actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],
        final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1354420)
    save(D/'cost.json',cost);v.update(version=329,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,
        cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage321_new_wrapper_actions=b['actions'])
    assert not (R/'project-effective-budget-v329.json').exists();save(R/'project-effective-budget-v329.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==321 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json')
    safe=lambda r:{k:r.get(k) for k in ['road','arm','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']}
    pub=dict(stage=321,rule=p['rule'],judgment=p['judgment'],budget_extension=read(D/'budget-extension.json'),
        results=[safe(r) for r in rr],baseline=[safe(p['baseline'][r]) for r in p['roads']],joint=[safe(p['joint'][r]) for r in p['roads']],
        details=details,matched_trigger_legal_state=pairchecks,fully_observed=len(rr)==6 and not any(r['technical_error'] or r['censored'] for r in rr),
        unobserved=o['unobserved'],technical_error=o['technical_error'],cost=cost,champion296_maintained=True,
        DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,automatic_extension=False,
        limitations=['Three roads selected after320 outcomes; diagnostic conditional set, not generalization.',
            'Single pulse components followed by own296 closed-loop states; not an additive decomposition of all later dynamics.',
            '319 model/false-warning limitations unchanged; no fitted or privileged runtime inputs.'])
    save(G/'retry/pulse321_result.json',pub);print(json.dumps(dict(results=pub['results'],details=details,cost=cost)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','run','close']);a.add_argument('--private-root',type=Path,required=True)
    x=a.parse_args();globals()[x.phase](x.private_root.resolve())
