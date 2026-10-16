"""Source+saved-record positive/negative controls, never simulation or control."""
import ast,copy,datetime,hashlib,json,sys,time
from pathlib import Path
from retry.terminal409_contract import validate
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def new(p,x):
 assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def source_checks():
 wrapper=ast.parse((G/'env_wrapper.py').read_text());cls=next(x for x in wrapper.body if isinstance(x,ast.ClassDef) and x.name=='CarEnvironment');step=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='step');loop=next(x for x in ast.walk(step) if isinstance(x,ast.For) and ast.unparse(x.iter)=='range(self._skip_frames)');br=any(isinstance(x,ast.If) and ast.unparse(x.test)=='terminated or truncated' and any(isinstance(z,ast.Break) for z in x.body) for x in loop.body)
 core=ast.parse((G/'core/vendor/car_racing.py').read_text());fps=next(x.value.value for x in core.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FPS' for t in x.targets));newlap=any(isinstance(x,ast.Assign) and any(ast.unparse(t)=='self.new_lap' for t in x.targets) and ast.unparse(x.value)=='self.finish_time_s is not None' for x in ast.walk(core));trunc=any(isinstance(x,ast.If) and ast.unparse(x.test)=='self.new_lap' and any(isinstance(z,ast.Assign) and ast.unparse(z)=='truncated = True' for z in x.body) for x in ast.walk(core));tracker=(G/'core/finish_line.py').read_text();checks=dict(wrapper_breaks_on_terminal=br,FPS50=fps==50,official_finish_sets_newlap=newlap,newlap_returns_truncated=trunc,tracker_keeps_crossing_candidate_time='self.finish_time_s = crossing_time_s' in tracker and 'longitudinal >= self.half_depth' in tracker);assert all(checks.values());return checks

def run(root):
 d=root/'stage409';assert not d.exists();d.mkdir(mode=0o700);b=read(root/'project-effective-budget-v428.json');assert (b['research_remaining'],b['final_reserved_actions'],b['final_reserve_used'])==(30892,84000,0)
 old=root/'stage408';original=[old/n for n in ['plan.json','plan.sha256','result.json','analysis.json','analysis-plan.json','cost.json','closure-checks.json','trace-private.jsonl','initial-private.json','final-full-private.json','stop-private.json']]+[G/'retry'/n for n in ['lap408_run.py','lap408_analyze.py','lap408_result.json','lap408_result.md']];protected=[root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json'];sources=[Path(__file__),G/'retry/terminal409_contract.py',G/'env_wrapper.py',G/'core/vendor/car_racing.py',G/'core/finish_line.py',root/'project-effective-budget-v428.json',root/'research-deadline-current.json']+original
 plan=dict(stage=409,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],scope='SourceAST andstored408 clock/sample/terminal audit; syntheticrecordmutations only; separatecorrectedcontract, frozen408neverwaived. Currentstate13actionrisk/progress designonly, no forecasts/optimization executed.',CPU_cap_s=10,wall_cap_s=30,new_wrapper_reset_actor_model_learning_SEALED_paid_reserve_cap=0,sources={str(p):sha(p) for p in sources},original408_preserve={str(p):sha(p) for p in original},protected={str(p):sha(p) for p in protected});new(d/'plan.json',plan);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);cpu=time.process_time();wall=time.perf_counter();sc=source_checks();rows=[json.loads(s) for s in (old/'trace-private.jsonl').read_text().splitlines()];initial=read(old/'initial-private.json');final=read(old/'final-full-private.json');r=read(old/'result.json');checks=[validate(z) for z in rows];assert all(z['passed'] for z in checks)
 last=rows[-1];mutations=[]
 def control(name,row,expected,kind=None):
  v=validate(row);assert v['passed']==expected,(name,v)
  if kind:assert v['classification']==kind
  mutations.append(dict(name=name,synthetic=True,expected_pass=expected,actual_pass=v['passed'],classification=v['classification'],errors=v['errors']))
 control('unchanged_full188',copy.deepcopy(rows[-2]),True,'nonterminal');control('unchanged_partial_finish189',copy.deepcopy(last),True,'official_finish')
 z=copy.deepcopy(last);z['raw_tire_samples'].pop();control('drop_one_wheel_sample',z,False)
 z=copy.deepcopy(last);z['raw_tire_samples']=z['raw_tire_samples'][:-4];control('drop_whole_rawtick_samples_clock_unchanged',z,False)
 z=copy.deepcopy(last);z['raw_tire_samples'][-1]['wheel']=0;control('duplicate_wheel_same_count',z,False)
 z=copy.deepcopy(last);z['raw_tire_samples'][-1]['raw_tick']=2;control('wrong_tick_label_same_count',z,False)
 z=copy.deepcopy(last);z['post']['time']+=.02;control('clock_advances_unlogged_tick',z,False)
 z=copy.deepcopy(last);z.update(ended=False,truncated=False,completed=False,finish_time_s=None);control('short_repeat_without_terminal',z,False)
 z=copy.deepcopy(last);z['finish_time_s']=z['post']['time']+.02;control('future_finish_timestamp',z,False)
 z=copy.deepcopy(last);z['finish_time_s']=None;control('completed_missing_finish_timestamp',z,False)
 z=copy.deepcopy(last);z.update(ended=True,truncated=False,completed=False,finish_time_s=None);control('other_terminal_is_not_official_lap',z,True,'other_terminal')
 n=sum(z['raw_ticks'] for z in rows);ns=sum(len(z['raw_tire_samples']) for z in rows);assert n==755 and ns==3020 and final['wrapper']['elapsed_raw_steps']-initial['wrapper']['elapsed_raw_steps']==n
 assert abs(final['physical']['actual_time']-initial['physical']['actual_time']-n/50)<1e-8 and all(abs(rows[i]['pre']['time']-rows[i-1]['post']['time'])<1e-8 for i in range(1,len(rows)))
 assert not any(z['ended'] or z['truncated'] for z in rows[:-1]);ft=final['wrapper']['finish_time_s'];qt=final['wrapper']['finish_qualified_time_s'];assert qt<=ft<=last['post']['time'] and ft==last['finish_time_s'] and abs(round((ft-initial['physical']['actual_time'])*1000)-15080)==0
 assert r['status']=='QUALIFICATION_OR_TECHNICAL_STOP' and r['error']=='QualificationFailure: rawtickshape' and not r['completed_safe']
 for f,h in {**plan['sources'],**plan['protected']}.items():assert sha(f)==h,f
 cpu_s=time.process_time()-cpu;wall_s=time.perf_counter()-wall;assert cpu_s<10 and wall_s<30
 result=dict(stage=409,source_checks=sc,stored_rows=189,corrected_contract_pass_rows=189,nonterminal_full_repeat_rows=188,normal_partial_terminal_rows=1,terminal_raw_ticks=3,terminal_wheel_samples=12,total_raw_ticks=n,total_wheel_samples=ns,clock_continuous=True,wrapper_elapsed_counter_delta=755,initial_raw_time=initial['physical']['actual_time'],final_raw_time=final['physical']['actual_time'],last_pre_time=last['pre']['time'],official_finish_timestamp=ft,last_post_time=last['post']['time'],official_lap_ms=15080,observed_delta_vs_O268_ms=300,damage=0,qualification_timestamp=qt,finish_confirmation_lag_s=last['post']['time']-ft,finish_timestamp_is_candidate_crossing_not_required_to_equal_confirmation=True,original408_status_preserved=r['status'],original408_completed_safe_preserved=False,original408_changed=False,original408_DONE_mark_still_not_run=True,separate_corrected_measurement_contract_pass=True,controls=mutations,negative_controls_rejected=sum(not z['expected_pass'] for z in mutations),no_new_driving_inference=True,new_wrapper_actions=0,new_resets=0,new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,new_reserve_use=0,CPU_s=cpu_s,wall_s=wall_s);new(d/'result.json',result);(G/'retry/terminal409_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':run(Path(sys.argv[1]))
