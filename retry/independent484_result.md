# 484 — 독립 DEV 반증 설계와 실행 전 경계

**설계만 완료했다. 신규 seed 추출·geometry solve·model world/tick·actual 행동·reset은 모두 0이다.** [계약](independent484_contract.json)은 실행 승인이 아니며, 후속 구현·계약 검토와 명시적 실행 승인 전에는 입력 선정이나 bootstrap도 시작하지 않는다. 적용 종료는 기존 정정 기록에 근거한 2026-10-20 19:01:55 KST이며 자동 연장은 없다.

## 검증된 출발점과 주장 범위

저장된 483 결과는 같은 80ms 후보·guard에서 순위만 바꾼 국소 기전의 증거다. 공통 4 holds/0.32초의 최소 margin은 control 0.9678868m, variant 1.5203888m로 +0.5525020m였다. control은 safe4 뒤 다음 query의 후보가 모두 부적격이었고 variant는 safe6이었다. 이는 사용한 한 root의 결과이며 독립 조건 일반화·실제 주행·픽셀 정책 개선은 검증하지 않았다. 이번 단계에서 483을 재실행하거나 같은 root를 연장하지 않았다.

484는 두 신규 DEV 조건 각각에서 공통 root 이후 최대 6 holds/24 raw ticks/0.48초만 비교하는 최소 독립 반증안이다. 두 arm은 동일 시작 상태와 종료 범위를 사용한다. whole-map GT를 사용하는 모델 진단이며 실제·픽셀 성능 주장을 허용하지 않는다.

## 조건 선정과 누출 방지

아직 존재하지 않는 두 슬롯을 고정했다. 실행 승인 후 현재까지의 identity 제외 원장을 완성하고, 한 번의 8-byte entropy에서 두 seed를 고정 순서로 정한다. identity 충돌만 슬롯당 최대 16회 대체하며 실패·길이·곡률·planner 성립·저장 크기·성능으로 고르지 않는다. track label 1/2는 obstacle stream 선택이지 road-family 독립성의 증명이 아니다. 선정된 조건이 준비에 실패하면 대체하지 않는다.

원래 DEV8, 이미 사용한 296의 DEV12 및 372에서 노출된 297의 DEV12를 별도 이력으로 유지하며 중복 합산하지 않는다. HOLDOUT_A 8회 사용, HOLDOUT_B 16 identities/32 episode queries 사용 이력은 잠근다. SEALED16은 미사용이며 이번 접근0이다. 182의 4조건 중 영구 DEV 전환은 2개뿐이다. 현재 확인된 미사용 DEV는0이며 전역 부재를 증명한 수치는 아니다. 오래된 337-seed inventory는 현재 제외 집합의 완전성 증명이 아니다.

검토 중 과거 DEV 성능이 섞인 메타데이터를 접한 경로는 비공개 감사에 기록하고 선정 근거에서 제외했다. 보호된 HOLDOUT/SEALED 성능·raw는 열지 않았다. identity·seed·비공개 입력·raw는 공개하지 않는다.

## 준비 비용과 공정 비교

조건별 새 geometry/P4가 필요하다. 기존 N1 node를 복사하지 않고 동결된 solver 1회, 기존 조건에서 허용된 수치 projection, 고정 계수와 4회 project_four만 허용한다. geometry는 조건당 CPU60초/wall90초 상한이다. native body에서 질량을 산출하여 별도 mass-probe world를 만들지 않는다.

조건별 official reset1회 후 동결된 SourceC/P4로 FIRST_LAP에서 signed arc가 처음 L/4에 도달한 boundary를 공통 root로 쓴다. root 탐색은 action127 이내이며 이후 nominal80ms source witness1회를 포함해 조건당 actual128회가 상한이다. reset은 raw64회 상한이며 내부 자동 재시도도 호출 전에 차단·계상한다. root 이전 준비가 실패하면 해당 조건은 inconclusive다.

새 조건마다 independent cold source2개와 held-first1개를 실제 witness에 맞춘다. native는 body/joint까지 해제한 뒤 model parent+shadow 비교로 넘어간다. 실제 동시 물리 world 최대2, 동시 적분1이다. 공통 native prefix의 입력·RNG·GoalLedger·charge journal을 연결하는 새 증명이 필요하며 history483의 고정 121행동 증명을 가장하지 않는다.

## 판정과 실행 전 게이트

후보·80ms·3m guard·steering·source tolerance를 그대로 두고 ranking만 바꾼다. 각 arm은 독립 parent2개와 held-first1개를 사용한다. 후보별 1회, 선택 후보의 독립 repeat, own join과 완전한 history 연결을 요구한다.

순위 차이는 **같은 query/context의 같은 eligible 후보 집합**에 두 순위를 적용한 full float32 명령 차이다. 서로 다른 arm 상태의 명령 차이만으로 세지 않는다. 성공은 두 조건 모두 자격 통과·순위 차이·variant safe/progress6 holds와 같은 시간 범위 최소 margin 이득 >0.25m다. control도 안전하면 두 조건의 한정된 margin 효과만 주장한다.

자격 있는 differing-policy 조건에서 새 안전 위반, 등록한 empty/progress 열화 또는 margin 이득 <−0.25m는 기각한다. 검증된 기각 근거가 root ceiling/NO_INFORMATION보다 우선한다. 기술·source 무효 자료로 정책 결과를 판정하지 않는다. root ceiling, 순위 차이 부재, 부분 시간 불일치, 약한·혼합 효과, 준비/자원 실패는 inconclusive이며 다른 seed·root·metric·horizon으로 구제하지 않는다.

## 비용 상한과 남은 장애물

| 권장 2조건안 | 상한 |
|---|---:|
| model world / charged ticks / wrapper slots |226 / 1,064 / 266|
| 비교 query·allocator calls |52|
| native actual / reset / reset 포함 raw |256 / 2 / 1,152|
| 전체 CPU / wall |2,400초 / 3,000초|
| model raw / native raw |392,471,929B / 648,961,335B|
| temp·proof·decision·512MiB 예비 포함 /tmp |1,645,413,040B|
| 설계 시 /tmp 추가 여유 |98,188,624B|

수치는 완료 보장이 아닌 hard cap이다. 481 모델 raw 실측329,731,405B/2,356ticks와 과거 native 최대392,413.371B/raw에 25% 여유·world header·reset·full readback 비용을 포함했다. 최근 472 native 실측263,325,073B/733raw는 더 낮다. 483 실제 측정 CPU107.826초와 개발 보수 계상20초를 구분했다.

508개 full-state의 개당393,216B 상한과 header 크기는 새 지도에서 아직 입증되지 않았다. model3,596/native3,264 파일 수 상한도 향후 writer가 모든 파일 생성 전에 slot·byte·temp·종료 기록 예비를 실제 강제해야 한다. codec 상속만으로 구현됐다고 주장하지 않는다. 새 지도·source·공간·schema 실패 시 필드 생략·상한 완화·기존 raw 삭제·대체 조건 선정 없이 중단한다. /tmp 단일 raw 사본은 비영속이며 hash로 복구할 수 없다.

첫 FIRST root H6 대안은 /tmp1,268,696,204B로 작지만 초기 직선·순위 차이 부재로 정보가 없을 위험이 크다. quarter H13은2,027,148,446B로 현재 여유를 초과한다. 사용한 N1 pre23 H13은 actual/reset0의 기술 회귀안일 뿐 독립 DEV를 대신하지 않는다. 483의 기전 자격과 새 조건 source gate가 있으므로 이번 제한된 주장의 선행 조건으로 N1 전체 rollout을 요구하지 않는다. 전체 정책 배치는 별도 전 구간 자격이 필요하다.

현재 연구 잔여26,175·예비84,000/사용0은 그대로다. 향후 별도 승인으로 actual256회를 모두 시도하면 연구 잔여 최소25,919이며 reset/raw/model은 별도 계상한다. 현재 단계에는 차감0이다. 다음 조치는 계약 검토, 현재 identity 제외 집합 완성, generic prefix 증명·writer quota 구현과 무적분 검증이다. 새 실행은 시작하지 않았다.

설계 산술·source/protected/main/원장 hash를 무적분 검증했고, 검토 전 코드·계약과 검토 후 receipt를 별도로 보존했다. 공개물은 설계 코드·집계 계약·이 보고서로 제한한다.
