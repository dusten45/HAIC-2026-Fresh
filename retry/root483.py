"""Authenticate saved481 own-prefix121 once; export no physics authority."""
import copy,json,hashlib
from pathlib import Path
from retry.io481 import read
from retry.history481 import validate_history
from retry.pilot420_backend import fingerprint
from retry.online483 import max_guard_error,rank
from retry.mechanism479 import physical_identity
from retry.ledger439 import require
from retry.loss389_analyze import sha

def authenticate(root):
    d=root/'stage481';manifest_path=root/'stage481-retention-manifest-private.json';manifest=read(manifest_path)
    # Complete physical byte authentication once, then decoded receipt hashes
    # authenticate all consumed state references during full-chain validation.
    for record in manifest['files']:
        p=Path(record['path']);require(p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],'483_SAVED481_BYTE_AUTH:'+p.name)
    require({p.name for p in d.iterdir() if p.is_file()}=={Path(r['path']).name for r in manifest['files']},'483_SAVED481_FILESET')
    ctxpath=d/'context-198-private.json';ctx=read(ctxpath)
    require(ctx['label']=='online' and ctx['index']==121 and ctx['before']['C']['phase']=='FIRST_LAP','483_ROOT_PRE122')
    require(ctx['state']['finish_tracker']['candidate_crossing_time_s'] is None and ctx['state']['finish_tracker']['finish_time_s'] is None,'483_ROOT_NO_PENDING')
    obs=read(d/'online-observer-private.json');constructor_root=read(d/'world10-before-constructor-private.json')['state'];actions=obs['actions'][:121];posts=obs['posts'][:484]
    contexts={}
    for p in d.glob('context-*-private.json'):
        c=read(p)
        if c['label']=='online' and c['index']<121:contexts[c['index']]=c
    require(set(contexts)==set(range(121)),'483_ROOT_PREFIX_CONTEXTS')
    # The observer root is its actual cold-restored boundary. The constructor
    # input has a different structural contact count, already explicitly outside
    # the frozen cold-restore identity; no physical/tracker/clock field is dropped.
    originalroot=contexts[0]['state']
    require(fingerprint(originalroot)==obs['link']['root_state_digest'] and physical_identity(originalroot)==physical_identity(constructor_root),'483_ORIGINAL_OBSERVER_ROOT_BINDING')
    auths=[]
    for i in range(121):
        n=contexts[i]['allocation_number'];p=d/f'decision-{n:03d}-private.json';dec=read(p)
        auths.append({**dec['authorization'],'decision_path':str(p),'decision_sha256':sha(p)})
    oldplan=read(root/'stage481-plan-durable-private.json');material=read(oldplan['input_material_path']);fixed=material['fixed']
    proof=validate_history(originalroot,obs['link']['model_ledger'],posts,actions,auths,ctx['state'],ctx['before'],ctx['ledger'],fixed['line'],auths[0]['policy_digest'])
    require(proof['actions']==121 and proof['physical_safe'] and not proof['own_model_finished'] and not proof['pending'] and not proof['progress_deadline_missed'],'483_ROOT_PREFIX121_AUTH')
    q=read(d/'result.json')['outcome']['online_queries'][121];expected={}
    for key,opt in q['options'].items():
        trace=read(opt['first_path']);op=Path(opt['first_path']);observed=read(op.with_name(op.name.replace('-private.json','-observer-private.json')))
        require(sha(op)==opt['first_sha256'] and len(trace['rows'])==1,'483_FIRST_SAVED_SOURCE')
        row=trace['rows'][0];expected[key]={**opt,'row':row,'posts':observed['posts'],'max_guard_path_error_m':max_guard_error(row,fixed['line'])}
    eligible=[k for k,v in expected.items() if v['valid']];selected={arm:min(eligible,key=lambda k:rank(expected[k],arm)) for arm in ('control','variant')}
    require(expected[selected['control']]['aliases']==q['selected_aliases'],'483_SAVED_CONTROL_RERANK')
    rootproof=dict(stage=483,passed=True,actions=121,source481_policy_digest=auths[0]['policy_digest'],root_context_path=str(ctxpath),root_context_sha256=sha(ctxpath),state_digest=fingerprint(ctx['state']),before_memory_digest=fingerprint(ctx['before']),ledger_digest=fingerprint(ctx['ledger']),source481_manifest_path=str(manifest_path),source481_manifest_sha256=sha(manifest_path),prefix_proof=proof,source_files_checked=len(manifest['files']),source_raw_bytes=sum(r['bytes'] for r in manifest['files']),new_physics=0,new_worlds=0)
    first=dict(options=expected,selected=selected,nominal=ctx['nominal'],qstar=ctx['qstar'],after=ctx['after'])
    return rootproof,dict(context=ctx,fixed=fixed,pace=material['pace']['frozen268'] if isinstance(material['pace'],dict) else material['pace'],projected_nodes=material['projected_nodes']['projected_nodes'] if isinstance(material['projected_nodes'],dict) else material['projected_nodes'],first_expected=first)
