"""One known-DEV package smoke using the unchanged official local runner.

Run with the selected interpreter's -I flag. --contract supplies private known
DEV identity, deadline and cap; --directory retains private accounting. This
supervisor is excluded from the submission ZIP. No HOLDOUT is run.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import numpy as np


def smoke(package, repository, contract_path, directory):
    contract = json.loads(contract_path.read_text())
    assert contract['native_cap'] == 600
    assert hashlib.sha256((repository/'local_runner.py').read_bytes()).hexdigest() == contract['runner_sha256']
    assert not (directory/'smoke-opening.json').exists()
    def write(name, x):
        p=directory/name;p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
    write('smoke-opening.json',dict(stage=232,one_use=True,native_cap=600))
    write('smoke-budget.json',dict(actions=0))
    sys.path[:0] = [str(package.resolve()), str(repository.resolve())]
    import local_runner
    from env_wrapper import CarEnvironment
    from agent import Agent
    assert Path(sys.modules['agent'].__file__).resolve() == package.resolve()/'agent.py'
    assert all(Path(m.__file__).resolve().is_relative_to(package.resolve())
        for n,m in sys.modules.items() if (n=='retry' or n.startswith('retry.')) and getattr(m,'__file__',None))
    assert local_runner.DEFAULT_AGENT_TIMEOUT_SECONDS == 5.0
    clocks={};latencies=[];reset=[];init=[];actions=raw_ticks=reset_ticks=0;initial=None;endpoint=None;invalid=0
    deadline=dt.datetime.fromisoformat(contract['deadline_utc'])
    safe_act_code=local_runner.safe_act.__code__;safe_reset_code=local_runner.safe_reset.__code__
    step_code=CarEnvironment.step.__code__;reset_code=CarEnvironment.reset.__code__
    runner_code=local_runner.run_local_test.__code__;init_code=Agent.__init__.__code__
    selected={safe_act_code,safe_reset_code,step_code,reset_code,runner_code,init_code}
    def profile(frame,event,arg):
        nonlocal actions,raw_ticks,reset_ticks,initial,endpoint,invalid
        code=frame.f_code
        if code not in selected:return
        key=id(frame)
        if event=='call':
            if code in {safe_act_code,reset_code}:
                assert dt.datetime.now(dt.timezone.utc)<deadline
            if code==step_code:
                assert actions<600
                clocks[(key,'physics')]=frame.f_locals['self'].unwrapped.t
            clocks[key]=time.perf_counter()
        elif event=='return':
            elapsed=(time.perf_counter()-clocks.pop(key))*1000
            if code==safe_act_code:
                latencies.append(elapsed);invalid+=int(not arg[1])
            elif code==safe_reset_code:reset.append(elapsed)
            elif code==init_code:init.append(elapsed)
            elif code==step_code:
                actions+=1;env=frame.f_locals['self'];raw_ticks+=round((env.unwrapped.t-clocks.pop((key,'physics')))*50)
                write('smoke-budget.json',dict(actions=actions))
            elif code==reset_code:
                env=frame.f_locals['self'];reset_ticks=round(env.unwrapped.t*50)
                geometry=hashlib.sha256(np.asarray(env.unwrapped.track,dtype='<f8').tobytes()).hexdigest()
                obstacles=[[float(i.position[0]),float(i.position[1]),float(i.fixtures[0].shape.radius)] for i in env.unwrapped.obstacles]
                obstacle_sha=hashlib.sha256(np.asarray(obstacles,dtype='<f8').tobytes()).hexdigest()
                assert geometry==contract['case']['road_geometry_sha256']
                assert obstacle_sha==contract['case']['expected_physical_obstacles_sha256']
                initial=dict(geometry_matches=True,physical_obstacles_match=True)
            elif code==runner_code:
                v=frame.f_locals
                if 'completed' in v:
                    endpoint={k:v[k] for k in ['completed','lap_time_ms','steps','progress','finish_qualified','terminated','truncated','retire_reason']}
                    endpoint['damage']=float(v['info']['damage'])
    start=time.perf_counter();cpu=time.process_time();error=None
    sys.setprofile(profile)
    try:
        c=contract['case']
        local_runner.run_local_test(c['track_id'],c['seed'],max_steps=600,frame_skip=4,render_mode=None)
    except Exception as e:error=type(e).__name__+': '+str(e)
    finally:
        sys.setprofile(None)
        def timing(a):return dict(count=len(a),median=float(np.median(a)),p95=float(np.percentile(a,95)),max=float(max(a))) if a else None
        write('smoke-outcome.json',dict(stage=232,native_actions=actions,native_cap=600,raw_step_ticks=raw_ticks,raw_reset_ticks=reset_ticks,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,initial=initial,endpoint=endpoint,full_safe_act_ms=timing(latencies),full_safe_reset_ms=timing(reset),agent_init_ms=timing(init),invalid_actions=invalid,default_timeout_s=5.0,timeout_or_invalid_count=invalid,technical_error=error,peak_RSS_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,official_runner_sha256=contract['runner_sha256'],official_runner_source_changed=False,profiler='Read-only supervisor times unchanged safe_act/safe_reset including Thread start/join; counts wrapper env.step returns. Supervisor excluded from participant package.',HOLDOUT_rerun=False,SEALED_opened=False))
    if error:raise RuntimeError(error)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for n in ['package','repository','contract','directory']:a.add_argument('--'+n,type=Path,required=True)
    p=a.parse_args();smoke(p.package,p.repository,p.contract,p.directory)
