"""Stored-only437 actual comparison; no policy call or integration."""
import copy,json,sys,time
from pathlib import Path
from dataclasses import asdict
from retry.receipt421_io import load_receipt,receipt_digest
from retry.receipt435 import choose,runtime_restore
from retry.audit431 import from_wire
from retry.preflight421 import restore_typed
from retry.pilot420_json import json_ready
from retry.loss389_analyze import read,save,sha

def run(root):
 d=root/'stage437';assert not(d/'analysis.json').exists();cpu=time.process_time();wall=time.perf_counter();result=read(d/'result.json');checks=[]
 for path in d.glob('P_decision*-evidence-private.json'):
  x=load_receipt(path);ctx,ev=restore_typed(copy.deepcopy(x));ev.update({r:from_wire(w) for r,w in x['early_evidence'].items()});ev.update({r:runtime_restore(w) for r,w in x['runtime_evidence'].items()});choice=choose(ctx,ev);assert json_ready(asdict(choice))==x['decision'];h=read(d/path.name.replace('-evidence-private.json','-receipt-digest.json'));assert receipt_digest(x)==h['digest'] and h['parent_unchanged'] and h['RNG_unchanged'];checks.append(dict(query=path.name.split('-')[0],recipe=choice.recipe,receipt_verified=True))
 arms=result['actual'];pair=len(arms)==2 and all(a['completed'] for a in arms);gain=None;gainbracket=None
 if pair:
  a,b=arms;gain=(a['official_event_time_s']-b['official_event_time_s']);u=a['suffix_event_rawtick_bracket'];v=b['suffix_event_rawtick_bracket'];gainbracket=[(u[0]-v[1])/50,(u[1]-v[0])/50]
 posthoc={}
 for arm in arms:
  name=arm['arm'];actual=[json.loads(t) for t in (d/('actual_'+name)/'trace-private.jsonl').read_text().splitlines()][118:];old=read(root/'stage436'/('parent_'+name+'-private.json'))['rows'];delta=[]
  for i,(a,b) in enumerate(zip(actual,old),1):delta.append(dict(relative_action=i,max_command_abs_delta=max(abs(x-y) for x,y in zip(a['command'],b['command'])),position_error_m=sum((x-y)**2 for x,y in zip(a['post']['pos'],b['predicted']['position']))**.5))
  posthoc[name]=dict(scope='Read436futureONLYafter437actualexecutionclosed; notselectorinput.',compared_rows=len(delta),first_command_difference_over1e_6=next((x for x in delta if x['max_command_abs_delta']>1e-6),None),max_position_error_m=max((x['position_error_m'] for x in delta),default=None))
 q=dict(stage=437,status=result['status'],error=result['error'],fresh_pair_both_official_completed=pair,actual_official_event_gain_s=gain,actual_gain_rawtick_bracket_s=gainbracket,unfinished_lap_time_estimated=False,receipt_rechecks=checks,actual=arms,posthoc436_comparison=posthoc,pixel_promotion=False,generalization=False,new_HOLDOUT_SEALED_seed_reserve=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'analysis.json',q);print(json.dumps(dict(status=q['status'],actual_actions=result['budget']['actual']['actions'],model_ticks=result['budget']['model']['ticks'],receipt_rechecks=len(checks),gain=gain,gain_bracket=gainbracket)))
if __name__=='__main__':run(Path(sys.argv[1]))
