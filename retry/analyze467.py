"""Read-only evidence verification and future466 cost accounting; no simulation."""
import hashlib
import json
from pathlib import Path
import shutil

G=Path(__file__).resolve().parents[1]
R=Path('/workspace/haic-private-retry-20261009')
D=R/'stage467'
T=Path('/tmp/haic-retry-stage467-private')

def save_new(path,value):
    with path.open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def main():
    result=json.loads((D/'result-private.json').read_text())
    manifest={}
    for path in sorted(T.rglob('*')):
        if path.is_file():
            relative=path.relative_to(T)
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if hashlib.sha256((D/'retained-synthetic'/relative).read_bytes()).hexdigest()!=digest:
                raise RuntimeError('retained_copy_hash_mismatch')
            manifest[str(relative)]=digest
    save_new(D/'retention-verification-private.json',dict(files=len(manifest),sha256=manifest))
    old=json.loads((G/'retry/design466_next.json').read_text())
    rate=old['storage']['observed_max_bytes_per_tick']
    header=old['storage']['fixed_header_bytes']
    # Hard world count64, not planned41: both ceilings must be retained.
    logical=2048*rate*1.25+64*header+16*1024**2+2*1024**2
    physical=logical*1.01+64*16*1024
    required_tmp=physical+512*1024**2
    required_workspace=physical*1.1+32*1024**2+512*1024**2+2*1024**2
    free={p:shutil.disk_usage(p).free for p in ['/tmp','/workspace']}
    future={'stage':'FUTURE466_COST_ONLY_NO_EXECUTION','planned_ticks':1458,'planned_worlds':41,
      'source_ticks':1242,'source_worlds':35,'cohort_ticks':216,'cohort_worlds':6,
      'hard_ticks':2048,'hard_worlds':64,'CPU_s':180,'wall_s':300,'actual_actions':0,'resets':0,
      'fixed_source':'same pre126 from463; common first fullgas; Original point-FF versus immutable Projected4 point-FF',
      'source_gate':'fresh source/restore/current/pending qualification plus new IO binding source manifest; no inherited pass',
      'cohort_gate':'each arm independent H13 twice plus held first transition; C.act once with prepared memory',
      'promotion':'strict positive common original-reference root+60m time bracket AND positive progress at1.04s AND all safety/fidelity gates',
      'stop':'unsupported IO/schema/resource/fidelity stops are technical stops; own lowered-target error alone never promotion',
      'logical_payload_forecast_bytes':logical,'gzip_forecast_bytes':physical,
      'forecast_basis':{'observed_max_bytes_per_tick':rate,'margin':1.25,'header_per_world':header,
        'world_count_for_storage':64,'metadata_bytes':16*1024**2,'plan_bytes':2*1024**2,
        'gzip_multiplier':1.01,'descriptor_and_partial_allowance_per_world':16*1024,
        'gzip_multiplier_is_planning_allowance_not_universal_bound':True,
        'requires_measured_manifest_growth_and_file_count_before_execution':True},
      'required_tmp_including_reserve_bytes':required_tmp,
      'required_workspace_including_reserve_retention_bytes':required_workspace,
      'free_at_analysis':free,'tmp_space_gate':free['/tmp']>=required_tmp,
      'workspace_space_gate':free['/workspace']>=required_workspace,
      'current_adapter_logical_cap_bytes':32*1024**2,'current_adapter_physical_cap_bytes':64*1024**2,
      'current_adapter_cap_gate':False,'production_connection_gate':False,
      'remaining':['declare separate larger immutable IO caps before any future execution',
        'connect real meter433/observer435/closure readers explicitly; present constructor proof is synthetic metadata',
        'version mutable budget/progress as immutable revisions; preserve every prior record',
        'fresh semantic source hashes and mandatory actual-file readbacks at every boundary',
        'fresh storage preflight with hard64 worlds, full replication and measured source growth'],
      'execution_authorized_by_this_file':False,'goal_11_seconds_unchanged':True}
    save_new(G/'retry/future467_cost.json',future)
    result['retained_files_verified']=len(manifest)
    result['scope_note']='main-body timer excludes Python/stdlib startup; process high-water RSS includes imports. No physics/native benchmark.'
    save_new(G/'retry/evidence467_result.json',result)
    save_new(G/'retry/evidence467_gate.json',dict(stage=467,passed=True,tests=11,
      new_physics_native_world_reset=0,retained_files_verified=len(manifest),protected_hashes_verified=18,
      IO_only=True,production_physics_connection_certified=False,future466_execution=False))
    rows=[]
    for case in result['benchmark']:
        reads=case['additional_full_readbacks']
        rows.append(f"| {case['case']} | {case['logical_bytes']:,} | {case['stored_bytes']:,} | {case['stored_over_logical']*100:.3f}% | {case['write_including_full_readback_wall_s']:.3f} | {min(x['wall_s'] for x in reads):.3f}–{max(x['wall_s'] for x in reads):.3f} |")
    text='''# 467 — 새 gzip 증거 IO 검증 완료, physics0

기존 JSON codec의 모든 field와 bytes marker, receipt 논리 JSON bytes를 유지하는 새 전용-root IO를 구현했다. 실물 gzip SHA·압축해제 논리 SHA·기존 canonical receipt digest를 구분한다. gzip footer 종료와 fsync 후 실제 파일을 재개방하여 CRC·길이·JSON/schema·세 digest를 검증하고 descriptor를 no-replace 발행한다. 성공 반환 전 발행된 descriptor와 실물을 다시 읽는다. descriptor와 root marker는 명시적인 control metadata이며 payload는 첫 출력부터 gzip이다. 기존 자료를 변환하지 않았다.

명시적 IO 주입 synthetic fixture에서 source→constructor proof→runtime link→H13/pending seal→continuation closure와 read-only reopen·restore·JSONL factual reader를 연결했다. 기존434 completion 의미 검증은 AST 동등성을 확인했다. constructor proof는 합성 metadata이며 실제 물리 world 복원 인증이 아니다. live meter433/observer435를 연결하거나 미래466을 실행하지 않았다. actual/DONE/promotion 권한은 false다.

통합·오류 주입11개 통과. 모든 byte값과 nested field, CRC·logical/stored/receipt hash·descriptor schema, 부분쓰기·중복·reserve·fsync·publish 실패, 손상 시 pending/started 비전진을 확인했다. 실패 partial/orphan은 유지하고, 성공한 이번 호출의 임시 hardlink만 정리한다. 기존 파일·백업·main·Participants·보호18파일·v475 예산은 유지했다.

| synthetic | logical bytes | gzip bytes | 원문 대비 | write+전수readback wall초 | 추가 전수read 3회 wall초 범위 |
|---|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

worker main부 CPU{result['CPU_s']:.3f}초/wall{result['wall_s']:.3f}초, process 최대RSS{result['peak_RSS_KiB']/1024:.2f}MiB. main timer는 Python/stdlib 시작을 포함하지 않는다. 실물 최종 증거{result['retained_tmp_file_bytes']:,}B와 동일 복사본을 보존하고 {len(manifest)}개 파일 hash를 전수 확인했다. disk 순간 peak는 별도 샘플링하지 않았으며 최종 보존량을 peak로 주장하지 않는다. 출력cap·CPU600/wall900·양 volume512MiB reserve 안에서 끝났다. 모델/native/world/reset·HOLDOUT·SEALED·유료 사용0.

3종과 warm read각3회 결과다. 실제 모델 증거의 압축률·cold read·파일수가 늘어난 manifest/fsync 비용을 보장하지 않는다. mixed의 작은 JSON token 반복은 write wall1.85초로 느렸으며 guard/serialization 비용도 포함한다. json_ready와 parse 객체는 메모리에 남으므로 observer posts/actions RAM 감소를 주장하지 않는다. JSONL은 명시한 새 formatting이며 과거 JSONL bytes를 변환하는 API가 아니다.

미래466 비용은1458ticks/41worlds 계획, hard2048/64·CPU180/wall300·actual/reset0이다. 공간은 계획41 대신 hard64 world header를 적용했다. gzip 이득을 보장하지 않는1.01배 allowance와 descriptor/partial 여유를 넣으면 tmp 요구{required_tmp:,.0f}B, workspace 전수복사·여유 포함{required_workspace:,.0f}B다. 현재 workspace{free['/workspace']:,}B이므로 **workspace gate 미통과**다. 467 자체32MiB/64MiB cap도 미래작업에 부족하다. 압축된 복사본에 압축률을 두 번 곱하지 않았다. [미래 비용/필수 게이트](future467_cost.json)를 만족하기 전 실행하지 않는다. 11초대 목표와 공통 first-fullgas 비교, 원래reference의+60m strict 시간·1.04초 진행 동시 승격 기준을 유지한다.

잘못된 Oct16 종료 응답을 정정했다. 현재 계약에는 실제 연장 근거 메시지와 시각, 최신 종료2026-10-20 19:01:55 KST를 함께 비공개 보존했다. 과거 최초 task prompt를 최신 철회로 해석하지 않는다. 이 작업에서 추가 실행 권한은 발행하지 않았다.
'''
    with (G/'retry/evidence467_result.md').open('x') as f:f.write(text)
    print(json.dumps(dict(retained_files=len(manifest),future_tmp_required=required_tmp,
        future_workspace_required=required_workspace,workspace_gate=future['workspace_space_gate'])))

if __name__=='__main__':main()
