"""Freeze one positive-history candidate and complete saved-cohort gate."""
import datetime,hashlib,zipfile,time
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage365';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def build(R):
 D=R/'stage365';assert not D.exists();D.mkdir(mode=0o700);q=read(R/'stage357/plan.json');base=q['configs']['variant'];assert sha(base['archive_path'])==base['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad'
 with zipfile.ZipFile(base['archive_path']) as z:old={n:z.read(n) for n in z.namelist()}
 assert {n:hashlib.sha256(b).hexdigest() for n,b in old.items()}==base['members_sha256'];new=dict(old);new['retry/support342_logic.py']=(G/'retry/history365_logic.py').read_bytes();source=new['retry/nominal238_base.py'].decode();a="if h[3] == 0 or not e['low']]";b="if h[3] == 0 or not e['low'] or e['positive_history']]";assert source.count(a)==1;new['retry/nominal238_base.py']=source.replace(a,b).encode();assert {n for n in old if old[n]!=new[n]}=={'retry/support342_logic.py','retry/nominal238_base.py'}
 archive=D/'history365.zip'
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(new.items()):
   item=zipfile.ZipInfo(name,date_time=(2026,10,16,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100444<<16;z.writestr(item,data)
 archive.chmod(0o600);variant=dict(base,archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in new.items()})
 cases=[]
 for c0 in q['cases']+q['untouched_cases']:
  c=dict(c0);c['cohort']='original357';c['baseline_reference']=str(R/'stage357'/c['key']/'variant/records-private.jsonl') if c0 in q['cases'] else None;c['reference_format']='cached';cases.append(c)
 def actual(key,prefix,cohort):
  trace=R/prefix/'trace-private.jsonl';return dict(key=key,road=key,group=cohort,cohort=cohort,records=str(trace),expected_tracker=str(trace),pixels=str(R/prefix/'frames-actions-private.npz'),GT=None,format='actual',count=len(trace.read_text().splitlines()),baseline_reference=str(trace),reference_format='actual')
 for key in read(R/'stage363/plan.json')['order']:cases.append(actual('363_'+key,'stage363/'+key+'/B','all363'))
 for stage,key in [(358,'O2'),(359,'N2'),(360,'T29511'),(361,'T2950'),(362,'T2954')]:cases.append(actual(f'actual{stage}_{key}',f'stage{stage}/B','other_actual357'))
 assert len(cases)==30 and sum(c['count'] for c in cases)==8140;mandatory=['N2_337','N2_340','actual359_N2'];maxacts=2*sum(c['count'] for c in cases if c['baseline_reference']);maxresets=2*sum(bool(c['baseline_reference']) for c in cases)
 files=[G/f'retry/{n}.py' for n in ['history365_logic','history365_stage','history365_run','history365_close','frozen_composite_runtime','support342_logic','confidence341_run','lineage339_audit','package349_run','probe338_stage']]+[R/'stage357/plan.json',R/'stage364/summary-private.json',R/'stage363/summary-private.json',R/'project-effective-budget-v380.json',R/'research-deadline-current.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',Path(base['archive_path']),archive,Path(base['worker_path']),Path(q['sandbox_path']),R/'stage349/candidate/reset-private.json']
 for c in cases:
  files += [Path(c[k]) for k in ['records','expected_tracker','pixels']]
  if c.get('GT'):files.append(Path(c['GT']))
  if c['baseline_reference']:files.append(Path(c['baseline_reference']))
 for key in ['N2_337','N2_340']:files.append(R/f'stage342/{key}/baseline/records-private.jsonl')
 v=read(R/'project-effective-budget-v380.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1291215,22190,84000,0)
 p=dict(stage=365,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],configs=dict(baseline=base,variant=variant),sandbox_path=q['sandbox_path'],cases=cases,mandatory_actor_cases=mandatory,
 change='Exactlyoneconcept: positive_history=ownrawroadneighbors>0 OR positive_historyofuniqueexistingdedupmatchedpredecessor. Multiplematchesdo notinherit. Same-frameexistingdedupedgesincludedanddiagnosed. Retainedmetadataunchangedbetweenbirths; age0guardmaintained; retainedlowwithpositivehistorykept. Existingdistance2m/transport/expiry/detection/controllers/models unchanged; GT/condition/frame/UIDnotruntimeexceptions.',
 design='Preflight8140inputcontexts30trajectories: original35712/2792 +all36313/3810 +fiveactual357/1538. Someobservationsduplicated/shared, notindependenttrials. Mechanicallyselectpairedactorcaseswhereactualroutingmembershipdiffers, plusmandatoryN2three. Othercasesrequireall-inputrouting/sourceinduction, no freshactorclaim.',
 gates='Preflight anyknownsupported directorbirth-supportedretained actualroutingloss, confirmeduniqueedgepositiveorigintransferbetween distinctGT-supportedfixtures onlowbirth, orcriticalN2membershiploss stopsbeforeactors. Unresolved/missingGTpropagationisambiguous, reportednotnegativegroundtruth. Actorbaseline mustreproducequalified357records beforevariant. Variant actualmetadata/membershipmustmatchpreflight; support gateandmandatoryN2fulloutput/normalmemorypreservation mandatory. Anyreproduction/integrityfailure stops; no retry/tuning/extraarms.',
 N2='OnN2_337andN2_340samefixedinputs: preservecritical121:0retainedexclusion127-129ages6-8andall357outputs; comparetohistoricalsame-inputno-filter342baseline path127-129,target128-129,firstfullcommand127,firststeering128. No newnofilteractor. Actual359cachebaselineunchangednotanewworldcomparison.',
 budget=dict(new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,research_remaining=22190,final_reserve=84000,actor_act_cap=maxacts,actor_commit_cap=maxacts,actor_reset_cap=maxresets,preflight_metadata_updates=8140,standalone_diagnostic_calls=0),source_hashes={str(f):sha(f) for f in files})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'call-budget.json',dict(actor_act_calls=0,actor_commit_calls=0,actor_resets=0));print('365registered:8140savedcontexts, separatecandidate, native0; mechanicalpairs+3N2cases; no tuning.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
