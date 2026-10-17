"""Opt-in binary64 shared-endpoint classification repair; no tolerance/fallback.

Interior projection retains417's norm(edge)**2 denominator. Endpoint identity
uses exact finite numeric equality (+0 and -0 identify one geometric value),
but normalization copies the original vertex owner's serialized coordinates.
Original frozen397/417 files and existing callers are never patched globally.
"""
import types
import numpy as np
from retry.signed417_executor import CoherentExecutor as _Original,ExecutorDomainError

def terms(line,pos,vel):
    line=np.asarray(line,float);pos=np.asarray(pos,float);vel=np.asarray(vel,float)
    if line.ndim!=2 or line.shape[1]!=2 or len(line)<2 or pos.shape!=(2,) or vel.shape!=(2,) or not all(np.isfinite(x).all() for x in (line,pos,vel)):
        raise ExecutorDomainError('Projection_schema491')
    # Reject aliases, never deduplicate/reorder/transform the reference.
    if len(np.unique(line,axis=0))!=len(line):raise ExecutorDomainError('Duplicate_numeric_vertex491')
    end=np.roll(line,-1,axis=0)
    with np.errstate(over='ignore',under='ignore',invalid='ignore',divide='ignore'):
        edges=end-line;ds=np.linalg.norm(edges,axis=1);denominator=ds*ds
        if not np.isfinite(ds).all() or not np.isfinite(denominator).all() or np.any(ds<=0) or np.any(denominator<=0):raise ExecutorDomainError('Nonpositive_or_nonfinite_segment491')
        numerator=np.sum((pos-line)*edges,axis=1)
        if not np.isfinite(numerator).all():raise ExecutorDomainError('Projection_numeric491')
        quotient=numerator/denominator
        if not np.isfinite(quotient).all():raise ExecutorDomainError('Projection_numeric491')
        raw_u=np.clip(quotient,0,1);feet=line+raw_u[:,None]*edges
        if not np.isfinite(raw_u).all() or not np.isfinite(feet).all():raise ExecutorDomainError('Projection_numeric491')
        u=raw_u.copy();vertex=np.full(len(line),-1,int)
        query_start=np.all(line==pos,axis=1);query_end=np.all(end==pos,axis=1)
        # A serialized query known to be this edge's own endpoint is exact
        # endpoint identity, independent of quotient roundoff at u=1.
        feet[query_start]=line[query_start];u[query_start]=0.
        feet[query_end]=end[query_end];u[query_end]=1.
        at_start=np.all(feet==line,axis=1)|(u==0)
        at_end=np.all(feet==end,axis=1)|(u==1)
        if np.any(at_start&at_end):raise ExecutorDomainError('Degenerate_endpoint_identity491')
        feet[at_start]=line[at_start];u[at_start]=0.;vertex[at_start]=np.arange(len(line))[at_start]
        feet[at_end]=end[at_end];u[at_end]=1.;vertex[at_end]=(np.arange(len(line))[at_end]+1)%len(line)
        distance=np.sum((pos-feet)**2,axis=1)
        if not np.isfinite(distance).all():raise ExecutorDomainError('Projection_numeric491')
    return dict(line=line,edges=edges,ds=ds,denominator=denominator,raw_u=raw_u,u=u,feet=feet,vertex=vertex,distance=distance,query_endpoint=query_start|query_end,foot_endpoint=at_start|at_end)

def canonical_projection(line,pos,vel,phase):
    z=terms(line,pos,vel);line=z['line'];ds=z['ds'];u=z['u'];feet=z['feet'];vertex=z['vertex'];edges=z['edges']
    ix=np.flatnonzero(z['distance']==z['distance'].min());side='interior'
    if len(ix)==1 and vertex[ix[0]]<0:
        j=int(ix[0]);fraction=float(u[j])
        if not 0<fraction<1:raise ExecutorDomainError('Projection_numeric491')
    else:
        vertices={int(vertex[j]) for j in ix}
        if len(vertices)!=1 or -1 in vertices:raise ExecutorDomainError('Distinct_or_nonadjacent_projection_ambiguity')
        node=next(iter(vertices));incident={(node-1)%len(line),node}
        if not set(int(j) for j in ix)<=incident:raise ExecutorDomainError('Distinct_or_nonadjacent_projection_ambiguity')
        if node==0 and phase in ['FIRST_LAP','FINISH_CONFIRM']:j=len(line)-1;fraction=1.;side='incoming_terminal_vertex'
        else:j=node;fraction=0.;side='outgoing_vertex'
    sarc=np.r_[0,np.cumsum(ds)];arc=float(sarc[-1] if side=='incoming_terminal_vertex' else sarc[j]+fraction*ds[j]);sigma=float(np.asarray(vel,float)@(edges[j]/ds[j]));foot=line[j] if fraction==0 else line[(j+1)%len(line)] if fraction==1 else feet[j]
    if not np.isfinite(sarc).all() or not np.isfinite(sigma):raise ExecutorDomainError('Projection_numeric491')
    return dict(index=j,u=fraction,arc=arc,sigma=sigma,path_error_m=float(np.linalg.norm(np.asarray(pos,float)-foot)),side=side,ties=len(ix))

class CoherentExecutor491(_Original):
    # Original act bytecode, defaults and all other policy methods preserved;
    # only this opt-in class's canonical lookup points at the repaired version.
    act=types.FunctionType(_Original.act.__code__,{**_Original.act.__globals__,'canonical_projection':canonical_projection},_Original.act.__name__,_Original.act.__defaults__,_Original.act.__closure__)
