"""One road perception bridge in copied240; original controller/model unchanged."""
import ast,hashlib,zipfile
from pathlib import Path
from retry.submission232_build import FORBIDDEN


def build(base,output):
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    original=dict(members);s=members['retry/nominal238_base.py'].decode();old='path = connected_route(image, obstacles, speed=speed, previous_steer=self.controller.previous_steer)';assert s.count(old)==1
    s=s.replace(old,'path = temporal_road_route(observation[-2], image, obstacles, speed=speed, previous_steer=self.controller.previous_steer)');s=s.replace('import numpy as np\n','import numpy as np\nfrom retry.roadfusion253 import route as temporal_road_route\n',1)
    members['retry/nominal238_base.py']=s.encode();members['retry/roadfusion253.py']=Path(__file__).with_name('roadfusion253.py').read_bytes()
    assert all(members[k]==v for k,v in original.items() if k!='retry/nominal238_base.py')
    for n,v in members.items():
        if not n.endswith('.py'):continue
        for node in ast.walk(ast.parse(v,filename=n)):
            if isinstance(node,ast.Import):assert all(x.name.split('.')[0] not in FORBIDDEN for x in node.names)
            if isinstance(node,ast.ImportFrom):assert (node.module or '').split('.')[0] not in FORBIDDEN
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ['open','eval','exec','compile','__import__']
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,v in sorted(members.items()):
            item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,v)
    output.chmod(0o600);return dict(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(v).hexdigest() for n,v in members.items()},original_controller_head_scales_byte_exact=True,static_boundary_passed=True)
