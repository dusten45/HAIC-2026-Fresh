"""Exact strict-clipping prefix predicates and JSON-safe atomic evidence storage."""
import json,math,os,tempfile
from pathlib import Path
import numpy as np

def plain(value):
 if isinstance(value,np.ndarray):return plain(value.tolist())
 if isinstance(value,np.generic):return plain(value.item())
 if isinstance(value,Path):return str(value)
 if isinstance(value,dict):return {str(k):plain(v) for k,v in value.items()}
 if isinstance(value,(tuple,list)):return [plain(v) for v in value]
 if isinstance(value,float) and not math.isfinite(value):raise ValueError('NONFINITE_JSON')
 if value is None or isinstance(value,(str,int,float,bool)):return value
 raise TypeError('UNSUPPORTED_JSON:'+type(value).__name__)

def atomic_write(path,value,overwrite=False):
 path=Path(path);data=(json.dumps(plain(value),indent=2,allow_nan=False)+'\n').encode();mode=0o600 if 'private' in str(path.parent) else 0o644
 tmp=None
 try:
  with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.'+path.name+'.',delete=False) as f:
   tmp=Path(f.name);os.chmod(tmp,mode);f.write(data);f.flush();os.fsync(f.fileno())
  if overwrite:os.replace(tmp,path)
  else:os.link(tmp,path);tmp.unlink()
 finally:
  if tmp is not None and tmp.exists():tmp.unlink()

def allowance(initial_clips,initial_samples,n):
 if not all(isinstance(x,(int,np.integer)) for x in (initial_clips,initial_samples,n)):raise TypeError('INTEGER_COUNTS_REQUIRED')
 if initial_samples<0 or n<0 or not 0<=initial_clips<=initial_samples:raise ValueError('INVALID_HISTORY')
 return (int(initial_samples)+int(n))//10-int(initial_clips)

def order_slack(ratios,initial_clips,initial_samples):
 r=np.asarray(ratios,dtype=float)
 if r.ndim!=1 or not np.all(np.isfinite(r)):raise ValueError('FINITE_VECTOR_REQUIRED')
 k=allowance(initial_clips,initial_samples,len(r))
 if k<0:return -1.,None
 if k>=len(r):return 1.,None
 # Stable index only selects a representative at ties; VALUE and predicate
 # are tie-invariant. Exact1 is admitted because clipping is STRICTLY >1.
 rank=np.argsort(-r,kind='stable');i=int(rank[k]);return 1.-float(r[i]),i

def count_pass(ratios,initial_clips,initial_samples):
 k=allowance(initial_clips,initial_samples,len(ratios));return sum(float(x)>1. for x in ratios)<=k

def source_fraction_pass(ratios,initial_clips,initial_samples):
 total=initial_samples+len(ratios);clipped=initial_clips+sum(float(x)>1. for x in ratios)
 return clipped/total<=.1 if total else clipped==0

def prefix_slacks(ratios,c0,n0):
 r=np.asarray(ratios,float);assert len(r)%4==0
 return np.array([order_slack(r[:n],c0,n0)[0] for n in range(4,len(r)+1,4)])

def nonexempt_branch(ratios,c0,n0):
 """A rank-branch sufficient set; NOT a frozen baseline clipped mask.

For each prefix exempt its k highest samples and constrain the complement to
<=1. Rebuild from a proposed ranking to permit old/new clipping identities to
swap. Union duplicates because each force sample is one fixed historical value.
"""
 r=np.asarray(ratios,float);ids=set()
 for n in range(4,len(r)+1,4):
  k=allowance(c0,n0,n)
  if k<0:raise ValueError('NO_BRANCH_FOR_NEGATIVE_ALLOWANCE')
  if k<n:ids.update(map(int,np.argsort(-r[:n],kind='stable')[k:]))
 return np.array(sorted(ids),dtype=int)
