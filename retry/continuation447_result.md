# 447 — 같은 live child로 H13 이후 +60m까지 관측

**모델의 원래 pre23 root부터 +60m까지 누적 시간 이득 [0.34, 0.38]초를 관측했다.** nominal은 [1.58,1.60]초, 첫 fullgas 한 번 뒤 own nominal은 [1.22,1.24]초다. H13에서 world를 복원하지 않고 같은 child/world/observer를 이어 실행했다. 실제 transfer·전체 lap·픽셀 정책 개선으로 승격하지 않았다.

## 선행 게이트와 실행 범위

동결한 원래444 before-constructor/current-input의 physical state·controller memory·actual root ledger·global RNG를 재사용했다. RNG는 보존된 상태를 복원했으며 새 조건 seed를 선택하지 않았다. branch별 독립2회와 별도 held 첫 전이1회를 유지했다. 새 실험은 이 두 branch뿐이며 H2 연장이나 실제/reset은 실행하지 않았다.

적분 전 정적 검사 **199개**와 저장 감사가 통과했다. baseline H13 두 사본은 원래444의 전체 rows·최종 physical snapshot·memory와 정확히 같았고, factual442/439의 기존 H13 source gate와 fresh-current 첫 전이 비교를 통과했다. 이 두 baseline gate와 held 검사가 끝난 뒤 candidate를 시작했다. 미래 예측 전체를 fresh-current 실제 검증으로 해석하지 않는다. candidate H13 역시 원래444와 정확히 같았다. 이후 H13 prefix digest·boundary key와 child/world/stream 객체 동일성을 매 행동 전후 검사했다. 모든 continuation은 own nominal이며 두 번째 fullgas pulse는 없다.

| branch | 원래 root 이후 행동/사본 | H13 이후 추가 행동/사본 | +60m raw tick bracket | 시간 bracket |
|---|---:|---:|---:|---:|
|nominal|20|7|79–80|1.58–1.60초|
|첫 fullgas 후 nominal|16|3|61–62|1.22–1.24초|

독립 사본의 모든 rows·최종 상태·memory가 정확히 같았고, held state/memory/RNG 보존 및 각 branch 자신의 첫 명령·body/wheel/clip·memory 비교가 통과했다. 새 native 권위나 DONE를 만들지 않았다. 추가13 cap 안에서 양쪽 모두 도달했고 안전·진행·기술 중단은 없었다. crossing은 50Hz 표본의 구간이며 보간한 공식 시간이 아니다.

## 기존446 복원 결과와의 차이

누적 crossing bracket은446과 같지만 **archival tail과 live tail의 rows 및 최종 상태는 정확히 다르다.** nominal 최종 상태44개 scalar, fullgas28개 scalar가 달랐으며 원시 차이 경로를 비공개 보존했다.

| 행동 종료 표본의 최대 절대 차이 | nominal | fullgas |
|---|---:|---:|
|위치 m|1.90735e-6|0|
|속력 m/s|9.46588e-6|5.08116e-6|
|yaw rad/s|1.63727e-6|2.68221e-7|
|clock 초|0|0|

해당 종료 표본의 collision/damage/contact/raw ticks/finish/terminated/truncated 이산 값은 같았다. 표의 최댓값은 행동 종료 표본에 한정되며 모든 내부 raw 상태의 상한이 아니다. 새 허용 오차를 만들어 정확 불일치를 통과로 바꾸지 않았다. solver warm-start가 원인이라고 단정하거나446 복원을 동등하다고 소급 인증하지 않는다.447의 직접 live 관측 자체가 이번 유한 구간의 증거이며 추가 실험·재시도는 하지 않았다.

+60m에서 fullgas의 더 높은 속력과 path/heading·yaw/slip 차이는 여전히 남는다. terminal debt 해소는 미판정이다. 경계 body 양끝·동일 lower preclip wheel phase의 집계는 [결과 JSON](continuation447_result.json)에 있으며 연속시간 보장 구간이 아니다. 이전+30m 이득이나446 이득,442 전체 lap1.32초와 가산하지 않는다.

## 비용과 다음 제안

새 비용은 H13 재실행208 + nominal tail56 + fullgas tail24 + held8 = **296 model ticks/6 worlds**, CPU **5.722초**, wall **5.745초**다. 이번에는 H13을 실제 새로 적분했으므로208 ticks를 청구했다. 과거316/88 ticks는 환급·재청구하지 않았다. 6 observer의 posts296과 reserved ticks296이 일치한다. planned424/6, hard512/8·CPU90초/wall150초·worker 순차1을 지켰다. 동시에 보존한 held world가 있어 live world 최대수는2다.

정적 CPU16.820초/wall16.895초와 저장 분석 비용은 별도다. 준비·보고·Git·일부 import를 포함한 프로젝트 전체 overhead는 완전 계측하지 않았다. 새 실제 행동/reset·학습·새 seed·HOLDOUT/SEALED·예비·별도 유료 자원은0이다. v467의 연구 잔여27,516·누적 실제1,320,548·예비84,000/사용0은 변하지 않았다.

다음 최소 질문은 같은 단발 pulse의 **native +60m transfer**다. 알려진 DEV 조건의 nominal/pulse 두 arm만, 각22-action prefix와 root 이후 최대26행동으로 실제96행동/reset2 상한을 제안한다. fresh current source·독립 모델 안전/반복 검사와 native 사실 우선 commit을 유지하며 최초 오류에서 전체 중단한다. 모델 계획 상한5624 ticks/hard6144·128 worlds 등은 [미실행 제안](next447_design.json)에 명시했다. 실제 SourceG1·안전 게이트와 원장·코드 동결은 다음 실행 전에 별도 확정해야 한다. 더 긴 모델만으로 actual transfer 불확실성은 해결되지 않으므로 이 안을 우선 제안하며, **실행·예약하지 않았다.**

재전달된 최초 요청의10월16일 종료를 현재 승인으로 잘못 읽은 이번 안내는 기존 명시적3일 연장 증거와 대조해 정정했다. 유효 종료는 **2026년10월20일19:01:55 KST**이며 자동 연장은 없다. 이 판단 정정 중 새 적분은 없었다. 기존 main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·기존 backup과 사용자 변경을 보존했고 private state/seed/명령/RNG는 공개하지 않았다.

[실행](continuation447.py) · [동일 객체 계약](live447.py) · [정적 fixture](test_live447.py) · [저장 분석](analyze447.py).
