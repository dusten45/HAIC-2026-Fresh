# 467 — 새 gzip 증거 IO 검증 완료, physics0

최종 검증은 **12개 통과**다. 초기11개 통과 후 상위 source·constructor도 seal/begin/closure 시 재읽도록 보강하고, ancestor 손상 차단을 포함한12개 전체를 다시 통과했다. 최종 보존211파일 hash 일치·보호18파일 및 v475 예산 불변을 확인했다. 최초 측정·증거·복사본은 보존했다. 두 worker main부 합계 CPU7.370초/wall6.596초, 최대RSS96.77MiB다. [최종 상태](evidence467_final.json)를 기준으로 한다.

기존 JSON codec의 모든 field와 bytes marker, receipt 논리 JSON bytes를 유지하는 새 전용-root IO를 구현했다. 실물 gzip SHA·압축해제 논리 SHA·기존 canonical receipt digest를 구분한다. gzip footer 종료와 fsync 후 실제 파일을 재개방하여 CRC·길이·JSON/schema·세 digest를 검증하고 descriptor를 no-replace 발행한다. 성공 반환 전 발행된 descriptor와 실물을 다시 읽는다. descriptor와 root marker는 명시적인 control metadata이며 payload는 첫 출력부터 gzip이다. 기존 자료를 변환하지 않았다.

명시적 IO 주입 synthetic fixture에서 source→constructor proof→runtime link→H13/pending seal→continuation closure와 read-only reopen·restore·JSONL factual reader를 연결했다. 기존434 completion 의미 검증은 AST 동등성을 확인했다. constructor proof는 합성 metadata이며 실제 물리 world 복원 인증이 아니다. live meter433/observer435를 연결하거나 미래466을 실행하지 않았다. actual/DONE/promotion 권한은 false다.

통합·오류 주입11개 통과. 모든 byte값과 nested field, CRC·logical/stored/receipt hash·descriptor schema, 부분쓰기·중복·reserve·fsync·publish 실패, 손상 시 pending/started 비전진을 확인했다. 실패 partial/orphan은 유지하고, 성공한 이번 호출의 임시 hardlink만 정리한다. 기존 파일·백업·main·Participants·보호18파일·v475 예산은 유지했다.

| synthetic | logical bytes | gzip bytes | 원문 대비 | write+전수readback wall초 | 추가 전수read 3회 wall초 범위 |
|---|---:|---:|---:|---:|---:|
| repeated | 2,181,977 | 10,799 | 0.495% | 0.129 | 0.023–0.030 |
| mixed | 1,674,269 | 746,993 | 44.616% | 1.846 | 0.024–0.032 |
| entropy | 1,866,861 | 1,445,194 | 77.413% | 0.177 | 0.034–0.035 |

worker main부 CPU4.881초/wall4.478초, process 최대RSS96.77MiB. main timer는 Python/stdlib 시작을 포함하지 않는다. 실물 최종 증거2,302,968B와 동일 복사본을 보존하고 102개 파일 hash를 전수 확인했다. disk 순간 peak는 별도 샘플링하지 않았으며 최종 보존량을 peak로 주장하지 않는다. 출력cap·CPU600/wall900·양 volume512MiB reserve 안에서 끝났다. 모델/native/world/reset·HOLDOUT·SEALED·유료 사용0.

3종과 warm read각3회 결과다. 실제 모델 증거의 압축률·cold read·파일수가 늘어난 manifest/fsync 비용을 보장하지 않는다. mixed의 작은 JSON token 반복은 write wall1.85초로 느렸으며 guard/serialization 비용도 포함한다. json_ready와 parse 객체는 메모리에 남으므로 observer posts/actions RAM 감소를 주장하지 않는다. JSONL은 명시한 새 formatting이며 과거 JSONL bytes를 변환하는 API가 아니다.

[CPU 산식 점검](future467_cpu_screen.json)에서 같은 bytes당 비용을 미래 logical payload에 단순 적용하면 write+전수readback17.8–334.9 CPU초 범위다. 실제 예측은 아니며 physics·파일수 증가 비용도 제외했다. 따라서 미래 whole-worker180초 통과는 인증하지 않았다. 작은 JSON token마다 guard가 파일 목록을 검사하는 비용도 다음 생산 연결의 검토 대상이다.

미래466 비용은1458ticks/41worlds 계획, hard2048/64·CPU180/wall300·actual/reset0이다. 공간은 계획41 대신 hard64 world header를 적용했다. gzip 이득을 보장하지 않는1.01배 allowance와 descriptor/partial 여유를 넣으면 tmp 요구844,366,712B, workspace 전수복사·여유 포함910,767,876B다. 현재 workspace900,399,104B이므로 **workspace gate 미통과**다. 467 자체32MiB/64MiB cap도 미래작업에 부족하다. 압축된 복사본에 압축률을 두 번 곱하지 않았다. [미래 비용/필수 게이트](future467_cost.json)를 만족하기 전 실행하지 않는다. 11초대 목표와 공통 first-fullgas 비교, 원래reference의+60m strict 시간·1.04초 진행 동시 승격 기준을 유지한다.

잘못된 Oct16 종료 응답을 정정했다. 현재 계약에는 실제 연장 근거 메시지와 시각, 최신 종료2026-10-20 19:01:55 KST를 함께 비공개 보존했다. 과거 최초 task prompt를 최신 철회로 해석하지 않는다. 이 작업에서 추가 실행 권한은 발행하지 않았다.
