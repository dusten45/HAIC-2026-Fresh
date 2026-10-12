"""Reproduce the fixed236 candidate ZIP from the retained232 archive."""
import argparse
import hashlib
from pathlib import Path
import zipfile


def build(base, output):
    with zipfile.ZipFile(base) as z:
        members={n:z.read(n) for n in z.namelist()}
    assert members['agent.py']==Path(__file__).with_name('submission232_agent.py').read_bytes()
    members['retry/nominal236_base.py']=members['agent.py']
    members['agent.py']=Path(__file__).with_name('pedal236_agent.py').read_bytes()
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(members.items()):
            assert not name.startswith('/') and '..' not in Path(name).parts
            item=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16
            z.writestr(item,data)
    return hashlib.sha256(output.read_bytes()).hexdigest()


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--base',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    p=a.parse_args();print(build(p.base,p.output))
