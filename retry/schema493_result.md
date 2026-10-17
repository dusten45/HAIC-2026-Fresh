# 493 — raw schema 계약 수정, 저장 증거 부족 확인

**물리 실행 없이 공통 raw adapter와 저장 증거를 검사했다. 492의 두 witness에는 tracker 직후 damage·controller phase의 직접 관측이 없어 전체 source gate를 마칠 수 없다.** 492의 실패·비용·원시 기록은 그대로 보존했다. 새로운 actual/reset/model/world/step은 모두0이며 모델 전용 재개 계약도 제안하지 않는다.

## 무엇이 직접 저장됐는가

|필드|492 native 직접 증거|올바른 시점과 한계|
|---|---|---|
|collision|Dispatch437의 tracker 직후 `_collision_this_step`|해당 raw step의 event flag|
|wheel contacts|같은 callback의 네 wheel tiles 유무 count|postWorld/tracker 직후|
|grass|각 raw_tick의 네 tire force 관측|Car.step의 force clamp 전, World.Step 전. postgrass로 바꾸지 않음|
|phase|before/after nominal controller memory와 hold 후 full controller|명령 생성/hold 경계 metadata. 각 tracker-post의 직접 controller 관측은 없음|
|damage|hold 전후 full physical snapshot, row.damage|wrapper가 raw loop를 마치고 damage를 갱신한 뒤의 최종값. 중간 tick tracker-post snapshot은 없음|
|GoalLedger|hold 전후 ledger와 연속 raw clock|시계·진행의 권위이며 damage/grass/phase 센서는 아님|

native 두 witness의 전후 damage가0이고 phase도 같아도, 해당 tick의 직접 측정으로 채우지 않았다. 소스상 damage 갱신이 raw loop 뒤 한 번이라는 사실은 timing 해석의 근거다. 이는 사용자께서 요구한 **직접 저장 증거**를 대신하지 않는다. 마지막 full snapshot도 마지막 tracker callback과 시각 숫자는 같지만 wrapper damage/effects 갱신 후이므로 같은 microphase가 아니다. 바퀴 회전 dynamics.phase와 controller phase도 혼동하지 않는다.

또한 model observer435의 `posts[].damage`는 `row.predicted.damage`, 즉 wrapper 종료값을 모든 tick에 소급 복사한 것이다. phase도 hold 메모리에서 붙였고 grass는 preWorld tire sample에서 붙였다. model collision은 `_collision_this_step or contacts`이며 native의 raw event와 의미가 다르다. 둘 다 false인 이번 기록을 이용해 저장되지 않은 원자 event 측정값을 추정하지 않았다.

## 공통 adapter와 반증 검사

[schema493.py](schema493.py)는 `COMMON_RAW493_V1`에서 pre-force, after-nominal, tracker-post, wrapper-return을 분리한다. 원래 damage/collision/contact/grass/phase 검사를 삭제하지 않았다. 직접 tracker capture가 없으면 `MissingEvidence493`로 닫힌다. 향후 직접 capture를 넣더라도 owner·clock·body/tracker digest·microphase와 SHA/JSON-pointer로 인증한 실제 관측 receipt가 일치해야 한다. synthetic의 메모리 reader는 synthetic fixture에만 쓰며 실제 관측의 권위가 아니다.

positive/negative synthetic **20개 통과**: 같은 clock의 잘못된 microphase, 이웃 tick, 다른 owner/post, before-nominal phase, 다른 contact, pre/post hull 시각, wheel/tick join, 누락 tick, 위조 receipt, collision/contact 집계 혼합, damage/grass 불일치를 거부했다. collision hold에서 tracker-post damage0과 wrapper 반환 damage0.2를 구분하는 positive 사례도 통과했다. boundary0으로 누락 raw damage를 채우는 사례는 거부됐다.

492 raw **675파일·119,416,267B**의 기존 SHA·JSON/codec/state digest와 전체 native **74 holds·296 action ticks**를 읽기 전용으로 검사했다. 모든 hold의 시각·wheel coverage·full boundary·controller memory·GoalLedger chain을 확인했다. 296ticks에는 preWorld grass와 native post collision/contact가 있지만 직접 tracker-post damage·controller phase는 없다. root→witness1→witness2의 full state/ledger join도 보존됐다. 이 구조적 일치가 부족한 관측을 보충하지는 않는다.

## 첫 cold trace는 어디까지 재사용할 수 있는가

기존 첫 cold frame을 그대로 사용해, 물리 생성자/reset/step/make_env를 poison한 상태로 원래 `ledger439.compare_first`를491 isolated binding에서 실행했다. 명령·before/after memory·현재 root 복원·body/wheel/hull fidelity·GoalLedger 부분 gate는 통과했다. body 위치·속도·yaw·시간 오차0, wheel force ratio 최대오차1.562980755e-6, hull speed 최대오차7.554285518e-6, grass exact·clip flag mismatch0이었다. source가 native ledger를 대체하지 않는 기존 규칙도 유지했다.

이는 **새493의 저장 데이터 부분 검사**다. 원래492를 source 통과로 고치지 않았다. 첫 cold의 전체 raw 비교는 누락과 시점/semantics 차이 때문에 완료하지 못한다. 두 번째 cold·실제 warm·H6는 계속 미실행이다. root의 source authority·정책 성공/기각·일반화 판정도 없다.

## 필요한 최소 재수집과 중복 방지

부족한 native 측정은 **두 witness의8 raw tracker callbacks**에서 직접 읽은 damage·controller phase다. 해당 callback에서 raw event와 contact/tiles, clock·owner·tracker/body snapshot을 함께 연결해야 before/post 혼합을 막을 수 있다. pre-force grass는 기존과 같이 같은 tick의 tire 관측으로 보존하고 post contacts와 별도 정의한다. model observer도 최종 damage 소급 복사를 직접 tick capture로 바꾸고 raw collision event와 contacts latch를 별도로 기록해야 한다. 이 observer의 소스/스키마 정적 gate를 새 물리보다 먼저 검증해야 한다.

492 native world는 이미 body/joint까지 파괴돼 과거8 callbacks에 관측을 추가할 수 없다. 새 native 증거가 별도로 승인될 경우, 같은 knowncase를 **새 reset1회→자연 prefix72actions→witness2actions**로 재현하고 초기 identity·root equality를 다시 확인하는 것이 현재 저장 root에 접근하는 경로다. 이는 새 수집의 예상 최소 접근 비용이지 실행 승인이나 동일 root 보장이 아니다. 과거 full prefix capture를 모두 다시 쓰는 것은 피하고, prefix 권위·charge/ledger 연속성과 새 witness tick 직접 관측을 필요한 범위로 저장할 수 있다. model에서 저장 root를 복원하는 것만으로 새 native 관측이라고 주장할 수 없다.

따라서 지금 남은 model-only cold/warm/H6만 실행하면 source gate가 생략된다. **이번에는 실행하지 않았고 해당 재개 계약도 만들지 않았다.** 기존 첫 cold trace는 부분 회귀 fixture로 보존하되 누락을 메울 수단으로 쓰지 않는다.

## 비용·보존

493 worker 기록은 CPU5.497810982초·wall5.742175759초·최대 RSS87,814,144B다. synthetic·전체492 저장 schema·첫 cold 부분 비교·불변 해시 검증을 포함한다. 기존/보호 기록3,895개 hash를 재확인했다. 연구 잔여 **26,101**, reserve **84,000/사용0**, best **13.640초**는 변하지 않았다. 최신 종료는 **2026-10-20 19:01:55 KST**다.

원시 state·좌표·seed·개인 자료와 상세 provenance는 비공개에 남긴다. 코드·계약·집계만 연구 브랜치에 통상 commit/push한다. 자동 후속 실행은 없다.

[집계 JSON](schema493_result.json) · [등록 계약](schema493_contract.json) · [검사 실행기](audit493.py) · [synthetic tests](test_schema493.py)
