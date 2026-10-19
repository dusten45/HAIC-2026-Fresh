"""Read-only initial checkpoint validation and registered 574 cost arithmetic."""
import json,time
from pathlib import Path
from types import SimpleNamespace
from retry.checkpoints574 import checkpoint_map,fd_ticks
from retry.clip561_core import atomic_write
from retry.path569_design import sha
import retry.handoff562_model as d
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response574-private')
def main():
    cpu,wall=time.process_time(),time.perf_counter();rd=d.rd;source=Path('/workspace/haic-response573-private/final-independent-tape-private.json');saved=rd(source);o=SimpleNamespace(static=rd(Path('/workspace/haic-response515-private/collected-map-state-private.json')),paths=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json')),ledger=rd(Path('/workspace/haic-response519-private/model-ledger-private.json')))
    def no_source(*a,**kw):raise RuntimeError('SOURCE_FORBIDDEN574_PREFLIGHT')
    d.source_tick=d.force_rows=no_source
    points,checks=checkpoint_map(o,saved['rows'],saved['checkpoint']);assert fd_ticks()==69696
    atomic_write(D/'initial-checkpoints-private.json',{str(h):d.Study.checkpoint(o,s) for h,s in points.items()})
    out=dict(passed=True,checks=checks,source_ticks=0,new_actions=0,per_center_FD_ticks=fd_ticks(),two_center_FD_ticks=2*fd_ticks(),total_registered_worst_ticks=148735,full_start_one_center_FD_ticks=138864,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,input_sha256={str(source):sha(source)},checkpoint_payload_sha256=sha(D/'initial-checkpoints-private.json'))
    atomic_write(G/'retry/wide574_design.json',out);print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
