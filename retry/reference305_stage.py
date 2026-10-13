"""One preregistered legal one-frame reference comparison; no fitting or DEV opening."""
import argparse,datetime,hashlib,time,zipfile
from pathlib import Path
from retry.path271_run import read,save,sha
from retry.completion297_search import metrics,diagnose

RULE='On fresh empty route only: accepted existing tracker affine transports immediately previous fresh route in its pixel coordinates; preserve directed order, sampled current allowed mask and forward points, require original lookahead length. Missing affine or short/invalid path => exact fallback. No chained retention.'
def prepare(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage305';assert not D.exists();D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v312.json');assert v['research_remaining']==7736 and v['actual_cumulative_wrapper_actions']==1138264
 old=read(R/'stage299/plan.json');base=old['baseline296'];cfg=dict(base['config']);source=Path(cfg['archive_path'])
 with zipfile.ZipFile(source) as z:members={n:z.read(n) for n in z.namelist()}
 members['retry/reference305_base.py']=members['agent.py'];members['agent.py']=(G/'retry/reference305_agent.py').read_bytes()
 name='retry/temporal_agent.py';s=members[name].decode();needle='        predicted = []';assert s.count(needle)==1;s=s.replace(needle,'        self.reference_motion305 = None if transform is None else transform.copy()\n'+needle);members[name]=s.encode()
 archive=D/'reference305.zip'
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(members.items()):item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
 archive.chmod(0o600);cfg.update(archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},worker_path=str(G/'retry/reference305_worker.py'),worker_sha256=sha(G/'retry/reference305_worker.py'))
 pilot=['T2950','T2954'];extension=[r for r in old['roads'] if r not in pilot];refs=[read(R/'stage300'/(r+'_296')/'result.json') for r in pilot];extra=[next(x for x in base['results'] if x['road']==r) for r in extension]
 sources=[G/'retry'/n for n in ['reference305_agent.py','reference305_worker.py','reference305_episode.py','reference305_run.py','reference305_stage.py']]+[source,archive,R/'project-effective-budget-v312.json']
 p=dict(stage=305,deadline_utc='2026-10-16T10:01:55+00:00',baseline296=base,candidate=dict(theta=base['theta'],config=cfg),cases=old['cases'],initial_observations=old['initial_observations'],pilot=pilot,pilot_baseline=refs,extension=extension,extension_baseline=extra,sandbox_path=old['sandbox_path'],phase_caps=dict(training=6000),state_variables=['immediately previous fresh route in its pixel coordinate chart','existing accepted image affine copied read-only by tracker','per-call recovery audit; recovered routes never refresh previous fresh state'],rule=RULE,hypothesis='One-frame affine-transported reference on fresh route loss prevents stale command continuation and improves completion-first TRAIN performance.',pilot_gate='Greater completed count, or equal count and strictly faster common-completion mean, else stop without alternative.',extension_rule='Only on pilot pass run remaining16TRAIN once each, total6000; no adoption or DEV.',stop='6000 native total, deadline, technical error or censor. Unknown is not DNF. No tuning, reserve, DEV, HOLDOUT, SEALED or champion change.',prior_difference='260 retains a world-coordinate GT plan with live pose;261 stores known directed edges and uses hull heading;262 rejects behind-hull targets using GT. This candidate stores only one immediately previous fresh pixel route and transports it with already computed legal LK/LMEDS image affine, no heading/pose/map/teacher/model. It changes only empty-route reference selection, no fresh-route ranking, guard, joint feedback, gain, learning, perception threshold or hazard state.171 uses transported reference only in score ties,253 blends road images; here all fresh nonempty routes remain exact296.',hashes={str(q):sha(q) for q in sources})
 save(D/'previous-current-champion.json',read(R/'current-champion.json'));save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,training=0));print('305 registered: one-frame affine reference, two TRAIN pilot, conditional16TRAIN, cap6000',flush=True)
def run(R):
 from retry.reference305_run import evaluate
 D=R/'stage305';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));pilot=[];extension=[];gate=False;error=None
 try:
  pilot=evaluate(D,p,p['pilot']);assert len(pilot)==2 and not any(x['technical_error'] or x['censored'] for x in pilot),'Incomplete pilot, no extension'
  d=diagnose(pilot,p['pilot_baseline']);c=sum(x['completed'] for x in pilot);bc=sum(x['completed'] for x in p['pilot_baseline']);gate=c>bc or (c==bc and d['common_mean_delta_ms'] is not None and d['common_mean_delta_ms']<0);save(D/'pilot-gate.json',dict(passed=bool(gate),candidate_completions=c,baseline_completions=bc,diagnostic=d));print('305 pilot gate '+str(bool(gate)),flush=True)
  if gate:
   extension=evaluate(D,p,p['extension']);assert len(extension)==16 and not any(x['technical_error'] or x['censored'] for x in extension),'Incomplete extension'
 except BaseException as e:error=type(e).__name__+': '+str(e);print(error,flush=True)
 save(D/'outcome-private.json',dict(pilot=pilot,extension=extension,pilot_gate=bool(gate),technical_error=error,wall_s=time.time()-read(D/'opening.json')['epoch']));print('305 execution closed',flush=True)
def close(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage305';p=read(D/'plan.json');o=read(D/'outcome-private.json');b=read(D/'budget.json');assert not (D/'cost.json').exists()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 rr=[read(q) for q in (D/'TRAIN').glob('*/result.json')];assert sum(x['native_actions'] for x in rr)==b['actions'];signals=[]
 import json
 for r in rr:
  assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];rows=[json.loads(s) for s in (D/'TRAIN'/r['road']/'trace-private.jsonl').read_text().splitlines()];changed=[x['step'] for x in rows if x['reference_audit']['accepted']];signals.append(dict(road=r['road'],reference_recovery_actions=len(changed),first_reference_recovery=changed[0] if changed else None,missing_target_actions=sum(x['features'][0]==1 for x in rows),collision_steps=[x['step'] for x in rows if x['collision']]))
 v=read(R/'project-effective-budget-v312.json');cost=dict(stage=305,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=b['actions'],native_cap=6000,new_official_runs=len(rr),raw_step_ticks=sum(x['raw_step_ticks'] for x in rr),raw_reset_ticks=sum(x['raw_reset_ticks'] for x in rr),episode_runner_CPU_s=sum(x['runner_CPU_s'] for x in rr),recorded_actor_CPU_s=sum(x['actor_CPU_s'] for x in rr),sum_episode_wall_s=sum(x['wall_s'] for x in rr),total_wall_s=o['wall_s'],new_source_physics_ticks=0,new_parameter_draws=0,new_fit_calls=0,new_paid_resources=0,B_operating_cap=v['B_operating_cap'],actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],final_reserved_actions=84000,final_reserve_used=0);save(D/'cost.json',cost)
 assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json');prior=R/'project-effective-budget-v312.json';v.update(version=313,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage305_new_wrapper_actions=b['actions'],budget_reason='One legal one-frame pixel reference recovery, no DEV/adoption/reserve');assert not (R/'project-effective-budget-v313.json').exists();save(R/'project-effective-budget-v313.json',v)
 ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==305 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']}
 pub=dict(stage=305,rule=p['rule'],hypothesis=p['hypothesis'],prior_difference=p['prior_difference'],pilot_baseline=[safe(r) for r in p['pilot_baseline']],pilot=[safe(r) for r in o['pilot']],pilot_gate=o['pilot_gate'],extension=[safe(r) for r in o['extension']],extension_baseline=[safe(r) for r in p['extension_baseline']],signals=signals,cost=cost,technical_error=o['technical_error'],champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False);save(G/'retry/reference305_result.json',pub);print(json.dumps(dict(pilot=pub['pilot'],gate=pub['pilot_gate'],extension=pub['extension'],signals=signals,cost=cost),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','run','close']);a.add_argument('--private-root',type=Path,required=True);x=a.parse_args();globals()[x.phase](x.private_root.resolve())
