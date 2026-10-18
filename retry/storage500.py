"""Whole-output quota for the proposed four-world screening, no physics imports.

Admission uses final serialized bytes (after any lossless codec envelope).
The future runtime must route every writer here; this module is not installed
into a simulator by500. Synthetic ledger tests do not allocate the full quota.
"""
from pathlib import Path
import hashlib
import os
import shutil

MIB=1024**2
LIMITS={'state':(320,512*1024,160*MIB),
        'tick':(1792,16*1024,28*MIB),
        'bundle':(448,64*1024,28*MIB),
        'other':(128,4*MIB,16*MIB)}
TOTAL=256*MIB
FINAL_MAX=232*MIB
FILES_MAX=2688
CLOSING_BYTES=256*1024
CLOSING_FILES=8

class StorageStop(ValueError):pass

class Store500:
    def __init__(self, root=None):
        self.root=None if root is None else Path(root)
        self.used={};self.counts={k:0 for k in LIMITS};self.sizes={k:0 for k in LIMITS}
        self.states={};self.closing=False;self.failed=False
        if self.root is not None:
            if self.root.exists():raise StorageStop('ROOT_EXISTS')
            self.root.mkdir(mode=0o700)
    def before(self,name,kind,n):
        if self.failed:raise StorageStop('FAILED_WRITE_NO_MORE_OUTPUT')
        if kind not in LIMITS or type(n) is not int or n<0:raise StorageStop('ENTRY_TYPE')
        if type(name) is not str or not name or Path(name).name!=name or name in ('.','..'):
            raise StorageStop('ENTRY_NAME')
        if name in self.used:raise StorageStop('IMMUTABLE_ENTRY')
        count,per,aggregate=LIMITS[kind]
        if self.counts[kind]+1>count or n>per or self.sizes[kind]+n>aggregate:
            raise StorageStop('CATEGORY_QUOTA')
        if not self.closing and kind=='other':
            if self.counts[kind]+1>count-CLOSING_FILES or self.sizes[kind]+n>aggregate-CLOSING_BYTES:
                raise StorageStop('CLOSING_RESERVE')
        final=sum(self.sizes.values())+n
        if final>FINAL_MAX or len(self.used)+2>FILES_MAX:raise StorageStop('FINAL_OR_ATOMIC_FILE_QUOTA')
        # Both new final object and atomic temporary are charged at peak, even
        # when replacement is atomic. No old file overwrite/reclamation credits.
        if final+n>TOTAL:raise StorageStop('ATOMIC_TEMP_QUOTA')
        return {'final_bytes':final,'atomic_peak_bytes':final+n,'files':len(self.used)+1}
    def record(self,name,kind,n,digest):
        self.before(name,kind,n)
        self.used[name]=(kind,n,digest);self.counts[kind]+=1;self.sizes[kind]+=n
    def publish(self,name,kind,data):
        if not isinstance(data,bytes):raise StorageStop('FINAL_BYTES_REQUIRED')
        h=hashlib.sha256(data).hexdigest();self.before(name,kind,len(data))
        if self.root is not None:
            if shutil.disk_usage(self.root).free < 512*MIB+len(data):
                raise StorageStop('FREE_RESERVE')
            p=self.root/name;temp=p.with_name(p.name+'.tmp500')
            if p.exists() or temp.exists():raise StorageStop('STALE_OR_EXISTING_FILE')
            try:
                with temp.open('xb') as f:
                    os.chmod(temp,0o600);f.write(data);f.flush();os.fsync(f.fileno())
                # Never replace an existing receipt, including an unexpected
                # concurrent writer. Single-link publish is atomic/exclusive.
                os.link(temp,p);temp.unlink()
                if p.read_bytes()!=data:raise StorageStop('READBACK')
            except BaseException:
                self.failed=True
                # Failed write remains evidence. Caller stops; no retries or
                # deleting unrelated artifacts. Failed temp counts admitted peak; all
                # subsequent writes are blocked, including attempted closeout.
                # World teardown is in-memory and the parent reports the stop.
                raise
        self.record(name,kind,len(data),h)
        return {'name':name,'sha256':h,'bytes':len(data)}
    def intern_state(self,data):
        if not isinstance(data,bytes):raise StorageStop('FINAL_BYTES_REQUIRED')
        h=hashlib.sha256(data).hexdigest()
        if h in self.states:
            old=self.states[h]
            if old['bytes']!=len(data):raise StorageStop('STATE_DIGEST_COLLISION')
            if self.root is not None and (self.root/old['name']).read_bytes()!=data:
                raise StorageStop('STATE_INTERN_BYTES_MISMATCH')
            return dict(old)
        ref=self.publish('state-'+h+'.json','state',data);self.states[h]=ref
        return dict(ref)
