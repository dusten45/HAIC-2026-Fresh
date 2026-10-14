"""Unmodified319 policy: twelve remaining TRAIN, reuse six, no DEV or promotion."""
import argparse,datetime,json,time,subprocess,sys,os
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import diagnose


def prepare(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage322';assert not D.exists();D.mkdir(mode=0o700)
    old=read(R/'stage319/plan.json');chosen=read(R/'stage321/plan.json');prior=R/'project-effective-budget-v329.json';v=read(prior);assert v['research_remaining']==572
    previous=[r for r in read(R/'stage321/outcome-private.json')['results'] if r['arm']=='B']
    assert len(previous)==3 and all(not r['technical_error'] and not r['censored'] for r in previous)
    roads=[r['road'] for r in old['baseline296']['results'] if r['road'] not in chosen['roads']]
    baseline={r['road']:r for r in old['baseline296']['results']};measured=sum(baseline[r]['native_actions'] for r in roads)
    cap=measured+15*20;increment=cap-v['research_remaining'];assert (measured,cap,increment)==(4168,4468,3896)
    grant=dict(stage=322,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),baseline_remaining15_native=measured,
        measured319_max_extra_per_road=20,allowance=300,planned_native_cap=cap,additional_research=increment,
        research_after=cap,B_after=1358316,scope='Explicit322 fixed remaining15 comparison only, preserve84000reserve',
        uncertainty='Measured allowance, not a guarantee of all endpoint costs; no cutoff classified as DNF.')
    save(D/'budget-extension.json',grant);v.update(version=330,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=increment,
        B_operating_cap=1358316,research_remaining=cap,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'))
    assert not (R/'project-effective-budget-v330.json').exists();save(R/'project-effective-budget-v330.json',v)
    p=dict(stage=322,deadline_utc=old['deadline_utc'],baseline296=old['baseline296'],previous321B=previous,roads=roads,
        cases=old['cases'],initial_observations=old['initial_observations'],on_config=chosen['configs']['B'],
        base_controller_theta=old['base_controller_theta'],sandbox_path=old['sandbox_path'],phase_caps=dict(extension=cap),native_cap=cap,
        rule='Exact frozen321B archive/worker; original319geometry,horizon,sampling,trigger,counterfactual steering gate,latch. Keep originalsteering,gas0,brakefloor.5 foroneaction,then296 actualmemory. No conditional/roadwise policy change.',
        comparison='All15 once plus reused post-selected321 B three =>full18 vs29617/18. Countfirst/equalstrict commonmean. Report diagnosed3 and new15 separately; damage notveto. NoDEV,HOLDOUT,SEALED,promotion or automatic expansion.',
        stop='Official ended/truncated only; cap/technical error unobserved,notDNF. No native replay. Before a new road, report insufficiency if remaining is below measured baseline pending costs.')
    paths=[G/'retry/brake322_stage.py',G/'retry/brake322_episode.py',R/'stage321/plan.json',R/'stage321/outcome-private.json',R/'stage321/cost.json',R/'project-effective-budget-v330.json',Path(p['on_config']['archive_path']),Path(p['on_config']['worker_path'])]
    paths += [R/'stage321/evaluations'/('B_'+r['road'])/'result.json' for r in previous]
    p['hashes']={str(q):sha(q) for q in paths}
    assert sha(Path(p['on_config']['archive_path']))==p['on_config']['archive_sha256']
    save(D/'previous-current-champion.json',read(R/'current-champion.json'));save(D/'plan.json',p)
    (D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,extension=0))
    print(json.dumps(grant),flush=True)

def verify(D):
    p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(q)==h,q
    return p


def run(R):
    D=R/'stage322';p=verify(D);assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()))
    results=[];error=None;shortfall=None;theta=p['base_controller_theta']
    for index,road in enumerate(p['roads']):
        remaining=p['native_cap']-read(D/'budget.json')['actions']
        pending=[r for r in p['baseline296']['results'] if r['road'] in p['roads'][index:]]
        pending_cost=sum(r['native_actions'] for r in pending)
        if remaining<pending_cost:
            shortfall=dict(remaining=remaining,pending_roads=p['roads'][index:],measured_baseline_pending_native=pending_cost,estimated_additional=pending_cost-remaining);break
        F=D/'evaluations'/road;assert not F.exists();F.mkdir(parents=True,mode=0o700)
        save(F/'job.json',dict(private_stage=str(D),phase='extension',native_cap=remaining,road=road,case=p['cases'][road],
            config=p['on_config'],initial_observation_sha256=p['initial_observations'].get(road),
            ceiling=float(45*np.exp(theta[5])),steering_gain=float(np.exp(theta[2]))))
        log=(F/'driver-private.log').open('x');(F/'driver-private.log').chmod(0o600)
        proc=subprocess.Popen([sys.executable,'-m','retry.brake322_episode','--job',str(F/'job.json')],stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        rc=proc.wait();log.close()
        if not (F/'result.json').exists():error='Childexit'+str(rc)+':no endpoint, no replay';break
        r=read(F/'result.json');results.append(r);save(D/'partial-private.json',results)
        print(json.dumps({k:r.get(k) for k in ['road','completed','actual_DNF','native_actions','lap_ms','technical_error','censored']}),flush=True)
        if r['technical_error'] or r['censored']:
            shortfall=dict(remaining=p['native_cap']-read(D/'budget.json')['actions'],current_road=road,pending_roads=p['roads'][index+1:],
                measured_baseline_pending_native=sum(x['native_actions'] for x in p['baseline296']['results'] if x['road'] in p['roads'][index+1:]));break
    save(D/'outcome-private.json',dict(results=results,technical_error=error,shortfall=shortfall,
        unobserved=[r for r in p['roads'] if not any(x['road']==r and not x['technical_error'] and not x['censored'] for x in results)],
        wall_s=time.time()-read(D/'opening.json')['epoch']))
    print('322 fixed15 execution closed',flush=True)


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage322';p=verify(D);o=read(D/'outcome-private.json');b=read(D/'budget.json');rr=o['results']
    assert not (D/'cost.json').exists();assert sum(r['native_actions'] for r in rr)==b['actions']<=p['native_cap']
    signals=[]
    for r in rr:
        assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
        rows=[json.loads(s) for s in (D/'evaluations'/r['road']/'trace-private.jsonl').read_text().splitlines()];assert len(rows)==r['native_actions']
        applied=[x for x in rows if x['shield_audit']['applied']];assert len(applied)<=1
        for x in rows:
            g=x['shield_audit'];assert np.float32(g['executed_memory'])==np.float32(x['action'][0])
            if g['applied']:assert g['first_overlap'] and g['strict_improvement'] and x['action'][1]==0 and np.float32(x['action'][2])==np.float32(max(g['base'][2],.5))
            else:assert x['action']==g['base']
        signals.append(dict(road=r['road'],actions=len(rows),interventions=len(applied),first_applied=applied[0]['step'] if applied else None))
    prior=R/'project-effective-budget-v330.json';v=read(prior)
    cost=dict(stage=322,new_wrapper_actions=b['actions'],native_cap=p['native_cap'],new_official_runs=len(rr),reused321_B_runs=3,
        raw_step_ticks=sum(r['raw_step_ticks'] for r in rr),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in rr),
        runner_CPU_s=sum(r['runner_CPU_s'] for r in rr),actor_CPU_s=sum(r['actor_CPU_s'] for r in rr),total_native_wall_s=o['wall_s'],
        new_source_physics_ticks=0,new_fits_or_PPO=0,new_paid_resources=0,additional_research=3896,
        actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],
        final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1358316)
    save(D/'cost.json',cost);v.update(version=331,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,
        cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage322_new_wrapper_actions=b['actions'])
    assert not (R/'project-effective-budget-v331.json').exists();save(R/'project-effective-budget-v331.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==322 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json')
    full=p['previous321B']+rr;fully=len(rr)==15 and not any(r['technical_error'] or r['censored'] for r in rr)
    base=p['baseline296']['results'];partbase=[r for r in base if r['road'] in p['roads']]
    def summary(a,baseline):
        diag=diagnose(a,baseline);nc=sum(r['completed'] for r in a);bc=sum(r['completed'] for r in baseline)
        eligible=nc>bc or(nc==bc and diag['common_mean_delta_ms'] is not None and diag['common_mean_delta_ms']<0)
        return dict(candidate_completions=nc,baseline_completions=bc,paired=diag,count_first_improved=bool(eligible),candidate_damage_sum=sum(r['damage'] for r in a),baseline_damage_sum=sum(r['damage'] for r in baseline))
    safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']}
    pub=dict(stage=322,rule=p['rule'],comparison=p['comparison'],budget_extension=read(D/'budget-extension.json'),
        new15=[safe(r) for r in rr],new15_baseline=[safe(r) for r in partbase],reused321_B_three=[safe(r) for r in p['previous321B']],
        full18=[safe(r) for r in full],new15_summary=summary(rr,partbase) if fully else None,full18_summary=summary(full,base) if fully else None,
        fully_observed=fully,signals=signals,unobserved=o['unobserved'],shortfall=o['shortfall'],technical_error=o['technical_error'],cost=cost,
        next_stage_candidate=bool(fully and summary(full,base)['count_first_improved']),champion296_maintained=True,
        DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,automatic_extension=False,
        limitations=['Known18TRAIN; three selectedafter320 and reused321 B outcomes, new15 separated. Not new DEV or generalization proof.',
            '319 geometry warning inaccuracies and sampling/model limits preserved; policy effect is not certified collision prediction.',
            '321 component diagnosis preserved; no new component/threshold search or prior319 joint results reused for B.'])
    save(G/'retry/brake322_result.json',pub);print(json.dumps(dict(new15=pub['new15'],new15_summary=pub['new15_summary'],full18_summary=pub['full18_summary'],cost=cost,next_stage_candidate=pub['next_stage_candidate'])),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','run','close']);a.add_argument('--private-root',type=Path,required=True)
    x=a.parse_args();globals()[x.phase](x.private_root.resolve())
