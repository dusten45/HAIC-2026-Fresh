"""Strict canonical snapshot comparison using existing plain(); no tolerance."""
import hashlib,json,math,pickle
from pathlib import Path
import numpy as np
from retry.pedal331_run import plain
from retry.receipt421_io import save_receipt,load_receipt
from retry.pilot420_backend import TechnicalStop

class CanonicalError(ValueError):
 def __init__(self,path,reason):self.path=path;self.reason=reason;super().__init__(path+':'+reason)
def pointer(path):return '/'+('/'.join(str(x).replace('~','~0').replace('/','~1') for x in path)) if path else ''
def inspect_supported(value,path=(),arrays=None):
 if arrays is None:arrays={}
 if isinstance(value,np.ndarray):
  if value.dtype.kind not in 'biufU':raise CanonicalError(pointer(path),'unsupported_array_dtype')
  arrays[path]=list(value.shape);inspect_supported(value.tolist(),path,arrays)
 elif isinstance(value,np.generic):
  item=value.item()
  if isinstance(item,np.generic):raise CanonicalError(pointer(path),'non_native_numpy_scalar')
  inspect_supported(item,path,arrays)
 elif type(value) is dict:
  if any(type(k) is not str for k in value):raise CanonicalError(pointer(path),'nonstring_or_colliding_dictionary_key')
  for k,v in value.items():inspect_supported(v,path+(k,),arrays)
 elif type(value) in (list,tuple):
  for i,v in enumerate(value):inspect_supported(v,path+(i,),arrays)
 elif type(value) is float:
  if not math.isfinite(value):raise CanonicalError(pointer(path),'nonfinite_number')
 elif value is not None and type(value) not in (str,int,bool):raise CanonicalError(pointer(path),'unsupported_type:'+type(value).__name__)
 return arrays

def sequence_shape(value):
 if type(value) is list:
  if not value:return [0]
  shapes=[sequence_shape(v) for v in value]
  return [len(value)]+shapes[0] if shapes[0] is not None and all(s==shapes[0] for s in shapes) else None
 return None if type(value) is dict else []

def canonical(value):
 arrays=inspect_supported(value);normal=plain(value)
 def node(v,path):
  if type(v) is dict:return dict(kind='dict',fields={k:node(x,path+(k,)) for k,x in sorted(v.items())})
  if type(v) is list:return dict(kind='sequence',shape=arrays.get(path,sequence_shape(v)),items=[node(x,path+(i,)) for i,x in enumerate(v)])
  return dict(kind='null' if v is None else type(v).__name__,value=v)
 return node(normal,())

def field_diff(left,right,path=()):
 out=[]
 def diff(kind,**values):out.append(dict(path=pointer(path),reason=kind,**values))
 if left['kind']!=right['kind']:diff('type',left=left['kind'],right=right['kind']);return out
 if left['kind']=='dict':
  a=left['fields'];b=right['fields']
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append(dict(path=pointer(path+(k,)),reason='missing_field',left_present=k in a,right_present=k in b))
   else:out.extend(field_diff(a[k],b[k],path+(k,)))
 elif left['kind']=='sequence':
  if left['shape']!=right['shape']:diff('shape',left=left['shape'],right=right['shape'])
  if len(left['items'])!=len(right['items']):diff('length',left=len(left['items']),right=len(right['items']))
  for i,(a,b) in enumerate(zip(left['items'],right['items'])):out.extend(field_diff(a,b,path+(i,)))
 elif left['value']!=right['value']:diff('value',left=left['value'],right=right['value'])
 # Preserve signed floating zero as well as every other numeric value.
 elif left['kind']=='float' and left['value']==0 and math.copysign(1.,left['value'])!=math.copysign(1.,right['value']):diff('signed_zero',left=math.copysign(1.,left['value']),right=math.copysign(1.,right['value']))
 return out

def compare(left,right):
 values=[];errors=[]
 for side,value in [('left',left),('right',right)]:
  try:values.append(canonical(value))
  except CanonicalError as e:values.append(None);errors.append(dict(side=side,path=e.path,reason=e.reason))
 diffs=field_diff(*values) if not errors else [dict(reason='canonicalization_rejected',side=e['side'],path=e['path'],detail=e['reason']) for e in errors]
 return dict(equal=not diffs,left=values[0],right=values[1],diffs=diffs)

def require_equal(left,right,directory,label):
 report=compare(left,right)
 if not report['equal']:
  # Pickles retain tuple/list, numpy dtype/shape and NaN/Inf without coercion;
  # never deserialize these private originals from untrusted input.
  payload=dict(original_left_pickle=pickle.dumps(left,protocol=5),original_right_pickle=pickle.dumps(right,protocol=5),normalized=report,scope='PRIVATE_MISMATCH_ORIGINALS_AND_EXACT_FIELD_DIFF; no numeric tolerance')
  path=Path(directory)/(label+'-snapshot-mismatch-private.json');save_receipt(path,payload);saved=load_receipt(path)
  if saved['original_left_pickle']!=payload['original_left_pickle'] or saved['original_right_pickle']!=payload['original_right_pickle']:raise TechnicalStop('canonical_mismatch_original_readback')
  raise TechnicalStop('canonical_snapshot_mismatch:'+str(path))
 return dict(equal=True,canonical_sha256=hashlib.sha256(json.dumps(report['left'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),numeric_tolerance=0.)
