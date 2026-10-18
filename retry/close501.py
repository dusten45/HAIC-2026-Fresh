"""501 saved-only closeout: authenticate retained bytes and exact empty witness."""
import time
START=time.perf_counter();CPU=time.process_time()
import hashlib,importlib.abc,json,math,os,signal,sys,types
from fractions import Fraction as F
from pathlib import Path
class NoPhysics(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.startswith(('Box2D','core.vendor')) or name in ('retry.terminal410_model','retry.source_vehicle_transition','retry.pilot420_backend','retry.runtime501'):
   raise RuntimeError('501_CLOSEOUT_PHYSICS_FORBIDDEN:'+name)
  return None
sys.meta_path.insert(0,NoPhysics())
import numpy as np
from retry.io501 import Adapter501,CONTENT,CHUNKS
from retry.pilot420_json import json_ready,restore_bytes
from retry import envelope500
from retry.signed417_executor import canonical_projection
G=Path(__file__).resolve().parents[1];R=Path('/workspace/haic-private-retry-20261009');C=R/'stage501';D=Path('/tmp/haic-retry-stage501-private')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(json_ready(v),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def strict(p):
 def pairs(rows):
  out={}
  for k,v in rows:
   if k in out:raise ValueError('DUPLICATE_JSON_KEY')
   out[k]=v
  return out
 return json.loads(p.read_text(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
def readonly_adapter(files):
 raw=lambda p:json.loads(Path(p).read_text())
 noop=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('CLOSEOUT_WRITE_FORBIDDEN'))
 codec=types.SimpleNamespace(ORIGINAL_READ=raw,ORIGINAL_LOAD=raw,json_ready=json_ready,restore_bytes=restore_bytes,canonical=canonical,STATE_KEY='__haic_full_state_ref481__',CODEC_KEY='__haic_lossless481__')
 mods={'io481':codec,'loss389_analyze':types.SimpleNamespace(read=raw,save=noop,sha=sha),'receipt421_io':types.SimpleNamespace(save_receipt=noop)}
 runtime=types.SimpleNamespace(import_module=lambda n:mods[n],modules=mods)
 store=types.SimpleNamespace(root=D,used={p.name:('read',p.stat().st_size,sha(p)) for p in files})
 return Adapter501(runtime,store)

def run():
 check= lambda v,s: None if v else (_ for _ in ()).throw(RuntimeError(s))
 ps=sorted(p for p in D.iterdir() if p.is_file());reader=readonly_adapter(ps)
 find=lambda label:next(D.glob('*-v1-'+label))
 final=reader.read(find('result-private.json'))
 def guard(*a):
  check(final['CPU_s']+time.process_time()-CPU+10<600,'CLOSEOUT_CPU')
  check(final['wall_s']+time.perf_counter()-START+20<900,'CLOSEOUT_WALL')
 guard();signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CLOSEOUT_CPU_TIMER')));signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('CLOSEOUT_WALL_TIMER')))
 signal.setitimer(signal.ITIMER_PROF,max(.001,590-final['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.001,880-final['wall_s']))
 check(final['worlds']==final['confirmed_worlds']==final['closed_worlds']==final['created_Box2D_worlds']==2 and final['live_worlds']==0,'WORLD_CLOSURE')
 check(final['actual_ticks']==734 and final['charged_ticks']==736 and final['holds']==184,'COUNTS')
 check(final['factual_passed'] and final['status']=='PACKAGE_REJECTED','VERDICT')
 fact=reader.read(find('D501_factual-result-private.json'));cand=reader.read(find('D501_candidate_1-result-private.json'));authority=reader.read(find('D501_candidate_1-own-authority-private.json'));static=reader.read(find('static-private.json'));plan=reader.read(find('plan.json'))
 check(len(fact['factual']['records'])==149 and fact['finish']=={'lo':593,'hi':594},'FACTUAL_FULL')
 check(cand['actions']==35 and cand['scalar_stop']=='EXACT_EMPTY_SET' and cand['safe'],'CANDIDATE_STOP')
 stop=authority['unexecuted_nominal_stop'];state=stop['state'];phase=stop['after']['C']['phase'];h=state['physical']['hull'];fixed=json.loads((R/'stage269/N1-plan-private.json').read_text());nodes=json.loads((R/'stage466-numeric-recovery1/projection-and-segments-private.json').read_text())['projected_nodes'];arcs=np.r_[0.,np.cumsum(fixed['free_profile']['ds'])].tolist();q=canonical_projection(fixed['line'],h['position'],h['velocity'],phase);v=math.hypot(*h['velocity'])
 context=envelope500.context(q['arc'],v,q['sigma'],arcs,nodes);failures=envelope500.residuals(context,context['low']);check(bool(failures),'EXACT_EMPTY_WITNESS')
 check(not isinstance(failures[0],str),'EMPTY_DOMAIN_NOT_BOUNDARY_FAILURE')
 witnesses=[]
 for kind,i,k in failures:
  if kind=='CURRENT_NODE':
   witnesses.append(dict(kind=kind,node_remaining_index=i,residual_speed_m_s=float(context['v']-context['nodes'][i][1])));continue
  d,r=context['nodes'][i];t=envelope500.TIMES[k];a=context['low'];travel=context['sigma']*t+a*t*t/2
  if kind=='UNCROSSED':residual=(context['v']+a*t)**2-r*r-2*F(envelope500.BRAKE)*(d-travel)
  else:residual=context['sigma']**2+2*a*d-(r-context['v']+context['sigma'])**2
  witnesses.append(dict(kind=kind,node_remaining_index=i,boundary_s=float(t),distance_ahead_m=float(d),node_speed_m_s=float(r),residual_m2_s2=float(residual),exact_residual=str(residual)))
 witness=dict(stage=501,scope='STORED_STATE_EXACT_ALGEBRA_ONLY_NO_NEW_PHYSICS',unexecuted_candidate_hold=36,completed_candidate_holds=35,root_elapsed_s=35*.08,episode_elapsed_s=(88+140)/50,physical_time_s=state['physical']['actual_time'],current_speed_m_s=v,sigma_m_s=q['sigma'],admissible_low=str(context['low']),admissible_high=str(context['high']),failure_count=len(failures),witnesses=witnesses,law_sha256=sha(G/'retry/envelope500.py'),root_current_s_private=q['arc'],new_physics=0)
 private=C/'empty-witness-private.json';check(not private.exists(),'IMMUTABLE_WITNESS');private.write_text(json.dumps(witness,ensure_ascii=False,indent=2)+'\n');private.chmod(0o600)
 # One linear byte/JSON/ref authentication pass; no bulk raw copy or repeated
 # world qualification. Semantic state SHA uses original481 canonical codec.
 manifest={};category={'state':0,'tick':0,'bundle':0,'other':0};totalbytes=0;refs=0
 for p in ps:
  guard();value=strict(p);data=p.read_bytes();digest=hashlib.sha256(data).hexdigest()
  kind='state' if p.name.startswith('state-') else 'tick' if 'direct501-' in p.name and '-bundle' not in p.name else 'bundle' if '-bundle' in p.name else 'other'
  limit={'state':512*1024,'tick':16*1024,'bundle':64*1024,'other':4*1024**2}[kind];check(len(data)<=limit,'ACTUAL_SERIALIZED_PERFILE_CAP')
  if kind=='state':check(value['sha256']==canonical(value['full_state']),'STATE_SEMANTIC_HASH')
  manifest[p.name]=dict(bytes=len(data),sha256=digest,category=kind);category[kind]+=1;totalbytes+=len(data)
 for p in ps:
  value=strict(p)
  def visit(v):
   nonlocal refs
   if isinstance(v,dict):
    if set(v)=={CONTENT}:parts=[v[CONTENT]]
    elif set(v)=={CHUNKS,'count'}:parts=v[CHUNKS]
    else:
     for x in v.values():visit(x)
     return
    for ref in parts:
     path=Path(ref['path']);check(path.parent==D and path.name in manifest,'CONTENT_REF_SCOPE');entry=manifest[path.name];check(entry['sha256']==ref['sha256'] and entry['bytes']==ref['bytes'],'CONTENT_REF_HASH_SIZE');refs+=1
   elif isinstance(v,list):
    for x in v:visit(x)
  visit(value)
 # Original501 namespaces/physics inputs still match all frozen plan pins.
 for p,hsh in {**plan['semantic_sources'],**plan['input_pins']}.items():check(sha(p)==hsh,'SOURCE_INPUT_IMMUTABLE')
 check(sha(R/'project-effective-budget-v495.json')==plan['budget_sha256'],'BUDGET_IMMUTABLE')
 for p,hsh in json.loads((R/'stage472/plan.json').read_text())['protected'].items():check(sha(p)==hsh,'PROTECTED_IMMUTABLE')
 newworkspace=[p for folder in [C,R/'stage501-source-private'] for p in folder.rglob('*') if p.is_file()]
 combined_bytes=totalbytes+sum(p.stat().st_size for p in newworkspace);combined_files=len(ps)+len(newworkspace)
 check(combined_bytes+1024**2<256*1024**2 and combined_files+8<=2688 and category['state']<=320,'WHOLE_STORAGE_CAP')
 check(sum(x['bytes'] for x in manifest.values() if x['category']=='other')+sum(p.stat().st_size for p in newworkspace)+1024**2<16*1024**2,'OTHER_CATEGORY_CAP')
 check(category['tick']==734 and category['bundle']==184,'CAPTURE_FILE_COUNTS')
 private_manifest=C/'retention-manifest-private.json';check(not private_manifest.exists(),'IMMUTABLE_MANIFEST')
 private_manifest.write_text(json.dumps(dict(stage=501,raw_directory=str(D),raw_files=manifest,workspace_files={str(p):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in newworkspace},source_plan_ref=str(find('plan.json')),new_raw_copies=0,new_archives=0,old_raw_deleted=0),ensure_ascii=False,indent=2)+'\n');private_manifest.chmod(0o600)
 public_witness={k:v for k,v in witness.items() if k not in ('witnesses','root_current_s_private')};public_witness['first_violation']={k:v for k,v in witnesses[0].items() if k not in ('node_remaining_index','exact_residual')}
 pbody=fact['factual']['records'];fstats=dict(holds=149,raw_ticks=594,episode_upper_s=(88+594)/50,all_registered_fields_passed=True,max_recomputed_nominal_difference=fact['factual']['max_recomputed_nominal_difference'],memory_exact_rows=fact['factual']['memory_exact_rows'],memory_scope=fact['factual']['scope'],max_post_position_error_m=max(x['physical']['body']['errors']['position_m'] for x in pbody),max_abs_progress_difference_m=max(abs(x['progress_difference_m']) for x in pbody))
 result=dict(stage=501,status=final['status'],factual=fstats,candidate=dict(holds=35,raw_ticks=140,all_integrated_holds_safe=True,official_finish=False,stop='EXACT_EMPTY_SET',cold_second_executed=False,held_first_executed=False,episode_finish_upper_s=None,witness=public_witness),execution={k:v for k,v in final.items() if k not in ('branches','outcome','storage')},static=dict(passed=static['passed'],capture_lifecycle_test_count=static['lifecycle']['test_count'],io_pure_tests=10,source_native_receipts=298,original397_417=static['graph']['original397_417'],own_saved_fixture=static['own_fixture']['passed'],writer_aliases=static['alias']['patched_aliases']),retention=dict(raw_files=len(ps),raw_bytes=totalbytes,categories=category,content_reference_links_authenticated=refs,workspace_files_before_manifest=len(newworkspace),workspace_bytes_before_manifest=sum(p.stat().st_size for p in newworkspace),combined_files_before_manifest=combined_files,combined_bytes_before_manifest=combined_bytes,private_manifest_sha256=sha(private_manifest),remaining_closing_bytes_reserved=1024**2,remaining_closing_files_reserved=8,physical_caps_passed=True,raw_copy_delete=0),model_screen_pass=False,actual_record_updated=False,target11_99_claimed=False,cold_repeat_or_held_claimed=False,no_retry=True,no_followup=True,research_remaining=26027,reserve=84000,reserve_used=0)
 result['closing_CPU_s']=time.process_time()-CPU;result['closing_wall_s']=time.perf_counter()-START
 result['charged_total_CPU_s_with_final_publication_allowance']=final['CPU_s']+result['closing_CPU_s']+10
 result['charged_total_wall_s_with_final_publication_allowance']=final['wall_s']+result['closing_wall_s']+20
 guard();(G/'retry/screen501_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(status=result['status'],witness=public_witness,raw_files=len(ps),raw_bytes=totalbytes,factual=fstats,charged_total_CPU_s=result['charged_total_CPU_s_with_final_publication_allowance'],charged_total_wall_s=result['charged_total_wall_s_with_final_publication_allowance']),ensure_ascii=False))
if __name__=='__main__':run()
