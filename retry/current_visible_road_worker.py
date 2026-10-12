"""Build a road-only privileged diagnostic around a frozen actual-call observer.

The archived Agent and its pixel obstacle/HUD inputs stay unchanged. Two road
threshold statements receive a fifth, evaluator-supplied binary plane. This is
research instrumentation, never a legal pixel-only submission candidate.
"""
import hashlib
from pathlib import Path


OBSERVER_SHA256 = '4afda780a78309da90e7f50cbe926520b2bc09908599923e447966b95dc354ea'

INSTALL = '''from agent import Agent
import copy
import runpy

boundary_source = clean / 'boundary.py'
boundary = runpy.run_path(str(boundary_source))
set_road_mask, _, _, boundary_receipt = boundary['install_mask_boundary'](
    sys.modules['retry.connected_agent'])
probe_steps = set(json.loads((clean / 'diagnostic.json').read_text())['route_shadow_steps'])
act_index = 0
'''

SHADOW = '''
def route_shadow(obs, actual_mask, response):
    # One pure route query: reuse actual tracked obstacles, HUD speed and the
    # PRE-controller memory. Never call perception, tracker or Agent again.
    old_route = copy.deepcopy(route_observed)
    old_counts = dict(call_counts)
    old_selection = copy.deepcopy(getattr(connected, 'LAST_CONNECTION_EVALUATION', None))
    memory_before = (controller_state(), np.asarray(agent.hazards).tobytes(),
                     agent.previous_image.tobytes())
    cp = response['contact_probe']
    original_mask = ((obs[-1] > .32) & (obs[-1] < .47)).astype(np.uint8)
    try:
        set_road_mask(original_mask)
        path = original_route(obs[-1], response['speed_constraint_probe']['tracked_obstacles_body'],
            speed=cp['old_HUD_speed_m_s'], previous_steer=cp['controller_before']['previous_steer'])
        point = original_target(path, cp['old_HUD_speed_m_s'])
        raw = None
        requested = cp['controller_before']['previous_steer']
        if point is not None:
            x, forward = map(float, point)
            curvature = 2*x/max(forward*forward+x*x, 1e-6)
            raw = float(np.clip(np.arctan(3.24*curvature), -.4, .4))
            requested = .8*raw + .2*requested
        comparison = dict(step=act_index,
            actual_path=response['speed_constraint_probe']['selected_path_body'],
            pixel_mask_shadow_path=np.asarray(path, np.float64).reshape(-1,2).tolist(),
            actual_selection=copy.deepcopy(response['connection_selection']),
            pixel_mask_shadow_selection=copy.deepcopy(connected.LAST_CONNECTION_EVALUATION),
            actual_raw_steer=None if cp['curvature'] is None else float(np.clip(np.arctan(3.24*cp['curvature']),-.4,.4)),
            actual_requested_steer=float(response['action'][0]),
            pixel_mask_shadow_raw_steer=raw,
            pixel_mask_shadow_requested_steer=float(np.float32(requested)),
            same_image_tracked_obstacles_HUD_and_previous_steer=True,
            scope='Unexecuted pure pixel-road route query on the actual oracle trajectory; no extra Agent, detector, tracker or controller call.')
    finally:
        set_road_mask(actual_mask)
        route_observed.clear(); route_observed.update(old_route)
        call_counts.clear(); call_counts.update(old_counts)
        connected.LAST_CONNECTION_EVALUATION = old_selection
    assert memory_before == (controller_state(), np.asarray(agent.hazards).tobytes(), agent.previous_image.tobytes())
    return comparison

'''


def build(observer_path, destination):
    source = Path(observer_path).read_text()
    assert hashlib.sha256(source.encode()).hexdigest() == OBSERVER_SHA256

    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old
        source = source.replace(old, new)

    replace('from agent import Agent\n', INSTALL)
    replace("modules = {name:str(Path(module.__file__).resolve())", SHADOW + "modules = {name:str(Path(module.__file__).resolve())")
    replace("'observer_extra_policy_calls':0,'observer_extra_vision_calls':0,'observer_model_calls':0,",
        "'observer_extra_policy_calls':0,'observer_extra_vision_calls':0,'observer_model_calls':0,\n"
        "                  'privileged_road_input':True,'submission_candidate':False,\n"
        "                  'input_contract':'four unchanged official planes plus binary visible-road diagnostic plane',\n"
        "                  'mask_boundary':boundary_receipt,\n"
        "                  'boundary_sha256':hashlib.sha256(boundary_source.read_bytes()).hexdigest(),")
    replace("    obs = np.frombuffer(base64.b64decode(request['observation']),dtype=np.float32).reshape(4,84,84).copy()",
        "    packed = np.frombuffer(base64.b64decode(request['observation']),dtype=np.float32).reshape(5,84,84)\n"
        "    obs = packed[:4].copy()\n"
        "    assert np.isin(packed[4], [0.,1.]).all()\n"
        "    supplied_mask = packed[4].astype(np.uint8)\n"
        "    set_road_mask(supplied_mask)")
    replace("        agent.reset(obs)", "        act_index = 0\n        agent.reset(obs)")
    replace("        assert request['op'] == 'act'", "        assert request['op'] == 'act'\n        act_index += 1")
    replace("    response.update(rss_mib=", "    response['road_input_receipt'] = dict(\n"
        "        original_four_planes_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),\n"
        "        supplied_mask_sha256=hashlib.sha256(supplied_mask.tobytes()).hexdigest(),\n"
        "        privileged_road_input=True)\n"
        "    if request['op']=='act' and act_index in probe_steps:\n"
        "        response['road_route_shadow'] = route_shadow(obs, supplied_mask, response)\n"
        "    response.update(rss_mib=")
    compile(source, str(destination), 'exec')
    with Path(destination).open('x') as f:
        f.write(source)
    Path(destination).chmod(0o600)
    return dict(original_observer_sha256=OBSERVER_SHA256,
        worker_sha256=hashlib.sha256(source.encode()).hexdigest(),
        archived_policy_files_changed=0, road_threshold_sites=2,
        fifth_plane='B=A & ~O; evaluator must enforce current view and renderer occlusion',
        original_obstacle_HUD_images_unchanged=True, privileged_diagnostic=True)
