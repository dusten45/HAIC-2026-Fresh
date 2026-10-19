"""Bounded phase-I and ablations on saved algebra, with box-valid witnesses."""
import numpy as np
from retry.algebra575_diagnose import ROOT,PRIVATE,Budget,read,write,tube

def load():
    v=dict(np.load(PRIVATE/'model-private.npz'));p={k:v[k] for k in ['A','b','bounds','objective','x0','scale']};p.update(groups=list(range(2,265,2)),ratio_rows=v['ratio_rows'].tolist(),path={k[5:]:v[k] for k in v if k.startswith('path_')});return p

def witness(A,b,bounds,weights):
    ids=np.flatnonzero(weights>0);w=weights[ids].astype(np.longdouble);a=A[ids].astype(np.longdouble);bb=b[ids].astype(np.longdouble);box=bounds.astype(np.longdouble)
    r=w@a;rhs=w@bb;lower=np.sum(np.minimum(r*box[:,0],r*box[:,1]));mag=np.max(abs(box),axis=1)
    allowance=np.longdouble(16*(len(ids)+A.shape[1]+8)*np.finfo(float).eps)*(np.sum(w@(abs(a))*mag)+np.sum(w*abs(bb))+np.longdouble('1e-300'))
    return dict(rows=ids.tolist(),weights=[float(x) for x in w],row_count=len(ids),weighted_rhs=float(rhs),weighted_lhs_box_lower=float(lower),strict_gap=float(lower-rhs),conservative_arithmetic_allowance=float(allowance),verified_contradiction=bool(lower-rhs>allowance),maximum_cancellation_residual=float(max(abs(r))))

def main():
    budget=Budget();out={}
    try:
        p=load();t=tube(p);A,b,box=t['A'],t['b'],t['bounds'];s=np.max(abs(A),axis=1);s=np.where(s>0,s,1.);scaled=A/s[:,None];rhs=b/s
        budget.solve('expanded-row-scaled-feasibility',scaled,rhs,box)
        phase=budget.solve('expanded-phase-I',np.c_[scaled,-np.ones(len(b))],rhs,np.vstack([box,[0.,None]]),np.r_[np.zeros(A.shape[1]),1.])
        if phase.success:
            weights=-phase.ineqlin.marginals/s;out['expanded_phase_I']=dict(minimum_scaled_slack=float(phase.fun),certificate=witness(A,b,box,weights));np.savez(PRIVATE/'expanded-certificate-private.npz',weights=weights)
        # Distinguish inward-domain exclusion from row margins and rank constraints.
        budget.solve('expanded-inward-box-only',p['A'],p['b'],box)
        ids=np.ones(len(b),bool);ids[p['ratio_rows']]=False
        budget.solve('expanded-tube-without-rank-branch',A[ids],b[ids],box)
        # Two categories of margin removed together is diagnostic, never admissible.
        q=tube(p,rounding=False,numerical=False)
        budget.solve('expanded-without-row-margins',q['A'],q['b'],q['bounds'])
        out['solves']=budget.records
    finally:budget.close();write(ROOT/'retry/algebra575_isolation.json',out)
    print(out)

if __name__=='__main__':main()
