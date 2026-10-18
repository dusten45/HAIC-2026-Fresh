"""Finite phase driver: pilot, cold, carry. Checkpoint every case/exit."""
import argparse,datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.structure537_control import choose,geometry_context,ADMISSION
from retry.structure537_control import choose as baseline_choose
from retry.launch540_control import choose_launch
from retry.frozen534_projection import initial_progress
from retry.drive519_control import project,steering,reference,force_rows,nominal
from retry.preview527_control import backup
from retry.closure524_control import tick
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response549-private')


def terminal_metrics(root,path,s):
    q=project(root.center,path,s);v=root.planar.linear.velocity;speed=math.hypot(*v);heading=abs(math.atan2(q['tangent'][0]*v[1]-q['tangent'][1]*v[0],sum(q['tangent'][j]*v[j] for j in range(2))))
    return dict(path_error=q['distance'],heading_error=heading,yaw_error=abs(root.planar.yaw-speed*path['curvature'][q['i']]),speed_deficit=max(0.,reference(q['s'],path)[0]-speed),speed=speed)


class Stage:
    def __init__(self,phase):
        self.phase=phase;self.cpu=time.process_time();self.wall=time.perf_counter();self.counter=[0];self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0);self.c=json.loads((G/'retry/retime549_model_contract.json').read_text());self.outcomes=[];self.current=None;self.arm='candidate';self.safety_state=None;self.probe_gate=None;limits=self.c['phase_caps'][phase];self.tick_cap=limits['model_ticks'];self.force_cap=limits['force'];self.cpu_cap=limits['CPU_s'];self.wall_cap=limits['wall_s']
        if (D/f'{phase}-STARTED.json').exists():raise RuntimeError('NO_PHASE_RETRY')
        for p,h in self.c['source_sha256'].items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
        for p,h in self.c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
        self.static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());self.paths=json.loads((D/'frozen-paths-private.json').read_text());self.ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());self.index=bounds(self.static['roads']);self.edge=boundary_index(self.static['boundary']);self.geometry=geometry_context(self.static,self.c['phase_caps'][phase]['geometry'])
        assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==self.c['fixed_path_sha256']
        self.save(D/f'{phase}-STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/retime549_model_contract.json').read_bytes()).hexdigest()))
    def save(self,p,value,overwrite=False):
        data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        if len(list(D.iterdir()))>=8192 or sum(z.stat().st_size for z in D.iterdir())+len(data)>256*1024**2:raise RuntimeError('PRIVATE_CAP')
        if overwrite:
            q=p.with_suffix(p.suffix+'.tmp');q.write_bytes(data);q.replace(p)
        else:
            with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def guard(self,reserve=0):
        if time.process_time()-self.cpu>=self.cpu_cap or time.perf_counter()-self.wall>=self.wall_cap:raise RuntimeError('PHASE_COST_CAP')
        if self.counter[0]>=self.tick_cap or self.cost['force_evaluations']+reserve>self.force_cap:raise RuntimeError('PHASE_WORK_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.c['deadline_utc']):raise RuntimeError('DEADLINE')
    def checkpoint(self):
        self.save(D/f'{self.phase}-latest-cost-private.json',dict(current_case=self.current,completed_cases=len(self.outcomes),model_ticks=self.counter[0],cost=self.cost,CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall,safety=self.safety_state),True)
    def root(self,state):return load_root(dict(state,roads=self.static['root']['roads']))
    def select(self,root,s,history):
        self.guard(6400);selector=baseline_choose if self.arm=='baseline' else choose;action,detail=selector(root,self.paths['candidate'],self.paths['backup'],s,self.counter,self.cost,self.tick_cap,history=history,geometry=self.geometry)
        if action is not None:
            final=next(x for x in detail['reports'] if x['mode']=='FINAL');assert detail['final_recertified'] and final['ok'] and final['peak']<=ADMISSION and final['min_footprint_margin_m']>=.5;assert action[0].tobytes()==np.float32(steering(root,self.paths['candidate'],s)).tobytes()
        return action,detail
    def simulate(self,label,root,completed,history,visited,full,holds):
        self.current=label;self.safety_state=None;path=self.paths['candidate'];s=initial_progress(root,path,completed);tracker=tracker_for(self.static,root,set(visited),completed>0,1.02+.08*completed) if full else None;visited=set(visited);elapsed=0.;trace=[];commands=[];minimum=margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);maxpath=maxover=maxbody=0.;stats={x:dict(peak=0.,samples=0,clipped=0) for x in ('launch','running')};stats['running'].update(clipped=history[0],samples=history[1]);modes={};failure=None;crossing=None;cross_hold=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        try:
            for i in range(completed,min(500,completed+holds)):
                self.checkpoint();self.guard(6400)
                if i<24:
                    action,detail=choose_launch(root,path,self.paths['backup'],s,i,(stats['launch']['clipped'],stats['launch']['samples']),self.counter,self.cost,self.tick_cap,self.geometry,guard=self.guard)
                else:action,detail=self.select(root,s,(stats['running']['clipped'],stats['running']['samples']))
                if action is None:stop='NO_ADMISSIBLE_ACTION';failure=dict(index=i+1,reason=stop);commands.append(dict(index=i+1,detail=detail));break
                modes[detail['mode']]=modes.get(detail['mode'],0)+1;commands.append(dict(index=i+1,action=action.tolist(),detail=detail));root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                for k in range(4):
                    self.guard(4);before=root;old_s=s;force=force_rows(root,action);self.cost['force_evaluations']+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),self.counter);elapsed+=.02;q=project(root.center,path,s);s=q['s'];
                    if self.cost['geometry_checks']>=self.geometry['max_checks']:raise RuntimeError('GEOMETRY_CAP')
                    self.cost['geometry_checks']+=1;gap=margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);minimum=min(minimum,gap);maxpath=max(maxpath,q['distance']);target=reference(s,path)[0];over=math.hypot(*root.planar.linear.velocity)-target
                    if i>=24:maxover=max(maxover,over)
                    maxbody=max(maxbody,max(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels),math.hypot(*hull_pose(root)[1]));group='launch' if i<24 else 'running';z=stats[group];z['peak']=max(z['peak'],max(x['ratio'] for x in force));z['samples']+=4;z['clipped']+=sum(x['clipped'] for x in force)
                    for ids in root.current_contacts:visited.update(ids)
                    if tracker:
                        pose,velocity=hull_pose(root);tracker.update(pose,velocity,len(visited)/len(self.static['track']),1.02+.08*completed+elapsed)
                    self.safety_state=dict(min_margin_m=minimum,max_path_error_m=maxpath,max_reference_overspeed_m_s=maxover,force_groups=stats);state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,progress=s,margin=gap,path_error=q['distance'],target=target,forces=force,action=action.tolist()));problems=[]
                    if gap<.5251524480367317:problems.append('MARGIN')
                    if maxpath>3:problems.append('PATH')
                    if maxover>4.85:problems.append('REFERENCE')
                    if maxbody>=100:problems.append('MODEL_BODY_DOMAIN')
                    if s-old_s<-.5 or s-old_s>max(5.,2*math.dist(root.center,before.center)):problems.append('PROJECTION')
                    if stats['launch']['peak']>2.5 or (i>=23 and stats['launch']['samples'] and stats['launch']['clipped']/stats['launch']['samples']>.15):problems.append('LAUNCH')
                    if stats['running']['peak']>ADMISSION or (stats['running']['samples'] and stats['running']['clipped']/stats['running']['samples']>.10):problems.append('RUNNING')
                    if self.probe_gate is not None and crossing is None:
                        gate=self.probe_gate;dot=lambda p:sum((p[j]-gate['point'][j])*gate['tangent'][j] for j in range(2));a=dot(before.center);b=dot(root.center)
                        if a<0<=b:
                            frac=-a/(b-a);vel=[before.planar.linear.velocity[j]+frac*(root.planar.linear.velocity[j]-before.planar.linear.velocity[j]) for j in range(2)];v=math.hypot(*vel);yaw=before.planar.yaw+frac*(root.planar.yaw-before.planar.yaw);heading=abs(math.atan2(gate['tangent'][0]*vel[1]-gate['tangent'][1]*vel[0],sum(gate['tangent'][j]*vel[j] for j in range(2))));assert sum(gate['tangent'][j]*vel[j] for j in range(2))>0;crossing=dict(lower_s=.02*(len(trace)-1),upper_s=.02*len(trace),time_s=.02*(len(trace)-1+frac),speed=v,heading_error=heading,yaw_error=abs(yaw-v*gate['curvature']));cross_hold=i+1
                    if problems:failure=dict(index=i+1,raw=k+1,episode_s=.08*completed+elapsed,violations=problems);stop=problems[0];break
                    if tracker and tracker.finish_time_s is not None:stop='MODEL_SOURCE_STYLE_FINISH';break
                    if full and 50+4*completed+len(trace)>=1224:stop='TIME_LIMIT';break
                    if full and s>path['length']+10 and tracker.finish_time_s is None:stop='ARC_WITHOUT_FINISH';break
                if failure or stop in ('MODEL_SOURCE_STYLE_FINISH','TIME_LIMIT','ARC_WITHOUT_FINISH'):break
                if cross_hold is not None and i+1>=cross_hold+12:break
        except BaseException as exc:
            self.save(D/f'{label}-interrupted-private.json',dict(error=type(exc).__name__+':'+str(exc),trace=trace,commands=commands,model_ticks=self.counter[0],cost=self.cost));raise
        clips,samples=history;trend=[];clip_peak=clips/samples if samples else 0.
        for q in trace:
            if q['index']>24:
                clips+=sum(z['clipped'] for z in q['forces']);samples+=4;clip_peak=max(clip_peak,clips/samples)
                if q['raw']==4 or q is trace[-1]:trend.append(dict(index=q['index'],clipped=clips,samples=samples,fraction=clips/samples))
        probe_complete=self.probe_gate is None or (cross_hold is not None and trace[-1]['index']>=cross_hold+12 and trace[-1]['raw']==4)
        item=dict(crossing=crossing,continuation12_complete=probe_complete,terminal=terminal_metrics(root,path,s),clipping_trajectory=trend,max_cumulative_clipping_fraction=clip_peak,label=label,stop=stop,pass_safety=probe_complete and failure is None and stop==('MODEL_SOURCE_STYLE_FINISH' if full else 'PROBE_COMPLETE'),raw_ticks=len(trace),actions=len(commands),completed_before=completed,force_groups=stats,min_margin_m=minimum,max_path_error_m=maxpath,max_reference_overspeed_m_s=maxover,max_body_speed_m_s=maxbody,mode_counts=modes,high_fraction=modes.get('HIGH',0)/max(1,sum(x for key,x in modes.items() if key!='FIXED_LAUNCH')),first_failure=failure,model_finish_episode_s=tracker.finish_time_s-1.02 if tracker and tracker.finish_time_s is not None else None)
        self.save(D/f'{label}-private.json',dict(summary=item,trace=trace,commands=commands));self.outcomes.append(item);self.checkpoint();return item
    def pilot(self):
        design=json.loads((G/'retry/retime549_design_result.json').read_text());assert design['passed'] and design['scalar_clock_difference_s']>0 and design['selected_window_scalar_proxy_s']>=.02
        data=json.loads((D/'probe-private.json').read_text());self.probe_gate=data['gate'];original=self.paths['candidate'];cases=[]
        for arm,path in [('baseline',self.paths['baseline']),('candidate',original)]:
            self.arm=arm;self.paths['candidate']=path;case=self.simulate('common-plane-'+arm,self.root(data['root']),data['completed'],tuple(data['history']),set(),False,64);cases.append(case)
            if not case['pass_safety']:return dict(passed=False,reason=arm+'_SAFETY_OR_CROSSING_OR_CONTINUATION_FAILURE',promotion_eligible=False)
        self.paths['candidate']=original;a,b=cases;ac=a['crossing'];bc=b['crossing'];am=a['terminal'];bm=b['terminal'];gain=ac['lower_s']-bc['upper_s'];cross_ok=bc['speed']>=ac['speed']-.15 and bc['heading_error']<=ac['heading_error']+.02 and bc['yaw_error']<=ac['yaw_error']+.05;end_ok=bm['path_error']<=am['path_error']+.10 and bm['heading_error']<=am['heading_error']+.02 and bm['yaw_error']<=am['yaw_error']+.05 and bm['speed_deficit']<=am['speed_deficit']+.15
        return dict(passed=bool(gain>=.02-1e-12 and cross_ok and end_ok),reason='ONE_COMMON_PLANE_FALSIFICATION',conservative_time_gain_s=gain,interpolated_time_gain_s=ac['time_s']-bc['time_s'],crossing_terminal_pass=bool(cross_ok),continuation_terminal_pass=bool(end_ok),promotion_eligible=False,not_whole_lap_gain=True)
    def full(self,kind):
        pilot=json.loads((G/'retry/retime549_pilot_result.json').read_text());assert pilot['passed']
        if kind=='cold':root=self.root(self.static['root']);completed=0;history=(0,0);visited=set(self.ledger['initial_visited'])
        else:
            cold=json.loads((G/'retry/retime549_cold_result.json').read_text());assert cold['passed'];case=json.loads(Path(self.ledger['checkpoint']).read_text());root=self.root(case['before_root_without_roads']);completed=self.ledger['completed_actions'];history=(0,352);visited=set(self.ledger['carry_visited'])
        item=self.simulate(kind+'-candidate',root,completed,history,visited,True,500);base=json.loads((G/('retry/joint541_'+kind+'_result.json')).read_text())['case'];gain=base['model_finish_episode_s']-item['model_finish_episode_s'] if item['pass_safety'] else None
        ms=round(base['model_finish_episode_s']*1000)-round(item['model_finish_episode_s']*1000) if item['pass_safety'] else None
        return dict(passed=bool(item['pass_safety'] and ms>=500),case=item,gain_vs541_s=gain,gain_vs541_ms=ms,effect_gate_unit='official_milliseconds',effect_threshold_ms=500,carry_uses_new_profile=kind=='carry')
    def run(self):
        from core.vendor.car_racing import CarRacing
        def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
        CarRacing.__init__=CarRacing.reset=CarRacing.step=poison
        def interrupt(*a):raise RuntimeError('PHASE_TIMER_CAP')
        signal.signal(signal.SIGPROF,interrupt);signal.setitimer(signal.ITIMER_PROF,self.cpu_cap);signal.signal(signal.SIGALRM,interrupt);signal.setitimer(signal.ITIMER_REAL,self.wall_cap);result={};error=None
        try:result=self.pilot() if self.phase=='pilot' else self.full(self.phase)
        except BaseException as exc:error=type(exc).__name__+':'+str(exc);result=dict(passed=False,technical_error=error);self.save(D/f'{self.phase}-error-private.json',dict(error=error,traceback=traceback.format_exc(),model_ticks=self.counter[0],cost=self.cost))
        finally:
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.checkpoint()
            out=dict(phase=self.phase,**result,cases=self.outcomes,model_integrator_ticks=self.counter[0],source_wheel_force_evaluations_in_integrator=4*self.counter[0],explicit_force_evaluations=self.cost['force_evaluations'],planner_cost=self.cost,CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall,native_actions=0,native_resets=0,research_remaining=22758,reserve=84000,reserve_used=0)
            self.save(G/f'retry/retime549_{self.phase}_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','cold','carry'),required=True);Stage(parser.parse_args().phase).run()
