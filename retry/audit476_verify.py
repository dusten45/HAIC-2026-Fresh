"""Independent source-order evaluator, proof checks and bounded exhaustive fixtures."""
import math,struct
import numpy as np

def number(rank):return struct.unpack('>f',struct.pack('>I',rank))[0]
def rank(q):return struct.unpack('>I',struct.pack('>f',q))[0]
def ref(w,q,branch,dtype):
 # Independent transcription retaining original augmented updates and branch order.
 command=np.asarray([0.,q if branch=='gas' else 0.,q if branch=='brake' else 0.],dtype=np.float32 if dtype=='native32' else np.float64)
 applied=w['gas']
 if w['wheel'] in (2,3):
  difference=np.clip(command[1],0,1)-applied
  if difference>0.1:difference=0.1
  applied+=difference
 spin=w['omega'];spin+=.02*(100000000*.02*.02*w['engine'])*applied/(4000*.02*.02)/(abs(spin)+5.)
 if command[2]>=.9:spin=0
 elif command[2]>0:
  direction=-np.sign(spin);value=15*command[2]
  if abs(value)>abs(spin):value=abs(spin)
  spin+=direction*value
 longitudinal=(-w['vf']+spin*w['radius'])*(205000*.02*.02);lateral=-w['vs']*(205000*.02*.02)
 magnitude=np.sqrt(np.square(longitudinal)+np.square(lateral));excess=max(0.,float(magnitude/w['limit']-1.))
 return float(longitudinal),excess

def verify(wheels,q0,branch,dtype,p):
 low=p['domain_rank_lo'];high=p['q0_rank'];assert high==rank(0. if q0==0 else q0)
 def e(j,k):return ref(wheels[j],number(k),branch,dtype)
 minima=[]
 for j in range(4):
  inc=e(j,high)[0]>=e(j,low)[0];l,h=low,high
  predicate=lambda k:e(j,k)[0]>=0 if inc else e(j,k)[0]<=0
  if not predicate(h):cross=h
  else:
   while l<h:
    mid=(l+h)//2
    if predicate(mid):h=mid
    else:l=mid+1
   cross=l
  pts={low,high,cross,max(low,cross-1)};minima.append(min((e(j,k)[1],k) for k in pts))
 def check_threshold(t,proofs):
  intervals=[]
  for j,cert in enumerate(proofs):
   interval=cert['interval']
   if interval is None:assert minima[j][0]>t;return_empty=True;intervals.append(None);continue
   l,h=(low+x for x in interval);assert low<=l<=h<=high
   assert e(j,l)[1]<=t and e(j,h)[1]<=t
   assert l==low or e(j,l-1)[1]>t
   assert h==high or e(j,h+1)[1]>t
   assert l<=minima[j][1]<=h
   intervals.append((l,h))
  if any(x is None for x in intervals):return None
  l=max(x[0] for x in intervals);h=min(x[1] for x in intervals);return (l,h) if l<=h else None
 t=p['objective'];iv=check_threshold(t,p['wheel_proofs']);assert iv is not None and iv[1]==p['q_rank']
 m=max(e(j,p['q_rank'])[1] for j in range(4));m0=max(e(j,high)[1] for j in range(4));assert m==t and m<=m0 and m0==p['objective_q0']
 if p['threshold_predecessor'] is not None:assert check_threshold(p['threshold_predecessor'],p['predecessor_wheel_proofs']) is None
 else:assert t==0
 if p['q_rank']<high:assert max(e(j,p['q_rank']+1)[1] for j in range(4))>t
 return True

def fixtures():
 from retry.allocator476 import solve,force,Unsupported,bits32,q32
 def wheel(j,**kw):
  w=dict(wheel=j,omega=0.,gas=0.,vf=0.,vs=0.,limit=400.,engine=1.,radius=.54);w.update(kw);return w
 cases=[]
 for dtype in ['native32','model64']:
  for center in [0.,.1,.5,.9,1.]:
   mid=bits32(center);lo=max(0,mid-48);hi=min(bits32(1.),mid+48);q=q32(hi)
   for branch in ['gas','brake']:
    ws=[wheel(j,omega=float(1 if j%2 else -1),gas=.5 if j>=2 else 0.,vf=float(.1*(j-1)),limit=.1,vs=.001) for j in range(4)]
    cases.append((f'{dtype}_{branch}_boundary_{center}',ws,q,branch,dtype,lo,hi))
  # Tiny full production domain, underflow and both signed zeros.
  cases.append((dtype+'_subnormal_full', [wheel(j,vf=1e-170,limit=1e-300) for j in range(4)],q32(128),'gas',dtype,0,128))
  cases.append((dtype+'_negative_zero',[wheel(j) for j in range(4)],-0.,'none',dtype,0,0))
  # Two opposing rear rolling targets produce a nonzero minimax interior.
  mid=bits32(.5);ws=[wheel(j) for j in range(4)]
  for j,delta in [(2,-7),(3,9)]:
   ws[j]=wheel(j,omega=1.,gas=.5,limit=1e-5);target=ref(ws[j],q32(mid+delta),'gas',dtype)[0];ws[j]['vf']=float(target/82.)
  cases.append((dtype+'_opposed_interior',ws,q32(mid+48),'gas',dtype,mid-48,mid+48))
  for sign in [-1.,1.]:
   for center in [.2,.9]:
    mid=bits32(center);ws=[wheel(j,omega=sign*3.,vf=.2,limit=.03,engine=.8) for j in range(4)]
    cases.append((f'{dtype}_brake_zero_lock_damage_{sign}_{center}',ws,q32(mid+48),'brake',dtype,mid-48,mid+48))
  # Pure full-domain constant lateral dominance => exact tie chooses q0.
  ws=[wheel(j,vs=100. if j<2 else 0.) for j in range(4)];cases.append((dtype+'_lateral_tie_full',ws,1.,'gas',dtype,0,bits32(1.)))
 outputs=[];br=set();checked=0
 for name,ws,q,branch,dtype,lo,hi in cases:
  p=solve(ws,q,branch,dtype,rank_lo=lo,rank_hi=hi);verify(ws,q,branch,dtype,p)
  exhaustive=hi-lo<=128
  if exhaustive:
   vals=[(max(ref(w,number(k),branch,dtype)[1] for w in ws),-k) for k in range(lo,hi+1)];best=min(vals);assert p['objective']==best[0] and p['q_rank']==-best[1],name;checked+=len(vals)
   # Direct source monotonic signed forces and V-shaped excess in finite windows.
   for w in ws:
    es=[ref(w,number(k),branch,dtype) for k in range(lo,hi+1)];fs=[x[0] for x in es];assert all(a<=b for a,b in zip(fs,fs[1:])) or all(a>=b for a,b in zip(fs,fs[1:]));m=min(range(len(es)),key=lambda i:es[i][1]);xs=[x[1] for x in es];assert all(a>=b for a,b in zip(xs[:m+1],xs[1:m+1])) and all(a<=b for a,b in zip(xs[m:],xs[m+1:]))
  for w in ws:
   for k in {lo,hi,(lo+hi)//2}:br.add(force(w,number(k),branch,dtype)['brake_branch'])
  outputs.append(dict(name=name,exhaustive=exhaustive,rank_count=hi-lo+1,selected_rank=p['q_rank'],objective=p['objective'],witness_passed=True))
 # Repeated gas ramp arithmetic only: no new force/body evolution.
 traces=[]
 for q in [.5,.8]:
  gas=0.;seq=[]
  for _ in range(4):diff=min(q-gas,.1);gas+=diff;seq.append(gas)
  traces.append(seq)
 # Equal first .1, but choose .15 vs .8 so remaining raw gas differs.
 traces=[]
 for q in [.15,.8]:
  gas=0.;seq=[]
  for _ in range(4):diff=min(q-gas,.1);gas+=diff;seq.append(gas)
  traces.append(seq)
 assert traces[0][0]==traces[1][0] and traces[0][-1]!=traces[1][-1]
 unsupported=[]
 for name,change in [('NaN',dict(vf=float('nan'))),('overflow',dict(vf=1e308)),('nonpositive_limit',dict(limit=0.)),('wrong_scalar_dtype',dict(vf=np.float32(0.)))]:
  ws=[wheel(j) for j in range(4)];ws[2].update(change)
  try:solve(ws,1.,'gas');raise AssertionError('unsupported accepted:'+name)
  except Unsupported as exc:unsupported.append(dict(name=name,reason=str(exc)))
 for name,ws,branch,q in [('wheel_identity',[wheel(0)]*4,'gas',1.),('none_nonzero',[wheel(j) for j in range(4)],'none',1.)]:
  try:solve(ws,q,branch);raise AssertionError('unsupported accepted:'+name)
  except Unsupported as exc:unsupported.append(dict(name=name,reason=str(exc)))
 assert br=={'none','linear','zero_clamp','lock'},br
 return dict(cases=outputs,total=len(outputs),exhaustive_cases=sum(x['exhaustive'] for x in outputs),exhaustively_compared_command_values=checked,observed_fixture_branches=sorted(br),unsupported=unsupported,repeated_gas_plateau_fixture=traces,damage='engine .8 synthetic arithmetic supported; actual saved damage0 only; no physical damage validation',all_passed=True,new_physics=0)
