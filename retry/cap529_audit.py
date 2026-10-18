"""Saved pair, disjoint event-clock bins and exact cap comparison; no propagation."""
import hashlib,json,math,time
from pathlib import Path
from retry.drive519_control import reference,drive
from retry.cap529_control import choose as cap_choose
from retry.response528_control import choose as fixed_choose
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response529-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/cap529_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    paths=json.loads((D/'frozen-paths-private.json').read_text());assert paths['comparison']==json.loads(Path('/workspace/haic-response528-private/frozen-paths-private.json').read_text())['candidate'];assert cap_choose is fixed_choose
    sources=[('528',Path('/workspace/haic-response528-private/cold-candidate-model-private.json'),paths['comparison']),('529',D/'cold-candidate-model-private.json',paths['candidate'])];results=[]
    for name,p,path in sources:
        data=json.loads(p.read_text());end=data['summary']['model_finish_episode_s'];labels={k:dict(time_s=0.,speed_integral=0.,force_sum=0.,wheel_samples=0.,fullgas_s=0.) for k in ('launch','source_forward','backward80','top_cap','curvature_transition')};bins=[0.]*12;cap=80 if name=='528' else 90
        static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());before=static['root'];s0=0.;distance=0.;above80=above85=0.;peak=0.
        for k,z in enumerate(data['trace']):
            w=max(0.,min((k+1)*.02,end)-k*.02)
            if not w:break
            v=math.hypot(*before['planar']['linear']['velocity']);sm=(s0+z['progress'])/2;target,ff=reference(sm,path);u=sm%path['length'];i=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=u),len(path['ds'])-1);label='launch' if z['index']<=24 else 'source_forward' if abs(ff-drive(path['launch_squared'][i]))<1e-7 else 'backward80' if abs(ff+80)<1e-7 else 'top_cap' if abs(target-cap)<1e-6 and abs(ff)<1e-8 else 'curvature_transition';a=z['action'];r=labels[label];r['time_s']+=w;r['speed_integral']+=v*w;r['force_sum']+=sum(t['ratio'] for t in z['forces'])*w/.02;r['wheel_samples']+=4*w/.02;r['fullgas_s']+=w*(a[1]==1.);distance+=math.dist(before['center'],z['root_without_roads']['center'])*w/.02;above80+=w*(v>=80);above85+=w*(v>=85);peak=max(peak,v)
            s1=z['progress']
            if s1>s0:
                for j in range(12):
                    left=-1e9 if j==0 else path['length']*j/12;right=1e9 if j==11 else path['length']*(j+1)/12;bins[j]+=w*max(0.,min(s1,right)-max(s0,left))/(s1-s0)
            else:bins[min(11,max(0,int(u/path['length']*12)))]+=w
            before=z['root_without_roads'];s0=s1
        for r in labels.values():r['mean_speed_m_s']=r.pop('speed_integral')/r['time_s'] if r['time_s'] else None;r['mean_force_ratio']=r.pop('force_sum')/r['wheel_samples'] if r['wheel_samples'] else None
        assert abs(sum(z['time_s'] for z in labels.values())-end)<1e-8 and abs(sum(bins)-end)<1e-8
        results.append(dict(name=name,model_event_finish_s=end,model_confirmation_elapsed_s=.02*len(data['trace']),event_interval_excludes_later_confirmation=True,labels=labels,twelve_disjoint_arc_bin_times_s=bins,actual_model_COM_chord_distance_m=distance,time_at_least80_m_s=above80,time_at_least85_m_s=above85,max_pre_force_COM_speed_m_s=peak))
    exact=results[0]['model_event_finish_s']-results[1]['model_event_finish_s'];r=json.loads((G/'retry/cap529_model_result.json').read_text());out=dict(source_input_pins_verified=True,comparison528_profile_exact=True,response_algorithm_object_identical=True,exact_cached_528_minus_529_model_event_s=exact,original_result_rounded18_literal_gain_s=r['direct_cap_cold_gain_vs528_s'],gain_field_roundoff_explanation='Modeldriverusedrounded18.00ratherthanexactcached17.999999999999705;2.95e-13isroundoffnotgain. Exactpairedsource-styleeventclocksareequal.',model_comparisons=results,twelve_bin_529_minus_528_s=[b-a for a,b in zip(results[0]['twelve_disjoint_arc_bin_times_s'],results[1]['twelve_disjoint_arc_bin_times_s'])],interpretation='Localcapentrygain+2.10m/peakspeed+9.67doesnotbecomefullmodelgain. Sourceforwardstilloccupiesmuchtime,andhighercapspendstimeacceleratingthenbraking; binshiftsareactualmodeltimedistributionnotisolatedcausallosses. Thisfixedroute/algorithm80->90caseonly;highercapsorothercontrollersnotrejected. Nextresearchpathlength/curvature,nocapsweep.',new_model_integrator_ticks=0,new_force_evaluations=0,native_actions=0,native_resets=0,research_remaining=24155,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<60 and out['wall_s']<90
    with (G/'retry/cap529_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
