"""Freeze and allocate before authorized release of existing conditional DEV."""
import datetime,time,sys,zipfile,hashlib
from pathlib import Path
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage372';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def verify_case(R,key,arm,full=False):
 p=verify(R,full);D=R/'stage372';binding=read(D/'cases-frozen-private.json');assert sha(D/'cases-frozen-private.json')==(D/'cases-frozen.sha256').read_text().strip();assert key in binding['order'] and arm in ['A','B'];return dict(config=p['configs'][arm],case=binding['cases'][key],observer_rng_seed=372,runtime_versions=p['runtime_versions'],sandbox_path=p['sandbox_path'],episode_cap=2000)

def build(R):
 D=R/'stage372';assert not D.exists();D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v388.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1300064,20499,84000,0,1404563)
 q=read(R/'stage365/plan.json');a=read(R/'stage296/champion-config.json');old=read(R/'stage296/plan.json');original=next(c['config'] for c in old['candidates'] if c['label']=='g1p4');assert original['archive_sha256']==a['archive_sha256'];a.update(worker_path=original['worker_path'],worker_sha256=original['worker_sha256']);configs=dict(A=a,B=q['configs']['variant'])
 assert a['archive_sha256']=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and configs['B']['archive_sha256']=='65df88a5b2391675e49c3f39259adab0f8a791da5ab58ea620cbe130b0a9ce34'
 for c in configs.values():
  assert sha(c['archive_path'])==c['archive_sha256'] and sha(c['worker_path'])==c['worker_sha256']
  with zipfile.ZipFile(c['archive_path']) as z:
   assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(c['members_sha256'])
   assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in c['members_sha256'].items())
 seal=read(R/'stage297/screen-seal.json');contract=read(R/'stage371/summary-private.json');assert not seal['opened_for_performance'] and contract['contract_only'];assert not (R/'stage297/DEV-opened-by372.json').exists()
 files=[G/f'retry/{n}.py' for n in ['confirm372_stage','confirm372_episode','confirm372_run','confirm372_close','frozen_composite_runtime','pixel_sandbox_runtime','qualify_pixel_package','source_vehicle_transition','episode337_run','pedal331_run','probe338_stage','package349_run','diagnose','full_route_reproduction','confidence341_run','history365_logic','lineage339_audit','pair343_close','episode367_stage']]+[G/'README.md',G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',R/'stage371/summary-private.json',R/'stage371/plan.json',R/'stage297/screen-seal.json',R/'stage365/plan.json',R/'stage296/plan.json',R/'stage296/champion-config.json',R/'current-champion.json',R/'stage296/champion-manifest.json',R/'protected-query-ledger-v1.json',R/'HOLDOUT.opened',R/'stage367/B/reset-policy-private.json',R/'project-effective-budget-v388.json',R/'research-deadline-current.json',Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'))
 for c in configs.values():files += [Path(c['archive_path']),Path(c['worker_path'])]
 markers={str(f):sha(f) for f in [R/'protected-query-ledger-v1.json',R/'HOLDOUT.opened',R/'current-champion.json',R/'stage297/screen-seal.json']}
 p=dict(stage=372,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],configs=configs,sandbox_path=q['sandbox_path'],runtime_versions=read(R/'stage369/summary-private.json')['comparability']['python_numpy_opencv_versions'],registered_manifest_references=seal['registrations'],case_source=str(R/'stage297/fresh-DEV-private.json'),declared_split='DEV_COMPLETION_CEM_297',order_rule='Exactoriginal12listandregisteredcase.arm_order; sixAB/sixBA, noresample/substitute',
 authorization='Explicitparent372:releaseexistingperformance-unopenedconditionalDEV12onlyforfrozen365vs296,24actualepisodes,grant27501beforeopening20499=>48000;actualconsumptiononly;SEALED16andreserve84000untouched;noautomaticpromotion.',
 judgment=contract['proposed_confirmation_contract']['judgment'],gates=contract['proposed_confirmation_contract']['stops'],after_exposure=contract['proposed_confirmation_contract']['after_exposure'],
 contract='Ownpixels/fullreturnedfloat32controls/normalmemory. SameCPU1/thread1/memory1024000000/IPC5s/CPU120s. Existing296preview286and365passive357workershashbound;policyZIPsunmodified. GTcapturedreadonlyneveractorinput;posthoconlylabels/gates. Initialregisteredseed/options/geometry/obstaclesandpairimagechecked,fullphysics/accessRNGcapturedandcomparedposthoc. No forcedpostbranchpixels. No retry/retune/alternate/capextension.',
 stops='Officialfinish/retire/otherofficialtruncationfirst;else2000protocolcensor/deadline/technicalstop. NormalDNFcontinues. Technical/integrity/initialmismatch/supportloss/confirmedwronglowtransferstopsremainingimmediatelyafteraudit. All24definitiveuncensoredplusgatesneededforjudgment.',
 budget=dict(research_before=20499,additional_research=27501,research_after_grant=48000,total_native_cap=48000,per_episode_cap=2000,actor_act_cap=48000,actor_commit_cap=48000,max_resets=24,final_reserved_actions=84000,final_reserve_used=0),protected_marker_hashes=markers,source_hashes={str(f):sha(f) for f in files})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget-extension.json',dict(stage=372,additional_research_actions=27501,research_before=20499,research_after_grant=48000,final_reserve_change=0,authorization=p['authorization']))
 v.update(version=389,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v388.json'),prior_budget_sha256=sha(R/'project-effective-budget-v388.json'),B_increment=27501,B_operating_cap=1432064,research_remaining=48000,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'));assert not (R/'project-effective-budget-v389.json').exists();save(R/'project-effective-budget-v389.json',v)
 save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=48000,reset_cap=24));print('372 frozen beforecontentrelease, grant27501 allocated, cap48000/per-episode2000.',flush=True)

def release(R):
 D=R/'stage372';p=verify(R,True);assert not (D/'release-private.json').exists();assert read(R/'project-effective-budget-v389.json')['research_remaining']==48000 and read(D/'native-budget.json')['resets']==0
 # Only now read the authorized registered conditions; no simulator queries.
 regs=[]
 for ref in p['registered_manifest_references']:
  assert sha(ref['path'])==ref['sha256'];m=read(ref['path']);regs.extend(m['cases'])
 cases=read(p['case_source']);assert len(cases)==len(regs)==12
 for c,r in zip(cases,regs):assert {k:v for k,v in c.items() if k!='public_label'}=={k:v for k,v in r.items() if k!='public_label'}
 order=[c['public_label'] for c in cases];assert order==['S297'+str(i) for i in range(12)] and [c['arm_order'] for c in cases]==[['A','B'],['B','A'],['A','B'],['B','A']]*3
 binding=dict(order=order,cases={c['public_label']:c for c in cases},manifest_sha256=sha(p['case_source']),registered_manifests=p['registered_manifest_references']);save(D/'cases-frozen-private.json',binding);(D/'cases-frozen.sha256').write_text(sha(D/'cases-frozen-private.json')+'\n');(D/'cases-frozen.sha256').chmod(0o600)
 opening=dict(stage=372,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(D/'plan.json'),case_binding_sha256=sha(D/'cases-frozen-private.json'),declared_split='DEV_COMPLETION_CEM_297',permanently_performance_exposed_from_this_execution=True,not_HOLDOUT_or_SEALED=True,arms={k:c['archive_sha256'] for k,c in p['configs'].items()},no_retuning=True,queries_file=str(D/'query-ledger-private.jsonl'))
 save(D/'release-private.json',opening);save(R/'stage297/DEV-opened-by372.json',opening);(D/'query-ledger-private.jsonl').touch(mode=0o600);print('372 release recorded permanently; original12/ABBA binding frozen beforeanyreset.',flush=True)
if __name__=='__main__':
 R=Path(sys.argv[1]).resolve();build(R) if sys.argv[2]=='build' else release(R)
