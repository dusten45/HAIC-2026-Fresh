"""472 raw-only exhaustive readback. Never archive, move, rewrite or omit raw."""
import base64,hashlib,json,os,time
from pathlib import Path
from retry.pilot420_json import TAG
from retry.receipt421_io import save_receipt

def reject_constant(value):raise ValueError('nonfinite JSON:'+value)
def unique_object(pairs):
    value={}
    for key,item in pairs:
        assert key not in value,'duplicate JSON key:'+key
        value[key]=item
    return value
def validate(value):
    if isinstance(value,dict):
        if TAG in value:
            assert set(value)=={TAG} and isinstance(value[TAG],str),'invalid bytes codec'
            base64.b64decode(value[TAG],validate=True)
        else:
            for item in value.values():validate(item)
    elif isinstance(value,list):
        for item in value:validate(item)

def inspect(path):
    path=Path(path);before=path.stat();h=hashlib.sha256();length=0
    with path.open('rb') as handle:
        while True:
            block=handle.read(1024*1024)
            if not block:break
            length+=len(block);h.update(block)
    assert length==before.st_size and before.st_mtime_ns==path.stat().st_mtime_ns,'raw changed while reading'
    schema=None;records=None
    if path.suffix=='.json':
        with path.open(encoding='utf8') as handle:value=json.load(handle,parse_constant=reject_constant,object_pairs_hook=unique_object)
        validate(value);schema='lossless_finite_JSON_'+type(value).__name__
        records=len(value) if isinstance(value,(dict,list)) else 1
    elif path.suffix=='.jsonl':
        records=0
        with path.open(encoding='utf8') as handle:
            for line in handle:
                assert line.strip(),'empty JSONL record'
                value=json.loads(line,parse_constant=reject_constant,object_pairs_hook=unique_object);assert isinstance(value,dict),'JSONL object required';validate(value);records+=1
        schema='lossless_finite_JSONL_objects'
    elif path.suffix in ('.log','.sha256','.txt'):
        with path.open(encoding='utf8') as handle:
            for _ in handle:pass
        schema='UTF8_text'
        if path.suffix=='.sha256':
            value=path.read_text().strip();assert len(value)==64 and all(c in '0123456789abcdef' for c in value),'invalid SHA file'
    else:raise AssertionError('unregistered raw schema:'+str(path))
    assert before.st_size==path.stat().st_size and before.st_mtime_ns==path.stat().st_mtime_ns,'raw changed during schema read'
    return dict(bytes=length,sha256=h.hexdigest(),schema=schema,records=records)

def inventory(roots):
    found={}
    for name,root in roots.items():
        root=Path(root);assert root.is_dir() and str(root.resolve()).startswith('/tmp/haic-retry-stage472-')
        for path in sorted(root.rglob('*')):
            assert not path.is_symlink(),'raw symlink forbidden'
            if path.is_file():found[name+'/'+str(path.relative_to(root))]=path
    return found

def retain(root):
    root=Path(root);manifest_path=root/'stage472-retention-manifest-private.json';assert not manifest_path.exists()
    assert json.loads((root/'stage472/progress-private.json').read_text())['phase'] in ('CLOSED','CLOSED_RESOURCE_STOP')
    assert (root/'stage472/saved-closure-private.json').is_file()
    roots=dict(model='/tmp/haic-retry-stage472-private',native='/tmp/haic-retry-stage472-native');cpu=time.process_time();wall=time.perf_counter()
    paths=inventory(roots);assert paths,'no raw'
    entries={name:inspect(path) for name,path in paths.items()}
    # A separate complete reopening verifies byte lengths, SHA and the schema.
    assert set(inventory(roots))==set(entries),'raw file set changed'
    for name,path in paths.items():assert inspect(path)==entries[name],'raw manifest mismatch:'+name
    assert set(inventory(roots))==set(entries),'raw file set changed after readback'
    result=dict(stage=472,retention='ORIGINAL_RAW_ONLY_NO_NEW_ARCHIVE',roots=roots,files=len(entries),raw_bytes=sum(v['bytes'] for v in entries.values()),entries=entries,
                every_file_reopened=True,full_length_SHA_schema_verified=True,all_files_verified_twice=True,new_archive_created=False,workspace_raw_copies=0,
                tmp_persistent_or_shared_assumed=False,loss_limit='If /tmp is lost, exact raw cannot be reverified; hashes cannot reconstruct raw.',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    save_receipt(manifest_path,result);return result

if __name__=='__main__':
    import sys
    result=retain(sys.argv[1]);print(json.dumps({k:v for k,v in result.items() if k!='entries'}))
