"""Fixed nine policies, direct strict source feasibility, no native admission.

603compiled kernel is compared with the original margin on EVERY memo miss.
"""
import time
BOOT_CPU = time.process_time(); BOOT_WALL = time.perf_counter()
import datetime, importlib.util, json, math, signal, subprocess, traceback
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import numpy as np
import retry.profile601 as prior
import retry.reuse601 as reuse
import retry.segments602 as compiled_geometry
import retry.residual604_math as residual
import retry.cold597_model as old597
from retry.checkpoints574 import clone
from retry.beam579_math import immutable, isolated
from retry.retime590_math import Gates, planes
from retry.lap518_finish import tracker_for
from retry.clip561_core import atomic_write
from retry.durable568 import Journal, evaluate_force, digest
base = prior.base; d = base.old.d
G = base.G; D = Path('/workspace/haic-response604-private')
CAPS = dict(model_attempted=180000, model_completed=180000, external_force=720000,
            internal_force=720000, total_force=1440000, geometry=600000)
REPLAY = dict(model_attempted=1174, model_completed=1174, external_force=4696,
              internal_force=4696, total_force=9392, geometry=7200)
RAW_KEYS = old597.REPLAY_KEYS + ['official_finish_raw']


class BudgetStop(RuntimeError): pass
class CandidateDomain(RuntimeError): pass


class Crossing(Gates):
    def __init__(self, owner):
        super().__init__(owner.planes); self.owner = owner; self.ineligible = []
    def add(self, row):
        self.owner.capacity(dict(geometry=len(self.planes) - len(self.hits)))
        self.owner.add('geometry', len(self.planes) - len(self.hits))
        before = set(self.hits)
        super().add(row)
        for key in set(self.hits) - before:
            if not self.hits[key]['eligible']:
                self.ineligible.append((key, self.hits.pop(key)))


class Applied:
    def __init__(self, owner):
        self.owner = owner; self.counter = owner.model; self.cost = owner.planner
    def evaluate(self, root, action, history, context, peak, clip, check_clip):
        o = self.owner; o.active_trial = None; o.model_mode = 'applied'
        value = base.old.body(root)
        if not math.isfinite(value): raise ValueError('NONFINITE_APPLIED_CURRENT_BODY')
        if value >= 100: raise CandidateDomain('APPLIED_CURRENT_BODY_GE100')
        o.applied_journal.append('APPLIED_INPUT', label=o.label, checkpoint=o.checkpoint(o.state), context=context, action_bits=action.tobytes().hex())
        verdict = evaluate_force(o.applied_journal, o.short(root), action.tolist(), history, context,
                                  lambda: o.model_force(root, action), peak, clip, check_clip)
        if verdict['gate']: o.pending = None
        return verdict
    def tick(self, *args):
        o = self.owner; o.applied_journal.append('APPLIED_TICK_START', label=o.label, counts=dict(o.counts))
        try: after = o.model_tick(*args)
        except base.old.DomainStop as exc: raise CandidateDomain(str(exc)) from exc
        o.applied_journal.append('APPLIED_TICK_END', label=o.label, root=o.short(after), counts=dict(o.counts))
        return after
    def geometry(self, root): return self.owner.source_geometry(root)


class Study(prior.Meter):
    def __init__(self):
        D.mkdir(mode=0o700, exist_ok=False)
        static = json.loads(base.old.INPUTS['static'].read_text())
        super().__init__(static, {})
        self.index = self.source_index; self.edge = self.source_edges
        self.paths = json.loads(base.old.INPUTS['candidate_paths'].read_text())
        self.ledger = json.loads(base.old.INPUTS['ledger'].read_text())
        self.applied_journal = Journal(D / 'applied-journal-private.jsonl')
        self.state = None; self.results = []; self.prefix_rows = []; self.records = {}
        self.context = None; self.errors = []; self.label = 'preparation'
        self.phase = 'preparation'; self.checks = {}; self.saved = []
        self.prefix = None; self.replay_result = None
        self.orig_geometry_margin = compiled_geometry.full.road_margin
        self.original_distance = compiled_geometry.distance
        self.original_plain_road = compiled_geometry.original.margin
        self.initial_state = None
    def times(self): return dict(CPU_s=time.process_time() - BOOT_CPU + 10., wall_s=time.perf_counter() - BOOT_WALL + 10.)
    def guard(self, *args):
        t = self.times()
        if t['CPU_s'] >= 5370 or t['wall_s'] >= 6555: raise BudgetStop('TOTAL_CLEANUP_RESERVE')
        if datetime.datetime.now(datetime.timezone.utc) >= base.DEADLINE: raise BudgetStop('DEADLINE')
    def capacity(self, req):
        self.guard()
        for k, n in req.items():
            if k in CAPS and self.counts[k] + n > CAPS[k]: raise BudgetStop('CAP_' + k)
    def add(self, k, n=1):
        self.capacity({k:n}); self.counts[k] += n
    def checkpoint(self, state):
        return dict(root=self.short(state['root']), progress=state['progress'], tracker=asdict(state['tracker']),
                    visited=sorted(state['visited']), launch=state['launch'].copy(), tracking=state['tracking'].copy(),
                    elapsed=state['elapsed'], global_raw=state['global_raw'])
    def reserve(self, feedback, replay_tail=True):
        need = dict(model_attempted=1540 if feedback else 4, model_completed=1540 if feedback else 4,
                    external_force=6160 if feedback else 16, internal_force=6160 if feedback else 16,
                    total_force=12320 if feedback else 32, geometry=6200 if feedback else 40)
        if replay_tail:
            need = {k:v + REPLAY[k] for k,v in need.items()}
        self.capacity(need)
        t = self.times(); tail_c, tail_w = (90,120) if replay_tail else (0,0)
        if t['CPU_s'] + 60 + tail_c + 30 >= 5400 or t['wall_s'] + 75 + tail_w + 45 >= 6600:
            raise BudgetStop('NEXT_HOLD_REPLAY_CLEANUP_TIME')
        if datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=75 + tail_w + 45) >= base.DEADLINE:
            raise BudgetStop('NEXT_HOLD_DEADLINE')
        self.applied_journal.append('HOLD_RESERVE', label=self.label, hold=self.next_hold, requests=need,
                                    CPU_s=60, wall_s=75, replay_CPU_s=tail_c, replay_wall_s=tail_w, counts=dict(self.counts))
    def begin_context(self):
        assert self.context is None
        self.context = reuse.Cache(self)
        ctx = self.context
        road = compiled_geometry.Road(*ctx.args[:4], already_frozen=True)
        compiled_geometry.full.road_margin = road
        original = ctx.original
        def checked_no_recursion(root, *args):
            value = original(root, *args)
            self.capacity(dict(geometry=1)); self.add('geometry'); self.add('helper_original_comparisons')
            plain = min(self.original_plain_road(root, *args[:4]),
                        compiled_geometry.full.obstacle_margin(compiled_geometry.original.polygons(root), args[4]))
            if not compiled_geometry.same(value, plain): raise AssertionError('603_HELPER_MARGIN_BITS_CHANGED')
            return value
        ctx.original = checked_no_recursion
        self._context_original = original
    def end_context(self):
        if self.context is not None:
            ctx = self.context
            # Cache.restore must restore the actual pre-context callable.
            ctx.original = self._context_original
            ctx.restore(); self.context = None
        compiled_geometry.full.road_margin = self.orig_geometry_margin
    def flush(self, label, hold, detail=None):
        data = dict(label=label, hold=hold, detail=detail, events=prior.materialize(self.journal.rows),
                    wheel_results=prior.materialize(self.raw_kernels), counts=dict(self.counts), time=self.times())
        atomic_write(D / f'{label}-hold-{hold:03d}-private.json', data)
        self.journal.rows.clear(); self.trial_summaries.clear(); self.raw_kernels.clear()
    def initial(self):
        root = d.load_root(self.static['root']); immutable(root)
        visited = set(self.ledger['initial_visited'])
        s = self.project('initial_projection', root.center, self.paths['candidate'], 0.)['s']
        self.add('geometry')
        tracker = tracker_for(self.static, root, visited, False, 1.02)
        self.state = dict(root=root, progress=s, visited=visited, tracker=tracker, elapsed=0., global_raw=0,
                          launch=[0,0], tracking=[0,0])
        self.begin_context()
        try: gap = self.source_geometry(root)
        finally: self.end_context()
        assert gap >= .5 and base.old.body(root) < 100 and tracker.finish_time_s is None
        return self.state
    def raw(self, action, h, k):
        self.capacity(dict(model_attempted=1,model_completed=1,external_force=4,internal_force=4,total_force=8,geometry=6))
        row, why = old597.base.Study.raw(self, self.state, action, h, k, Applied(self))
        row['tick_executed'] = 'root_without_roads' in row
        if row['tick_executed']:
            row['visited'] = sorted(self.state['visited'])
            row['checkpoint_sha256'] = digest(self.checkpoint(self.state))
            row['official_finish_raw'] = old597.official_raw(self.state['tracker'].finish_time_s)
        self.applied_journal.append('APPLIED_RESULT', label=self.label, row=row)
        return row, why
    def same_saved(self, row):
        old = self.tape['rows'][row['global_raw_before']]
        assert all(digest(row[k]) == digest(old[k]) for k in RAW_KEYS), '597_ROW_OR_CHECKPOINT_MISMATCH'
    def choose(self, h):
        self.model_mode = 'incumbent_forecast'; before = digest(self.checkpoint(self.state))
        self.add('chooser_calls'); begin = len(self.trial_summaries)
        action, report = base.old.tracking.choose(self.state['root'], self.paths['candidate'], self.paths['backup'],
            self.state['progress'], self.model, self.planner, 180000, history=tuple(self.state['tracking']), geometry=self.geometry_context)
        assert digest(self.checkpoint(self.state)) == before, 'INCUMBENT_MUTATED_ACTUAL_STATE'
        assert all(q['exact'] for q in self.trial_summaries[begin:])
        if action is not None:
            assert report['final_recertified'] and any(q['mode']=='FINAL' and q['ok'] for q in report['reports'])
        return action, report
    def residual_action(self, incumbent, coeff):
        def target(s, path):
            self.add('geometry'); return residual.target(s, path)
        return residual.action(self.state['root'], self.paths['candidate'], self.state['progress'], incumbent, coeff,
            lambda *a: self.project('residual_projection', *a), target)
    def prefix96(self):
        self.label = 'prefix'; self.state = self.initial(); self.initial_state = clone(self.state)
        for h in range(1,25):
            self.next_hold = h; self.reserve(False); self.begin_context()
            try:
                for k in range(1,5):
                    row, why = self.raw(self.fixed[h], h, k)
                    assert why is None; self.same_saved(row); self.prefix_rows.append(row)
            finally: self.end_context(); self.flush('prefix',h)
        self.prefix = clone(self.state); immutable(self.prefix['root']); isolated(self.prefix,[self.state])
        assert self.prefix['global_raw'] == 96
        assert digest(self.checkpoint(self.prefix)) == self.tape['rows'][95]['checkpoint_sha256']
        self.prefix_hash = digest(self.checkpoint(self.prefix))
        atomic_write(D / 'raw96-checkpoint-private.json', self.checkpoint(self.prefix))
        self.checks['raw96_initial_prefix_all_rows_and_full_checkpoint_exact597'] = True
    def evaluate(self, label, coeff):
        self.label = label; self.state = clone(self.prefix); isolated(self.state,[self.prefix])
        assert digest(self.checkpoint(self.prefix)) == self.prefix_hash
        gates = Crossing(self); rows=[]; commands=[]; reason=None; first_failure=None
        start_cost = self.counts.copy(); start_time = self.times()
        atomic_write(D / (label + '-STARTED-private.json'), dict(coeff=coeff, checkpoint_sha256=self.prefix_hash))
        for h in range(25,295):
            if 50 + self.state['global_raw'] >= 1224:
                reason='ORIGINAL_TIME_LIMIT_ENDPOINT_CENSORED'; break
            self.next_hold=h; self.reserve(h>=40); self.begin_context(); details=None; hold=[]
            try:
                incumbent = self.fixed[h].copy() if h<=39 else None
                report=None
                if h>=40: incumbent, report = self.choose(h)
                if incumbent is None:
                    reason='INCUMBENT_NO_ADMISSIBLE_ACTION'; first_failure=dict(hold=h, report=report); break
                action, meta = self.residual_action(incumbent, coeff)
                details=dict(incumbent_bits=incumbent.tobytes().hex(), action_bits=action.tobytes().hex(), original_FINAL=report,
                             residual=meta, modified_action_future_certified=False)
                if label=='zero':
                    assert action.tobytes() == incumbent.tobytes()
                    if h>=40:
                        old = self.old_choices[h]
                        assert digest(report) == digest(old['detail']) and action.tolist() == old['action'], 'ZERO_CHOICE_MISMATCH597'
                commands.append(dict(index=h, action=action.tolist()))
                for k in range(1,5):
                    if 50+self.state['global_raw']>=1224: reason='ORIGINAL_TIME_LIMIT_ENDPOINT_CENSORED'; break
                    row, why = self.raw(action,h,k); rows.append(row); hold.append(row)
                    if label=='zero': assert not why; self.same_saved(row)
                    if why:
                        reason='APPLIED_STRICT_'+why; first_failure=dict(hold=h,raw=k,global_raw_before=row['global_raw_before'],reason=why); break
                    gates.add(row)
                    if self.state['tracker'].finish_time_s is not None: raise AssertionError('UNEXPECTED_WHOLE_FINISH_BEFORE_ENDPOINT_STOP')
                gates.finish_hold(hold)
            except CandidateDomain as exc:
                reason='CANDIDATE_APPLIED_BODY_DOMAIN'; first_failure=dict(hold=h,reason=str(exc))
            except base.old.DomainStop as exc:
                reason='CANDIDATE_FORECAST_BODY_DOMAIN'; first_failure=dict(hold=h,reason=str(exc))
            finally:
                self.active_trial=None; self.pending=None; self.end_context(); self.flush(label,h,details)
            atomic_write(D / (label+'-latest-private.json'), dict(checkpoint=self.checkpoint(self.state), reason=reason, counts=dict(self.counts)), True)
            if reason or gates.passed('400'): break
        safe = reason is None and gates.passed('400')
        if reason is None and not safe: reason='ENDPOINT_NOT_REACHED_CENSORED'
        summary=dict(label=label,coefficients=coeff,safe_s400=safe,stop=reason or 'SAFE_S400_WHOLE_HOLD',failure=first_failure,
            applied_completed=sum(q['tick_executed'] for q in rows),applied_attempted=len(rows),global_raw=self.state['global_raw'],
            crossings=gates.hits,cost={k:self.counts[k]-start_cost[k] for k in self.counts},
            time={k:self.times()[k]-start_time[k] for k in start_time}, endpoint_is_official_lap=False)
        self.records[label]=dict(rows=rows,commands=commands,checkpoint=self.checkpoint(self.state),crossings=gates.hits)
        atomic_write(D / (label+'-result-private.json'),dict(summary=summary,**self.records[label]))
        self.results.append(summary)
        assert digest(self.checkpoint(self.prefix)) == self.prefix_hash
        if label=='zero':
            assert safe, 'ZERO_POSITIVE_ENDPOINT_NOT_SAFE'
            self.checks['zero_all_rows_choices_and_checkpoint_exact597'] = True
            # Saved597 endpoint comparison without new dynamics or original margin queries.
            old_g = Crossing(self)
            for i in range(96, self.state['global_raw'], 4):
                old_hold=self.tape['rows'][i:i+4]
                for row in old_hold: old_g.add(row)
                old_g.finish_hold(old_hold)
            assert digest(old_g.hits) == digest(gates.hits), 'ZERO_S400_PLANE_BASELINE_MISMATCH'
            self.checks['zero_saved597_worldplanes_exact'] = True
        return summary
    def replay(self, best):
        self.capacity(REPLAY); t=self.times()
        if t['CPU_s']+90+30>=5400 or t['wall_s']+120+45>=6600: raise BudgetStop('REPLAY_TIME_RESERVE')
        self.label='replay'; self.state=self.initial(); assert digest(self.checkpoint(self.state))==digest(self.checkpoint(self.initial_state))
        expected=self.prefix_rows+self.records[best['label']]['rows']
        commands={h:self.fixed[h] for h in range(1,25)}
        commands.update({q['index']:np.asarray(q['action'],np.float32) for q in self.records[best['label']]['commands']})
        gates=Crossing(self); rows=[]
        atomic_write(D/'REPLAY_STARTED-private.json',dict(label=best['label'],expected_rows=len(expected),requests=REPLAY))
        for j in range(0,len(expected),4):
            h=expected[j]['index']; self.next_hold=h; self.reserve(False,False); self.begin_context()
            try:
                hold=[]
                for old in expected[j:j+4]:
                    row,why=self.raw(commands[h],h,old['raw']); assert why is None
                    assert digest(row)==digest(old),'INDEPENDENT_COMMAND_REPLAY_ROW_MISMATCH'
                    rows.append(row);hold.append(row);gates.add(row)
                gates.finish_hold(hold)
            finally: self.end_context();self.flush('replay',h)
        assert digest(self.checkpoint(self.state))==digest(self.records[best['label']]['checkpoint'])
        assert digest(gates.hits)==digest(self.records[best['label']]['crossings'])
        self.replay_result=dict(label=best['label'],exact=True,raw=len(rows),all_rows_checkpoint_planes_exact=True)
        atomic_write(D/'independent-replay-private.json',dict(summary=self.replay_result,rows=rows,checkpoint=self.checkpoint(self.state),crossings=gates.hits))
    def prepare(self):
        c597=json.loads((G/'retry/cold597_contract.json').read_text())
        c603=json.loads((G/'retry/scalar603_contract.json').read_text())
        r603=json.loads((G/'retry/scalar603_result.json').read_text())
        for p,h in c597['implementation_sha256'].items(): assert base.sha(G/p)==h,('597_SOURCE',p)
        for p,h in c603['source_sha256'].items(): assert base.sha(G/p)==h,('603_SOURCE',p)
        for p,h in c603['compiler_runtime_sha256'].items(): assert base.sha(Path(p))==h,('603_RUNTIME',p)
        binary=Path(c603['command'][-1]); assert base.sha(binary)==r603['binary_sha256']
        spec=importlib.util.spec_from_file_location('_scalar603',binary)
        self.extension=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.extension)
        env=self.extension.environment();assert env.pop('original_math_hypot') is math.hypot
        assert env['FLT_EVAL_METHOD']==0 and env['rounding_mode']==env['FE_TONEAREST']
        for k,p in [('static',base.old.INPUTS['static']),('paths',base.old.INPUTS['candidate_paths']),('ledger',base.old.INPUTS['ledger'])]:
            assert base.sha(p)==c597['input_sha256'][k]
        saved=Path('/workspace/haic-response597-private/final-independent-tape-private.json')
        choices=Path('/workspace/haic-response597-private/choices-private.json')
        r597=json.loads((G/'retry/cold597_result.json').read_text())
        assert base.sha(saved)==r597['private_sha256'][saved.name] and base.sha(choices)==r597['private_sha256'][choices.name]
        self.tape=json.loads(saved.read_text());self.old_choices={q['hold']:q for q in json.loads(choices.read_text())}
        old577=json.loads(base.old.INPUTS['tape'].read_text())
        assert base.sha(base.old.INPUTS['tape'])==c597['input_sha256']['tape']
        self.fixed={q['index']:np.asarray(q['action'],np.float32) for q in old577['commands'] if q['index']<=39}
        assert sorted(self.fixed)==list(range(1,40))
        assert subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
        assert not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
        def forbidden(*a,**kw): raise AssertionError('604_NATIVE_WORLD_RESET_ACTION_FORBIDDEN')
        base.old.CarRacing.__init__=base.old.CarRacing.reset=base.old.CarRacing.step=forbidden
        base.old.Car.__init__=base.old.Car.step=forbidden
        import retry.plan512_control as kernel
        assert kernel.MAX_MODEL_TICKS==200000
        files=['retry/residual604.py','retry/residual604_math.py','retry/reuse601.py','retry/segments602.py',
               'retry/scalar603.c','retry/timing600.py','retry/profile601.py','retry/cold598_support.py']
        self.contract=dict(study=604,status='FROZEN_BEFORE_TESTS_OR_SOURCE',
            registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=base.DEADLINE.isoformat(),
            source_sha256={p:base.sha(G/p) for p in files},source597_contract_sha256=base.sha(G/'retry/cold597_contract.json'),
            source603_contract_sha256=base.sha(G/'retry/scalar603_contract.json'),binary_sha256=base.sha(binary),
            input_sha256=dict(static=base.sha(base.old.INPUTS['static']),paths=base.sha(base.old.INPUTS['candidate_paths']),
                ledger=base.sha(base.old.INPUTS['ledger']),source597_tape=base.sha(saved),source597_choices=base.sha(choices),
                fixed577=base.sha(base.old.INPUTS['tape'])),
            caps=CAPS,time_caps=dict(CPU_s=5400,wall_s=6600,cleanup_CPU_s=30,cleanup_wall_s=45),
            replay_reserve=REPLAY,replay_time_reserve=dict(CPU_s=90,wall_s=120),hold_time_reserve=dict(CPU_s=60,wall_s=75),
            hold_cost_reserve=dict(feedback_model=1540,feedback_geometry=6200,fixed_model=4,fixed_geometry=40),
            kernel_hardcap=200000,stronger_global_choose_cap=180000,
            family=residual.family(),knots=residual.KNOTS,
            residual_spec='Offset(current actual old551 progress) piecewise cubic smoothstep80/100/130/160/190/220,ends0,amplitude.20. Pedal two C1 smoothstep bumps80..140peak110 and140..220peak180,amplitude.025. Shift virtualPPtarget along left normal atlookahead station. Delta=shifted-targetPPfloat32 minus original-targetPPfloat32 on SAME state,addedtoincumbent. Saturate steering tofloat32(.4),netpedal[-1,1],castfloat32/exclusivegasbrake. Zero coefficients/outside80..220 short-circuit exactbytes; zero individual residual preserves corresponding original bytes.',
            incumbent='Exact577fixedcommands1..39;40+unchanged537replansonACTUALcandidate root/progress/running history withalloriginal trials and freshFINAL. No action if incumbent returnsnone. FreshFINAL certifies original incumbent action with its backup witness,NOTmodified action/fullresidualfuture.',
            protocol='NEW SOURCE-ONLY DIRECT APPLIED VALIDATION. Afteroriginalincumbentselection, residual-modifiedcommandsappliedWITHOUTfutureadmissioncertificate. Strictactual preforce1.059/clip.10 andpostfootprint.50/path3/reference4.85/body<100/projection[-.5,max(5,2COMstep)]/finitefullstate eachraw. Launch1..24unchangedforce2.5/clip.15by24 andnoreferenceveto. Control float32 domain unchanged. No native authorization or retroactive pass of old failures.',
            start='Oneoriginalsourceinitial->raw96 strictreconstruction,allrows/fullcheckpoint against597includingvisited/tracker/clock/launch/tracking exact. Clone fullstate independently nineways; no actual598root. Zero first mustexactmatch597rawrowsandall537choices/reportstothefixeds400plane endpoint,otherwisewhole stop.',
            endpoint='Frozenold551s200/300/400 worldplanes fromsame590leftsegment endpoint rule. FirstELIGIBLEforwardCOMchordcross (a<0<=b,postprogress within10m,patherror<=3) withENTIREcrossingholdsafe.200/300diagnosticsonly,no preparatory pruning. OriginalTimeLimit50+raw<=1224only hard horizon;missingendpoint atthatlimit is censored,notfamilynegative;unexpectedwholefinish stops beforeanycontinuation. Stopatfirsts400wholehold,neverwholelapresearch.',
            gain='ComparecontinuouslinearCOMchordcross time withzero;record20msbefore/afterrawbracket/fraction/ULP. Anystrictpositivegain,NO100/500msgate. Selectbestevaluatedstrictsafes400 byearliesttime,fixedfamilyorderontie. AtmostONEindependentfrozencommandreplayfromoriginalinitial,fullrawrows/checkpoint/worldplanesexact;nocontrollerevaluationinreplay. Ifcostcensoredremaining candidatesor replaymarkedcensored,nocapexpansion.',
            helper='Reusepinned603binary ONLYsegment/SAT/min,originalmath.hypot,601memo+602preparedcontext. FreshmemoPERHOLDcoverschooserandapplied4raw,geometryonlykey,immutablevalue/context. EVERYmemoMISSfullcompiledmargincomparedbitwisewithoriginalPythonroad+obstaclemargin;originalcomparisonisEXTRAchargedgeometrybeforecall. Firstmismatchwholetechnicalstop. Alllogicalmargin/projectionand3worldplanepacksandresidualproject/targetpackscharged;physicsbody/hull/contactinternalsincludedmodeltickpack.',
            reservation_derivation='32cert*(49margin+48postprojection+44internalprojection)+6=4518;plus32*49originalmargincomparisons=1568;plus24appliedgeometry/planes+2residualpacks+2initialmargin=6114<6200. Feedback1536forecast+4appliedraw=1540. Replay1174*6+64<7200. Beforeeachholdreservefullhold+entirereplay+cleanup;forecast/rejected/FINAL/prefix/applied/replayallglobalcharged.',
            errors='Ordinaryappliedstrictfailure,incumbentNO_SAFE,orfinitebodydomain>=100 stopTHATcandidateandcontinuefixednext;zero/prefixfailurestopsALL. Nonfinite,identity,numeric helper mismatch,unexpectedIO/technical=>ALLstop,noreplay. Budget/deadline=>current/unstartedcostcensored,attemptonlyreservedconditionalbestreplayifitstillfits. No retry/alteredamplitude/othercandidate.',
            recording='Durablecompleteinputandreservebeforeeachappliedforce/tick;forecastinputdurablebeforehold,primitiveforecasttelemetrydeferredtoexclusiveperholdfilesasin603. No model/evaluatorvalueshidden;allwheelreturnsandmodelrootskeptprivateperhold. Currentcheckpointfsyncedafterhold. prior10CPU/wallprepchargeincluded.',
            scope=dict(native=0,worlds=0,resets=0,actions=0,new_seed=0,HOLDOUT=0,SEALED=0,carry=0,FD=0,solver=0),
            research_remaining=22211,reserve=84000,reserve_used=0,
            parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip())
        atomic_write(G/'retry/residual604_contract.json',self.contract)
        atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=base.sha(G/'retry/residual604_contract.json'),source=0))
        tests=residual.pure_checks();memo_tests,_=reuse.pure_checks();tests['clone_memo_checks']=memo_tests
        atomic_write(G/'retry/residual604_tests.json',tests)
        self.add('geometry',3);self.planes=planes(self.paths['candidate'])
        atomic_write(D/'fixed-planes-private.json',self.planes)
        self.install_meters();compiled_geometry.distance=self.extension.distance
    def run(self):
        status='PREPARATION';error=None;cost_censored=False;best=None
        def stop_timer(*a):raise BudgetStop('SIGNAL_TIME_CAP')
        signal.signal(signal.SIGPROF,stop_timer);signal.signal(signal.SIGALRM,stop_timer)
        signal.setitimer(signal.ITIMER_PROF,max(.01,5370-self.times()['CPU_s']))
        signal.setitimer(signal.ITIMER_REAL,max(.01,6555-self.times()['wall_s']))
        try:
            self.prepare();self.prefix96()
            for label,coeff in residual.family():
                try: self.evaluate(label,coeff)
                except BudgetStop:
                    if label=='zero':raise
                    cost_censored=True;break
            zero=self.results[0];assert zero['label']=='zero' and zero['safe_s400']
            base_time=zero['crossings']['400']['time_s']
            for q in self.results:
                hit=q['crossings'].get('400');q['s400_gain_s']=base_time-hit['time_s'] if q['safe_s400'] else None
                if hit:
                    q['time_resolution']=dict(raw_step_s=.02,before_raw=hit['before_raw'],after_raw=hit['after_raw'],
                        fraction=hit['fraction'],interpolation_ULP_s=math.ulp(hit['time_s']),
                        gain_below32ULP=(abs(q['s400_gain_s'])<=32*max(math.ulp(base_time),math.ulp(hit['time_s']))) if q['s400_gain_s'] is not None else None)
            eligible=[q for q in self.results[1:] if q['safe_s400'] and q['s400_gain_s']>0]
            best=min(eligible,key=lambda q:q['crossings']['400']['time_s']) if eligible else None
            if best:
                try:self.replay(best)
                except BudgetStop:cost_censored=True;self.replay_result=dict(label=best['label'],exact=False,status='COST_CENSORED_NO_RETRY')
            status='SAFE_EARLIER_S400_EXACT_REPLAY' if self.replay_result and self.replay_result.get('exact') else 'SOURCE_FEASIBILITY_COMPLETE_NO_POSITIVE_VERIFIED_GAIN'
            if cost_censored:status+='__COST_CENSORED'
        except BudgetStop as exc:
            cost_censored=True;status='BUDGET_CENSORED';error=type(exc).__name__+':'+str(exc)
        except BaseException as exc:
            status='TECHNICAL_OR_POSITIVE_CONTROL_STOP';error=type(exc).__name__+':'+str(exc)
            atomic_write(D/'error-private.json',dict(error=error,traceback=traceback.format_exc(),label=self.label))
        finally:
            self.end_context();self.restore();compiled_geometry.distance=self.original_distance
            compiled_geometry.full.road_margin=self.orig_geometry_margin
            atomic_write(D/'final-checkpoint-private.json',self.checkpoint(self.state) if self.state else None)
            if self.journal.rows:atomic_write(D/'remaining-telemetry-private.json',dict(events=prior.materialize(self.journal.rows),wheel_results=prior.materialize(self.raw_kernels)))
            self.applied_journal.append('STUDY_END',status=status,error=error,counts=dict(self.counts),time=self.times())
            self.applied_journal.close()
            completed={q['label'] for q in self.results}
            result=dict(study=604,status=status,error=error,checks=self.checks,candidates=self.results,
                uncompleted=[dict(label=n,status='COST_CENSORED' if cost_censored else 'NOT_EXECUTED_AFTER_GLOBAL_STOP') for n,_ in residual.family() if n not in completed],
                best_evaluated_label=best['label'] if best else None,replay=self.replay_result,
                cost=dict(self.counts),time=self.times(),kernel_hardcap=200000,model_counter=self.model[0],
                native=0,worlds=0,resets=0,actions=0,new_seed=0,HOLDOUT=0,SEALED=0,carry=0,
                research_remaining=22211,reserve=84000,reserve_used=0,native_incumbent_s=13.22,
                whole_lap_claim=False,native_admission=False,general_promotion=False,
                contract_sha256=base.sha(G/'retry/residual604_contract.json') if (G/'retry/residual604_contract.json').exists() else None,
                private_sha256={p.name:base.sha(p) for p in D.glob('*.json*')})
            atomic_write(G/'retry/residual604_result.json',result)
            atomic_write(D/'CLOSED-private.json',dict(time=self.times(),result_sha256=base.sha(G/'retry/residual604_result.json'),cost=dict(self.counts)))
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            print(json.dumps(result,indent=2))


if __name__=='__main__':Study().run()
