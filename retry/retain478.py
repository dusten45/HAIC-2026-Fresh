"""478 derived evidence single-copy full readback, no physics or model imports."""
import datetime,json,sys,time,hashlib
from pathlib import Path
from retry.audit475_forces import read,sha,put,G

def run(root):
 d=root/'stage478';p=read(d/'plan.json');cpu=time.process_time();files=sorted(f for f in d.iterdir() if f.is_file());inv=[]
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 for f,h in read(G/'retry/audit478_contract.json')['source_sha256'].items():assert sha(f)==h,f
 for f in files:
  b=f.read_bytes();h=hashlib.sha256(b).hexdigest();s=b.decode()
  if f.suffix=='.json':json.loads(s,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
  a=f.read_bytes();assert len(a)==len(b) and hashlib.sha256(a).hexdigest()==h
  inv.append(dict(path=str(f),bytes=len(b),sha256=h,full_readbacks=2))
 assert files==sorted(f for f in d.iterdir() if f.is_file());size=sum(x['bytes'] for x in inv);assert size<=p['raw_hard_bytes']
 put(root/'stage478-retention-manifest-private.json',dict(stage=478,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=inv,new_archive=False,workspace_new_raw_copies=0))
 out=dict(stage=478,files=len(inv),raw_bytes=size,all_files_twice_length_sha_JSON_verified=True,source_protected18_ledger_verified=True,CPU_s=time.process_time()-cpu,new_archive=False,workspace_new_raw_copies=0,new_physics=0,new_native=0,new_world=0,new_reset=0,new_actor=0,new_search=0,tmp_loss='Hashes cannot recreate raw')
 put(G/'retry/audit478_retention.json',out);print(json.dumps(out))
if __name__=='__main__':run(Path(sys.argv[1]))
