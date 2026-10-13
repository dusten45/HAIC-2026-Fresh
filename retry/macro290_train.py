"""Categorical3action PPO,16charged-native windows; durable no-replay recovery."""
import argparse,time,datetime,json,os
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha
from retry.preview286_run import save,plain
from retry.macro290_model import RECIPE,create,vector,reward,apply

def train(path,resume=False):
 import torch
 from torch import nn
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 D=path.parent;p=read(path);assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 opening=D/'training-opening.json';assert resume==opening.exists()
 actor,critic=create();ao=torch.optim.Adam(actor.parameters(),lr=3e-4);vo=torch.optim.Adam(critic.parameters(),lr=3e-4);norm=np.load(p['normalization']);mean,std=norm['mean'],norm['std'];rng=np.random.default_rng(29001);shuffle=np.random.default_rng(29002)
 def cp_save(batch,cursor,updates):
  q=D/f'checkpoint{batch}.pt';tmp=q.with_suffix('.tmp');torch.save(dict(actor=actor.state_dict(),critic=critic.state_dict(),actor_optimizer=ao.state_dict(),critic_optimizer=vo.state_dict(),rng_state=rng.bit_generator.state,shuffle_state=shuffle.bit_generator.state,cursor=cursor,completed_batch=batch,updates=updates,recipe=RECIPE),tmp);tmp.chmod(0o600);tmp.replace(q);save(D/'state.json',dict(last_committed_batch=batch,checkpoint_sha256=sha(q),charged_training_native=read(D/'budget.json')['training']))
 def evaluate(net,x):
  with torch.no_grad():return net(torch.tensor(x,dtype=torch.float64)).numpy()
 def probabilities(x):
  logits=evaluate(actor,x);pr=np.exp(logits-logits.max());return pr/pr.sum()
 def load_decisions(F):
  q=F/'decision-journal-private.jsonl';return [json.loads(x) for x in q.read_text().splitlines()] if q.exists() else []
 episodes=[];updates=[];cursor=0;last=0;serial=0;collectwall=updatewall=0.;cpu=time.process_time()
 if resume:
  files=list(D.glob('checkpoint[0-9]*.pt'));latest=max(files,key=lambda q:int(q.stem[10:]));cp=torch.load(latest);actor.load_state_dict(cp['actor']);critic.load_state_dict(cp['critic']);ao.load_state_dict(cp['actor_optimizer']);vo.load_state_dict(cp['critic_optimizer']);rng.bit_generator.state=cp['rng_state'];shuffle.bit_generator.state=cp['shuffle_state'];cursor=cp['cursor'];last=cp['completed_batch'];updates=cp['updates']
  for F in sorted(D.glob('episode[0-9]*_*')):
   header=read(F/'header.json');serial=max(serial,header['serial']+1)
   if (F/'result.json').exists():r=read(F/'result.json')
   elif (F/'terminal-or-cut-receipt.json').exists():
    r=read(F/'terminal-or-cut-receipt.json');r['reaping']=None;save(F/'result.json',r)
   else:
    # Keep completed macrodecisions only; unfinished macro actions arecharged
    # loss, never replayed or given a fabricated commitmentbootstrap.
    decisions=load_decisions(F)
    if decisions and not decisions[-1]['done']:
     decisions[-1]['cut']=True;save(F/'recovered-decisions.json',decisions)
    r=dict(road=header['road'],batch=header['batch'],serial=header['serial'],next_cursor=header['next_cursor'],technical_interrupted=True,completed=False,actual_DNF=False,collection_cut=False,valid_decisions=len(decisions),valid_native=sum(d['duration'] for d in decisions),native_actions=None,lap_ms=None,wall_s=0.,raw_step_ticks=None,raw_reset_ticks=None)
    save(F/'result.json',r)
   episodes.append(r)
   if header['batch']>last:
    cursor=header['next_cursor'];statefile=F/'last-decision-header.json';rng.bit_generator.state=read(statefile)['rng_state'] if statefile.exists() else header['rng_state']
 else:
  save(opening,dict(epoch=time.time()));cp_save(0,0,[]);save(D/'initial-receipt.json',dict(probabilities=probabilities(np.zeros(28)).tolist(),actor_parameters=sum(x.numel() for x in actor.parameters()),critic_parameters=sum(x.numel() for x in critic.parameters()),legal_inputs=28,GT_inputs=False))
 def deadline():assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
 def collect(batch,window_end):
  nonlocal cursor,serial,collectwall
  road=RECIPE['road_order'][cursor%6];cursor+=1;F=D/f'episode{serial:03d}_{road}';episode_serial=serial;serial+=1;F.mkdir(mode=0o700);save(F/'header.json',dict(road=road,batch=batch,serial=episode_serial,next_cursor=cursor,rng_state=rng.bit_generator.state));worker=env=None;decisions=[];rows=[];steps=ticks=0;start=time.perf_counter();prevp=prevt=totalreward=0.;terminal=cut=False;complete=False;error=None;reset=0
  journal=(F/'native-journal-private.jsonl').open('x',buffering=1);os.chmod(journal.name,0o600);dj=(F/'decision-journal-private.jsonl').open('x',buffering=1);os.chmod(dj.name,0o600)
  try:
   worker=prepare(p['base'],F/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;t0=raw.t;reset=round(t0*50);worker.call('reset',obs);pending,_=worker.call('act',obs)
   while window_end-read(D/'budget.json')['training']>=3:
    deadline();x=vector(pending,mean,std);pr=probabilities(x);category=int(rng.choice(5,p=pr));value=float(evaluate(critic,x)[0]);sample=dict(x=x.tolist(),category=category,old_probs=pr.tolist(),old_logp=float(np.log(pr[category])),value=value,reward=0.,next_value=0.,duration=0,done=False,cut=False)
    save(F/'last-decision-header.json',dict(rng_state=rng.bit_generator.state,category=category,decision=len(decisions)))
    for within in range(3):
     deadline();action=apply(pending['action'],pending['features'],category);committed,_=worker.call('commit',action);assert committed['history'][-1]==action.tolist() and np.float32(committed['memory'])==action[0]
     b=read(D/'budget.json');assert b['training']<16384 and b['actions']<22884;b['training']+=1;b['actions']+=1;save(D/'budget.json',b);before=raw.t;obs,_,ended,truncated,info=env.step(action);steps+=1;ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or steps==2000);cut=not terminal and within==2 and window_end-b['training']<3
     t=raw.finish_time_s-t0 if complete else raw.t-t0;progress=raw.tile_visited_count/len(raw.track);rt=reward(progress,prevp,t,prevt,'completed' if complete else 'DNF' if terminal else None);prevp,prevt=progress,t;totalreward+=rt;sample['reward']+=rt;sample['duration']+=1;sample['done']=terminal;sample['cut']=cut
     if terminal:nv=0.;next_response=None
     else:
      next_response,_=worker.call('peek' if cut else 'act',obs)
      if cut:assert next_response['peek_state_preserved'] and next_response['state']==committed['state']
      assert next_response['history']==committed['history'];nv=float(evaluate(critic,vector(next_response,mean,std))[0])
     sample['next_value']=nv;row=dict(step=steps,decision=len(decisions),category=category,within=within,base=pending['action'],action=action.tolist(),history=committed['history'],memory=committed['state'],reward=rt,progress=progress,time_s=t,completed=complete,terminal=terminal,collection_cut=cut,rng_state=rng.bit_generator.state,macro_prefix=sample)
     journal.write(json.dumps(plain(row),allow_nan=False)+'\n');rows.append(dict(category=category,action=action.tolist()))
     if terminal or cut:break
     pending=next_response
    decisions.append(dict(sample));dj.write(json.dumps(plain(sample),allow_nan=False)+'\n')
    if terminal or cut:break
   expected=2-t/160 if complete else progress-1 if terminal else None
   if expected is not None:assert abs(totalreward-expected)<1e-9
   receipt=dict(road=road,batch=batch,serial=episode_serial,next_cursor=cursor,native_actions=steps,valid_native=sum(d['duration'] for d in decisions),valid_decisions=len(decisions),completed=complete,actual_DNF=terminal and not complete,collection_cut=cut,technical_interrupted=False,lap_ms=round(t*1000) if complete else None,retire_reason=None if complete else info.get('retire_reason') or ('collection_cut' if cut else 'max_steps'),return_sum=totalreward,expected_terminal_return=expected,damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),bootstrap_value=nv if cut else 0.,raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,actor_CPU_s=committed['actor_cumulative_CPU_s'],native_category_counts={str(c):sum(r['category']==c for r in rows) for c in range(5)},macro_category_counts={str(c):sum(d['category']==c for d in decisions) for c in range(5)})
   save(F/'terminal-or-cut-receipt.json',receipt)
  except Exception as e:
   error=type(e).__name__+': '+str(e)
   if decisions and not decisions[-1]['done']:decisions[-1]['cut']=True;save(F/'recovered-decisions.json',decisions)
   receipt=dict(road=road,batch=batch,serial=episode_serial,next_cursor=cursor,native_actions=steps,valid_native=sum(d['duration'] for d in decisions),valid_decisions=len(decisions),completed=False,actual_DNF=False,collection_cut=False,technical_interrupted=True,error=error,wall_s=time.perf_counter()-start,raw_step_ticks=ticks,raw_reset_ticks=reset)
  finally:
   journal.close();dj.close()
   if worker:reaping=worker.close()
   if env:env.close()
  receipt['reaping']=reaping if worker else None;save(F/'result.json',receipt);episodes.append(receipt);save(D/'episodes-private.json',episodes);collectwall+=receipt['wall_s']
  if error:raise RuntimeError(error)
  return decisions
 error=None
 try:
  for batch in range(last+1,17):
   windowfile=D/f'window{batch}.json'
   if windowfile.exists():window=read(windowfile)
   else:
    start_native=read(D/'budget.json')['training'];window=dict(start_native=start_native,end_native=min(start_native+1024,16384));save(windowfile,window)
   data=[]
   for ep in episodes:
    if ep['batch']==batch:
     F=D/f"episode{ep['serial']:03d}_{ep['road']}";data+=read(F/'recovered-decisions.json') if (F/'recovered-decisions.json').exists() else load_decisions(F)
   while window['end_native']-read(D/'budget.json')['training']>=3:data+=collect(batch,window['end_native'])
   assert len(data)>=2 and all(d['duration']==3 or d['done'] for d in data)
   save(D/f'rollout{batch}-private.json',data);adv=np.zeros(len(data));carry=0.
   for i in range(len(data)-1,-1,-1):
    d=data[i];delta=d['reward']+(0 if d['done'] else d['next_value'])-d['value'];carry=delta+.95*(0 if d['done'] or d['cut'] else 1)*carry;adv[i]=carry
   target=adv+np.array([d['value'] for d in data]);A=torch.tensor((adv-adv.mean())/(adv.std()+1e-8),dtype=torch.float64);X=torch.tensor([d['x'] for d in data],dtype=torch.float64);C=torch.tensor([d['category'] for d in data],dtype=torch.long);OLD=torch.tensor([d['old_probs'] for d in data],dtype=torch.float64);LP=torch.tensor([d['old_logp'] for d in data],dtype=torch.float64);RET=torch.tensor(target,dtype=torch.float64)
   with torch.no_grad():beforep=actor(X).softmax(1);beforev=critic(X).squeeze(1);assert torch.max(abs(beforep-OLD)).item()<1e-12
   tick=time.perf_counter();steps=0;maxkl=0.;stopped=False;agmax=vgmax=0.
   for epoch in range(4):
    for idx in np.array_split(shuffle.permutation(len(data)),int(np.ceil(len(data)/64))):
     deadline();logprobs=actor(X[idx]).log_softmax(1);kl=(OLD[idx]*(OLD[idx].log()-logprobs)).sum(1).mean();maxkl=max(maxkl,float(kl))
     if float(kl)>.01:stopped=True;break
     lp=logprobs.gather(1,C[idx,None]).squeeze(1);ratio=(lp-LP[idx]).exp();loss=-torch.minimum(ratio*A[idx],ratio.clamp(.9,1.1)*A[idx]).mean();vloss=.5*(critic(X[idx]).squeeze(1)-RET[idx]).pow(2).mean();assert torch.isfinite(loss) and torch.isfinite(vloss)
     ao.zero_grad();loss.backward();ag=float(nn.utils.clip_grad_norm_(actor.parameters(),.5));ao.step();vo.zero_grad();vloss.backward();vg=float(nn.utils.clip_grad_norm_(critic.parameters(),.5));vo.step();agmax=max(agmax,ag);vgmax=max(vgmax,vg);steps+=1
    if stopped:break
   with torch.no_grad():afterp=actor(X).softmax(1);afterv=critic(X).squeeze(1)
   change=float((afterp-beforep).pow(2).mean().sqrt());assert steps>0 and agmax>0 and vgmax>0 and change>0;assert all(torch.isfinite(t).all() for t in list(actor.parameters())+list(critic.parameters()))
   wall=time.perf_counter()-tick;updatewall+=wall;u=dict(batch=batch,macro_decisions=len(data),valid_native=sum(d['duration'] for d in data),charged_window_native=read(D/'budget.json')['training']-window['start_native'],unused_native_allowance=window['end_native']-read(D/'budget.json')['training'],optimizer_steps=steps,epochs_completed=epoch if stopped else epoch+1,target_KL_stop=stopped,max_checked_KL=maxkl,full_KL=float((OLD*(OLD.log()-afterp.log())).sum(1).mean()),probability_RMS_change=change,actor_gradient_norm_max=agmax,critic_gradient_norm_max=vgmax,value_MSE_before=float((beforev-RET).pow(2).mean()),value_MSE_after=float((afterv-RET).pow(2).mean()),mean_probabilities=afterp.mean(0).tolist(),sampled_macro_counts={str(c):sum(d['category']==c for d in data) for c in range(5)},wall_s=wall)
   updates.append(u);save(D/'updates-private.json',updates);cp_save(batch,cursor,updates);save(D/'progress-private.json',dict(update=batch,training_native=read(D/'budget.json')['training'],macro_decisions=sum(u['macro_decisions'] for u in updates),complete=sum(e['completed'] for e in episodes),DNF=sum(e['actual_DNF'] for e in episodes),cuts=sum(e['collection_cut'] for e in episodes),elapsed_s=time.time()-read(opening)['epoch']));print(str(read(D/'progress-private.json')),flush=True)
  params={f'actor_{k}':v.detach().numpy() for k,v in actor.state_dict().items()};q=D/'final-actor-private.npz';np.savez(q,**params,mean=mean,std=std);q.chmod(0o600)
 except Exception as e:error=type(e).__name__+': '+str(e);save(D/'technical-error.json',dict(error=error,budget=read(D/'budget.json')))
 save(D/'training-outcome-private.json',dict(stage=290,technical_error=error,episodes=episodes,updates=updates,budget=read(D/'budget.json'),phase_CPU_s=time.process_time()-cpu,phase_collect_wall_s=collectwall,phase_update_wall_s=updatewall,wall_s=time.time()-read(opening)['epoch'],no_screen_performance_access=True,GT_policy_inputs=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);a.add_argument('--resume',action='store_true');args=a.parse_args();train(args.plan.resolve(),args.resume)
