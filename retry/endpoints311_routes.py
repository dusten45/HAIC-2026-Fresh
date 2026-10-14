"""All reachable terminal columns on the unchanged chosen row, one extra tree."""
import heapq
import numpy as np

def expand(image,obstacles,legacy,routing_problem):
 if not legacy:return legacy,dict(legacy_count=0,added_count=0,tree_runs=0,goal_row=None,terminal_columns=[])
 allowed,distance,start,_,goal,_=routing_problem(image,obstacles)
 assert start is not None and goal is not None
 costs,previous,queue={start:0.},{},[(0.,start)]
 moves=[(dy,dx,float(np.hypot(dx/1.3608,dy/1.701))) for dy in [-1,0,1] for dx in [-1,0,1] if dy or dx]
 while queue:
  cost,current=heapq.heappop(queue)
  if cost!=costs[current]:continue
  y,x=current
  for dy,dx,length in moves:
   ny,nx=y+dy,x+dx
   if not 24<=ny<=56 or not 3<=nx<81 or not allowed[ny,nx]:continue
   if dy and dx and(not allowed[y,nx] or not allowed[ny,x]):continue
   nxt=(ny,nx);new=cost+length*(1+2/max(float(distance[ny,nx]),1.5))
   if new<costs.get(nxt,float('inf')):costs[nxt]=new;previous[nxt]=current;heapq.heappush(queue,(new,nxt))
 candidates=list(legacy);columns=[]
 for col in sorted(c for row,c in costs if row==goal[0]):
  if col==goal[1]:continue
  endpoint=(goal[0],col);chain=[endpoint]
  while chain[-1]!=start:chain.append(previous[chain[-1]])
  path=[(0.,0.)]+[((x-42)/1.3608,(63-y)/1.701) for y,x in reversed(chain)]
  assert not any(path==c['path'] for c in legacy)
  candidates.append(dict(path=path,base_cost_m=costs[endpoint],side='terminal_'+str(col),terminal_column=col));columns.append(col)
 return candidates,dict(legacy_count=len(legacy),added_count=len(candidates)-len(legacy),tree_runs=1,goal_row=goal[0],original_terminal_column=goal[1],terminal_columns=columns)

def choose(candidates,speed,previous_steer,route_target,legacy_count,connection_weight=1.):
 if not candidates:return [],dict(candidate_count=0,selected_index=None,existing_rank_preserved=True)
 minimum=min(c['base_cost_m'] for c in candidates);original_min=candidates[0]['base_cost_m'];offset=max(0.,original_min-minimum);keys=[];details=[];oldkeys=[];newlegacykeys=[]
 for i,c in enumerate(candidates):
  x,y=map(float,route_target(c['path'],speed));curvature=2*x/max(y*y+x*x,1e-6);raw=float(np.clip(np.arctan(3.24*curvature),-.4,.4));next_steer=.8*raw+.2*previous_steer;connection=max(0.,speed)*abs(next_steer-previous_steer)/3.
  if i<legacy_count:
   oldgap=max(0.,c['base_cost_m']-original_min);oldgap=0. if oldgap<1e-9 else oldgap;oldscore=oldgap+connection_weight*connection;gap=oldgap+offset;score=oldscore+offset;key=(score,0,oldscore,i);oldkeys.append((oldscore,i));newlegacykeys.append((key,i))
  else:
   gap=max(0.,c['base_cost_m']-minimum);gap=0. if gap<1e-9 else gap;score=gap+connection_weight*connection;key=(score,1,c['terminal_column'],i)
  keys.append((key,i));details.append(dict(base_gap_m=gap,connection_m=connection,next_steer=next_steer,side=c['side']))
 assert [i for _,i in sorted(oldkeys)]==[i for _,i in sorted(newlegacykeys)]
 selected=min(keys)[1]
 return candidates[selected]['path'],dict(candidate_count=len(candidates),selected_index=selected,previous_command_proxy=previous_steer,speed_estimate_m_s=speed,connection_weight=connection_weight,candidate_scores=details,expanded_minimum_cost_m=minimum,legacy_shared_gap_offset_m=offset,existing_rank_preserved=True,selected_added=selected>=legacy_count)
