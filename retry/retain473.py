"""473 exhaustive original raw-only readback, no archive or transformation."""
import json,time
from pathlib import Path
from retry.retain472 import inspect
from retry.receipt421_io import save_receipt

def retain(root):
    root=Path(root);d=root/'stage473';raw=Path('/tmp/haic-retry-stage473-private');dest=root/'stage473-retention-manifest-private.json'
    assert d.resolve()==raw and not dest.exists() and (d/'saved-closure-private.json').exists()
    assert json.loads((d/'progress-private.json').read_text())['phase'] in ('CLOSED','CLOSED_RESOURCE_STOP')
    cpu=time.process_time();wall=time.perf_counter()
    def paths():
        result={}
        for p in sorted(raw.rglob('*')):
            assert not p.is_symlink()
            if p.is_file():result[str(p.relative_to(raw))]=p
        return result
    files=paths();assert files;entries={name:inspect(path) for name,path in files.items()}
    assert set(paths())==set(entries)
    for name,path in files.items():assert inspect(path)==entries[name],name
    assert set(paths())==set(entries)
    out=dict(stage=473,retention='ORIGINAL_RAW_ONLY_NO_NEW_ARCHIVE',raw_directory=str(raw),files=len(entries),raw_bytes=sum(x['bytes'] for x in entries.values()),entries=entries,every_file_reopened=True,full_length_SHA_schema_verified=True,all_files_verified_twice=True,new_archive_created=False,workspace_raw_copies=0,tmp_persistent_or_shared_assumed=False,loss_limit='If /tmp is lost, exact raw cannot be reverified; hashes cannot reconstruct raw.',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    save_receipt(dest,out);public={k:v for k,v in out.items() if k not in ('entries','raw_directory')};save_receipt(Path(__file__).resolve().parent/'compare473_retention.json',public);return public

if __name__=='__main__':
    import sys
    print(json.dumps(retain(sys.argv[1])))
