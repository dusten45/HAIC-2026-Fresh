"""One fixed six-model output mean, all-model support intersection, H1 pedals."""
import numpy as np
from retry.h1_329_select import candidates


def choose(base,features,state,models,enabled):
    base=np.asarray(base,np.float32).copy();assert len(models)==6
    audit=dict(enabled=bool(enabled),changed=False,reason='disabled',base=base.tolist(),action=base.tolist(),q=None,
               baseline_next_speed=None,chosen_next_speed=None,baseline_error=None,chosen_error=None,
               selected_name='baseline',selected_supported=False,candidates=[],base_support_by_model=None,model_count=6)
    if not enabled:return base,audit
    f=np.asarray(features,float)
    if len(f)!=16 or bool(f[0]) or not np.isfinite([f[2],f[6]]).all() or f[2]<=0 or f[6]<0:
        audit['reason']='absent_or_invalid_target';return base,audit
    q=float(f[6]);audit['q']=q
    if state is None or not np.isfinite(state).all():audit['reason']='invalid_current_HUD';return base,audit
    state=np.asarray(state,float);current=np.r_[state,base]
    support=[bool(np.all(current>=m['low']) and np.all(current<=m['high'])) for m in models];audit['base_support_by_model']=support
    if not all(support):audit['reason']='base_input_outside_any_support';return base,audit
    names,actions=candidates(base);valid=[]
    for index,(name,action) in enumerate(zip(names,actions)):
        x=np.r_[state,action];supported=[bool(np.all(x>=m['low']) and np.all(x<=m['high'])) for m in models]
        predictions=[float(state[0]+(np.r_[(x-m['mean'])/m['scale'],1.]@m['beta'])[0]) for m in models] if all(supported) else None
        prediction=float(np.mean(predictions)) if predictions is not None and np.isfinite(predictions).all() else None
        error=abs(prediction-q) if prediction is not None else None
        audit['candidates'].append(dict(name=name,action=action.tolist(),support_by_model=supported,supported=all(supported),model_next_speeds=predictions,next_speed=prediction,error=error))
        if error is not None:valid.append((index,error,prediction))
    if not valid or valid[0][0]!=0:audit['reason']='undefined_base_prediction';return base,audit
    _,base_error,base_speed=valid[0];audit.update(baseline_error=base_error,baseline_next_speed=base_speed)
    best=min(v[1] for v in valid);winners=[v for v in valid if v[1]==best];selected=winners[0][0] if len(winners)==1 else 0
    out=actions[selected].copy();entry=audit['candidates'][selected];changed=not np.array_equal(out,base)
    if changed:assert entry['error']<base_error and all(entry['support_by_model']) and len(entry['model_next_speeds'])==6
    assert out[0]==base[0]
    audit.update(changed=changed,reason='unique_improvement' if changed else 'exact_tie' if len(winners)>1 else 'baseline_best',
                 action=out.tolist(),chosen_next_speed=entry['next_speed'],chosen_error=entry['error'],selected_name=names[selected],selected_supported=entry['supported'])
    return out,audit
