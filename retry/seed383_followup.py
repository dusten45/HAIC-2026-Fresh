"""Seed identity intersection audit only. No policy/world/render/terrain access.

Private outputs retain seed metadata. Public output contains counts only.
"""
import collections,datetime,hashlib,json,os,re,sys,time
from pathlib import Path
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp')
 with t.open('x') as f:
  os.chmod(t,0o600);json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 t.replace(p)

def metadata_name(name):
 n=name.lower()
 if any(s in n for s in ['result','trajectory','trace','observation','frame','scene','truth','diagnostic','analysis','outcome','feature','geometry','groundtruth','gt-private']):return False
 if any(s in n for s in ['exclusion','cost','budget','model','ready','response','policy','summary','recovery']):return False
 return n.endswith('.json') and (n=='episode-header.json' or bool(re.search(r'(?:^|[-_])plan(?:[-_.]|$)',n)) or n in {'contract.json','contract-v2.json','contract-a.json','evaluation-plan.json','cases-frozen-private.json','plan.json','job.json','cases.json','config.json','configuration.json','preregistration.json','training-selection.json','selection.json','screen-seal.json','DEV-cases.json'.lower()} or any(s in n for s in ['preregistered','split','-cases','case-private','identities','identity','manifest','registration','selection-contract','fresh-dev']))

SKIP=['excluded','exclusion','source_hash','sha256','params','metrics','analysis','outcome','summary','truth','physical','geometry','position','trajectory','trace','features','frames','pixels','observations','road_points','road_coordinates']

def extract(obj, path='$'):
 rows=[];seed_without_track=[];unsupported=[]
 def walk(x,loc):
  if isinstance(x,dict):
   seeds=[k for k in ['seed','track_seed','road_seed','reset_seed'] if k in x and isinstance(x[k],int) and not isinstance(x[k],bool)]
   tracks=[k for k in ['track_id','trackId'] if k in x and isinstance(x[k],int) and not isinstance(x[k],bool)]
   for k in seeds:
    rows.append(dict(seed=x[k],track_id=x[tracks[0]] if tracks else None,json_path=loc+'.'+k))
    if not tracks:seed_without_track.append(loc+'.'+k)
   if 'seeds' in x and isinstance(x['seeds'],list):
    vals=x['seeds'];ids=x.get('track_ids')
    if all(isinstance(s,int) and not isinstance(s,bool) for s in vals):
     for i,s in enumerate(vals):rows.append(dict(seed=s,track_id=ids[i] if isinstance(ids,list) and len(ids)==len(vals) else None,json_path=loc+'.seeds['+str(i)+']'))
    else:unsupported.append(loc+'.seeds')
   for k,val in x.items():
    if k=='SEALED':continue # Protected declarations, not experiment exposure.
    if any(s in k.lower() for s in SKIP):continue
    if k in seeds or k in tracks or k=='seeds':continue
    walk(val,loc+'.'+k)
  elif isinstance(x,list):
   for i,val in enumerate(x):
    if isinstance(val,(dict,list)):walk(val,loc+'['+str(i)+']')
 walk(obj,path)
 return rows,seed_without_track,unsupported

def stage_of(p,root):
 for part in p.relative_to(root).parts:
  m=re.fullmatch(r'stage(\d+)',part)
  if m:return int(m.group(1))
 return 0

def audit(root):
 outer=root/'stage383/seed-followup'
 d=outer/'pass3';assert not d.exists();d.mkdir(mode=0o700)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();wall,cpu=time.perf_counter(),time.process_time()
 original=root/'preregistered-v1.json';doc=read(original)
 sealed=doc['split']['SEALED'];assert len(sealed)==16 and all(set(x)=={'track_id','seed'} for x in sealed)
 sealed_seeds={x['seed'] for x in sealed};sealed_pairs={(x['track_id'],x['seed']) for x in sealed}
 assert len(sealed_seeds)==len(sealed_pairs)==16
 # Other original split identities are allowed exposure candidates.
 original_other=[dict(seed=x['seed'],track_id=x['track_id'],json_path='$.split.'+k) for k,v in doc['split'].items() if k!='SEALED' for x in v]
 candidates=[];denied_names=collections.Counter();filelist=[]
 for p in root.rglob('*.json'):
  if not p.is_file() or outer in p.parents:continue
  if any(part in {'cpu','package','sources','sources-final','__pycache__'} for part in p.relative_to(root).parts):continue
  if metadata_name(p.name):filelist.append(p)
  else:denied_names[p.name]+=1
 files={};rows=[];errors=[];unsupported=[];stagestats=collections.defaultdict(lambda:dict(metadata_files=0,identity_rows=0))
 for p in sorted(filelist):
  try:
   if p==original:rr=original_other;missing=[];bad=[]
   else:rr,missing,bad=extract(read(p))
  except (json.JSONDecodeError,UnicodeDecodeError,ValueError) as exc:
   errors.append(dict(path=str(p),error=type(exc).__name__));continue
  files[str(p)]=sha(p);stage=stage_of(p,root);stagestats[stage]['metadata_files']+=1;stagestats[stage]['identity_rows']+=len(rr)
  unsupported += [dict(file=str(p),path=x) for x in bad]
  for row in rr:rows.append(dict(file=str(p),stage=stage,**row))
 # Metadata-only exposure indicators: stat paths, never open result/trace content.
 exposure_stages=collections.defaultdict(collections.Counter)
 for p in root.rglob('*'):
  if not p.is_file() or outer in p.parents:continue
  name=p.name
  if name in {'frames-actions-private.npz','episode-header.json','trace-private.jsonl','trajectory-private.json','execution-claim.json','episode-opening.json'}:
   exposure_stages[stage_of(p,root)][name]+=1
 ledger_rows=[json.loads(s) for s in (root/'experiment-cost-lines.jsonl').read_text().splitlines()]
 positive=set()
 for x in ledger_rows:
  stage=x.get('stage')
  if isinstance(stage,int) and any(isinstance(x.get(k),(int,float)) and x[k]>0 for k in ['new_wrapper_actions','native_used','new_native_actions','native_actions']):positive.add(stage)
 for st in positive:exposure_stages[st]['positive_native_ledger']=1
 stage_seeds=collections.defaultdict(set)
 for row in rows:stage_seeds[row['stage']].add(row['seed'])
 conservative_seeds={x['seed'] for x in rows};conservative_pairs={(x['track_id'],x['seed']) for x in rows if x['track_id'] is not None}
 overlap=sealed_seeds&conservative_seeds;pair_overlap=sealed_pairs&conservative_pairs
 hits=[x for x in rows if x['seed'] in overlap]
 # Offline101 only re-reads explicitly named91/95/98 cached episodes.
 contract101=read(root/'stage101/contract-v2.json')
 inherited101=set()
 refs101=[]
 for run in contract101['runs'].values():
  for value in run['files'].values():
   q=Path(value)
   assert q.is_relative_to(root)
   st=stage_of(q,root)
   assert st in {91,95,98}
   inherited101.update(stage_seeds[st]);refs101.append(dict(path=value,source_stage=st))
 assert inherited101
 stage_seeds[101].update(inherited101)
 save(d/'offline101-seed-provenance-private.json',dict(source_contract_sha256=sha(root/'stage101/contract-v2.json'),reference_paths=refs101,inherited_seeds=sorted(inherited101),no_referenced_trace_or_observations_opened=True))
 gaps=[dict(stage=st,indicators=dict(ind),reason='Exposure/native metadata exists but no seed identity found in inspected manifests/jobs') for st,ind in sorted(exposure_stages.items()) if not stage_seeds[st]]
 # Reference hints stay private; never read performance/terrain to fill gaps.
 save(d/'source-hashes-private.json',files);save(d/'identity-rows-private.json',rows);save(d/'intersection-hits-private.json',hits)
 save(d/'coverage-private.json',dict(stage_metadata=dict(stagestats),exposure_indicators={str(k):dict(v) for k,v in exposure_stages.items()},missing_seed_stages=gaps,parse_errors=errors,unsupported_seed_containers=unsupported,excluded_filename_counts=dict(denied_names)))
 save(d/'protected-original-identity-private.json',dict(original_manifest_sha256=sha(original),SEALED_pairs=sealed,scope='Identity fields only; no conditions generated, geometry/observations/results read'))
 result=dict(audit_label='383-seed-followup',created_utc=now,metadata_files=len(files),identity_rows=len(rows),conservative_unique_seeds=len(conservative_seeds),conservative_unique_pairs=len(conservative_pairs),SEALED_unique_seeds=16,SEALED_unique_pairs=16,seed_intersection_count=len(overlap),pair_intersection_count=len(pair_overlap),intersection_hits=len(hits),covered_exposure_stages=len(set(exposure_stages)&{st for st,s in stage_seeds.items() if s}),uncovered_exposure_stages=[x['stage'] for x in gaps],metadata_parse_errors=len(errors),unsupported_seed_containers=len(unsupported),scope='All permitted metadata registrations conservatively treated as potentially exposed; no performance/observations/terrain read; exclusions and protected SEALED declaration not counted as experiments',audit_wall_s=time.perf_counter()-wall,audit_CPU_s=time.process_time()-cpu)
 save(d/'inspection-summary.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':audit(Path(sys.argv[1]).resolve())
