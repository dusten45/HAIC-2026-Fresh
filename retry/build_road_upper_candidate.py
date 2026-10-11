"""Build a separate archive changing only the two existing road upper bounds."""
from pathlib import Path
import argparse, hashlib, json, zipfile


def build(original, output, upper):
    old='road = ((image > 0.32) & (image < 0.47)).astype(np.uint8)'
    new=f'road = ((image > 0.32) & (image < {upper})).astype(np.uint8)'
    changed={'retry/connected_agent.py','retry/ridge_agent.py'}
    members={}; baseline={}
    with zipfile.ZipFile(original) as z:
        for name in z.namelist():
            relative=Path(name);assert not relative.is_absolute() and '..' not in relative.parts
            data=z.read(name);baseline[name]=hashlib.sha256(data).hexdigest()
            if name in changed:
                source=data.decode();assert source.count(old)==1
                edited=source.replace(old,new);assert edited.replace(new,old)==source
                data=edited.encode()
            members[name]=data
    assert changed.issubset(members)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(members.items()):
            item=zipfile.ZipInfo(name,(2020,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(item,data)
    output.chmod(0o600)
    hashes={n:hashlib.sha256(d).hexdigest() for n,d in members.items()}
    assert {n for n in hashes if hashes[n]!=baseline[n]}==changed
    return {'archive_path':str(output),'archive_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'members_sha256':hashes,'original_archive_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
            'changed_members':sorted(changed),'single_change':f'Road upper 0.47 -> {upper}; all else byte-identical'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('original',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--upper',required=True);a=p.parse_args();assert 0.47<float(a.upper)<1
    print(json.dumps(build(a.original,a.output,a.upper),indent=2))
