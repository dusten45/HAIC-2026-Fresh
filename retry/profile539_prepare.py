"""Prepare one profile and roots from saved538 only. No physics integration."""
import hashlib,json,math,time
from pathlib import Path
from retry.profile539_profile import rebuild_profile

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response539-private');S=Path('/workspace/haic-response538-private');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();old=read(S/'frozen-paths-private.json');s=read('/workspace/haic-response515-private/collected-map-state-private.json');lateral=.70*sum(w['friction'] for w in s['root']['planar']['linear']['wheels'])/s['root']['planar']['linear']['mass'];base=old['candidate'];check=rebuild_profile(base,lateral,80.);assert check==base;new=rebuild_profile(base,lateral)
 for k in ('points','ds','arcs','length','curvature'):assert new[k]==base[k]
 paths=dict(baseline=base,baseline_backup=old['backup'],candidate=new,backup=old['backup'])
 with (D/'frozen-paths-private.json').open('x') as f:json.dump(paths,f,indent=2)
 (D/'approved-case-private.json').write_bytes((S/'approved-case-private.json').read_bytes())
 rows=read(D/'accounting-rows-private.json');info=read(G/'retry/profile539_analysis.json');first=info['longest_flat_run']['first_action'];last=info['longest_flat_run']['last_action'];valid=[]
 for i in range(first,last+1):
  z=[r for r in rows if r['index']==i]
  if any(i<=r['index']<i+12 and r['ff']< -1 for r in rows):valid.append((max(r['v'] for r in z),i))
 assert valid;decel=max(valid,key=lambda x:(x[0],-x[1]))[1];geo=min(rows,key=lambda r:r['margin'])['index'];selected=[dict(label='cap-plateau',index=first,holds=16),dict(label='next-braking',index=decel,holds=12),dict(label='footprint',index=geo,holds=12)]
 start=read(S/'close-baseline-private.json')['counts']['raw_completed']+51;raw=[read(p) for p in sorted(S.glob('raw-*.json')) if int(p.stem.split('-')[-1])>start];cases=[]
 for c in selected:
  a=read(S/('action-candidate-%03d.json'%c['index']));rr=[r for r in raw if r['phase']=='action' and 24<r['action']<c['index']];cases.append(dict(c,completed=c['index']-1,root_without_roads=a['before_root_without_roads'],history=dict(samples=4*len(rr),clipped=sum(z['ratio']>1 for r in rr for z in r['forces']))))
 with (D/'pilot-roots-private.json').open('x') as f:json.dump(cases,f)
 clock=lambda p:sum(2*d/(math.sqrt(p['launch_squared'][i])+math.sqrt(p['launch_squared'][i+1])) for i,d in enumerate(p['ds']))
 out=dict(candidate='One90primary referencecap; fixed533geometry/538source-response/backup80/othercriteria.90=0.9*solverbody100 reference reserve, not body safety proof. Allowed+4.85 band consumes part of reserve; allbody<100 remains explicit.',geometry_identical=True,baseline80_arithmetic_exact=True,backup_identical=True,scalar_reference_clocks_s={'baseline':clock(base),'candidate':clock(new)},scalar_clock_is_not_physical_bound_or_recoverable_gain=True,roots=selected,root_selection='Firstactionlongestactual538flat80run,16hold; maxactualspeedactionthere withnegativeffwithin12holds,12hold; globalactualminimumfootprintbeforestate,12hold. Determinedfrom538only, before539outcomes.',frozen_paths_sha256=sha(D/'frozen-paths-private.json'),pilot_roots_sha256=sha(D/'pilot-roots-private.json'),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,model_ticks=0)
 with (G/'retry/profile539_preparation.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
