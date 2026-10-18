"""Read-only actual518 decomposition; no trajectory/model integration."""
import json,math,time,hashlib,datetime,signal
from pathlib import Path
from retry.lap518_control import path_for,project,reference
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response519-private')

def run():
    t=time.perf_counter();cpu=time.process_time();c=json.loads((G/'retry/audit519_contract.json').read_text())
    def guard(*a):
        if time.process_time()-cpu>=60 or time.perf_counter()-t>=90:raise RuntimeError('ANALYSIS_CAP')
    signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,90)
    for n,h in c['inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());native=json.loads(Path('/workspace/haic-response518-private/native-full-records-private.json').read_text());offset=0;results=[]
    for arm in native:
        budget=arm['budget'];path=path_for(static,budget);L=path['length'];count=arm['reset_ticks']+sum(x['raw_ticks'] for x in arm['rows']);rows=[json.loads(Path('/workspace/haic-response518-private/raw-%04d.json'%i).read_text()) for i in range(offset+1,offset+count+1)];offset+=count;epoch=rows[arm['reset_ticks']-1]['time'];end=arm['official_finish_episode_s']
        def empty():return dict(time_s=0.,distance_m=0.,speed_integral=0.,low40_s=0.,gas_s=0.,brake_s=0.,coast_s=0.,force_peak=0.,force_sum=0.,wheel_samples=0.,clipped_wheels=0.,min_margin_m=1e9,curvature_integral=0.)
        limits={k:empty() for k in ('fixed_launch','forward25','backward45','top80','curvature_or_transition')};zones={k:empty() for k in ('fixed_launch','corner','entry20','exit20','straight','transition')};bins=[empty() for _ in range(12)];joint={};samples=[]
        curve_s=[s for s,k in zip(path['arcs'],path['curvature']) if abs(k)>=.02]
        def add(z,r,w,dist,speed,k,action):
            z['time_s']+=w;z['distance_m']+=dist*w/.02;z['speed_integral']+=speed*w;z['low40_s']+=w*(speed<40);z['gas_s']+=w*(action[1]>0);z['brake_s']+=w*(action[2]>0);z['coast_s']+=w*(action[1]==0 and action[2]==0);z['min_margin_m']=min(z['min_margin_m'],r['margin']);z['curvature_integral']+=abs(k)*w
            for f in r['forces']:z['force_peak']=max(z['force_peak'],f['ratio']);z['force_sum']+=f['ratio']*w/.02;z['wheel_samples']+=w/.02;z['clipped_wheels']+=(f['ratio']>1)*w/.02
        for r in rows:
            guard()
            if r['phase']!='action':continue
            lo=r['time']-epoch-.02;hi=r['time']-epoch;w=max(0.,min(hi,end)-max(lo,0.))
            if w<=0:continue
            s0=project(r['before_position'],path,r['station'])['s'];s1=r['station'];sm=(s0+s1)/2;s=sm%L;i=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=s),len(path['ds'])-1);target,ff=reference(sm,path);k=path['curvature'][i];action=arm['rows'][r['action']-1]['action'];speed=math.hypot(*r['before']['velocity']);dist=math.dist(r['before_position'],r['position'])
            if r['action']<=24:limit=zone='fixed_launch'
            else:
                limit='forward25' if abs(ff-25)<1e-8 else 'backward45' if abs(ff+45)<1e-8 else 'top80' if abs(target-80)<1e-7 and abs(ff)<1e-8 else 'curvature_or_transition'
                ahead=min((v-s)%L for v in curve_s);behind=min((s-v)%L for v in curve_s)
                zone='corner' if abs(k)>=.02 else 'entry20' if ahead<=20 else 'exit20' if behind<=20 else 'straight' if abs(k)<=.005 else 'transition'
            add(limits[limit],r,w,dist,speed,k,action);add(zones[zone],r,w,dist,speed,k,action);add(joint.setdefault(zone+'|'+limit,empty()),r,w,dist,speed,k,action)
            # Per20ms linear arc split for12bins; seam/end excursions assigned
            # toadjacent first/lastbin, never counted as a newlap.
            if s1>s0:
                for j in range(12):
                    left=-1e9 if j==0 else L*j/12;right=1e9 if j==11 else L*(j+1)/12;fraction=max(0.,min(s1,right)-max(s0,left))/(s1-s0)
                    if fraction:add(bins[j],r,w*fraction,dist,speed,k,action)
            else:add(bins[min(11,max(0,int(s/L*12)))],r,w,dist,speed,k,action)
            samples.append(dict(index=r['action'],s=s,time=hi,speed=speed,target=target,ff=ff,limit=limit,zone=zone,gas=action[1],brake=action[2],margin=r['margin']))
        def finish(z):
            T=z.pop('time_s');v=z.pop('speed_integral');k=z.pop('curvature_integral');fs=z.pop('force_sum');n=z['wheel_samples'];return dict(time_s=T,mean_speed_m_s=v/T if T else None,mean_abs_curvature=k/T if T else None,mean_force_ratio=fs/n if n else None,**z)
        limits={k:finish(v) for k,v in limits.items()};zones={k:finish(v) for k,v in zones.items()};bins=[finish(v) for v in bins];joint={k:finish(v) for k,v in joint.items()}
        assert abs(sum(x['time_s'] for x in limits.values())-end)<1e-8 and abs(sum(x['time_s'] for x in bins)-end)<1e-8
        q=path['launch_squared'];clock=sum(2*d/(math.sqrt(q[i])+math.sqrt(q[i+1])) for i,d in enumerate(path['ds']))
        results.append(dict(budget=budget,actual_official_lap_s=end,reference_path_length_m=L,scalar_reference_clock_s=clock,scalar_clock_is_not_feasible_or_optimal_bound=True,actual_minus_reference_clock_s=end-clock,limits=limits,zones=zones,bins=bins,joint=joint))
        (D/('actual-'+str(int(budget))+'-labels-private.json')).write_text(json.dumps(samples)+'\n')
    old=json.loads((G/'retry/diagnostic499_result.json').read_text())
    result=dict(actual=results,public_history=dict(old_actual_s=old['lap_s'],old_canonical_path_length_m=old['canonical_line_length_m'],old_original_scalar_clock_s=old['reference_clocks']['original_full_s'],old_P4_scalar_clock_s=old['reference_clocks']['P4_full_s'],verified_code_differences=['racing258_plan:16coefficient splineoffsetline optimizedfixedbudget193+objectives,notGaussianwaypointavoid','oldprofile:top100,source-dependent drive min35.0189/power andbrake91.1687; currenttop80/forward25/back45','pace268/417:~1.5paceandP4projection vs currentbudget100directcurvature; oldlateral87.648beforepace; gain1.5 vs current2'],track_or_state_equivalence_verified=False,old_raw_restored=False),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,native_actions=0,native_resets=0,model_integrator_ticks=0,research_remaining=24938,reserve=84000,reserve_used=0)
    (G/'retry/audit519_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(CPU_s=result['CPU_s'],wall_s=result['wall_s'],actual=[dict(budget=x['budget'],lap=x['actual_official_lap_s'],clock=x['scalar_reference_clock_s'],limits=x['limits']) for x in results]),indent=2))

if __name__=='__main__':run()
