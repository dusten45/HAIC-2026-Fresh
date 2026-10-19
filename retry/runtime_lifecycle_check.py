"""Saved-input API/budget lifecycle checks. No environment or native rollout."""
import argparse,ast,copy,hashlib,importlib.util,json,os,pickle,select,subprocess,sys,time
from pathlib import Path
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('baseline_package');p.add_argument('saved_checkpoint');p.add_argument('output');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(args.output);out.mkdir(exist_ok=False);start=time.process_time();wall=time.perf_counter()
    package=Path(args.baseline_package);checkpoint=Path(args.saved_checkpoint)
    sys.path.insert(0,str(root/'submit_core'));import runtime598 as core
    from retry.runtime598_diagnostic import plain
    def module(name,path):
        spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
    baseline=module('lifecycle_baseline',package/'agent.py');candidate=module('agent',root/'submit_core/observation_agent.py')
    # Only the resource default and reset's counter-zero statement may differ.
    old=ast.parse((package/'agent.py').read_text());new=ast.parse((root/'submit_core/observation_agent.py').read_text())
    def normalize(tree,patched):
        for c in tree.body:
            if isinstance(c,ast.ClassDef) and c.name=='_TickCounter':
                for f in c.body:
                    if isinstance(f,ast.FunctionDef) and f.name=='__init__':
                        f.body[-1].value=ast.Constant(value='RESOURCE_DEFAULT')
            if isinstance(c,ast.ClassDef) and c.name=='Agent' and patched:
                f=next(f for f in c.body if isinstance(f,ast.FunctionDef) and f.name=='reset')
                assert isinstance(f.body[0],ast.Assign) and ast.unparse(f.body[0])=='self.counter[0] = 0'
                f.body=f.body[1:]
        return ast.dump(tree,include_attributes=False)
    assert normalize(old,False)==normalize(new,True),'UNAUTHORIZED_ALGORITHM_CHANGE'
    assert hashlib.sha256((package/'runtime598.py').read_bytes()).digest()==hashlib.sha256((root/'submit_core/runtime598.py').read_bytes()).digest()
    import cv2
    image=cv2.imread(str(checkpoint/'initial-private.png'),0);obs=np.repeat((image/255.).astype(np.float32)[None],4,axis=0);obs.flags.writeable=False
    failure=np.load(checkpoint/'input-private.npy',allow_pickle=False);failure.flags.writeable=False
    records=[];captured=[];select_original=core.Controller.select
    def record(controller,*a,**kw):
        result=select_original(controller,*a,**kw);captured.append(plain(result[1]));return result
    core.Controller.select=record
    def call(label,agent,observation):
        before=agent.counter[0];snapshot=observation.tobytes();cpu=time.process_time();begin=time.perf_counter();error=None;action=None;index=len(captured)
        try:action=agent.act(observation)
        except BaseException as exc:error=type(exc).__name__+':'+str(exc)
        duration=time.perf_counter()-begin
        row=dict(label=label,error=error,model_ticks=agent.counter[0]-before,counter_before=before,counter_after=agent.counter[0],limit=agent.counter.limit,whole_act_s=duration,CPU_s=time.process_time()-cpu,observation_unchanged=observation.tobytes()==snapshot)
        if action is not None:
            row['valid_raw_float32_action']=bool(isinstance(action,np.ndarray) and action.dtype==np.float32 and action.shape==(3,) and np.isfinite(action).all() and -1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1)
        records.append(row);assert duration<5 and row['observation_unchanged']
        return action.tobytes() if action is not None else None,captured[-1] if len(captured)>index else None,row
    old_agent=baseline.Agent();new_agent=candidate.Agent();assert old_agent.counter.limit==50000 and new_agent.counter.limit==core.MAX_MODEL_TICKS==200000
    a,b,r=call('baseline_initial',old_agent,obs);c,d,q=call('candidate_initial',new_agent,obs);assert a==c and b==d and r['model_ticks']==q['model_ticks']==820
    # Episode resets must match fresh calculations; diagnostic counts differ by
    # design, while action bytes and full chooser reports must remain identical.
    old_agent.reset(obs);new_agent.reset(obs);assert old_agent.counter[0]==820 and new_agent.counter[0]==0
    a,b,r=call('baseline_second_reset_initial',old_agent,obs);c,d,q=call('candidate_second_reset_initial',new_agent,obs);assert a==c and b==d
    preserved=candidate.Agent();preserved.counter.limit=1234;preserved.counter[0]=100;preserved.reset(obs);assert preserved.counter[0]==0 and preserved.counter.limit==1234
    # Synthetic offsets test the configuration boundary without spending50k
    # model steps. The actual executed deltas alone count against this test.
    old_default=baseline.Agent();old_default.counter[0]=49999;_,_,r=call('old_default_cross_50k',old_default,obs);assert 'ADAPTER_MODEL_TICK_BUDGET' in r['error'] and r['model_ticks']==1
    old_dev=baseline.Agent();old_dev.counter.limit=200000;old_dev.counter[0]=49999
    patched=candidate.Agent();patched.counter[0]=49999
    a,b,r=call('baseline_DEV_configuration_cross_50k',old_dev,obs);c,d,q=call('candidate_default_cross_50k',patched,obs);assert a==c and b==d and r['model_ticks']==q['model_ticks']==820
    count=candidate._TickCounter();count[0]=200000
    try:count[0]+=1
    except RuntimeError as exc:assert str(exc)=='ADAPTER_MODEL_TICK_BUDGET'
    else:raise AssertionError('HARD_CAP_DISABLED')
    assert count[0]==200000
    memory=(checkpoint/'agent-before-private.pkl').read_bytes();native=json.loads((checkpoint/'result-private.json').read_text())
    old_agent=baseline.Agent();old_agent.__dict__=pickle.loads(memory);new_agent=candidate.Agent();new_agent.__dict__=pickle.loads(memory)
    a,b,r=call('baseline_saved_failure',old_agent,failure);c,d,q=call('candidate_saved_failure',new_agent,failure)
    assert a is c is None and b==d and r['error']==q['error']==native['worker_failure']['error']
    assert plain(old_agent.diagnostics)==plain(new_agent.diagnostics)==native['worker_failure']['diagnostics']
    # The research quota is outside Agent and cannot be renewed by reset.
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    stderr=(out/'worker-stderr-private.log').open('w');proc=subprocess.Popen([sys.executable,'-u',str(root/'retry/submit_worker.py'),str(root/'submit_core/observation_agent.py'),'1640'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,env=env)
    def receive(timeout):
        assert select.select([proc.stdout],[],[],timeout)[0],'WORKER_DEADLINE'
        return json.loads(proc.stdout.readline())
    def request(command):
        begin=time.perf_counter();proc.stdin.write(command+obs.tobytes());proc.stdin.flush();r=receive(5.);r['whole_request_s']=time.perf_counter()-begin;assert r['whole_request_s']<5.;return r
    ready=receive(10.);responses=[]
    try:
        for episode in range(3):
            reset=request(b'R');action=request(b'A');responses.append(dict(episode=episode+1,reset=reset,action=action))
        assert all('action' in r['action'] for r in responses[:2])
        assert [r['action']['resource_model_ticks'] for r in responses]==[820,1640,1640]
        assert [r['reset']['episode_model_ticks'] for r in responses]==[0,0,0]
        assert 'ADAPTER_MODEL_TICK_BUDGET' in responses[-1]['action']['error']
    finally:
        proc.stdin.write(b'Q');proc.stdin.flush();proc.wait(timeout=5);stderr.close()
    result=dict(status='PASS',only_counter_default_and_reset_changed=True,core_bytes_unchanged=True,default_limit=200000,original_chooser_limit=180000,episode_reset_equivalent_to_fresh=True,external_research_quota_survives_resets=True,original_explicit_test_cap_preserved=True,synthetic_counter_offsets_not_executed_ticks=True,
        initial_action_bytes_and_complete_reports_identical=True,cross_50k_matches_prior_DEV_configuration=True,saved_failure_preserved=True,
        calls=records,worker_startup_s=ready['startup_wall_s'],worker_max_RSS_KiB=max(r['action']['max_RSS_KiB'] for r in responses),worker_max_whole_request_s=max(r['action']['whole_request_s'] for r in responses),
        worker_quota_model_ticks=responses[-1]['action']['resource_model_ticks'],model_ticks=sum(r['model_ticks'] for r in records)+responses[-1]['action']['resource_model_ticks'],CPU_s=time.process_time()-start+sum(r['action']['CPU_s']+r['reset']['CPU_s'] for r in responses),wall_s=time.perf_counter()-wall,native_actions=0)
    (out/'result-private.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='calls'},indent=2));assert result['model_ticks']<50000 and result['CPU_s']<600


if __name__=='__main__':main()
