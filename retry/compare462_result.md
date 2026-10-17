# 462 — 첫80ms secant-동등 명령의 단일 모델 비교

**두 모델 부모가 각각 자기 finish를 확인했고 Original−SecantOnce의 root 이후 완료 bracket 차이는[0.20,0.24]초였다.** actual/reset·새 seed·학습·HOLDOUT/SEALED·예비·추가 유료 자원0이다. 각 whole arm은 한 번이며 전체 실험 반복 성공을 주장하지 않는다. query의 독립2회와 전체 arm 반복은 다르다.

|arm|첫80ms|이후 실제로 선택된 guardian 명령|부모 행동|자기 모델 finish raw bracket|root 이후 모델 시간|
|---|---|---|---:|---:|---:|
|Original|원래 nominal|nominal50회|51|[199,200]|[3.98,4.00]초|
|SecantOnce|secant와exact같은 기존fullgas|nominal46·neutralbrake1회|48|[188,189]|[3.76,3.78]초|

저장458P pre126(+522.611849m)을 고정했고 관측 prefix 경과10.00초는 모델 tail과 분리한다. 표는 새 native lap가 아니다. root는 이미 본 DEV 자료의 구조 가설에서 선택했으며 blind 검증·다른 root/픽셀/실제 일반화가 아니다.

## 첫 변경과 후속 반응

[승인된461 계약](design461_next.md)의 첫80ms feedforward만 `[r(s+sigma*.08)-r(s)]/.08`로 바꾸고 feedback1.5·line/profile·pedal map·steering을 유지했다. 이 root에서 전체 float32 명령이 기존 fullgas recipe와 exact 같은지 저장/정적/실행 첫 current state에서 확인했다. 이후 secant는 호출하지 않고 두 arm 모두 기존 guardian를 썼다. 동일 feedback 정책이라도 자기 상태가 달라 후속 명령 sequence는 달라진다.

첫80ms 모델 속도 변화는 Original−7.744m/s, SecantOnce+2.477m/s였다. 처음13행동 끝의 초기 대비 속도 변화는−13.606/−10.691m/s, 자기 위치의 reference 대비 속도 오차는−17.018/+2.373m/s였다.13행동 말 위치는 서로 다르므로 이 오차를 같은 공간 성적으로 비교하지 않는다.

|공통 원래pre23 공간 경계|Original 모델 통과|SecantOnce 모델 통과|모델 시간 이득|
|---:|---:|---:|---:|
|+570m|0.64–0.66초|0.56–0.58초|0.06–0.10초|
|+630m|1.54–1.56초|1.30–1.32초|0.22–0.26초|
|+690m|2.32–2.34초|2.02–2.04초|0.28–0.32초|
|+750m|3.28–3.30초|3.04–3.06초|0.22–0.26초|
|자기 modeled finish|3.98–4.00초|3.76–3.78초|0.20–0.24초|

동일 root에서 관측된 raw20ms first-crossing bracket이며 보간하지 않았다. 첫 구간의 이득을 합산하지 않았고690m 이후 이득 일부가 줄어든 사실도 보존한다.

## 경로·힘·guardian 개입

|관측 모델 지표|Original|SecantOnce|
|---|---:|---:|
|첫13행동 최대 경로오차|0.805m|1.178m|
|첫13행동 clipping rawtick|2/52|6/52|
|전체 부모 최대 경로오차|1.251m|1.337m|
|전체 부모 clipping rawtick|24/201|17/190|
|전체 preclip force/friction 최대비|1.557|1.245|
|전체 grass wheel sample|0|0|

전체 관측 rawtick201/190에는 official event를 확인하는 추가 raw post도 포함되며 완료 bracket과 구분한다. SecantOnce는 첫13행동의 경로/힘 노출이 더 컸다. 전체 count는 관측 길이가 다른 값이고 force clipping은 즉시 safety 위반과 같지 않다. 이 비교로 물리 안전 상한이나 exact actuator inverse를 식별하지 않았다.

SecantOnce의22번째 결정, 원래pre23+661.047m에서 guardian neutralbrake가 한 번 선택됐다. 두 nominal shadow가 **완전H13에서 `path_error_over3m` UNSAFE**로 거절된 뒤 기존 neutral pair가 valid여서 선택됐다. 이것은 부모가3m를 넘었다는 뜻이 아니다. 이후 Original/SecantOnce 부모에 unsafe/progress/technical 오류는 없었다. 지원되지 않는 H13미만 진행 거절이나 거절 우회는0이다.

Original은 pending query/자기 부모 확인이1회, SecantOnce는0회다. 각 arm의 guardian finish certificate13개는 완료 자격만 제공하며 부모 DONE를 대신하지 않았다. 양쪽 자기 부모 tracker event·확인 post·모델 ledger로만 완료했다. 실제 GoalLedger는 read-only였고 모델은 자기 ForecastLedger만 전진했다.

## 무엇을 배웠는가

이 root에서 처음 brake 대신 secant-동등 fullgas를 한 번 쓰고 같은 guardian를 따르면 모델 tail에서0.20–0.24초 이득이 남았다. 이는 단발 명령과 후속 상태/guardian 반응을 합친 조건부 결과다. **동일한 fullgas를 내는 다른 처방도 같은 궤적을 만들므로 sample-hold가 원인이라는 입증이나 secant 법칙 전체의 개선 증거로 쓰지 않는다.** 전체 secant 적용·다른 root 탐색·actual 승격을 하지 않았다.

Original nominal H13은 기존439 물리/geometry/clock/phase 기준으로 저장 native와 factual 비교를 통과했다. 추가 same-command suffix 대조는4행동까지다.5번째부터 명목 명령의 bitwise 동일성이 끝나 그 뒤 전체 native trajectory의 동일 제어 factual 자격을 주장하지 않는다. fresh current의 exact 비교, trajectory 허용 오차, 모델 자기 일관성 범위를 섞지 않았다. SecantOnce에는 새 native counterpart가 없다.

따라서 모델 학습 정보는 얻었지만 실제13.760/14.000초나 남은1.77–2.01초 전체 격차를 해결했다고 말하지 않는다. 음수/작은/overlap 결과를 보존하는 사전 기준을 바꾸지 않았고 임의 gain 문턱으로 골라내지 않았다. 자동 후속 실험0이다.

## 선행 gate·비용·재현

단일 [정책 JSON](design461_next.json)의 planned43650ticks/839worlds·hard49152/896·CPU1800초/wall2400초·순차1·actual0을 그대로 연결했다. 시작 직전 `/tmp` free5469794304bytes가 사전 경험적 저장 추정4527961708bytes보다 큼을 확인했다. JSON·예산 fixture·runner·meter가 같은 설정을 읽고 source/contract hash를 동결했다. 코드/정적 gate는93a8630으로 먼저 commit/push했다.

통합 정적264개와 저장 감사는 새 적분0에서 통과했다. fresh preflight는 old source/current/pending1137ticks/35worlds + root216/6 = **1353/41**로 통과했다. root nominal13은 저장 실제 factual 범위, fullgas13 독립2+held 첫 전이는 모델 자기일관성이다. 첫 query는 각각 fresh nominal/fullgas pair2회 valid를 요구했고 실패 시 fallback이 없는 기존 fixed-first 경로를 사용했다. 이후 guardian의 독립2회를 포함해 모든 query를 fresh 수행했다.

|실제 측정 구간|model ticks|worlds|
|---|---:|---:|
|fresh preflight|1353|41|
|Original|4803|103|
|SecantOnce|4610|99|
|**합계**|**10766**|**243**|

reserved tick도10766이며243 observer stream의 raw post10766개와 일치했다.99개 부모 전이가 fresh selected-first 대조를 통과했다. source·protected/original hash를 저장 감사에서 다시 확인했다. whole worker meter는 **CPU212.751초/wall213.823초**, 별도 정적은 **CPU23.861초/wall23.913초**, 저장 감사는 **CPU8.536초/wall10.523초**다. worker에 import·source 확인·qualification·제어·physics/observer·snapshot/proof/hash/IO·cleanup을 포함했고, 개발/준비/보고/Git/후처리까지 전체 프로젝트 overhead를 완전 계측하거나 순수 solver 시간으로 부르지 않는다.

최종 checkpoint는 **2026-10-17 19:55:49 KST CLOSED**, PID179010은 exit0이다. worker213.8초로10분 전에 종료했다. 단계별 시각·PID·arm/행동·ticks/worlds를 private progress/log와 공개 [진행 기록](compare462_progress.json)에 남겼고 중간 상태를 한국어로 보고했다. 같은 비교의 중복 실행·whole arm 반복·상한 변경0이다.

[코드](compare462.py)·[fixture](test_compare462.py)·[gate](compare462_gate.json)·[집계 JSON](compare462_result.json)·[입력 hash](compare462_inputs.json)·[저장 감사](analyze462.py)를 연구 브랜치에 보존한다. full private plan은 workspace에도 별도 저장했다. raw state/명령/좌표/seed/RNG·개인 자료를 공개하지 않았다.

새 raw1988개 파일901363757bytes는 지정 실행기 `/tmp`에 남기고, [보존 코드](retain462.py)로 workspace private archive113694300bytes와 SHA256 manifest를 만들었다. 모든 member를 대조했고 원본 삭제/이동0이다. 후처리 비용CPU8.676초/wall8.721초이며 적분0이다. [보존 집계](compare462_retention.json)를 제공한다. `/tmp` 공유/영속성은 가정하지 않으며 임시 raw 경로 소실은 재현 한계다. 공개 코드/집계/hash만으로 private 입력을 복원할 수 없다.

이번 raw bytes/tick은 약83723로 이전 관측최대64959보다 높았다. world별 고정 header/receipt 때문에25% 경험적 여유도 보장 상한이 아님을 실제로 확인했다. 현재 실제 저장은 가용 공간 안이었고 IO 오류가 없었다. 다음 실험의 저장 산식에 이전 비율을 자동 재사용하지 않는다.

v474 누적 실제1321369·연구26695·예비84000/사용0·SEALED·main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·기존 사용자 변경·원본/백업/보호자료를 유지했다. 최신 종료 **2026-10-20 19:01:55 KST** 이후 새 실험·자동 연장 없음이다.
