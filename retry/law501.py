"""501 own-state candidate and incremental registered factual calibration.

Candidate inputs contain no saved trajectory, future command or finish label.
Scalar500 code, geometry, P4 and SourceC nominal/steering are unchanged.
"""
import copy,math
from dataclasses import asdict
import numpy as np
from retry import envelope500

class ScreenStop501(RuntimeError):pass

def check(v,s):
    if not v:raise ScreenStop501(s)


def candidate_one(c,arcs,nodes,project):
    before=copy.deepcopy(c.ctrl.memory());nominal=c.ctrl.act(c.m);after=copy.deepcopy(c.ctrl.memory())
    phase=c.ctrl.phase();h=c.m.car.hull
    if phase=='FINISH_CONFIRM':
        # Existing SourceC has already validated the current own corridor and
        # tracker. No new pending/terminal policy or forecast is manufactured.
        command=np.asarray(nominal,np.float32).copy();details={'scope':'UNCHANGED_QUALIFIED_CONFIRMATION'}
    else:
        check(phase=='FIRST_LAP','CANDIDATE_PHASE')
        q=project(c.fixed['line'],list(h.position),list(h.linearVelocity),phase)
        details=envelope500.act(np.asarray(nominal).tolist(),phase,q['arc'],math.hypot(*h.linearVelocity),q['sigma'],arcs,nodes)
        command=np.asarray(details['action'],np.float32)
    n=len(c.rows)
    c.one('501_FIXED_ENVELOPE',first_override=command,prepared_nominal=nominal,prepared_before=before)
    check(len(c.rows)==n+1,'CANDIDATE_NO_OBSERVED_ROW')
    row=c.rows[-1];check(row['memory_before']==before and row['memory_after']==after,'NOMINAL_MEMORY_NOT_ONCE')
    check(row['command']==command.tolist() and command[0]==nominal[0],'COMMAND_OR_STEERING_CHANGED')
    expected=copy.deepcopy(after)
    if c.status=='FINISHED':expected['C']['phase']='DONE'
    check(c.ctrl.memory()==expected,'ONLY_OWN_OFFICIAL_DONE')
    return details


class FactualGate501:
    def __init__(self,mods,fixed,ledger):
        self.mods=mods;self.fixed=fixed;self.old=ledger
        geo=mods['geometry439'];self.projection=geo.Projection439(fixed['line'],sum(fixed['free_profile']['ds']),.1)
        self.telescope=geo.Telescope439(self.projection);self.goal_i=geo.Interval.point(ledger.goal_m)
        self.model=mods['planner419_model_ledger'].ForecastLedger.fork(ledger)
        self.records=[];self.nominal_delta_max=0.;self.memory_exact_rows=0
    def one(self,c,row,after,nominal):
        f=c.rows[-1];mods=self.mods;ledger=mods['ledger439'];q=f['predicted']
        check(np.array_equal(np.asarray(f['command'],np.float32),np.asarray(row['command'],np.float32)),'FACTUAL_COMMAND')
        check(f['memory_before']['C']['phase']==row['memory_before']['C']['phase'] and f['memory_after']['C']['phase']==row['nominal_memory_after']['C']['phase'],'FACTUAL_PHASE')
        body=mods['paired417_common'].shapecheck(f,row)
        check(body['passed'] and body['wheel']['clipped_flag_mismatches']==0,'FACTUAL_BODY_WHEEL_HULL')
        check(set(f['safety'])==set(row['safety']) and not f['safety'],'FACTUAL_SAFETY')
        # Existing435 replay compared phase exactly and recorded future nominal
        # drift; exact nominal/memory/current input remains a copied-root rule.
        self.nominal_delta_max=max(self.nominal_delta_max,float(np.max(np.abs(np.asarray(nominal)-np.asarray(row['nominal'])))))
        self.memory_exact_rows+=int(f['memory_before']==row['memory_before'] and f['memory_after']==row['nominal_memory_after'])
        native_posts=after['posts'];model_posts=c.capture_session495.posts
        check(len(native_posts)==len(model_posts)==q['raw_ticks'],'FACTUAL_DIRECT_POST_COVERAGE')
        for a,b in zip(native_posts,model_posts):
            check('damage' not in a and 'phase' not in a,'HISTORICAL_MISSING_FIELDS_CHANGED')
            check(abs(a['time']-b['time'])<1e-8 and math.dist(a['position'],b['position'])<=.1 and abs(math.hypot(*a['velocity'])-math.hypot(*b['velocity']))<=.5,'FACTUAL_TRACKER_POST_PHYSICAL')
            check(a['collision']==b['collision'] and a['wheel_road_contacts']==b['wheel_road_contacts'] and a['progress']==b['progress'],'FACTUAL_TRACKER_POST_FLAGS_PROGRESS')
            ta,tb=a['tracker_after'],b['tracker_after']
            # Static geometry and directly observed discrete/event state exact.
            # Tracker's continuous last-position arithmetic is replayed on its
            # OWN observed posts below, not given a newly invented tolerance.
            for k,av in ta.items():
                if isinstance(av,bool) or av is None or k.endswith('_time_s') or k in ('center','forward','half_width','half_depth'):
                    bv=tb[k]
                    if isinstance(av,float) and k.endswith('_time_s'):check(bv is not None and abs(av-bv)<1e-8,'FACTUAL_TRACKER_EVENT:'+k)
                    else:check(av==bv,'FACTUAL_TRACKER_DISCRETE:'+k)
        check(after['full_post']['physical']['damage']==q['damage'],'FACTUAL_WRAPPER_DAMAGE')
        actual,observed=ledger.row_candidate(self.old,row,self.fixed['line'],self.projection.L)
        t=ledger.geometry_transition(self.projection,f,row)
        predicted=self.projection.progress(self.model.progress_m,t,'model')
        check(predicted==f['model_progress']==c.ledger.progress_m,'FACTUAL_OWN_PROGRESS')
        nextmodel=self.model.advance_prediction(mods['planner419_model_ledger'].ModelPrediction(predicted,self.model.last_clock_tick+q['raw_ticks'],q['finished']))
        bound=self.telescope.advance(self.old.progress_m,self.model.progress_m,actual.progress_m,nextmodel.progress_m,t)
        cert,self.goal_i=ledger.compare_ledgers(self.old,actual,self.model,nextmodel,observed['goal_hit'],bool(predicted>=self.model.goal_m or q['finished']),bound,self.goal_i)
        first=None
        if not self.records:
            _,first=ledger.compare_first(self.old,f,row,self.fixed)
        check(asdict(nextmodel)==asdict(c.ledger),'FACTUAL_FULL_MODEL_LEDGER')
        self.old,self.model=actual,nextmodel
        result=dict(global_step=row['step'],physical=body,progress_interval=cert['progress_interval'],progress_difference_m=cert['progress_difference_m'],ledger_discrete_exact=True,phase_exact=True,direct_post_registered_fields=True,first_current_exact=first is not None)
        self.records.append(result);return result
    def result(self):
        return dict(passed=len(self.records)==149,holds=len(self.records),max_recomputed_nominal_difference=self.nominal_delta_max,memory_exact_rows=self.memory_exact_rows,scope='Existing435 full factual body/wheel/hull/phase calibration plus439 continuous geometry/discrete ledger. Future continuous nominal-memory drift is recorded, not certified as fresh copied-current exact. Missing old direct postdamage/phase not filled.',records=self.records)
