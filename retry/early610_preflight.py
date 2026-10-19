"""Exercise actual610 state/control/ledger paths with evaluation dependencies stubbed."""
import ast
import inspect
import math
import textwrap
from collections import Counter
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import numpy as np
import retry.residual605 as old
import retry.early609_core as core


def validate_prefix_histories(s, rows, checkpoint):
    # Use the exact phase expression in the unchanged actual source raw method.
    tree=ast.parse(textwrap.dedent(inspect.getsource(old.old597.base.Study.raw)))
    expr=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='group' for t in n.targets))
    rule=compile(ast.Expression(expr),'<original-raw-phase>','eval')
    group=lambda index:eval(rule,{'__builtins__':{}},{'index':index})
    assert group(24)=='launch' and group(25)=='tracking'
    histories={k:list(s.initial_cp[k]) for k in ['launch','tracking']}
    phases=Counter()
    elapsed=s.initial_cp['elapsed']
    for n,row in enumerate(rows,1):
        assert row['global_raw_before']==n-1 and row['global_raw_after']==n
        assert row['index']==(n-1)//4+1 and row['raw']==(n-1)%4+1
        assert row['launch_history_before']==histories['launch']
        assert row['tracking_history_before']==histories['tracking']
        assert row['episode_before_s']==elapsed
        phase=group(row['index']); phases[phase]+=1
        forces=row['forces']
        assert len(forces)==4 and all(math.isfinite(f['ratio']) and bool(f['clipped'])==(f['ratio']>1.) for f in forces)
        proposed=[histories[phase][0]+sum(f['clipped'] for f in forces),histories[phase][1]+4]
        assert proposed==row['proposed_history']
        histories[phase]=proposed
        elapsed+=.02
        assert elapsed==row['episode_after_s']
        cp=dict(root=row['root_without_roads'],progress=row['progress'],tracker=row['tracker'],
            visited=row['visited'],launch=list(histories['launch']),tracking=list(histories['tracking']),
            elapsed=elapsed,global_raw=n)
        assert old.digest(cp)==row['checkpoint_sha256'], '610_PREFIX_FULL_CHECKPOINT_IDENTITY'
    assert all(histories[k]==checkpoint[k] for k in ['launch','tracking'])
    assert old.digest(cp)==old.digest(checkpoint) and len(rows)==96
    return dict(passed=True,raws=96,phase_counts=dict(phases),both_histories_exact_each_raw=True,
        final_launch_exact=True,final_tracking_exact=True,all_raw_checkpoint_hashes_exact=True,
        phase_source='Unchanged late568_model.Study.raw group expression index<=24',source_calls=0)


def run_preflight(s):
    # __main__ and imported module can differ under python -m; use the class's
    # actual defining globals so dependency patches affect the executing object.
    import sys
    module=sys.modules[s.__class__.__module__]
    tracking=module.base.old.tracking
    choose_tree=ast.parse(inspect.getsource(tracking.choose))
    first=choose_tree.body[0].body[0]
    assert isinstance(first,ast.Assign) and isinstance(first.value,ast.Call) and first.value.func.id=='nominal'
    real_counts=s.counts
    before_counts=s.counts.copy()
    initial_hash=old.digest(s.checkpoint(s.start))
    a=old.clone(s.start); b=old.clone(s.start)
    old.isolated(a,[b,s.start])
    a['tracking'][0]+=1; a['launch'][0]+=1; a['visited'].add(-999)
    a['tracker'].finish_time_s=123.; a['elapsed']+=1.; a['progress']+=1.
    assert old.digest(s.checkpoint(b))==initial_hash and old.digest(s.checkpoint(s.start))==initial_hash
    s.state=old.clone(s.start)
    state_hash=old.digest(s.checkpoint(s.state))
    s.arm='C'; s.hold=25; s.label='preflight'
    outdir=module.D/'preflight-private'; outdir.mkdir(mode=0o700,exist_ok=False)
    s.reserve('joint')
    # The same Counter and real durable Journal used in source execution.
    original_geometry=s.counts['geometry']
    s.counts['geometry']=module.CAPS['geometry']
    try:
        s.reserve('joint')
    except old.BudgetStop:
        budget_rejected=True
    else:
        raise AssertionError('610_ACTUAL_RESERVATION_DID_NOT_REJECT')
    finally:
        s.counts['geometry']=original_geometry
    nominal=np.asarray([.1,.54321,0.],np.float32)
    shifted=np.asarray([.11,.65432,0.],np.float32)
    scenario={'zero':False,'io':False,'none':False}
    calls=Counter()
    def forbidden(*a,**k):
        raise AssertionError('610_PREFLIGHT_REAL_KERNEL_OR_CHOOSER_CALLED')
    def nominal_dependency(root,path,progress):
        assert root is s.state['root'] and path is s.paths['candidate'] and progress==s.state['progress']
        calls['nominal_dependency']+=1
        return nominal.copy()
    def residual_dependency(root,path,progress,action,coeff,project,target):
        assert root is s.state['root'] and path is s.paths['candidate'] and coeff is s.coeff
        assert action.tobytes()==nominal.tobytes() and callable(project) and callable(target)
        return (nominal.copy(),dict(offset=0.,pedal_residual=0.)) if scenario['zero'] else (shifted.copy(),dict(offset=.1,pedal_residual=.01))
    projection_values=[]
    def project_dependency(*args):
        assert args[0] is s.state['root'].center and args[1] is s.paths['candidate']
        return dict(s=projection_values.pop(0),distance=0.,i=0)
    def factory(root,high,low,progress,counter,cost,geometry,max_ticks,history):
        assert root is s.state['root'] and high is s.paths['candidate'] and low is s.paths['backup']
        assert counter is s.model and cost is s.planner and geometry is s.geometry_context
        assert history==tuple(s.state['tracking']) and max_ticks==180000
        def evaluate(action):
            calls['certificate_dependency']+=1
            if scenario['io']: raise IOError('610_INJECTED_CERTIFIER_IO')
            if scenario['none']: return dict(ok=False,model_ticks=0)
            if not scenario['zero'] and action[0].tobytes()==nominal[0].tobytes():
                return dict(ok=False,model_ticks=0)
            u=float(action[1])-float(action[2])
            projection_values.extend(progress+(i+1)*(2+u)/48 for i in range(48))
            for i in range(48):
                s.project('tracking_forecast',root.center,high,progress)
            return dict(ok=True,model_ticks=48,first_hold=dict(progress_gain=s.score_trace[3]-progress))
        return evaluate
    with ExitStack() as stack:
        stack.enter_context(patch.object(module,'D',outdir))
        stack.enter_context(patch.object(tracking,'choose',forbidden))
        stack.enter_context(patch.object(tracking,'tick',forbidden))
        stack.enter_context(patch.object(tracking,'force_rows',forbidden))
        stack.enter_context(patch.object(tracking,'nominal',nominal_dependency))
        stack.enter_context(patch.object(tracking,'certifier',factory))
        stack.enter_context(patch.object(old.residual,'action',residual_dependency))
        stack.enter_context(patch.object(s,'original_project',project_dependency,create=True))
        frames=object()
        stack.enter_context(patch.object(module.previous.prev,'final_frames',lambda events,wheels:frames))
        direct=s.nominal_proposal()
        assert direct.tobytes()==nominal.tobytes()
        action,final,f=s.choose_joint()
        assert action[0].tobytes()==shifted[0].tobytes() and action[1]==1. and final['ok'] and f is frames
        nonzero_calls=calls['certificate_dependency']
        assert nonzero_calls==43 and old.digest(s.checkpoint(s.state))==state_hash
        scenario['zero']=True; s.hold=26
        action,final,f=s.choose_joint()
        assert action[0].tobytes()==nominal[0].tobytes() and action[1]==1. and f is frames
        zero_calls=calls['certificate_dependency']-nonzero_calls
        assert zero_calls==21
        # Selection and tie use the same function called by the actual batch.
        entries=[dict(index=3,report={'ok':True},end_progress=2.,first4_progress=1.),dict(index=2,report={'ok':True},end_progress=2.,first4_progress=2.),dict(index=1,report={'ok':True},end_progress=2.,first4_progress=2.)]
        assert core.select(entries)['index']==1 and core.select([]) is None
        scenario['zero']=False; scenario['none']=True; s.hold=27
        action,final,f=s.choose_joint()
        assert action is None and final is None and f is None
        assert calls['certificate_dependency']==nonzero_calls+zero_calls+42
        scenario['none']=False; scenario['io']=True; s.hold=28
        try: s.choose_joint()
        except IOError: pass
        else: raise AssertionError('610_ACTUAL_C_SWALLOWED_IO')
        invoked=[]
        def fail_arm(label):
            invoked.append(label)
            raise IOError('610_INJECTED_ARM_IO')
        with patch.object(s,'run_arm',fail_arm):
            try: s.compare()
            except IOError as exc:
                status,error=s.technical_stop(exc)
            else: raise AssertionError('610_ACTUAL_DISPATCH_SWALLOWED_IO')
        assert invoked==['A'] and status=='TECHNICAL_STOP_NO_RETRY' and not s.results
    assert s.counts is real_counts and budget_rejected
    assert all(s.counts[k]==0 for k in ['model_attempted','model_completed','external_force','internal_force','total_force'])
    assert s.model==[0] and s.context is None and not s.originals
    assert old.digest(s.checkpoint(s.state))==state_hash and old.digest(s.checkpoint(s.start))==initial_hash
    logical=s.counts['geometry']-before_counts['geometry']
    assert logical==2064 and not projection_values
    s.applied_journal.append('ACTUAL_OBJECT_PREFLIGHT_PASS',checks=10,stub_projection_queries_charged=logical,
        source_model=0,force=0,real_geometry_evaluator=0,chooser=0)
    s.arm=None; s.hold=None; s.label='preparation'
    return dict(passed=True,checks=['prefix96_original_phase_rule_both_histories_each_raw_full_hash',
        'actual_fullstate_clone_mutation_isolation','actual_Counter_and_durable_Journal_reservation',
        'actual_cap_rejection_and_counter_restoration','actual_nominal_proposal_dependency_data_flow',
        'actual_choose_joint_batch_certify_scored_project_no_base_safe_requirement',
        'actual_zero_region_same_time_grid_and_dedup','actual_selection_tie_and_no_fallback',
        'actual_C_IO_propagation','actual_comparison_whole_stop_and_technical_handler'],
        callbacks_noop=False,actual_object=True,physical_kernel=0,chooser=0,real_geometry_evaluator=0,
        logical_stub_projection_queries_charged=logical,nonzero_pair_and_FINAL_calls=nonzero_calls,
        zero_pair_and_FINAL_calls=zero_calls,no_safe_pair_calls=42,dependency_calls=dict(calls),
        private_preflight_directory=outdir.name,
        private_preflight_sha256={p.name:module.base.sha(p) for p in outdir.glob('*.json')})
