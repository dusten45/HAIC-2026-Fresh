"""Fixed H1 speed argmin over bounded final pedals; no state or parameter fitting."""
import numpy as np

NAMES=['baseline','gas_up','gas_down','brake_up','brake_down']


def candidates(base):
    base=np.asarray(base,np.float32);out=[base.copy()];names=['baseline']
    for name,channel,delta in [('gas_up',1,.03),('gas_down',1,-.03),('brake_up',2,.02),('brake_down',2,-.02)]:
        a=base.copy();a[channel]=np.float32(np.clip(float(a[channel])+delta,0.,1.))
        if not any(np.array_equal(a,b) for b in out):out.append(a);names.append(name)
    return names,out


def choose(base,features,state,model,enabled):
    base=np.asarray(base,np.float32).copy();audit=dict(enabled=bool(enabled),changed=False,reason='disabled',base=base.tolist(),action=base.tolist(),q=None,
        baseline_next_speed=None,chosen_next_speed=None,baseline_error=None,chosen_error=None,selected_name='baseline',selected_supported=False,candidates=[])
    if not enabled:return base,audit
    f=np.asarray(features,float)
    if len(f)!=16 or bool(f[0]) or not np.isfinite([f[2],f[6]]).all() or f[2]<=0 or f[6]<0:
        audit['reason']='absent_or_invalid_target';return base,audit
    q=float(f[6]);audit['q']=q
    if state is None or not np.isfinite(state).all():audit['reason']='invalid_current_HUD';return base,audit
    state=np.asarray(state,float);current=np.r_[state,base]
    if np.any(current<model['low']) or np.any(current>model['high']):audit['reason']='base_input_outside_support';return base,audit
    names,actions=candidates(base);valid=[]
    for index,(name,a) in enumerate(zip(names,actions)):
        x=np.r_[state,a];supported=bool(np.all(x>=model['low']) and np.all(x<=model['high']))
        prediction=float(state[0]+(np.r_[(x-model['mean'])/model['scale'],1.]@model['beta'])[0]) if supported else None
        error=abs(prediction-q) if prediction is not None and np.isfinite(prediction) else None
        audit['candidates'].append(dict(name=name,action=a.tolist(),supported=supported,next_speed=prediction,error=error))
        if error is not None:valid.append((index,error,prediction))
    if not valid or valid[0][0]!=0:audit['reason']='undefined_base_prediction';return base,audit
    _,base_error,base_speed=valid[0];audit.update(baseline_error=base_error,baseline_next_speed=base_speed)
    best=min(v[1] for v in valid);winners=[v for v in valid if v[1]==best]
    selected=winners[0][0] if len(winners)==1 else 0
    chosen=actions[selected].copy();entry=audit['candidates'][selected]
    changed=not np.array_equal(chosen,base)
    if changed:assert entry['error']<base_error
    assert chosen[0]==base[0]
    audit.update(changed=changed,reason='unique_improvement' if changed else 'exact_tie' if len(winners)>1 else 'baseline_best',action=chosen.tolist(),
        chosen_next_speed=entry['next_speed'],chosen_error=entry['error'],selected_name=names[selected],selected_supported=entry['supported'])
    return chosen,audit
