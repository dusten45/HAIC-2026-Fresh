"""495 same byte/file caps, compact lossless logical observers and bounded sidecars."""
import copy,json,re,types
from pathlib import Path
from retry.quota492 import RunQuota as OriginalQuota,QuotaStop,MIB
from retry.pilot420_json import json_ready

# Prospective format bounds. Separate allocator/decision caps remain8MiB each.
MODEL_NONSTATE_BOUND=(106*192*1024+384*1024+6*768*1024+113*3*24*1024+113*16*1024+536*16*1024+134*64*1024+26*16*1024+26*8*1024+MIB+2*MIB+4*MIB+MIB)
MODEL_FILE_BOUND=sum([113,339,113,260,26,26,536,134,52,26,1,2,2,16])
NATIVE_FILE_BOUND=sum([710,387,516,1,1,1,1,1,2,1,10,1,1,1,2,16])
class RunQuota(OriginalQuota):
    def reserve(self,path,size,control=None):
        p=Path(path);scope=self.scope(p);n=p.name
        limit=None
        if n.startswith('direct495-'):limit=64*1024 if '-bundle' in n else 16*1024
        elif scope=='model':
            if any(k in n for k in ('before-constructor','before-first-step','runtime-link')):limit=24*1024
            elif 'before-integration' in n:limit=16*1024
            elif re.fullmatch(r'D495-A_(control|variant)_(1|2|held)-private.json',n):limit=768*1024
            elif n=='D495-A_source_warm-private.json':limit=384*1024
            elif n.startswith('D495-A_') and n.endswith('-private.json') and not any(k in n for k in ('source-gate','root-authority')):limit=192*1024
            elif n.startswith('context-'):limit=16*1024
            elif n.startswith('own-link-'):limit=8*1024
            elif n in ('branch-results-private.json','query-details-private.json'):limit=2*MIB
            elif n in ('plan.json','D495-A-source-gate-private.json','D495-A-root-authority-private.json'):limit=MIB
        if limit is not None and size>limit:raise QuotaStop('495_format_cap:'+n+':'+str(size)+'>'+str(limit))
        return super().reserve(path,size,control)

def prospective():
    if not(MODEL_NONSTATE_BOUND<=62*MIB and MODEL_FILE_BOUND<=1840 and NATIVE_FILE_BOUND<=1664):raise QuotaStop('495_prospective_bounds')
    return dict(model_nonstate_worst_bytes=MODEL_NONSTATE_BOUND,model_nonstate_cap=62*MIB,model_state_worst_bytes=260*512*1024,model_bytes_cap=192*MIB,model_files_worst=MODEL_FILE_BOUND,model_files_cap=1840,native_files_worst=NATIVE_FILE_BOUND,native_files_cap=1664,tick_receipt_max=16384,bundle_max=65536,logical_observer_records_embedded_losslessly=True,termination_slots=16,termination_bytes=MIB)

class PackedObservers495:
    """Two logical observer records share the existing complete child payload.

    H6 never uses legacy H13 observation-file references. Observer methods run
    unchanged; records retain every field under observer_records495. No prior
    file is touched and no old raw file is deleted or archived.
    """
    def __init__(self,graph,codec,codec_module):
        self.graph=graph;self.codec=codec;self.codec_module=codec_module;self.logical={}
    def target(self,path):
        p=Path(path);n=p.name
        if n.endswith('-observer-private.json'):label=n[:-len('-observer-private.json')];kind='observer-private'
        elif n.endswith('-observer-final-private.json'):
            label=n[:-len('-observer-final-private.json')]
            # Prefix contains child_id before the semantic label.
            index=label.index('D495-A_');label=label[index:];kind='observer-final'
        else:return None
        if not label.startswith('D495-A_'):raise QuotaStop('495_observer_scope')
        return p.parent/(label+'-private.json'),kind
    def save(self,path,value):return self.write(path,value,False)
    def save_receipt(self,path,value):return self.write(path,value,True)
    def write(self,path,value,is_receipt):
        target=self.target(path)
        if target is None:
            if hasattr(self,'owner_extra') and isinstance(value,dict) and {'rows','final_state','controller_memory'}<=set(value):
                value=copy.deepcopy(value)
                label=Path(path).name[:-len('-private.json')]
                value.update(self.owner_extra(label))
            return self.codec.save_receipt(path,value) if is_receipt else self.codec.save(path,value)
        dest,kind=target
        if not dest.is_file():raise QuotaStop('495_child_payload_before_observer_required')
        full=self.codec_module.load_receipt(dest)
        observer=full.setdefault('observer_records495',{})
        if kind in observer:raise QuotaStop('495_duplicate_logical_observer')
        observer[kind]=copy.deepcopy(value)
        self.codec.save(dest,full)
        decoded=self.codec_module.load_receipt(dest)
        if self.codec_module.canonical(decoded['observer_records495'][kind])!=self.codec_module.canonical(value):raise QuotaStop('495_logical_observer_roundtrip')
        self.logical[str(path)]=dict(path=str(dest),pointer='/observer_records495/'+kind)
        return self.codec_module.canonical(value) if is_receipt else None
    def install(self):
        self.codec.install()
        for module in self.graph.modules.values():
            if module is self.codec_module:continue
            for k,v in list(vars(module).items()):
                if isinstance(v,types.MethodType) and v.__self__ is self.codec:
                    if v.__func__.__name__=='save':setattr(module,k,self.save)
                    elif v.__func__.__name__=='save_receipt':setattr(module,k,self.save_receipt)
        return self
