# 497 — 코드 동일성 선행 검사에서 기술적 중단, 물리 실행0

**판정은 TECHNICAL_STOP이다.** 저장 C4 root 조향 평활화 제거 진단을 한 번 접수해 worker를 실행했으나, 물리 실행 전 `497_ORIGINAL_CODE_EXACT`에서 중단됐다. 정책의 성공·반증·11초 목표 달성에 관한 결과는 없다. 추가 보정 world·root·sweep·rescue·재실행은 하지 않았다.

## 승인 정정과 고정 실험

유효 종료는 **2026-10-20 19:01:55 KST**다. 496에서10월16일을 최신 종료라고 쓴 해석은 오류였으며 [정정 이력](diagnostic497_correction.md)을 추가했다. 당시 보고서·JSON·코드·private 기록과 커밋76abed0은 보존했다. 최신 인간 중단 지시는 확인되지 않았다. 승인 원문의 상세 provenance는 private에 남겼다.

[실행 계약](diagnostic497_contract.json)은 [원래 제안](diagnostic497_proposal.json)의 수치·기술 한도를 유지한다. 이미 노출된 DEV의 저장 C4 하나에서 원래 nominal law와 조향 평활화 한 연산만 제거한 law를 비교하도록 구성했다. `laststeer=steer`는 양쪽 모두 유지하며, 이후 pedal 차이는 동일 법칙에 대한 각 상태의 결과로 기록한다. 새 trigger/allocator/후보 확장/profile 재계산은 없다. C4는 사후 선택된 모델 기전 fixture이고 자연 trigger나 독립 DEV 표본이 아니다.

최대6worlds/26holds/104chargedticks, 전체CPU180s/wall240s, private64MiB/512files/32fullstates×512KiB를 고정했다. 모든 source·cold·held 검사는 이6world 안에 포함한다. 국소 지지에는 같은 시간 progress+0.25m 이상, minimum margin 손실0.25m 이내와 H6 안전/정확 반복이 필요하다. 기술 gate 실패는 정책 반증과 구별한다.

## 구현과 중단 지점

별도 import graph에서 기존495 source·capture·history를 재사용했다. 과거 source/candidate/policy 파일을 수정하지 않았다. C4는 before-nominal memory와 full ForecastLedger를 Stream 전에 복원하고, 각 constructor 전에 저장 RNG를 복원하도록 구성했다. 기존495 finite validator는 진짜 과거 prefix3개만 인증하며, 신규 nominal-only 이력은 별도497 authority로 tracker/clock/전체 state·memory·RNG·ledger를 replay한다. allocator receipt를 조작하거나 기존 whitelist를 넓히지 않았다.

실행 전 검토에서 digest 형식, model 비용 구간, NumPy 직렬화, cold-root 연결과 source pin 누락을 수정했다. 이때 worker/world/적분은0이었다. 원래 AST와 variant AST를 역변환 비교해 단일 smoothing 대입식만 다름을 확인했다.

한 번 실행한 worker는 저장 prefix를 읽은 뒤 원래 controller의 추출 코드와 등록 코드의 `marshal.dumps()` 바이트 동일성을 검사했다. 여기서 실패했으므로 pure controller once-act 검사도 완료하지 못했고, static gate 전체가 통과하지 않았다. 최초 counted control hold, source fidelity, cold/held와 H6는 **모두 미실행**이다.

중단 후 AST 추출·compile만 수행한 무물리 조사에서는 원래 controller 추출 함수와497의 추출 결과가 다음과 같았다.

|항목|관측|
|---|---|
|AST digest|동일|
|코드 객체 `==`|true|
|bytecode/constants/names/variables/filename/line table/flags/stack/exception/free/cell 등13개 필드|모두 동일|
|`marshal.dumps()` 바이트|다름|

따라서 직렬화 바이트가 같아야 한다는 기준은 이 경우 잘못된 gate다. 새 정책의 물리 결함을 뜻하지 않는다. 이 조사는 controller/model 생성이나 worker 재실행 없이 compile만 했으며, 실제 gate와 당시 소스는 수정하지 않고 보존했다. 다음 조치 후보는 이 동일성 기준을 AST와 코드 필드 기반으로 고치는 것이지만, 이번 중단 뒤 새 실행은 하지 않았다.

## 실제 비용과 보존

|항목|실제|한도|
|---|---:|---:|
|model worlds /holds /chargedticks|0 /0 /0|6 /26 /104|
|actual action /reset /새seed /allocator|0 /0 /0 /0|0 /0 /0 /0|
|worker CPU /wall|6.487661s /6.471478s|180s /240s|
|최대 RSS|96,350,208B|실행 전1GiB fail-closed check|
|worker private files /bytes|5 /16,099B|512 /67,108,864B|
|fullstate objects|0|32|
|중단 후 pure compile 조사 CPU|0.044255s|별도 정리 비용, 물리0|

worker 종료 후 실제 liveworld0, closedworld0, modelticks0을 확인했다. 입력/source SHA와 budget 불변 검사를 마쳤다. 비공개 원시 파일·오류 traceback·plan·예산·당시 코드 hash와 중단 후 조사 기록을 보존했다. 공개 계약은 중단 뒤 private 승인 provenance만 제거한 버전이며, 실행 당시 계약 원본과 SHA는 private에 별도로 보존했다. 기술/수치 기준은 바꾸지 않았다.

연구 잔액 **26,027**, reserve **84,000/사용0**, 기존 최선 **13.640초**가 그대로다. 새 완주 기록·성능 향상·HOLDOUT/SEALED 접근은 없다. main 지정 SHA·Participants·기존 백업도 변경하지 않았다.

[집계 JSON](diagnostic497_result.json) · [단일 worker](run497.py) · [nominal 이력 인증](history497.py)
