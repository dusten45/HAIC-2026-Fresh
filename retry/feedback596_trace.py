"""Passive537 forecast telemetry; never selects an action or changes a gate."""
def post_flags(minimum,maxover,distance,delta,limit):
 flags=dict(FOOTPRINT=minimum<.50,REFERENCE=maxover>4.85,PATH=distance>3,PROJECTION_BACKWARD=delta<-.5,PROJECTION_FORWARD=delta>limit)
 first=next((k for k,v in flags.items() if v),None)
 reason='FORECAST_FOOTPRINT_MARGIN' if flags['FOOTPRINT'] else 'REFERENCE_WITH_NUMERIC_RESERVE' if flags['REFERENCE'] else 'PROJECTION_OR_PATH' if first else None
 return flags,first,reason
class Trial:
 def __init__(self,history,progress,minimum):
  self.history=list(history);self.progress=progress;self.minimum=minimum;self.peak=0.;self.maxover=0.;self.rows=[];self.ticks=0;self.attempts=0;self.reason='CURRENT_FOOTPRINT_MARGIN' if minimum<.5 else None;self.first_failure='CURRENT_FOOTPRINT' if minimum<.5 else None
 def force(self,forces,admission):
  self.attempts+=1;self.history=[self.history[0]+sum(f['clipped'] for f in forces),self.history[1]+4];self.peak=max(self.peak,max(f['ratio'] for f in forces));reason='FORCE_PEAK' if self.peak>admission else 'CLIP_HISTORY' if self.history[0]/self.history[1]>.10 else None
  if reason:self.reason=reason;self.first_failure=reason
  return reason
 def post(self,gap,over,distance,delta,limit):
  self.minimum=min(self.minimum,gap);self.maxover=max(self.maxover,over);flags,first,reason=post_flags(self.minimum,self.maxover,distance,delta,limit)
  if reason:self.reason=reason;self.first_failure=first
  return flags,first
 def summary(self):return dict(ok=self.reason is None,reason=self.reason or 'CERTIFIED_12HOLD_FLOAT32',peak=self.peak,max_reference_overspeed=self.maxover,clipped=self.history[0],samples=self.history[1],model_ticks=self.ticks,min_footprint_margin_m=self.minimum,attempts=self.attempts,split_first_failure=self.first_failure)
