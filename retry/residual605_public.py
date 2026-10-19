"""Publish technical aggregates; retain as-executed full failure report privately."""
import copy,hashlib,json,os
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response605-private')
def sha(data):return hashlib.sha256(data).hexdigest()
def projection(value,original_sha):
    result=copy.deepcopy(value)
    removed=0
    for candidate in result['candidates']:
        failure=candidate.get('failure')
        if failure and 'report' in failure:
            report=failure.pop('report');removed+=1
            failure['incumbent_report_private']=True
            failure['incumbent_mode']=report.get('mode')
            failure['finite_trial_count']=len(report.get('trials',[]))
    result['publication']=dict(as_executed_result_private=True,as_executed_sha256=original_sha,
                               removed_full_incumbent_reports=removed,scientific_values_changed=False)
    return result
def main():
    public=G/'retry/residual605_result.json';data=public.read_bytes()
    closed=json.loads((D/'CLOSED-private.json').read_text());assert sha(data)==closed['result_sha256']
    private=D/'as-executed-result-private.json'
    with private.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    private.chmod(0o600)
    value=projection(json.loads(data),sha(data))
    out=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    tmp=public.with_suffix('.public.tmp')
    with tmp.open('xb') as f:f.write(out);f.flush();os.fsync(f.fileno())
    tmp.replace(public)
    assert sha(private.read_bytes())==closed['result_sha256']
    print(json.dumps(value['publication'],indent=2))
if __name__=='__main__':main()
