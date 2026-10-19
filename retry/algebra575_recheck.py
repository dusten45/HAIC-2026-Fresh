"""One corrected implementation, same saved algebra, no source execution."""
import numpy as np
from retry.algebra575_diagnose import ROOT,PRIVATE,Budget,read,write,static_checks
from retry.algebra575_isolate import load,witness
from retry.causal575_rounding import solve,effective_uncertainty,numerical_margin,check

def reduced_witness(A,b,box,weights):
    weights=weights.copy();before=witness(A,b,box,weights)
    for i in np.argsort(weights):
        if weights[i]<=0:continue
        old=weights[i];weights[i]=0.;v=witness(A,b,box,weights)
        if not v['verified_contradiction']:weights[i]=old
    after=witness(A,b,box,weights);after['original_row_count']=before['row_count'];return after

def main():
    budget=Budget();out=dict(implementation_corrections=1,source_ticks=0,actual_actions=0,HOLDOUT=0,SEALED=0,branches={})
    try:
        p=load();saved=dict(np.load(PRIVATE/'expanded-tube-private.npz'));weights=np.load(PRIVATE/'expanded-certificate-private.npz')['weights'];out['original_expanded_reduced_certificate']=reduced_witness(saved['A'],saved['b'],saved['bounds'],weights)
        for name,fixed in [('tail',196),('expanded',0)]:
            branch=dict(p,bounds=p['bounds'].copy());branch['bounds'][:fixed]=0.;used=[0]
            def bounded(c,A_ub,b_ub,bounds,**ignored):
                used[0]+=1
                return budget.solve('corrected-'+name+'-'+str(used[0]),A_ub,b_ub,bounds,c)
            x,meta=solve(branch,solve_fn=bounded,max_solves=8)
            q,box,mag=effective_uncertainty(branch);gamma=400*np.finfo(float).eps/(1-400*np.finfo(float).eps);margin=abs(p['A'][:,:264])@q;num=numerical_margin(p['A'],p['b'],mag,gamma);b=p['b']-margin-num
            t=dict(A=p['A'],b=b,bounds=box,q=q,margin=margin,numerical=num)
            out['branches'][name]=dict(result=meta,static=static_checks(branch,t))
            if x is not None:
                # Never execute. Keep policy commands private; expose original-row verdict.
                np.save(PRIVATE/(name+'-algebra-candidate-private.npy'),x)
                out['branches'][name]['original_rounded_verdict']=check(branch,x)
            else:
                # Independent feasibility witness, separate from the objective solver.
                s=np.max(abs(p['A']),axis=1);s=np.where(s>0,s,1.);A=p['A']/s[:,None]
                phase=budget.solve('corrected-'+name+'-phase-I',np.c_[A,-np.ones(len(b))],b/s,np.vstack([box,[0.,None]]),np.r_[np.zeros(396),1.])
                if phase.success:
                    weights=-phase.ineqlin.marginals/s;out['branches'][name]['certificate']=reduced_witness(p['A'],b,box,weights)
        # Prove the expanded inward-box-only failure without rounding/numeric margins.
        q,box,_=effective_uncertainty(p);s=np.max(abs(p['A']),axis=1);s=np.where(s>0,s,1.)
        phase=budget.solve('expanded-inward-only-phase-I',np.c_[p['A']/s[:,None],-np.ones(len(s))],p['b']/s,np.vstack([box,[0.,None]]),np.r_[np.zeros(396),1.])
        if phase.success:out['inward_only_certificate']=reduced_witness(p['A'],p['b'],box,-phase.ineqlin.marginals/s)
        out['solves']=budget.records
    finally:budget.close();write(ROOT/'retry/algebra575_recheck.json',out)
    print({name:out['branches'][name]['result'] for name in out['branches']})

if __name__=='__main__':main()
