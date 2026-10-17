"""Metadata-only identity exclusion audit; never draws or constructs anything.

Old383 identity rows are retained, even when a source later changes. All known
registration/exclusion declarations are unioned with later plan identities.
Coverage is recorded-identity coverage, never unknown historical geometry.
"""
import collections
import datetime
import hashlib
import json
import os
import re
from pathlib import Path

EXCLUSION_KEYS=('excluded_seeds','excluded_road_geometry_sha256',
 'excluded_obstacle_spec_sha256','excluded_physical_obstacles_sha256',
 'excluded_obstacle_rng_entropy','excluded_parent_entropy_vectors')
HASH_KEYS={'road_geometry_sha256':'excluded_road_geometry_sha256',
 'obstacle_spec_sha256':'excluded_obstacle_spec_sha256',
 'expected_physical_obstacles_sha256':'excluded_physical_obstacles_sha256',
 'physical_obstacles_sha256':'excluded_physical_obstacles_sha256',
 'physical_float32_obstacle_sha256':'excluded_physical_obstacles_sha256'}
DENY=('result','trajectory','trace','observation','frame','scene','truth',
 'diagnostic','analysis','outcome','feature','geometry','groundtruth','gt-private',
 'episode-split','input-material','context-','before-constructor','before-first-step',
 'before-integration','observer','runtime-link','allocation','decision-','state-')
SKIP=('metrics','performance','losses','results','analysis','outcome','summary',
 'physical','position','trajectory','trace','features','frames','pixels',
 'observations','road_points','road_coordinates','cached_results','initial_observations')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def stage(p,root):
    for part in Path(p).relative_to(root).parts:
        m=re.match(r'^stage(\d+)(?:[-.]|$)',part)
        if m:return int(m[1])
    return 0
def metadata_name(name):
    n=name.lower()
    if not n.endswith('.json') or any(s in n for s in DENY):return False
    return (n in ('job.json','episode-header.json','contract.json','contract-v2.json',
     'config.json','configuration.json','cases.json','cases-frozen-private.json',
     'screen-seal.json','preregistration.json') or
     bool(re.search(r'(?:^|[-_])plan(?:[-_.]|$)',n)) or
     any(s in n for s in ('preregistered','split','identit','registration',
                         'selection-contract','fresh-dev','exclusion','-cases',
                         'case-private','manifest')))
def inventory(root):
    """Follow current raw symlinks for metadata NAMES, never open raw content."""
    seen=set();files=[]
    for folder,dirs,names in os.walk(root,followlinks=True):
        real=Path(folder).resolve()
        if real in seen:dirs[:]=[];continue
        seen.add(real)
        dirs[:]=[d for d in dirs if d not in {'cpu','package','sources','sources-final',
          '__pycache__','.git','.venv'} and not d.startswith('stage485')]
        files.extend(Path(folder)/n for n in names)
    return sorted(files)
def extract(value,path,sets,rows,refs,errors,loc='$'):
    if isinstance(value,dict):
        tracks=[value[k] for k in ('track_id','trackId') if type(value.get(k)) is int]
        for k,v in value.items():
            here=loc+'.'+k
            if k in EXCLUSION_KEYS:
                if type(v) is int and v>=0 and any(marker in loc for marker in ('_counts','new_identity_metadata_added','$.findings.')):continue
                if type(v) is not list:errors.append((str(path),here,'bad_exclusion_list'));continue
                for item in v:
                    try:sets[k].add(tuple(item) if isinstance(item,list) else item)
                    except TypeError:errors.append((str(path),here,'bad_exclusion_item'))
            elif k in ('seed','track_seed','road_seed','reset_seed') and type(v) is int:
                if not 0<=v<2**32:errors.append((str(path),here,'seed_range'))
                else:
                    sets['excluded_seeds'].add(v)
                    rows.append(dict(file=str(path),stage=stage(path,ROOT),seed=v,
                      track_id=tracks[0] if tracks else None,json_path=here))
            elif k in ('seeds','initial_seed_draw') and isinstance(v,list):
                if not all(type(s) is int and 0<=s<2**32 for s in v):errors.append((str(path),here,'unsupported_seed_vector'))
                else:
                    for i,s in enumerate(v):
                        sets['excluded_seeds'].add(s)
                        rows.append(dict(file=str(path),stage=stage(path,ROOT),seed=s,track_id=None,json_path=here+'['+str(i)+']'))
            elif k in HASH_KEYS and isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v):sets[HASH_KEYS[k]].add(v)
            elif k in ('obstacle_rng_entropy','obstacle_rng_lineage') and isinstance(v,list):
                if all(type(s) is int for s in v):sets['excluded_obstacle_rng_entropy'].add(tuple(v))
                else:errors.append((str(path),here,'unsupported_obstacle_entropy'))
            elif k in ('family_entropy','parent_entropy_vector','parent_entropy_identity') and isinstance(v,list):
                if all(type(s) is int and 0<=s<2**32 for s in v):sets['excluded_parent_entropy_vectors'].add(tuple(v))
                else:errors.append((str(path),here,'unsupported_parent_entropy'))
            elif k=='initial_osurandom_bytes_hex' and isinstance(v,str):
                try:
                    b=bytes.fromhex(v)
                    if not b or len(b)%4:raise ValueError('word_alignment')
                    sets['excluded_parent_entropy_vectors'].add(tuple(int.from_bytes(b[i:i+4],'little') for i in range(0,len(b),4)))
                except ValueError:errors.append((str(path),here,'unsupported_draw_hex'))
            elif not any(s in k.lower() for s in SKIP):extract(v,path,sets,rows,refs,errors,here)
            if isinstance(k,str) and k.startswith('/') and k.endswith('.json'):refs.add(str(Path(k)))
            if isinstance(v,str) and v.startswith('/') and v.endswith('.json'):refs.add(str(Path(v)))
    elif isinstance(value,list):
        for i,v in enumerate(value):
            if isinstance(v,(dict,list)):extract(v,path,sets,rows,refs,errors,loc+'['+str(i)+']')

def write_once(path,value):
    with Path(path).open('x') as f:
        os.chmod(path,0o600);json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def audit(root,output_dir):
    global ROOT
    ROOT=Path(root).absolute();root=ROOT;output_dir=Path(output_dir)
    if output_dir.exists():raise FileExistsError(str(output_dir))
    base=root/'stage383/seed-followup/pass3'
    anchors=[root/'stage484-split-audit-private.json',base/'inspection-summary.json',
       base/'identity-rows-private.json',base/'source-hashes-private.json',
       root/'stage297/exclusion-final.json',root/'preregistered-v1.json',
       root/'protected-query-ledger-v1.json',root/'split-reclassifications.jsonl']
    sources={str(p):sha(p) for p in anchors};summary=load(base/'inspection-summary.json')
    if summary['uncovered_exposure_stages'] or summary['metadata_parse_errors'] or summary['unsupported_seed_containers']:raise ValueError('383_source_coverage_not_closed')
    rows=load(base/'identity-rows-private.json');old_sources=load(base/'source-hashes-private.json')
    sets={k:set() for k in EXCLUSION_KEYS};errors=[];refs={};direct=collections.defaultdict(set);changed=[];missing=[]
    for row in rows:
        sets['excluded_seeds'].add(row['seed']);direct[row['file']].add(row['seed'])
    for path,expected in old_sources.items():
        p=Path(path)
        if not p.is_file():missing.append(path);continue
        actual=sha(p);sources[path]=actual
        if actual!=expected:changed.append(dict(path=path,before_sha256=expected,current_sha256=actual))
    files=inventory(root);metadata=[];indicators=collections.defaultdict(collections.Counter)
    for p in files:
        st=stage(p,root)
        if not 0<=st<=484:continue
        if st>=384 and (p.name in {'frames-actions-private.npz','trace-private.jsonl','trajectory-private.json','execution-claim.json','episode-opening.json'} or p.name.endswith('-observer-private.json') or p.name.endswith('-before-constructor-private.json')):indicators[st][p.name if len(p.name)<40 else 'typed_raw_presence']+=1
        # Through383 the frozen row inventory supplies seed exposure coverage.
        # Read only pure split/exclusion declarations for their recorded hashes.
        old_pure=(p.name=='split.json' or p.name.startswith('split-v') or 'exclusion' in p.name.lower())
        if metadata_name(p.name) and (st>=384 or old_pure or p in anchors):metadata.append(p)
    metadata.extend(p for p in anchors if p.suffix=='.json' and p.name in {'preregistered-v1.json','protected-query-ledger-v1.json'})
    metadata=sorted(set(metadata))
    for p in metadata:
        try:
            data=load(p);sources[str(p)]=sha(p);rr=[];ref=set();extract(data,p,sets,rr,ref,errors)
            rows.extend(rr);direct[str(p)].update(row['seed'] for row in rr);refs[str(p)]=ref
        except (ValueError,TypeError,KeyError,UnicodeDecodeError) as exc:errors.append((str(p),'$',type(exc).__name__))
    # Protect every original SEALED identity without looking at generated data.
    original=load(root/'preregistered-v1.json');sealed=original['split']['SEALED']
    for c in sealed:sets['excluded_seeds'].add(c['seed'])
    # Old parent words remain reserved even if the accepted child was replaced.
    for vector in sets['excluded_parent_entropy_vectors']:sets['excluded_seeds'].update(vector)
    inherited={path:set(values) for path,values in direct.items()}
    changed_graph=True
    while changed_graph:
        changed_graph=False
        for path,targets in refs.items():
            before=len(inherited.setdefault(path,set()))
            for target in targets:inherited[path].update(inherited.get(target,set()))
            changed_graph|=len(inherited[path])!=before
    stage_seeds=collections.defaultdict(set)
    for path,values in inherited.items():
        try:stage_seeds[stage(path,root)].update(values)
        except ValueError:pass
    gaps=[dict(stage=st,indicators=dict(ind),reason='Later exposure files lack direct or metadata-reference seed coverage') for st,ind in sorted(indicators.items()) if not stage_seeds[st]]
    # Fail closed on changed historical metadata unless the currently allowed
    # schema was re-inspected; old seeds remain excluded regardless.
    unresolved_changes=[v for v in changed if Path(v['path']) not in metadata]
    blockers=[]
    if missing:blockers.append('historical_source_files_missing')
    if errors:blockers.append('metadata_parse_or_identity_schema_errors')
    if gaps:blockers.append('post383_exposure_identity_coverage_gaps')
    if unresolved_changes:blockers.append('changed_historical_metadata_not_reinspected')
    if not all(c['seed'] in sets['excluded_seeds'] for c in sealed):blockers.append('SEALED_identity_exclusion_missing')
    snapshot={k:sorted([list(v) if isinstance(v,tuple) else v for v in sets[k]]) for k in EXCLUSION_KEYS}
    snapshot['physical_hash_coverage_limit']='All recorded/current seed and entropy identities are excluded. Historical unrecorded physical/spec/RNG/road hashes are not reconstructed; these hash exclusions cover metadata-available identities only. No protected geometry/raw/performance is opened.'
    output_dir.mkdir(mode=0o700)
    write_once(output_dir/'sources-private.json',sources)
    write_once(output_dir/'exclusions-private.json',snapshot)
    write_once(output_dir/'identity-rows-private.json',rows)
    coverage=dict(post383_exposure_indicators={str(k):dict(v) for k,v in sorted(indicators.items())},post383_stage_seed_counts={str(k):len(v) for k,v in sorted(stage_seeds.items()) if k>=384},gaps=gaps,errors=errors,historical_missing=missing,historical_changed=changed,unresolved_historical_changes=unresolved_changes,metadata_paths=[str(p) for p in metadata])
    write_once(output_dir/'coverage-private.json',coverage)
    result=dict(stage=485,status='RECORDED_IDENTITY_COMPLETENESS_PASS' if not blockers else 'BLOCKED_BEFORE_SELECTION',passed=not blockers,blockers=blockers,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_files=len(sources),metadata_files_read=len(metadata),identity_rows=len(rows),exclusion_counts={k:len(v) for k,v in sets.items()},post383_exposure_stages=len(indicators),old383_snapshot_alone_used=False,protected_SEALED_count=len(sealed),protected_raw_performance_opened=False,case_performance_used=False,new_draws=0,new_geometry=0,new_worlds=0,new_steps=0,new_resets=0,new_actual=0,ledger_changed=False,old_files_changed=False,source_ledger_caveat='Scope is completeness of recorded identities and metadata-source coverage, not proof that unrecorded historical geometry differs.',artifacts={name:dict(path=str(output_dir/name),sha256=sha(output_dir/name)) for name in ('sources-private.json','exclusions-private.json','identity-rows-private.json','coverage-private.json')})
    write_once(output_dir/'audit-private.json',result)
    return result

if __name__=='__main__':
    import sys
    result=audit(Path(sys.argv[1]),Path(sys.argv[2]));print(json.dumps(result));raise SystemExit(0 if result['passed'] else 2)
