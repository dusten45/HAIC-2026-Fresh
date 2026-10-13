"""Paired8update joint PPO: only GAE lambda differs, common fresh seeds."""
import argparse,time,datetime,hashlib,json,os,traceback
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.ppo275_model import RECIPE,STD,create,vector,logp,apply,reward

def train(path,resume=False):
    allstart=time.perf_counter()
    import torch
    from torch import nn
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=path.parent;p=read(path)
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(Path(q))==h
    opening=D/'training-opening.json'
    assert resume==opening.exists(),'Use resume only for a started training run'
    actor,critic=create();ao=torch.optim.Adam(actor.parameters(),lr=RECIPE['actor_lr']);vo=torch.optim.Adam(critic.parameters(),lr=RECIPE['critic_lr'])
    normalization=np.load(p['normalization']);mean,std=normalization['mean'],normalization['std']
    noise=np.random.default_rng(p['noise_seed']);shuffle=np.random.default_rng(p['shuffle_seed'])
    checkpoints=list(D.glob('checkpoint[0-9]*.pt'))
    latest=max(checkpoints,key=lambda q:int(q.stem[10:])) if checkpoints else Path(p['initial_checkpoint'])
    checkpoint=torch.load(latest)
    actor.load_state_dict(checkpoint['actor']);critic.load_state_dict(checkpoint['critic']);ao.load_state_dict(checkpoint['actor_optimizer']);vo.load_state_dict(checkpoint['critic_optimizer'])
    for k,v in actor.state_dict().items():assert torch.equal(v,checkpoint['actor'][k])
    for k,v in critic.state_dict().items():assert torch.equal(v,checkpoint['critic'][k])
    for loaded,saved in [(ao.state_dict(),checkpoint['actor_optimizer']),(vo.state_dict(),checkpoint['critic_optimizer'])]:
        assert loaded['param_groups']==saved['param_groups']
        for key,state in saved['state'].items():
            for name,value in state.items():
                if torch.is_tensor(value):assert torch.equal(loaded['state'][key][name],value)
                else:assert loaded['state'][key][name]==value
    if checkpoints:
        noise.bit_generator.state=checkpoint['noise_state'];shuffle.bit_generator.state=checkpoint['shuffle_state']
    cursor=checkpoint['cursor']
    last_batch=checkpoint.get('completed_batch',2);start_batch=last_batch+1;end_batch=10
    updates=checkpoint.get('updates',read(Path(p['initial_updates'])))
    episodes=[]
    for folder in sorted(D.glob('episode[0-9]*_*')):
        if (folder/'result.json').exists():episodes.append(read(folder/'result.json'))
        elif resume:
            # An abruptly interrupted process never replays its physics prefix.
            header=read(folder/'episode-header.json');entries=[]
            if (folder/'step-journal-private.jsonl').exists():
                for line in (folder/'step-journal-private.jsonl').read_text().splitlines():
                    try:entries.append(json.loads(line))
                    except json.JSONDecodeError:break
            if entries:
                data={k:np.array([e['buffer'][k] for e in entries]) for k in entries[0]['buffer']}
                data['cut'][-1]=True
                q=folder/'buffer-private.npz';np.savez_compressed(q,**data);q.chmod(0o600)
                rng_state=entries[-1]['noise_state']
            else:rng_state=header['noise_state']
            r=dict(road=header['road'],batch=header['batch'],serial=header['serial'],valid_samples=len(entries),
                technical_interrupted=True,technical_error='prior_process_interruption',completed=False,actual_DNF=False,collection_cut=False,
                next_cursor=header['next_cursor'],noise_state=rng_state,native_actions=None,lap_ms=None)
            save(folder/'result.json',r);episodes.append(r)
    # Restore sampling after durable episodes beyond the last optimizer transaction.
    pending_episodes=[e for e in episodes if e['batch']>last_batch]
    if pending_episodes:
        last=max(pending_episodes,key=lambda e:e['serial']);noise.bit_generator.state=last['noise_state'];cursor=last['next_cursor']
    serial=max([e['serial'] for e in episodes],default=-1)+1
    if not opening.exists():
        save(opening,dict(epoch=time.time(),initialization_wall_s=time.perf_counter()-allstart))
        save(D/'continuity-receipt.json',dict(source_checkpoint_sha256=sha(latest),initial_valid_samples=2048,
            starting_actor_optimizer_steps=[int(v['step']) for v in ao.state_dict()['state'].values()],
            starting_critic_optimizer_steps=[int(v['step']) for v in vo.state_dict()['state'].values()],
            model_and_optimizer_tensors_exact=True,common_noise_seed=p['noise_seed'],common_shuffle_seed=p['shuffle_seed'],starting_road_cursor=cursor,only_lambda_differs=p['GAE_lambda']))
    error=None;cpu=time.process_time();collectwall=0.;updatewall=0.
    def deadline():assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
    def evaluate(net,x):
        with torch.no_grad():return net(torch.as_tensor(x,dtype=torch.float64)).numpy().copy()
    def episode(batch,cap):
        nonlocal cursor,collectwall,serial
        deadline()
        road=RECIPE['road_order'][cursor%6];cursor+=1;episode_serial=serial;folder=D/f'episode{serial:03d}_{road}';serial+=1;folder.mkdir(mode=0o700)
        save(folder/'episode-header.json',dict(road=road,batch=batch,serial=episode_serial,next_cursor=cursor,noise_state=noise.bit_generator.state))
        env=worker=None;buffer=[];rows=[];rawticks=0;calls=0;peeks=0;start=time.perf_counter();elapsed_return=0.;previous_p=previous_t=0.;timings=[];episode_error=None;resetticks=0;reaping=None
        journal=(folder/'step-journal-private.jsonl').open('x',buffering=1);os.chmod(journal.name,0o600)
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
                budget=read(D/'budget.json');assert budget['actions']<p['native_cap'];budget['actions']+=1;budget['training']+=1;save(D/'budget.json',budget)
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
                journal.write(json.dumps(dict(buffer={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in buffer[-1].items()},noise_state=noise.bit_generator.state,row=rows[-1]))+'\n')
                if terminal or cut:break
                pending,ipc=next_response,next_ipc
            expected=2-t/160 if complete else progress-1 if terminal else None
            if expected is not None:assert abs(elapsed_return-expected)<1e-9
            r=dict(road=road,batch=batch,serial=episode_serial,valid_samples=len(buffer),next_cursor=cursor,noise_state=noise.bit_generator.state,technical_interrupted=False,native_actions=step,completed=complete,actual_DNF=terminal and not complete,collection_cut=cut,
                lap_ms=round(t*1000) if complete else None,return_sum=elapsed_return,expected_terminal_return=expected,
                retire_reason=None if complete else info.get('retire_reason') or ('collection_cut' if cut else 'max_steps'),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),
                bootstrap_value=nv if cut else 0.,raw_step_ticks=rawticks,raw_reset_ticks=resetticks,worker_calls=calls,unexecuted_pure_peek_calls=peeks,
                actor_CPU_s=committed['actor_cumulative_CPU_s'] if terminal else next_response['actor_cumulative_CPU_s'],wall_s=time.perf_counter()-start,
                full_policy_ms=dict(median=float(np.median(timings)),p95=float(np.percentile(timings,95)),max=float(max(timings))),pixel_only=True,GT_policy_inputs=False)
        except Exception as e:
            episode_error=type(e).__name__+': '+str(e)
            if buffer:buffer[-1]['cut']=True
            r=dict(road=road,batch=batch,serial=episode_serial,valid_samples=len(buffer),next_cursor=cursor,noise_state=noise.bit_generator.state,
                technical_interrupted=True,technical_error=episode_error,completed=False,actual_DNF=False,collection_cut=False,
                native_actions=None,lap_ms=None,wall_s=time.perf_counter()-start,raw_step_ticks=rawticks,raw_reset_ticks=resetticks if env else 0)
        finally:
            journal.close()
            if worker:reaping=worker.close()
            if env:env.close()
        r['reaping']=reaping if worker else None;collectwall+=r['wall_s'];save(folder/'result.json',r);save(folder/'trajectory-private.json',rows)
        q=folder/'buffer-private.npz'
        if buffer:np.savez_compressed(q,**{k:np.array([b[k] for b in buffer]) for k in buffer[0]});q.chmod(0o600)
        episodes.append(r);save(D/'episodes-private.json',episodes)
        if episode_error:raise RuntimeError(episode_error)
        return buffer
    try:
        for batch in range(start_batch,end_batch+1):
            collected=[]
            for ep in episodes:
                if ep['batch']==batch and ep['valid_samples']:
                    folder=D/f"episode{ep['serial']:03d}_{ep['road']}";cached=dict(np.load(folder/'buffer-private.npz'))
                    collected.extend({k:cached[k][i] for k in cached} for i in range(len(cached['reward'])))
            while len(collected)<RECIPE['rollout']:collected+=episode(batch,min(2000,RECIPE['rollout']-len(collected)))
            data={k:np.array([b[k] for b in collected]) for k in collected[0]};q=D/f'rollout{batch}-private.npz';np.savez_compressed(q,**data);q.chmod(0o600)
            # LatentGaussian likelihood; never infer likelihood from clippedactions.
            assert np.max(abs(logp(data['latent'],data['old_mu'])-data['old_logp']))<1e-12
            adv=np.zeros(len(collected));carry=0.
            for i in range(len(collected)-1,-1,-1):
                terminal=float(data['done'][i]);delta=data['reward'][i]+(1-terminal)*data['next_value'][i]-data['value'][i]
                carry=delta+p['GAE_lambda']*(0. if data['cut'][i] else 1-terminal)*carry;adv[i]=carry
            observed_mc=np.full(len(collected),np.nan);offset=0
            for ep in sorted([e for e in episodes if e['batch']==batch],key=lambda e:e['serial']):
                n=ep['valid_samples']
                if ep['completed'] or ep['actual_DNF']:observed_mc[offset:offset+n]=np.cumsum(data['reward'][offset:offset+n][::-1])[::-1]
                offset+=n
            assert offset==len(collected)
            target=adv+data['value']
            if p['GAE_lambda']==1.:
                m=np.isfinite(observed_mc);assert np.max(abs(target[m]-observed_mc[m]))<1e-10
            normal=(adv-adv.mean())/(adv.std()+1e-8)
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
            terminal_mask=np.isfinite(observed_mc)
            for name,v in [('before',before_v.numpy()),('after',after_v.numpy())]:
                prediction_error=v[terminal_mask]-observed_mc[terminal_mask]
                update['observed_terminal_MC_RMSE_'+name]=float(np.sqrt(np.mean(prediction_error**2)))
                update['observed_terminal_MC_bias_'+name]=float(np.mean(prediction_error))
            update['observed_terminal_samples']=int(terminal_mask.sum());update['GAE_lambda']=p['GAE_lambda']
            updates.append(update);save(D/'updates-private.json',updates)
            q=D/f'checkpoint{batch}.pt';tmp=q.with_suffix('.tmp');torch.save(dict(actor=actor.state_dict(),critic=critic.state_dict(),actor_optimizer=ao.state_dict(),critic_optimizer=vo.state_dict(),noise_state=noise.bit_generator.state,shuffle_state=shuffle.bit_generator.state,cursor=cursor,recipe=RECIPE,completed_batch=batch,updates=updates),tmp);tmp.chmod(0o600);tmp.replace(q)
            save(D/'state.json',dict(last_committed_batch=batch,checkpoint=str(q),checkpoint_sha256=sha(q),valid_training_total=batch*1024))
            progress=dict(arm=p['arm'],GAE_lambda=p['GAE_lambda'],update=batch,valid_total=batch*1024,new_native=read(D/'budget.json')['training'],
                train_complete=sum(e['completed'] for e in episodes),train_DNF=sum(e['actual_DNF'] for e in episodes),train_cuts=sum(e['collection_cut'] for e in episodes),
                optimizer_steps=steps,KL=update['final_full_batch_KL'],elapsed_s=time.time()-read(opening)['epoch'])
            save(D/'progress-private.json',progress);print(str(progress),flush=True)
        params={f'actor_{k}':v.detach().numpy() for k,v in actor.state_dict().items()};q=D/'final-actor-private.npz';np.savez(q,**params,mean=mean,std=std);q.chmod(0o600)
    except Exception as e:error=type(e).__name__+': '+str(e);save(D/'technical-error.json',dict(error=error,consumed=read(D/'budget.json')))
    save(D/'training-outcome-private.json',dict(stage=278,arm=p['arm'],GAE_lambda=p['GAE_lambda'],episodes=episodes,updates=updates,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(opening)['epoch'],initialization_wall_s=read(opening)['initialization_wall_s'],CPU_s=time.process_time()-cpu,collect_wall_s=collectwall,update_wall_s=updatewall,GT_policy_inputs=False,DEV_screen_used=False,champion_changed=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);a.add_argument('--resume',action='store_true');args=a.parse_args();train(args.plan.resolve(),args.resume)
