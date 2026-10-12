"""Two fresh DEVscreen identities, fixed before trainingrank; durable8byte draw."""
import argparse
import hashlib
import json
from pathlib import Path


def register(selector,contract,output,recover_draw=None):
    c=json.loads(contract.read_text());s=selector.read_text();assert hashlib.sha256(selector.read_bytes()).hexdigest()==c['source_sha256'][str(selector)]
    edits={"'identity-only-four-v1'":"'identity-only-two-devscreen-v1'","[1, 2, 3, 4]":"[1, 2]","[['A', 'B'], ['B', 'A'], ['A', 'B'], ['B', 'A']]":"[['A', 'B'], ['B', 'A']]","[0, 1, 2, 3]":"[0, 1]","os.urandom(16)":"os.urandom(8)","f'holdout{contract[\"stage\"]}-{index}'":"f'dev-screen{contract[\"stage\"]}-{index}'","f'HOLDOUT_{contract[\"stage\"]}'":"f'DEV_SCREEN_{contract[\"stage\"]}'","'registered_conditions': 4":"'registered_conditions': 2","{'AB': 2, 'BA': 2}":"{'AB': 1, 'BA': 1}","Single 16-byte draw, four little-endian uint32 seeds":"Single 8-byte draw, two little-endian uint32 seeds", "== 4\n":"== 2\n"}
    for a,b in edits.items():assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
    namespace={'__name__':'fixed_two_devscreen_selector','__file__':str(selector)}
    if recover_draw is not None:
        draw=json.loads(recover_draw.read_text());assert draw['contract_sha256']==hashlib.sha256(contract.read_bytes()).hexdigest()
        repairs={"('draw-receipt.json', 'split.json', 'split.sha256', 'selection-receipt.json')":"('split.json', 'split.sha256', 'selection-receipt.json')",
            "raw = os.urandom(8)":"raw = bytes.fromhex(recovery_draw['initial_osurandom_bytes_hex'])",
            "write_once(output_dir / 'draw-receipt.json', draw)":"assert draw['initial_seed_draw']==recovery_draw['initial_seed_draw']",
            "replacement = os.urandom(4)":"raise RuntimeError('Identitycollision during recovery; no new draw permitted')"}
        for a,b in repairs.items():assert s.count(a)==1;s=s.replace(a,b)
        namespace['recovery_draw']=draw
    exec(compile(s,str(selector),'exec'),namespace)
    return namespace['register'](contract,output)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for n in ['selector','contract','output']:a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--recover-draw',type=Path)
    p=a.parse_args();print(json.dumps(register(p.selector,p.contract,p.output,p.recover_draw)))
