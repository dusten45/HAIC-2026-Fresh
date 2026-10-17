"""Saved-only private470 retention of model and native volumes; originals preserved."""
import hashlib,json,os,shutil,sys,tarfile,time
from pathlib import Path

RESERVE=512*1024**2
G=Path(__file__).resolve().parents[1]

def digest_stream(stream):
    h=hashlib.sha256()
    while True:
        data=stream.read(1024*1024)
        if not data:return h.hexdigest()
        h.update(data)

def put(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');path.chmod(0o600)

class ReserveWriter:
    def __init__(self,raw,directory):self.raw=raw;self.directory=directory
    def write(self,data):
        if shutil.disk_usage(self.directory).free-len(data)<RESERVE:raise RuntimeError('470_retention_storage_reserve512MiB_keep_partial_and_originals')
        if shutil.disk_usage('/workspace').free<RESERVE:raise RuntimeError('470_workspace_metadata_reserve512MiB')
        return self.raw.write(data)
    def flush(self):return self.raw.flush()
    def tell(self):return self.raw.tell()

def retain(root,out_name='stage469-revision1-retained'):
    start,cpu=time.perf_counter(),time.process_time();d=root/'stage469-revision1';p=json.loads((d/'plan.json').read_text())
    assert json.loads((d/'progress-private.json').read_text())['phase']=='CLOSED'
    assert (d/'saved-closure-private.json').is_file()
    assert out_name=='stage469-revision1-retained'
    out=Path('/tmp/haic-retry-stage469-revision1-retained');assert not out.exists(),'preserve failed or partial attempt'
    groups={'model':d.resolve()};files={name:sorted(f for f in folder.rglob('*') if f.is_file()) for name,folder in groups.items()}
    assert all(not f.is_symlink() for values in files.values() for f in values)
    sizes={name:sum(f.stat().st_size for f in values) for name,values in files.items()}
    forecast=sum(sizes.values())*1.1+32*1024**2
    free=shutil.disk_usage('/tmp').free
    result=dict(stage=470,status='PREFLIGHT',original_files_removed=0,new_actual_actions=0,new_model_ticks=0,uncompressed_bytes_by_volume=sizes,forecast_archive_bytes=int(forecast),tmp_free_bytes_before=free,required_free_reserve_bytes=RESERVE,forecast_basis='full raw bytes times1.1 plus32MiB; every compressed write checks512MiB reserve',tmp_is_not_shared_or_durable=True,workspace_raw_archive_copies=0,raw_and_archive_location='same selected executor /tmp',reproduction_limit='If /tmp is lost, exact new raw and archive cannot be reverified; manifest hashes cannot reconstruct raw.')
    def publish():
        result.update(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,tmp_free_bytes_after=shutil.disk_usage('/tmp').free)
        public=G/'retry/compare470_retention.json';public.write_text(json.dumps(result,indent=2)+'\n')
    if free<forecast+RESERVE:
        result['status']='NOT_STARTED_INSUFFICIENT_FORECAST_ALLOWANCE';result['current_executor_tmp_archives_verified']=False;publish();print(json.dumps(result));return result
    out.mkdir(mode=0o700);manifest={};archives={}
    try:
        for name,folder in groups.items():
            for f in files[name]:
                key=name+'/'+str(f.relative_to(folder))
                with f.open('rb') as source:manifest[key]=dict(bytes=f.stat().st_size,sha256=digest_stream(source))
        put(out/'file-manifest-private.json',manifest)
        assert shutil.disk_usage(root).free>=RESERVE+len(json.dumps(manifest).encode())
        manifest_path=root/'stage469-revision1-retention-manifest-private.json'
        assert not manifest_path.exists()
        put(manifest_path,manifest)
        for name,folder in groups.items():
            archive=out/(name+'470-private.tar.gz')
            with archive.open('xb') as raw:
                os.chmod(archive,0o600)
                with tarfile.open(fileobj=ReserveWriter(raw,out),mode='w:gz',compresslevel=1) as tar:
                    for f in files[name]:
                        if shutil.disk_usage(out).free<RESERVE:raise RuntimeError('470_retention_reserve_before_member')
                        key=name+'/'+str(f.relative_to(folder));assert f.stat().st_size==manifest[key]['bytes']
                        tar.add(f,arcname=key,recursive=False)
                raw.flush();os.fsync(raw.fileno())
            seen=set()
            with tarfile.open(archive,'r:gz') as tar:
                for member in tar:
                    assert member.isfile() and member.name in manifest and member.name.startswith(name+'/') and member.name not in seen
                    with tar.extractfile(member) as source:assert digest_stream(source)==manifest[member.name]['sha256']
                    assert member.size==manifest[member.name]['bytes'];seen.add(member.name)
            assert seen=={key for key in manifest if key.startswith(name+'/')}
            # Verify unchanged original bytes too; no raw evidence is removed.
            for f in files[name]:
                with f.open('rb') as source:assert digest_stream(source)==manifest[name+'/'+str(f.relative_to(folder))]['sha256']
            with archive.open('rb') as raw:archive_sha=digest_stream(raw)
            archives[name]=dict(files=len(seen),uncompressed_bytes=sizes[name],archive_bytes=archive.stat().st_size,archive_sha256=archive_sha,all_members_SHA256_verified=True,originals_SHA256_reverified=True)
        result.update(status='VERIFIED',archives=archives,current_executor_tmp_archives_verified=True,archive_bytes=sum(x['archive_bytes'] for x in archives.values()),prior_retention_failure_preserved=out_name.endswith('recovery1'))
    except BaseException as exc:
        result.update(status='STOP_PARTIAL_RETAINED',error=type(exc).__name__+': '+str(exc),archives=archives,current_executor_tmp_archives_verified=False)
        # Keep partial archives and both raw directories. No retry or deletion.
    publish();put(out/'retention-result.json',result);print(json.dumps(result));return result

if __name__=='__main__':retain(Path(sys.argv[1]).resolve())
