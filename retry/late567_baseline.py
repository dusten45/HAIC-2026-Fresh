"""Bounded exact source replay of the preregistered s=800 late checkpoint."""
import copy, hashlib, json, math, time
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np

from retry.clip561_core import atomic_write, plain
import retry.handoff562_model as d
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
from retry.closure524_control import tick
from retry.speed516_control import force_rows
from retry.corner515_model import margin
from retry.lap518_finish import hull_pose
from core.finish_line import FinishLineTracker

G=Path(__file__).resolve().parents[1]
PRIV=Path('/workspace/haic-response567-private')
TAPE=Path('/workspace/haic-response565-private/final-tape-private.json')
STATIC=Path('/workspace/haic-response515-private/collected-map-state-private.json')
PATHS=Path('/workspace/haic-response551-private/frozen-paths-private.json')
LEDGER=Path('/workspace/haic-response519-private/model-ledger-private.json')
CONTRACT=G/'retry/late567_contract.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rd=lambda p:json.loads(p.read_text())

class Meter:
    def __init__(self, study):
        self.s=study; self.counter=[0]; self.cost={'force_evaluations':0,'geometry_checks':0,'body_checks':0,'max_body':0.0}
    def guard(self,reserve=0):
        if self.counter[0]>1200 or self.cost['force_evaluations']+reserve>4800 or self.cost['geometry_checks']>1400:
            raise RuntimeError('567 replay work cap')
    def force(self,root,action):
        self.guard(4); return force_rows(root,action)
    def tick(self,root,gas,brake,index,counter):
        self.guard(); after=tick(root,gas,brake,self.s.index,counter)
        body=max(math.hypot(*hull_pose(after)[1]),*(math.hypot(*(after.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in after.planar.linear.wheels))
        self.cost['body_checks']+=1; self.cost['max_body']=max(self.cost['max_body'],body)
        if not math.isfinite(body) or body>=100: raise RuntimeError('567 MODEL_BODY_DOMAIN')
        return after
    def geometry(self,root):
        self.guard(); self.cost['geometry_checks']+=1
        return margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles'])

def main():
    PRIV.mkdir(mode=0o700,exist_ok=False)
    contract=rd(CONTRACT); tape=rd(TAPE); static=rd(STATIC); paths=rd(PATHS); ledger=rd(LEDGER)
    rows=tape['rows']; commands={int(x['index']):np.asarray(x['action'],np.float32) for x in tape['commands']}
    study=SimpleNamespace(static=static,paths=paths,index=bounds(static['root']['roads']),edge=boundary_index(static['boundary']))
    checkpoint=next(r for r in rows if r['global_raw_after']==528)
    root=d.load_root(dict(checkpoint['root_without_roads'],roads=static['root']['roads']))
    visited=set(ledger['initial_visited'])
    for r in rows[:528]:
        rr=d.load_root(dict(r['root_without_roads'],roads=static['root']['roads']))
        for ids in rr.current_contacts: visited.update(ids)
    state=dict(root=root,visited=visited,tracker=FinishLineTracker(**checkpoint['tracker']),elapsed=checkpoint['episode_after_s'],global_raw=528,progress=checkpoint['progress'],launch=[55,384],tracking=list(checkpoint['proposed_history']))
    meter=Meter(study); start=time.perf_counter(); cpu=time.process_time(); actual=[]
    start_hash=hashlib.sha256(json.dumps({'root':checkpoint['root_without_roads'],'tracker':checkpoint['tracker'],'progress':checkpoint['progress'],'tracking':state['tracking'],'visited':sorted(visited)},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    try:
        for idx in range(133,153):
            for raw in range(1,5):
                rec,reason=d.Study.raw(study,state,commands[idx],idx,raw,meter)
                actual.append(rec)
                if reason: raise RuntimeError('567 incumbent segment violated '+reason)
        expected=[r for r in rows if 528<r['global_raw_after']<=608]
        equal=len(expected)==len(actual) and all(d.canonical(a['root_without_roads'])==d.canonical(b['root_without_roads']) and d.canonical(a['forces'])==d.canonical(b['forces']) for a,b in zip(actual,expected))
        if not equal: raise RuntimeError('567 exact baseline mismatch')
        result={'completed':True,'start_rule':'first saved hold bracketing s=800','start_global_raw':528,'start_progress_m':checkpoint['progress'],'first_variable_hold':133,'last_variable_hold':152,'end_global_raw':608,'end_progress_m':state['progress'],'fresh_source_ticks':meter.counter[0],'force_evaluations':meter.cost['force_evaluations'],'geometry_checks':meter.cost['geometry_checks'],'body_checks':meter.cost['body_checks'],'max_body':meter.cost['max_body'],'CPU_s':time.process_time()-cpu,'wall_s':time.perf_counter()-start,'exact_saved_fullstate_and_force_replay':equal,'start_checkpoint_sha256':start_hash,'inputs_sha256':{str(p):sha(p) for p in (TAPE,STATIC,PATHS,LEDGER)},'contract_sha256':sha(CONTRACT),'candidate_count':0,'DEV_only':True,'HOLDOUT':0,'SEALED':0,'native_actions':0,'paid_compute':0,'reserve_used':0}
        atomic_write(PRIV/'baseline-replay-private.json',{'start_hash':start_hash,'rows':actual,'state':d.short(state['root']),'tracker':asdict(state['tracker']),'visited':sorted(visited)})
        atomic_write(G/'retry/late567_baseline_result.json',result)
        atomic_write(G/'retry/late567_cost.json',{'baseline_replay':{k:result[k] for k in ('fresh_source_ticks','force_evaluations','geometry_checks','body_checks','CPU_s','wall_s')},'candidate_runs':0,'aggregate_cap_from_contract':contract['cost_caps']})
        print(json.dumps(result,indent=2))
    except BaseException as e:
        atomic_write(PRIV/'failure-private.json',{'error':type(e).__name__+': '+str(e),'rows':actual})
        raise

if __name__=='__main__': main()
