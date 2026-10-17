"""Strict489 geometry-only output accounting; standard library, no physics.

Two control files and64KiB are reserved inside40 files and16MiB. The caller
must mark its result/stop records control=True; all other outputs are data.
Only this instance may write its flat, newly assigned output directory.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading

MIB=1024**2

class QuotaStop(RuntimeError):pass

class Quota:
    MAX_FILES=40
    MAX_BYTES=16*MIB
    FILE_BYTES=2*MIB
    TEMP_BYTES=2*MIB
    CONTROL_FILES=2
    CONTROL_BYTES=64*1024
    RESERVE_BYTES=512*MIB
    CONTROL_NAMES=frozenset(('result.json','stop.json','stop-private.json','result-private.json'))

    def __init__(self,directory,free_bytes=None):
        original=Path(directory)
        if original.is_symlink():raise QuotaStop('489_directory_symlink')
        self.directory=original.resolve();self.directory.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.free_bytes=free_bytes or (lambda p:shutil.disk_usage(p).free)
        self.records={};self.temporary_bytes=0;self.lock=threading.Lock()
        for p in self.directory.iterdir():
            if not p.is_file() or p.is_symlink():raise QuotaStop('489_existing_nonregular_output')
            b=p.read_bytes();self.records[p.name]=(len(b),self._sha(b),p.name in self.CONTROL_NAMES)
        self._validate(self.records);self.diskpreflight()

    @staticmethod
    def _sha(data):return hashlib.sha256(data).hexdigest()

    def _path(self,name):
        if not isinstance(name,str) or not name or name in ('.','..') or Path(name).name!=name or '/' in name or '\\' in name:
            raise QuotaStop('489_basename_required')
        p=self.directory/name
        if p.is_symlink():raise QuotaStop('489_output_symlink')
        return p

    def _validate(self,rows):
        if len(rows)>self.MAX_FILES:raise QuotaStop('489_file_cap40')
        if sum(x[0] for x in rows.values())>self.MAX_BYTES:raise QuotaStop('489_byte_cap16MiB')
        if any(x[0]>self.FILE_BYTES for x in rows.values()):raise QuotaStop('489_perfile2MiB')
        data=[x for x in rows.values() if not x[2]];control=[x for x in rows.values() if x[2]]
        if len(data)>self.MAX_FILES-self.CONTROL_FILES:raise QuotaStop('489_control_slot_reserve')
        if sum(x[0] for x in data)>self.MAX_BYTES-self.CONTROL_BYTES:raise QuotaStop('489_control_byte_reserve')
        if len(control)>self.CONTROL_FILES or sum(x[0] for x in control)>self.CONTROL_BYTES:raise QuotaStop('489_control_pool')

    def diskpreflight(self,additional_bytes=0):
        if type(additional_bytes) is not int or additional_bytes<0:raise QuotaStop('489_invalid_disk_reservation')
        result={}
        for volume in ('/tmp','/workspace'):
            free=self.free_bytes(volume);result[volume]=free
            if free-additional_bytes<self.RESERVE_BYTES:raise QuotaStop('489_disk_reserve:'+volume)
        return result

    def _check_actual(self):
        paths=list(self.directory.iterdir())
        if {p.name for p in paths}!=set(self.records):raise QuotaStop('489_untracked_or_missing_output')
        for p in paths:
            if not p.is_file() or p.is_symlink():raise QuotaStop('489_nonregular_output')
            b=p.read_bytes();size,digest,_=self.records[p.name]
            if len(b)!=size or self._sha(b)!=digest:raise QuotaStop('489_external_output_mutation')

    def write_json(self,name,value,control=False,exclusive=False):
        data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        return self.write_bytes(name,data,control,exclusive)

    def write_bytes(self,name,data,control=False,exclusive=False):
        if not isinstance(data,bytes):raise QuotaStop('489_bytes_required')
        with self.lock:
            p=self._path(name);self._check_actual()
            if type(control) is not bool or type(exclusive) is not bool:raise QuotaStop('489_boolean_flags_required')
            if control and name not in self.CONTROL_NAMES:raise QuotaStop('489_control_name_required')
            proposed=dict(self.records);proposed[name]=(len(data),self._sha(data),control)
            self._validate(proposed)
            if self.temporary_bytes+len(data)>self.TEMP_BYTES:raise QuotaStop('489_temp2MiB')
            self.diskpreflight(len(data))
            temporary=None;published=False;self.temporary_bytes+=len(data)
            try:
                with tempfile.NamedTemporaryFile('wb',dir=self.directory,prefix=name+'.',suffix='.tmp',delete=False) as f:
                    temporary=Path(f.name);os.chmod(temporary,0o600);f.write(data);f.flush();os.fsync(f.fileno())
                if exclusive:os.link(temporary,p)
                else:os.replace(temporary,p);temporary=None
                published=True;self.records=proposed
                # A returned digest always authenticates actual retained bytes.
                if p.read_bytes()!=data:raise QuotaStop('489_publish_readback')
            finally:
                if temporary is not None and temporary.exists():temporary.unlink()
                self.temporary_bytes-=len(data)
                if published and p.is_file():
                    actual=p.read_bytes();self.records[name]=(len(actual),self._sha(actual),control)
            return dict(path=str(p),bytes=len(data),sha256=self._sha(data),control=control)

    def inventory(self):
        with self.lock:
            self._check_actual();self._validate(self.records)
            entries=[dict(path=str(self.directory/name),bytes=size,sha256=digest,control=control) for name,(size,digest,control) in sorted(self.records.items())]
            return dict(files=entries,file_count=len(entries),bytes=sum(x['bytes'] for x in entries),temporary_bytes=self.temporary_bytes,control_files=sum(x['control'] for x in entries),control_bytes=sum(x['bytes'] for x in entries if x['control']))
