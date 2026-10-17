"""Lossless current-raw state interning with exact decoded receipt authentication.

Only complete terminal snapshot objects are interned. Source maps remain inline.
Historical files/writers/bytes are never transformed. No physical state is omitted.
"""
import copy,hashlib,json,re,shutil,sys
from pathlib import Path
import retry.loss389_analyze as plain
import retry.receipt421_io as receipt
from retry.pilot420_json import json_ready,restore_bytes
from retry.pilot420_backend import ResourceStop,TechnicalStop
ORIGINAL_READ=plain.read
ORIGINAL_LOAD=receipt.load_receipt
STATE_KEY='__haic_full_state_ref481__'
CODEC_KEY='__haic_lossless481__'

def canonical(value):return hashlib.sha256(json.dumps(json_ready(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def expand(value,d):
    if isinstance(value,dict):
        if set(value)=={STATE_KEY}:
            h=value[STATE_KEY]
            if not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h):raise TechnicalStop('481_bad_state_ref')
            obj=ORIGINAL_READ(Path(d)/('state-'+h+'.json'))
            if set(obj)!={'full_state','sha256'} or obj['sha256']!=h or canonical(obj['full_state'])!=h:raise TechnicalStop('481_state_object_auth')
            return obj['full_state']
        return {k:expand(v,d) for k,v in value.items()}
    if isinstance(value,list):return [expand(v,d) for v in value]
    return value

def read(path):
    path=Path(path);value=ORIGINAL_READ(path)
    if isinstance(value,dict) and CODEC_KEY in value:
        if value[CODEC_KEY]!=1 or set(value)!={CODEC_KEY,'payload','decoded_sha256'}:raise TechnicalStop('481_codec_schema')
        decoded=restore_bytes(expand(value['payload'],path.parent))
        if canonical(decoded)!=value['decoded_sha256']:raise TechnicalStop('481_decoded_digest')
        return decoded
    return value

def load_receipt(path):
    value=read(path)
    return restore_bytes(value)

class Quota:
    STATE_MAX=393216
    STATES_MAX=2030 # <=2/world + one context/allocator +4 fixed source-root allowance.
    NONSTATE_MODEL_MAX=812*160*1024+1210*128*1024+402*16*1024+22*1024**2
    def __init__(self,d,model_cap,extra_cap,decision_cap=16*1024**2):
        self.d=Path(d).resolve();self.model_cap=model_cap;self.extra_cap=extra_cap;self.decision_cap=decision_cap
        self.oldsave=plain.save;self.oldreceipt=receipt.save_receipt
        self.used={p.resolve():p.stat().st_size for p in self.d.iterdir() if p.is_file()};self.objects=set()
        if self.STATES_MAX*self.STATE_MAX+self.NONSTATE_MODEL_MAX>model_cap:raise TechnicalStop('481_codec_worst_bound')
    def category(self,p):
        if p.name.startswith('allocation-'):return 'allocator'
        if p.name.startswith('decision-'):return 'decision'
        return 'model'
    def cap(self,p):
        n=p.name
        if n.startswith('state-'):return self.STATE_MAX
        if n.startswith('allocation-input-'):return 4096
        if n.startswith('allocation-proof-'):return 8192
        if n.startswith('decision-'):return 65536
        if n.startswith('context-'):return 16384 # full state is a separate lossless object
        if 'runtime-link' in n:return 256*1024
        if 'before-constructor' in n or 'before-first-step' in n or 'before-integration' in n or n=='plan.json':return 2*1024**2
        return 32*1024**2
    def before(self,path,value):
        p=Path(path).resolve()
        if p.parent!=self.d:raise TechnicalStop('481_write_outside_current_raw:'+str(p))
        size=len((json.dumps(json_ready(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
        if size>self.cap(p):raise ResourceStop('481_perfile_cap:'+p.name)
        totals={k:sum(n for f,n in self.used.items() if self.category(f)==k) for k in ('model','allocator','decision')};cat=self.category(p);totals[cat]+=size-self.used.get(p,0)
        if totals['model']>self.model_cap or totals['allocator']>self.extra_cap or totals['decision']>self.decision_cap:raise ResourceStop('481_total_output_cap')
        nonstate=sum(n for f,n in self.used.items() if self.category(f)=='model' and not f.name.startswith('state-'))
        if cat=='model' and not p.name.startswith('state-'):nonstate+=size-self.used.get(p,0)
        if nonstate>self.NONSTATE_MODEL_MAX:raise ResourceStop('481_nonstate_model_cap')
        for volume in ('/tmp','/workspace'):
            if shutil.disk_usage(volume).free-size<512*1024**2:raise ResourceStop('481_storage_reserve')
        return p,size
    def intern(self,value):
        if isinstance(value,dict):
            if set(value)=={'physical','finish_tracker','elapsed_raw_steps'}:
                h=canonical(value);path=self.d/('state-'+h+'.json')
                if h not in self.objects:
                    if len(self.objects)>=self.STATES_MAX:raise ResourceStop('481_state_object_count')
                    obj={'full_state':value,'sha256':h};p,n=self.before(path,obj)
                    self.oldreceipt(path,obj);self.used[p]=n;self.objects.add(h)
                return {STATE_KEY:h}
            return {k:self.intern(v) for k,v in value.items()}
        if isinstance(value,list):return [self.intern(v) for v in value]
        return value
    def pack(self,value):
        ready=json_ready(value)
        return {CODEC_KEY:1,'payload':self.intern(ready),'decoded_sha256':canonical(value)}
    def save(self,path,value):
        packed=self.pack(value);p,n=self.before(path,packed);self.oldsave(path,packed);self.used[p]=n
    def save_receipt(self,path,value):
        packed=self.pack(value);p,n=self.before(path,packed);self.oldreceipt(path,packed);self.used[p]=n
        return canonical(value)
    def install(self):
        mappings=[(self.oldsave,self.save),(self.oldreceipt,self.save_receipt),(ORIGINAL_READ,read),(ORIGINAL_LOAD,load_receipt)]
        for name,module in list(sys.modules.items()):
            if name.startswith('retry.') and name!='retry.io481' and module is not None:
                for key,value in list(vars(module).items()):
                    for old,new in mappings:
                        if value is old:setattr(module,key,new);break
        return self
