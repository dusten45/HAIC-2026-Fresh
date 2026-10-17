"""Fresh-root467 gzip-first immutable evidence; explicit descriptors only."""
import gzip,hashlib,json,os,re,shutil,tempfile,time
from pathlib import Path
from retry.pilot420_json import json_ready,restore_bytes
from retry.receipt421_io import receipt_digest

SCHEMA='HAIC_EVIDENCE467_DESCRIPTOR_V1'
KIND='gzip-json-receipt'
JSONL_KIND='gzip-jsonl-records'
MAX_LOGICAL_BYTES=32*1024**2
MAX_TOTAL_PHYSICAL_BYTES=64*1024**2
RESERVE_BYTES=512*1024**2

class Evidence467Error(RuntimeError):pass

class Evidence467:
    def __init__(self,directory,resource_guard=None,fault_hook=None):
        self.directory=Path(directory);self.resolved_root=self.directory.resolve(strict=False);self.root_identity=None
        if self.directory.exists() or self.directory.is_symlink():raise Evidence467Error('fresh_root_required')
        self.resource_guard=resource_guard;self.fault_hook=fault_hook
        self.cpu_start=time.process_time();self.wall_start=time.perf_counter();self.events=[];self.readonly=False;self.logical_reserved=0;self.attempted_names=set()
        self._guard();self.directory.mkdir(mode=0o700)
        stat=self.directory.stat();self.root_identity=(stat.st_dev,stat.st_ino)
        marker=(json.dumps(dict(schema=SCHEMA,kind='fresh-gzip-evidence-root'),sort_keys=True)+'\n').encode('utf-8')
        self._guard(len(marker))
        with (self.directory/'_root467.json').open('xb') as raw:
            os.chmod(raw.name,0o600)
            if raw.write(marker)!=len(marker):raise Evidence467Error('short_root_marker_write')
            raw.flush();os.fsync(raw.fileno())
        self._sync_directory()
    @classmethod
    def open_readonly(cls,directory,resource_guard=None):
        obj=cls.__new__(cls);obj.directory=Path(directory);obj.resolved_root=obj.directory.resolve(strict=False);obj.root_identity=None
        if not obj.directory.is_dir() or obj.directory.is_symlink():raise Evidence467Error('readonly_root_required')
        stat=obj.directory.stat();obj.root_identity=(stat.st_dev,stat.st_ino)
        obj.resource_guard=resource_guard;obj.fault_hook=None;obj.cpu_start=time.process_time();obj.wall_start=time.perf_counter();obj.events=[];obj.readonly=True;obj.logical_reserved=0;obj.attempted_names=set()
        obj._guard();marker=obj._path('_root467.json')
        if marker.stat().st_size>2048:raise Evidence467Error('root_schema_size')
        if json.loads(marker.read_text(encoding='utf-8'))!=dict(schema=SCHEMA,kind='fresh-gzip-evidence-root'):raise Evidence467Error('root_schema')
        return obj
    def _fault(self,stage,**details):
        if self.fault_hook is not None:self.fault_hook(stage,details)
    def _guard(self,additional=0):
        if self.directory.is_symlink() or self.directory.resolve(strict=False)!=self.resolved_root:raise Evidence467Error('root_identity_or_symlink_changed')
        if self.root_identity is not None:
            stat=self.directory.stat()
            if (stat.st_dev,stat.st_ino)!=self.root_identity:raise Evidence467Error('root_inode_changed')
        if self.resource_guard is not None:self.resource_guard()
        if time.process_time()-self.cpu_start>=600 or time.perf_counter()-self.wall_start>=900:raise Evidence467Error('CPU600_wall900')
        for volume in ['/tmp','/workspace']:
            if shutil.disk_usage(volume).free-additional<RESERVE_BYTES:raise Evidence467Error('reserve512MiB:'+volume)
        if self.directory.exists():
            sizes=0
            for path in self.directory.rglob('*'):
                if path.is_symlink():raise Evidence467Error('symlink_artifact_forbidden')
                if path.is_file():sizes+=path.stat().st_size
            if sizes+additional>MAX_TOTAL_PHYSICAL_BYTES:raise Evidence467Error('total_physical64MiB')
    @staticmethod
    def _name(name):
        if type(name) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}',name) or name in ['.','..']:raise Evidence467Error('invalid_logical_name')
        return name
    def _path(self,name):
        if type(name) is not str or Path(name).name!=name or name in ['.','..']:raise Evidence467Error('invalid_relative_path')
        path=self.directory/name
        if path.is_symlink():raise Evidence467Error('symlink_artifact_forbidden')
        return path
    def _chunks(self,encoded):
        encoder=json.JSONEncoder(ensure_ascii=False,indent=2,allow_nan=False)
        for text in encoder.iterencode(encoded):
            data=text.encode('utf-8')
            for offset in range(0,len(data),65536):yield data[offset:offset+65536]
        yield b'\n'
    def _jsonl_chunks(self,encoded):
        for row in encoded:
            data=(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
            for offset in range(0,len(data),65536):yield data[offset:offset+65536]
    def _write(self,raw,data,kind):
        self._guard(len(data));self._fault('write',kind=kind,bytes=len(data),offset=raw.tell())
        written=raw.write(data)
        if written!=len(data):raise Evidence467Error('short_write')
        return written
    def _fsync(self,raw,kind):
        raw.flush();self._guard();self._fault('fsync',kind=kind);os.fsync(raw.fileno())
    def _sync_directory(self):
        fd=os.open(self.directory,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    def write_receipt(self,name,value):
        return self._write_evidence(name,value,KIND)
    def write_jsonl(self,name,rows):
        if type(rows) is not list:raise Evidence467Error('JSONL_rows_must_be_list')
        return self._write_evidence(name,rows,JSONL_KIND)
    def _write_evidence(self,name,value,kind):
        if self.readonly:raise Evidence467Error('readonly_writer_forbidden')
        self._name(name);self._guard()
        if name in self.attempted_names:raise Evidence467Error('duplicate_or_failed_attempt_name')
        self.attempted_names.add(name)
        physical=self._path(name+('.json.gz' if kind==KIND else '.jsonl.gz'));descriptor_path=self._path(name+'.descriptor.json')
        if physical.exists() or descriptor_path.exists():raise Evidence467Error('duplicate_receipt')
        encoded=json_ready(value);semantic=receipt_digest(value);logical_count=0;logical_hash=hashlib.sha256();chunks=self._chunks if kind==KIND else self._jsonl_chunks
        # Validate serialization and logical cap before creating an artifact.
        for data in chunks(encoded):
            self._guard();logical_count+=len(data)
            if logical_count>MAX_LOGICAL_BYTES:
                self.logical_reserved+=logical_count
                raise Evidence467Error('logical32MiB')
            logical_hash.update(data)
        self.logical_reserved+=logical_count
        if self.logical_reserved>MAX_LOGICAL_BYTES:raise Evidence467Error('aggregate_logical32MiB')
        fd,temporary_name=tempfile.mkstemp(prefix=name+'.',suffix='.gzip.partial',dir=self.directory)
        temporary=Path(temporary_name);os.chmod(temporary,0o600)
        owner=self
        class GuardedWriter:
            def __init__(self,raw):self.raw=raw
            def write(self,data):return owner._write(self.raw,data,'gzip')
            def flush(self):return self.raw.flush()
            def tell(self):return self.raw.tell()
        # Failures intentionally retain partial/orphan files and never publish
        # a successful descriptor. No catch path repairs or retries the write.
        with os.fdopen(fd,'wb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=GuardedWriter(raw),compresslevel=1,mtime=0) as zipped:
                for data in chunks(encoded):self._guard();zipped.write(data)
            self._fsync(raw,'gzip')
        self._guard();os.link(temporary,physical);self._sync_directory()
        # The temporary is this call's new hardlink, never a prior artifact.
        temporary.unlink()
        stored_hash=hashlib.sha256();stored_count=0
        with physical.open('rb') as raw:
            while True:
                self._guard();data=raw.read(65536)
                if not data:break
                stored_hash.update(data);stored_count+=len(data)
        descriptor=dict(schema=SCHEMA,kind=kind,logical_name=name,physical_relative_path=physical.name,descriptor_relative_path=descriptor_path.name,stored_sha256=stored_hash.hexdigest(),logical_sha256=logical_hash.hexdigest(),receipt_digest=semantic,stored_bytes=stored_count,logical_bytes=logical_count)
        # Real physical reopen/decompression/CRC/schema/hash verification occurs
        # BEFORE descriptor publication, not a comparison to the input object.
        restored=self._read_payload(descriptor)
        if receipt_digest(restored)!=semantic:raise Evidence467Error('prepublication_semantic_readback')
        text=(json.dumps(descriptor,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        self._guard(len(text));fd,temp_descriptor_name=tempfile.mkstemp(prefix=name+'.',suffix='.descriptor.partial',dir=self.directory)
        temp_descriptor=Path(temp_descriptor_name);os.chmod(temp_descriptor,0o600)
        with os.fdopen(fd,'wb') as raw:self._write(raw,text,'descriptor');self._fsync(raw,'descriptor')
        self._fault('descriptor_publish',logical_name=name);self._guard();os.link(temp_descriptor,descriptor_path);self._sync_directory();temp_descriptor.unlink()
        self.read_receipt(descriptor) if kind==KIND else self.read_jsonl(descriptor)
        self.events.append(dict(logical_name=name,physical_readback_verified=True,descriptor_readback_verified=True,stored_bytes=stored_count,logical_bytes=logical_count))
        return descriptor
    def _validate_descriptor(self,descriptor):
        required={'schema','kind','logical_name','physical_relative_path','descriptor_relative_path','stored_sha256','logical_sha256','receipt_digest','stored_bytes','logical_bytes'}
        if type(descriptor) is not dict or set(descriptor)!=required:raise Evidence467Error('descriptor_schema')
        if descriptor['schema']!=SCHEMA or descriptor['kind'] not in [KIND,JSONL_KIND]:raise Evidence467Error('descriptor_kind')
        name=self._name(descriptor['logical_name'])
        if descriptor['physical_relative_path']!=name+('.json.gz' if descriptor['kind']==KIND else '.jsonl.gz') or descriptor['descriptor_relative_path']!=name+'.descriptor.json':raise Evidence467Error('descriptor_path_identity')
        for key in ['stored_sha256','logical_sha256','receipt_digest']:
            if type(descriptor[key]) is not str or not re.fullmatch('[0-9a-f]{64}',descriptor[key]):raise Evidence467Error('descriptor_hash_schema')
        for key,limit in [('stored_bytes',MAX_TOTAL_PHYSICAL_BYTES),('logical_bytes',MAX_LOGICAL_BYTES)]:
            if type(descriptor[key]) is not int or not (0<=descriptor[key]<=limit if key=='logical_bytes' and descriptor['kind']==JSONL_KIND else 0<descriptor[key]<=limit):raise Evidence467Error('descriptor_size_schema')
    def _read_payload(self,descriptor):
        self._validate_descriptor(descriptor);self._guard();path=self._path(descriptor['physical_relative_path'])
        stored_hash=hashlib.sha256();count=0
        with path.open('rb') as raw:
            while True:
                self._guard();data=raw.read(65536)
                if not data:break
                count+=len(data)
                if count>descriptor['stored_bytes']:raise Evidence467Error('stored_length_overrun')
                stored_hash.update(data)
        if count!=descriptor['stored_bytes'] or stored_hash.hexdigest()!=descriptor['stored_sha256']:raise Evidence467Error('stored_hash_or_length')
        logical_hash=hashlib.sha256();parts=[];count=0
        with gzip.open(path,'rb') as stream:
            while True:
                self._guard();data=stream.read(65536)
                if not data:break
                count+=len(data)
                if count>MAX_LOGICAL_BYTES or count>descriptor['logical_bytes']:raise Evidence467Error('logical_length_overrun')
                logical_hash.update(data);parts.append(data)
        if count!=descriptor['logical_bytes'] or logical_hash.hexdigest()!=descriptor['logical_sha256']:raise Evidence467Error('logical_hash_or_length')
        logical=b''.join(parts)
        try:
            text=logical.decode('utf-8')
            def decode(text):return restore_bytes(json.loads(text,parse_constant=lambda x:(_ for _ in ()).throw(Evidence467Error('nonfinite_json'))))
            if descriptor['kind']==KIND:value=decode(text)
            else:
                if text and not text.endswith('\n'):raise Evidence467Error('JSONL_final_newline')
                records=text.split('\n')[:-1] if text else []
                value=[decode(line) for line in records]
                if any(not line for line in records):raise Evidence467Error('JSONL_empty_record')
        except (UnicodeError,ValueError,TypeError) as error:raise Evidence467Error('logical_JSON_schema') from error
        if receipt_digest(value)!=descriptor['receipt_digest']:raise Evidence467Error('receipt_digest_mismatch')
        return value
    def read_receipt(self,descriptor):
        self._validate_descriptor(descriptor)
        if descriptor['kind']!=KIND:raise Evidence467Error('receipt_reader_kind')
        return self._read_published(descriptor)
    def read_jsonl(self,descriptor):
        self._validate_descriptor(descriptor)
        if descriptor['kind']!=JSONL_KIND:raise Evidence467Error('JSONL_reader_kind')
        return self._read_published(descriptor)
    def _read_published(self,descriptor):
        self._validate_descriptor(descriptor);self._guard();path=self._path(descriptor['descriptor_relative_path'])
        if path.stat().st_size>16384:raise Evidence467Error('descriptor_size')
        with path.open('rb') as raw:published=json.loads(raw.read().decode('utf-8'))
        if published!=descriptor:raise Evidence467Error('published_descriptor_mismatch')
        return self._read_payload(descriptor)
