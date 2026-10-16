"""Pure GT scalar executor with explicit reset/first-lap/finish domains.

No environment, actor, model, data-file access, or physics integration here.
Finish fields are current privileged diagnostic inputs, not legal pixel inputs.
"""
import math
import numpy as np
from retry.scalar392_audit import pedals

class ExecutorDomainError(RuntimeError):pass

def canonical_projection(line,pos,vel,phase):
    line=np.asarray(line,float);pos=np.asarray(pos,float);vel=np.asarray(vel,float);edges=np.roll(line,-1,axis=0)-line;ds=np.linalg.norm(edges,axis=1)
    if np.any(ds<=0):raise ExecutorDomainError('Nonpositive_segment')
    u=np.clip(np.sum((pos-line)*edges,axis=1)/(ds*ds),0,1);feet=line+u[:,None]*edges;vertex=np.full(len(line),-1,int)
    for j in range(len(line)):
        if u[j]==0:feet[j]=line[j];vertex[j]=j
        elif u[j]==1:feet[j]=line[(j+1)%len(line)];vertex[j]=(j+1)%len(line)
    distance=np.sum((pos-feet)**2,axis=1);ix=np.flatnonzero(distance==distance.min());side='interior'
    if len(ix)==1 and 0<u[ix[0]]<1:j=int(ix[0]);fraction=float(u[j])
    else:
        vertices={int(vertex[j]) for j in ix}
        if len(vertices)!=1 or -1 in vertices:raise ExecutorDomainError('Distinct_or_nonadjacent_projection_ambiguity')
        node=next(iter(vertices))
        if node==0 and phase in ['FIRST_LAP','FINISH_CONFIRM']:j=len(line)-1;fraction=1.;side='incoming_terminal_vertex'
        else:j=node;fraction=0.;side='outgoing_vertex'
    sarc=np.r_[0,np.cumsum(ds)];arc=float(sarc[-1] if side=='incoming_terminal_vertex' else sarc[j]+fraction*ds[j]);sigma=float(vel@(edges[j]/ds[j]));foot=line[j] if fraction==0 else line[(j+1)%len(line)] if fraction==1 else feet[j]
    return dict(index=j,u=fraction,arc=arc,sigma=sigma,path_error_m=float(np.linalg.norm(pos-foot)),side=side,ties=len(ix))

class CoherentExecutor:
    def __init__(self,fixed,intent='lap'):
        self.line=np.asarray(fixed['line'],float);self.ds=np.asarray(fixed['free_profile']['ds'],float);self.nodes=np.asarray(fixed['free_profile']['speed'],float)*1.5;self.model=fixed['model'];self.L=float(np.cumsum(np.linalg.norm(np.roll(self.line,-1,axis=0)-self.line,axis=1))[-1]);self.intent=intent
        if intent not in ['lap','stop']:raise ExecutorDomainError('Unknown_intent')
        if len(self.nodes)!=len(self.line)+1 or len(self.ds)!=len(self.line) or np.any(self.ds<=0) or np.any(~np.isfinite(self.nodes)):raise ExecutorDomainError('Invalid_profile')
        if intent=='lap' and (self.nodes[0]!=0 or np.any(self.nodes[1:]<=0)):raise ExecutorDomainError('Unsupported_nonlaunch_stop_target')
        self.phase='LAUNCH' if intent=='lap' else 'STOP';self.previous_arc=None;self.s=None;self.last_time=None;self.launch_commanded=False
    def _advance(self,arc,cursor_arc):
        if self.previous_arc is None:self.s=arc+round((cursor_arc-arc)/self.L)*self.L
        else:
            delta=(arc-self.previous_arc+self.L/2)%self.L-self.L/2
            if abs(delta)==self.L/2:raise ExecutorDomainError('Halfperiod_arc_ambiguity')
            self.s+=delta
        self.previous_arc=arc
    def _reference(self,q):
        j=q['index'];u=q['u'];w=(1-u)*self.nodes[j]**2+u*self.nodes[j+1]**2
        if w<=0:raise ExecutorDomainError('Zero_target_outside_launch')
        r=float(np.sqrt(w));f=float((self.nodes[j+1]**2-self.nodes[j]**2)/(2*self.ds[j]));return r,f
    def _confirm_valid(self,state,finish):
        t=state['time'];candidate=finish.get('candidate_crossing_time_s');qualified=finish.get('qualified_time_s')
        if candidate is None or qualified is None or not finish.get('crossing_from_back'):raise ExecutorDomainError('Finish_confirmation_not_current')
        if not math.isfinite(candidate) or not math.isfinite(qualified) or candidate>t or qualified>t:raise ExecutorDomainError('Future_finish_metadata')
        forward=np.asarray(finish['forward'],float);right=np.asarray([forward[1],-forward[0]]);offset=np.asarray(state['pos'])-finish['center'];lon=float(offset@forward);lat=float(offset@right);vf=float(np.asarray(state['vel'])@forward);vs=float(np.asarray(state['vel'])@right)
        if not(0<=lon<finish['half_depth'] and abs(lat)<=finish['half_width'] and vf>1e-4 and abs(vs)<=4*vf):raise ExecutorDomainError('Invalid_finish_confirmation_corridor')
    def mark_done(self,finish,now):
        when=finish.get('finish_time_s')
        if when is None or not math.isfinite(when) or not math.isfinite(now) or when>now:raise ExecutorDomainError('DONE_without_current_official_finish')
        self.phase='DONE';return dict(phase=self.phase,official_finish_time_s=when)
    def act(self,state,nominal,finish,cursor_arc=0.):
        phase_before=self.phase;t=float(state['time']);v=float(state['speed']);nominal=np.asarray(nominal,np.float32)
        if not np.isfinite(nominal).all() or not np.isfinite(state['pos']).all() or not np.isfinite(state['vel']).all() or not math.isfinite(t) or v<0 or not math.isfinite(v) or not(np.all(nominal>=np.asarray([-.4,0,0],np.float32)) and np.all(nominal<=np.asarray([.4,1,1],np.float32))):raise ExecutorDomainError('Nonfinite_or_negative_speed')
        if finish.get('finish_time_s') is not None:return None,self.mark_done(finish,t)
        if self.phase=='DONE':raise ExecutorDomainError('Action_after_DONE_without_reset')
        if self.last_time is not None and t<=self.last_time:raise ExecutorDomainError('Duplicate_or_nonmonotone_action_boundary')
        self.last_time=t
        if self.phase=='STOP':
            z=pedals(-1.5*v,v,self.model);a=nominal.copy();a[1:]=[0.,z['brake']];return a,dict(phase=self.phase,raw_accel=-1.5*v,target=0.,intent='stop')
        q=canonical_projection(self.line,state['pos'],state['vel'],self.phase);self._advance(q['arc'],cursor_arc)
        candidate=finish.get('candidate_crossing_time_s') is not None
        if self.phase=='FINISH_CONFIRM' or candidate:
            if self.phase=='LAUNCH':raise ExecutorDomainError('Finish_candidate_during_launch')
            self._confirm_valid(state,finish);self.phase='FINISH_CONFIRM';r=float(self.nodes[-1]);f=0.;sigma=float(np.asarray(state['vel'])@np.asarray(finish['forward']))
        elif self.phase=='LAUNCH':
            if not self.launch_commanded:
                self.launch_commanded=True;return nominal.copy(),dict(phase=self.phase,phase_before=phase_before,launch='reset_finite_original_law',actual_arc=self.s,projection=q)
            if not(0<self.s<self.L):
                if self.s>=self.L:raise ExecutorDomainError('Launch_outside_first_lap')
                return nominal.copy(),dict(phase=self.phase,phase_before=phase_before,launch='await_positive_current_projection',actual_arc=self.s,projection=q)
            self.phase='FIRST_LAP';r,f=self._reference(q);sigma=q['sigma']
        else:
            if self.phase!='FIRST_LAP' or not(0<self.s<self.L):raise ExecutorDomainError('First_lap_arc_domain')
            r,f=self._reference(q);sigma=q['sigma']
        if sigma<-.1:raise ExecutorDomainError('Meaningful_negative_progress_domain')
        raw=f*(sigma/r)+1.5*(r-v)
        if not all(math.isfinite(x) for x in [r,f,sigma,raw]):raise ExecutorDomainError('Nonfinite_reference')
        z=pedals(raw,v,self.model);a=nominal.copy();a[1:]=[z['gas'],z['brake']]
        if not(np.isfinite(a).all() and np.all(a>=np.asarray([-.4,0,0],np.float32)) and np.all(a<=np.asarray([.4,1,1],np.float32))):raise ExecutorDomainError('Action_bounds')
        return a,dict(phase=self.phase,phase_before=phase_before,actual_arc=self.s,projection=q,r=r,f=f,sigma=sigma,raw_accel=raw,command_accel=z['command_accel'])
