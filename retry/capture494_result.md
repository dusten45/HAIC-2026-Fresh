# 494 — 직접 callback capture 무적분 체크포인트 통과

**native/model의 tracker 직후 직접 callback을 immutable receipt와 COMMON_RAW493_V1에 연결했고, fake env/controller 기반31개 검사가 통과했다.** 새 physical world/reset/step은0, physics poison 진입 시도도0이다. 실제 source/warm/history/H6의 동적 자격이나 새 물리 실행 승인을 뜻하지 않는다. 492 실패·493 부분 검증·원본/비용은 보존했다.

## 생산 연결

[capture494.py](capture494.py)의 `Registry494.native(authority,...)`는 NativeAuthority439의 bound env/controller와 ledger accessor를 고정한다. controller phase를 직접 읽을 때 memory 전후 불변을 검사하며 act를 호출하지 않는다. `Registry494.model(child,...)`는 같은 방식으로 child의 model/controller/ledger를 묶는다. 설치는 `retry492` isolated graph만 허용한다. 실제 native `Dispatch437.call`과 model `ObserveMixin.one`이 참조하는 PostTrackerTap 별칭에 composite callback을 연결하며, 원래 capture434 클래스의 global과 기존437/435/492/493 파일은 바꾸지 않는다.

callback은 원 tracker.update가 끝난 뒤 live damage·controller phase·raw collision event·네 wheel tile/contact·body/tracker snapshot을 직접 읽는다. raw clock은 `ledger_before.last_clock_tick + callback ordinal`이고 live 시간·tracker/body identity를 확인한다. pre-force hull은 한 raw tick 앞이어야 한다. model contacts는 **hold 동안 BeginContact 누적 latch**로 별도 이름을 쓰며 raw event나 현재 접촉이라고 부르지 않는다.

직접 capture를 JSON-ready 구조로 정규화하고 immutable sidecar에 먼저 저장한다. 그 뒤 SHA/JSON pointer를 외부 ref로 붙여 self-referential hash를 피한다. legacy observer에는 다른 사본을 주므로, hold 후 damage/phase/post를 변경해도 sidecar와 digest가 변하지 않는다. 각 hold의 원래 tires/hulls도 별도 immutable receipt에 묶는다. wrapper 반환 후에는 최종 damage·terminal·반환 phase와 전체 hold를 별도 봉인한다.

`finish_hold`는 원 wrapper/child 반환 뒤 명시적으로 호출하는 API다. callback에서 읽은 phase와 after-nominal metadata를 연결하며, terminal 반환 후 DONE은 분리한다. 1~3tick은 terminal 근거가 있어야 하고, 누락 tick을4개로 채우지 않는다. 실제 후속 실행자는 등록된 quota writer를 주입해야 한다. 제공된 ImmutableWriter494는 이번 private synthetic 검증용 유한 writer다.

## 인증·비교

인증은 외부의 input/line/nodes/projection/runtime/capture 소스 SHA binding을 요구한다. owner·tick·microphase·snapshot/post digest·실제 파일 receipt·JSON pointer·preforce wheel/tick/time·wrapper 반환을 모두 연결한다. Python에서 `True == 1`이어도 raw clock/count/index는 exact int와 범위 검사로 거부한다. 직접 관측이 없으면493의 missing-evidence gate는 계속 닫힌다.

cold repeat은 **각각의 owner/receipt를 먼저 인증**한 뒤 측정 필드 전체를 정확히 비교한다. 차이를 허용하는 것은 owner와 receipt 식별자뿐이다. body/tracker/controller snapshot, 직접 damage/phase/event/contact, preforce 모든 원본 tires/hulls, wrapper 반환과 source/input binding은 비교에 남는다. native/model raw flag 비교는 기존493 검사에 wrapper-return damage 안전 판정을 추가한다. raw damage0이어도 반환 damage0.2면 safe로 판정하지 않는다. 전체 physical fidelity/history는 별도 gate라는 범위를 명시했다.

## 검증 결과와 복구 기록

31개 검사는 생산 callback을 실제 immutable serializer/read_ref와 함께 실행했다. native는 실제 isolated Dispatch437.call에 fake env/readonly controller를 연결했고, model은 실제 생산 PostTrackerTap 별칭에 fake model/controller를 연결했다. **전체 ObserveMixin.one은 실행하지 않았다.** 모든 physics 생성자/reset/step/make_env를 poison했고 진입 시도0을 확인했다. 추가 nominal act도0이었다.

positive는9개 fake holds다. 다른 owner/receipt 경로의 cold exact repeat, legacy mutable post 재작성, raw0/반환0.2의 damage 구분, 누적 contact latch와 tick event 분리, 2tick terminal의 FINISH_CONFIRM→반환 후 DONE을 확인했다. negative는 누락·5번째 callback·nonterminal partial·잘못된 시각/owner·bool index/clock/count·source binding·봉인된 post/phase/grass/반환값 변조·overwrite·NaN을 거부했다. callback 또는 native writer 예외에서도 원 tracker 메서드를 복원하고 해당 session/ticket을 실패 상태로 남겼다.

첫 fake 검증은 tracker tuple이 JSON에서 list로 복원되는 차이를 잡아 실패했다. 최초 소스·plan·sidecar·실패 기록을 private에 보존하고 JSON 구조 정규화만 고친 뒤, **같은494 내부의 두 번째 static validation**으로31개를 통과했다. 물리 재시도는 없다. 첫 실패 worker의 CPU/wall은 미기록이며, 성공 worker 수치에 포함했다고 주장하지 않는다.

성공 validation의 CPU **1.742582111초**, wall **2.201340628초**, 최대 RSS **74,448,896B**다. immutable synthetic receipts는81파일·324,318B이며 출력 상한 안이다. 실제 잔액 **26,101**, reserve **84,000/사용0**, best **13.640초**와 종료 **2026-10-20 19:01:55 KST**는 유지한다.

## 체크포인트의 한계

생산 callback/tap 연결과 fake 입출력 계약 검증까지 완료했다. 실제 ObserveMixin.one의 전체 lifecycle, 실제 raw native/model source 일치·warm continuation·history·자원 sizing은 아직 자격이 없다. 이번 단계는 새 native/reset/model 적분을 실행하지 않았고, 체크포인트 검토 전 후속 물리 실행은 금지 상태다. 과거492/493 증거를 소급 승격하지 않는다. 자동 후속 실행은 없다.

[집계 JSON](capture494_result.json) · [등록 계약](capture494_contract.json) · [생산 callback](capture494.py) · [fake 검증](test_capture494.py) · [검증 실행기](check494.py)
