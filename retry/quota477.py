"""Pre-serialization byte quotas around unchanged historical atomic writers."""
import json,shutil,sys
from pathlib import Path
from retry.pilot420_backend import ResourceStop,TechnicalStop
from retry.pilot420_json import json_ready
import retry.loss389_analyze as plain
import retry.receipt421_io as receipt
class Quota:
 def __init__(self,d,model_cap,extra_cap):
  self.d=Path(d).resolve();self.model_cap=model_cap;self.extra_cap=extra_cap;self.used={p.resolve():p.stat().st_size for p in self.d.iterdir() if p.is_file()};self.oldsave=plain.save;self.oldreceipt=receipt.save_receipt
 def cap(self,path):
  n=path.name
  if n.startswith('allocation-input-'):return 4096
  if n.startswith('allocation-proof-'):return 8192
  if 'own-reference-before' in n:return 65536
  if 'runtime-link' in n:return 256*1024
  if 'before-constructor' in n or 'before-first-step' in n or 'before-integration' in n or n=='plan.json':return 2*1024**2
  return 32*1024**2
 def before(self,path,value,isreceipt=False):
  path=Path(path).resolve()
  if path.parent!=self.d:raise TechnicalStop('477_writer_outside_current_raw:'+str(path))
  text=json.dumps(json_ready(value) if isreceipt else value,ensure_ascii=False,indent=2,allow_nan=False)+'\n';size=len(text.encode())
  if size>self.cap(path):raise ResourceStop('477_file_quota:'+path.name)
  model=sum(n for p,n in self.used.items() if not p.name.startswith('allocation-'));extra=sum(n for p,n in self.used.items() if p.name.startswith('allocation-'))
  if path.name.startswith('allocation-'):extra+=size-self.used.get(path,0)
  else:model+=size-self.used.get(path,0)
  if model>self.model_cap or extra>self.extra_cap:raise ResourceStop('477_total_raw_quota')
  if shutil.disk_usage('/tmp').free-size<512*1024**2 or shutil.disk_usage('/workspace').free<512*1024**2:raise ResourceStop('477_write_reserve')
  return path,size
 def save(self,path,value):
  p,n=self.before(path,value);result=self.oldsave(path,value);self.used[p]=n;return result
 def save_receipt(self,path,value):
  p,n=self.before(path,value,True);result=self.oldreceipt(path,value);self.used[p]=n;return result
 def install(self):
  for name,module in list(sys.modules.items()):
   if name.startswith('retry.') and module is not None:
    for key,value in list(vars(module).items()):
     if value is self.oldsave:setattr(module,key,self.save)
     elif value is self.oldreceipt:setattr(module,key,self.save_receipt)
  return self
