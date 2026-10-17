"""Freeze single-copy saved audit evidence; preserve failed partial JSON as opaque."""
import datetime,hashlib,json,sys,time
from pathlib import Path
from retry.audit475_forces import read,sha,put,G

def run(root):
 d=root/'stage475';plan=read(d/'plan.json');cpu=time.process_time();wall=time.perf_counter();inventory=[];files=sorted(p for p in d.iterdir() if p.is_file())
 for group in ['sources','protected','original408_preserve']:
  for f,h in plan[group].items():assert sha(f)==h,f
 for p in files:
  data=p.read_bytes();h=hashlib.sha256(data).hexdigest();text=data.decode('utf-8');kind='opaque preserved failed partial JSON' if p.name=='domain-private.json' else 'JSONL' if p.suffix=='.jsonl' else 'JSON' if p.suffix=='.json' else 'text';n=0
  if kind=='JSON':json.loads(text);n=1
  if kind=='JSONL':
   for line in text.splitlines():json.loads(line);n+=1
  again=p.read_bytes();assert len(again)==len(data) and hashlib.sha256(again).hexdigest()==h
  inventory.append(dict(path=str(p),bytes=len(data),sha256=h,kind=kind,records=n,full_readbacks=2))
 assert files==sorted(p for p in d.iterdir() if p.is_file())
 put(root/'stage475-retention-manifest-private.json',dict(stage=475,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=inventory,new_archive_created=False,workspace_new_raw_copies=0,failed_partial_preserved=True))
 out=dict(stage=475,files=len(files),raw_bytes=sum(x['bytes'] for x in inventory),full_length_sha_verified_twice=True,valid_JSON_JSONL_parsed=True,opaque_failed_partial_files=1,failed_partial_not_claimed_valid_schema=True,new_archive_created=False,workspace_new_raw_copies=0,source_and_protected18_and_ledger_verified=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,tmp_loss_limit='Hashes do not reconstruct missing derived raw or source473 tmp files',new_physics=0,new_native=0)
 put(G/'retry/audit475_retention.json',out);print(json.dumps(out))
if __name__=='__main__':run(Path(sys.argv[1]))
