"""Freeze compatible saved TRAIN corpus and fallback-only archives/observer."""
import argparse
import datetime
import json
import zipfile
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

OBSERVER='''
from retry.temporal_agent import TemporalRouteAgent
from retry.clearance_agent import road_and_obstacles
original_tracked=TemporalRouteAgent.tracked_obstacles
tracker_record=None
def tracked_observer(self,image,speed):
    global tracker_record
    before_hazards=copy.deepcopy(self.hazards)
    previous_yaw=float(decode(self.previous_image.astype(np.float32)/255)[5]) if self.previous_image is not None else None
    old_image_exists=self.previous_image is not None
    captured={}
    assert sys.getprofile() is None
    def capture(frame,event,arg):
        if event=='return' and frame.f_code is original_tracked.__code__:
            transform=frame.f_locals.get('transform')
            captured['affine']=None if transform is None else transform.tolist()
            captured['optical_reason']='accepted' if transform is not None else 'no_previous_image' if not old_image_exists else 'no_hazards' if not before_hazards else 'rejected_or_unavailable'
    sys.setprofile(capture)
    try:out=original_tracked(self,image,speed)
    finally:sys.setprofile(None)
    tracker_record=dict(before=before_hazards,after=copy.deepcopy(self.hazards),previous_yaw=previous_yaw,current_yaw=float(decode(image)[5]),current_speed=float(decode_feedback_speed(image,speed)),direct=[list(map(float,p)) for p in road_and_obstacles(image)[1]],**captured)
    return out
TemporalRouteAgent.tracked_obstacles=tracked_observer
'''


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage334';assert not D.exists();D.mkdir(mode=0o700)
    cfgs=read(R/'stage330/artifacts-private.json');baseworker=Path(read(R/'stage331/plan.json')['config']['worker_path']);source=baseworker.read_text();assert 'from retry.hud248_features import decode' in source
    # Install after decode/helper imports, before readiness/act; no policy attrs added.
    marker="cv2_module.setRNGSeed=seed_observer";assert source.count(marker)==1;source=source.replace(marker,marker+'\n'+OBSERVER)
    source=source.replace("response.update(rss_mib=", "response['tracker_record']=tracker_record\n    response.update(rss_mib=")
    worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600)
    configs={}
    oldline='                y -= decode_feedback_speed(image, speed) * 0.08'
    newline='''                assert self.previous_image is not None
                previous_yaw=float(decode(self.previous_image.astype(np.float32)/255)[5])
                current_yaw=float(decode(image)[5])
                delta=.08*(previous_yaw+current_yaw)/2
                offset=np.array([x,y])-np.array([0.,decode_feedback_speed(image,speed)*.08])
                c,s=np.cos(delta),np.sin(delta)
                x,y=float(c*offset[0]+s*offset[1]),float(-s*offset[0]+c*offset[1])'''
    for kind,original in cfgs.items():
        configs[kind]={}
        for enabled in [False,True]:
            with zipfile.ZipFile(original['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
            if enabled:
                code=members['retry/temporal_agent.py'].decode();assert code.count(oldline)==1
                code=code.replace('import numpy as np','import numpy as np\nfrom retry.hud248_features import decode').replace(oldline,newline);members['retry/temporal_agent.py']=code.encode()
            f=D/'artifacts'/kind/('ON' if enabled else 'OFF');f.mkdir(parents=True,mode=0o700);archive=f/'policy.zip'
            with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
                for n,b in sorted(members.items()):z.writestr(n,b)
            archive.chmod(0o600);config=dict(original,archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:__import__('hashlib').sha256(b).hexdigest() for n,b in members.items()},worker_path=str(worker),worker_sha256=sha(worker));configs[kind]['ON' if enabled else 'OFF']=config
            for n,h in original['members_sha256'].items():assert config['members_sha256'][n]==h or (enabled and n=='retry/temporal_agent.py')
    save(D/'configs-private.json',configs)
    cases=[]
    for road in read(R/'stage306/plan.json')['collection_roads']:
        F=R/'stage306/collection'/road;cases.append(dict(key=road,road=road,group='original6',kind='OFF',folder=str(F),pixels=str(F/'observations-actions-private.npz'),snapshots=str(F/'full-source-captures-private.jsonl.gz'),original_fields='collection',GT='all preaction frames',initial_state='independent reset'))
    for key,folder,gt in [('N2_333B',R/'stage333/B','all pre/post basic poses; static obstacle fixtures from64+'),('N2_330_A',R/'stage331/A','actual64+ only;330 alias exact'),('N2_331B',R/'stage331/B','actual64+ only')]:
        cases.append(dict(key=key,road='N2',group='N2',kind='ON',folder=str(folder),pixels=str(folder/'raw-pixels-actions-private.npz'),snapshots=None,original_fields='333' if key=='N2_333B' else '331',GT=gt,initial_state='independent reset'))
    inputs=[baseworker,R/'project-effective-budget-v341.json',R/'research-deadline-current.json',R/'stage330/artifacts-private.json',R/'stage331/plan.json',R/'stage332/summary-private.json',R/'stage333/summary-private.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',worker,D/'configs-private.json']+[G/'retry'/f for f in ['fallback334_math.py','fallback334_stage.py','fallback334_run.py','fallback334_metrics.py']]
    for case in cases:
        F=Path(case['folder']);inputs+=[Path(case['pixels']),F/'trace-private.jsonl',F/'result.json']
        if case['snapshots']:inputs.append(Path(case['snapshots']))
    for variants in configs.values():
        for cfg in variants.values():inputs.append(Path(cfg['archive_path']))
    plan=dict(stage=334,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],cases=cases,
        formula='CCW yaw rate,delta=.08*(previous_yaw+current_yaw)/2,d_old=(0,current_HUD_speed*.08),pnext=R(-delta)*(pold-d_old). Existing previous_image supplies previous yaw; no new state/learned parameter.',
        intervention='Only rejected/missing optical fallback line changed. Accepted affine algorithm/coordinate conversion untouched. Detection,radius,age,expiry,dedup,routing,controller unchanged. Distinct from323 replacing valid optical rotation.',
        evaluations='OFF full stored-record reproduction first pertrajectory; paired singleinterval tracker outputs share OFF initialhazards/directdetections/acceptedaffine; separate natural sequentialON fullactor replay on fixed recorded observations and recorded command history, originalnominal memoryupdates. Not physicalclosedloop.',
        timing='Only newest frame per actual policy input; firstresetframe no interval. Require stackshift andactualGT .08 whereavailable; no concatenation across episodes, reset copies or gaps.',
        correspondence='Nearest previous-GT identity frozen for paired transported point; sequential identity assigned at detection birth whereGTexists and propagated via source age/dedup lineage, never rematched to improve current error. Unknown birthGT staysunknown. Report birth errors/nearestsecondmargin and ambiguity; no fitted association threshold.',
        visibility='No stored authoritative visibility mask/occlusion label. Independent viewport geometry can establish in-frame eligibility, not actual visibility. Missing detection alone never labeled occlusion; true occlusion retention remains unverified absent independent evidence.',
        gates='Stop first OFF action/features/nominalmemory or available policystate mismatch, timegap/stack mismatch, OFF tracker reconstruction mismatch, or changed accepted optical outputs on same interval/input. No retry/sweep/fitting. No promotion from static output; next native requires new preregistered measured budget.',
        weighting='original6 road-balanced group and knownN2 three trajectories reported separately;330=331A alias countedonce. N2 common intervals deduplicated for aggregate metric, prefer333GT coverage. No claim all TRAIN corpus exhaustively enumerated.',
        native=0,new_learning_fits=0,source_physics_rollout=0,research_remaining=0,final_reserved_actions=84000,sandbox_path=read(R/'stage331/plan.json')['sandbox_path'],source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    print('334registered9trajectories; native0 fit0 rollout0; fallbackonly',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);build(p.parse_args().private_root)
