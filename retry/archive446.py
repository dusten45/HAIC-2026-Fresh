"""Archival H13 restoration only; no claim of original live-world continuity."""
import copy
import math
from dataclasses import asdict
from retry.pilot420_backend import Child as BaseChild,model_ledger_view
from retry.observer435 import ObserveMixin,Stream
from retry.planner419_model_ledger import ForecastLedger


class ArchiveGateError(ValueError):
    pass


def validate_archive(data, actual_root_digest):
    if type(data.get('model_ledger')) is not dict:
        raise ArchiveGateError('archival_model_ledger_mapping_required')
    ledger=ForecastLedger(**data['model_ledger'])
    if ledger.actual_root_digest!=actual_root_digest or ledger.done or ledger.deadline_missed:
        raise ArchiveGateError('archival_root_channel_or_stopped')
    if len(data['rows'])!=13 or sum(r['predicted']['raw_ticks'] for r in data['rows'])!=52:
        raise ArchiveGateError('archival_H13_coverage')
    if data['rows'][-1]['memory_after']!=data['controller_memory']:
        raise ArchiveGateError('archival_memory_not_last_observation')
    if data['rows'][-1]['model_progress']!=ledger.progress_m:
        raise ArchiveGateError('archival_ledger_not_last_observation')
    last=data['rows'][-1]
    if ledger.goal_m!=last['model_goal'] or ledger.age_actions!=last['model_age'] or ledger.done!=last['predicted']['finished']:
        raise ArchiveGateError('archival_goal_age_done_not_last_observation')
    if type(ledger.age_actions) is not int or type(ledger.last_clock_tick) is not int or not all(math.isfinite(v) for v in [ledger.progress_m,ledger.goal_m,ledger.actual_root_goal_m]):
        raise ArchiveGateError('archival_ledger_numeric_types')
    state=data['final_state']
    if ledger.last_clock_tick!=round(state['physical']['actual_time']*50) or state['finish_tracker']['finish_time_s'] is not None:
        raise ArchiveGateError('archival_clock_or_finish')
    if data['rows'][-1]['predicted']['time']!=state['physical']['actual_time']:
        raise ArchiveGateError('archival_end_time')
    return ledger


class ArchivalChild446(ObserveMixin,BaseChild):
    def __init__(self,*args,full_ledger,**kwargs):
        # Existing constructor takes only a current model VALUE view. Restore
        # the complete predicted history ledger before attaching its observer.
        BaseChild.__init__(self,*args,**kwargs)
        self.ledger=ForecastLedger(**copy.deepcopy(full_ledger))
        self.stream=Stream(self)
