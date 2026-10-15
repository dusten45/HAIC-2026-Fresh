"""Verify actual wrapper horizon; one reset/run, budget only after live counter."""
import argparse
import datetime
import inspect
import json
import math
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha


def contract_test():
    import gymnasium as gym
    from gymnasium.wrappers import TimeLimit
    from env_wrapper import CarEnvironment
    from core.finish_line import FinishLineTracker
    class CounterEnv(gym.Env):
        def __init__(self):
            self.car=type('CounterCar',(),{'set_damage_effects':lambda self,*args:None})();self.t=0.;self.tile_visited_count=0;self.track=[None]*10;self.finish_time_s=None;self.observation_space=gym.spaces.Box(0,255,(96,96,3),np.uint8);self.action_space=gym.spaces.Box(-1,1,(3,),np.float32)
        def reset(self,**kwargs):self.t=0.;return self.step(None)[0],{}
        def step(self,action):self.t+=.02;return np.zeros((96,96,3),np.uint8),0.,False,False,{}
    start,cpu=time.perf_counter(),time.process_time();env=CarEnvironment(TimeLimit(CounterEnv(),8200));env.reset();initial=env.env._elapsed_steps;initial_ticks=round(env.unwrapped.t*50);limit=math.ceil((env.env._max_episode_steps-initial)/env._skip_frames);counts=[]
    assert initial==50 and initial_ticks==51 and limit==2038
    for i in range(limit):
        before=env.env._elapsed_steps;_,_,ended,truncated,_=env.step(np.zeros(3));counts.append(env.env._elapsed_steps-before)
        assert not ended and truncated==(i==limit-1)
    assert counts[-1]==2 and all(n==4 for n in counts[:-1]) and env.env._elapsed_steps==8200;env.close()
    tracker=FinishLineTracker(center=(0.,0.),forward=(0.,1.),half_width=1.,half_depth=.5)
    assert not tracker.update((0.,-2.),(0.,1.),0.,1.)
    assert not tracker.update((0.,-.4),(0.,1.),.96,2.)
    assert not tracker.update((0.,.1),(0.,1.),.96,3.)
    assert tracker.update((0.,.6),(0.,1.),.96,4.) and tracker.finish_time_s==3. and tracker.qualified_time_s==2.
    return dict(passed=True,synthetic_only_noHAICphysics=True,synthetic_wrapper_calls=2038,reset_counter=initial,reset_raw_ticks=initial_ticks,raw_limit=8200,frame_skip=4,postreset_action_cap=limit,last_action_raw_ticks=2,finish_backdating_center3_confirm4=True,wrapper_truncated_can_mean_finish=True,default_CLI_max_actions=2000,scope='Current335make_env physical TimeLimit cap2038; separate CLI/registered2000 action loop not used as336earlycut. Completion beyond2000 would not certify defaultCLI horizon.',wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,time_limit_source=inspect.getsourcefile(TimeLimit))


def verify(R,full=False):
    D=R/'stage336';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    return p


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage336';assert not D.exists();D.mkdir(mode=0o700);contract=contract_test();save(D/'synthetic-contract-verification.json',contract)
    p335=read(R/'stage335/plan.json');assert sha(R/'stage335/plan.json')==(R/'stage335/plan.sha256').read_text().strip()
    for f,h in p335['source_hashes'].items():assert sha(f)==h,f
    result=read(R/'stage335/B/result.json');assert result['comparison_valid'] and result['native_actions']==72 and result['protocol_stop'] and not result['actual_terminal'];assert read(R/'stage335/independent-verification.json')['passed']
    assert read(R/'stage335/A-qualification.json')['passed'] and read(R/'stage335/cache-receipt.json')['passed'];cfg=p335['configs']['ON'];assert cfg==read(R/'stage334/configs-private.json')['ON']['ON'] and sha(cfg['archive_path'])==cfg['archive_sha256'] and sha(cfg['worker_path'])==cfg['worker_sha256']
    inputs=[R/'stage335/plan.json',R/'stage335/B/result.json',R/'stage335/B/trace-private.jsonl',R/'stage335/B/raw-pixels-actions-private.npz',R/'stage335/B/first-divergence-private.json',R/'stage335/cache/ON-reset-private.json',R/'stage335/A-qualification.json',R/'stage335/cache-receipt.json',R/'stage334/configs-private.json',R/'stage334/summary-private.json',R/'stage331/A/result.json',R/'stage331/A/raw-pixels-actions-private.npz',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'stage330/plan.json',R/'project-effective-budget-v344.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(contract['time_limit_source']),G/'retry/episode336_stage.py',G/'retry/episode336_run.py',G/'retry/diagnose.py',G/'retry/frozen_composite_runtime.py',G/'retry/pedal331_run.py',G/'retry/full_route_reproduction.py',G/'retry/source_vehicle_transition.py',G/'env_wrapper.py',G/'local_runner.py',G/'retry/evaluate.py',G/'damage.py',G/'README.md']+list((G/'core').rglob('*.py'))
    p=dict(stage=336,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=p335['case'],observer_rng_seed=p335['observer_rng_seed'],config=cfg,sandbox_path=p335['sandbox_path'],authorized_action_cap=2038,expected_horizon=contract,
        question='Does fixed334/335fallback-only candidate officially complete actualN2episode?',
        contract='One newB reset once. Verify actual TimeLimit maximum/elapsed and rawclock after this reset before registering budget or issuing policy actions. cap=ceil((rawmax-elapsed)/skip). Ifcap>2038,stop/report before actions; ifsmaller registerexactcap. No separate363cut. Distinguish currentresearchTimeLimit fromdefaultCLI2000.',
        replay='Actual full33572prefix required:73pixelstacks,72returned/executedcommands,fullactorstate/nominalmemory/features/tracker,accessiblephysics/RNG. Samearchive/worker. Stop unexpected difference, no repair/reseed. Then every returnedaction on own actualinputs, no saved continuation/teleport/newA.',
        termination='Finish flag first: core sets truncatedTrue on finish. Officiallap_ms=round((retroactivecenter-crossingfinish_time_s-postresetstarttime)*1000), not declarationclock oractioncount. Actual retirement differs from timeout/truncation and forcedcensoring. Stop terminal/truncated,verifiedcap,contractfailure orauthorizationdeadline.',
        evidence='Preserve334nearestworsening/subsetgain andunverifiedrealocclusion; GT evaluatoronly. No newfit/sourcephysicsrollout/threshold/horizonsearch. OneTRAIN feasibility only ifcomplete; no championpromotion.',
        method='Parent fulloriginal reread08:36:20-08:39:29UTC; suppliedproblem/evaluation/resource/causalcontract applied, originaltexts notcopied.',final_reserved_actions=84000,source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);print('336contractsyntheticverified2038; finishtruncationsuccess; actualcounterandbudgetpendingoneBreset',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage336';p=verify(R,True);assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()));z=np.load(R/'stage335/B/raw-pixels-actions-private.npz');old=[json.loads(s) for s in (R/'stage335/B/trace-private.jsonl').read_text().splitlines()];w=prepare(p['config'],D/'cache/cpu',p['sandbox_path']);start,cpu=time.perf_counter(),time.process_time();records=[];receipt={}
    try:
        reset,_=w.call('reset',z['observations'][0]);assert reset['state']==read(R/'stage335/cache/ON-reset-private.json')['state'];save(D/'cache/reset-private.json',reset)
        for i in range(72):
            r,_=w.call('act',z['observations'][i]);assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['tracker_record']==old[i]['tracker'] and r['pixel_path']==old[i]['pixel_path'] and r['delta_audit']==old[i]['audit']
            c,_=w.call('commit',z['actions'][i]);assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory'];records.append(dict(response=r,commit=c))
        receipt=dict(passed=True,cached_actor_calls=72,full335state_commands_features_memory_exact=True,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=c['actor_cumulative_CPU_s'],new_native_actions=0)
    finally:receipt['reaping']=w.close()
    save(D/'cache/records-private.json',records);save(D/'cache-receipt.json',receipt);print('336cached33572exact; no newA and no nativeactions',flush=True)


def register_actual(R,env):
    D=R/'stage336';p=verify(R);timer=env.env;skip=env._skip_frames;elapsed=timer._elapsed_steps;maximum=timer._max_episode_steps;remaining=maximum-elapsed;cap=math.ceil(remaining/skip)
    receipt=dict(wrapper=type(env).__name__,time_limit_class=type(timer).__name__,raw_class=type(env.unwrapped).__name__,elapsed_after_reset=elapsed,raw_limit=maximum,frame_skip=skip,warmup=env.warmup_steps,raw_reset_ticks=round(env.unwrapped.t*50),postreset_start_time=env.unwrapped.t,remaining_raw=remaining,postreset_action_cap=cap,last_action_raw_ticks=remaining-skip*(cap-1),max_authorized_cap=p['authorized_action_cap'])
    save(D/'actual-reset-contract.json',receipt)
    if cap>p['authorized_action_cap']:save(D/'pre-native-blocked.json',dict(reason='Actualrequiredcapexceedsauthorized2038',actual_cap=cap,native_actions=0));raise RuntimeError('Actualcapexceedsauthorized2038; no nativeactions issued')
    assert maximum==8200 and skip==4 and elapsed==50 and env.warmup_steps==50 and receipt['raw_reset_ticks']==51
    prior=R/'project-effective-budget-v344.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==1282199 and v['research_remaining']==0 and v['B_operating_cap']==1366199 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    grant=dict(stage=336,additional_research_actions=cap,reason='Explicitauthorizedonecompleteepisode; capverifiedfromsameactualBresetTimeLimitcounter, not296363actions.',native_cap=cap,actual_reset_contract_sha256=sha(D/'actual-reset-contract.json'),final_reserve_change=0)
    save(D/'budget-extension.json',grant);v.update(version=345,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=cap,B_operating_cap=v['B_operating_cap']+cap,research_remaining=cap,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'))
    assert not (R/'project-effective-budget-v345.json').exists();save(R/'project-effective-budget-v345.json',v);save(D/'native-budget.json',dict(cap=cap,actions=0));print(json.dumps(dict(actual_reset_elapsed=elapsed,remaining_raw=remaining,registered_cap=cap,B_operating_cap=v['B_operating_cap'],reserve=84000)),flush=True)
    return cap


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','cache']);p.add_argument('--private-root',required=True,type=Path);a=p.parse_args();globals()[a.command](a.private_root)
