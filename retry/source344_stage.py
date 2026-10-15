"""Identify the exact historical generator and register a 320-call cache."""
import argparse
import ast
import datetime
import time
import zipfile
from pathlib import Path
from retry.path271_run import read,save,sha
from retry.support342_stage import ROUTE

TRACKER='''
from retry.temporal_agent import TemporalRouteAgent
from retry.clearance_agent import road_and_obstacles
from retry.hud_feedback import decode_feedback_speed
original_tracked=TemporalRouteAgent.tracked_obstacles
tracker_record=None
support_state=[]
support_record=None
routing_evidence=None
act_step=0
confidence_enabled=json.loads((clean/'confidence342-config.json').read_text())['enabled']
def tracked_observer(self,image,speed):
    global tracker_record,support_state,support_record
    before_hazards=copy.deepcopy(self.hazards);old_image_exists=self.previous_image is not None;captured={}
    assert sys.getprofile() is None
    def capture(frame,event,arg):
        if event=='return' and frame.f_code is original_tracked.__code__:
            transform=frame.f_locals.get('transform')
            captured['affine']=None if transform is None else transform.tolist()
            captured['optical_reason']='accepted' if transform is not None else 'no_previous_image' if not old_image_exists else 'no_hazards' if not before_hazards else 'rejected_or_unavailable'
    sys.setprofile(capture)
    try:out=original_tracked(self,image,speed)
    finally:sys.setprofile(None)
    tracker_record=dict(before=before_hazards,after=copy.deepcopy(self.hazards),current_speed=float(decode_feedback_speed(image,speed)),direct=[list(map(float,p)) for p in road_and_obstacles(image)[1]],**captured)
    support_record=advance_evidence(tracker_record,support_state,act_step,image);support_state=support_record['after']
    return out
TemporalRouteAgent.tracked_obstacles=tracked_observer
'''


def verify(R):
    D=R/'stage344';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.pair343_stage import verify as previous
    previous(R);G=Path(__file__).resolve().parent.parent;D=R/'stage344';assert not D.exists();D.mkdir(mode=0o700);job=read(R/'stage306/collection/O2/job.json');cfg=job['config'];archive=Path(cfg['archive_path']);original=Path(cfg['worker_path']);assert sha(archive)==cfg['archive_sha256']=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937';assert sha(original)==cfg['worker_sha256']
    historical=read(R/'stage306/collection/O2/ready-private.json')
    for name,path in historical['policy_modules'].items():
        relative=str(Path(path).relative_to(R/'stage306/collection/O2/cpu/package'));assert historical['policy_module_sha256'][name]==cfg['members_sha256'][relative]
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())==set(cfg['members_sha256'])
        for name,wanted in cfg['members_sha256'].items():assert __import__('hashlib').sha256(z.read(name)).hexdigest()==wanted
        temporal=z.read('retry/temporal_agent.py').decode();assert 'y -= decode_feedback_speed(image, speed) * 0.08' in temporal and 'previous_yaw' not in temporal
        constants={}
        for node in ast.parse(z.read('retry/cem294_constants.py').decode()).body:
            if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
                try:constants[node.targets[0].id]=ast.literal_eval(node.value)
                except ValueError:pass
    logic=G/'retry/source344_logic.py';s342=(G/'retry/support342_logic.py').read_text();expected=s342.replace('"""Pixel-only birth evidence; flags never delete or modify tracked hazards."""','"""Same342birth rule; metadata follows the original296straight fallback only."""').replace("            delta=.08*(tracker['previous_yaw']+tracker['current_yaw'])/2\n            offset=np.array([x,y])-np.array([0.,tracker['current_speed']*.08]);c,s=np.cos(delta),np.sin(delta)\n            x,y=float(c*offset[0]+s*offset[1]),float(-s*offset[0]+c*offset[1])","            y-=tracker['current_speed']*.08");assert logic.read_text()==expected
    source=original.read_text();source=source.replace('agent = Agent()','agent = Agent()\n'+logic.read_text()+'\n'+TRACKER)
    start=source.index('def route_observer(');end=source.index('nominal_module.connected_route=route_observer',start);source=source[:start]+ROUTE+source[end:]
    source=source.replace('agent.reset(obs);history=[];pending=False;last_base=None','agent.reset(obs);history=[];pending=False;last_base=None;support_state=[];support_record=None;routing_evidence=None;act_step=0')
    marker='base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True';assert source.count(marker)==1;source=source.replace(marker,'act_step+=1\n                '+marker)
    source=source.replace('    response.update(rss_mib=',"    response['tracker_record']=tracker_record\n    response['support_record']=support_record\n    response['routing_evidence']=routing_evidence\n    response.update(rss_mib=")
    worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600);configs={}
    for mode,enabled in [('baseline',False),('candidate',True)]:
        constants_cfg=dict(cfg.get('constants',{}));constants_cfg['confidence342-config.json']=dict(enabled=enabled);configs[mode]=dict(cfg,worker_path=str(worker),worker_sha256=sha(worker),constants=constants_cfg)
    inputs=[original,archive,worker,logic,G/'retry/support342_logic.py',G/'retry/support342_stage.py',R/'stage306/collection/O2/job.json',R/'stage306/collection/O2/ready-private.json',R/'stage306/collection/O2/trace-private.jsonl',R/'stage306/collection/O2/observations-actions-private.npz',R/'stage334/O2/OFF-private.jsonl',R/'stage334/O2/GT-private.json',R/'stage343/summary-private.json',R/'stage296/champion-manifest.json',R/'project-effective-budget-v355.json',R/'research-deadline-current.json']
    inputs += [G/'retry'/n for n in ['source344_stage.py','source344_run.py','frozen_composite_runtime.py']]
    p=dict(stage=344,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],configs=configs,sandbox_path=read(R/'stage342/plan.json')['sandbox_path'],inputs=160,actor_cap=320,reset_cap=2,original_config=cfg,source_constants=constants,
        policy_identity='Exact historical306collection296archive and pedal306_worker, ready module hashes match archived job. Not334ON/H1. Native original had straight HUDspeedfallback, kept unchanged. Only source-lineage metadata follows that existing fallback; birth predicate exactly342.',
        state_scope='Original trace stored float64 nominal memory and features, not a full actor pickle. Reproduce stored memory/action/features; reconstruct original five-field worker state contract from exact pixels, qualified334OFFtracker and original command history, plus source lateral constants. Do not claim unavailable full original pickle/RNG comparison.',
        design='Original160stored observations first, baseline160thenqualify offline, thencandidate160. Same original frozen archive/models/detector/tracker/controller; only one fixed birth-road-neighbor hard-routing exclusion. Each own returned controls/history and normal memory. No step/coordinate/GT/future rule.',
        gate='Baseline original actions/features/memory/state contract and qualifiedtracker/path must reproduce beforecandidate. Pixel-only actor, no GT access. Any supported direct or birth-supported retained point withheld is a cache safety failure. Material/occlusion unknown. Store source outputs before offline validation so validator-only repair needs no duplicate actor calls.',
        recovery='Hard cap320actor calls/reset2, precharge each request and save responses. Offline checker repair can use saved outputs; policy/source reproduction failure remains implementation problem and cannot be passed by relaxing expectedbehavior. Any actual rerun must fit remainingcap, otherwise reportshortfall.',
        limits='343current334ON/H1wascontrol-unexposed; this explicitly different source-policy cache cannot reverse that result or prove actual safety/completion. No native or promotion automatically follows.',
        budget=dict(new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,parameter_sweeps=0,research_remaining=1116,final_reserved_actions=84000),methodology='Parent confirms both full originals re-reviewed before344; source identification,one hypothesis,same inputs,P3/P8,cheap falsification.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'call-budget.json',dict(actor_calls=0,resets=0,cap=320,reset_cap=2));print('344 exact296source registered; actor320/reset2/native0; originalstate scope explicit',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)
