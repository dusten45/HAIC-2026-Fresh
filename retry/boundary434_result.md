# 434 종료 경계 정적 설계 — 최종102개 통과, 적분0

공식 이벤트 시각, 공식 확인 시각, H13의 signed geometric remaining path를 분리한 prospective 구현을 추가했다. 최종 정적 suite **102개가 통과**했다. 모델 world 생성·물리 적분·실제 주행은 시작하지 않았다. 433은 계속 계약 중단이며, 빠진 H13 전체 tracker snapshot을 소급 복원·인증하지 않는다.

## source 검토와 분리 원칙

`core/finish_line.py`는 qualification 이후 뒤에서 finish 영역에 진입한 상태에서 중앙선을 넘으면 `candidate_crossing_time_s`를 기록한다. 영역의 앞 경계까지 나간 후 그 candidate 시각을 `finish_time_s`로 확정한다. 따라서 **event 시각과 confirmation 시각은 다를 수 있다**. `remaining_path_m`의 부호는 이 tracker의 공식 종료 판정에 쓰이지 않는다.

`signed417_executor.py`는 physics보다 먼저 `act()`에서 controller phase를 갱신한다. 해당 행동의 physics 중 crossing이 새로 생기면 H13 controller memory는 아직 `FIRST_LAP`이고 post-world tracker는 pending일 수 있다. phase를 소급해 `FINISH_CONFIRM`으로 덮어쓰지 않는다.

기존 `planner419.TerminalVector.validate`는 음수 remaining path를 거부하되, initial 구간 안에서 이미 official finish가 확인된 경우에만 예외를 허용한다. 이는 기하 부호를 곧바로 완료로 판정하는 코드는 아니지만, **종료 vector 정의역의 예외를 공식 확인 여부 및 tail0에 묶고 있다**. 이 표현이 433의 H13 음수·tail1 확인을 받지 못했다. 기존 코드는 수정하지 않았다.

## 구현한 prospective 계약

[boundary434.py](boundary434.py)는 순수 기록 검증과 별도 완료 타입을 구현한다. [capture434.py](capture434.py)는 별도 불변 기록과 continuation barrier, source tracker의 post-update 관측 tap을 제공한다. integrator·act·step·DONE를 호출하는 코드는 없다.

- H13 전체 snapshot(physical·tracker·elapsed raw steps), end13 state/memory digest, controller phase, 전체 RNG bytes·digest, model ledger, root/context·policy·recipe·실행/nominal 명령열·source versions, initial raw/action records와 검증 게이트를 봉인한다. signed geometry는 원래 값을 보존한다.
- **저장과 pending 인증은 별개**다. 정상 non-pending H13도 continuation 전에 initial-boundary 파일로 저장한다. 음수인데 등록 crossing이 없는 기록은 보존하지만 continuation을 거부한다. 음수가 곧 완료나 안전을 의미하지 않는다.
- pending 인증은 root의 과거 candidate/finish를 재사용하지 않는다. candidate는 query root 이후 H13 이내의 정확한 raw tick에 있어야 하고 qualification≤candidate≤H13 시각, departed/from-back, 기존 corridor·velocity 조건을 만족해야 한다. 공식 tracker 알고리즘을 관측 post-world samples에 재생해 snapshot과 정확히 비교한다.
- 관측된 controller phase와 endpoint tracker 분류를 각각 보존한다. 각 행동의 phase는 그 행동 **이전** tracker에 대한 source `act()` 순서와 맞아야 한다. 마지막 행동 도중 생긴 pending을 controller가 이미 보았다고 가정하지 않는다.
- 모든 반복은 별도의 child identity와 `*-initial-boundary-private.json`을 갖는다. 봉인·readback 검증 전에는 continuation을 시작할 수 없다. `*-continuation-final-private.json`은 별도 파일로 보존하며 initial 기록을 덮어쓰지 않는다. unsafe/censored final도 보존하지만 완료 증명은 발급하지 않는다.
- 완료 타입은 **같은 child·root/context·policy·recipe/명령열·ledger·source version·봉인 key**에 연결된 후속 기록만 받는다. 원 pending의 취소·교체, 다른 crossing, 다른 child, unsafe/censored, 시각 불일치는 거부한다. 확인된 tracker의 event가 원 candidate와 같을 때에만 이벤트 raw tick으로 bracket을 만든다.
- initial 안전·진행·memory/ledger는 initial 기록으로 검증한다. 뒤의 finish로 과거 안전이나 미달한 initial goal을 구제하지 않는다. 완료 타입에도 실제 parent 실행·DONE·승격 권한은 없다. 기존419 chooser를 그대로 호출하여 엄격 bracket·baseline 선택 규칙을 유지한다.

단순 음수 허용, 0 clamp, epsilon, event 시각을 confirmation 시각으로 대체하는 처리는 없다. 시각은 source의 raw 1/50 증가 및 정수 raw clock과 정확히 대응해야 한다.

명시적 **합성 정적 예시**는 다음과 같다. 실제 physics 결과가 아니다.

| 상태 | H13 마지막 raw tick | 후속 확인 raw tick |
|---|---:|---:|
| root 대비 raw tick | 52 | 53 |
| 관측 controller phase | FIRST_LAP | FINISH_CONFIRM |
| tracker | 등록 pending, 미확인 | 동일 event 공식 확인 |
| geometric remaining | −0.18m(원값) | 완료 판정 근거로 사용하지 않음 |
| 완료 bracket | `null` | event 기준 **[51,52]** |
| initial/continuation 관측 비용 | 52 ticks /13행동 | 1 tick /1행동 |
| 실제 parent DONE 권한 | false | false |

확인 시각은 raw53이고 이벤트는 raw52다. 두 시각과 initial/tail 관측 수를 따로 저장한다. 개별 boundary의 실제 CPU/wall과 meter 비용 연결은 아직 모델에서 측정하지 않았다.

## 정적 대조와 보존

최종 **102개, 실패0/error0**다. 기존74개와 새28개를 포함한다. 정확한 H13 경계 및 H13 내부 pending, phase 지연/잘못된 phase, crossing 없는 진짜 음수 기록, 확인 실패/취소/다른 event/다른 child, root 이전 이벤트, missing/위조 snapshot, 명령·source·RNG·ledger·시각 불일치, initial/continuation 손상·경로/접촉 위반, unsafe/censored, 미래 goal 구제 거부를 검사했다. 두 반복의 initial/final 파일4개를 구분하고 중복 봉인·continuation 시작·덮어쓰기도 거부했다.

기존433의 정상·단일/복합 물리 부적격을 포함한 **41개 receipt의 선택·bracket과 root/memory/ledger가 그대로**였다. 원래 initial 안에서 종료 확인된 양성 사례와 source tracker tap의 반환값·instance schema도 유지됐다. tap은 원래 update를 한 번 호출하고 관측하며 예외 때 원래 연결을 복원한다. synthetic positions로 tracker 계산을 검증했을 뿐 Box2D나 차량 물리를 적분하지 않았다. 모델/environment 생성자는 차단·계수했고0이었다.

개발 중 97개 및 별도4개를 먼저 통과했다. 이후 일반 non-pending H13 저장을 보완해 최종102개를 다시 검사했다. 이전 소스3개는 비공개 `stage434/revision1-sources/`에 원계획/통과 기록과 함께 보존했다. 총203 test invocations를 별개의203개 증거로 세지 않는다. 최종 계획 SHA256은 `d7f35ce467d2f5937d2a1c8fb050c24e35d6ae1effd904fe6d99f77418acfb82`다.

세 정적 실행 합계 CPU **17.124308초**, wall **17.703964초**다. 준비·정리 예시·보고·Git 시간은 완전 계측하지 않았다. 새 모델 ticks/worlds·실제 행동/reset·actor·학습·SEALED·reserve·유료 자원 사용은 모두 **0**이다. v454 연구 잔여 **28,444**, 누적 실제 **1,319,620**, reserve **84,000/사용0**을 유지했다. 기존 기록5,590개·동결 source·보호 archive를 대조했고 433 원실패/보고서는 그대로다. 원문 state·RNG·지도·seed·receipt는 비공개 공간에 유지하며 공식 Participants/main과 백업을 수정하지 않았다.

## 부족한 근거와 다음 모델 검증 계획

**434는 정적 통과이며 모델 실행 승인이 아니다.** source 알고리즘 재생과 digest는 기록의 일관성을 확인한다. physics 진위를 증명하지 않으며, `LIVE` scope 이름이나 GateProofs를 임의로 true로 쓰는 것만으로 자격이 생기지 않는다. 다음의 근거가 먼저 필요하다.

1. 별도 계획에서 authority의 source versions를 tracker·physics·controller·selector·fixed geometry·새 observer/capture 코드의 동결 manifest에 연결한다. post-update tap에 기존 preclip tire/grass·raw/path/contact·행동·RNG·ledger 자료를 정확히 결합해야 한다. tap 자체만으로 기존 안전 검사와 같다고 주장하지 않는다. 현재 child_id·봉인 key 결합은 정적으로 검사했으며, live world 식별자와 observer/명령 stream을 같은 객체에 등록하는 연결도 다음 gate에서 검증해야 한다.
2. observer를 켠 423 C0/427 P 전체 명령 독립 반복, 12개 실제 상태 복원, pending 확인·held parent/메모리/RNG/ledger 검증을 먼저 수행한다. 기존 미관측 observer 결과/저장 raw와 body/wheel/hull/phase/finish를 대조해야 한다. 기본 선행 비용은1,134 ticks/32 worlds이나 추가 적분을 요구하면 상한을 다시 계산해야 한다.
3. 모든 계속할 child의 H13을 독립 불변 파일에 봉인하고 readback한 뒤 같은 child만 continuation한다. unsafe/censored pending은 final 기록과 시간 `null`을 유지하는 runtime 후보 경로가 필요하다. 현재 runner에는 새 API를 연결하지 않았고 이 routing도 모델 검증되지 않았다.
4. **Current.validate 및 parent 라우팅은 원래대로다.** parent 자체가 pending이면서 음수 remaining이면 현재도 거부된다. endpoint 성공은 parent 처리의 자격이 아니다. 이 범위는 별도로 검토하거나 해당 상태에서 중단해야 하며 자동 완화하지 않는다.
5. 위 선행 조건을 만족하고 별도로 승인받은 뒤에만 동일 root의 C0≤80, P FIRST_LAP planner≤64→guardian만 사용하여 전체≤100 모델 pilot을 제안한다. 기존 H13/recipe/gain/tail/strict bracket을 유지한다. 캡 산술은 **519,038 ticks/882 worlds**, cap **524,288 ticks/1,024 worlds/CPU1,800초/wall2,400초/순차1개**다. observer/snapshot/hash/IO 오버헤드는 whole-worker cap 안에서 실측하며 아직 보장되지 않았다. 최초 모델 기술/정의역/복원/재현 오류에는 중단한다. 실제·학습·SEALED·예비 전환은 없다.

종료는 **2026년 10월 20일 19:01:55 KST**이며 자동 연장은 없다. [기계 판독 결과·제안](boundary434_result.json) · [433 원실패](pilot433_result.md).
