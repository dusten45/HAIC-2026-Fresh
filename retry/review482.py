"""One saved-only reconciliation of the independent equal/zero-M80 review."""
import time
START=time.perf_counter()
import hashlib,json,sys
from pathlib import Path
from retry.render482 import classify_ties
G=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(root):
    d=root/'stage482/review-correction';record=d/'after-private.json';assert not record.exists()
    p=G/'retry/diagnostic482_findings.json';old=d/p.name
    assert sha(p)==sha(old)
    private=root/'stage482/analysis1/timeseries-private.json';data=json.loads(private.read_text());findings=json.loads(p.read_text());assert findings['source_private_sha256']==sha(private)
    summary=json.loads((G/'retry/diagnostic482_summary.json').read_text());ties=[x for x in summary['minM80_margin_tradeoffs_over1mm'] if x['M80_advantage']==0]
    zero,positive=classify_ties(data['series'],ties)
    assert len(zero)==20 and [x['action'] for x in positive]==[6,7,66] and len(ties)==23
    findings['exact_equal_M80_tie_margin_tradeoffs_over1mm']=len(ties)
    findings['exact_zero_M80_tie_margin_tradeoffs_over1mm']=len(zero)
    findings['exact_positive_M80_ties']=positive
    findings['source_renderer_sha256']=sha(G/'retry/render482.py')
    findings['review_correction']=dict(original_findings_sha256=sha(old),original_renderer_sha256=sha(d/'render482.py'),correction_script_sha256=sha(__file__),reason='Exact equal-M80 ties comprise20 zero and3 positive; M80_advantage==0 did not imply selected_M80==0. No risk/geometry/timeseries/plot changed.')
    p.write_text(json.dumps(findings,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    x=dict(source_code_sha256=sha(__file__),CPU_s=time.process_time(),wall_s=time.perf_counter()-START,zero_ties=zero,positive_ties=positive,final_findings_sha256=sha(p),new_physics=0,new_worlds=0,original_four_files_preserved=True)
    with record.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
    print(json.dumps(dict(equal_ties=len(ties),zero=len(zero),positive=positive,new_physics=0,CPU_s=x['CPU_s'],wall_s=x['wall_s'])))
if __name__=='__main__':run(Path(sys.argv[1]))
