"""Full single-copy477 raw readback and hash/source closure."""
import datetime,hashlib,json,sys,time
from pathlib import Path
from retry.audit475_forces import read,sha,put,G

def run(root):
 d=root/'stage477-revision1';p=read(d/'plan.json');cpu=time.process_time();wall=time.perf_counter();files=sorted(f for f in d.iterdir() if f.is_file());inventory=[]
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 for f in files:
  data=f.read_bytes();h=hashlib.sha256(data).hexdigest();text=data.decode();kind='JSON' if f.suffix=='.json' else 'text'
  if kind=='JSON':json.loads(text,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
  again=f.read_bytes();assert len(again)==len(data) and hashlib.sha256(again).hexdigest()==h
  inventory.append(dict(path=str(f),bytes=len(data),sha256=h,kind=kind,full_readbacks=2))
 assert files==sorted(f for f in d.iterdir() if f.is_file());size=sum(x['bytes'] for x in inventory);assert size<=p['storage_forecast']['model_payload_bytes']+p['storage_forecast']['allocator_extra_bytes']
 put(root/'stage477-retention-manifest-private.json',dict(stage=477,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=inventory,new_archive_created=False,workspace_new_raw_copies=0))
 out=dict(stage=477,files=len(inventory),raw_bytes=size,all_files_verified_twice=True,all_JSON_parsed=True,source_protected18_ledger_verified=True,new_archive_created=False,workspace_new_raw_copies=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,tmp_loss='Hashes do not recreate raw',new_actual=0,new_reset=0)
 put(G/'retry/compare477_retention.json',out);print(json.dumps(out))
if __name__=='__main__':run(Path(sys.argv[1]))
