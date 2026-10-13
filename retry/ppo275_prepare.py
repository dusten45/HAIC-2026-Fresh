"""Frozen275 recipe and small likelihood/zero/history/peek checks, no physics."""
import argparse,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.ppo275_model import RECIPE,create,vector,apply,logp,STD

def prepare(R):
    import torch
    from retry.frozen_composite_runtime import prepare as runtime
    G=Path(__file__).resolve().parent.parent;D=R/'stage275';D.mkdir(mode=0o700);assert not (D/'plan.json').exists()
    old=read(R/'stage271/plan.json');base=dict(old['candidate']);base.update(worker_path=str(G/'retry/ppo275_worker.py'),worker_sha256=sha(G/'retry/ppo275_worker.py'))
    cases=read(R/'stage270/plan.json');roads=RECIPE['road_order'];sources=[G/'retry'/n for n in ['ppo275_prepare.py','ppo275_model.py','ppo275_worker.py','ppo275_train.py','ppo244_math.py','frozen_composite_runtime.py','diagnose.py','pixel263_worker.py']]
    hashes={str(q):sha(q) for q in sources+[Path(base['archive_path']),R/'stage231/single-head.npz',R/'project-effective-budget-v276.json']}
    for road in ['O0','N0']:
        q=R/'stage251/training'/road/'cache-private.npz';hashes[str(q)]=sha(q)
    p=dict(stage=275,deadline_utc='2026-10-16T10:01:55+00:00',native_cap=3072,available_research=3179,recipe=RECIPE,base=base,
        cases={r:cases['cases'][r] for r in roads},initial_observations={r:cases['initial_observations'][r] for r in roads},
        normalization=str(R/'stage231/single-head.npz'),sandbox_path=old['sandbox_path'],hashes=hashes,TRAIN_roads=roads,DEV_screen_used=False,
        policy_and_critic_inputs='16currentpixelderivedfeatures + last3ownexecutedactions and availability masks; no GT/roadIDs/progress/time/damage',
        zero_memory_rule='If returned steeringequals240base, preserve exact240nominalfloat64memory; otherwise store returnedfloat32command. float32(memory) always equals actualsteering.',
        likelihood='Stored latentGaussian3D likelihood before tanh/actionclips, fixedstd0.2; no inverseclippedaction likelihood.',
        termination='Official finish or actualDNF bootstrap0; pure rolloutcut criticbootstrap, GAEtrace reset, next episodehistory reset. Peek clones basecontroller and commits no action.',
        stop='Exactly3rollouts/updates unless technical/nonfinite/stateactionerror. No policy selection/DEV screen/checkpoint choice/native control replay.')
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0))
    actor,critic=create();normalization=np.load(p['normalization']);mean,std=normalization['mean'],normalization['std'];start=time.perf_counter();calls=0;pairs=0;a=b=None
    reference=dict(base);reference.update(worker_path=str(G/'retry/pixel263_worker.py'),worker_sha256=sha(G/'retry/pixel263_worker.py'))
    try:
        a=runtime(reference,D/'identity240',p['sandbox_path']);b=runtime(base,D/'identity275',p['sandbox_path'])
        for road in ['O0','N0']:
            z=np.load(R/'stage251/training'/road/'cache-private.npz');a.call('reset',z['observations'][0]);reset,_=b.call('reset',z['observations'][0]);calls+=2
            assert reset['history']==[]
            for obs in z['observations'][:8]:
                ra,_=a.call('act',obs);rb,_=b.call('act',obs);calls+=2;x=vector(rb,mean,std)
                with torch.no_grad():mu=actor(torch.as_tensor(x,dtype=torch.float64)).numpy()
                assert np.array_equal(mu,np.zeros(3));action=apply(rb['action'],mu);assert np.array_equal(action,np.array(ra['action'],np.float32)) and rb['features']==ra['features']
                commit,_=b.call('commit',action);calls+=1;state=commit['state']
                assert state['previous_steer']==ra['nominal_state']['previous_steer'] and state['hazards_sha256']==ra['nominal_state']['hazards_sha256'] and state['previous_image_sha256']==ra['nominal_state']['previous_image_sha256'] and state['lateral_acceleration']==ra['nominal_state']['lateral_acceleration'];pairs+=1
    finally:
        if a:assert a.close()['process_reaped']
        if b:assert b.close()['process_reaped']
    w=None;active_checks=0;peek_checks=0
    try:
        w=runtime(base,D/'active-history',p['sandbox_path']);z=np.load(R/'stage251/training/O0/cache-private.npz');w.call('reset',z['observations'][0]);calls+=1;history=[]
        for i in range(4):
            rb,_=w.call('act',z['observations'][i]);calls+=1;assert rb['history']==history[-3:]
            action=apply(rb['action'],np.array([.1,-.1,.1]));commit,_=w.call('commit',action);calls+=1;history.append(action.tolist())
            assert commit['history']==history[-3:] and np.float32(commit['memory'])==action[0];active_checks+=1
            peek,_=w.call('peek',z['observations'][i+1]);calls+=1;assert peek['state']==commit['state'] and peek['history']==history[-3:] and peek['peek_state_preserved'];peek_checks+=1
        reset,_=w.call('reset',z['observations'][0]);rb,_=w.call('act',z['observations'][0]);calls+=2
        assert reset['history']==rb['history']==[] and rb['history_features']==[0.]*12
    finally:
        if w:assert w.close()['process_reaped']
    mu=np.zeros((4,3));latent=np.random.default_rng(27500).normal(size=(4,3))*STD
    expected=torch.distributions.Normal(torch.tensor(mu),STD).log_prob(torch.tensor(latent)).sum(-1).numpy()
    assert np.max(abs(logp(latent,mu)-expected))<1e-12
    save(D/'preflight.json',dict(passed=True,zero_identity_pairs=pairs,active_commit_history_checks=active_checks,pure_peek_checks=peek_checks,reset_history_checked=True,latent_logprob_matches_torch=True,
        actor_parameters=sum(v.numel() for v in actor.parameters()),critic_parameters=sum(v.numel() for v in critic.parameters()),offline_worker_calls=calls,wall_s=time.perf_counter()-start,native=0,GT_policy_inputs=False,torch_version=torch.__version__))
    print('275preflight passed:16exact240pairs,4commit/history/peekchecks,3Dlogprob verified,native0',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);prepare(a.parse_args().private_root.resolve())
