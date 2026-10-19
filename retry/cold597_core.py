"""Pure597 scheduling and official integer finish rules; no physics."""
WARMUP=50
TIME_LIMIT=1224
MAX_APPLIED=TIME_LIMIT-WARMUP
EPOCH=1.02
DT=.02

def official_raw(finish_time):
 if finish_time is None:return None
 raw=round((finish_time-EPOCH)/DT)
 if not 0<raw<=MAX_APPLIED or abs((finish_time-EPOCH)-raw*DT)>1e-9:raise ValueError('NONINTEGER_OFFICIAL_FINISH_CLOCK')
 return raw

def reserve_request(feedback,replay_reserved=True):
 n=1540 if feedback else 4
 out=dict(model_attempted=n,model_completed=n,external_force=4*n,internal_force=4*n,total_force=8*n,geometry=4526 if feedback else 8)
 if replay_reserved:
  for k,v in dict(model_attempted=MAX_APPLIED,model_completed=MAX_APPLIED,external_force=4*MAX_APPLIED,internal_force=4*MAX_APPLIED,total_force=8*MAX_APPLIED,geometry=2+2*MAX_APPLIED).items():out[k]+=v
 return out

def fits(counts,need,caps):return all(counts.get(k,0)+v<=caps[k] for k,v in need.items())
def replay_allowed(status,error):return status=='WHOLE_STRICT_SAFE_OFFICIAL_FINISH' and error is None
