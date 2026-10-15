"""Freeze private standalone334/H1 + fixed342 rule; no new policy choice."""
import datetime
import hashlib
from pathlib import Path
import sys
import time
import zipfile
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def replace_once(source,old,new):
    assert source.count(old)==1,old
    return source.replace(old,new)


def candidate_members(members):
    out=dict(members);out['retry/support342_logic.py']=(G/'retry/support342_logic.py').read_bytes()
    s=out['retry/temporal_agent.py'].decode()
    s=replace_once(s,'from retry.hud248_features import decode','from retry.hud248_features import decode\nfrom retry.support342_logic import advance_evidence')
    s=replace_once(s,'        self.hazards = []','        self.hazards = []\n        self.support349_state = []\n        self.support349_step = 0\n        self.support349_record = None')
    s=replace_once(s,'        current = np.rint(image * 255).astype(np.uint8)','        before349 = list(self.hazards)\n        previous_yaw349 = float(decode(self.previous_image.astype(np.float32)/255)[5]) if self.previous_image is not None else None\n        current = np.rint(image * 255).astype(np.uint8)')
    s=replace_once(s,'        for x, y, radius in road_and_obstacles(image)[1]:','        direct349 = road_and_obstacles(image)[1]\n        for x, y, radius in direct349:')
    s=replace_once(s,'        self.previous_image, self.hazards = current, predicted','''        self.previous_image, self.hazards = current, predicted
        self.support349_step += 1
        tracker349 = dict(before=before349, after=predicted,
            previous_yaw=previous_yaw349, current_yaw=float(decode(image)[5]),
            current_speed=float(decode_feedback_speed(image,speed)),
            affine=None if transform is None else transform.tolist(), direct=direct349)
        self.support349_record = advance_evidence(tracker349,self.support349_state,self.support349_step,image)
        self.support349_state = self.support349_record['after']''')
    out['retry/temporal_agent.py']=s.encode()
    s=out['retry/nominal238_base.py'].decode()
    s=replace_once(s,'        path = connected_route(image, obstacles, speed=speed, previous_steer=self.controller.previous_steer)',"        routing349 = [p for p,e in zip(obstacles,self.support349_state) if not e['low']]\n        assert len(obstacles)==len(self.support349_state)\n        path = connected_route(image, routing349, speed=speed, previous_steer=self.controller.previous_steer)")
    out['retry/nominal238_base.py']=s.encode()
    return out


def observer(source):
    # Observe the archive's routing arguments; this adapter never filters them.
    source=replace_once(source,'def route_observer(*args,**kwargs):\n    path=original_route(*args,**kwargs)', '''routing_evidence=None
def route_observer(image,obstacles_override=None,speed=0.,previous_steer=0.):
    global routing_evidence
    full=copy.deepcopy(agent.hazards)
    support=getattr(agent,'support349_state',None)
    removed=[] if support is None else [i for i,e in enumerate(support) if e['low']]
    selected=[p[:3] for i,p in enumerate(full) if i not in removed]
    assert [list(p) for p in obstacles_override]==[list(p) for p in selected]
    routing_evidence=dict(full_hazards=full,routing_hazards=selected,removed_indices=removed,
        removed_evidence=[] if support is None else [support[i] for i in removed],tracker_preserved=True)
    path=original_route(image,obstacles_override,speed=speed,previous_steer=previous_steer)''')
    source=replace_once(source,"    response['tracker_record']=tracker_record","    response['tracker_record']=tracker_record\n    response['support_record']=getattr(agent,'support349_record',None)\n    response['packaged_support_state']=getattr(agent,'support349_state',None)\n    response['packaged_support_step']=getattr(agent,'support349_step',None)\n    response['routing_evidence']=routing_evidence")
    source=replace_once(source,"                  'package_init_ms':", "                  'actual_code_paths':dict(root_act=Agent.act.__code__.co_filename,tracked=original_tracked.__code__.co_filename,nominal_act=sys.modules['retry.nominal238_base'].Agent.act.__code__.co_filename),\n                  'package_init_ms':")
    return source


def verify(R):
    D=R/'stage349';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    D=R/'stage349';assert not D.exists();D.mkdir(mode=0o700)
    prior=read(R/'stage337/plan.json');base=prior['config'];assert sha(base['archive_path'])==base['archive_sha256']=='133cf83a145b1db6b9bd32c43139e8dc43967ed547b3154b73164fa5d6a55a33'
    assert sha(base['worker_path'])==base['worker_sha256']
    with zipfile.ZipFile(base['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
    assert {n:hashlib.sha256(v).hexdigest() for n,v in members.items()}==base['members_sha256']
    candidate=candidate_members(members)
    assert {n for n in members if members[n]!=candidate[n]}=={'retry/temporal_agent.py','retry/nominal238_base.py'}
    assert set(candidate)-set(members)=={'retry/support342_logic.py'}
    for name,data in candidate.items():
        if name.endswith('.py'):compile(data,name,'exec')
    artifacts=D/'artifacts';artifacts.mkdir(mode=0o700)
    baseline=artifacts/'baseline334.zip';baseline.write_bytes(Path(base['archive_path']).read_bytes());baseline.chmod(0o600)
    target=artifacts/'candidate349.zip'
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,data in sorted(candidate.items()):
            i=zipfile.ZipInfo(n,date_time=(2026,10,15,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100444<<16;z.writestr(i,data)
    target.chmod(0o600)
    worker=D/'observer-worker-private.py';worker.write_text(observer(Path(base['worker_path']).read_text()));worker.chmod(0o600);compile(worker.read_text(),str(worker),'exec')
    configs={}
    for name,path,values in [('baseline',baseline,members),('candidate',target,candidate)]:
        configs[name]=dict(base,archive_path=str(path),archive_sha256=sha(path),members_sha256={n:hashlib.sha256(v).hexdigest() for n,v in values.items()},worker_path=str(worker),worker_sha256=sha(worker))
    v=read(R/'project-effective-budget-v360.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(233,84000,0)
    files=[G/'retry/package349_stage.py',G/'retry/package349_run.py',G/'retry/support342_logic.py',G/'retry/frozen_composite_runtime.py',G/'retry/probe338_stage.py',Path(base['archive_path']),Path(base['worker_path']),baseline,target,worker,R/'project-effective-budget-v360.json',R/'research-deadline-current.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'stage337/cache/reset-private.json',R/'stage337/actual-reset-contract.json']
    for stage in [337,340]:files.extend(R/f'stage{stage}/B'/n for n in ['trace-private.jsonl','frames-actions-private.npz'])
    files += [R/f'stage342/N2_{stage}/candidate/records-private.jsonl' for stage in [337,340]]
    deadline=read(R/'research-deadline-current.json')['deadline_utc'];assert time.time()<datetime.datetime.fromisoformat(deadline.replace('Z','+00:00')).timestamp()
    p=dict(stage=349,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,configs=configs,sandbox_path=prior['sandbox_path'],order=[dict(mode='baseline',input_stage=337,count=233),dict(mode='candidate',input_stage=340,count=233)],
        question='Standalone fixed342 package equivalence in current334ON/H1 context only. Reproduce baseline337 first; candidate340 must match saved342 generic-rule replay, then describe differences from actual340 known121-only selection. No cross-trajectory causal A/B inference.',
        stop='Stop on baseline reproduction, frozen generic342 replay equivalence, source/hash/input/interface/reset/tracker failure or leakage; no extra actor/reset beyond466/2 and no policy repair or expansion. A difference from known121 selection is an expected diagnostic outcome, not permission to modify the candidate.',
        gates='Exact baseline action/features/path/audit/commit-state. Candidate exact342 action/features/path/audit/support/tracker and commit-state projection excluding expected agent_pickle hash due packaged metadata attributes. Float32(4,84,84) pixels only; own returned commands and normal memory.',
        identity='Baseline archive byte-identical334ON/H1. Candidate changes only temporal metadata bookkeeping, fixed342 helper and routing arguments; full hazards still used for scheduling/count/min-distance. Rule executes in package, not observer. No296 context pooling or champion replacement.',
        reset='Two pixel-only resets. Baseline complete saved reset state exact. Candidate original state projection exact; metadata empty/step0/recordNone. Extra metadata necessarily changes serialized agent hash; do not claim full pickle identity.',
        promotion='None. Package qualification is research replay evidence, not official fresh-machine/submission qualification or completion evidence.',
        budget=dict(actor_act_calls=466,actor_resets=2,new_native_actions=0,new_environment_resets=0,new_fits=0,new_thresholds=0,new_tuning=0,research_remaining=233,final_reserve=84000),source_hashes={str(f):sha(f) for f in files})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    save(D/'call-budget.json',dict(actor_act_calls=0,actor_resets=0,cap=466,reset_cap=2))
    save(D/'artifact-manifest-private.json',dict(baseline_archive_sha256=sha(baseline),candidate_archive_sha256=sha(target),configs=configs,standalone_policy_decision_code=True,external_worker_only_observes=True,changed_existing_members=['retry/temporal_agent.py','retry/nominal238_base.py'],added_members=['retry/support342_logic.py'],new_native=0))
    print('349 registered: baseline337233 then candidate340233, actor466/reset2; standalone private archives frozen.',flush=True)


if __name__=='__main__':build(Path(sys.argv[1]).resolve())
