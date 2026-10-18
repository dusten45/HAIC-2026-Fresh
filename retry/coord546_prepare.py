"""Confirm stored545 contract mismatch; freeze same feasible problem for546."""
import datetime,hashlib,json,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response545-private');O=Path('/workspace/haic-response546-private');O.mkdir(mode=0o700,exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=read(G/'retry/shoot545_recovery_result.json');floor=r['baseline']['min_margin_m']-.002;points=[read(p)['summary'] for p in sorted(D.glob('rollout-*-private.json'))];feasible=[p for p in points if p['feasible']];samefloor=[p for p in feasible if p['min_margin_m']>=floor]
 for name in ('entry-private.json','gate-private.json','frozen-paths-private.json','fresh-feasible541-baseline-private.json'):
  p=O/name
  with p.open('xb') as f:f.write((D/name).read_bytes())
  p.chmod(0o600)
 out=dict(status='STORED545_CHECK_AND546_INPUT_FREEZE',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),unified_margin_floor_m=floor,stored545_feasible_points=len(feasible),stored545_points_satisfying_final_floor=len(samefloor),diagnostic_best_gain_original_floor_s=r['baseline']['objective_s']-min(p['objective_s'] for p in feasible),diagnostic_best_gain_unified_floor_s=r['baseline']['objective_s']-min(p['objective_s'] for p in samefloor),common_plane_baseline_hold=r['baseline']['crossing']['time_s']/.08,old_fixed_tail_start_after_hold=20,old_solver_iterations=6,old_solver_converged=False,full_lap_cost_correction=dict(naive_full_replay=343*684,causal_prefix_caching_forward=684+2*4*sum(range(1,172)),not_an_impossibility_lower_bound=True,actually_executed=False),private_inputs_sha256={str(p):sha(p) for p in O.glob('*private.json')},new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/coord546_preparation.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
