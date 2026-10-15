"""Apply existing O0 evidence by source/state algebra, with zero policy calls."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile
import numpy as np
from retry.path271_run import read,save,sha
from retry.package349_run import cached,projection
from retry.support342_logic import advance_evidence

G=Path(__file__).resolve().parent.parent


def dump(tree):return ast.dump(tree,include_attributes=False)


def normalized_candidate(name,source):
    """Erase only349's explicitly enumerated metadata/filter additions."""
    tree=ast.parse(source)
    if name=='retry/temporal_agent.py':
        tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module=='retry.support342_logic')]
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='TemporalRouteAgent')
        for fn in cls.body:
            if not isinstance(fn,ast.FunctionDef):continue
            body=[]
            for n in fn.body:
                if isinstance(n,ast.Assign):
                    targets=[ast.unparse(t) for t in n.targets]
                    if any(t.startswith('self.support349_') or t in ['before349','previous_yaw349','tracker349','direct349'] for t in targets):continue
                if isinstance(n,ast.AugAssign) and ast.unparse(n.target)=='self.support349_step':continue
                if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=='direct349':n.iter=ast.parse('road_and_obstacles(image)[1]',mode='eval').body
                body.append(n)
            fn.body=body
    elif name=='retry/nominal238_base.py':
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Agent');fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='act');body=[]
        for n in fn.body:
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='routing349' for t in n.targets):continue
            if isinstance(n,ast.Assert) and ast.unparse(n.test)=='len(obstacles) == len(self.support349_state)':continue
            for x in ast.walk(n):
                if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='connected_route':
                    assert isinstance(x.args[1],ast.Name) and x.args[1].id=='routing349';x.args[1]=ast.Name(id='obstacles',ctx=ast.Load())
            body.append(n)
        fn.body=body
    else:raise AssertionError(name)
    return tree


def run(R):
    D=R/'stage351';assert not D.exists();D.mkdir(mode=0o700)
    a=read(R/'stage342/plan.json');q=read(R/'stage349/plan.json');case=next(c for c in a['cases'] if c['key']=='O0');deadline=read(R/'research-deadline-current.json')['deadline_utc']
    assert time.time()<datetime.datetime.fromisoformat(deadline.replace('Z','+00:00')).timestamp()
    assert sha(R/'stage342/plan.json')==(R/'stage342/plan.sha256').read_text().strip() and sha(R/'stage349/plan.json')==(R/'stage349/plan.sha256').read_text().strip()
    for name in [case['pixels'],case['expected_tracker']]:assert sha(name)==a['source_hashes'][name]
    assert a['configs']['baseline']['archive_sha256']==a['configs']['candidate']['archive_sha256']==q['configs']['baseline']['archive_sha256']
    assert a['configs']['baseline']['constants']['confidence342-config.json']==dict(enabled=False) and a['configs']['candidate']['constants']['confidence342-config.json']==dict(enabled=True)
    assert {k:v for k,v in a['configs']['baseline'].items() if k!='constants'}=={k:v for k,v in a['configs']['candidate'].items() if k!='constants'}
    assert q['configs']['baseline']['assets']==q['configs']['candidate']['assets']==a['configs']['baseline']['assets']
    assert q['configs']['baseline']['constants']==q['configs']['candidate']['constants']=={k:v for k,v in a['configs']['baseline']['constants'].items() if k!='confidence342-config.json'}
    files=[G/'retry/deduplicate351.py',G/'retry/support342_logic.py',G/'retry/package349_stage.py',G/'retry/package349_run.py',R/'stage342/plan.json',R/'stage342/run-result.json',R/'stage349/plan.json',R/'stage349/final-report-verification.json',R/'stage350/summary-private.json',R/'stage350/commit-receipt.json',R/'stage306/collection/O0/result.json',R/'stage306/collection/O0/job.json',R/'stage334/O0/ON-private.jsonl',Path(case['pixels']),Path(a['configs']['baseline']['worker_path']),Path(q['configs']['candidate']['archive_path']),Path(q['configs']['baseline']['archive_path']),R/'stage349/baseline/reset-private.json',R/'stage349/candidate/reset-private.json',R/'project-effective-budget-v363.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip']
    for mode in ['baseline','candidate']:files += [R/f'stage342/O0/{mode}/{n}' for n in ['records-private.jsonl','reset-private.json','ready-private.json','receipt.json']]
    p=dict(stage=351,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,decision_before_audit='Duplicate fixed-input experiment; use existing342O0replay and independently check applicability without new actors.',scope='Exactly first190already savedO0inputs, same334ON/H1 models/nominal/controller/fallback context and fixed342rule. Source306pixels are off-policy for334; do not call this an actual334O0run.',budget=dict(actor_calls=0,actor_resets=0,native_actions=0,environment_resets=0,routing_calls=0,target_calls=0,metadata_algebra_updates=190,research_remaining=1746,final_reserve=84000),stop='Stop on any source/input/reset/algebra/saved-output mismatch. No fallback actor, policy modification, tuning, rollout, split opening or promotion in351.',proof='Match archive members; strip only enumerated metadata bookkeeping/filter additions and require original AST exactly; exact helper functions and selection mapping. Reconstruct190metadata states from stored tracker and pixels, verify existing same-input policy outputs/normal memory/reset. This is evidence transfer, not a new standaloneO0execution.',method='Parent reports full original document context and same-condition/single-change principles re-reviewed. Avoid redundant cache calls; retain uncertainty of off-policy evidence.',source_hashes={str(f):sha(f) for f in files})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'call-budget.json',dict(actor_calls=0,actor_cap=0,native_actions=0,native_cap=0))
    start,cpu=time.perf_counter(),time.process_time()
    with zipfile.ZipFile(q['configs']['baseline']['archive_path']) as z:base={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(q['configs']['candidate']['archive_path']) as z:candidate={n:z.read(n) for n in z.namelist()}
    assert {n:hashlib.sha256(v).hexdigest() for n,v in base.items()}==q['configs']['baseline']['members_sha256']==a['configs']['baseline']['members_sha256']
    assert {n:hashlib.sha256(v).hexdigest() for n,v in candidate.items()}==q['configs']['candidate']['members_sha256']
    changed={n for n in base if base[n]!=candidate[n]};assert changed=={'retry/temporal_agent.py','retry/nominal238_base.py'} and set(candidate)-set(base)=={'retry/support342_logic.py'}
    for name in changed:assert dump(normalized_candidate(name,candidate[name]))==dump(ast.parse(base[name])),name
    helper=ast.parse(candidate['retry/support342_logic.py']);worker=ast.parse(Path(a['configs']['candidate']['worker_path']).read_text())
    for name in ['birth_evidence','advance_evidence']:
        assert dump(next(n for n in helper.body if isinstance(n,ast.FunctionDef) and n.name==name))==dump(next(n for n in worker.body if isinstance(n,ast.FunctionDef) and n.name==name))
    assert candidate['retry/support342_logic.py']==(G/'retry/support342_logic.py').read_bytes()
    # Enumerate actual method chain; metadata update occurs once per policy call.
    nominal=ast.parse(candidate['retry/nominal238_base.py']);act=next(n for n in ast.walk(nominal) if isinstance(n,ast.FunctionDef) and n.name=='act')
    assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='tracked_obstacles' for n in ast.walk(act))==1
    A=cached(R/'stage342/O0/baseline/records-private.jsonl');B=cached(R/'stage342/O0/candidate/records-private.jsonl');assert len(A)==len(B)>=190
    obs=np.load(case['pixels'])['observations'][:190];assert obs.shape==(190,4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and obs.min()>=0 and obs.max()<=1
    assert np.array_equal(obs[1:,:3],obs[:-1,1:]) and all(np.array_equal(obs[0,0],x) for x in obs[0])
    expected=[json.loads(s) for s in Path(case['expected_tracker']).read_text().splitlines()];previous=[];held=[];births=[];differences={k:[] for k in ['action','features','pixel_path','target','nominal_memory','original_policy_state']}
    resetA=read(R/'stage342/O0/baseline/reset-private.json');resetB=read(R/'stage342/O0/candidate/reset-private.json');assert resetA['state']==resetB['state']
    assert resetA['state']==read(R/'stage349/baseline/reset-private.json')['state'];assert projection(resetA['state'])==projection(read(R/'stage349/candidate/reset-private.json')['state'])
    for i in range(190):
        x=A[i]['response'];y=B[i]['response'];cx=A[i]['commit'];cy=B[i]['commit'];assert x['tracker_record']==y['tracker_record']==expected[i]['tracker']
        state=advance_evidence(y['tracker_record'],previous,i+1,obs[i,-1]);previous=state['after'];assert state==x['support_record']==y['support_record']
        removed=[j for j,e in enumerate(previous) if e['low']];assert removed==y['routing_evidence']['removed_indices'];assert not x['routing_evidence']['removed_indices']
        assert y['routing_evidence']['routing_hazards']==[h[:3] for j,h in enumerate(y['tracker_record']['after']) if j not in removed]
        if removed:held.append(i+1)
        births += [dict(step=i+1,direct_index=b['uid'][1],area_pixels=b['component_area']) for b in state['births'] if b['low']]
        for key in ['action','features','pixel_path']:
            if x[key]!=y[key]:differences[key].append(i+1)
        if x['features'][1:3]!=y['features'][1:3]:differences['target'].append(i+1)
        if cx['memory']!=cy['memory']:differences['nominal_memory'].append(i+1)
        if cx['state']!=cy['state']:differences['original_policy_state'].append(i+1)
        for r,c,old in [(x,cx,A),(y,cy,B)]:
            assert not r['python_audit_denied_events'] and not c['python_audit_denied_events']
            assert c['history'][-1]==r['action'] and c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==np.float32(r['action'][0])
            assert r['features'][7]==(resetA['state']['previous_steer'] if i==0 else old[i-1]['commit']['memory'])
    assert not any(differences.values()) and held==list(range(181,190)) and not any(e['low'] for e in previous)
    for mode in ['baseline','candidate']:
        ready=read(R/f'stage342/O0/{mode}/ready-private.json');assert not ready['simulator_imported'] and not ready['python_audit_denied_events']
        for name,path in ready['policy_modules'].items():
            relative=path.split('/package/',1)[1];assert ready['policy_module_sha256'][name]==a['configs'][mode]['members_sha256'][relative]
        assert read(R/f'stage342/O0/{mode}/receipt.json')['technical_error'] is None
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    v=read(R/'project-effective-budget-v363.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1284297,1746,84000,0,1370043)
    cost=dict(stage=351,new_wrapper_actions=0,new_actor_calls=0,actor_resets=0,new_environment_resets=0,new_routing_calls=0,new_target_calls=0,metadata_algebra_updates=190,new_learning_fits=0,new_tuning=0,new_paid_resources=0,audit_wall_s=time.perf_counter()-start,audit_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1284297,research_remaining=1746,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1370043,measurement_scope='Offline source/records/metadata audit only; no new policy or simulator execution. Preparation/closure/git/task wall not fully timed.')
    proposal=dict(status='Proposed only; not executed, reserved or granted.',minimum_design='Keep existing actualN2effect337DNF versus350finish; no N2rerun. Add one independent actualO0paired baseline334ON/H1 versus frozen349candidate from matching fresh resets, existing permitted TRAINcase only. Twoactualarms are necessary because historicalO0actual used296and cannot substitute for334baseline.',
        bounded_plan=dict(per_arm_cap=400,total_new_native_cap=800,new_environment_resets=2,new_native_auxiliary=0,research_remaining_after_maximum=946,additional_research_needed=0,maximum_step_ticks=3200,expected_reset_ticks_total=102,maximum_total_raw_ticks=3302),
        cap_reason='Existing O0source296actualfinished304actions;400offers96moreactions perarm while staying within1746. This is only a cost reference from anotherpolicy, not evidence334/349mustfinish by400. Choose400beforeexecution, no cutoff sweep or automaticextension.',
        preconditions='Separately register both exact349archive/worker hashes, identicalenvironment/versions/case/init/RNG, orderAthenB and400each/800total caps. Current334actualtrajectory is unknown: do not force source306O0prefix or birth181. Match reset and the naturally common actualprefix until first returned-control difference, then each uses ownobservations/fullcontrols/normalmemory. No extra cache actors are needed after351evidence transfer.',
        outcomes='N2effect is retained as one knowncondition, not pooled lapscore. For O0report bothfinish/DNF/protocolcensor and officiallaps; only if bothfinish compare exact officialBminusAlap. Any positive lapdelta is observed regression; no chosen tolerance. Damage/contact/progress secondary. Onearm400censor yields inconclusive completion/regression, not a safety pass; stop rather than expand automatically.',
        stop='Officialfinish/retirement before400, source/input/reset/physics/accessRNG/commonprefix/interface/leak/technical mismatch or deadline. Chargeactualfailedactions; no automaticthirdarm/retry/tuning/split/promotion.',
        full_default_alternative=dict(per_arm_cap=2000,total_cap=4000,additional_research_needed=2254,reason='If both arms must be funded through default2000ratherthan accept400protocolcensor, current1746is insufficient. This alternative is not authorized or reserved.'),final_reserved_actions=84000)
    result=dict(stage=351,decision='Duplicate cached experiment; no new actor invocation. Existing342O0first190evidence applies to unchanged349semanticpipeline under the recorded inputs, by exact source/reset/state-algebra correspondence.',new_actor_calls=0,new_native_actions=0,verified_input_stacks=190,input_file_hash_preserved=True,baseline_archive_byte_identical_to342=True,candidate_semantic_changes='Only equivalent metadata bookkeeping and same fixed routing filter moved intoarchive. Normalized original tracker/nominal AST identical, helper functions exact, all other original members byteidentical.',reset_and_memory_qualification='Existing342baseline/candidate reset states exact and original state projections match349resets; own-returned-command commits, f7previousnominalmemory and full original A/Bstates checked through190.',differences=differences,low_births=births,withheld_actions=held,
        interpretation='Known181birth is retained181-189andexpires190. Withholding its footprint changes neither recorded routing/target/control nor normalmemory on these inputs. No new standaloneO0agent-pickle execution was performed; added349metadata changesfullpicklebyconstruction. NativeO0behavior under334/349remains unmeasured.',
        limits=['SourceO0pixels came from296actualtrajectory; this is off-policy fixed-input evidence for334ON/H1, never a substitution for actualO0baseline or generalization/occlusion safety.',
        'Same inputs, source logic and reset/memory context make another190+190actor replay redundant. Source/state algebra and previous349/350package qualifications support applicability; no new O0runtime/latency/fullpickle parity measurement.',
        'No threshold/fit/tuning/rollout/protectedsplit/promotion. N2singleknowncondition outcome doesnot establish otherTRAINconditions are unaffected.'],next_minimum_closed_loop_comparison=proposal,cost=cost,champion296_preserved=True,promotion=False,new_protected_split_opened=False,deadline_utc=deadline)
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937'
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    save(D/'cost.json',cost);save(D/'summary-private.json',result);save(D/'next-comparison-proposal.json',proposal);save(G/'retry/deduplicate351_result.json',result);save(D/'final-report-verification.json',dict(passed=True,source_normalization_exact=True,helper_exact=True,saved_inputs_reset_memory_route_target_control_190=True,extra_actors_avoided=380,actor_calls=0,native_actions=0,research_remaining=1746,final_reserve=84000,next_comparison_not_executed=True))
    v.update(version=364,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v363.json'),prior_budget_sha256=sha(R/'project-effective-budget-v363.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage351_new_wrapper_actions=0);assert not (R/'project-effective-budget-v364.json').exists();save(R/'project-effective-budget-v364.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==351 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(decision='duplicate; actor0native0',differences=differences,held_actions=held,cost=cost,next_bounded_pair_cap=800,next_default_pair_shortfall=2254)),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
