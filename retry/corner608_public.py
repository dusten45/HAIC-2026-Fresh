"""Preserve exact execution output privately; publish aggregate gate metrics."""
import hashlib
import json
from pathlib import Path

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response608-private')


def main():
    source = G / 'retry/corner608_result.json'
    original = D / 'as-executed-result-private.json'
    if original.exists():
        raise RuntimeError('608_PUBLICATION_ALREADY_DONE')
    original.write_bytes(source.read_bytes())
    original.chmod(0o600)
    result = json.loads(original.read_text())
    allowed = {'before_raw', 'after_raw', 'fraction', 'time_s', 'hold',
               'eligible', 'whole_hold_safe'}
    result['crossings'] = {k: {a: b for a, b in v.items() if a in allowed}
                           for k, v in result['crossings'].items()}
    result['publication'] = dict(private_state_history_and_reports_excluded=True,
        as_executed_private_sha256=hashlib.sha256(original.read_bytes()).hexdigest())
    source.write_text(json.dumps(result, indent=2) + '\n')
    (D / 'PUBLICATION-private.json').write_text(json.dumps(dict(
        original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
        public_sha256=hashlib.sha256(source.read_bytes()).hexdigest()), indent=2) + '\n')


if __name__ == '__main__':
    main()
