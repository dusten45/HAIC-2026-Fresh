"""Strict, pure code/binding gate; ignores marshal allocation/location artifacts.

No research imports, file IO, model, geometry, seed, or physical entry points.
The parent supplies independently compiled frozen references and live expected
binding objects. Verification executes neither the candidate nor its reference.
"""
import builtins
import dis
import hashlib
import json
import math
import struct
import types


class CodeGate498Error(ValueError):pass
def require(value,reason):
    if not value:raise CodeGate498Error('498_CODE_GATE:'+reason)
def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _value(value):
    """Typed constants/defaults; bool/int, signed zero and bytes stay distinct."""
    kind=type(value)
    if value is None:return ['none']
    if value is Ellipsis:return ['ellipsis']
    if kind is bool:return ['bool',value]
    if kind is int:return ['int',str(value)]
    if kind is float:
        require(math.isfinite(value),'nonfinite_constant')
        return ['float64',struct.pack('>d',value).hex()]
    if kind is complex:
        return ['complex',_value(value.real),_value(value.imag)]
    if kind is str:return ['str',value]
    if kind is bytes:return ['bytes',value.hex()]
    if kind is types.CodeType:return ['code',code_signature(value)]
    if kind in (tuple,list):return [kind.__name__,[_value(v) for v in value]]
    if kind is frozenset:
        values=[_value(v) for v in value]
        return ['frozenset',sorted(values,key=lambda v:json.dumps(v,sort_keys=True))]
    if kind is dict:
        pairs=[[_value(k),_value(v)] for k,v in value.items()]
        return ['dict',sorted(pairs,key=lambda v:json.dumps(v[0],sort_keys=True))]
    raise CodeGate498Error('498_CODE_GATE:unsupported_constant:'+kind.__name__)


def code_signature(code):
    require(type(code) is types.CodeType,'code_type')
    # co_code is the public, de-specialized bytecode, not the private adaptive
    # interpreter cache. Exception targets/stack effects ARE executable meaning.
    return dict(bytecode=code.co_code.hex(),exceptiontable=getattr(code,'co_exceptiontable',b'').hex(),
        argcount=code.co_argcount,posonlyargcount=code.co_posonlyargcount,
        kwonlyargcount=code.co_kwonlyargcount,nlocals=code.co_nlocals,
        stacksize=code.co_stacksize,flags=code.co_flags,
        names=list(code.co_names),varnames=list(code.co_varnames),
        freevars=list(code.co_freevars),cellvars=list(code.co_cellvars),
        constants=[_value(v) for v in code.co_consts])


def verify_code(actual,reference,*,label='code'):
    left=code_signature(actual);right=code_signature(reference)
    require(left==right,label+':semantic_code_mismatch')
    return dict(passed=True,label=label,semantic_code_sha256=fingerprint(left),
                filename_line_allocation_identity_ignored=True,exceptiontable_checked=True,
                nested_constants_checked=True)


def _global_names(code):
    names=set()
    for instruction in dis.get_instructions(code):
        if instruction.opname in ('LOAD_GLOBAL','STORE_GLOBAL','DELETE_GLOBAL'):
            names.add(instruction.argval)
    for constant in code.co_consts:
        if type(constant) is types.CodeType:names.update(_global_names(constant))
    return names


def _builtins(namespace):
    value=namespace.get('__builtins__',builtins)
    require(type(value) in (dict,types.ModuleType),'builtins_namespace_type')
    return vars(value) if type(value) is types.ModuleType else value


def _lookup_global(namespace,name):
    if name in namespace:return namespace[name]
    fallback=_builtins(namespace)
    require(name in fallback,'unbound_global:'+name)
    return fallback[name]


def _token(value):
    if isinstance(value,types.ModuleType):return dict(kind='module',name=value.__name__)
    if isinstance(value,types.FunctionType):
        return dict(kind='function',module=value.__module__,qualname=value.__qualname__,code=fingerprint(code_signature(value.__code__)))
    if isinstance(value,type):return dict(kind='class',module=value.__module__,qualname=value.__qualname__)
    if isinstance(value,(types.BuiltinFunctionType,types.BuiltinMethodType)):
        return dict(kind='builtin',module=getattr(value,'__module__',None),qualname=getattr(value,'__qualname__',value.__name__))
    try:return dict(kind='value',typed=_value(value))
    except CodeGate498Error:
        return dict(kind='object_identity_verified',type_module=type(value).__module__,type_name=type(value).__qualname__)


def verify_function(actual,reference,*,globals_expected,closure_expected=None,label='function'):
    """Compare code/defaults and authenticate ACTUAL globals/closure identities.

    Reference closures need only the same free-variable shape. In particular an
    independently compiled reference SourceC has a different __class__ cell;
    pass closure_expected={'__class__': actual_cloned_SourceC} explicitly.
    Nonbuiltin global names require explicit expected live objects. Builtins
    default to the standard builtin object and cannot be silently shadowed.
    """
    require(type(actual) is types.FunctionType and type(reference) is types.FunctionType,label+':function_type')
    require(type(globals_expected) is dict,label+':globals_mapping')
    proof=verify_code(actual.__code__,reference.__code__,label=label)
    require(_value(actual.__defaults__)==_value(reference.__defaults__),label+':defaults_mismatch')
    require(_value(actual.__kwdefaults__)==_value(reference.__kwdefaults__),label+':kwdefaults_mismatch')
    names=actual.__code__.co_freevars
    if closure_expected is None:
        require(not names,label+':closure_expected_required');closure_expected={}
    require(type(closure_expected) is dict and set(closure_expected)==set(names),label+':closure_keys')
    cells=actual.__closure__ or ()
    require(len(cells)==len(names),label+':closure_shape')
    closures={}
    for name,cell in zip(names,cells):
        try:value=cell.cell_contents
        except ValueError as exc:raise CodeGate498Error('498_CODE_GATE:'+label+':empty_closure:'+name) from exc
        require(value is closure_expected[name],label+':closure_identity:'+name)
        closures[name]=_token(value)
    globals_proof={}
    for name in sorted(_global_names(actual.__code__)|set(globals_expected)):
        if name in globals_expected:expected=globals_expected[name]
        else:
            require(name in vars(builtins),label+':expected_global_missing:'+name)
            expected=vars(builtins)[name]
        require(_lookup_global(actual.__globals__,name) is expected,label+':global_identity:'+name)
        globals_proof[name]=_token(expected)
    proof.update(defaults=_value(actual.__defaults__),kwdefaults=_value(actual.__kwdefaults__),
                 closure_bindings=closures,global_bindings=globals_proof,actual_binding_identities_checked=True)
    proof['function_fingerprint']=fingerprint(proof)
    return proof


def _scope_value(actual,expected,np_expected,label):
    if isinstance(expected,np_expected.ndarray):
        require(isinstance(actual,np_expected.ndarray),label+':array_type')
        require(actual.dtype.kind in 'biufc' and np_expected.isfinite(actual).all() and np_expected.isfinite(expected).all(),label+':array_numeric_finite')
        require(actual.dtype==expected.dtype and actual.shape==expected.shape and actual.tobytes()==expected.tobytes(),label+':array_bytes')
        return dict(kind='ndarray',dtype=actual.dtype.str,shape=list(actual.shape),
                    sha256=hashlib.sha256(actual.tobytes()).hexdigest())
    if isinstance(expected,np_expected.generic):
        require(type(actual) is type(expected) and actual.dtype==expected.dtype and actual.tobytes()==expected.tobytes(),label+':numpy_scalar_value')
        require(actual.dtype.kind in 'biufc' and bool(np_expected.isfinite(actual)),label+':numpy_scalar_finite')
        return dict(kind='numpy_scalar',dtype=actual.dtype.str,bytes=actual.tobytes().hex())
    try:left=_value(actual);right=_value(expected)
    except CodeGate498Error:
        require(actual is expected,label+':object_identity')
        return _token(expected)
    require(left==right,label+':typed_value')
    return dict(kind='value',typed=left)


def _external_names(code):
    """Conservative module LOAD_NAME inputs before a preceding assignment.

    The frozen controller's ordinary sequential module extraction is supported;
    a name read in a branch before a later STORE is conservatively required.
    """
    assigned=set();external=set()
    for instruction in dis.get_instructions(code):
        if instruction.opname=='LOAD_NAME' and instruction.argval not in assigned:external.add(instruction.argval)
        elif instruction.opname=='STORE_NAME':assigned.add(instruction.argval)
        elif instruction.opname=='DELETE_NAME':assigned.discard(instruction.argval)
    return external|_global_names(code)


def verify_exec(actual_code,reference_code,*,globals_dict,scope,np_expected,scope_expected,label='controller_exec'):
    """Check extracted module code and real exec(np globals, controller scope).

    scope_expected must cover all nonbuiltin external inputs except np. Array
    dtype/shape/bytes and scalar typed values are exact; env/model owners can be
    provided as explicit expected live object identities. No exec is performed.
    """
    require(type(globals_dict) is dict and type(scope) is dict and type(scope_expected) is dict,label+':namespace_types')
    proof=verify_code(actual_code,reference_code,label=label)
    required=_external_names(actual_code);scopes={};global_tokens={}
    for name in sorted(required|set(scope_expected)):
        if name=='np':
            value=scope[name] if name in scope else _lookup_global(globals_dict,name)
            require(value is np_expected,label+':np_identity');global_tokens[name]=_token(np_expected)
        elif name in scope_expected:
            require(name in scope,label+':missing_scope:'+name)
            scopes[name]=_scope_value(scope[name],scope_expected[name],np_expected,label+':scope:'+name)
        elif name in vars(builtins):
            value=scope[name] if name in scope else _lookup_global(globals_dict,name)
            require(value is vars(builtins)[name],label+':builtin_shadow:'+name)
            global_tokens[name]=_token(value)
        else:raise CodeGate498Error('498_CODE_GATE:'+label+':unverified_scope_input:'+name)
    proof.update(scope_bindings=scopes,global_bindings=global_tokens,all_external_inputs_bound=True)
    proof['exec_fingerprint']=fingerprint(proof)
    return proof


def negative_fixtures():
    """Pure synthetic checks only; caller runs within registered static poison."""
    tests=[]
    def reject(name,fn,reason=None):
        try:fn()
        except CodeGate498Error as exc:
            if reason is not None:require(reason in str(exc),'fixture_wrong_rejection:'+name+':'+str(exc))
            tests.append(name);return
        raise AssertionError('498_NEGATIVE_ACCEPTED:'+name)
    scope={'HELPER':len}
    exec(compile('def f(x=1, *, y=2):\n return HELPER(x)+y\n','synthetic498-A','exec'),scope)
    reference=scope['f']
    other={};exec(compile('def f(x=1, *, y=2):\n return HELPER(x)+y\n','different-location498','exec'),other)
    valid=types.FunctionType(other['f'].__code__,scope,'f',reference.__defaults__)
    valid.__kwdefaults__=dict(reference.__kwdefaults__)
    verify_function(valid,reference,globals_expected={'HELPER':len})
    tests.append('independent_compile_location_ignored_semantics_equal')
    wrong=types.FunctionType(valid.__code__,{'HELPER':sum},'f',(1,));wrong.__kwdefaults__={'y':2}
    reject('global_identity_replacement',lambda:verify_function(wrong,reference,globals_expected={'HELPER':len}),':global_identity:HELPER')
    wrong=types.FunctionType(valid.__code__,scope,'f',(True,));wrong.__kwdefaults__={'y':2}
    reject('bool_default_not_integer',lambda:verify_function(wrong,reference,globals_expected={'HELPER':len}))
    wrong=types.FunctionType(valid.__code__,scope,'f',(1,));wrong.__kwdefaults__={'y':3}
    reject('kwdefault_replacement',lambda:verify_function(wrong,reference,globals_expected={'HELPER':len}))
    changed=compile('def f(x=1, *, y=2):\n return HELPER(x)-y\n','synthetic498-change','exec')
    replacement=next(v for v in changed.co_consts if type(v) is types.CodeType)
    reject('opcode_change',lambda:verify_code(replacement,reference.__code__))
    reject('constant_change',lambda:verify_code(compile('a=2','x','exec'),compile('a=1','x','exec')))
    reject('nested_code_change',lambda:verify_code(compile('def f(): return 2','x','exec'),compile('def f(): return 1','x','exec')))
    reject('signedzero_constant',lambda:verify_code(compile('a=-0.0','x','exec'),compile('a=0.0','x','exec')))
    reject('freevar_layout_change',lambda:verify_code(reference.__code__.replace(co_freevars=('rogue',)),reference.__code__))
    if hasattr(reference.__code__,'co_exceptiontable'):
        guarded=compile('try:\n x=1\nexcept Exception:\n x=2\n','guarded498','exec')
        reject('exceptiontable_change',lambda:verify_code(guarded.replace(co_exceptiontable=b''),guarded))
    def make_cell(value):
        def closed():return value
        return closed.__closure__[0]
    def outer(value):
        def closed():return value
        return closed
    marker=object();closed=outer(marker)
    verify_function(closed,outer(object()),globals_expected={},closure_expected={'value':marker})
    reject('closure_object_swap',lambda:verify_function(types.FunctionType(closed.__code__,{},'closed',None,(make_cell(object()),)),closed,globals_expected={},closure_expected={'value':marker}))
    reject('closure_mapping_omitted',lambda:verify_function(closed,closed,globals_expected={}))
    # __class__ cells from independently compiled class definitions are expected
    # to differ. Actual cell identity must still bind the supplied actual class.
    a={};b={};text='class C:\n def m(self): return __class__\n'
    exec(compile(text,'actual-class','exec'),a);exec(compile(text,'reference-class','exec'),b)
    verify_function(a['C'].m,b['C'].m,globals_expected={},closure_expected={'__class__':a['C']})
    reject('class_cell_wrong_owner',lambda:verify_function(a['C'].m,b['C'].m,globals_expected={},closure_expected={'__class__':b['C']}))
    tests.append('independent_reference_class_cell_allowed_actual_owner_verified')
    import numpy as np
    executable=compile('y=np.asarray(x)+gain\nz=max(y)\n','exec498','exec')
    array=np.asarray([1.,-0.],dtype='<f8');scope_inputs=dict(x=array,gain=np.float64(.25))
    verify_exec(executable,executable,globals_dict={'np':np},scope=dict(scope_inputs),np_expected=np,scope_expected=dict(scope_inputs))
    reject('exec_numpy_global_replaced',lambda:verify_exec(executable,executable,globals_dict={'np':object()},scope=dict(scope_inputs),np_expected=np,scope_expected=scope_inputs),':np_identity')
    reject('exec_numpy_local_shadow',lambda:verify_exec(executable,executable,globals_dict={'np':np},scope={**scope_inputs,'np':object()},np_expected=np,scope_expected=scope_inputs),':np_identity')
    reject('exec_builtin_local_shadow',lambda:verify_exec(executable,executable,globals_dict={'np':np},scope={**scope_inputs,'max':min},np_expected=np,scope_expected=scope_inputs),':builtin_shadow:max')
    reject('exec_unbound_required_scope',lambda:verify_exec(executable,executable,globals_dict={'np':np},scope=dict(scope_inputs),np_expected=np,scope_expected={'x':array}),':unverified_scope_input:gain')
    changed=array.copy();changed[1]=0.
    reject('exec_array_signedzero_bytes_changed',lambda:verify_exec(executable,executable,globals_dict={'np':np},scope={**scope_inputs,'x':changed},np_expected=np,scope_expected=scope_inputs),':array_bytes')
    reject('exec_array_dtype_changed',lambda:verify_exec(executable,executable,globals_dict={'np':np},scope={**scope_inputs,'x':array.astype('<f4')},np_expected=np,scope_expected=scope_inputs),':array_bytes')
    reject('exec_numpy_scalar_changed',lambda:verify_exec(executable,executable,globals_dict={'np':np},scope={**scope_inputs,'gain':np.float64(.5)},np_expected=np,scope_expected=scope_inputs),':numpy_scalar_value')
    tests.append('exec_inputs_arrays_numpy_scalars_builtins_verified_without_exec')
    return dict(passed=True,tests=tests,count=len(tests),synthetic_only=True,
                candidate_reference_functions_executed=False,new_world_reset_step_seed=0)
