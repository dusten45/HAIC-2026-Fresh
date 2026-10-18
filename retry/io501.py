"""Pure Store500 adapter for an explicitly supplied isolated481 codec graph.

No simulation modules are imported. The caller owns registration and execution.
All immutable objects use final serialized-byte admission and exact readback.
"""
import copy
import hashlib
import json
from pathlib import Path

CHUNKS='__haic_list_chunks501__'
CONTENT='__haic_content_ref501__'
CONTENT_THRESHOLD=128*1024
class AdapterStop(RuntimeError):pass

class Adapter501:
    def __init__(self,runtime,store,*,logical_root=None):
        self.runtime=runtime;self.store=store
        if store.root is None:raise AdapterStop('501_PHYSICAL_STORE_REQUIRED')
        self.root=Path(store.root).resolve()
        self.logical_root=Path(logical_root or self.root).resolve()
        self.codec=runtime.import_module('io481')
        self.aliases={};self.logical_hashes={};self.versions={};self.objects={}
        self.original_read=self.codec.ORIGINAL_READ
        self.original_load=self.codec.ORIGINAL_LOAD
        self.original_sha=runtime.import_module('loss389_analyze').sha
        self.original_save=runtime.import_module('loss389_analyze').save
        self.original_receipt=runtime.import_module('receipt421_io').save_receipt
        self.mappings=[];self.patched=set()
    def encode(self,value):
        return (json.dumps(self.codec.json_ready(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    def key(self,path):
        p=Path(path).resolve()
        if p!=self.logical_root and self.logical_root not in p.parents:raise AdapterStop('501_WRITE_OUTSIDE_REGISTERED_ROOT')
        return str(p)
    def publish(self,name,kind,value):
        data=self.encode(value);ref=self.store.publish(name,kind,data)
        path=self.root/ref['name']
        if path.read_bytes()!=data:raise AdapterStop('501_COMPLETE_READBACK')
        return dict(path=str(path),sha256=ref['sha256'],bytes=ref['bytes'])
    def intern(self,value):
        if isinstance(value,dict):
            if set(value)=={'physical','finish_tracker','elapsed_raw_steps'}:
                h=self.codec.canonical(value);name='state-'+h+'.json'
                obj={'full_state':value,'sha256':h}
                if name not in self.objects:self.objects[name]=self.publish(name,'state',obj)
                elif self.encode(obj)!=(self.root/name).read_bytes():raise AdapterStop('501_STATE_DIGEST_COLLISION')
                return {self.codec.STATE_KEY:h}
            return {k:self.intern(v) for k,v in value.items()}
        if isinstance(value,list):return [self.intern(v) for v in value]
        return value
    def chunks(self,value):
        if isinstance(value,dict):return {k:self.chunks(v) for k,v in value.items()}
        if not isinstance(value,list):return value
        value=[self.chunks(v) for v in value]
        if len(self.encode(value))<=1024*1024:return value
        refs=[];part=[]
        def flush():
            if not part:return
            data=self.encode(part);h=hashlib.sha256(data).hexdigest();name='chunk501-'+h+'.json'
            if name not in self.objects:self.objects[name]=self.publish(name,'other',part)
            refs.append(dict(self.objects[name],count=len(part)))
        for item in value:
            if part and len(self.encode(part+[item]))>1024*1024:flush();part=[]
            if len(self.encode([item]))>4*1024*1024:raise AdapterStop('501_INDIVIDUAL_METADATA_ITEM_4MIB')
            part.append(item)
        flush();return {CHUNKS:refs,'count':len(value)}
    def content_intern(self,value):
        """Other metadata only: exact JSON containers at fixed128KiB threshold.

        Children are interned first. The physical object is ordinary lossless
        JSON; its reference carries its final byte hash, size and container type.
        """
        if isinstance(value,dict):
            if set(value) in ({self.codec.STATE_KEY},{CHUNKS,'count'},{CONTENT}):return value
            value={k:self.content_intern(v) for k,v in value.items()}
        elif isinstance(value,list):value=[self.content_intern(v) for v in value]
        else:return value
        data=self.encode(value)
        if len(data)<CONTENT_THRESHOLD or len(data)>1024*1024:return value
        h=hashlib.sha256(data).hexdigest();name='content501-'+h+'.json'
        if name not in self.objects:self.objects[name]=self.publish(name,'other',value)
        elif (self.root/name).read_bytes()!=data:raise AdapterStop('501_CONTENT_DIGEST_COLLISION')
        return {CONTENT:dict(self.objects[name],container='dict' if isinstance(value,dict) else 'list')}
    def unchunk(self,value):
        if isinstance(value,dict):
            if set(value)=={CONTENT}:
                ref=value[CONTENT];p=Path(ref['path']);data=p.read_bytes()
                if hashlib.sha256(data).hexdigest()!=ref['sha256'] or len(data)!=ref['bytes']:raise AdapterStop('501_CONTENT_AUTH')
                obj=json.loads(data)
                if ref.get('container')!=('dict' if isinstance(obj,dict) else 'list' if isinstance(obj,list) else None):raise AdapterStop('501_CONTENT_CONTAINER')
                return self.unchunk(obj)
            if set(value)=={CHUNKS,'count'}:
                rows=[]
                for ref in value[CHUNKS]:
                    p=Path(ref['path']);data=p.read_bytes()
                    if hashlib.sha256(data).hexdigest()!=ref['sha256'] or len(data)!=ref['bytes']:raise AdapterStop('501_CHUNK_AUTH')
                    block=json.loads(data)
                    if type(block) is not list or len(block)!=ref['count']:raise AdapterStop('501_CHUNK_COUNT')
                    rows.extend(self.unchunk(block))
                if len(rows)!=value['count']:raise AdapterStop('501_CHUNKS_TOTAL')
                return rows
            return {k:self.unchunk(v) for k,v in value.items()}
        if isinstance(value,list):return [self.unchunk(v) for v in value]
        return value
    def kind(self,path):
        n=Path(path).name
        if n.startswith(('direct501-','direct495-')) and '-bundle' not in n:return 'tick'
        if '-bundle' in n:return 'bundle'
        return 'other'
    def _save(self,path,value,receipt,kind=None):
        key=self.key(path);logical_hash=self.codec.canonical(value)
        if key in self.aliases:
            if self.logical_hashes[key]==logical_hash:return logical_hash
            if receipt:raise AdapterStop('501_IMMUTABLE_LOGICAL_RECEIPT')
        category=kind or self.kind(path)
        payload=self.intern(self.codec.json_ready(value))
        # Direct tick/bundle readers only know481 refs; never emit501 generic
        # content/chunk refs into these already finite16/64KiB categories.
        if category=='other':payload=self.chunks(self.content_intern(payload))
        packed={self.codec.CODEC_KEY:1,'payload':payload,'decoded_sha256':logical_hash}
        version=self.versions.get(key,0)+1
        # Full logical path hash prevents colliding basenames; physical names are
        # versioned, never overwritten or credited as reclaimed output.
        tag=hashlib.sha256(key.encode()).hexdigest()[:20]
        name='logical501-'+tag+'-v'+str(version)+'-'+Path(path).name
        ref=self.publish(name,category,packed)
        self.aliases[key]=ref;self.logical_hashes[key]=logical_hash;self.versions[key]=version
        if self.codec.canonical(self.read(path))!=logical_hash:raise AdapterStop('501_LOGICAL_ROUNDTRIP')
        return logical_hash
    def save(self,path,value):self._save(path,value,False)
    def save_receipt(self,path,value):return self._save(path,value,True)
    def writer(self,path,value,*,kind=None):
        self._save(path,value,True,kind)
        return dict(**self.physical_ref(path),pointer='')
    def physical_sha(self,path):
        key=str(Path(path).resolve())
        if key in self.aliases:
            ref=self.aliases[key]
            if hashlib.sha256(Path(ref['path']).read_bytes()).hexdigest()!=ref['sha256']:raise AdapterStop('501_SHA_ALIAS_AUTH')
            return ref['sha256']
        return self.original_sha(path)
    sha=physical_sha
    def account_external(self,path,*,name=None):
        """Charge existing501 preparation output without copying its bytes."""
        p=Path(path).resolve();data=p.read_bytes()
        label=name or ('external501-'+hashlib.sha256(str(p).encode()).hexdigest()+'.json')
        self.store.record(label,'other',len(data),hashlib.sha256(data).hexdigest())
        return dict(path=str(p),name=label,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    def physical_ref(self,path):return copy.deepcopy(self.aliases[self.key(path)])
    def raw_read(self,path):
        key=str(Path(path).resolve())
        if key in self.aliases:
            ref=self.aliases[key];data=Path(ref['path']).read_bytes()
            if hashlib.sha256(data).hexdigest()!=ref['sha256']:raise AdapterStop('501_ALIAS_AUTH')
            return json.loads(data)
        p=Path(path).resolve()
        if p.parent==self.root and p.name in self.store.used:
            data=p.read_bytes()
            if hashlib.sha256(data).hexdigest()!=self.store.used[p.name][2]:raise AdapterStop('501_PHYSICAL_AUTH')
            return json.loads(data)
        return self.original_read(path)
    def read(self,path):
        value=self.raw_read(path)
        if isinstance(value,dict) and self.codec.CODEC_KEY in value:
            if value[self.codec.CODEC_KEY]!=1 or set(value)!={self.codec.CODEC_KEY,'payload','decoded_sha256'}:raise AdapterStop('501_CODEC_SCHEMA')
            expanded=self.unchunk(value['payload'])
            base=self.root if str(Path(path).resolve()) in self.aliases or Path(path).resolve().parent==self.root else Path(path).resolve().parent
            decoded=self.codec.restore_bytes(self.expand(expanded,base))
            if self.codec.canonical(decoded)!=value['decoded_sha256']:raise AdapterStop('501_DECODED_DIGEST')
            return decoded
        return value
    def expand(self,value,base=None):
        base=self.root if base is None else Path(base)
        if isinstance(value,dict):
            if set(value)=={self.codec.STATE_KEY}:
                h=value[self.codec.STATE_KEY]
                if type(h) is not str or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise AdapterStop('501_STATE_REF')
                obj=self.raw_read(base/('state-'+h+'.json'))
                if set(obj)!={'full_state','sha256'} or obj['sha256']!=h or self.codec.canonical(obj['full_state'])!=h:raise AdapterStop('501_STATE_AUTH')
                return obj['full_state']
            return {k:self.expand(v,base) for k,v in value.items()}
        if isinstance(value,list):return [self.expand(v,base) for v in value]
        return value
    def load_receipt(self,path):return self.codec.restore_bytes(self.read(path))
    def install(self):
        if not self.mappings:
            self.mappings=[(self.original_save,self.save),(self.original_receipt,self.save_receipt),
                (self.original_read,self.read),(self.original_load,self.load_receipt),(self.original_sha,self.physical_sha),
                (self.codec.read,self.read),(self.codec.load_receipt,self.load_receipt)]
        modules=self.runtime.modules
        modules=modules.values() if isinstance(modules,dict) else modules
        for module in list(modules):
            if not getattr(module,'__private_clone492__',False):raise AdapterStop('501_NONISOLATED_MODULE')
            for key,value in list(vars(module).items()):
                for old,new in self.mappings:
                    if value is old:setattr(module,key,new);self.patched.add((module.__name__,key));break
        self.codec.ORIGINAL_READ=self.raw_read
        self.codec.ORIGINAL_LOAD=self.load_receipt
        self.codec.read=self.read;self.codec.load_receipt=self.load_receipt
        # Graph.exec_module calls codec.install after every later import.
        self.codec.install=self.install
        return self
    def audit(self):
        misses=[];aliases=[]
        modules=self.runtime.modules
        modules=modules.values() if isinstance(modules,dict) else modules
        old_ids={id(old) for old,new in self.mappings}
        for module in list(modules):
            for key,value in vars(module).items():
                if module is self.codec and key in ('ORIGINAL_READ','ORIGINAL_LOAD'):continue
                if id(value) in old_ids:misses.append(module.__name__+':'+key)
                if key in ('save','save_receipt','read','load_receipt','sha'):aliases.append(module.__name__+':'+key)
        if misses:raise AdapterStop('501_UNROUTED_FUNCTION_ALIASES:'+','.join(misses))
        return dict(passed=True,alias_slots=aliases,patched_aliases=len(self.patched),scope='IDENTITY_ALIASES_ONLY_DIRECT_PATH_WRITERS_REQUIRE_CALLSITE_ADAPTER')
    def summary(self):
        return dict(logical_files=len(self.aliases),physical_files=len(self.store.used),
                    serialized_bytes=sum(self.store.sizes.values()),categories=dict(self.store.counts),
                    patched_aliases=len(self.patched),immutable_versions=True)
