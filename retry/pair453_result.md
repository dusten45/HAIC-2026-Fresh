# 453 — 고정 H1+조건부 B native 전체 lap pair

**두 arm 모두 공식 native 완주했다. baseline15.08초, candidate14.98초로 전체 lap 이득은0.10초다.** candidate는11.99초 목표보다 **2.99초 느리다.** 국소 모델 이득을 합산하지 않고 같은 known DEV의 자기 native 공식 finish event에서 직접 비교했다.11초대·픽셀 정책·공식 서버 성적·새 조건 일반화는 달성/검증하지 않았다.

| arm | 실제 행동 | prefix/이후 검증 전이 | +270m 이후 B 전환 | 공식 lap | 목표11.99초 |
|---|---:|---:|---:|---:|---:|
|baseline|189|22/167|78행동 뒤|15.08초|3.09초 미달|
|candidate|188|22/166|72행동 뒤|14.98초|2.99초 미달|

정책 차이는 candidate의 pre23 첫 fullgas 한 번뿐이다. 동일22-action 관측 prefix, +270m까지 own nominal, 그 뒤 동일 조건부 B와 기존 native finish 경로를 고정했다. 양쪽 neutral 선택은1회씩이고 candidate의 추가 fullgas는 없다. baseline 전체189개의 native rows는 저장442 C0와 정확히 같았다.

## 먼저 통과한 검사와 native 권위

source/code/정책·mode 전환·root·270m·H13·기존 허용 오차·중단 기준·원장v472를 동결했다. 정적 **242개**와 저장 감사는 첫 시도에 통과했다. 새 fixture는 forced pulse/fixed 구간 fallback 금지,270m/B/pending mode, current native GoalLedger와 ForecastLedger 구분, 등록된 late FINISHED shadow의 actual-DONE 금지,440/220/reset2 및 모델98304/1792 상한을 검사했다. 기존 recorded native pending/권위 fixture도 함께 통과했다.

fresh preflight는 **1,353 ticks/41 worlds**로 허용1458/41 안에서 통과했고 그 후에만 native reset을 시작했다. H1 source216/6은 원래 model H13 재현과 held/반복에 더해 nominal442·fullgas448의 실제13행동을 factual calibration으로 비교했다. 기존 full native/current restore/pending qualification1137/35는 physics/threshold 변경 없이 새 private stage로 출력 위치만 바꿔 수행했다. 이전 결과·모델 상태를 새 정책 전체 성공으로 소급하지 않았다.

각 arm 초기 전체 state/wrapper/관측 hash/RNG는 원래 known condition과 정확히 같았고 pre23 root도 원래와 양쪽 사이 정확히 같았다. 고정22 prefix는 자기 charged native ticket의 사실을 먼저 commit하고 저장 실제/기존 source와 대조했다. 모든 postroot 명령은 fresh-current 독립 모델 반복과 read-only adapter·nominal memory·GoalLedger 검증을 거쳤다. fixed 구간의 자격 실패는 중단이며 B 구간에서만 등록된 비선택 대안 거절에 neutral을 허용했다. 선택된 명령은 own native 사실 commit 뒤 기존439 물리/geometry·goal-side/age/clock/deadline/DONE 검사를 수행했다.

**377개 실제 호출 모두 native 사실 기록과 성공 dispatch가 있다.333개 current 전이가 전부 검증됐고 미확정 행동과 clipping 비교 불일치는0이다.** 모델 값을 실제 ledger에 commit하지 않았고 실패 후 추가 dispatch를 허용하는 경로도 쓰지 않았다. 양쪽 모두 자기 official tracker/native finish를 확인한 뒤에만 완료로 처리했다.

baseline 공식 event/확인 시각은16.10/16.12초, candidate는16.00/16.00초이며 reset-complete1.02초를 뺀 lap이15.08/14.98초다. 이것은 공식 관측 값이며 late shadow 완료를 native DONE로 대신하지 않았다. 이번 live pair의 registered pending query는0회다. pending/at-root/negative-domain 권위는 정적·fresh preflight에서 검증했지만, 이번 live에서 그 경로가 실행됐다고 표시하지 않는다. late future model FINISHED guardian의 자격과 own native 완료 검사는 실제 사용됐다.

## 국소 이득과 전체 결과

이번 **native** +270m crossing은 lap 기준 baseline[6.16,6.18]초, candidate[5.74,5.76]초로 국소 이득[0.40,0.44]초다. 이후 official finish까지는 baseline[8.90,8.92]초, candidate[9.22,9.24]초로 candidate가 **[0.30,0.34]초 더 썼다.** 그 결과 전체 차이는0.10초로 작아졌다. 이는 같은 실제 trace의 공간 구간 시간 차이며 속력/steering/tyre/guardian 어느 요인이 원인인지는 아직 분리하지 않았다.

candidate 전체 force ratio 최대1.26874는 baseline1.23199보다 높지만 clipped wheel 표본은17/2996 대44/3020으로 적다. 최대 post path error는1.41497m 대1.37915m였다. 양쪽 damage0이며 기존 안전/진행 기준을 통과했다. 특정 표본 하나나 branch terminal state의 불일치만으로 전체 상태가 좋다/나쁘다고 판단하지 않는다. 이번 시간 이득은 이 고정 단발 pulse+frozen B 한 가설의 known-condition 결과이며 다른 방법군이나 연구 전체에 대한 판정은 아니다. 원래451의14행동 censor와 과거 실패·비용은 그대로다.

## 비용·재현·마감

실사용은 **actual377 wrapper/reset2**, raw action755+749=1504, reset102를 포함해 **1606 native ticks**다. 모델은 preflight1353 + baseline16822 + candidate16666 = **34,841 ticks/711 worlds**이고 raw posts/reserved가 일치한다. planned83,826/1625·hard98,304/1792, actual440/reset2·각220, 모든 exclusive 시간 상한을 지켰다. 재시도와 새 seed·학습·HOLDOUT/SEALED·예비·추가 유료 자원은0이다.

| worker 비용 | CPU초 | wall초 |
|---|---:|---:|
|model exclusive|805.143|811.009|
|actual exclusive|174.278|176.133|
|whole worker|979.529|987.245|

native exclusive에는 reset·제어·snapshot·native 물리/observer·사실 commit·forecast 비교·IO가 포함되며 model region은 제외한다. model에는 preflight/query 복원·physics/observer·검사·receipt/IO·cleanup이 포함된다. 정적 CPU20.773초/wall20.877초, 저장 감사 CPU21.552초와 추가 저장 구간 진단은 별도다. 순수 solver 비용이나 전체 준비·보고·Git·일부 import overhead는 완전 계측하지 않았다.

실제 단계·arm/행동·소비량·시각을 decision checkpoint에 기록하고 진행 중 구현 gate·native270m B전환·baseline 완주·candidate 진행을 연구 브랜치에도 commit/push했다. 마지막 checkpoint는 **2026-10-17 17:52:14 KST `CLOSED`**이며 PID174122 종료를 확인했다. 최종 집계는 [JSON](pair453_result.json), 진행 이력의 최종 상태는 [progress](pair453_progress.json)에 있다.

v473은 새 실제377만 차감해 연구 잔여 **27,059**, 누적 실제 **1,321,005**, 예비 **84,000/사용0**이다. 다음 판단은 이미 저장된 두 native trace에서 +270m 이후0.30–0.34초가 소모된 공간/제어 구간을 분해하는 것이다. 새로운 pulse/seed/정책/실험을 추가 실행하지 않았다. 현재 고정 정책을 더 작은 gate로 반복하는 것보다 이 전체 결과로 다음 가설을 선택해야 한다.

유효 종료 **2026년10월20일19:01:55 KST**, main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·기존 사용자 변경·backup을 보존했다. private state/seed/명령/RNG는 공개하지 않았다.

[실행/동결](pair453.py) · [정책과 current/pending query](query453.py) · [native pair](native453.py) · [상한/비용](meter453.py) · [새 integration fixture](test_pair453.py) · [저장 감사](analyze453.py).
