"""Saved525 actual time partitions and governor reasons; no new simulation."""
import datetime,hashlib,json,math,time
from pathlib import Path
from retry.drive519_control import project,reference,drive,nominal
from retry.governor525b_control import path_for
from retry.plan513_model import load_root
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response526-private');OLD=Path('/workspace/haic-response525-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/audit526_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    for n,h in json.loads((D/'input-manifest-private.json').read_text()).items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());arm=json.loads((OLD/'native-full-records-private.json').read_text())[1];path=path_for(static,'governor');L=path['length'];offset=51+1024+51;raw=[json.loads((OLD/f'raw-{i:04d}.json').read_text()) for i in range(offset+1,offset+921)];epoch=1.02;end=arm['official_finish_episode_s']
    def blank():return dict(time_s=0.,speed_integral=0.,distance_m=0.,force_integral=0.,force_samples=0.,peak=0.,clipped_integral=0.,brake_integral=0.,acceleration_integral=0.,deceleration_integral=0.,low40_s=0.,high75_s=0.)
    limits={k:blank() for k in ('launch','source_forward','backward45','top80','curvature_transition')};pedals={k:blank() for k in ('launch','gas','brake','coast')};zones={k:blank() for k in ('launch','corner','entry20','exit20','straight_transition')};bins=[blank() for _ in range(12)];curve=[s for s,k in zip(path['arcs'],path['curvature']) if abs(k)>=.02];backup=[];samples=[];brake_running=[];COMdistance=0.;maxspeed=0.
    def add(z,r,w,v,distance,a):
        z['time_s']+=w;z['speed_integral']+=w*v;z['distance_m']+=distance*w/.02;z['low40_s']+=w*(v<40);z['high75_s']+=w*(v>=75);z['brake_integral']+=w*a[2]
        if r['forces']:
            z['force_integral']+=w*sum(f['ratio'] for f in r['forces']);z['force_samples']+=w*4;z['peak']=max(z['peak'],max(f['ratio'] for f in r['forces']));z['clipped_integral']+=w*sum(f['ratio']>1 for f in r['forces']);unit=[x/v for x in r['before']['velocity']] if v else [0.,0.];acc=sum(sum(f['vector'][j]*unit[j] for j in range(2)) for f in r['forces'])/r['before']['mass'];z['acceleration_integral']+=w*acc;z['deceleration_integral']+=w*max(0.,-acc)
    for r in raw:
        lo=r['time']-epoch-.02;hi=r['time']-epoch;w=max(0.,min(hi,end)-max(lo,0.))
        if w<=0:continue
        s0=project(r['before_position'],path,r['station'])['s'];s1=r['station'];s=((s0+s1)/2)%L;i=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=s),len(path['ds'])-1);target,ff=reference((s0+s1)/2,path);q=path['launch_squared'][i];a=arm['rows'][r['action']-1]['action'];v=math.hypot(*r['before']['velocity']);distance=math.dist(r['before_position'],r['position']);COMdistance+=distance*w/.02;maxspeed=max(maxspeed,v)
        if r['action']<=24:lim=ped=zone='launch'
        else:
            lim='source_forward' if abs(ff-drive(q))<1e-7 else 'backward45' if abs(ff+45)<1e-7 else 'top80' if abs(target-80)<1e-6 and abs(ff)<1e-8 else 'curvature_transition';ped='gas' if a[1]>0 else 'brake' if a[2]>0 else 'coast';ahead=min((t-s)%L for t in curve);behind=min((s-t)%L for t in curve);zone='corner' if abs(path['curvature'][i])>=.02 else 'entry20' if ahead<=20 else 'exit20' if behind<=20 else 'straight_transition'
        for z in (limits[lim],pedals[ped],zones[zone]):add(z,r,w,v,distance,a)
        if s1>s0:
            for j in range(12):
                left=-1e9 if j==0 else L*j/12;right=1e9 if j==11 else L*(j+1)/12;f=max(0.,min(s1,right)-max(s0,left))/(s1-s0)
                if f:add(bins[j],r,w*f,v,distance,a)
        else:add(bins[min(11,max(0,int(s/L*12)))],r,w,v,distance,a)
        samples.append(dict(index=r['action'],limit=lim,pedal=ped,zone=zone,time=r['time']-epoch,station=s,speed=v,reference=target))
    def finish(z):
        t=z.pop('time_s');n=z.pop('force_samples');speed=z.pop('speed_integral');force=z.pop('force_integral');brake=z.pop('brake_integral');acc=z.pop('acceleration_integral');dec=z.pop('deceleration_integral');clip=z.pop('clipped_integral');return dict(time_s=t,mean_speed_m_s=speed/t if t else None,mean_force_ratio=force/n if n else None,clip_fraction=clip/n if n else None,mean_brake=brake/t if t else None,mean_source_projected_acceleration_m_s2=acc/t if t else None,mean_source_deceleration_m_s2=dec/t if t else None,**z)
    limits={k:finish(v) for k,v in limits.items()};pedals={k:finish(v) for k,v in pedals.items()};zones={k:finish(v) for k,v in zones.items()};bins=[finish(v) for v in bins]
    for part in (limits,pedals,zones):assert abs(sum(z['time_s'] for z in part.values())-end)<1e-8
    assert abs(sum(z['time_s'] for z in bins)-end)<1e-8
    for record in arm['rows']:
        if record['governor_mode']!='BACKUP':continue
        data=json.loads((OLD/f"action-governor-{record['index']:03d}.json").read_text());state=data['before_root_without_roads'];state['roads']=static['root']['roads'];root=load_root(state);s=project(root.center,path)['s'];high=nominal(root,path,s);a=record['action'];report=data['governor_detail']['reports'][0];backup.append(dict(index=record['index'],rejection=report['reason'],rejected_forecast_peak=report['peak'],rejection_after_predicted_raw_ticks=report['model_ticks'],gas_reduction=float(high[1])-a[1],brake_increase=a[2]-float(high[2]),mode='BRAKE_INCREASE' if a[2]>high[2]+1e-9 else 'GAS_REDUCTION',actual_current_hold_peak=max(f['ratio'] for r in raw if r['action']==record['index'] for f in r['forces'])))
    assert len(backup)==7
    out=dict(actual_official_finish_s=end,partitions_are_separate_views_do_not_add_across_views=True,causal_time_loss_or_recoverable_gain_not_established=True,reference_path_length_m=L,actual_COM_chord_distance_m=COMdistance,actual_max_speed_m_s=maxspeed,limits=limits,pedals=pedals,zones=zones,twelve_arc_bins=bins,governor_backup_holds=backup,backup_time_s=.56,scalar_clock_s=sum(2*d/(math.sqrt(path['launch_squared'][i])+math.sqrt(path['launch_squared'][i+1])) for i,d in enumerate(path['ds'])),scalar_clock_is_not_feasible_or_optimal_bound=True,model_integrator_ticks=0,force_evaluations=0,native_actions=0,native_resets=0,research_remaining=24155,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<60 and out['wall_s']<90
    with (D/'actual-labels-private.json').open('x') as f:json.dump(samples,f,indent=2)
    (D/'actual-labels-private.json').chmod(0o600)
    with (G/'retry/audit526_result.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
