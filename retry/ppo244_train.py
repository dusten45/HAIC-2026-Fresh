"""One fixed residual PPO244 pilot, latent likelihood, private durable batches.

Only16legal features enteractor/value; coverage/time/terminal are reward only.
Batchcuts bootstrap then close/reset to nextfixedroad, enabling no-replay resume.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np


def train(path):
    import torch
    from torch import nn
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    from retry.frozen_paired_evaluation import sha,verify_files
    from retry.ppo244_math import apply,log_probability,reward,T_LIMIT,STD
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip();verify_files(p['source_sha256']);verify_files(p['runtime_sha256'])
    D=path.parent;torch.set_num_threads(1);torch.manual_seed(24403)
    model=np.load(p['normalization_path']);mean,std=model['mean'],model['std']
    actor=nn.Linear(16,2,dtype=torch.float64);nn.init.zeros_(actor.weight);nn.init.zeros_(actor.bias)
    critic=nn.Sequential(nn.Linear(16,32,dtype=torch.float64),nn.Tanh(),nn.Linear(32,1,dtype=torch.float64));nn.init.normal_(critic[0].weight,0,.25);nn.init.zeros_(critic[0].bias);nn.init.zeros_(critic[2].weight);nn.init.zeros_(critic[2].bias)
    ao=torch.optim.Adam(actor.parameters(),lr=3e-4);vo=torch.optim.Adam(critic.parameters(),lr=3e-4)
    control_rng=np.random.default_rng(244);noise=np.random.default_rng(24401);shuffle=np.random.default_rng(24402)
    def read(q):return json.loads(q.read_text())
    def save(q,x,exclusive=False):
        payload=json.dumps(x,indent=2,allow_nan=False)+'\n'
        if exclusive:
            with q.open('x') as f:f.write(payload)
        else:
            t=q.with_name(q.name+'.tmp');t.write_text(payload);t.chmod(0o600);t.replace(q)
        q.chmod(0o600)
    if not (D/'opening.json').exists():save(D/'opening.json',dict(stage=244,start_epoch=time.time(),one_use=True),True)
    state=read(D/'state.json') if (D/'state.json').exists() else dict(noisy_done=0,batches_done=0,road_cursor=0,episode_serial=0,noise_state=noise.bit_generator.state,control_state=control_rng.bit_generator.state,shuffle_state=shuffle.bit_generator.state,checkpoint=None)
    # Recover completed optimizer transactions; unfinished native episodes are never replayed.
    for cp_path in sorted(D.glob('checkpoint*.pt'),key=lambda q:int(q.stem.replace('checkpoint',''))):
        saved=torch.load(cp_path)
        if 'state' in saved and saved['state']['batches_done']>state['batches_done']:
            state=saved['state'];save(D/'state.json',state);save(D/'updates.json',saved['updates'])
    if state['checkpoint']:
        cp=torch.load(D/state['checkpoint']);actor.load_state_dict(cp['actor']);critic.load_state_dict(cp['critic']);ao.load_state_dict(cp['actor_optimizer']);vo.load_state_dict(cp['value_optimizer'])
    noise.bit_generator.state=state['noise_state'];control_rng.bit_generator.state=state['control_state'];shuffle.bit_generator.state=state['shuffle_state']
    episodes=read(D/'episodes.json') if (D/'episodes.json').exists() else [];updates=read(D/'updates.json') if (D/'updates.json').exists() else []
    completed_records=sorted((D/'episodes').glob('episode*/completion.json'),key=lambda q:int(q.parent.name.replace('episode',''))) if (D/'episodes').exists() else []
    for record in completed_records:
        saved=read(record)
        if saved['state']['episode_serial']>state['episode_serial']:
            state=saved['state'];noise.bit_generator.state=state['noise_state'];control_rng.bit_generator.state=state['control_state'];shuffle.bit_generator.state=state['shuffle_state']
        if not any(e.get('serial')==saved['result']['serial'] for e in episodes):episodes.append(saved['result'])
    def persist():
        state.update(noise_state=noise.bit_generator.state,control_state=control_rng.bit_generator.state,shuffle_state=shuffle.bit_generator.state);save(D/'state.json',state);save(D/'episodes.json',episodes);save(D/'updates.json',updates)
    def deadline():assert time.time()<__import__('datetime').datetime.fromisoformat(p['deadline_utc']).timestamp()
    def charge(phase):
        b=read(D/'budget.json');assert b['actions']<11000;b['actions']+=1;b['phases'][phase]=b['phases'].get(phase,0)+1;save(D/'budget.json',b)
    def vector(response):return np.asarray(response['legal_feature_audit']['features'],float)
    def value(x):
        with torch.no_grad():return float(critic(torch.as_tensor(x,dtype=torch.float64)).item())
    def episode(label,phase,cap,rng,deterministic=False,freeze_zero=False):
        deadline();serial=state['episode_serial'];folder=D/'episodes'/('episode'+str(serial));folder.mkdir(parents=True,exist_ok=False,mode=0o700)
        worker=env=None;rows=[];buffer=[];start=time.perf_counter();actor_CPU=0.;calls=0;policy_ms=[];rawticks=0;reset_ticks=0;result=None
        try:
            worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();case=p['cases'].get(label,p['screen_cases_by_label'].get(label));ob,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});reset_ticks=round(env.unwrapped.t*50);start_t=env.unwrapped.t
            response,reset_ms=worker.call('reset',ob);assert reset_ms<=5000
            pending,ms=worker.call('act',ob);calls+=1;actor_CPU=pending['actor_cumulative_CPU_s'];previous_p=0.;previous_time=0.;ep_return=0.;terminal=False;ended=truncated=False
            for step in range(1,cap+1):
                deadline();f=vector(pending);x=(f-mean)/std;base=np.asarray(pending['action'],np.float32)
                policy_start=time.perf_counter()
                with torch.no_grad():mu=actor(torch.as_tensor(x,dtype=torch.float64)).numpy().copy()
                if freeze_zero:assert np.array_equal(mu,np.zeros(2))
                z=mu.copy() if deterministic else mu+STD*rng.normal(size=2);oldlog=float(log_probability(z,mu));action=apply(base,z);extra_ms=(time.perf_counter()-policy_start)*1000;v=value(x);assert action[0]==base[0] and ms+extra_ms<=5000
                charge(phase);old_t=env.unwrapped.t;ob,_,ended,truncated,info=env.step(action);ticks=round((env.unwrapped.t-old_t)*50);rawticks+=ticks;elapsed=env.unwrapped.t-start_t;progress=env.unwrapped.tile_visited_count/len(env.unwrapped.track)
                completed=env.unwrapped.finish_time_s is not None;official_limit=step>=2000 and not completed;terminal=bool(ended or truncated or official_limit)
                status='completed' if completed else 'DNF' if terminal else None
                rt=env.unwrapped.finish_time_s-start_t if completed else elapsed
                rew=reward(progress,previous_p,rt,previous_time,status);ep_return+=rew;previous_p=progress;previous_time=rt
                cutoff=not terminal and step==cap
                if terminal:nv=0.
                else:
                    nxt,nms=worker.call('act',ob);calls+=1;actor_CPU=nxt['actor_cumulative_CPU_s'];nv=value((vector(nxt)-mean)/std)
                buffer.append(dict(x=x,features=f,latent=z,old_mu=mu,old_logp=oldlog,reward=rew,done=terminal,truncated=cutoff,value=v,next_value=nv,base=base,executed=action))
                speed=float(np.linalg.norm(env.unwrapped.car.hull.linearVelocity));rows.append(dict(action=step,speed_m_s=speed,damage=env.damage.damage,visited=env.unwrapped.tile_visited_count,progress=progress,reward=rew,raw_ticks=ticks,terminal=terminal,collection_truncated=cutoff));policy_ms.append(ms+extra_ms)
                if terminal or cutoff:
                    expected=2-rt/T_LIMIT if completed else progress-1 if terminal else None
                    if expected is not None:assert abs(ep_return-expected)<1e-9
                    result=dict(label=label,phase=phase,native_actions=step,completed=completed,actual_DNF=terminal and not completed,collection_truncated=cutoff,lap_ms=round(rt*1000) if completed else None,retire_reason=info.get('retire_reason') or ('max_steps' if official_limit else 'collection_cut' if cutoff else None),damage=env.damage.damage,visited=env.unwrapped.tile_visited_count,total_tiles=len(env.unwrapped.track),return_sum=ep_return,expected_terminal_return=expected,bootstrap_value=nv if cutoff else None,raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,base_actor_calls=calls,unexecuted_bootstrap_peek_calls=int(cutoff),base_actor_CPU_s=actor_CPU,full_policy_including_baseIPC_ms={'median':float(np.median(policy_ms)),'p95':float(np.percentile(policy_ms,95)),'max':float(max(policy_ms))},wall_s=time.perf_counter()-start)
                    break
                pending,ms=nxt,nms
        finally:
            if worker:reap=worker.close()
            if env:env.close()
        assert result is not None;result['reaping']=reap
        data={k:np.asarray([b[k] for b in buffer]) for k in buffer[0]};q=folder/'latent-buffer.npz';np.savez_compressed(q,**data);q.chmod(0o600)
        save(folder/'trajectory-private.json',rows,True);result.update(serial=serial,batch=state['batches_done'] if phase=='training' else None);save(folder/'result.json',result,True);episodes.append(result);state['episode_serial']+=1
        if phase=='training':state['road_cursor']+=1
        if phase=='control':state['noisy_done']+=1
        state.update(noise_state=noise.bit_generator.state,control_state=control_rng.bit_generator.state,shuffle_state=shuffle.bit_generator.state)
        save(folder/'completion.json',dict(state=state,result=result),True);persist();print(json.dumps(result),flush=True)
        return buffer
    error=None;start=time.perf_counter();cpu=time.process_time()
    try:
        # One control run perroad; no reward/damage gates and no repeatedfills.
        for i,label in enumerate(['O0','N0']):
            if i<state['noisy_done']:continue
            cap=1024-read(D/'budget.json')['phases'].get('control',0)
            if cap<=0:break
            episode(label,'control',cap,control_rng,freeze_zero=True)
        sequence=['O0','N0','O2','N1','N2','N3']
        for batchno in range(state['batches_done'],8):
            batchpath=D/('batch'+str(batchno)+'.npz')
            if batchpath.exists():data=dict(np.load(batchpath))
            else:
                collected=[]
                for e in episodes:
                    if e['phase']=='training' and e.get('batch')==batchno:
                        cached=dict(np.load(D/'episodes'/('episode'+str(e['serial']))/'latent-buffer.npz'))
                        collected.extend({k:cached[k][i] for k in cached} for i in range(len(cached['reward'])))
                while len(collected)<1024:
                    label=sequence[state['road_cursor']%6];buf=episode(label,'training',min(1024-len(collected),2000),noise);collected+=buf
                data={k:np.asarray([b[k] for b in collected]) for k in collected[0]};np.savez_compressed(batchpath,**data);batchpath.chmod(0o600)
            assert len(data['reward'])==1024
            adv=np.zeros(1024);carry=0.
            for i in range(1023,-1,-1):
                done=float(data['done'][i]);delta=data['reward'][i]+(1-done)*data['next_value'][i]-data['value'][i]
                continuation=0. if data['truncated'][i] else 1-done
                carry=delta+.95*continuation*carry;adv[i]=carry
            returns=adv+data['value'];normalized=(adv-adv.mean())/(adv.std()+1e-8)
            X=torch.as_tensor(data['x'],dtype=torch.float64);Z=torch.as_tensor(data['latent'],dtype=torch.float64);oldmu=torch.as_tensor(data['old_mu'],dtype=torch.float64);oldlp=torch.as_tensor(data['old_logp'],dtype=torch.float64);A=torch.as_tensor(normalized,dtype=torch.float64);RET=torch.as_tensor(returns,dtype=torch.float64)
            maxkl=0.;nupdate=0;stopped=False;actor_loss=value_loss=0.
            for epoch in range(2):
                for idx in np.array_split(shuffle.permutation(1024),8):
                    m=actor(X[idx]);kl=((m-oldmu[idx])**2).sum(1).mean()/(2*STD**2);maxkl=max(maxkl,float(kl.item()))
                    if kl.item()>.01:stopped=True;break
                    logp=-.5*((Z[idx]-m)/STD).pow(2).sum(1)-2*np.log(STD)-np.log(2*np.pi);ratio=(logp-oldlp[idx]).exp();assert torch.isfinite(ratio).all()
                    aloss=-torch.minimum(ratio*A[idx],ratio.clamp(.9,1.1)*A[idx]).mean();vloss=(critic(X[idx]).squeeze(1)-RET[idx]).pow(2).mean()
                    assert torch.isfinite(aloss) and torch.isfinite(vloss);ao.zero_grad();aloss.backward();nn.utils.clip_grad_norm_(actor.parameters(),.5);ao.step();vo.zero_grad();(.5*vloss).backward();nn.utils.clip_grad_norm_(critic.parameters(),.5);vo.step();nupdate+=1;actor_loss=float(aloss.item());value_loss=float(vloss.item())
                if stopped:break
            checkpoint='checkpoint'+str(batchno+1)+'.pt'
            state.update(batches_done=batchno+1,checkpoint=checkpoint);updates.append(dict(batch=batchno+1,native_training=(batchno+1)*1024,optimizer_minibatch_steps=nupdate,target_KL_stop=stopped,max_checked_analytic_KL=maxkl,actor_loss=actor_loss,value_MSE=value_loss,actor_max_abs_parameter=float(max(t.abs().max().item() for t in actor.parameters()))));state.update(noise_state=noise.bit_generator.state,control_state=control_rng.bit_generator.state,shuffle_state=shuffle.bit_generator.state)
            temp=D/(checkpoint+'.tmp');torch.save(dict(actor=actor.state_dict(),critic=critic.state_dict(),actor_optimizer=ao.state_dict(),value_optimizer=vo.state_dict(),state=state,updates=updates),temp);temp.chmod(0o600);temp.replace(D/checkpoint);persist();print(json.dumps(updates[-1]),flush=True)
        assert read(D/'budget.json')['phases']['training']==8192
        if not (D/'final-actor.npz').exists():np.savez(D/'final-actor.npz',weights=actor.weight.detach().numpy().T,bias=actor.bias.detach().numpy(),mean=mean,std=std);(D/'final-actor.npz').chmod(0o600)
        # Finalcheckpoint only, no validationbeforethis point.
        for label in ['S0','S1']:
            if any(e['phase']=='screen' and e['label']==label for e in episodes):continue
            cap=11000-read(D/'budget.json')['actions']
            if cap<=0:break
            episode(label,'screen',min(cap,2000),noise,deterministic=True)
    except Exception as e:error=type(e).__name__+': '+str(e);save(D/'technical-error.json',dict(error=error,state=state))
    finally:
        save(D/'outcome.json',dict(stage=244,episodes=episodes,updates=updates,native_actions=read(D/'budget.json')['actions'],phases=read(D/'budget.json')['phases'],wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_this_process_s=time.process_time()-cpu,technical_error=error,batches_done=state['batches_done'],champion_changed=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False))


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);train(a.parse_args().plan.resolve())
