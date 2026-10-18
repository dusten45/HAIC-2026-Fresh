"""Finite phase driver: pilot, cold, carry. Checkpoint every case/exit."""
import argparse,datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.brake536_control import choose,geometry_context,ADMISSION
from retry.frozen534_projection import initial_progress
from retry.drive519_control import project,steering,reference,force_rows,nominal
from retry.preview527_control import backup
from retry.closure524_control import tick
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose,tracker_for
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response536-private')


class Stage:
    def __init__(self,phase):
        self.phase=phase;self.cpu=time.process_time();self.wall=time.perf_counter();self.counter=[0];self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0);self.c=json.loads((G/'retry/brake536_contract.json').read_text());self.outcomes=[];self.current=None
        if (D/f'{phase}-STARTED.json').exists():raise RuntimeError('NO_PHASE_RETRY')
        for p,h in self.c['source_sha256'].items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
        for p,h in self.c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
        self.static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());self.paths=json.loads((D/'frozen-paths-private.json').read_text());self.ledger=json.loads(Path('/workspace/haic-response519-private/model-ledger-private.json').read_text());self.index=bounds(self.static['roads']);self.edge=boundary_index(self.static['boundary']);self.geometry=geometry_context(self.static,65000)
        assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==self.c['fixed_path_sha256']
        self.save(D/f'{phase}-STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/brake536_contract.json').read_bytes()).hexdigest()))
    def save(self,p,value,overwrite=False):
        data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        if len(list(D.iterdir()))>=8192 or sum(z.stat().st_size for z in D.iterdir())+len(data)>256*1024**2:raise RuntimeError('PRIVATE_CAP')
        if overwrite:
            q=p.with_suffix(p.suffix+'.tmp');q.write_bytes(data);q.replace(p)
        else:
            with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def guard(self,reserve=0):
        if time.process_time()-self.cpu>=600 or time.perf_counter()-self.wall>=720:raise RuntimeError('PHASE_COST_CAP')
        if self.counter[0]>=60000 or self.cost['force_evaluations']+reserve>300000:raise RuntimeError('PHASE_WORK_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.c['deadline_utc']):raise RuntimeError('DEADLINE')
    def checkpoint(self):
        self.save(D/f'{self.phase}-latest-cost-private.json',dict(current_case=self.current,completed_cases=len(self.outcomes),model_ticks=self.counter[0],cost=self.cost,CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall),True)
    def root(self,state):return load_root(dict(state,roads=self.static['root']['roads']))
    def select(self,root,s,history):
        self.guard(6400);action,detail=choose(root,self.paths['candidate'],self.paths['backup'],s,self.counter,self.cost,60000,history=history,geometry=self.geometry)
        if action is not None:
            final=next(x for x in detail['reports'] if x['mode']=='FINAL');assert detail['final_recertified'] and final['ok'] and final['peak']<=ADMISSION and final['min_footprint_margin_m']>=.5;assert action[0].tobytes()==np.float32(steering(root,self.paths['candidate'],s)).tobytes()
        return action,detail
    def simulate(self,label,root,completed,history,visited,full,holds):
        self.current=label;path=self.paths['candidate'];s=initial_progress(root,path,completed);tracker=tracker_for(self.static,root,set(visited),completed>0,1.02+.08*completed) if full else None;visited=set(visited);elapsed=0.;trace=[];commands=[];minimum=margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);maxpath=maxover=maxbody=0.;stats={x:dict(peak=0.,samples=0,clipped=0) for x in ('launch','running')};stats['running'].update(clipped=history[0],samples=history[1]);modes={};failure=None;stop='PROBE_COMPLETE' if not full else 'MAX500'
        try:
            for i in range(completed,min(500,completed+holds)):
                self.checkpoint();self.guard(6400)
                if i<24:action=np.array([steering(root,path,s),.32,0.],np.float32);detail=dict(mode='FIXED_LAUNCH')
                else:action,detail=self.select(root,s,(stats['running']['clipped'],stats['running']['samples']))
                if action is None:stop='NO_ADMISSIBLE_ACTION';failure=dict(index=i+1,reason=stop);commands.append(dict(index=i+1,detail=detail));break
                modes[detail['mode']]=modes.get(detail['mode'],0)+1;commands.append(dict(index=i+1,action=action.tolist(),detail=detail));root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
                for k in range(4):
                    self.guard(4);before=root;old_s=s;force=force_rows(root,action);self.cost['force_evaluations']+=4;root=tick(root,float(action[1]),float(action[2]),bounds(root.roads),self.counter);elapsed+=.02;q=project(root.center,path,s);s=q['s'];gap=margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);minimum=min(minimum,gap);maxpath=max(maxpath,q['distance']);target=reference(s,path)[0];over=math.hypot(*root.planar.linear.velocity)-target
                    if i>=24:maxover=max(maxover,over)
                    maxbody=max(maxbody,max(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels),math.hypot(*hull_pose(root)[1]));group='launch' if i<24 else 'running';z=stats[group];z['peak']=max(z['peak'],max(x['ratio'] for x in force));z['samples']+=4;z['clipped']+=sum(x['clipped'] for x in force)
                    for ids in root.current_contacts:visited.update(ids)
                    if tracker:
                        pose,velocity=hull_pose(root);tracker.update(pose,velocity,len(visited)/len(self.static['track']),1.02+.08*completed+elapsed)
                    state=asdict(root);state.pop('roads');trace.append(dict(index=i+1,raw=k+1,root_without_roads=state,progress=s,margin=gap,path_error=q['distance'],target=target,forces=force,action=action.tolist()));problems=[]
                    if gap<.5:problems.append('MARGIN')
                    if maxpath>3:problems.append('PATH')
                    if maxover>5:problems.append('REFERENCE')
                    if maxbody>=100:problems.append('MODEL_BODY_DOMAIN')
                    if s-old_s<-.5 or s-old_s>max(5.,2*math.dist(root.center,before.center)):problems.append('PROJECTION')
                    if stats['launch']['peak']>2.5 or (i>=23 and stats['launch']['samples'] and stats['launch']['clipped']/stats['launch']['samples']>.15):problems.append('LAUNCH')
                    if stats['running']['peak']>1.06 or (stats['running']['samples'] and stats['running']['clipped']/stats['running']['samples']>.10):problems.append('RUNNING')
                    if problems:failure=dict(index=i+1,raw=k+1,episode_s=.08*completed+elapsed,violations=problems);stop=problems[0];break
                    if tracker and tracker.finish_time_s is not None:stop='MODEL_SOURCE_STYLE_FINISH';break
                    if full and 50+4*completed+len(trace)>=1224:stop='TIME_LIMIT';break
                    if full and s>path['length']+10 and tracker.finish_time_s is None:stop='ARC_WITHOUT_FINISH';break
                if failure or stop in ('MODEL_SOURCE_STYLE_FINISH','TIME_LIMIT','ARC_WITHOUT_FINISH'):break
        except BaseException as exc:
            self.save(D/f'{label}-interrupted-private.json',dict(error=type(exc).__name__+':'+str(exc),trace=trace,commands=commands,model_ticks=self.counter[0],cost=self.cost));raise
        item=dict(label=label,stop=stop,pass_safety=failure is None and stop==('MODEL_SOURCE_STYLE_FINISH' if full else 'PROBE_COMPLETE'),raw_ticks=len(trace),actions=len(commands),completed_before=completed,force_groups=stats,min_margin_m=minimum,max_path_error_m=maxpath,max_reference_overspeed_m_s=maxover,max_body_speed_m_s=maxbody,mode_counts=modes,high_fraction=modes.get('HIGH',0)/max(1,sum(x for key,x in modes.items() if key!='FIXED_LAUNCH')),first_failure=failure,model_finish_episode_s=tracker.finish_time_s-1.02 if tracker and tracker.finish_time_s is not None else None)
        self.save(D/f'{label}-private.json',dict(summary=item,trace=trace,commands=commands));self.outcomes.append(item);self.checkpoint();return item
    def pilot(self):
        cases=json.loads((D/'roots-private.json').read_text());tests=[]
        for case in cases:
            self.current=case['label'];root=self.root(case['root_without_roads']);s=initial_progress(root,self.paths['candidate'],case['completed']);action,detail=self.select(root,s,(case['history']['clipped'],case['history']['samples']));old_backup=backup(root,self.paths['candidate'],self.paths['backup'],s);signed=lambda a:float(a[1]) if a[1]>0 else -float(a[2]);normal=case['label']=='normal141';normal_equal=not normal or action is not None and action.tolist()==case['old_action'];record=dict(label=case['label'],available=action is not None,mode=detail['mode'],fresh_final=detail.get('final_recertified',False),normal_original_action_equal=normal_equal,below_old_backup=bool(action is not None and signed(action)<signed(old_backup)),available_stronger_than_backup=any(x['ok'] and x['u']<signed(old_backup) for x in detail.get('trials',[])),FINAL=next((x for x in detail.get('reports',[]) if x['mode']=='FINAL'),None));tests.append(record);self.save(D/(case['label']+'-selection-private.json'),dict(summary=record,detail=detail,action=None if action is None else action.tolist()));self.checkpoint()
            if action is None or not normal_equal:break
        passed=len(tests)==5 and all(x['available'] and x['fresh_final'] and x['normal_original_action_equal'] for x in tests) and next(x for x in tests if x['label']=='actual33')['available_stronger_than_backup']
        if passed:
            for case in [x for x in cases if x['label']!='normal141']:
                item=self.simulate('bridge-'+case['label'],self.root(case['root_without_roads']),case['completed'],(case['history']['clipped'],case['history']['samples']),set(),False,12)
                if not item['pass_safety'] or item['raw_ticks']!=48:passed=False;break
        if passed:
            case=next(x for x in cases if x['label']=='normal141');item=self.simulate('normal141-recovery',self.root(case['root_without_roads']),140,(case['history']['clipped'],case['history']['samples']),set(),False,36);passed=item['pass_safety'] and item['raw_ticks']==144
        if passed:
            for case in json.loads((D/'risks-private.json').read_text()):
                item=self.simulate('regression-'+case['label'],self.root(case['root_without_roads']),case['index']-1,(case['history']['clipped'],case['history']['samples']),set(),False,24)
                if not item['pass_safety'] or item['raw_ticks']!=96:passed=False;break
        return dict(passed=passed,selection_tests=tests)
    def full(self,kind):
        pilot=json.loads((G/'retry/brake536_pilot_result.json').read_text());assert pilot['passed']
        if kind=='cold':root=self.root(self.static['root']);completed=0;history=(0,0);visited=set(self.ledger['initial_visited'])
        else:
            cold=json.loads((G/'retry/brake536_cold_result.json').read_text());assert cold['passed'];case=json.loads(Path(self.ledger['checkpoint']).read_text());root=self.root(case['before_root_without_roads']);completed=self.ledger['completed_actions'];history=(0,352);visited=set(self.ledger['carry_visited'])
        item=self.simulate(kind+'-candidate',root,completed,history,visited,True,500);old525=json.loads(Path('/workspace/haic-response525-private/'+('cold-governor-B-model-private.json' if kind=='cold' else 'carry-governor-B-model-private.json')).read_text())['summary'];old528=json.loads(Path('/workspace/haic-response528-private/cold-candidate-model-private.json' if kind=='cold' else '/workspace/haic-response535-private/carry-baseline528-model-private.json').read_text())['summary'];gain525=old525['model_finish_episode_s']-item['model_finish_episode_s'] if item['pass_safety'] else None;gain528=old528['model_finish_episode_s']-item['model_finish_episode_s'] if item['pass_safety'] else None
        return dict(passed=bool(item['pass_safety'] and gain525>=.50 and gain528>=.10 and item['high_fraction']>=.5),case=item,gain_vs525_s=gain525,gain_vs528_s=gain528)
    def run(self):
        from core.vendor.car_racing import CarRacing
        def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_IN_MODEL')
        CarRacing.__init__=CarRacing.reset=CarRacing.step=poison
        def interrupt(*a):raise RuntimeError('PHASE_TIMER_CAP')
        signal.signal(signal.SIGPROF,interrupt);signal.setitimer(signal.ITIMER_PROF,600);signal.signal(signal.SIGALRM,interrupt);signal.setitimer(signal.ITIMER_REAL,720);result={};error=None
        try:result=self.pilot() if self.phase=='pilot' else self.full(self.phase)
        except BaseException as exc:error=type(exc).__name__+':'+str(exc);result=dict(passed=False,technical_error=error);self.save(D/f'{self.phase}-error-private.json',dict(error=error,traceback=traceback.format_exc(),model_ticks=self.counter[0],cost=self.cost))
        finally:
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.checkpoint()
            out=dict(phase=self.phase,**result,cases=self.outcomes,model_integrator_ticks=self.counter[0],source_wheel_force_evaluations_in_integrator=4*self.counter[0],explicit_force_evaluations=self.cost['force_evaluations'],planner_cost=self.cost,CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall,native_actions=0,native_resets=0,research_remaining=23893,reserve=84000,reserve_used=0)
            self.save(G/f'retry/brake536_{self.phase}_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','cold','carry'),required=True);Stage(parser.parse_args().phase).run()
