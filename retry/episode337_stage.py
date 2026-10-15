"""Authorized technical replacement; +1 grant, unchanged candidate and logger."""
import argparse
import ast
import datetime
import inspect
import json
import math
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha


def verify(R,full=False):
    D=R/'stage337';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    return p


def sanity(G):
    from damage import calculate_damage_effects
    from dataclasses import asdict
    from retry.episode336_run import json_default
    start,cpu=time.perf_counter(),time.process_time()
    for value in [0.,.2,1.]:
        effect=calculate_damage_effects(value);row={'info':{'damage_effects':effect},'np_scalar':np.int64(1),'array':np.array([0.,1.])};converted=json.loads(json.dumps(row,default=json_default,allow_nan=False));assert converted['info']['damage_effects']==asdict(effect)
    old=ast.parse((G/'retry/episode336_run.py').read_text());new=ast.parse((G/'retry/episode337_run.py').read_text())
    for node in ast.walk(new):
        if isinstance(node,ast.Constant) and node.value=='stage337':node.value='stage336'
        if isinstance(node,ast.ImportFrom) and node.module=='retry.episode337_stage':node.module='retry.episode336_stage'
    assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
    return dict(passed=True,DamageEffects_serializer_regression=True,numpy_nested_supported=True,run_AST_equal_corrected336_except_namespace=True,no_new_native_measurement_fields=True,no_policy_control_physics_time_change=True,new_native_actions=0,new_actor_calls=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu)


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage337';assert not D.exists();D.mkdir(mode=0o700);save(D/'serializer-sanity.json',sanity(G))
    p336=read(R/'stage336/plan.json');assert sha(R/'stage336/plan.json')==(R/'stage336/plan.sha256').read_text().strip();repair=read(R/'stage336/serializer-repair-verification.json');assert repair['passed'] and sha(G/'retry/episode336_run.py')==repair['fixed_public_source_sha256']
    for f,h in p336['source_hashes'].items():
        if sha(f)!=h:assert Path(f)==G/'retry/episode336_run.py' and sha(R/'stage336/executed-source/episode336_run.py')==h
    previous=read(R/'stage336/B/result.json');assert previous['native_actions']==1 and previous['censored'] and not previous['actual_DNF'];assert read(R/'stage336/actual-reset-contract.json')['postreset_action_cap']==2038
    inputs=[R/'stage336/plan.json',R/'stage336/B/result.json',R/'stage336/cost.json',R/'stage336/serializer-repair-verification.json',R/'stage336/actual-reset-contract.json',R/'stage336/synthetic-contract-verification.json',R/'stage336/executed-source/episode336_run.py',G/'retry/episode336_run.py',R/'stage335/plan.json',R/'stage335/B/result.json',R/'stage335/B/trace-private.jsonl',R/'stage335/B/raw-pixels-actions-private.npz',R/'stage335/B/first-divergence-private.json',R/'stage335/cache/ON-reset-private.json',R/'stage334/summary-private.json',R/'stage334/configs-private.json',R/'stage330/plan.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'project-effective-budget-v346.json',R/'research-deadline-current.json',Path(p336['config']['archive_path']),Path(p336['config']['worker_path']),G/'retry/episode337_stage.py',G/'retry/episode337_run.py',G/'retry/diagnose.py',G/'retry/frozen_composite_runtime.py',G/'retry/pedal331_run.py',G/'retry/full_route_reproduction.py',G/'retry/source_vehicle_transition.py',G/'damage.py',G/'env_wrapper.py',G/'local_runner.py']+list((G/'core').rglob('*.py'))
    p=dict(stage=337,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=p336['case'],observer_rng_seed=p336['observer_rng_seed'],config=p336['config'],sandbox_path=p336['sandbox_path'],authorized_action_cap=2038,
        question='Same fixed334/335fallback-only N2 episode completion; technical replacement, not a new policy.',
        authorization='Explicitparentreplacement: preserve336censor1native; +1research from2037to2038 beforeexecution, B1368238, reserve84000unchanged. One newB; technicalrecovery insidebudget autonomous, report exactshortfallifmore needed.',
        contract='Same corrected336runner except337namespace, no newfields orcontrol changes. Verify live elapsed50/rawmax8200/skip4 cap2038. Freshcached33572thenactual335prefix72 states/commands/pixels/physics/accessRNG; continue own observations allreturnedcontrols untilofficialterminal/actualcap/deadline, not363.',
        termination=p336['termination'],reference_scope='336technicalcensor notDNF; oldA/296qualifiedcomparators notnewruns. Hidden solver/OpenCVRNG andactualocclusionunverified preserved. Finishflagfirst andretroactivelap time.',
        method='Parent full24chapters/appliedplan reread11:22:52-11:23:24UTC; suppliedsanity/feasibility/generalization/resourceprinciples; originals notcopied.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);print('337replacementregistered; serializer/native0sanitypassed; policyandmeasurementsunchanged',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage337';p=verify(R,True);assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()));z=np.load(R/'stage335/B/raw-pixels-actions-private.npz');old=[json.loads(s) for s in (R/'stage335/B/trace-private.jsonl').read_text().splitlines()];w=prepare(p['config'],D/'cache/cpu',p['sandbox_path']);start,cpu=time.perf_counter(),time.process_time();records=[];receipt={}
    try:
        reset,_=w.call('reset',z['observations'][0]);assert reset['state']==read(R/'stage335/cache/ON-reset-private.json')['state'];save(D/'cache/reset-private.json',reset)
        for i in range(72):
            r,_=w.call('act',z['observations'][i]);assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['tracker_record']==old[i]['tracker'] and r['pixel_path']==old[i]['pixel_path'] and r['delta_audit']==old[i]['audit']
            c,_=w.call('commit',z['actions'][i]);assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory'];records.append(dict(response=r,commit=c))
        receipt=dict(passed=True,cached_actor_calls=72,full335state_commands_features_memory_exact=True,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=c['actor_cumulative_CPU_s'],new_native_actions=0)
    finally:receipt['reaping']=w.close()
    save(D/'cache/records-private.json',records);save(D/'cache-receipt.json',receipt)
    prior=R/'project-effective-budget-v346.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==1282200 and v['research_remaining']==2037 and v['B_operating_cap']==1368237 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    grant=dict(stage=337,additional_research_actions=1,reason='Explicitauthorizedtechnicalreplacementafter336censor; restore2038cap withoutrefunding336actual1.',native_cap=2038,final_reserve_change=0)
    save(D/'budget-extension.json',grant);v.update(version=347,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=1,B_operating_cap=1368238,research_remaining=2038,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'))
    assert not (R/'project-effective-budget-v347.json').exists();save(R/'project-effective-budget-v347.json',v);save(D/'native-budget.json',dict(cap=2038,actions=0));print('337cached72exact; +1registered; B1368238 remaining2038 reserve84000',flush=True)


def register_actual(R,env):
    D=R/'stage337';p=verify(R);timer=env.env;skip=env._skip_frames;elapsed=timer._elapsed_steps;maximum=timer._max_episode_steps;remaining=maximum-elapsed;cap=math.ceil(remaining/skip)
    receipt=dict(wrapper=type(env).__name__,time_limit_class=type(timer).__name__,raw_class=type(env.unwrapped).__name__,elapsed_after_reset=elapsed,raw_limit=maximum,frame_skip=skip,warmup=env.warmup_steps,raw_reset_ticks=round(env.unwrapped.t*50),postreset_start_time=env.unwrapped.t,remaining_raw=remaining,postreset_action_cap=cap,last_action_raw_ticks=remaining-skip*(cap-1),max_authorized_cap=p['authorized_action_cap'])
    save(D/'actual-reset-contract.json',receipt);assert cap==2038 and elapsed==50 and maximum==8200 and skip==4 and receipt['raw_reset_ticks']==51
    assert read(D/'native-budget.json')==dict(cap=2038,actions=0);print('337actualresetcounter50/8200; cap2038confirmed',flush=True);return cap


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','cache']);p.add_argument('--private-root',required=True,type=Path);a=p.parse_args();globals()[a.command](a.private_root)
