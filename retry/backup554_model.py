"""Finite phase driver: pilot, cold, carry. Checkpoint every case/exit."""
import argparse,datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
import retry.structure537_control as tracking_module
import retry.launch540_control as launch_module
from retry.structure537_control import choose,geometry_context,ADMISSION
from retry.backup554_control import Planner,install_dispatch
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
source_tick=tick
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response554-private')


class Stage:
    def __init__(self,phase):
        self.phase=phase;self.cpu=time.process_time();self.wall=time.perf_counter();self.counter=[0];self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0,model_body_checks=0,max_all_model_body_speed_m_s=0.);self.c=json.loads((G/'retry/backup554_contract.json').read_text());self.outcomes=[];self.current=None;self.arm='candidate';self.safety_state=None;self.current_curve=None;self.trigger_verified=False;self.dynamic_done=False;self.crossings={};limits=self.c['phase_caps'][phase];self.tick_cap=limits['model_ticks'];self.force_cap=limits['force'];self.cpu_cap=limits['CPU_s'];self.wall_cap=limits['wall_s']
        if (D/f'{phase}-STARTED.json').exists():raise RuntimeError('NO_PHASE_RETRY')
        for p,h in self.c['source_sha256'].items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
        for p,h in self.c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
        self.static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());self.paths=json.loads((D/'frozen-paths-private.json').read_text());self.ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());self.index=bounds(self.static['roads']);self.edge=boundary_index(self.static['boundary']);self.geometry=geometry_context(self.static,self.c['phase_caps'][phase]['geometry'])
        assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==self.c['fixed_path_sha256'];self.private=D;self.entry=json.loads((D/'entry-private.json').read_text());self.planner=Planner(self,self.entry)
        self.save(D/f'{phase}-STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/backup554_contract.json').read_bytes()).hexdigest()))
    def checked_tick(self,root,gas,brake,index,counter):
        self.guard();after=source_tick(root,gas,brake,index,counter);v=max(math.hypot(*hull_pose(after)[1]),*(math.hypot(*(after.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in after.planar.linear.wheels));self.cost['model_body_checks']+=1;self.cost['max_all_model_body_speed_m_s']=max(self.cost['max_all_model_body_speed_m_s'],v)
        if not math.isfinite(v) or v>=100:
            state=asdict(after);state.pop('roads');self.save(D/f'{self.phase}-first-model-domain-private.json',dict(root_without_roads=state,body_speed=v,model_ticks=counter[0]));raise RuntimeError('MODEL_BODY_DOMAIN')
        return after
    def measure_margin(self,root):
        if self.cost['geometry_checks']>=self.geometry['max_checks']:raise RuntimeError('GEOMETRY_CAP')
        self.cost['geometry_checks']+=1;return margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles'])
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
    def body_speed(self,root):
        return max(math.hypot(*hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels))
    def original_select(self,root,s,history):
        self.guard(6400);action,detail=choose(root,self.paths['candidate'],self.paths['backup'],s,self.counter,self.cost,self.tick_cap,history=history,geometry=self.geometry)
        if action is not None:
            f=next(z for z in detail['reports'] if z['mode']=='FINAL');assert f['ok'] and f['peak']<=ADMISSION and f['min_footprint_margin_m']>=.5
        return action,detail
    def select(self,root,s,history):
        if self.trigger_verified and self.planner.dot(root.center)>=0:self.dynamic_done=True
        inside=not self.dynamic_done and self.planner.dot(root.center)<0 and (self.trigger_verified or self.entry['progress']-1e-9<=s<self.entry['target_station'])
        if inside:
            if not self.trigger_verified:
                state=asdict(root);state.pop('roads');assert json.dumps(state,sort_keys=True)==json.dumps(self.entry['root'],sort_keys=True);assert list(history)==self.entry['history'];self.trigger_verified=True;self.save(D/f'{self.phase}-trigger-identity-private.json',dict(root_exactly_saved551=True,history_exact=True,model_ticks=self.counter[0]))
            action,detail=self.planner.decide(root,s,history);self.current_curve=self.planner.last_curve if action is not None else None
        else:self.current_curve=None;action,detail=self.original_select(root,s,history)
        if action is not None:
            assert action[0].tobytes()==np.float32(steering(root,self.paths['candidate'],s)).tobytes();final=next(z for z in detail['reports'] if z['mode']=='FINAL');assert final['ok'] and final['min_footprint_margin_m']>=.5 and final['peak']<=ADMISSION
        return action,detail
    def active_reference(self,root,s):return self.planner.ref(root,s,self.current_curve)
    def record_crossing(self,name,gate,before,root,raw_count):
        if name in self.crossings:return
        dot=lambda p:sum((p[j]-gate['point'][j])*gate['tangent'][j] for j in range(2));a,b=dot(before.center),dot(root.center)
        if a<0<=b:
            frac=-a/(b-a);v=[before.planar.linear.velocity[j]+frac*(root.planar.linear.velocity[j]-before.planar.linear.velocity[j]) for j in range(2)];sv=math.hypot(*v);self.crossings[name]=dict(lower_s=.02*(raw_count-1),upper_s=.02*raw_count,time_s=.02*(raw_count-1+frac),speed=sv,yaw=before.planar.yaw+frac*(root.planar.yaw-before.planar.yaw))
    def simulate(self,label,root,completed,history,visited,full,holds):
        self.current=label;self.safety_state=None;self.crossings={};path=self.paths['candidate'];s=initial_progress(root,path,completed);tracker=tracker_for(self.static,root,set(visited),completed>0,1.02+.08*completed) if full else None;visited=set(visited);elapsed=0.;trace=[];commands=[];minimum=self.measure_margin(root);maxpath=maxover=maxbody=0.;stats={x:dict(peak=0.,samples=0,clipped=0) for x in ('launch','running')};stats['running'].update(clipped=history[0],samples=history[1]);modes={};failure=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        try:
            for i in range(completed,min(500,completed+holds)):
                self.checkpoint();self.guard(6400)
                if i<24:
                    if self.arm=='baseline':action=np.array([steering(root,path,s),.32,0.],np.float32);detail=dict(mode='FIXED_LAUNCH')
                    else:action,detail=choose_launch(root,path,self.paths['backup'],s,i,(stats['launch']['clipped'],stats['launch']['samples']),self.counter,self.cost,self.tick_cap,self.geometry,guard=self.guard)
                else:action,detail=self.select(root,s,(stats['running']['clipped'],stats['running']['samples']))
                if action is None:stop='NO_ADMISSIBLE_ACTION';failure=dict(index=i+1,reason=stop);commands.append(dict(index=i+1,detail=detail));break
                modes[detail['mode']]=modes.get(detail['mode'],0)+1;commands.append(dict(index=i+1,action=action.tolist(),detail=detail));root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                for k in range(4):
                    self.guard(4);before=root;old_s=s;force=force_rows(root,action);self.cost['force_evaluations']+=4;root=self.checked_tick(root,float(action[1]),float(action[2]),bounds(root.roads),self.counter);elapsed+=.02;q=project(root.center,path,s);s=q['s'];gap=self.measure_margin(root);minimum=min(minimum,gap);maxpath=max(maxpath,q['distance']);target=self.active_reference(root,s);over=math.hypot(*root.planar.linear.velocity)-target
                    if i>=24:maxover=max(maxover,over)
                    maxbody=max(maxbody,max(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels),math.hypot(*hull_pose(root)[1]));group='launch' if i<24 else 'running';z=stats[group];z['peak']=max(z['peak'],max(x['ratio'] for x in force));z['samples']+=4;z['clipped']+=sum(x['clipped'] for x in force)
                    for ids in root.current_contacts:visited.update(ids)
                    if tracker:
                        pose,velocity=hull_pose(root);tracker.update(pose,velocity,len(visited)/len(self.static['track']),1.02+.08*completed+elapsed)
                    self.safety_state=dict(min_margin_m=minimum,max_path_error_m=maxpath,max_reference_overspeed_m_s=maxover,force_groups=stats);state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,progress=s,margin=gap,path_error=q['distance'],target=target,body_speed=max(math.hypot(*hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels)),forces=force,old_target=reference(s,path)[0],action=action.tolist()));
                    if not full:
                        self.record_crossing('gate',self.entry['gate'],before,root,len(trace));self.record_crossing('return',self.entry['return_gate'],before,root,len(trace))
                    problems=[]
                    if not all(math.isfinite(x) for x in (s,gap,maxbody,maxover,maxpath)):problems.append('NONFINITE')
                    if gap<.5:problems.append('MARGIN')
                    if maxpath>3:problems.append('PATH')
                    if maxover>4.85:problems.append('REFERENCE')
                    if maxbody>=100:problems.append('MODEL_BODY_DOMAIN')
                    if s-old_s<-.5 or s-old_s>max(5.,2*math.dist(root.center,before.center)):problems.append('PROJECTION')
                    if stats['launch']['peak']>2.5 or (i>=23 and stats['launch']['samples'] and stats['launch']['clipped']/stats['launch']['samples']>.15):problems.append('LAUNCH')
                    if stats['running']['peak']>ADMISSION or (stats['running']['samples'] and stats['running']['clipped']/stats['running']['samples']>.10):problems.append('RUNNING')
                    if problems:failure=dict(index=i+1,raw=k+1,episode_s=.08*completed+elapsed,violations=problems);stop=problems[0];break
                    if tracker and tracker.finish_time_s is not None:stop='MODEL_SOURCE_STYLE_FINISH';break
                    if full and 50+4*completed+len(trace)>=1224:stop='TIME_LIMIT';break
                    if full and s>path['length']+10 and tracker.finish_time_s is None:stop='ARC_WITHOUT_FINISH';break
                if failure or stop in ('MODEL_SOURCE_STYLE_FINISH','TIME_LIMIT','ARC_WITHOUT_FINISH'):break
                if not full and 'return' in self.crossings:break
        except BaseException as exc:
            self.save(D/f'{label}-interrupted-private.json',dict(error=type(exc).__name__+':'+str(exc),trace=trace,commands=commands,model_ticks=self.counter[0],cost=self.cost));raise
        clips,samples=history;trend=[];clip_peak=clips/samples if samples else 0.
        for q in trace:
            if q['index']>24:
                clips+=sum(z['clipped'] for z in q['forces']);samples+=4;clip_peak=max(clip_peak,clips/samples)
                if q['raw']==4 or q is trace[-1]:trend.append(dict(index=q['index'],clipped=clips,samples=samples,fraction=clips/samples))
        item=dict(crossings=self.crossings.copy(),dynamic_trigger_verified=self.trigger_verified,clipping_trajectory=trend,max_cumulative_clipping_fraction=clip_peak,label=label,stop=stop,pass_safety=(full or ('gate' in self.crossings and 'return' in self.crossings)) and failure is None and stop==('MODEL_SOURCE_STYLE_FINISH' if full else 'PROBE_COMPLETE'),raw_ticks=len(trace),actions=len(commands),completed_before=completed,force_groups=stats,min_margin_m=minimum,max_path_error_m=maxpath,max_reference_overspeed_m_s=maxover,max_body_speed_m_s=maxbody,mode_counts=modes,high_fraction=modes.get('HIGH',0)/max(1,sum(x for key,x in modes.items() if key!='FIXED_LAUNCH')),first_failure=failure,model_finish_episode_s=tracker.finish_time_s-1.02 if tracker and tracker.finish_time_s is not None else None)
        endstate=asdict(root);endstate.pop('roads');self.save(D/f'{label}-private.json',dict(summary=item,trace=trace,commands=commands,end_root_without_roads=endstate,end_progress=s,source_tracker=asdict(tracker) if tracker else None));self.outcomes.append(item);self.checkpoint();return item
    def pilot(self):
        item=self.simulate('fixed-segment-candidate',self.root(self.entry['root']),self.entry['completed'],tuple(self.entry['history']),set(),False,self.c['pilot_max_holds'])
        if not item['pass_safety']:return dict(passed=False,reason='RAW_SAFETY_OR_NO_COMMON_BOUNDARY',case=item)
        gains={};speed_checks={}
        for name,key in [('gate','baseline_gate'),('return','baseline_return')]:
            a=self.entry[key];b=item['crossings'][name];gains[name]=a['lower_s']-b['upper_s'];speed_checks[name]=b['speed']>=a['speed']-.15
        data=json.loads((D/'fixed-segment-candidate-private.json').read_text());root=self.root(data['end_root_without_roads']);history=list(self.entry['history'])
        for row in data['trace']:history[0]+=sum(z['clipped'] for z in row['forces']);history[1]+=4
        self.guard(6400);a,d=self.original_select(root,data['end_progress'],tuple(history));future=bool(a is not None);self.save(D/'pilot-fresh-return-witness-private.json',dict(action_exists=future,detail=d,executed=False));passed=all(v>=.02-1e-12 for v in gains.values()) and all(speed_checks.values()) and future
        return dict(passed=bool(passed),case=item,baseline551_saved_prefix_reused=True,baseline_model_ticks_recomputed=0,conservative_time_gain_s=gains,terminal_speed_pass=speed_checks,fresh_followup_certified=future,not_whole_lap_or_actual_gain=True)
    def full(self,kind):
        identity=json.loads((G/'retry/backup554_preparation.json').read_text());assert identity['passed'];assert json.loads((G/'retry/backup554_pilot_result.json').read_text())['passed']
        if kind=='cold':root=self.root(self.static['root']);completed=0;history=(0,0);visited=set(self.ledger['initial_visited'])
        else:
            cold=json.loads((G/'retry/backup554_cold_result.json').read_text());assert cold['passed'];case=json.loads(Path(self.ledger['checkpoint']).read_text());root=self.root(case['before_root_without_roads']);completed=self.ledger['completed_actions'];history=(0,352);visited=set(self.ledger['carry_visited'])
        item=self.simulate(kind+'-candidate',root,completed,history,visited,True,500);base=json.loads((G/('retry/joint541_'+kind+'_result.json')).read_text())['case'];gain=base['model_finish_episode_s']-item['model_finish_episode_s'] if item['pass_safety'] else None
        ms=round(base['model_finish_episode_s']*1000)-round(item['model_finish_episode_s']*1000) if item['pass_safety'] else None
        return dict(passed=bool(item['pass_safety'] and ms>=(500 if kind=='cold' else 0)),case=item,gain_vs541_s=gain,gain_vs541_ms=ms,effect_gate_unit='official_milliseconds',effect_threshold_ms=500 if kind=='cold' else 0,baseline541_reused=True,source_finish_is_model_estimate=True,native_executed=False)
    def run(self):
        from core.vendor.car_racing import CarRacing
        def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
        CarRacing.__init__=CarRacing.reset=CarRacing.step=poison;install_dispatch();tracking_module.tick=self.checked_tick;launch_module.tick=self.checked_tick
        def interrupt(*a):raise RuntimeError('PHASE_TIMER_CAP')
        signal.signal(signal.SIGPROF,interrupt);signal.setitimer(signal.ITIMER_PROF,self.cpu_cap);signal.signal(signal.SIGALRM,interrupt);signal.setitimer(signal.ITIMER_REAL,self.wall_cap);result={};error=None
        try:result=self.pilot() if self.phase=='pilot' else self.full(self.phase)
        except BaseException as exc:error=type(exc).__name__+':'+str(exc);result=dict(passed=False,technical_error=error);self.save(D/f'{self.phase}-error-private.json',dict(error=error,traceback=traceback.format_exc(),model_ticks=self.counter[0],cost=self.cost))
        finally:
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.checkpoint()
            out=dict(phase=self.phase,**result,cases=self.outcomes,model_integrator_ticks=self.counter[0],source_wheel_force_evaluations_in_integrator=4*self.counter[0],explicit_force_evaluations=self.cost['force_evaluations'],planner_cost=self.cost,CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall,native_actions=0,native_resets=0,research_remaining=22758,reserve=84000,reserve_used=0)
            self.save(G/f'retry/backup554_{self.phase}_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','cold','carry'),required=True);Stage(parser.parse_args().phase).run()
