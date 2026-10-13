"""One clock gate only; all251 coefficients/norm/scales preserved byte-for-byte."""
import ast,hashlib,zipfile
from pathlib import Path
from retry.submission232_build import FORBIDDEN


def build(base,output):
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    original=dict(members);members['retry/continuous251_source.py']=members['retry/nominal238_base.py'];members['retry/nominal238_base.py']=Path(__file__).with_name('gate252_agent.py').read_bytes()
    assert all(members[k]==v for k,v in original.items() if k!='retry/nominal238_base.py')
    for n,v in members.items():
        if not n.endswith('.py'):continue
        for node in ast.walk(ast.parse(v,filename=n)):
            if isinstance(node,ast.Import):assert all(x.name.split('.')[0] not in FORBIDDEN for x in node.names)
            if isinstance(node,ast.ImportFrom):assert (node.module or '').split('.')[0] not in FORBIDDEN
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ['open','exec','eval','compile','__import__']
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for n,v in sorted(members.items()):
            info=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,v)
    output.chmod(0o600);return dict(archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(v).hexdigest() for n,v in members.items()},coefficients_normalization_scales_byte_exact=True,static_boundary_passed=True)
