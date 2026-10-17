"""Preserve both original verifier failure and successful arithmetic evidence."""
import datetime,hashlib,json,sys,time
from pathlib import Path
from retry.audit475_forces import read,sha,put,G

def run(root):
 cpu=time.process_time();dirs=[root/'stage476',root/'stage476-recovery1'];p=read(dirs[1]/'plan.json');inventory=[]
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 contract=read(G/'retry/audit476_model_contract.json')
 for f,h in contract['source_sha256'].items():assert sha(f)==h,f
 for directory in dirs:
  files=sorted(f for f in directory.iterdir() if f.is_file())
  for f in files:
   b=f.read_bytes();text=b.decode('utf-8');kind='JSON' if f.suffix=='.json' else 'text'
   if kind=='JSON':json.loads(text,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
   h=hashlib.sha256(b).hexdigest();again=f.read_bytes();assert len(again)==len(b) and hashlib.sha256(again).hexdigest()==h
   inventory.append(dict(path=str(f),bytes=len(b),sha256=h,kind=kind,full_readbacks=2))
  assert files==sorted(f for f in directory.iterdir() if f.is_file())
 size=sum(f['bytes'] for f in inventory);assert size<=16*1024**2
 put(root/'stage476-retention-manifest-private.json',dict(stage=476,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=inventory,original_failure_and_success_retained=True,new_archive_created=False,workspace_new_raw_copies=0))
 result=dict(stage=476,files=len(inventory),raw_bytes=size,all_files_full_length_sha_verified_twice=True,all_JSON_valid=True,original_failure_preserved=True,new_archive_created=False,workspace_new_raw_copies=0,sources_protected18_ledger_and_final_contract_hashes_verified=True,CPU_s=time.process_time()-cpu,tmp_loss='Hashes cannot recreate lost raw',new_physics=0,new_native=0,new_world=0,new_reset=0)
 put(G/'retry/audit476_retention.json',result);print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]))
