"""Lossless JSON codec for immutable planner bytes; private receipts only."""
import base64,math
from dataclasses import asdict,is_dataclass
TAG='__haic_private_bytes_base64_v1__'
def json_ready(value):
 if is_dataclass(value):return json_ready(asdict(value))
 if isinstance(value,bytes):return {TAG:base64.b64encode(value).decode('ascii')}
 if isinstance(value,dict):return {k:json_ready(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [json_ready(v) for v in value]
 if value is None or isinstance(value,(str,bool,int)):return value
 if isinstance(value,float):
  if not math.isfinite(value):raise ValueError('nonfinite_receipt_value')
  return value
 raise TypeError('unsupported_receipt_type:'+type(value).__name__)
def restore_bytes(value):
 if isinstance(value,dict):
  if set(value)=={TAG}:return base64.b64decode(value[TAG],validate=True)
  return {k:restore_bytes(v) for k,v in value.items()}
 if isinstance(value,list):return [restore_bytes(v) for v in value]
 return value
