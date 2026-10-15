"""Freeze saved-data diagnosis and eight pre-state-clone control calls."""
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent
PROBE="""    if op=='restore_probe':
        assert pending
        obs=payload.reshape(4,84,84).copy();before_state=state()
        saved_route=copy.deepcopy(observed_route);saved_features=copy.deepcopy(observed_features);saved_evidence=copy.deepcopy(routing_evidence)
        import retry.connected_agent as routing
        saved_evaluation=copy.deepcopy(routing.LAST_CONNECTION_EVALUATION)
        hazards=copy.deepcopy(agent.hazards);support=copy.deepcopy(agent.support349_state)
        variants={}
        try:
            for mode in ['original','restored']:
                diagnostic_restore=mode=='restored'
                clone=copy.deepcopy(diagnostic_before_agent);clone.__dict__.pop('correct_pedals',None)
                clone.hazards=copy.deepcopy(hazards);clone.support349_state=copy.deepcopy(support)
                clone.tracked_obstacles=lambda image,speed:[p[:3] for p in hazards]
                calculated=np.asarray(clone.act(obs),np.float32);f=list(clone.selector_features)
                variants[mode]=dict(action=calculated.tolist(),features=f,nominal_memory=float(clone.controller.previous_steer),path=copy.deepcopy(observed_route['path']),target=None if f[0] else f[1:3],nominal=f[13:16],delta_audit=copy.deepcopy(clone.delta_audit),routing_evidence=copy.deepcopy(routing_evidence))
            original=variants['original'];assert original['action']==last_base.tolist() and original['features']==saved_features['features'] and original['path']==saved_route['path'] and original['nominal_memory']==float(agent.controller.previous_steer) and original['delta_audit']==agent.delta_audit
        finally:
            diagnostic_restore=False;routing.LAST_CONNECTION_EVALUATION=saved_evaluation
            observed_route.clear();observed_route.update(saved_route);observed_features.clear();observed_features.update(saved_features);routing_evidence=saved_evidence
        assert state()==before_state
        response=dict(variants=variants,state_preserved=True,state=state(),clone_act_calls=2,routing_entries=2,target_entries=2,not_a_trajectory=True)
    elif op=='commit':
"""

def verify(R,full=False):
    D=R/'stage364';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p

def build(R):
    D=R/'stage364';assert not D.exists();D.mkdir(mode=0o700);q=read(R/'stage363/plan.json');cfg=q['config'];assert sha(cfg['archive_path'])==cfg['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad';source=Path(cfg['worker_path']).read_text()
    source=source.replace('last_base=None\ndef state():','last_base=None\ndiagnostic_before_agent=None\ndiagnostic_restore=False\ndef state():')
    source=source.replace("    selected=[list(p) for p in obstacles_override]","    if diagnostic_restore:obstacles_override=[h[:3] for h in full]\n    selected=[list(p) for p in obstacles_override]")
    source=source.replace("    if op=='commit':\n",PROBE)
    source=source.replace('base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True','diagnostic_before_agent=copy.deepcopy(agent)\n                base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True')
    assert source.count("if op=='restore_probe'")==1 and 'diagnostic_before_agent=copy.deepcopy(agent)' in source;compile(source,'worker364','exec');worker=D/'diagnostic-worker-private.py';worker.write_text(source);worker.chmod(0o600);diag=dict(cfg,worker_path=str(worker),worker_sha256=sha(worker))
    files=[G/f'retry/{n}.py' for n in ['diagnosis364_stage','diagnosis364_run','diagnosis364_audit','diagnosis364_close','frozen_composite_runtime','lineage339_audit','support342_logic','confidence341_run','package349_run','probe338_stage']]+[R/'stage363/plan.json',R/'stage363/summary-private.json',R/'stage363/T29510/support-gate.json',R/'stage359/plan.json',R/'stage359/summary-private.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'project-effective-budget-v379.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),worker,Path(q['sandbox_path'])]
    for prefix in ['stage363/T29510/B','stage359/B']:files += [R/prefix/n for n in ['trace-private.jsonl','frames-actions-private.npz','result.json']]
    v=read(R/'project-effective-budget-v379.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1291215,22190,84000,0)
    p=dict(stage=364,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=diag,original_config=cfg,sandbox_path=q['sandbox_path'],target_steps=[60,61,62,63],reproduction_inputs=63,
        scope='SavedT29510birth59/excluded60-63andknownN2birth121/excluded127-129. No newnative/simulation/learning/candidatechange. Inspectfixedbirthmorphology/boundaries/ringgray/neighbor,evidenceanddedup/transport. No thresholdorparametersearch.',
        calls='Onefrozen357prefixreplay63act+63commit+onepixelreset. At60-63twofreshpre-actclonesperinputwithsamepostperceptionfulltracker/support,speed/priorsteer/controller/H1. Onlyroutingarguments restoredtofullhazards forcounterfactual; noGTandnofeedbacktocontinuation. Eightclonefullpipelinecalls/routingentries/targetentries. Originalcloneoutputmustreproduceactualfirst; accessedlivestateunchangedafterprobe.',
        gates='Anyarchive/source/input/tracker/support/action/path/features/audit/originalstateprojectionreproductionmismatchorclonepollutionstops. No automaticretry/expandedframe/extraarm/thresholdtuning. Fullagentpickledigestcodeidentityexcludedfromcrossworkerprojection,accessibleRNGchecked. Noenvimports.',
        hypothesis_space='Existingroadneighborbinaryfeature,detectorarea/shape/boundary,evidenceofadditionaldirectobservationsandexisting2mdedupassociation/temporalcontinuity. AlreadyobservedT58to59associationandN121noassociation;onlyhypothesis, no policyexceptionsbyID/frame/UID orGTfeatures.',
        budget=dict(new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,candidate_modifications=0,actor_act_cap=63,actor_commit_cap=63,pixel_reset_cap=1,probe_cap=4,clone_act_cap=8,routing_entry_cap=8,target_entry_cap=8,research_remaining=22190,final_reserve=84000),source_hashes={str(f):sha(f) for f in files})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'call-budget.json',dict(actor_act_calls=0,actor_commit_calls=0,pixel_resets=0,probes=0,clone_act_calls=0,routing_entries=0,target_entries=0));print('364 registered saved-dataonly:63prefix+8same-inputclonecalls; native0; budgetsunchanged.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
