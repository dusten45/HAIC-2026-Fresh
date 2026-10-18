"""Full-phase gate uses official millisecond clock, before any539full outcome."""
import argparse,hashlib,json
from pathlib import Path
from retry.profile539_model import Stage,G,D

class FullStage(Stage):
 def full(self,kind):
  result=super().full(kind)
  if result['case']['pass_safety']:
   base=json.loads((G/f'retry/transfer538_{kind}_result.json').read_text())['case']['model_finish_episode_s'];candidate=result['case']['model_finish_episode_s'];ms=round(base*1000)-round(candidate*1000);result.update(gain_vs538_ms=ms,passed=ms>=500,effect_gate_unit='official_milliseconds')
  return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('cold','carry'),required=True);a=p.parse_args();m=json.loads((G/'retry/profile539_clock_registration.json').read_text());assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==m['active_full_source_sha256'];FullStage(a.phase).run()
