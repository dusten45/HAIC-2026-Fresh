"""Install local speed profile wrapper while preserving every current240 member."""
import ast,hashlib,zipfile
from pathlib import Path
from retry.submission232_build import FORBIDDEN

def build(base,output):
 with zipfile.ZipFile(base) as z:original={n:z.read(n) for n in z.namelist()}
 members=dict(original);members['retry/frozen240_root.py']=original['agent.py'];members['agent.py']=Path(__file__).with_name('pixel263_agent.py').read_bytes()
 assert all(members[n]==v for n,v in original.items() if n!='agent.py')
 for name,data in members.items():
  if not name.endswith('.py'):continue
  for node in ast.walk(ast.parse(data,filename=name)):
   if isinstance(node,ast.Import):assert all(x.name.split('.')[0] not in FORBIDDEN for x in node.names)
   if isinstance(node,ast.ImportFrom):assert (node.module or '').split('.')[0] not in FORBIDDEN
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in {'open','exec','eval','compile','__import__'}
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(members.items()):
   item=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,data)
 output.chmod(0o600)
 return dict(type='champion',archive_path=str(output),archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(d).hexdigest() for n,d in members.items()},assets={},constants={},all_original_members_except_root_byte_exact=True,original_root_preserved=True,static_boundary_passed=True)
