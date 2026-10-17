"""Post-close private evidence retention; no model/environment imports or calls.

Copy the closed temporary stage into a private workspace archive and verify every
member against streaming hashes. Originals remain untouched. This does not make
/tmp shared across execution environments or guarantee cloud volume retention.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import time


def digest_stream(stream):
    h=hashlib.sha256()
    while True:
        chunk=stream.read(1024*1024)
        if not chunk:return h.hexdigest()
        h.update(chunk)


def retain(root):
    start,cpu=time.perf_counter(),time.process_time()
    stage=root/'stage462'
    assert json.loads((stage/'progress-private.json').read_text())['phase']=='CLOSED'
    assert (stage/'saved-closure-private.json').is_file()
    out=root/'stage462-retained'
    assert not out.exists(), 'Retention is once-only; preserve a failed attempt.'
    out.mkdir(mode=0o700)
    files=sorted(p for p in stage.resolve().rglob('*') if p.is_file())
    assert not any(p.name.endswith('.tmp') for p in files)
    manifest={}
    for p in files:
        with p.open('rb') as f:manifest['stage462/'+str(p.relative_to(stage.resolve()))]=dict(sha256=digest_stream(f),bytes=p.stat().st_size)
    metadata=out/'file-manifest-private.json'
    metadata.write_text(json.dumps(manifest,indent=2)+'\n');metadata.chmod(0o600)
    archive=out/'stage462-private.tar.gz'
    with archive.open('xb') as raw:
        os.chmod(archive,0o600)
        with tarfile.open(fileobj=raw,mode='w:gz',compresslevel=1) as tar:
            for p in files:
                if shutil.disk_usage(out).free<512*1024**2:raise RuntimeError('retention_storage_reserve_512MiB')
                tar.add(p,arcname='stage462/'+str(p.relative_to(stage.resolve())),recursive=False)
    seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            assert member.isfile() and member.name in manifest
            with tar.extractfile(member) as f:assert digest_stream(f)==manifest[member.name]['sha256']
            assert member.size==manifest[member.name]['bytes'];seen.add(member.name)
    assert seen==set(manifest)
    with archive.open('rb') as f:archive_sha=digest_stream(f)
    result=dict(stage=462,closed_stage_files=len(files),uncompressed_bytes=sum(x['bytes'] for x in manifest.values()),archive_bytes=archive.stat().st_size,archive_sha256=archive_sha,all_members_SHA256_verified=True,original_files_removed=0,new_actual_actions=0,new_model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,tmp_is_not_shared_or_durable=True,workspace_private_archive_retained=True)
    path=out/'retention-result.json';path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
    print(json.dumps(result))

if __name__=='__main__':retain(Path(sys.argv[1]).resolve())
