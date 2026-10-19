"""Fsynced, hash-chained pre-evaluation evidence; no simulator imports."""
import hashlib,json,math,os
from pathlib import Path
from retry.clip561_core import plain

def digest(x):
    return hashlib.sha256(json.dumps(plain(x),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

class Journal:
    def __init__(self,path):
        self.path=Path(path);self.fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_APPEND,0o600)
        parent=os.open(self.path.parent,os.O_RDONLY)
        try:os.fsync(parent)
        finally:os.close(parent)
        self.seq=0;self.head='0'*64
    def append(self,kind,**data):
        payload=dict(sequence=self.seq,previous=self.head,kind=kind,**plain(data));head=digest(payload)
        line=(json.dumps(dict(payload,sha256=head),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
        view=memoryview(line)
        while view:
            n=os.write(self.fd,view)
            if n<=0:raise OSError('JOURNAL_SHORT_WRITE')
            view=view[n:]
        os.fsync(self.fd);self.seq+=1;self.head=head
        return head
    def close(self):
        if self.fd is not None:os.fsync(self.fd);os.close(self.fd);self.fd=None

def evaluate_force(journal,root,action,history,context,force_fn,peak_limit=1.059,clip_limit=.1,check_clip=True,inject=None):
    """An evaluator cannot run before its complete input has reached fsync."""
    identity=dict(state_id=digest(root),action_id=digest(action),history_id=digest(history))
    before=journal.append('BEFORE_FORCE',root=root,action=action,history=history,context=context,**identity)
    if inject:inject('after_input')
    forces=force_fn();ratios=[float(f['ratio']) for f in forces]
    if len(forces)!=4 or not all(math.isfinite(v) for v in ratios):raise ValueError('INVALID_FORCE_ROWS')
    if any(bool(f['clipped'])!=(v>1.) for f,v in zip(forces,ratios)):raise ValueError('EXACT_CLIP_IDENTITY')
    proposed=[int(history[0])+sum(bool(f['clipped']) for f in forces),int(history[1])+4]
    peak=max(ratios);gate='FORCE' if peak>peak_limit else 'CLIP_HISTORY' if check_clip and proposed[0]/proposed[1]>clip_limit else None
    verdict=journal.append('FORCE_VERDICT',input_event=before,forces=forces,proposed_history=proposed,peak=peak,peak_limit=peak_limit,clip_limit=clip_limit,check_clip=check_clip,gate=gate,context=context,**identity)
    if inject:inject('after_verdict')
    return dict(forces=forces,history=proposed,gate=gate,event=verdict,identity=identity)

def guarded_tick(journal,verdict,context,step_fn,body_fn,serialize,inject=None):
    journal.append('BEFORE_TICK',force_event=verdict['event'],context=context,**verdict['identity'])
    if inject:inject('before_tick')
    after=step_fn();body=float(body_fn(after))
    journal.append('AFTER_TICK',force_event=verdict['event'],root=serialize(after),body=body,body_domain_pass=math.isfinite(body) and body<100.,context=context)
    if not math.isfinite(body) or body>=100.:raise RuntimeError('MODEL_BODY_DOMAIN')
    if inject:inject('after_tick')
    return after

def inspect(path):
    head='0'*64;n=0;kinds={}
    with open(path) as f:
        for line in f:
            row=json.loads(line);h=row.pop('sha256')
            if row['sequence']!=n or row['previous']!=head or digest(row)!=h:raise ValueError('JOURNAL_CHAIN_INVALID')
            head=h;n+=1;kinds[row['kind']]=kinds.get(row['kind'],0)+1
    return dict(events=n,head=head,kinds=kinds,valid=True)
