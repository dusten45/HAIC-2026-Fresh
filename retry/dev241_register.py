"""Register fresh241 roads as DEV before evaluation, source-only identity draw.

--selector is the retained immutable identity selector; --contract freezes its
source hash and metadata. Only case ID/split tags change, no draw/geometry rules.
The selector fsyncs the initial vector before any geometry is constructed.
"""
import argparse
import hashlib
from pathlib import Path
import json


def register(selector,contract,output):
    c=json.loads(contract.read_text());source=selector.read_text()
    assert hashlib.sha256(selector.read_bytes()).hexdigest()==c['source_sha256'][str(selector)]
    edits={"f'holdout{contract[\"stage\"]}-{index}'":"f'fresh-dev{contract[\"stage\"]}-{index}'",
           "f'HOLDOUT_{contract[\"stage\"]}'":"f'DEV_{contract[\"stage\"]}'"}
    for a,b in edits.items():assert source.count(a)==1;source=source.replace(a,b)
    namespace={'__name__':'declared_dev241_source_selector','__file__':str(selector)}
    exec(compile(source,str(selector),'exec'),namespace)
    return namespace['register'](contract,output)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for n in ['selector','contract','output']:a.add_argument('--'+n,type=Path,required=True)
    p=a.parse_args();print(json.dumps(register(p.selector,p.contract,p.output)))
