"""Observed native448 wrapper-end roots; hashes bind recoverable global RNG."""
import copy,hashlib,pickle,random
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.planner419 import GoalLedger
from retry.terminal410_model import from_actual_full
from retry.receipt421_io import load_receipt
from retry.loss389_analyze import read
from retry.ledger439 import require


def validate_native449(full,last,ledger,original,python_numpy_blob):
    require(type(ledger) is GoalLedger and not ledger.done and not ledger.deadline_missed,'449_NATIVE_LEDGER_TYPE_OR_STOPPED')
    require(full['controller']==last['nominal_memory_after'],'449_NATIVE_MEMORY_NOT_LAST')
    require(round(full['physical']['actual_time']*50)==ledger.last_clock_tick and full['physical']['actual_time']==last['post']['time'],'449_NATIVE_CLOCK_NOT_LAST')
    require(ledger.progress_m==last['progress_after'],'449_NATIVE_PROGRESS_NOT_LAST')
    require(full['wrapper']['finish_time_s'] is None and not last['completed'] and not last['safety'],'449_NATIVE_UNSAFE_OR_FINISHED')
    py,numpy=pickle.loads(python_numpy_blob)
    require(hashlib.sha256(pickle.dumps(py,protocol=5)).hexdigest()==full['RNG']['python_sha256'],'449_PYTHON_RNG_NOT_NATIVE')
    require(hashlib.sha256(pickle.dumps(numpy,protocol=5)).hexdigest()==full['RNG']['numpy_sha256'],'449_NUMPY_RNG_NOT_NATIVE')
    ticks=ledger.last_clock_tick-original['last_clock_tick']
    require(type(ticks) is int and ticks>0,'449_NATIVE_PREFIX_CLOCK')
    return ticks


def load_root449(root,arm):
    require(arm in ['nominal','fullgas'],'449_ARM')
    d=root/'stage448';folder=d/('actual_'+arm);result=read(folder/'result.json')
    require(result['status']=='NATIVE_EXIT60_VERIFIED','449_NATIVE_ARM_NOT_QUALIFIED')
    rows=[__import__('json').loads(s) for s in (folder/'trace-private.jsonl').read_text().splitlines()]
    step=len(rows);require(step==result['native_actions'],'449_NATIVE_ROW_COVERAGE')
    packet=load_receipt(folder/(arm+'_step'+str(step)+'-after-native-private.json'))
    fact=load_receipt(folder/(arm+'_step'+str(step)+'-actual-fact-private.json'))
    full=read(folder/'final-private.json')
    require(full==packet['full_post'],'449_FINAL_NOT_OWN_NATIVE_POST')
    require(result['actual_ledger']==fact['fact']['actual_ledger'],'449_NATIVE_LEDGER_NOT_OWN_FACT')
    ledger=GoalLedger(**result['actual_ledger'])
    original=load_receipt(folder/'448-native-authorization-private.json')['actual_root_ledger']
    payload=load_receipt(d/(arm+'_current'+str(step-22)+'_copy1_inputs-before-integration-private.json'))
    blob=payload['global_RNG_pickle'];require(hashlib.sha256(blob).hexdigest()==payload['RNG_digest'],'449_INPUT_RNG_BLOB_DIGEST')
    prefix_ticks=validate_native449(full,rows[-1],ledger,original,blob)
    require(prefix_ticks==4*(step-22),'449_NATIVE_WHOLE_WRAPPER_DELTA')
    if arm=='nominal':
        factual=load_receipt(root/'stage442/actual_C0/C0_step43-before-native-private.json')['full_pre_before_nominal']
        require(full==factual,'449_BASELINE_NOT_FACTUAL442_PRE43')
    return dict(full=full,state=from_actual_full(full),memory=copy.deepcopy(full['controller']),ledger=ledger,original=original,native_prefix_ticks=prefix_ticks,RNG_blob=blob,source_native_step=step)


def restore_root_rng449(data):
    # This reconstructs the saved state, never selects or seeds a new condition.
    py,numpy=pickle.loads(data['RNG_blob']);random.setstate(py);np.random.set_state(numpy)
    require(hashlib.sha256(pickle.dumps(random.getstate(),protocol=5)).hexdigest()==data['full']['RNG']['python_sha256'],'449_RESTORED_PYTHON_RNG')
    require(hashlib.sha256(pickle.dumps(np.random.get_state(),protocol=5)).hexdigest()==data['full']['RNG']['numpy_sha256'],'449_RESTORED_NUMPY_RNG')
