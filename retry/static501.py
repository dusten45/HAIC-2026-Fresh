"""Pure binding/caller/capture fixtures for original417 screening."""
import ast,copy,hashlib,json,math,types
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import numpy as np
from dataclasses import asdict
from retry.codegate498 import verify_function,verify_exec,negative_fixtures
from retry.preflight498 import compiled_reference,reference_functions

def check(v,s):
    if not v:raise RuntimeError('501_STATIC:'+s)

def binding_gate(runtime):
    ctl=runtime.import_module('terminal410_run');paired=runtime.import_module('paired417_common')
    cross=runtime.import_module('cross404_common');probe=runtime.import_module('probe390_run');factorial=runtime.import_module('factorial401_run')
    original=runtime.import_module('executor397');signed=runtime.import_module('signed417_executor')
    anchors={'Controller.__init__':dict(control_code=probe.control_code,G=cross.G,scope_for=cross.scope_for,executor=cross.executor),
      'Controller.act':dict(SimpleNamespace=types.SimpleNamespace,np=np,copy=copy,sensor=factorial.sensor,ExecutorDomainError=original.ExecutorDomainError),
      'Controller.memory':{},'Controller.phase':{},'SourceC.__init__':dict(Controller=ctl.Controller,policy=paired.policy)}
    refs=reference_functions(runtime);proof=[]
    for name,ref in refs.items():
        owner=paired.SourceC if name.startswith('SourceC') else ctl.Controller
        proof.append(verify_function(getattr(owner,name.split('.')[1]),ref,globals_expected=anchors[name],closure_expected={'__class__':paired.SourceC} if name.startswith('SourceC') else None,label=name))
    for actual,mod,qual,expected in [(probe.control_code,'probe390_run','control_code',dict(ast=ast,Path=Path,hashlib=hashlib)),(cross.scope_for,'cross404_common','scope_for',dict(np=np)),(cross.executor,'cross404_common','executor',dict(np=np,CoherentExecutor=original.CoherentExecutor)),(factorial.sensor,'factorial401_run','sensor',dict(math=math)),(paired.policy,'paired417_common','policy',dict(np=np,CoherentExecutor=signed.CoherentExecutor))]:
        ref=types.FunctionType(compiled_reference(mod,qual),{},qual)
        proof.append(verify_function(actual,ref,globals_expected=expected,label=qual))
    return dict(passed=True,proofs=proof,negative_fixtures=negative_fixtures())


def fake_model(state):
    NS=types.SimpleNamespace;h=state['physical']['hull']
    return NS(car=NS(hull=NS(position=h['position'],linearVelocity=h['velocity'],angle=h['angle'],angularVelocity=h['angular_velocity']),wheels=[NS(joint=NS(angle=w['joint']['angle']),tiles=w['tiles']) for w in state['physical']['wheels']]),t=state['physical']['actual_time'],finish_line_tracker=NS(**state['finish_tracker']))


def control_gate(runtime,fixed,pace,root,before,expected,nodes):
    from retry import envelope500
    c=runtime.import_module('paired417_common').SourceC(fixed,pace,copy.deepcopy(before))
    originalcode,_=runtime.import_module('probe390_run').control_code(Path(__file__).parent/'pace269_run.py')
    proof=verify_exec(c.code,originalcode,globals_dict={'np':np},scope=c.scope,np_expected=np,scope_expected={**runtime.import_module('cross404_common').scope_for(None,fixed,pace),'index':before['index'],'laststeer':before['laststeer']},label='501_frozen_nominal')
    m=fake_model(root);a=c.act(m)
    check(a.tolist()==expected['nominal'] and c.memory()==expected['nominal_memory_after'],'FIRST_COPIED_NOMINAL_MEMORY')
    d=runtime.import_module('paired417_common').SourceC(fixed,pace,copy.deepcopy(before));d.policy.nodes=np.asarray(nodes).copy();d.policy.nodes.setflags(write=False)
    b=d.act(m);after=copy.deepcopy(d.memory());q=runtime.import_module('signed417_executor').canonical_projection(fixed['line'],list(m.car.hull.position),list(m.car.hull.linearVelocity),d.phase());arcs=np.r_[0.,np.cumsum(fixed['free_profile']['ds'])].tolist()
    z=envelope500.act(b.tolist(),d.phase(),q['arc'],math.hypot(*m.car.hull.linearVelocity),q['sigma'],arcs,nodes)
    check(z['action'][0]==float(b[0]) and d.memory()==after,'PURE_CANDIDATE_NO_EXTRA_MEMORY')
    return dict(passed=True,source_nominal=proof,copied_current_nominal_memory_exact=True,candidate_pure_scalar=True,physics=0)


def capture_lifecycle(runtime,folder,binding):
    # The production full495 fake-world fixture runs with in-memory synthetic
    # refs only. This exercises real capture callbacks, not a real simulator.
    import retry.capture494 as cap494, retry.capture495 as cap495, retry.schema493 as schema, retry.test_capture495 as fixture
    class Memory:
        def __init__(self):self.files={};self.data={}
        def __call__(self,name,value):
            raw=cap494.encoded(value);check(Path(name).name==name and len(raw)<=1024**2,'FAKE_WRITER_CAP')
            path='/virtual501/'+name;check(path not in self.files,'FAKE_IMMUTABLE');self.files[path]=len(raw);self.data[path]=raw
            return dict(path=path,sha256=hashlib.sha256(raw).hexdigest(),pointer='')
        def read(self,ref):
            raw=self.data[ref['path']];check(hashlib.sha256(raw).hexdigest()==ref['sha256'],'FAKE_REF_AUTH')
            value=json.loads(raw)
            for token in ref['pointer'].split('/')[1:]:
                token=token.replace('~1','/').replace('~0','~');value=value[int(token)] if isinstance(value,list) else value[token]
            return value
    memory=Memory();olddefaults=dict(schema.adapt_hold.__kwdefaults__)
    with ExitStack() as stack:
        for module in (cap494,cap495,fixture):stack.enter_context(patch.object(module,'read_ref',memory.read))
        schema.adapt_hold.__kwdefaults__={**olddefaults,'reference_reader':memory.read}
        try:result=fixture.run(runtime,folder,binding,writer=memory)
        finally:schema.adapt_hold.__kwdefaults__=olddefaults
    result.pop('private_fixtures495',None);result['physical_fixture_files']=0;result['synthetic_refs_in_memory_only']=True
    return result


def own_saved_gate(runtime,mods,root_ledger,fixed,validator,private_root):
    """One genuine saved473 model hold checks new own-chain validator only.

    Snapshot reader and capture-count dependency are explicit fake-only stubs;
    the original stored physical/memory/ledger/post values are unmodified.
    """
    load=mods['receipt421_io'].load_receipt
    folder=private_root/'stage473';label='OriginalReference_held_first'
    p=load(folder/(label+'-private.json'));o=load(folder/(label+'-observer-private.json'))
    number=o['link']['world_number'];before=load(folder/f'world{number}-before-first-step-private.json')['model_root']
    row=p['rows'][0];ledger=mods['planner419_model_ledger'].ForecastLedger(**p['model_ledger'])
    initial=mods['planner419_model_ledger'].ForecastLedger.fork(root_ledger)
    t=dict(index=1,state_before=before,memory_before=row['memory_before'],ledger_before=asdict(initial),state_after=p['final_state'],memory_after=p['controller_memory'],ledger_after=p['model_ledger'],row_digest=mods['io481'].canonical(row))
    NS=types.SimpleNamespace
    fake=NS(rows=[row],stream=NS(actions=o['actions'],posts=o['posts']),capture_holds495=[None],L=sum(fixed['free_profile']['ds']),fixed=fixed,m=object(),ctrl=NS(memory=lambda:copy.deepcopy(p['controller_memory'])),ledger=ledger)
    fakebackend=NS(**vars(mods['pilot420_backend']));fakebackend.snapshot=lambda _:copy.deepcopy(p['final_state'])
    altered=dict(mods,pilot420_backend=fakebackend);r=dict(state=before,before=row['memory_before'],ledger=root_ledger)
    proof=validator(fake,r,[t],altered)
    bad=copy.deepcopy(t);bad['ledger_after']['last_clock_tick']+=1
    try:validator(fake,r,[bad],altered)
    except Exception:pass
    else:raise AssertionError('501_OWN_LEDGER_TAMPER_ACCEPTED')
    return dict(passed=True,saved_hold=label,own=proof,ledger_tamper_rejected=True,snapshot_reader_explicit_saved_stub=True,direct_capture_count_stub_only=True,new_direct_capture_authentication_claimed=False,physics=0)
