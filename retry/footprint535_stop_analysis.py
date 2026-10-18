"""Pure saved-certificate/domain classification, no rollout or force calls."""
import json,time
from pathlib import Path
from retry.plan513_model import load_root
from retry.frozen534_projection import initial_progress
from retry.lap518_control import nominal
from retry.preview527_control import backup
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response535-recovery-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();s=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());a=json.loads((D/'stop-actual-33-private.json').read_text());b=json.loads((D/'stop-model-33-private.json').read_text());root=load_root(dict(json.loads((D/'action-candidate-032.json').read_text())['after_root_without_roads'],roads=s['root']['roads']));progress=initial_progress(root,paths['candidate'],32);high=nominal(root,paths['candidate'],progress);low=backup(root,paths['candidate'],paths['backup'],progress);signed=lambda x:float(x[1]) if x[1]>0 else -float(x[2]);lower,upper=signed(low),signed(high);safe=[x for x in a['grid'] if x['report']['ok']];inside=sum(lower<=x['u']<=upper for x in safe);below=sum(x['u']<lower for x in safe);above=sum(x['u']>upper for x in safe);trialsa=a['detail']['trials'];trialsb=b['detail']['trials']
    out=dict(actual33_source_response_candidates=len(trialsa),actual33_safe_in_sampled_interval=sum(x['ok'] for x in trialsa),actual33_min_attempted_force_peak=min(x['peak'] for x in trialsa),model33_min_attempted_force_peak=min(x['peak'] for x in trialsb),force_admission=1.06,actual33_full_grid_safe_count=len(safe),safe_full_grid_inside_source_response_interval=inside,safe_full_grid_below_backup=below,safe_full_grid_above_nominal=above,safe_full_grid_min_forecast_margin_m=min(x['report']['min_footprint_margin_m'] for x in safe),safe_full_grid_max_force_peak=max(x['report']['peak'] for x in safe),scope='Saveddataonly. TwoavailableforecastcommandsdoNOTproveactualsafecontinuation;nativepairnotrepeated. Interval/numericalcoverageproblemnotproofsteering/pathrequired. Nothresholdrelaxation/controllerchange.',model_ticks=0,force_evaluations=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    with (G/'retry/footprint535_stop_analysis.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
