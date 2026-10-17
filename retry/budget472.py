"""472 conservative durable native charge ledger; immutable475, owned LIVE476."""
import copy,datetime,fcntl,json,os,tempfile
from pathlib import Path
from retry.loss389_analyze import sha
from retry.pilot420_backend import TechnicalStop

ARM='Projected4ReferenceCommonPulse'

def atomic472(path,value,exclusive=False):
    path=Path(path);fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as handle:
            json.dump(value,handle,indent=2,sort_keys=True,allow_nan=False);handle.write('\n');handle.flush();os.fsync(handle.fileno())
        if exclusive:os.link(tmp,path);os.unlink(tmp)
        else:os.replace(tmp,path)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

class ChargeLedger472:
    def __init__(self,p,d):
        self.p=p;self.d=Path(d);self.before_path=Path(p['budget_before_path']);self.path=Path(p['ledger_path']);self.before_hash=p['budget_before_sha256'];self.current_hash=None;self.sequence=0
        self.owner=dict(stage=472,pid=os.getpid(),plan_sha256=sha(self.d/'plan.json'),native_directory=str(Path(p['native_directory']).resolve()))
        self.before=json.loads(self.before_path.read_text());self.verify_before()
        if self.path.exists():raise TechnicalStop('472_existing476_no_resume_overwrite')
    def verify_before(self):
        if self.before_path.name!='project-effective-budget-v475.json' or self.path.name!='project-effective-budget-v476.json' or self.before_path.resolve().parent!=self.path.resolve().parent:raise TechnicalStop('472_ledger_paths')
        if sha(self.before_path)!=self.before_hash:raise TechnicalStop('472_frozen475_hash')
        expected=dict(version=475,research_remaining=26346,actual_cumulative_wrapper_actions=1321718,final_reserved_actions=84000,final_reserve_used=0)
        if any(self.before.get(k)!=v for k,v in expected.items()):raise TechnicalStop('472_frozen475_balance')
    def charge(self,kind,nb):
        with open(str(self.path)+'.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);self.verify_before()
            if self.current_hash is None:
                if self.path.exists():raise TechnicalStop('472_foreign476')
            elif not self.path.exists() or sha(self.path)!=self.current_hash:raise TechnicalStop('472_live476_changed')
            self.sequence+=1;debit=nb['actions'];ledger=copy.deepcopy(self.before)
            ledger.update(version=476,prior_budget_path=str(self.before_path),prior_budget_sha256=self.before_hash,owner=self.owner,
                          at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),research_remaining=26346-debit,
                          actual_cumulative_wrapper_actions=1321718+debit,stage472_new_wrapper_actions=debit,
                          stage472_actual_resets=nb['resets'],stage472_actual_retries=0,stage472_status='LIVE',
                          research_status='STAGE472_P4_SINGLE_NATIVE_LIVE_CHARGE_BEFORE_CALL',
                          current_stage_execution_cap='472 one fixed125 then ownP4 current-pair suffix70; no rescue/followup',charged_attempts_no_refund=True)
            receipt=dict(stage=472,sequence=self.sequence,owner=self.owner,kind=kind,arm=ARM,
                         actions=debit,resets=nb['resets'],research_remaining=26346-debit,
                         arm_actions=dict(nb['arm_actions']),arm_resets=dict(nb['arm_resets']),
                         status='CHARGED_BEFORE_CALL_CONSERVATIVE_NO_REFUND')
            atomic472(Path(self.p['native_directory'])/('charge472-%04d-private.json'%self.sequence),receipt,exclusive=True)
            atomic472(self.path,ledger,exclusive=self.current_hash is None);self.current_hash=sha(self.path)

def close472(p,d,result):
    """Saved-only closure after worker exit; reconcile every conservative charge.

    Never creates476, spends/refunds actions, rewrites475, or authorizes a retry.
    The saved worker result supplies the last LIVE hash, independently of the
    analyzer process PID. A second identical closure is read-only/idempotent.
    """
    d=Path(d);before_path=Path(p['budget_before_path']);path=Path(p['ledger_path'])
    if sha(before_path)!=p['budget_before_sha256']:raise TechnicalStop('472_close475_changed')
    before=json.loads(before_path.read_text());actions=result['new_actual_actions'];resets=result['new_resets']
    if not(0<=actions<=195 and 0<=resets<=1):raise TechnicalStop('472_close_native_caps')
    journals=sorted(Path(p['native_directory']).glob('charge472-*-private.json'))
    if not path.exists():
        if actions or resets or journals or result.get('live_ledger_sha256') is not None:raise TechnicalStop('472_close_missing_charged476')
        return dict(status='NO_NATIVE_CHARGE_NO476',research_remaining=before['research_remaining'],reserve_used=0)
    with open(str(path)+'.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);ledger=json.loads(path.read_text());owner=ledger.get('owner',{})
        if owner.get('stage')!=472 or owner.get('plan_sha256')!=sha(d/'plan.json') or owner.get('native_directory')!=str(Path(p['native_directory']).resolve()):raise TechnicalStop('472_close_foreign_owner')
        if result['plan_sha256']!=owner['plan_sha256']:raise TechnicalStop('472_close_result_plan')
        counters=dict(actions=0,resets=0)
        for index,journal in enumerate(journals,1):
            receipt=json.loads(journal.read_text());kind=receipt['kind']
            if kind not in ('reset','action') or receipt['sequence']!=index or receipt['owner']!=owner or receipt['arm']!=ARM:raise TechnicalStop('472_close_journal_identity')
            counters['resets' if kind=='reset' else 'actions']+=1
            if receipt['actions']!=counters['actions'] or receipt['resets']!=counters['resets'] or receipt['research_remaining']!=26346-counters['actions']:raise TechnicalStop('472_close_journal_running_debit')
        if counters!=dict(actions=actions,resets=resets) or len(journals)!=actions+resets:raise TechnicalStop('472_close_journal_count')
        expected=dict(version=476,stage472_new_wrapper_actions=actions,stage472_actual_resets=resets,
                      research_remaining=26346-actions,actual_cumulative_wrapper_actions=1321718+actions,
                      final_reserved_actions=84000,final_reserve_used=0,prior_budget_sha256=p['budget_before_sha256'])
        if any(ledger.get(k)!=v for k,v in expected.items()):raise TechnicalStop('472_close_live_balance')
        result_hash=sha(d/'result.json')
        if ledger.get('stage472_status')=='CLOSED':
            if ledger.get('stage472_result_sha256')!=result_hash:raise TechnicalStop('472_close_different_result')
            return dict(status='ALREADY_CLOSED',ledger_sha256=sha(path),research_remaining=ledger['research_remaining'],reserve_used=0)
        if ledger.get('stage472_status')!='LIVE' or sha(path)!=result.get('live_ledger_sha256'):raise TechnicalStop('472_close_live_hash')
        actual=result['budget']['actual']
        if actual['actions']!=actions or actual['resets']!=resets:raise TechnicalStop('472_close_worker_budget')
        ledger.update(stage472_status='CLOSED',stage472_result_sha256=result_hash,
                      stage472_result_status=result['status'],stage472_charge_journals_verified=len(journals),
                      research_status='STAGE472_CLOSED_'+result['status'],
                      current_stage_execution_cap='472 closed; no retry/followup/extension',
                      closed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        atomic472(path,ledger)
        return dict(status='CLOSED',ledger_sha256=sha(path),research_remaining=ledger['research_remaining'],reserve_used=0,
                    charged_actions=actions,resets=resets,journals_verified=len(journals))
