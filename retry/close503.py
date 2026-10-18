"""Saved-only recovery after numpy.bool_ result formatting failure; no physics."""
import importlib.abc, json, math, sys, time
from dataclasses import replace
from pathlib import Path
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self,name,path=None,target=None):
        if name.startswith(('Box2D','core.vendor')):raise RuntimeError('CLOSE503_NO_PHYSICS')
sys.meta_path.insert(0,NoPhysics())
from retry.brake502_response import Wheel, wheel_response


def run():
    cpu=time.process_time();start=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response503-private')
    raw=json.loads((D/'bench-raw.json').read_text());assert len(raw)==18 and sum(len(r['ticks']) for r in raw)==72
    stats=lambda a:dict(count=len(a),RMSE=math.sqrt(sum(x*x for x in a)/len(a)),max_abs=max(map(abs,a)))
    cases={};force_error=[];omega_error=[];torque=[];stage={k:[] for k in ('frozen_geometry','heading','offset','friction')};per_fixture={};heading=offset=0.;changes=0
    for r in raw:
        end=r['ticks'][-1];cases.setdefault(r['fixture'],{})[r['arm']]=dict(error_m_s=math.hypot(*end['COM_after'])-r['target'],forecast_error_m_s=math.hypot(*end['COM_after'])-r['prediction'],hull_error_m_s=math.hypot(*end['hull_velocity'])-r['target'])
        first=[Wheel(**dict(w,offset=tuple(w['offset']))) for w in r['ticks'][0]['observed_before']['wheels']]
        per_fixture.setdefault(r['fixture'],{k:[] for k in stage})
        for tick in r['ticks']:
            measured=tick['observed_before'];v=tuple(measured['velocity'])
            for a,w0,wd in zip(tick['forces'],first,measured['wheels']):
                w=Wheel(**dict(wd,offset=tuple(wd['offset'])));after,f,_=wheel_response(w,v,0.,r['brake'])
                force_error.append(math.dist(f,a['vector']));omega_error.append(after.omega-tick['omega_after'][a['wheel']])
                torque.append(1.6*(tick['omega_after'][a['wheel']]-w.omega)-1.6*(a['omega_braked']-w.omega)+.02*a['f']*.54)
                if r['arm']=='response':
                    heading=max(heading,abs(w.heading-w0.heading));offset=max(offset,math.dist(w.offset,w0.offset));changes+=int(w.friction!=w0.friction)
                    # Actual current omega/v held common: isolate geometry/contact
                    # assumptions on this tick, not a replay of lost local stats.
                    x=replace(w0,omega=w.omega)
                    for key in stage:
                        if key=='heading':x=replace(x,heading=w.heading)
                        elif key=='offset':x=replace(x,offset=w.offset)
                        elif key=='friction':x=replace(x,friction=w.friction)
                        residual=math.dist(wheel_response(x,v,0.,r['brake'])[1],a['vector'])
                        stage[key].append(residual);per_fixture[r['fixture']][key].append(residual)
    errors={arm:stats([c[arm]['error_m_s'] for c in cases.values()]) for arm in ('scalar','response')}
    source_pass=max(force_error)<=1e-3 and max(map(abs,omega_error))<=1e-5
    passed=source_pass and errors['response']['RMSE']<=.5*errors['scalar']['RMSE'] and errors['response']['max_abs']<=.15 and max(abs(c['response']['hull_error_m_s']) for c in cases.values())<=.15
    result=dict(status='ROBUSTNESS_GATE_PASS' if passed else 'FROZEN_KINEMATICS_CANDIDATE_REJECTED',cases=cases,**errors,
        source_law_gate_pass=bool(source_pass),source_force_oracle_error_N=stats(force_error),source_omega_oracle_error_rad_s=stats(omega_error),same_tick_torque_identity_residual=stats(torque),
        saved_only_actual_current_omega_velocity_conditional_force_residual_N={k:stats(a) for k,a in stage.items()},per_fixture_conditional_force_residual_N={n:{k:stats(a) for k,a in s.items()} for n,s in per_fixture.items()},
        measured_heading_drift_rad=heading,measured_wheel_offset_drift_m_s=offset,measured_friction_changes=changes,
        worlds=18,closed_worlds=18,closure_evidence='All18 world-finally body/joint0 assertions precede saved bench-raw.json; raw saved after fixed loop',raw_ticks=72,live_worlds=0,
        execution_source_changed=False,physical_retry=0,formatter_failure='numpy.bool_ not JSON serializable at final result; complete private raw saved first',
        workload_charge=dict(worker_CPU_s_conservative=5.,worker_wall_s_conservative=5.,external_shell_wall_s=.322266297,closing_CPU_s=time.process_time()-cpu,closing_wall_s=time.perf_counter()-start),
        original_preregistered_closed_loop_substitution_summary_recovered=False,scope='New synthetic fixtures only; no old501 raw or track evidence',research_remaining=26027,reserve=84000,reserve_used=0,native_actions_resets_seeds_HOLDOUT_SEALED=0)
    with (G/'retry/brake503_result.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','per_fixture_conditional_force_residual_N')},indent=2))


if __name__=='__main__':run()
