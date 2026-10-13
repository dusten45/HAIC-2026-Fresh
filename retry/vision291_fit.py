"""Onefixed capacitymatched pixelaugmented vs28 predictor, wholeN2heldout."""
import argparse,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha
from retry.preview286_run import save

def run(R):
 import torch
 from torch import nn
 torch.set_num_threads(1);D=R/'stage291';p=read(D/'plan.json');out=read(D/'collection-outcome-private.json');assert out['technical_error'] is None;assert not (D/'prediction-private.json').exists();start=time.perf_counter();cpu=time.process_time();X=[];images=[];Y=[];ids=[];iscomplete=[];meta=[]
 for ep in out['results']:
  if ep['censored']:continue
  F=D/(ep['road']+'_'+ep['behavior']);z=np.load(F/'observations-private.npz');assert bool(z['actual_terminal']);n=len(z['rewards']);indices=np.unique(np.r_[np.arange(0,n,3),n-1]);target=np.cumsum(z['rewards'][::-1])[::-1];eid=len(meta);meta.append(dict(road=ep['road'],behavior=ep['behavior'],completed=ep['completed'],rows=len(indices),native_actions=n))
  X.extend(z['features'][indices]);I=(z['pixels'][indices].astype(np.float32)/255).reshape(len(indices),4,42,2,42,2).mean(axis=(3,5));images.extend(I);Y.extend(target[indices]);ids.extend([eid]*len(indices));iscomplete.extend([ep['completed']]*len(indices))
 X=np.array(X,np.float32);I=np.array(images,np.float32);Y=np.array(Y,np.float32);ids=np.array(ids);C=np.array(iscomplete,bool);roads=np.array([meta[i]['road'] for i in ids]);train=roads!='N2';test=~train;trainids=np.unique(ids[train]);testids=np.unique(ids[test]);assert len(trainids)>=6 and len(testids)>=2 and len(set(C[test]))==2
 weights=np.array([1/meta[i]['rows'] for i in ids],np.float64);w=weights[train]/weights[train].sum();mean=(X[train]*w[:,None]).sum(0);std=np.sqrt(((X[train]-mean)**2*w[:,None]).sum(0));std=np.where(std<1e-6,1.,std);X=(X-mean)/std
 class Feature(nn.Module):
  def __init__(self):super().__init__();self.net=nn.Sequential(nn.Linear(28,150),nn.ReLU(),nn.Linear(150,1))
  def forward(self,x,image):return self.net(x).squeeze(1)
 class Visual(nn.Module):
  def __init__(self):
   super().__init__();self.conv=nn.Sequential(nn.Conv2d(4,8,3,stride=2),nn.ReLU(),nn.Conv2d(8,16,3,stride=2),nn.ReLU(),nn.AdaptiveAvgPool2d((2,2)));self.head=nn.Sequential(nn.Linear(92,32),nn.ReLU(),nn.Linear(32,1))
  def forward(self,x,image):return self.head(torch.cat([x,self.conv(image).flatten(1)],1)).squeeze(1)
 XT=torch.tensor(X,dtype=torch.float32);IT=torch.tensor((I-.5)*2,dtype=torch.float32);YT=torch.tensor(Y);WT=torch.tensor(weights*train.sum()/len(trainids),dtype=torch.float32);trainidx=np.flatnonzero(train);models={};preds={};receipts={}
 for name,cls in [('feature28',Feature),('pixel_plus28',Visual)]:
  torch.manual_seed(291);net=cls();optimizer=torch.optim.Adam(net.parameters(),lr=.001);shuffle=np.random.default_rng(29109);tick=time.perf_counter();cpus=time.process_time();steps=0
  for epoch in range(20):
   net.train()
   for idx in np.array_split(shuffle.permutation(trainidx),int(np.ceil(len(trainidx)/64))):
    prediction=net(XT[idx],IT[idx]);loss=((prediction-YT[idx]).pow(2)*WT[idx]).mean();assert torch.isfinite(loss);optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(net.parameters(),1.);optimizer.step();steps+=1
  net.eval()
  with torch.no_grad():pred=net(XT,IT).numpy()
  assert np.isfinite(pred).all();modelpath=D/(name+'-private.pt');torch.save(net.state_dict(),modelpath);modelpath.chmod(0o600);models[name]=net;preds[name]=pred;receipts[name]=dict(parameters=sum(v.numel() for v in net.parameters()),epochs=20,optimizer_steps=steps,wall_s=time.perf_counter()-tick,CPU_s=time.process_time()-cpus)
 def metrics(pred,mask):
  episodes=[]
  for eid in np.unique(ids[mask]):
   sel=mask&(ids==eid);err=pred[sel]-Y[sel];episodes.append(dict(meta[eid],RMSE=float(np.sqrt(np.mean(err**2))),MAE=float(np.mean(abs(err))),bias=float(err.mean()),mean_prediction=float(pred[sel].mean()),mean_target=float(Y[sel].mean()),completion_sign_accuracy=float(np.mean((pred[sel]>0)==C[sel]))))
  mse=np.mean([r['RMSE']**2 for r in episodes]);return dict(episode_balanced_RMSE=float(np.sqrt(mse)),episode_balanced_MAE=float(np.mean([r['MAE'] for r in episodes])),episode_balanced_bias=float(np.mean([r['bias'] for r in episodes])),completion_sign_accuracy_episode_balanced=float(np.mean([r['completion_sign_accuracy'] for r in episodes])),episode_count=len(episodes),sample_rows=int(mask.sum()),episodes=episodes)
 metrics_all={name:dict(fit=metrics(pred,train),heldout_N2=metrics(pred,test),fit_receipt=receipts[name]) for name,pred in preds.items()};a=metrics_all['feature28']['heldout_N2']['episode_balanced_RMSE'];b=metrics_all['pixel_plus28']['heldout_N2']['episode_balanced_RMSE'];summary=dict(stage=291,source_pixels='Newactualsameexecution observations, no276/290pixelsavailable, no feature/hash inversion',fit_roads=p['fit_roads'],heldout_road='N2',eligible_episodes=meta,fit_episodes=len(trainids),test_episodes=len(testids),fit_complete=int(sum(meta[i]['completed'] for i in trainids)),fit_DNF=int(sum(not meta[i]['completed'] for i in trainids)),test_complete=int(sum(meta[i]['completed'] for i in testids)),test_DNF=int(sum(not meta[i]['completed'] for i in testids)),sampling='preaction everythird pluslast, fullobservedterminal only',target='Realizednative suffix reward return underrecordedmixed240/frozen290behavior',models=metrics_all,heldout_pixel_RMSE_relative_improvement=(a-b)/a,fit_normalization_only=True,episode_frames_never_mixed_fit_test=True,road_policy_GT_futureframes_excluded_from_inputs=True,analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,limitations=['Onlyoneheldroad/twoterminalepisodes; noframeindependence orsignificance claim','Bothmodels same28inputs, nearlymatchedparameters but differentarchitecture; gain cannotisolate architecture fromadditionalpixels exactly','Twofixedbehaviors, hiddenfuturemacro/RNG commitment creates irreduciblerealizedreturn uncertainty; no behaviorIDinput','Behavior policies previouslyusedall6TRAINroads; heldroad is predictorfit exclusion, not freshcompetition generalization'],decision='Smallpositiveheldroad pixelaugmentation evidence; uncertainfromtwoepisodes, no largepixelPPO authorized orstarted.' if b<a else 'Noheldroad RMSEgain fromthisfixedvisual predictor; smallsample/model uncertainty remains, no largepixelPPO.')
 save(D/'prediction-private.json',dict(predictions={k:v.tolist() for k,v in preds.items()},targets=Y.tolist(),episode_ids=ids.tolist(),normalization_mean=mean.tolist(),normalization_std=std.tolist()));save(D/'fit-summary.json',summary);print(str({k:summary[k] for k in ['fit_episodes','test_episodes','heldout_pixel_RMSE_relative_improvement','decision','analysis_wall_s']}),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
