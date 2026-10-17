"""492 retained-file reservations and atomic writes; no runtime physics imports.

Model serialization is the unchanged481 codec, attached lazily by model_quota().
All limits include termination-control reservations; only new492 outputs belong
in these roots. Native observation writers must use write_bytes, never raw open.
"""
import json, os, shutil, sys, tempfile
from dataclasses import dataclass
from pathlib import Path

MIB=1024**2
class QuotaStop(RuntimeError):pass
@dataclass(frozen=True)
class Ticket:
    path: Path
    scope: str
    category: str
    size: int
    control: bool

class RunQuota:
    MODEL_FILES=1840
    NATIVE_FILES=1664
    MODEL_BYTES=192*MIB
    NATIVE_BYTES=256*MIB
    WORKSPACE_BYTES=16*MIB
    ALLOCATOR_BYTES=8*MIB
    DECISION_BYTES=8*MIB
    TEMP_BYTES=8*MIB
    RESERVE_BYTES=512*MIB
    NONSTATE_MODEL_BYTES=62*MIB
    STATE_BYTES=512*1024
    STATE_OBJECTS=260
    CONTROL_FILES={'model':16,'native':16,'workspace':8}
    CONTROL_BYTES={'model':MIB,'native':MIB,'workspace':MIB}
    WORKSPACE_FILES=64  # extra finite metadata bound; entirely within16MiB

    def __init__(self,model_dir,native_dir,workspace_paths=(),free_bytes=None,codec_module=None,install_modules=None):
        self.codec_module=codec_module;self.install_modules=install_modules
        self.model_dir=Path(model_dir).resolve();self.native_dir=Path(native_dir).resolve()
        if self.model_dir==self.native_dir or self.model_dir in self.native_dir.parents or self.native_dir in self.model_dir.parents:
            raise QuotaStop('overlapping_raw_roots')
        self.free_bytes=free_bytes or (lambda p:shutil.disk_usage(p).free)
        self.workspace=set();self.records={};self.pending={};self.temporary_bytes=0;self.model=None
        for d in (self.model_dir,self.native_dir):
            d.mkdir(parents=True,exist_ok=True)
            for p in d.rglob('*'):
                if p.is_symlink():raise QuotaStop('symlink_in_output_root')
                if p.is_file():self.records[p.resolve()]=(p.stat().st_size,self.scope(p),self.category(p),self.is_control(p))
        for p in workspace_paths:self.register_workspace(p,existing=True)
        self._validate()

    @staticmethod
    def is_control(p):
        n=Path(p).name
        exact={'cleanup-private.json','preparation-result-private.json','budget.json','progress-private.json','stop-private.json','result.json','cleanup-stop-private.json','retention-manifest-private.json','final-control-private.json'}
        return n in exact or n.endswith(('-checkpoint-private.json','-retention-manifest-private.json','-cleanup-stop-private.json','-preparation-stop-private.json'))

    def scope(self,path):
        p=Path(path).resolve()
        if self.model_dir in p.parents:return 'model'
        if self.native_dir in p.parents:return 'native'
        if p in self.workspace:return 'workspace'
        raise QuotaStop('unregistered_output_path:'+str(p))

    def category(self,path):
        p=Path(path).resolve();scope=self.scope(p)
        if scope!='model':return scope
        if p.name.startswith('allocation-'):return 'allocator'
        if p.name.startswith('decision-'):return 'decision'
        return 'model'

    def register_workspace(self,path,existing=False):
        if Path(path).is_symlink():raise QuotaStop('workspace_symlink')
        p=Path(path).resolve()
        if p==self.model_dir or p==self.native_dir or self.model_dir in p.parents or self.native_dir in p.parents:
            raise QuotaStop('workspace_path_is_raw')
        if p in self.workspace:return p
        if p.exists() and not existing:raise QuotaStop('workspace_path_already_exists')
        self.workspace.add(p)
        if p.exists():
            if not p.is_file() or p.is_symlink():raise QuotaStop('workspace_not_regular_file')
            self.records[p]=(p.stat().st_size,'workspace','workspace',self.is_control(p))
        self._validate();return p

    def _effective(self):
        out=dict(self.records)
        out.update({p:(t.size,t.scope,t.category,t.control) for p,t in self.pending.items()})
        return out

    def _validate(self):
        rows=self._effective()
        limits={'model':self.MODEL_FILES,'native':self.NATIVE_FILES,'workspace':self.WORKSPACE_FILES}
        byte_limits={'model':self.MODEL_BYTES,'native':self.NATIVE_BYTES,'workspace':self.WORKSPACE_BYTES,'allocator':self.ALLOCATOR_BYTES,'decision':self.DECISION_BYTES}
        for scope,limit in limits.items():
            selected=[v for v in rows.values() if v[1]==scope]
            if len(selected)>limit:raise QuotaStop(scope+'_file_cap')
            if sum(not v[3] for v in selected)>limit-self.CONTROL_FILES[scope]:raise QuotaStop(scope+'_control_slot_reserve')
        for cat,limit in byte_limits.items():
            selected=[v for v in rows.values() if v[2]==cat]
            if sum(v[0] for v in selected)>limit:raise QuotaStop(cat+'_byte_cap')
            if cat in self.CONTROL_BYTES and sum(v[0] for v in selected if not v[3])>limit-self.CONTROL_BYTES[cat]:raise QuotaStop(cat+'_control_byte_reserve')
        nonstate=[v for p,v in rows.items() if v[2]=='model' and not p.name.startswith('state-')]
        if sum(v[0] for v in nonstate)>self.NONSTATE_MODEL_BYTES:raise QuotaStop('nonstate_model_byte_cap')
        if sum(v[0] for v in nonstate if not v[3])>self.NONSTATE_MODEL_BYTES-self.CONTROL_BYTES['model']:raise QuotaStop('nonstate_control_byte_reserve')
        states=[(p,v) for p,v in rows.items() if v[2]=='model' and p.name.startswith('state-')]
        if len(states)>self.STATE_OBJECTS or any(v[0]>self.STATE_BYTES for p,v in states):raise QuotaStop('state_object_cap')

    def reserve(self,path,size,control=None):
        original=Path(path)
        if original.is_symlink():raise QuotaStop('output_symlink')
        p=original.resolve();scope=self.scope(p);cat=self.category(p)
        if p in self.pending:raise QuotaStop('duplicate_pending_write')
        if type(size) is not int or size<0:raise QuotaStop('invalid_size')
        is_control=self.is_control(p) if control is None else bool(control)
        if is_control and not self.is_control(p):raise QuotaStop('unregistered_control_name')
        if size>self.TEMP_BYTES:raise QuotaStop('perfile_or_temp_8MiB')
        if scope=='native':cap=2*MIB
        elif cat=='allocator':cap=4096 if p.name.startswith('allocation-input-') else 8192
        elif cat=='decision':cap=65536
        elif p.name.startswith('state-'):cap=self.STATE_BYTES
        elif scope=='workspace':cap=2*MIB
        elif any(k in p.name for k in ('before-constructor','before-first-step','runtime-link')):cap=MIB
        else:cap=4*MIB
        if size>cap:raise QuotaStop('perfile_cap')
        if p.exists() and p not in self.records:raise QuotaStop('untracked_existing_output')
        if p in self.records and p.stat().st_size!=self.records[p][0]:raise QuotaStop('external_output_mutation')
        t=Ticket(p,scope,cat,size,is_control);self.pending[p]=t
        try:
            self._validate()
            for volume in ('/tmp','/workspace'):
                # Include all other in-flight reservations; no concurrent write
                # can spend the same free bytes. Existing old output stays live
                # throughout atomic replacement, hence charge the full new size.
                held=sum(x.size for x in self.pending.values() if (x.scope=='workspace')==(volume=='/workspace'))
                if self.free_bytes(volume)-held<self.RESERVE_BYTES:raise QuotaStop('free_reserve:'+volume)
        except BaseException:
            self.pending.pop(p,None);raise
        return t

    def abort(self,ticket):self.pending.pop(ticket.path,None)

    def commit(self,ticket):
        p=ticket.path
        if self.pending.get(p)!=ticket or not p.is_file() or p.stat().st_size!=ticket.size:raise QuotaStop('commit_without_exact_published_file')
        self.records[p]=(ticket.size,ticket.scope,ticket.category,ticket.control);self.pending.pop(p);self._validate()

    @staticmethod
    def _fsync_directory(path):
        fd=os.open(path,os.O_RDONLY | os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)

    def _publish(self,ticket,data,exclusive=False):
        p=ticket.path;temporary=None;published=False
        if not isinstance(data,bytes) or len(data)!=ticket.size:
            self.abort(ticket);raise QuotaStop('serialized_size_changed')
        charged_temp=False
        try:
            if self.temporary_bytes+len(data)>self.TEMP_BYTES:raise QuotaStop('aggregate_temporary_cap')
            self.temporary_bytes+=len(data);charged_temp=True
            p.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile('wb',dir=p.parent,prefix=p.name+'.',suffix='.tmp',delete=False) as f:
                temporary=Path(f.name);os.chmod(temporary,0o600);f.write(data);f.flush();os.fsync(f.fileno())
            if exclusive:os.link(temporary,p)
            else:os.replace(temporary,p);temporary=None
            published=True
            # A synced file alone does not durably publish its new name.
            self._fsync_directory(p.parent)
            self.commit(ticket)
            if p.read_bytes()!=data:raise QuotaStop('full_readback_mismatch')
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink();self._fsync_directory(p.parent)
            if charged_temp:self.temporary_bytes-=len(data)
            if published and p.is_file():
                self.records[p]=(p.stat().st_size,ticket.scope,ticket.category,ticket.control)
            self.abort(ticket)

    def write_bytes(self,path,data,*,exclusive=False,control=None):
        if not isinstance(data,bytes):raise QuotaStop('bytes_required')
        t=self.reserve(path,len(data),control);self._publish(t,data,exclusive)

    def save(self,path,value,*,control=None):
        data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        self.write_bytes(path,data,control=control)

    def save_receipt(self,path,value,*,control=None):
        from retry.pilot420_json import json_ready
        import hashlib
        ready=json_ready(value);data=(json.dumps(ready,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        self.write_bytes(path,data,exclusive=True,control=control)
        return hashlib.sha256(json.dumps(ready,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

    def summary(self):
        rows=self._effective();return {'retained':len(self.records),'pending':len(self.pending),'temporary_bytes':self.temporary_bytes,'files':{s:sum(v[1]==s for v in rows.values()) for s in ('model','native','workspace')},'bytes':{s:sum(v[0] for v in rows.values() if v[2]==s) for s in ('model','native','workspace','allocator','decision')}}

    def full_readback(self):
        import hashlib
        if self.pending or self.temporary_bytes:raise QuotaStop('unfinished_writes')
        result={}
        for p,(size,scope,category,control) in self.records.items():
            if not p.is_file() or p.is_symlink():raise QuotaStop('readback_not_regular')
            data=p.read_bytes()
            if len(data)!=size:raise QuotaStop('readback_size_changed')
            result[str(p)]={'bytes':size,'sha256':hashlib.sha256(data).hexdigest()}
        for root in (self.model_dir,self.native_dir):
            if {p.resolve() for p in root.rglob('*') if p.is_file()}!={p for p in self.records if root in p.parents}:raise QuotaStop('untracked_output_on_readback')
        self._validate()
        return result

    def model_quota(self):
        """Attach unchanged481 packing/reader logic with central write guards."""
        if self.model is not None:return self.model
        codec=self.codec_module
        if codec is None:raise QuotaStop('explicit_isolated_codec_required')
        owner=self
        class ModelQuota(codec.Quota):
            STATES_MAX=260
            STATE_MAX=512*1024
            NONSTATE_MODEL_MAX=62*MIB
            def __init__(self):
                super().__init__(owner.model_dir,owner.MODEL_BYTES,owner.ALLOCATOR_BYTES,owner.DECISION_BYTES)
                self.original_save=self.oldsave;self.original_receipt=self.oldreceipt
                self.oldsave=lambda p,v: self.publish(p,v,False)
                self.oldreceipt=lambda p,v: self.publish(p,v,True)
            def cap(self,p):
                if p.name.startswith('state-'):return self.STATE_MAX
                if any(k in p.name for k in ('before-constructor','before-first-step','runtime-link')):return MIB
                return min(super().cap(p),4*MIB)
            def before(self,path,value):
                p,n=super().before(path,value)
                owner.reserve(p,n)
                return p,n
            def publish(self,path,value,receipt):
                p=Path(path).resolve();ticket=owner.pending.get(p)
                if ticket is None:raise QuotaStop('codec_write_without_reservation')
                ready=codec.json_ready(value) if receipt else value
                data=(json.dumps(ready,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
                owner._publish(ticket,data,receipt)
                return codec.canonical(value) if receipt else None
            def install(self):
                mappings=[(self.original_save,self.save),(self.original_receipt,self.save_receipt),(codec.ORIGINAL_READ,codec.read),(codec.ORIGINAL_LOAD,codec.load_receipt)]
                if owner.install_modules is None:raise QuotaStop('explicit_install_modules_required')
                modules=owner.install_modules() if callable(owner.install_modules) else owner.install_modules
                for module in modules:
                    if module is codec:continue
                    if module is not None:
                        for k,v in list(vars(module).items()):
                            for old,new in mappings:
                                if v is old:setattr(module,k,new);break
                return self
        self.model=ModelQuota();return self.model
