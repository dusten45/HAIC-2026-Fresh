"""483 byte limits only; unchanged frozen481 lossless codec and readers."""
from retry.io481 import (
    Quota as _Quota481, read, load_receipt, canonical, CODEC_KEY, STATE_KEY,
)
from retry.pilot420_backend import TechnicalStop

class Quota(_Quota481):
    STATES_MAX = 250
    NONSTATE_MODEL_MAX = 58556416

    def __init__(self, d, model_cap, extra_cap, decision_cap=16*1024**2):
        if model_cap>201085448 or extra_cap>16*1024**2 or decision_cap>16*1024**2:
            raise TechnicalStop('483_approved_byte_caps')
        super().__init__(d, model_cap, extra_cap, decision_cap)
