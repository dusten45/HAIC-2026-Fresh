"""Saved-only474 exhaustive original derived-evidence readback; no archive."""
import json,time
from pathlib import Path
from retry.retain472 import inspect
from retry.receipt421_io import save_receipt

def retain(root):
    root=Path(root);raw=Path('/tmp/haic-retry-stage474-private');d=root/'stage474';dest=root/'stage474-retention-manifest-private.json'
    assert d.resolve()==raw and not dest.exists() and (d/'saved-closure-private.json').exists()
    assert json.loads((d/'result.json').read_text())['status']=='SAVED_ONLY_ANALYSIS_COMPLETE'
    cpu=time.process_time();wall=time.perf_counter()
    def paths():
        result={}
        for p in sorted(raw.rglob('*')):
            assert not p.is_symlink()
            if p.is_file():result[str(p.relative_to(raw))]=p
        return result
    files=paths();entries={name:inspect(path) for name,path in files.items()};assert entries
    assert set(paths())==set(entries)
    for name,path in files.items():assert inspect(path)==entries[name],name
    assert set(paths())==set(entries)
    out=dict(stage=474,files=len(entries),raw_bytes=sum(v['bytes'] for v in entries.values()),entries=entries,every_file_reopened=True,full_length_SHA_schema_verified=True,all_files_verified_twice=True,new_archive_created=False,workspace_new_raw_copies=0,tmp_persistent_or_shared_assumed=False,loss_limit='If /tmp is lost exact derived raw and its source473 raw cannot be reverified; hashes cannot reconstruct raw.',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    save_receipt(dest,out);public={k:v for k,v in out.items() if k!='entries'};save_receipt(Path(__file__).resolve().parent/'audit474_retention.json',public);return public

if __name__=='__main__':
    import sys
    print(json.dumps(retain(sys.argv[1])))
