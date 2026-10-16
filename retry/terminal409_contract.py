"""Pure stored-record contract: action repeat may stop early at a terminal boundary.

Does not construct an environment, call a policy, or integrate a model. Passing
this separate contract never changes the frozen408 qualification result.
"""
import math

def validate(row,repeat=4,fps=50):
 errors=[]
 def err(s):errors.append(s)
 try:
  n=row['raw_ticks'];pre=float(row['pre']['time']);post=float(row['post']['time']);terminal=bool(row['ended'] or row['truncated']);completed=bool(row['completed']);samples=row['raw_tire_samples']
  if not(isinstance(n,int) and not isinstance(n,bool) and 1<=n<=repeat):err('raw_tick_count_outside_repeat')
  elif not terminal and n!=repeat:err('short_nonterminal_repeat')
  if not(math.isfinite(pre) and math.isfinite(post) and post>pre and abs((post-pre)-n/fps)<=1e-8):err('clock_tick_mismatch')
  if len(samples)!=4*n:err('missing_or_extra_wheel_samples')
  if [(s.get('raw_tick'),s.get('wheel')) for s in samples]!=[(t,w) for t in range(1,n+1) for w in range(4)]:err('wheel_tick_coverage_or_order')
  finish=row.get('finish_time_s')
  if completed:
   if not terminal:err('official_finish_without_terminal_flag')
   if finish is None or not math.isfinite(float(finish)) or float(finish)>post+1e-8:err('missing_or_future_finish_timestamp')
  elif finish is not None:err('finish_timestamp_without_completed_flag')
  kind='official_finish' if completed else 'other_terminal' if terminal else 'nonterminal'
 except (KeyError,TypeError,ValueError,OverflowError) as e:
  err('invalid_record_schema:'+type(e).__name__);kind='invalid_schema'
 return dict(passed=not errors,classification=kind,errors=errors)
