"""Atomic, non-overwriting private receipt JSON; same lossless bytes codec as420."""
import hashlib,json,os,tempfile
from pathlib import Path
from retry.pilot420_json import json_ready,restore_bytes

def receipt_digest(value):
 data=json.dumps(json_ready(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8');return hashlib.sha256(data).hexdigest()
def _write_all(file,text):file.write(text);file.flush();os.fsync(file.fileno())
def save_receipt(path,value):
 path=Path(path)
 if path.exists():raise FileExistsError(str(path))
 # Fail serialization beforecreatinga partial file.
 text=json.dumps(json_ready(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n';temporary=None
 try:
  with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as file:
   temporary=Path(file.name);os.chmod(temporary,0o600);_write_all(file,text)
  # Atomic publish withoutreplacingan existingreceipt, evenif itappearsafterthecheck.
  os.link(temporary,path)
 finally:
  if temporary is not None and temporary.exists():temporary.unlink()
 return receipt_digest(value)
def load_receipt(path):return restore_bytes(json.loads(Path(path).read_text()))
