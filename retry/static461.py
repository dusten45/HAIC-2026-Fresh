"""Single combined saved audit: reproduction, no physics, budget and root binding."""
import copy,hashlib,json,time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import sys


def run(root):
    from retry import analyze461,budget461,diagnose
    from retry.source_vehicle_transition import SourceVehicleTransition
    from retry.terminal410_model import TerminalVehicleTransition
    import Box2D
    start,cpu=time.perf_counter(),time.process_time();directory=Path(__file__).resolve().parent
    before=json.loads((directory/'structural461_result.json').read_text());plan=json.loads((directory/'design461_next.json').read_text())
    forbidden=[]
    with ExitStack() as stack:
        for cls in [SourceVehicleTransition,TerminalVehicleTransition]:
            for name in ['__init__','step']:
                forbidden.append(stack.enter_context(patch.object(cls,name,side_effect=AssertionError('461_FORBIDDEN_PHYSICS'))))
        forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('461_FORBIDDEN_NATIVE'))))
        forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('461_FORBIDDEN_WORLD'))))
        after=analyze461.run(root)
        for mock in forbidden:mock.assert_not_called()
    a,b=copy.deepcopy(before),copy.deepcopy(after)
    a.pop('storage');b.pop('storage');assert a==b
    planned=budget461.calculate(plan);assert (planned['ticks'],planned['worlds'])==(43650,839)
    for item in after['data'].values():
        z=item['qualified_s'];assert abs(sum(z[k] for k in ['reference_s','speed_tracking_s','heading_s','body_slip_correction_s','origin_COM_correction_s','geometry_sampling_residual_s'])-z['dt'])<1e-10
        assert item['formula_max_float32_pedal_error']==0
    assert after['next_root_binding']['secant_fullgas_float32_alias'] and after['next_root_binding']['root_state_memory_ledger_binding_passed']
    assert planned['empirical_raw_bytes_at_hard_with_margin_and_reserve']<after['storage']['/tmp']['free']
    out=dict(stage=461,passed=True,new_actual_actions=0,new_model_ticks=0,new_worlds=0,new_resets=0,scientific_reproduction_exact=True,constructors_and_steps_forbidden=True,clock_components_close=True,nominal_pedals_float32_exact=True,next_root_binding_passed=True,budget=planned,contract_json_sha256=hashlib.sha256((directory/'design461_next.json').read_bytes()).hexdigest(),storage_estimate_fits_current_tmp=True,storage_guaranteed=False,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start)
    (directory/'structural461_gate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':run(Path(sys.argv[1]).resolve())
