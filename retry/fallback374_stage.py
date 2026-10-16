"""Pure296 plus the already-fixed334 fallback; one known TRAIN, cap2000."""
import datetime,time,sys,zipfile,hashlib
from pathlib import Path
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage374';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def build(R):
 D=R/'stage374';assert not D.exists();assert not any(__import__('json').loads(s).get('stage')==374 for s in (R/'experiment-cost-lines.jsonl').read_text().splitlines());D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v391.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1306464,41600,84000,0,1432064)
 base=read(R/'stage296/champion-config.json');old=read(R/'stage334/configs-private.json')['OFF']['ON'];assert sha(base['archive_path'])==base['archive_sha256']=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and sha(old['archive_path'])==old['archive_sha256']=='7da9a3dc5c6aa65b791fd96b5e58203cfb5a3192f99efccb7cbc9082b278f46f'
 with zipfile.ZipFile(base['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
 assert all(hashlib.sha256(members[n]).hexdigest()==h for n,h in base['members_sha256'].items());original_temporal=members['retry/temporal_agent.py']
 with zipfile.ZipFile(old['archive_path']) as z:
  assert z.read('retry/h1_330_base.py')==members['agent.py'];members['retry/temporal_agent.py']=z.read('retry/temporal_agent.py');members['retry/hud248_features.py']=z.read('retry/hud248_features.py')
  assert all(z.read(n)==b for n,b in members.items() if n not in ['agent.py'])
 oldline='                y -= decode_feedback_speed(image, speed) * 0.08'
 newlines='''                assert self.previous_image is not None
                previous_yaw=float(decode(self.previous_image.astype(np.float32)/255)[5])
                current_yaw=float(decode(image)[5])
                delta=.08*(previous_yaw+current_yaw)/2
                offset=np.array([x,y])-np.array([0.,decode_feedback_speed(image,speed)*.08])
                c,s=np.cos(delta),np.sin(delta)
                x,y=float(c*offset[0]+s*offset[1]),float(-s*offset[0]+c*offset[1])'''
 assert original_temporal.decode().count(oldline)==1 and original_temporal.decode().replace('import numpy as np','import numpy as np\nfrom retry.hud248_features import decode').replace(oldline,newlines).encode()==members['retry/temporal_agent.py']
 assert set(members)-set(base['members_sha256'])=={'retry/hud248_features.py'} and {n for n,h in base['members_sha256'].items() if hashlib.sha256(members[n]).hexdigest()!=h}=={'retry/temporal_agent.py'}
 assert not any('h1_' in n or 'support342' in n for n in members)
 archive=D/'fallback374.zip'
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(members.items()):z.writestr(n,b)
 archive.chmod(0o600)
 #Onlyobserveactualroutingarguments;theobserverneverselects/changeshazards.
 worker=D/'observer-worker-private.py';wsource=Path(old['worker_path']).read_text();a='''def route_observer(*args,**kwargs):
    path=original_route(*args,**kwargs)''';b='''routing_evidence=None
def route_observer(*args,**kwargs):
    global routing_evidence
    full=copy.deepcopy(agent.hazards)
    selected=copy.deepcopy(args[1] if len(args)>1 else kwargs['obstacles_override'])
    assert [list(p) for p in selected]==[list(h[:3]) for h in full]
    routing_evidence=dict(full_hazards=full,routing_hazards=selected,removed_indices=[],tracker_preserved=True)
    path=original_route(*args,**kwargs)''';assert wsource.count(a)==1;wsource=wsource.replace(a,b);needle="response['tracker_record']=tracker_record";assert wsource.count(needle)==1;wsource=wsource.replace(needle,needle+"\n    response['routing_evidence']=routing_evidence");compile(wsource,str(worker),'exec');worker.write_text(wsource);worker.chmod(0o600)
 cfg=dict(base,archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},worker_path=str(worker),worker_sha256=sha(worker));save(D/'config-private.json',cfg)
 hist=read(R/'stage361/plan.json');job=read(R/'stage295/TRAIN/T2950/g1p4/job.json');br=read(R/'stage295/TRAIN/T2950/g1p4/result.json');assert job['case']==hist['case'] and br['actual_DNF'] and br['native_actions']==315 and br['archive_sha256']==base['archive_sha256'] and br['initial_observation_sha256']==hist['expected_initial_observation_sha256']
 files=[G/f'retry/{n}.py' for n in ['fallback374_stage','fallback374_run','fallback374_close','frozen_composite_runtime','pixel_sandbox_runtime','qualify_pixel_package','source_vehicle_transition','episode337_run','pedal331_run','probe338_stage','package349_run','diagnose','full_route_reproduction','fallback334_math','confidence341_run','pair343_close']]+[G/'README.md',G/'env_wrapper.py',G/'local_runner.py',G/'damage.py',R/'stage296/champion-config.json',R/'stage296/submission296.zip',R/'current-champion.json',R/'stage296/champion-manifest.json',R/'stage334/configs-private.json',Path(old['archive_path']),Path(old['worker_path']),R/'stage361/plan.json',R/'stage295/TRAIN/T2950/g1p4/job.json',R/'stage295/TRAIN/T2950/g1p4/result.json',R/'stage373/candidate365-rejected-locked.json',R/'project-effective-budget-v391.json',R/'research-deadline-current.json',R/'protected-query-ledger-v1.json',R/'HOLDOUT.opened',D/'config-private.json',archive,worker,Path(hist['sandbox_path'])]+list((G/'core').rglob('*.py'))
 markers={str(f):sha(f) for f in [R/'current-champion.json',R/'stage296/champion-manifest.json',R/'protected-query-ledger-v1.json',R/'HOLDOUT.opened',R/'stage373/candidate365-rejected-locked.json']}
 p=dict(stage=374,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,base_config=base,case=hist['case'],expected_initial_observation_sha256=hist['expected_initial_observation_sha256'],observer_rng_seed=374,sandbox_path=hist['sandbox_path'],runtime_versions=read(R/'stage369/summary-private.json')['comparability']['python_numpy_opencv_versions'],episode_cap=2000,total_native_cap=2000,actor_act_cap=2000,reset_cap=1,
 authorization='Explicitparent374:onefrozenpure296H1OFF/fallbackON/birthroutingOFFT2950actualrun,max2000from41600existingresearch. No372materials/newsplit/control/cache/tuning/retry/extension/promotion;reserve84000untouched.',
 package_difference=dict(changed_original_members=['retry/temporal_agent.py'],added_fixed_dependency=['retry/hud248_features.py'],root_and_every_other296_member_byte_exact=True,no_H1_modules_models_or_selector=True,no_birthrouting_support_history=True,same334_fixed_fallback_bytes=True,worker_change='Readonlyrecord/assertalltrackedhazardspassedtorouting;nohazardselectionorpolicyactionchange.'),
 historical296={k:br.get(k) for k in ['completed','actual_DNF','censored','technical_error','native_actions','lap_ms','damage','visited','total_tiles','retire_reason','initial_observation_sha256','geometry_sha256','archive_sha256']},
 contract='Ownfloat32officialpixels,fullreturnedcontrols,normalownmemory. Fixedmodels/perception/trackerage/dedup/expiry/acceptedoptical/routing/controller/head/coefficients. GTreadonlycapture/posthocdiagnosticsonly,nocontrolinput. Resetidentityusesregisteredmetadata/imagehash;nohistoricalforcedactions/pixels/state/RNG.',
 stops='Firstofficialfinish/retire/otherofficialtruncation,else2000protocolcensor/currentdeadline/technicalorlegality/integrityerror. Fullhazardsmustreachrouting. No retry/reseed/substitute/capextension/retune.',
 judgment='T2950officialfinishwithlegality/integrity/supportgatespasseslocalrescuefeasibilityonly. DNF/censorrejectslocalrescue;technicalerrorunresolvednotnormalDNF. NoautomaticT2954/otherTRAIN/newDEV/HOLDOUT/SEALED/promotion. Historical296notfreshpairedcontrol;fulloldRNG/actorstateprefixunavailable;singleknownTRAINnotgeneralization.',budget=dict(research_before=41600,episode_reservation=2000,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),protected_marker_hashes=markers,excluded_directory_stats={str(f):f.stat().st_mtime_ns for f in [R/'stage372',R/'stage297']},source_hashes={str(f):sha(f) for f in files})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'reservation.json',p['budget']);save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=2000,reset_cap=1));print('374 frozen pure296+fixedfallback only, H1/birthrouting absent;oneT2950 cap2000from41600.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
