"""Model query value view; immutable actual root is binding, never capability."""
import copy
from dataclasses import asdict, dataclass
from retry.receipt421_io import receipt_digest
from retry.planner419 import GoalLedger
from retry.planner419_model_ledger import ForecastLedger
from retry.pilot420_backend import capture_context, model_ledger_view, snapshot, fingerprint, rnghash


class QueryChannelError(ValueError):
    pass


def require(value, why):
    if not value:
        raise QueryChannelError(why)


@dataclass(frozen=True)
class ModelQuery445:
    owner: object
    actual_owner: object
    actual_digest: str
    state: dict
    before: dict
    context: object
    context_digest: str
    parent_ledger: dict
    after_memory_digest: str
    global_rng_digest: str
    native_ticks: int
    actual_execution_allowed: bool = False
    actual_DONE_allowed: bool = False

    def validate(self, parent, actual):
        require(parent is self.owner and actual is self.actual_owner, 'wrong_query_owner')
        require(type(parent.ledger) is ForecastLedger and type(actual) is GoalLedger, 'wrong_ledger_channel')
        require(not self.actual_execution_allowed and not self.actual_DONE_allowed, 'model_has_no_native_authority')
        require(actual.digest()==self.actual_digest and parent.ledger.actual_root_digest==self.actual_digest, 'actual_root_changed')
        require(not actual.done and not parent.ledger.done and not parent.ledger.deadline_missed, 'stopped_or_done_model')
        require(asdict(parent.ledger)==self.parent_ledger and parent.m.native_ticks==self.native_ticks, 'stale_or_mutated_ledger')
        require(fingerprint(snapshot(parent.m))==fingerprint(self.state), 'stale_or_mutated_state')
        require(fingerprint(parent.ctrl.memory())==self.after_memory_digest, 'parent_memory_changed')
        require(rnghash()==self.global_rng_digest, 'parent_global_RNG_changed')
        require(type(self.context.ledger) is GoalLedger and self.context.ledger==model_ledger_view(parent.ledger), 'forged_query_value_view')
        require(receipt_digest(asdict(self.context))==self.context_digest, 'forged_context')
        require(self.context.parent.raw_clock_tick==parent.ledger.last_clock_tick==round(parent.m.t*50), 'query_clock_mismatch')
        self.context.validate()
        return self

    def spawn(self, experiment, parent, actual, label, recipe):
        self.validate(parent, actual)
        # Exact production path through new()->GuardianChild()->Child()->fork.
        child = experiment.new(self.state, self.before, self.context.ledger,
                               label, recipe, guardian=True)
        self.validate(parent, actual)
        return child

    def commit_actual_done(self, *_):
        raise QueryChannelError('model_cannot_commit_actual_DONE')


def bind_model_query(parent, actual, before, nominal, fixed, policy_digest):
    require(type(parent.ledger) is ForecastLedger and type(actual) is GoalLedger, 'wrong_ledger_channel')
    require(parent.ledger.actual_root_digest==actual.digest(), 'other_actual_root')
    require(not parent.ledger.done and not actual.done, 'query_after_model_or_actual_done')
    context = capture_context(parent.m, parent.ctrl, before, nominal, parent.ledger,
                              fixed, policy_digest, {}, actual.digest())
    result = ModelQuery445(parent, actual, actual.digest(), copy.deepcopy(snapshot(parent.m)),
                           copy.deepcopy(before), context, receipt_digest(asdict(context)),
                           asdict(parent.ledger), fingerprint(parent.ctrl.memory()),
                           rnghash(), parent.m.native_ticks)
    return result.validate(parent, actual)
