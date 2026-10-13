"""One joint direction, paired signs, executed-memory factorial; no training."""
import argparse,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def prepare(R):
    from retry.frozen_composite_runtime import prepare as actor
    G=Path(__file__).resolve().parent.parent;D=R/'stage273';D.mkdir(mode=0o700)
    assert not (D/'plan.json').exists();old=read(R/'stage271/plan.json');model=np.load(R/'stage231/single-head.npz')
    mean,std=model['mean'],model['std'];features=[]
    for road in ['O0','O2','N0','N1','N2','N3']:
        f=np.load(R/'stage251/training'/road/'cache-private.npz')['features']
        features.append(np.c_[(f-mean)/std,np.ones(len(f))])
    covariance=sum(x.T@x/len(x) for x in features)/len(features)
    raw=np.random.default_rng(273).normal(size=(17,3));radius=np.sqrt(np.trace(raw.T@covariance@raw)/3)
    theta=raw*(.2/radius)
    q=D/'joint-parameters.npz';np.savez(q,mean=mean,std=std,theta=theta,covariance=covariance);q.chmod(0o600)
    base=dict(old['candidate']);base.update(worker_path=str(G/'retry/joint273_worker.py'),worker_sha256=sha(G/'retry/joint273_worker.py'),
        assets={'joint-parameters.npz':dict(path=str(q),sha256=sha(q))})
    configs={}
    for sign in [1,-1]:
        for feedback in ['nominal','executed']:
            name=('plus' if sign==1 else 'minus')+'_'+feedback
            c=dict(base);c['constants']={'joint-mode.json':dict(sign=sign,feedback=feedback)};configs[name]=c
    sources=[G/'retry'/n for n in ['joint273_prepare.py','joint273_worker.py','joint273_run.py','frozen_composite_runtime.py','pixel263_worker.py','ppo244_math.py','ars247_math.py','diagnose.py']]
    hashes={str(p):sha(p) for p in sources+[q,Path(base['archive_path']),R/'stage231/single-head.npz',R/'project-effective-budget-v273.json']}
    for road in ['O0','O2','N0','N1','N2','N3']:
        p=R/'stage251/training'/road/'cache-private.npz';hashes[str(p)]=sha(p)
    order=[dict(road='O0',policy=n) for n in ['plus_nominal','plus_executed','minus_executed','minus_nominal']]+[dict(road='N0',policy=n) for n in ['plus_executed','plus_nominal','minus_nominal','minus_executed']]
    plan=dict(stage=273,deadline_utc='2026-10-16T10:01:55+00:00',order=order,max_actions=2600,per_case_cap=325,
        cases={r:old['cases'][r] for r in ['O0','N0']},initial_observations={r:old['initial_observations'][r] for r in ['O0','N0']},baselines={r:old['baselines'][r] for r in ['O0','N0']},
        configs=configs,sandbox_path=old['sandbox_path'],hashes=hashes,seed=273,parameter_directions=1,antithetic_signs=2,latent_RMS_on_equal_road_saved240=.2,
        residual_bounds=[.015,.03,.02],train_steps=0,GT_runtime_inputs=False,
        primary_gate='Executed-memory4/4complete and at least3of4matched memory pairs faster, no slower pair by more than80ms; censoredpairs unknown and forbid advance.',
        candidate_gate='A fixed executed-memory sign must complete both roads faster than240 on both to recommend longer legal joint-policy learning. No automatic champion or screen.',
        objective='Official completion first, time second; terminal return2-T/160 ifcomplete,p-1ifactualDNF,censor=null. Damage diagnostic only.',
        stop='All8scheduled arms unless technical failure; no outcome pruning/refit/additionaldirections. Per-case325actioncap is censoring; no native replay.')
    save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0))
    pairs=0;calls=0;start=time.perf_counter();a=b=None
    baseline=dict(base);baseline['worker_path']=str(G/'retry/pixel263_worker.py');baseline['worker_sha256']=sha(G/'retry/pixel263_worker.py');baseline['assets']={};baseline['constants']={}
    zero=dict(base);zero['constants']={'joint-mode.json':dict(sign=0,feedback='executed')}
    try:
        a=actor(baseline,D/'identity_base',plan['sandbox_path']);b=actor(zero,D/'identity_zero',plan['sandbox_path'])
        for road in ['O0','N0']:
            z=np.load(R/'stage251/training'/road/'cache-private.npz')
            for w in [a,b]:w.call('reset',z['observations'][0]);calls+=1
            for obs in z['observations'][:8]:
                ra,_=a.call('act',obs);rb,_=b.call('act',obs);calls+=2
                assert ra['action']==rb['action'] and ra['features']==rb['features'] and ra['nominal_state']==rb['nominal_state'];pairs+=1
    finally:
        if a:assert a.close()['process_reaped']
        if b:assert b.close()['process_reaped']
    # Frozen joint math and feedback switch use the same base state/action.
    synthetic=dict(base);synthetic['constants']={'joint-mode.json':dict(sign=1,feedback='executed')}
    w=None
    try:
        w=actor(synthetic,D/'active_preflight',plan['sandbox_path']);z=np.load(R/'stage251/training/O0/cache-private.npz');w.call('reset',z['observations'][0]);calls+=1
        for obs in z['observations'][:8]:
            rb,_=w.call('act',obs);calls+=1;f=np.array(rb['features']);audit=rb['joint_audit'];latent=np.r_[(f-mean)/std,1.]@theta
            expected=np.clip(np.array(audit['base_action'])+[.015,.03,.02]*np.tanh(latent),[-.4,0,0],[.4,1,1]).astype(np.float32)
            assert np.array_equal(expected,np.array(rb['action'],np.float32));assert rb['nominal_state']['previous_steer']==float(expected[0])
    finally:
        if w:assert w.close()['process_reaped']
    save(D/'preflight.json',dict(passed=True,zero_identity_pairs=pairs,active_math_and_memory_checks=8,offline_actor_calls=calls,wall_s=time.perf_counter()-start,native=0,model_physics=0))
    print('273preflightpassed,16identitypairs,8activechecks,native0',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);prepare(a.parse_args().private_root.resolve())
