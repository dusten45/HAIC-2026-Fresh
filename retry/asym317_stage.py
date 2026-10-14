"""Register one matched B/C pilot, actor-only export, fixed six TRAIN final eval."""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import diagnose


def prepare(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage317';assert not D.exists();D.mkdir(mode=0o700)
    old=read(R/'stage313/plan.json');v=read(R/'project-effective-budget-v322.json')
    assert v['research_remaining']==2195 and v['B_operating_cap']==1330000
    grant=dict(stage=317,explicit_research_increment=20189,research_after=22384,B_after=1350189,reserve=84000,
        source='Explicit delegated317 matched pilot authorization; this pilot only')
    save(D/'budget-extension.json',grant)
    v.update(version=323,prior_budget_path=str(R/'project-effective-budget-v322.json'),prior_budget_sha256=sha(R/'project-effective-budget-v322.json'),
        B_operating_cap=1350189,B_increment=20189,research_remaining=22384,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'))
    save(R/'project-effective-budget-v323.json',v)
    rows=[]
    for road in old['screen']:
        rows += [json.loads(s)['features'] for s in (R/'stage306/collection'/road/'trace-private.jsonl').read_text().splitlines()]
    x=np.array(rows);mean=x.mean(0);std=np.maximum(x.std(0),1e-6)
    q=D/'normalization-private.npz';np.savez(q,mean=mean,std=std);q.chmod(0o600)
    cfg=dict(old['baseline296']['config'],worker_path=str(G/'retry/ppo275_worker.py'),worker_sha256=sha(G/'retry/ppo275_worker.py'))
    roads=['O0','N0','O2','N1','N2','N3']
    p=dict(stage=317,deadline_utc='2026-10-16T10:01:55+00:00',base=cfg,baseline296=old['baseline296'],
        normalization=str(q),cases={r:old['cases'][r] for r in roads},initial_observations={r:old['initial_observations'][r] for r in roads},
        sandbox_path=old['sandbox_path'],roads=roads,noise_seed=31701,shuffle_seed=31702,GAE_lambda=.95,
        stage_root=str(D),native_cap=8192,comparison='Count first; equal count strict common-completion mean improvement. Compare C vs B and both vs cached296. No damage/minimum-gain veto, selection, DEV or promotion.',
        rule='Fresh identical legal28 actor zero mean residual; equal31-input hidden32 critics, extra input weights0. B extras0,C current pre-progress/damage/time160. PredictS and subtract currentoffset forV. Same target offset in critic loss/bootstrap. No316 ridge parameters.',
        reset_accounting='Current actual reset progress is known for critic/offset; reward still original previous_progress0. First terminal S target differs by known reset progress, not a guessed reset state. Both arms identical.',
        hash_source_names=['asym317_stage.py','asym317_train.py','asym317_model.py','asym317_build.py','asym317_eval.py','ppo275_model.py','ppo244_math.py','ppo275_worker.py','pixel263_worker.py','frozen_composite_runtime.py'])
    paths=[G/'retry'/n for n in p['hash_source_names']]+[Path(cfg['archive_path']),q,R/'project-effective-budget-v323.json']
    p['hashes']={str(q):sha(q) for q in paths}
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    save(D/'previous-current-champion.json',read(R/'current-champion.json'))
    save(D/'budget.json',dict(actions=0,training=0,evaluation=0))
    for arm in ['B','C']:
        A=D/arm;A.mkdir(mode=0o700);save(A/'training-plan.json',dict(p,arm=arm))
        (A/'training-plan.sha256').write_text(sha(A/'training-plan.json')+'\n');(A/'training-plan.sha256').chmod(0o600)
        save(A/'budget.json',dict(actions=0,training=0,evaluation=0))
    print('317 registered, research22384=training16384+evaluation6000; reserve unchanged',flush=True)


def preflight(R):
    import torch
    from retry.asym317_model import create,inputs
    from retry.ppo275_model import vector,apply
    from retry.asym317_build import build
    from retry.frozen_composite_runtime import prepare as actor
    G=Path(__file__).resolve().parent.parent;D=R/'stage317';p=read(D/'plan.json')
    assert not (D/'preflight.json').exists()
    a,c=create();b,d=create()
    assert all(torch.equal(a.state_dict()[k],b.state_dict()[k]) for k in a.state_dict())
    assert all(torch.equal(c.state_dict()[k],d.state_dict()[k]) for k in c.state_dict())
    normal=np.load(p['normalization']);params={f'actor_{k}':v.detach().numpy() for k,v in a.state_dict().items()}
    q=D/'initial-actor-private.npz';np.savez(q,**params,mean=normal['mean'],std=normal['std']);q.chmod(0o600)
    zero=build(Path(p['base']['archive_path']),q,D/'zero-policy-private.zip')
    zero.update(worker_path=str(G/'retry/pixel263_worker.py'),worker_sha256=sha(G/'retry/pixel263_worker.py'))
    workers=[];checks=0
    try:
        workers=[actor(p['base'],D/'preflight-base',p['sandbox_path']),actor(zero,D/'preflight-zero',p['sandbox_path'])]
        obs=np.load(R/'stage306/collection/O0/observations-actions-private.npz')['observations']
        for w in workers:w.call('reset',obs[0])
        for image in obs[:12]:
            ra,_=workers[0].call('act',image);rb,_=workers[1].call('act',image)
            x=vector(ra,normal['mean'],normal['std']);cb,off=inputs(x,.23,.4,.11,'B');cc,_=inputs(x,.23,.4,.11,'C')
            with torch.no_grad():
                assert torch.equal(c(torch.tensor(cb)),d(torch.tensor(cc)))
                mu=a(torch.tensor(x)).numpy();assert np.all(mu==0)
            action=apply(ra['action'],mu);ack,_=workers[0].call('commit',action)
            assert np.array_equal(action,np.array(rb['action'],np.float32)) and ra['features']==rb['features']
            assert all(ack['state'][k]==rb['nominal_state'][k] for k in ['previous_steer','hazards_sha256','previous_image_sha256','lateral_acceleration'])
            checks+=1
    finally:
        for w in workers:assert w.close()['process_reaped']
    save(D/'preflight.json',dict(passed=True,zero_actor_base_identity_pairs=checks,equal_actor_and31critic_initial_tensors=True,
        critic_extra_weights_zero=True,initial_value_equal=True,no316coefficients=True,new_native=0))
    print('317 zero residual identity and critic initialization verified',flush=True)


def train(R):
    D=R/'stage317';assert read(D/'preflight.json')['passed'];assert not (D/'training-processes.json').exists()
    procs=[];start=time.time()
    for arm in ['B','C']:
        F=D/arm;log=(F/'training-driver-private.log').open('x');(F/'training-driver-private.log').chmod(0o600)
        proc=subprocess.Popen([sys.executable,'-m','retry.asym317_train','--plan',str(F/'training-plan.json')],stdout=log,stderr=subprocess.STDOUT,
            env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        procs.append((arm,proc,log))
    save(D/'training-processes.json',dict(epoch=start,processes={a:p.pid for a,p,l in procs}))
    for arm,proc,log in procs:
        rc=proc.wait();log.close();print(arm+' child exit '+str(rc),flush=True)
    save(D/'training-wall.json',dict(parallel_elapsed_s=time.time()-start))


def finalize(R):
    import torch
    from retry.asym317_model import create
    from retry.asym317_build import build
    from retry.ppo275_model import vector,apply
    from retry.frozen_composite_runtime import prepare as actor
    G=Path(__file__).resolve().parent.parent;D=R/'stage317';p=read(D/'plan.json')
    assert read(D/'first-rollout-verified.json')['passed'];assert not (D/'evaluation-plan.json').exists()
    configs={};parity=[]
    for arm in ['B','C']:
        F=D/arm;o=read(F/'training-outcome-private.json');assert not o['technical_error'] and len(o['updates'])==8
        assert read(F/'budget.json')['training']==8192
        cfg=build(Path(p['base']['archive_path']),F/'final-actor-private.npz',F/'submission-final-private.zip')
        cfg.update(worker_path=str(G/'retry/pixel263_worker.py'),worker_sha256=sha(G/'retry/pixel263_worker.py'));save(F/'candidate-private.json',cfg);configs[arm]=cfg
        net,_=create();net.load_state_dict(torch.load(F/'checkpoint8.pt')['actor']);normal=np.load(p['normalization'])
        workers=[];count=0
        try:
            workers=[actor(p['base'],F/'parity-base',p['sandbox_path']),actor(cfg,F/'parity-runtime',p['sandbox_path'])]
            obs=np.load(R/'stage306/collection/O0/observations-actions-private.npz')['observations']
            for w in workers:w.call('reset',obs[0])
            for image in obs[:12]:
                ra,_=workers[0].call('act',image);rb,_=workers[1].call('act',image)
                with torch.no_grad():mu=net(torch.tensor(vector(ra,normal['mean'],normal['std']))).numpy()
                action=apply(ra['action'],mu);ack,_=workers[0].call('commit',action)
                assert np.array_equal(action,np.array(rb['action'],np.float32))
                assert ra['features']==rb['features']
                assert all(ack['state'][k]==rb['nominal_state'][k] for k in ['previous_steer','hazards_sha256','previous_image_sha256','lateral_acceleration'])
                count+=1
        finally:
            for w in workers:assert w.close()['process_reaped']
        parity.append(dict(arm=arm,torch_numpy_action_and_memory_exact_pairs=count,actor_only_export=True))
    order=[dict(road=r,arm=a) for i,r in enumerate(p['roads']) for a in (['B','C'] if i%2==0 else ['C','B'])]
    ep=dict(p,candidates=configs,order=order)
    ep['hashes']=dict(p['hashes'])
    for cfg in configs.values():ep['hashes'][cfg['archive_path']]=cfg['archive_sha256']
    save(D/'evaluation-plan.json',ep);(D/'evaluation-plan.sha256').write_text(sha(D/'evaluation-plan.json')+'\n');(D/'evaluation-plan.sha256').chmod(0o600)
    save(D/'export-parity.json',parity);print('317 final8 only, actor-only exports verified;12 fixed TRAIN endpoints registered',flush=True)


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage317';p=read(D/'plan.json');eo=read(D/'evaluation-outcome-private.json');b=read(D/'budget.json')
    assert not (D/'cost.json').exists();training={a:read(D/a/'training-outcome-private.json') for a in ['B','C']}
    tr=[e for o in training.values() for e in o['episodes']];rr=eo['results']
    assert sum(e['native_actions'] for e in tr)+sum(e['native_actions'] for e in rr)==b['actions']<=22384
    prior=R/'project-effective-budget-v323.json';v=read(prior)
    cost=dict(stage=317,new_wrapper_actions=b['actions'],training_native=b['training'],evaluation_native=b['evaluation'],native_cap=22384,
        raw_step_ticks=sum(e['raw_step_ticks'] for e in tr+rr),raw_reset_ticks=sum(e['raw_reset_ticks'] for e in tr+rr),
        training_parallel_wall_s=read(D/'training-wall.json')['parallel_elapsed_s'],evaluation_wall_s=eo['wall_s'],
        training_CPU_s=sum(o['CPU_s'] for o in training.values()),evaluation_CPU_s=eo['CPU_s'],actor_CPU_s=sum(e['actor_CPU_s'] for e in tr+rr),
        source_model_physics_ticks=0,new_paid_resources=0,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],
        research_remaining=v['research_remaining']-b['actions'],final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1350189)
    save(D/'cost.json',cost);v.update(version=324,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),
        actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage317_new_wrapper_actions=b['actions'])
    assert not (R/'project-effective-budget-v324.json').exists();save(R/'project-effective-budget-v324.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==317 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json')
    safe=lambda r:{k:r.get(k) for k in ['arm','road','completed','actual_DNF','censored','unexecuted','technical_error','lap_ms','damage','native_actions','retire_reason']}
    arms={};base=[r for r in p['baseline296']['results'] if r['road'] in p['roads']]
    for a in ['B','C']:
        ar=[r for r in rr if r['arm']==a];fully=len(ar)==6 and not any(r.get('unexecuted') or r.get('censored') or r.get('technical_error') for r in ar)
        arms[a]=dict(results=[safe(r) for r in ar],fully_observed=fully,completions=sum(r['completed'] for r in ar),against296=diagnose(ar,base) if fully else None,
            updates=training[a]['updates'],training_complete=sum(e['completed'] for e in training[a]['episodes']),training_DNF=sum(e['actual_DNF'] for e in training[a]['episodes']),training_cuts=sum(e['collection_cut'] for e in training[a]['episodes']))
    pair=diagnose([r for r in rr if r['arm']=='C'],[r for r in rr if r['arm']=='B']) if all(arms[a]['fully_observed'] for a in arms) else None
    pub=dict(stage=317,rule=p['rule'],comparison=p['comparison'],preflight=read(D/'preflight.json'),first_matched_rollout=read(D/'first-rollout-verified.json'),
        actor_only_export_parity=read(D/'export-parity.json'),arms=arms,C_against_B=pair,baseline296=[safe(r) for r in base],cost=cost,
        technical_error=eo['technical_error'],champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,automatic_extension=False,
        limitations=['316 C-A uncertainty and completion-stratum worsening remain.','Single matched noise/shuffle seed, same six known TRAIN, eight updates; not convergence or generalization proof.'])
    save(G/'retry/asym317_result.json',pub);print(json.dumps(dict(arms={a:{k:x[k] for k in ['fully_observed','completions','against296']} for a,x in arms.items()},C_against_B=pair,cost=cost)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','preflight','train','finalize','close']);a.add_argument('--private-root',type=Path,required=True)
    x=a.parse_args();globals()[x.phase](x.private_root.resolve())
