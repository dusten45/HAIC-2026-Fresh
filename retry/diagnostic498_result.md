# 498 — 엄격 code gate 통과 후 C4 비교 완료, NO_INFORMATION

**동일 C4에서 평활화 제거 비교를 물리적으로 한 번 마쳤으며 판정은 NO_INFORMATION이다.** 두 arm 모두6 own holds를 안전하게 마쳤고 독립 cold 반복과 held-first가 정확히 일치했다. 같은0.48초에서 progress 이득은 **0.009233679m**, 최소 margin 차이는 **−0.117940353m**다. progress+0.25m 기준에 미달해 승격하지 않았으며, 사전 반증 기준에도 해당하지 않는다. 새 완주/11초 달성/배포 결과가 아니다.

## 497 보존과 엄격한 검증

497의 marshal 실패 기록·원본 소스와 private 계약은 변경하지 않았다. 498은 최신 명시 승인에 따라 같은 저장 C4·같은 입력/예산·같은 한 번의 비교를 수행했다. 승인 종료는 **2026-10-20 19:01:55 KST**이며 자동 연장은 없다.

marshal 바이트 동일성은 사용하지 않는다. AST에서 단일 smoothing 식만 바뀌는지 역변환 비교하고, 독립적으로 컴파일한 원본과 public bytecode·exception table·인자/locals/stack/flags·names/vars/freevars/cellvars·중첩 코드와 typed 상수를 대조한다. bool/int·signed zero·bytes도 구분한다. functions의 defaults/kwdefaults, 실제 SourceC `__class__` owner, global 객체 identity를 검사한다.

기대 binding은 actual globals 자기 복사에만 의존하지 않는다. 정상 np/copy/math/ast/Path/types와 소스가 고정된 control_code/scope_for/executor/sensor/original policy에 연결한다. 각 helper를 원본 AST와 대조하고,491 policy wrapper의 코드 및 old/self closure를 별도로 검사했다. 원본 reference를 만들기 **전에** np/copy/sensor/policy/Controller globals를 바꿔도 정확한 global identity 오류로 거부되는5개 fixture를 통과했다. exec scope도 고정 입력/root memory의 배열 dtype/shape/bytes와 scalar type/value를 비교하고 np/builtin shadow와 누락 입력을 거부한다.

전체 사전 경로는 물리 constructor/reset/step poison 아래에서 입력·cloned namespace import·writer/meter 설치·root receipt/history 인증·pure controller 호출·관측 lifecycle fixture까지 실행했다. 원래 Stream/ObserveMixin init/one/dump/close는 fake BaseChild 의존성으로 검사했고, 물리 진입은0이었다. synthetic code/binding 검사22개, lifecycle23개, reference 이전 global 변조5개, 저장 nominal own history의 ledger/policy/row 변조3개를 확인했다. 저장 history fixture의 마지막 snapshot 의존성만 명시적으로 stub했으며 실제 own 이력은 아래 실제 비교에서 다시 인증했다.

## 물리 전 사전 실패와 복구 비용

첫498 사전 worker는 `dependency.control_code:semantic_code_mismatch`에서 멈췄다. **world/hold/tick0**이었다. 그 소스5개·plan·오류·산출물은 private에 그대로 보존했다.

compile만 수행한 조사에서 함수만 독립 컴파일하면 모듈 import 문맥이 사라져 Python이 `LOAD_ATTR` 대신 `LOAD_METHOD`를 내보내는 차이를 확인했다. gate를 삭제하거나 bytecode 불일치를 무조건 허용하지 않았다. **원본 전체 모듈 AST를 실행 없이 컴파일**한 뒤 해당 qualified code를 추출하도록 참조 생성만 고쳤다. namespace 변환도 기존492의 허용된 변환을 그대로 사용했다.

이어지는 `continue-static`은 첫 worker의 물리 카운터가 전부0이어야 진입할 수 있고, 이전 출력 파일·bytes와 비용을 총한도에서 먼저 차감한다. 첫 CPU7.416838s/wall7.434556s에 조사·마지막 기록을 위한 보수 allowance CPU0.25s/wall0.5s를 더해 누적했다. 다른 root/보정 world/물리 재시도/parameter sweep/rescue는0이다. 총 물리 비교는 아래 **한 번**이다.

## 저장 C4와 실제 source·own 인증

495의 source/warm-qualified quarter authority와 진짜 finite prefix3개를 재인증해 C4 before-nominal state/memory/full ledger에 연결했다. cold Stream root와 native root의 구조적 contact 진단 차이는 기존 physical identity 규칙 하나만 사용해 구분했다. C4를 새로운 native witness나 독립 DEV로 취급하지 않았다.

각 branch constructor 전에 저장 RNG를 복원하고 full ForecastLedger를 Stream 전에 넣었다. nominal은 own hold마다 한 번만 호출했고 allocator와 행동 override는 사용하지 않았다. 원래 SourceC/P4 법칙을 유지하면서 variant의 `steer=.8*steer+.2*laststeer`만 `steer=steer`로 바꿨다. `laststeer=steer`와 physical actuator bounds는 유지했다. 이후 각 상태 때문에 달라지는 pedal은 같은 법칙의 결과다.

첫 counted control hold를 저장495 nominal trace와 대조했다. command·before/after memory, body/wheel/raw hull·phase·clip/grass·직접 tracker-post 및 wrapper-return 안전 검사를 모두 통과했고, 보고된 물리 오차는0이었다. 별도 calibration world는 사용하지 않았다.

각 arm은 cold H6 두 개와 held-first 하나를 실행했다. full nominal-only own authority가 모든 tracker/clock/state/memory/RNG/ledger join을 replay했고, 최초 두 H6의 signature/posts와 direct capture 전체가 일치했다. held-first도 첫 transition과 정확히 일치했다. source 이후 native 일반화나 whole-lap 일관성을 주장하지 않는다.

## 국소 결과와 기전의 한계

|항목|control|평활화 제거|
|---|---:|---:|
|첫 cold의 안전 own holds|6/6|6/6|
|동일 실행 시간|0.48s|0.48s|
|root 대비 progress|21.890311382m|21.899545061m|
|root-inclusive 최소 margin|1.645433660m|1.527493307m|
|첫 hold 앞바퀴 최대 횡력|209.60N|260.19N|
|H6 앞바퀴 최대 횡력|235.77N|260.19N|
|H6 앞바퀴 clipping 수|0|0|
|마지막 절대 heading 오차|18.36°|17.97°|
|마지막 차체 절대 lateral 속도|0.7073m/s|0.8061m/s|

첫 조향 변화량은 평활화 제거로25% 커졌다. 첫 hold 앞 최대 횡력도 약24% 증가했고 전체 최소 margin은 나빠졌으나, 두 arm 모두 안전했고 힘 clipping은 없었다. heading·차체 횡속도 변화의 방향도 같지 않다. 서로 다른 tick/wheel의 힘 최대를 벡터 합하지 않았다. 경로 법선 속도와 차체 횡속도도 구분해서 private에 보존했다.

사전 국소 지지 기준은 H6 안전·정확 반복에 **progress≥+0.25m 및 margin 손실≤0.25m**를 함께 요구한다. 관측된 progress 약9.23mm는 이를 충족하지 않는다. 더 이른 unsafe 또는 margin 보상 없이 progress0.25m 이상 손실이라는 반증 기준도 충족하지 않아 **NO_INFORMATION**이다. 끝 오차 일부 개선만 뽑아 승격하지 않는다. 이 결과는 평활화 제거라는 한 개입에 국한하며, preview/종방향 후보/위험 trigger 전체를 기각하거나 원인을 확정하지 않는다.

## 총비용·보존

|항목|누적 실제|한도|
|---|---:|---:|
|model worlds /종료 world /live|6 /6 /0|6 /6 /0|
|wrapper holds /charged ticks|26 /104|26 /104|
|actual action /reset /새seed /allocator|0 /0 /0 /0|0 /0 /0 /0|
|이전 사전 비용 포함 worker CPU /wall snapshot|38.829037s /39.357085s|180s /240s|
|성공한 worker 단독 CPU /wall|31.162199s /31.422529s|위 총한도에 포함|
|최대 RSS|129,728,512B|사전1GiB fail-closed check|
|fullstate objects|14|32|
|실패 사전 raw·소스·조사 포함 파일/bytes|306 /13,395,905B|512 /67,108,864B|

raw codec/readback 두 번, 원본 SHA 불변 검사와 world body/joint teardown은 worker 한도 안에서 완료했다. 결과 snapshot 뒤 마지막 control JSON 기록까지 전체한도 guard를 유지했다. 보존 manifest와 publication metadata는 남겨 둔 종료 allowance 안에 기록한다. 연구 잔액 **26,027**, reserve **84,000/사용0**, 기존 최선 **13.640초**가 그대로다. HOLDOUT/SEALED 접근은0이다.

원시 state/좌표/RNG/명령열과 상세 trace는 private에 보존한다. 공개는 코드·등록 계약·집계·이 보고서다. main 지정 SHA·Participants·기존 백업은 보존하며 일반 연구 브랜치 commit/push 후 원격 SHA를 검증한다. 추가 실험이나 자동 후속 실행은 하지 않는다.

[집계 JSON](diagnostic498_result.json) · [실행 계약](diagnostic498_contract.json) · [worker](run498.py) · [엄격 code gate](codegate498.py) · [전체 사전 경로](preflight498.py) · [nominal own 이력](history498.py)
