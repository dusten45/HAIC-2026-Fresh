"""495 opt-in full model lifecycle, selected/own/history capture gates."""
import copy
from pathlib import Path
from retry.runtime492 import Graph,canonical_projection,CoherentExecutor491,ExecutorDomainError
from retry.capture495 import Registry495,install_model495,authenticate_hold495,compare_repeat495,compare_flags495
from retry.capture494 import check,encoded

def install(runtime,meter,quota,packing):
    registry=Registry495();registry.install(runtime);runtime.capture_registry495=registry
    def writer_factory(child):
        def writer(name,value):
            check(Path(name).name==name,'495_sidecar_name')
            path=meter.d/('direct495-'+name)
            # The central codec/quota reserves actual serialized bytes and the
            # live file count before publishing any new immutable sidecar.
            packing.codec.save_receipt(path,value)
            from retry.schema493 import source_ref
            return source_ref(path,'')
        return writer
    lifecycle=install_model495(runtime,registry,writer_factory,runtime.binding)
    backend=runtime.import_module('pilot420_backend');base=runtime.import_module('online481');online=runtime.import_module('online485')
    closed_caps={};native_fail=backend.TechnicalStop
    def fail(v,reason):
        if not v:raise native_fail('495_'+reason)
    def holds(child):
        values=getattr(child,'capture_holds495',[])
        fail(len(values)==len(child.rows),'CAPTURE_ROW_COVERAGE')
        for h,row in zip(values,child.rows):
            authenticate_hold495(h,runtime.binding)
            report=compare_flags495(h,h,runtime.binding)
            fail(report['safe'] or bool(row['safety']),'DIRECT_SAFETY_NOT_IN_LEGACY_ROW')
        return values
    def extra(label):
        for stream in meter.streams.values():
            child=stream.child
            if child is not None and child.label==label:return dict(direct_holds495=copy.deepcopy(holds(child)))
        raise native_fail('495_DUMP_OWNER_NOT_LIVE:'+label)
    packing.owner_extra=extra
    original_closed=base.closed
    def closed(child):
        values=copy.deepcopy(holds(child));result=original_closed(child)
        closed_caps[result[0]]=values
        return result
    base.closed=closed
    original_select=online.select
    def select(child,ctx,binding,first_expected=None):
        result,summary=original_select(child,ctx,binding,first_expected)
        if result is not None:
            first=summary['options'][summary['selected']]['first_path'];repeat=result['auth']['repeat_path']
            fail(first in closed_caps and repeat in closed_caps,'SELECTED_CAPTURE_REFERENCES')
            a=closed_caps[first];b=closed_caps[repeat];fail(len(a)==len(b)==1,'SELECTED_REPEAT_HOLD_COUNT')
            compare_repeat495(a[0],b[0],runtime.binding)
            result['direct_hold495']=copy.deepcopy(a[0])
        return result,summary
    online.select=select
    original_own=base.own
    def own(child,ctx,selected):
        result=original_own(child,ctx,selected)
        current=holds(child)[-1]
        flags=compare_flags495(selected['direct_hold495'],current,runtime.binding)
        fail(flags['passed'] and flags['safe'],'OWN_DIRECT_FLAGS_OR_RETURN_DAMAGE')
        # Original full physical fidelity, source join and current-memory tests
        # already ran in original_own. Cold exactness is never imposed on warm
        # parent physiology; all direct discrete fields remain exact here.
        result[1]['direct_capture495']=flags
        return result
    base.own=own
    original_history=online.history
    def history(child,memory=None):
        holds(child)
        return original_history(child,memory)
    online.history=history
    return dict(registry=registry,lifecycle=lifecycle,closed_captures=closed_caps,all_model_paths_share_full_one=True,selected_independent_capture_exact=True,own_direct_flags_and_return_damage=True,history_capture_coverage=True)
