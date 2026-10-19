"""User-required final replay of a NEW safe finish, even when not promoted.

This uses the reserved 569 verification budget; it never reruns the search or
the unchanged seed. The search's narrower 'selected working point' condition
does not override the user's explicit request to verify a new safe candidate.
"""
import datetime,json,time
from pathlib import Path
import numpy as np
import retry.path569_model as m
from retry.clip561_core import atomic_write
from retry.durable568 import Journal,inspect

class FrozenPhase:
    def __init__(self,row):self.row=row;self.bucket=row['bucket'];self.label=row['label']
    def values(self):return {k:v for k,v in self.row.items() if k not in ('bucket','label')}

def main():
    result=m.rd(m.G/'retry/path569_result.json')
    if result.get('independent_verification') is not None:raise RuntimeError('FINAL_REPLAY_ALREADY_DONE')
    safe=[e for e in result['events'] if e.get('safe_finish')]
    if not safe:raise RuntimeError('NO_NEW_SAFE_CANDIDATE_TO_VERIFY')
    event=min(safe,key=lambda e:(e['official_candidate_raw'],e['actual_times']['hull_finish']));label=event['label']
    atomic_write(m.D/'VALIDATION-STARTED.json',dict(selected_new_candidate=label,policy_promoted=False,requested_by='569 user: new safe candidate final independent replay',budget='existing verification1200ticks/35CPU/50wall',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=m.sha(Path(__file__))))
    atomic_write(m.D/'search-finished-result-private.json',result)
    s=m.Study.__new__(m.Study);s.contract=m.rd(m.G/'retry/path569_contract.json');s.design=m.rd(m.G/'retry/path569_design.json');s.tape,s.static,s.paths,s.ledger=map(m.rd,m.base.INPUTS[:4]);s.commands={r['index']:np.asarray(r['action'],np.float32) for r in s.tape['commands']};s.index=m.d.bounds(s.static['root']['roads']);s.edge=m.d.boundary_index(s.static['boundary']);s.phases=[FrozenPhase(p) for p in result['cost']['phases']];s.cpu=time.process_time()-result['cost']['total']['CPU_s'];s.wall=time.perf_counter()-result['cost']['total']['wall_s'];s.journal=Journal(m.D/'verification-journal-private.jsonl')
    cp=m.rd(m.D/(label+'-feedback-private.json'))['checkpoint'];state=dict(cp);state['root']=m.d.load_root(dict(state.pop('root_without_roads'),roads=s.static['root']['roads']));state['tracker']=m.d.FinishLineTracker(**state['tracker']);state['visited']=set(state['visited'])
    probe=m.rd(m.D/(label+'-diagnostic-private.json'));fb=m.rd(m.D/(label+'-feedback-private.json'));case=dict(x=np.asarray(probe['x']),program=dict(rows=probe['rows'][:80]),feedback=dict(rows=fb['rows'],commands=fb['commands'],state=state))
    try:
        verification=s.verify(case);verification.update(selected_new_safe_candidate=label,policy_promoted=False,user_required_validation=True)
        result['independent_verification']=verification
    finally:
        s.save_cost();s.journal.close();audit=m.rd(m.G/'retry/path569_audit.json');audit['independent_validation_journal']=inspect(m.D/'verification-journal-private.jsonl');audit['validation_source_sha256']=m.sha(Path(__file__));atomic_write(m.G/'retry/path569_audit.json',audit,True)
        result['cost']=s.cost();atomic_write(m.G/'retry/path569_result.json',result,True);s.save_cost()
    print(json.dumps(verification,indent=2))

if __name__=='__main__':
    from core.vendor.car_racing import CarRacing
    def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
    CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
    main()
