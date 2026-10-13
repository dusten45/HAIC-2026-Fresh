"""Three real on-policy joint PPO updates; legal pixels/actions, no screen."""
import argparse,time,datetime,hashlib
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.ppo275_model import RECIPE,STD,create,vector,logp,apply,reward

def train(path,recovery=False):
    allstart=time.perf_counter()
    import torch
    from torch import nn
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=path.parent;p=read(path)
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    repair=read(D/'recovery-plan.json') if recovery else None
    if recovery:
        assert sha(D/'recovery-plan.json')==(D/'recovery-plan.sha256').read_text().strip()
        assert not (D/'recovery-opening.json').exists(),'No replay of recovery'
        for q,h in repair['new_source_hashes'].items():assert sha(Path(q))==h
    for q,h in p['hashes'].items():
        if recovery and q in repair['new_source_hashes']:
            assert sha(Path(repair['archived_originals'][q]))==h
        else:assert sha(Path(q))==h
    if recovery:p['base']=dict(p['base'],worker_sha256=repair['new_source_hashes'][p['base']['worker_path']])
    assert read(D/'preflight.json')['passed']
    if not recovery:assert not (D/'opening.json').exists(),'No replay of started training' 
    actor,critic=create();ao=torch.optim.Adam(actor.parameters(),lr=RECIPE['actor_lr']);vo=torch.optim.Adam(critic.parameters(),lr=RECIPE['critic_lr'])
    normalization=np.load(p['normalization']);mean,std=normalization['mean'],normalization['std']
    noise=np.random.default_rng(27501);shuffle=np.random.default_rng(27502)
    opening=D/('recovery-opening.json' if recovery else 'opening.json')
    episodes=[];updates=[];cursor=0;start_batch=1;end_batch=RECIPE['pilot_batches']
    if recovery:
        assert sha(D/'checkpoint1.pt')==repair['checkpoint_sha256']
        checkpoint=torch.load(D/'checkpoint1.pt');actor.load_state_dict(checkpoint['actor']);critic.load_state_dict(checkpoint['critic'])
        ao.load_state_dict(checkpoint['actor_optimizer']);vo.load_state_dict(checkpoint['critic_optimizer'])
        noise.bit_generator.state=checkpoint['noise_state'];shuffle.bit_generator.state=checkpoint['shuffle_state']
        noise.normal(size=(repair['consumed_and_unexecuted_noise_draws'],3))
        cursor=checkpoint['cursor']+1
        episodes=read(D/'episodes-private.json');updates=read(D/'updates-private.json');start_batch=end_batch=2
    save(opening,dict(epoch=time.time(),initialization_wall_s=time.perf_counter()-allstart))
    serial=len(list(D.glob('episode[0-9]*_*')))
    error=None;cpu=time.process_time();collectwall=0.;updatewall=0.
    def deadline():assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
    def evaluate(net,x):
        with torch.no_grad():return net(torch.as_tensor(x,dtype=torch.float64)).numpy().copy()
    def episode(batch,cap):
        nonlocal cursor,collectwall,serial
        road=RECIPE['road_order'][cursor%6];cursor+=1;folder=D/f'episode{serial:03d}_{road}';serial+=1;folder.mkdir(mode=0o700)
        env=worker=None;buffer=[];rows=[];rawticks=0;calls=0;peeks=0;start=time.perf_counter();elapsed_return=0.;previous_p=previous_t=0.;timings=[]
        try:
            worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][road]
            obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;start_t=raw.t;resetticks=round(start_t*50)
            assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road]
            response,_=worker.call('reset',obs);assert response['history']==[]
            pending,ipc=worker.call('act',obs);calls+=1
            for step in range(1,cap+1):
                deadline();tick=time.perf_counter();assert not pending['python_audit_denied_events']
                x=vector(pending,mean,std);mu=evaluate(actor,x);v=float(evaluate(critic,x)[0]);z=mu+STD*noise.normal(size=3)
                oldlp=float(logp(z,mu));action=apply(pending['action'],z)
                committed,commit_ipc=worker.call('commit',action);calls+=1;assert committed['history'][-1]==action.tolist()
                assert np.float32(committed['memory'])==action[0]
                extra_ms=(time.perf_counter()-tick)*1000;timings.append(ipc+extra_ms)
                budget=read(D/'budget.json');assert budget['actions']<p['native_cap'];budget['actions']+=1;save(D/'budget.json',budget)
                before=raw.t;obs,_,ended,truncated,info=env.step(action);rawticks+=round((raw.t-before)*50)
                complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000);cut=not terminal and step==cap
                t=raw.finish_time_s-start_t if complete else raw.t-start_t;progress=raw.tile_visited_count/len(raw.track)
                rt=reward(progress,previous_p,t,previous_t,'completed' if complete else 'DNF' if terminal else None);elapsed_return+=rt;previous_p=progress;previous_t=t
                if terminal:nv=0.;next_response=None
                else:
                    op='peek' if cut else 'act';next_response,next_ipc=worker.call(op,obs);calls+=1
                    assert not next_response['python_audit_denied_events']
                    if cut:assert next_response['peek_state_preserved'] and next_response['state']==committed['state'];peeks+=1
                    else:assert next_response['features'][7]==committed['memory']
                    assert next_response['history']==committed['history'];nv=float(evaluate(critic,vector(next_response,mean,std))[0])
                buffer.append(dict(x=x,latent=z,old_mu=mu,old_logp=oldlp,reward=rt,value=v,next_value=nv,done=terminal,cut=cut,base=np.array(pending['action'],np.float32),executed=action))
                rows.append(dict(step=step,features=pending['features'],history=pending['history'],action=action.tolist(),committed_memory=committed['memory'],history_after=committed['history'],reward=rt,damage=env.damage.damage,visited=raw.tile_visited_count,terminal=terminal,collection_cut=cut,full_policy_ms=timings[-1]))
                if terminal or cut:break
                pending,ipc=next_response,next_ipc
            expected=2-t/160 if complete else progress-1 if terminal else None
            if expected is not None:assert abs(elapsed_return-expected)<1e-9
            r=dict(road=road,batch=batch,native_actions=step,completed=complete,actual_DNF=terminal and not complete,collection_cut=cut,
                lap_ms=round(t*1000) if complete else None,return_sum=elapsed_return,expected_terminal_return=expected,
                retire_reason=None if complete else info.get('retire_reason') or ('collection_cut' if cut else 'max_steps'),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),
                bootstrap_value=nv if cut else 0.,raw_step_ticks=rawticks,raw_reset_ticks=resetticks,worker_calls=calls,unexecuted_pure_peek_calls=peeks,
                actor_CPU_s=committed['actor_cumulative_CPU_s'] if terminal else next_response['actor_cumulative_CPU_s'],wall_s=time.perf_counter()-start,
                full_policy_ms=dict(median=float(np.median(timings)),p95=float(np.percentile(timings,95)),max=float(max(timings))),pixel_only=True,GT_policy_inputs=False)
        finally:
            if worker:reaping=worker.close()
            if env:env.close()
        r['reaping']=reaping;collectwall+=r['wall_s'];save(folder/'result.json',r);save(folder/'trajectory-private.json',rows)
        q=folder/'buffer-private.npz';np.savez_compressed(q,**{k:np.array([b[k] for b in buffer]) for k in buffer[0]});q.chmod(0o600)
        episodes.append(r);save(D/'episodes-private.json',episodes)
        print(str({k:r[k] for k in ['road','batch','completed','actual_DNF','collection_cut','native_actions','lap_ms']}),flush=True)
        return buffer
    try:
        for batch in range(start_batch,end_batch+1):
            collected=[]
            while len(collected)<RECIPE['rollout']:collected+=episode(batch,min(2000,RECIPE['rollout']-len(collected)))
            data={k:np.array([b[k] for b in collected]) for k in collected[0]};q=D/f'rollout{batch}-private.npz';np.savez_compressed(q,**data);q.chmod(0o600)
            # LatentGaussian likelihood; never infer likelihood from clippedactions.
            assert np.max(abs(logp(data['latent'],data['old_mu'])-data['old_logp']))<1e-12
            adv=np.zeros(len(collected));carry=0.
            for i in range(len(collected)-1,-1,-1):
                terminal=float(data['done'][i]);delta=data['reward'][i]+(1-terminal)*data['next_value'][i]-data['value'][i]
                carry=delta+RECIPE['GAE_lambda']*(0. if data['cut'][i] else 1-terminal)*carry;adv[i]=carry
            target=adv+data['value'];normal=(adv-adv.mean())/(adv.std()+1e-8)
            X=torch.as_tensor(data['x'],dtype=torch.float64);Z=torch.as_tensor(data['latent'],dtype=torch.float64);OLD=torch.as_tensor(data['old_mu'],dtype=torch.float64);LP=torch.as_tensor(data['old_logp'],dtype=torch.float64);A=torch.as_tensor(normal,dtype=torch.float64);RET=torch.as_tensor(target,dtype=torch.float64)
            with torch.no_grad():before_mu=actor(X).clone();before_v=critic(X).squeeze(1).clone()
            assert torch.max(torch.abs(before_mu-OLD)).item()<1e-12
            tick=time.perf_counter();steps=0;maxkl=0.;stopped=False;actor_grad=[];critic_grad=[];clipfractions=[]
            for epoch in range(RECIPE['epochs']):
                for idx in np.array_split(shuffle.permutation(len(X)),len(X)//RECIPE['minibatch']):
                    deadline();m=actor(X[idx]);kl=((m-OLD[idx])**2).sum(1).mean()/(2*STD**2);maxkl=max(maxkl,float(kl.item()))
                    if kl.item()>RECIPE['target_KL']:stopped=True;break
                    lp=-.5*((Z[idx]-m)/STD).pow(2).sum(1)-3*np.log(STD)-1.5*np.log(2*np.pi);ratio=(lp-LP[idx]).exp()
                    assert torch.isfinite(ratio).all();clipfractions.append(float(((ratio<.9)|(ratio>1.1)).double().mean().item()))
                    loss=-torch.minimum(ratio*A[idx],ratio.clamp(.9,1.1)*A[idx]).mean();vloss=(critic(X[idx]).squeeze(1)-RET[idx]).pow(2).mean()
                    assert torch.isfinite(loss) and torch.isfinite(vloss)
                    ao.zero_grad();loss.backward();ag=float(nn.utils.clip_grad_norm_(actor.parameters(),.5));assert np.isfinite(ag);ao.step();actor_grad.append(ag)
                    vo.zero_grad();(.5*vloss).backward();vg=float(nn.utils.clip_grad_norm_(critic.parameters(),.5));assert np.isfinite(vg);vo.step();critic_grad.append(vg);steps+=1
                if stopped:break
            wall=time.perf_counter()-tick;updatewall+=wall
            with torch.no_grad():after_mu=actor(X);after_v=critic(X).squeeze(1)
            assert all(torch.isfinite(v).all() for v in list(actor.parameters())+list(critic.parameters()))
            update=dict(batch=batch,native_training=batch*RECIPE['rollout'],optimizer_minibatch_steps=steps,epochs_completed=epoch if stopped else epoch+1,target_KL_stop=stopped,
                max_checked_analytic_KL=maxkl,final_full_batch_KL=float(((after_mu-OLD)**2).sum(1).mean().item()/(2*STD**2)),actor_gradient_norm_max=max(actor_grad,default=0.),critic_gradient_norm_max=max(critic_grad,default=0.),
                actor_mu_change_RMS=float(((after_mu-before_mu)**2).mean().sqrt().item()),actor_mu_abs_max=float(after_mu.abs().max().item()),
                value_MSE_before=float(((before_v-RET)**2).mean().item()),value_MSE_after=float(((after_v-RET)**2).mean().item()),ratio_clip_fraction_mean=float(np.mean(clipfractions)) if clipfractions else None,wall_s=wall)
            assert steps>0 and update['actor_gradient_norm_max']>0 and update['critic_gradient_norm_max']>0 and update['actor_mu_change_RMS']>0
            updates.append(update);save(D/'updates-private.json',updates)
            q=D/f'checkpoint{batch}.pt';torch.save(dict(actor=actor.state_dict(),critic=critic.state_dict(),actor_optimizer=ao.state_dict(),critic_optimizer=vo.state_dict(),noise_state=noise.bit_generator.state,shuffle_state=shuffle.bit_generator.state,cursor=cursor,recipe=RECIPE),q);q.chmod(0o600)
            print(str(update),flush=True)
        params={f'actor_{k}':v.detach().numpy() for k,v in actor.state_dict().items()};q=D/'final-actor-private.npz';np.savez(q,**params,mean=mean,std=std);q.chmod(0o600)
    except Exception as e:error=type(e).__name__+': '+str(e);save(D/'technical-error.json',dict(error=error,consumed=read(D/'budget.json')))
    save(D/'outcome-private.json',dict(stage=275,episodes=episodes,updates=updates,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(opening)['epoch'],initialization_wall_s=read(opening)['initialization_wall_s'],recovered_boundary_error=recovery,CPU_s=time.process_time()-cpu,collect_wall_s=collectwall,update_wall_s=updatewall,GT_policy_inputs=False,DEV_screen_used=False,champion_changed=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);a.add_argument('--resume-boundary-repair',action='store_true');args=a.parse_args();train(args.plan.resolve(),args.resume_boundary_repair)
