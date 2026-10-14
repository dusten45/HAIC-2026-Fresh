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
    from retry.asym317_model import create as matched_create,inputs,charge
    actor,critic=matched_create();ao=torch.optim.Adam(actor.parameters(),lr=RECIPE['actor_lr']);vo=torch.optim.Adam(critic.parameters(),lr=RECIPE['critic_lr'])
    normalization=np.load(p['normalization']);mean,std=normalization['mean'],normalization['std']
    noise=np.random.default_rng(p['noise_seed']);shuffle=np.random.default_rng(p['shuffle_seed'])
    assert not resume and not opening.exists(),'Existing execution must be inspected; no automatic replay'
    cursor=0;serial=0;start_batch=1;end_batch=8;episodes=[];updates=[]
    save(opening,dict(epoch=time.time(),initialization_wall_s=time.perf_counter()-allstart))
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
            obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;start_t=raw.t;resetticks=round(start_t*50);initial_progress=raw.tile_visited_count/len(raw.track)
            assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road]
            response,_=worker.call('reset',obs);assert response['history']==[]
            pending,ipc=worker.call('act',obs);calls+=1
            for step in range(1,cap+1):
                deadline();tick=time.perf_counter();assert not pending['python_audit_denied_events']
                x=vector(pending,mean,std);mu=evaluate(actor,x);critic_x,offset=inputs(x,raw.tile_visited_count/len(raw.track),env.damage.damage,(raw.t-start_t)/160,p['arm'])
                sv=float(evaluate(critic,critic_x)[0]);v=sv-offset;z=mu+STD*noise.normal(size=3)
                oldlp=float(logp(z,mu));action=apply(pending['action'],z)
                committed,commit_ipc=worker.call('commit',action);calls+=1;assert committed['history'][-1]==action.tolist()
                assert np.float32(committed['memory'])==action[0]
                extra_ms=(time.perf_counter()-tick)*1000;timings.append(ipc+extra_ms)
                charge(p['stage_root'],p['arm'],'training')
                before=raw.t;obs,_,ended,truncated,info=env.step(action);rawticks+=round((raw.t-before)*50)
                complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000);cut=not terminal and step==cap
                t=raw.finish_time_s-start_t if complete else raw.t-start_t;progress=raw.tile_visited_count/len(raw.track)
                rt=reward(progress,previous_p,t,previous_t,'completed' if complete else 'DNF' if terminal else None);elapsed_return+=rt;previous_p=progress;previous_t=t
                if terminal:nv=0.;nsv=0.;next_offset=0.;next_response=None
                else:
                    op='peek' if cut else 'act';next_response,next_ipc=worker.call(op,obs);calls+=1
                    assert not next_response['python_audit_denied_events']
                    if cut:assert next_response['peek_state_preserved'] and next_response['state']==committed['state'];peeks+=1
                    else:assert next_response['features'][7]==committed['memory']
                    assert next_response['history']==committed['history']
                    next_x=vector(next_response,mean,std)
                    next_critic_x,next_offset=inputs(next_x,progress,env.damage.damage,(raw.t-start_t)/160,p['arm'])
                    nsv=float(evaluate(critic,next_critic_x)[0]);nv=nsv-next_offset
                    assert abs(nv-(nsv-next_offset))<1e-12
                if not terminal:assert abs((raw.t-before)-.08)<1e-9
                expected_delta=rt+(0. if terminal else nsv-next_offset)-(sv-offset)
                assert abs(expected_delta-(rt+(1-float(terminal))*nv-v))<1e-12
                buffer.append(dict(x=x,critic_x=critic_x,offset=offset,S_value=sv,next_S_value=nsv,next_offset=next_offset,latent=z,old_mu=mu,old_logp=oldlp,reward=rt,value=v,next_value=nv,done=terminal,cut=cut,base=np.array(pending['action'],np.float32),executed=action))
                rows.append(dict(step=step,features=pending['features'],history=pending['history'],action=action.tolist(),committed_memory=committed['memory'],history_after=committed['history'],pre_privileged=critic_x[28:].tolist(),pre_offset=offset,next_offset=next_offset,reward=rt,damage=env.damage.damage,visited=raw.tile_visited_count,terminal=terminal,collection_cut=cut,full_policy_ms=timings[-1]))
                journal.write(json.dumps(dict(buffer={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in buffer[-1].items()},noise_state=noise.bit_generator.state,row=rows[-1]))+'\n')
                if terminal or cut:break
                pending,ipc=next_response,next_ipc
            expected=2-t/160 if complete else progress-1 if terminal else None
            if expected is not None:
                assert abs(elapsed_return-expected)<1e-9
                suffix=np.cumsum(np.array([b['reward'] for b in buffer])[::-1])[::-1]
                s_target=suffix+np.array([b['offset'] for b in buffer])
                expected_s=np.full(len(buffer),expected);expected_s[0]+=initial_progress
                assert np.max(abs(s_target-expected_s))<1e-9
            r=dict(road=road,batch=batch,serial=episode_serial,valid_samples=len(buffer),next_cursor=cursor,noise_state=noise.bit_generator.state,technical_interrupted=False,native_actions=step,completed=complete,actual_DNF=terminal and not complete,collection_cut=cut,
                lap_ms=round(t*1000) if complete else None,return_sum=elapsed_return,expected_terminal_return=expected,
                retire_reason=None if complete else info.get('retire_reason') or ('collection_cut' if cut else 'max_steps'),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),
                bootstrap_value=nv if cut else 0.,raw_step_ticks=rawticks,raw_reset_ticks=resetticks,worker_calls=calls,unexecuted_pure_peek_calls=peeks,
                actor_CPU_s=committed['actor_cumulative_CPU_s'] if terminal else next_response['actor_cumulative_CPU_s'],wall_s=time.perf_counter()-start,
                full_policy_ms=dict(median=float(np.median(timings)),p95=float(np.percentile(timings,95)),max=float(max(timings))),pixel_only=True,GT_policy_inputs=False,critic_privileged_inputs=p['arm']=='C',current_offset_common=True,accounting_checks=len(buffer),reset_progress_known=initial_progress)
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
            if batch==1:
                root=Path(p['stage_root']);save(D/'first-rollout-ready.json',dict(sha256=sha(q)))
                other=root/('C' if p['arm']=='B' else 'B')
                while not (other/'first-rollout-ready.json').exists():
                    deadline();assert not (other/'technical-error.json').exists(),'Other arm failed before matched gate';time.sleep(.2)
                if p['arm']=='B':
                    qb=root/'B/rollout1-private.npz';qc=root/'C/rollout1-private.npz'
                    assert sha(qb)==read(root/'B/first-rollout-ready.json')['sha256']
                    assert sha(qc)==read(root/'C/first-rollout-ready.json')['sha256']
                    bb=dict(np.load(qb));cc=dict(np.load(qc))
                    keys=['x','latent','old_mu','old_logp','reward','value','next_value','offset','next_offset','S_value','next_S_value','done','cut','base','executed']
                    exact={k:bool(np.array_equal(bb[k],cc[k])) for k in keys}
                    assert all(exact.values()),exact
                    assert np.all(bb['critic_x'][:,28:]==0)
                    assert np.array_equal(bb['critic_x'][:,:28],cc['critic_x'][:,:28])
                    save(root/'first-rollout-verified.json',dict(passed=True,samples=1024,equal_arrays=exact,extra_inputs_differ_but_initial_weights_zero=True))
                else:
                    while not (root/'first-rollout-verified.json').exists():
                        deadline();assert not (other/'technical-error.json').exists(),'Other arm failed before matched gate';time.sleep(.2)
                    assert read(root/'first-rollout-verified.json')['passed']
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
            X=torch.as_tensor(data['x'],dtype=torch.float64);CX=torch.as_tensor(data['critic_x'],dtype=torch.float64);OFFSET=torch.as_tensor(data['offset'],dtype=torch.float64);Z=torch.as_tensor(data['latent'],dtype=torch.float64);OLD=torch.as_tensor(data['old_mu'],dtype=torch.float64);LP=torch.as_tensor(data['old_logp'],dtype=torch.float64);A=torch.as_tensor(normal,dtype=torch.float64);RET=torch.as_tensor(target+data['offset'],dtype=torch.float64)
            with torch.no_grad():before_mu=actor(X).clone();before_v=(critic(CX).squeeze(1)-OFFSET).clone()
            assert torch.max(torch.abs(before_mu-OLD)).item()<1e-12
            tick=time.perf_counter();steps=0;maxkl=0.;stopped=False;actor_grad=[];critic_grad=[];clipfractions=[]
            for epoch in range(RECIPE['epochs']):
                for idx in np.array_split(shuffle.permutation(len(X)),len(X)//RECIPE['minibatch']):
                    deadline();m=actor(X[idx]);kl=((m-OLD[idx])**2).sum(1).mean()/(2*STD**2);maxkl=max(maxkl,float(kl.item()))
                    if kl.item()>RECIPE['target_KL']:stopped=True;break
                    lp=-.5*((Z[idx]-m)/STD).pow(2).sum(1)-3*np.log(STD)-1.5*np.log(2*np.pi);ratio=(lp-LP[idx]).exp()
                    assert torch.isfinite(ratio).all();clipfractions.append(float(((ratio<.9)|(ratio>1.1)).double().mean().item()))
                    loss=-torch.minimum(ratio*A[idx],ratio.clamp(.9,1.1)*A[idx]).mean();vloss=(critic(CX[idx]).squeeze(1)-RET[idx]).pow(2).mean()
                    assert torch.isfinite(loss) and torch.isfinite(vloss)
                    ao.zero_grad();loss.backward();ag=float(nn.utils.clip_grad_norm_(actor.parameters(),.5));assert np.isfinite(ag);ao.step();actor_grad.append(ag)
                    vo.zero_grad();(.5*vloss).backward();vg=float(nn.utils.clip_grad_norm_(critic.parameters(),.5));assert np.isfinite(vg);vo.step();critic_grad.append(vg);steps+=1
                if stopped:break
            wall=time.perf_counter()-tick;updatewall+=wall
            with torch.no_grad():after_mu=actor(X);after_v=critic(CX).squeeze(1)-OFFSET
            assert all(torch.isfinite(v).all() for v in list(actor.parameters())+list(critic.parameters()))
            update=dict(batch=batch,native_training=batch*RECIPE['rollout'],optimizer_minibatch_steps=steps,epochs_completed=epoch if stopped else epoch+1,target_KL_stop=stopped,
                max_checked_analytic_KL=maxkl,final_full_batch_KL=float(((after_mu-OLD)**2).sum(1).mean().item()/(2*STD**2)),actor_gradient_norm_max=max(actor_grad,default=0.),critic_gradient_norm_max=max(critic_grad,default=0.),
                actor_mu_change_RMS=float(((after_mu-before_mu)**2).mean().sqrt().item()),actor_mu_abs_max=float(after_mu.abs().max().item()),
                value_MSE_before=float(((before_v-(RET-OFFSET))**2).mean().item()),value_MSE_after=float(((after_v-(RET-OFFSET))**2).mean().item()),ratio_clip_fraction_mean=float(np.mean(clipfractions)) if clipfractions else None,wall_s=wall)
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
    save(D/'training-outcome-private.json',dict(stage=317,arm=p['arm'],GAE_lambda=p['GAE_lambda'],episodes=episodes,updates=updates,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(opening)['epoch'],initialization_wall_s=read(opening)['initialization_wall_s'],CPU_s=time.process_time()-cpu,collect_wall_s=collectwall,update_wall_s=updatewall,GT_policy_inputs=False,GT_critic_inputs=p['arm']=='C',common_current_offset=True,DEV_screen_used=False,champion_changed=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);a.add_argument('--resume',action='store_true');args=a.parse_args();train(args.plan.resolve(),args.resume)
