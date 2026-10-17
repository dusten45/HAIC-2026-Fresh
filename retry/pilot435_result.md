# 435 observer/runtime 모델 검증 — parent pending 정의역에서 중단

observer/runtime 연결의 정적108개와 선행 재현·복원 게이트를 통과한 뒤 동일 root 모델 pilot을 실행했다. C0는71행동에서 공식 finish를 확인했다. P는54행동 뒤 질의55의 **기존 `Current.validate`가 pending parent의 음수 remaining path를 거부**하여 중단했다. 행동55·추가 모델 재시도·parent 규약 완화는 없었다. P parent의 official finish는 미확인이므로 전체 완료 시간 이득은 **`null`**이다.

## 새 연결과 정적 검증

`observer435.py`가 원래 Child/GuardianChild의 physics·정책 코드를 그대로 호출하면서 post-tracker tap을 연결한다. 원래 nominal은 내부 호출이면 정확히1회, prepared nominal이면 추가 호출0회이며 실행 명령을 같은 child의 stream에 기록한다. live world·controller 객체·world 번호·child label·registry가 다르면 거부한다. run plan SHA와 constructor proof, root state/memory/RNG/ledger, 명령열,28개 semantic source/geometry hash 항목을 연결했다. tracker·physics·controller·selector·fixed geometry·observer/capture가 source manifest에 포함된다.

post-update 시각·hull·tracker를 같은 raw tick의 기존 preclip tire/grass·pre-world hull, contact/collision과 묶었다. 원래 metrics와 observer의 물리 사유 집합이 다르면 중단한다. H13은13번째 행동 직후, 다음 nominal 준비 전에 전체 snapshot·memory/RNG/ledger·raw/action 기록을 저장하고 readback한다. 계속할 planner child마다 별도 불변 initial-boundary와 continuation-final을 두며, continuation은 봉인한 같은 world/stream만 시작할 수 있다. initial 상태가 이미 종료된 기존 양성은 원래 Evidence 경로를 유지한다.

pending H13의 후속 공식 확인에는 `Completion434`를 사용한다. 이벤트 시각은 initial raw 기록에서, 확인 시각과 추가 비용은 tail 기록에서 얻는다. 다른 child/event·취소·교체·unsafe/censored는 완료 자격을 얻지 않는다. unsafe/censored pending용 `UnfinishedPending435`도 구현해 초기 안전·진행 증거와 final 기록을 유지하되 시간은 항상 `null`, 완료 witness는 false다. 이 receipt에도 actual 실행/DONE/승격 권한은 없다.

최종 정적 **108개 모두 통과**했다. 기존434의102개와 live identity·unsafe pending/공식 raw event 동반 시 시간 거부·wire 변조·source/clock/damage/proof 거부 등을 포함한다. 모델/environment 생성자는 차단·계수했고0이었다.

적분 전 복구 이력은 별도로 보존했다. 첫 정적 실행은 합성 polygon의 중복 closing vertex가 길이0 segment를 만들어106개에서 error1로 중단했다. 실제 geometry나 strict 검증을 바꾸지 않고 중복 꼭짓점만 제거한 후108개를 통과했다. 이어 H13 저장 시점을 행동13 직후로 보완하고108개를 다시 통과했다. 원계획·원소스·실패/통과 기록을 비공개 `first-static-*`, `pre-model1-*`로 보존했다. 정책·물리·임계값·예산 변경은 없었다. 모델 시작 이후에는 코드를 수정하지 않았다.

최종 계획 SHA256: `28c0934a02db56083d1b9983518f424fea47c2ebb7e2a6848899f5d886f864ec`.

## 모델 선행 게이트와 관측 검증

observer를 켠 저장423 C0의71행동/427 P의59행동을 각각 독립2회 전체 재현했다. 427의 실제 상태12개를 각각 두 번 복원해 첫 전이를 검사했고 pending nominal2회·held parent 검증도 통과했다. body/wheel/raw hull·phase·clipping·공식 finish와 parent/memory/RNG/actual ledger 불변을 확인했다.

모든 해당 replay/restore의 rows·최종 physical snapshot·controller memory가 **433의 observer 없는 저장 결과와 정확히 같았다**. 관측 post/action stream도 전체 replay2쌍·restore12쌍·pending1쌍, 총15쌍이 정확히 같았다. 비교는 저장 reference와 수행해 추가 unobserved world를 만들지 않았고, 선행 비용은 기존과 같은 **1,134 ticks /32 worlds**였다. 이 자격은 저장된 실제 상태/명령에 한정되며 이후 새 모델 상태의 실제 안전·일반화를 인증하지 않는다. 알려진 DEV root만 사용했고 새 HOLDOUT/SEALED 평가는 없다.

모델 전체에서458개 live world stream,40,763개 post raw ticks,10,344개 action records를 대조했다. raw 관측 수가 실제 meter tick과 일치했다.192개 continuation initial-boundary와192개 별도 final,318개 일반 H13 관측 기록을 확인했다. 모두 source manifest·constructor proof·같은 child/봉인 key에 연결된다.

새 질의42 nominal의 required/repeat 두 child는 H13 pending을 각각 봉인하고 같은 이벤트의 후속 공식 확인을 검증했다. H13 controller phase는 관측대로 `FIRST_LAP`, remaining path는 **−0.1803092504m**, initial52 raw ticks와 tail1 raw tick이었다. 완료 bracket은 query-root 대비 event **[51,52]**이며 confirmation은 raw53이다. 이 증명으로 nominal을 선택했지만 child 미래 완료를 parent 완료로 바꾸지 않았다. 이는 새435의 prospective 증거이며 **433의 빠진 H13 tracker snapshot을 소급 인증한 것이 아니다**.

저장된54개 선택 receipt의 digest·context·선택을 재검증했다. C0 첫71행동과 P 첫41행동의 rows 및 선택은433과 정확히 같았다. 실제 모델에서 새 pending 완료 receipt는 대표1개(독립 반복 capsule2개)를 관측했다. unsafe/censored pending 특수 receipt는 이번 모델에서 발생하지 않아 그 경로의 검증은 정적 수준으로 남는다. 일반 unsafe tail4개와 early 물리 부적격16개에는 모두 시간 `null`을 유지했다.

## 최초 모델 오류: parent의 현재 pending 상태

P 행동54 이후 tracker는 candidate를 현재 raw 시각에 등록했고 departed/from-back/qualification 조건도 갖췄지만 아직 `finish_time_s=None`이다. 다음 nominal을 준비하며 controller phase는 `FIRST_LAP`에서 `FINISH_CONFIRM`으로 갱신됐다. 그때 Current의 remaining path는 **−0.1803110304m**, `official_finished=False`, model ledger `done=False`였다.

원래 `Current.validate`는 phase와 관계없이 미완료 상태의 음수 remaining path를 거부한다. 따라서 `ContractError: past_first_lap_path_domain`에서 즉시 중단했다. source/parent routing을 바꾸거나 음수를0으로 자르지 않았다. 질의55 후보 평가·선택·parent step은 없고, 전체 state/memory-before/after-nominal/RNG/ledger와 pending tracker를 별도 context-stop 기록으로 보존했다. nominal 준비만 있었으며 physics 적분55는 없었다.

이 오류는433의 child endpoint 표현과 다른 **parent routing 범위**다. 이번 observer gate나 endpoint 완료 증명이 parent 자체의 DONE를 허용하는 근거가 되지 않는다. 완료 확인을 생략하거나 pending 시각만으로 P의 lap time/전체 이득을 산출하지 않았다.

| 항목 | C0 모델 | P 모델 |
|---|---:|---:|
| parent 행동 | 71 | 54 |
| planner / guardian 완료 선택 | 0 /71 | 54 /0 |
| 결과 | 공식 finish 확인 | 현재 pending·정의역 중단으로 검열 |
| root 이후 공식 이벤트 구간 | 5.62–5.64초 | 미확인, `null` |
| 관측 parent raw ticks | 283 | 216 |
| 최대 post 경로 오차 | 1.13470m | 2.66505m |
| 최대 힘 비율 | 1.11472 | 2.07261 |
| clipped wheel samples | 6 /1,132 | 107 /864 |

C0 확인 step 종료5.66초와 event 구간을 구분했다. **P planner64 이후 guardian 전환은 도달하지 않아 관측되지 않았다.** parent 첫 전이125개는 선택 child와 허용 오차 내에서 일치하고 clipping 불일치는0이었다. FINISHED candidate witness121개는 중첩 모델 질의 집계이며 독립 parent 완주121개가 아니다.

공통 arc70/75/80/85/90/95%의 P 부분 이득 구간은 각각0.18–0.22 /0.36–0.40 /0.70–0.74 /0.88–0.92 /0.98–1.02 /1.22–1.26초다. 합산하거나 P 전체 완료/11초대 성과로 대체하지 않는다. 새 실제 주행은 없다.

## 비용과 보존

최악 산술은 **519,038 ticks /882 worlds**를 시작 전에 재확인했다. observer와 저장 reference 검증의 추가 적분/world는0이고 모든 callback·join·snapshot·봉인·hash·IO·검증을 worker cap 안에 포함했다. 한도는524,288 ticks/1,024 worlds/CPU1,800초/wall2,400초/순차 적분1개다.

실제 모델 지출은 **40,763 ticks /458 worlds**, worker CPU **586.330초**, 실행 wall **585.200초**다. 미확인 tick0, 최대 보유 world7개·동시 적분1개로 모두 cap 이내다. 정적 세 실행 합계 CPU30.986817초/wall35.272994초와 저장 분석 CPU8.758633초는 별도다. 준비·정리·보고·Git 시간은 완전 계측하지 않았다. 과거 비용을 다시 청구하지 않았다.

물리와 선택이 같은 historical prefix의 query-region CPU도 기록했다. C0 71결정은 old433 **67.583초→435125.532초**, P 첫41결정은 **164.768초→370.792초**였다. 이 영역에는 observer/봉인/IO/검증을 포함하고 parent step은 제외한다. 같은 run의 통제된 overhead benchmark는 아니므로 순수 observer 비용 비율로 단정하지 않는다. CPU cap 안에 실측 비용을 모두 기록했으며 worst tick 상한 전체를 CPU 한도 내에 반드시 끝낸다는 보장은 하지 않는다.

새 실제 행동/reset·actor·학습·SEALED·reserve·별도 유료 자원 사용은 모두 **0**이다. v455 연구 잔여 **28,444**, 누적 실제 **1,319,620**, reserve **84,000/사용0**을 유지했다. 기존 기록5,615개와 동결 source·보호 archive, 생성 전458개/첫 적분457개/질의 전125개/parent 전이 전125개 증거 연결을 확인했다. 433 원실패와434 정적 보고서는 그대로다. 원문 state·지도·seed·RNG·명령/receipt는 비공개 공간에 보존하며 공식 Participants/main 및 백업은 변경하지 않았다.

다음 장애물은 **현재 parent pending을 기하학적 remaining path와 구분하는 별도 routing 계약**이다. 이번 실행은 여기서 종료하며 기존 `Current.validate`를 우회하거나 추가 모델/실제 실행으로 자동 전환하지 않는다. 종료는2026년10월20일19:01:55 KST이며 자동 연장은 없다.

[기계 판독 결과](pilot435_result.json) · [434 정적 설계와 당시 한계](boundary434_result.md) · [433 원실패](pilot433_result.md).
