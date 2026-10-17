# 428: 상시 planner 모델 pilot의 initial8 불안전 분기와 중단

**P는35회 현재 상태 선택을 적용한 뒤36번째 질의에서 중단됐다. 미선택 fullgas child가8행동째 경로 오차3.51m로 불안전해졌고, 기존419 receipt가 공식 finish 없이13행동 미만인 initial 결과를 표현하지 못해 첫 기술 오류 규칙으로 닫았다.** padding·horizon 변경·waiver·재시도·실제 실행은 없다.

새 C0도 부모64회 상한에서 공식 종료 미관측으로 검열됐다. 따라서 **새 C0/P 공식 모델 완주 이득은None**이다. P 부모는35회까지 안전/진행·선택 첫 모델 전이 게이트를 통과했지만 이후 완주는 관측하지 않았다. 마지막 선택의 완료 witness를 부모의 완주로 대신하지 않는다.

## 동결 범위와 비용 상한

계획 SHA-256: `36151336d0b6e7c4fefbbc331f94b73fab8f0010551b29ed5b1a22e81ffdbb7d`. 같은 알려진 root에서 C0/P를 새로 만들고 **두 모델 부모 각각 최대64회**로 동결했다. C0도64회 뒤 tail을 추가하지 않는다. 이 해석과 C0 검열 시 새 완주 이득을 계산하지 않는 조건을 시작 전에 보고했다.

최악64회 P 고유3recipe initial13+같은 child 추가308 C tail·독립 반복493,056tick, C0 양 recipe guardian13·반복13,312tick, 부모128행동512tick, 자격1132tick을 합쳐 **508,012tick/671world**다. 승인524,288tick/1024world/CPU1800초/wall2400초/적분 순차1개 안에 들었다. 준비 시간은 별도다.

적격 FIRST_LAP의 P만419를 질의하고 FINISH_CONFIRM에서는 검증된426 guardian certificate를 사용하도록 했다. guardian 증거는 planner 순위/Evidence/actual DONE 권한이 없다. 모델 부모는 실제 환경이 아니다. 세 recipe·pedal 크기·gain·horizon13·signed C·projection·경로/조향 규칙·엄격 bracket 지배와 memory/ledger 분리를 유지했다. 새 seed·path·성능 파라미터 탐색은 없다.

캐시는 사용하지 않았다. 모든 world/질의는 새로 계산했고 root state/memory/RNG/clock 및 ledger/policy digest를 보존했다. 가까운 상태나 미래 actual 기록을 선택 입력으로 쓰지 않았다. 첫 기술·정의역·fidelity·복원·독립 반복·부모/RNG/memory/ledger 오류, baseline guardian 불가 또는 비용 cap에서 전체 중단한다.

## 선행 자격

정적28개 대조가 종료 시각·phase/corridor·권한 분리·음성 대조·새 worst-case bound를 통과했다. 모델 적분 전에는0tick이었다.

그 뒤423 C0의 실제71행동과427 P12의 실제59행동 suffix를 저장 actual 명령으로 각각 독립2회 모델 재현했다. 첫13과 continuation의 body/wheel/raw hull·phase·clip flag·공식 finish가 기존 허용치를 통과했고 두 반복 signature가 같았다. 이는 고정 명령의 물리 자격이며 exact 폐루프 명령/memory 재생 주장이 아니다.

427의 실제 current query state12개도 각각2회 복원해 첫 선택 전이·phase·clip flag를 확인했다. 보유 부모·입력 memory·global RNG·불변 실제 ledger는 모든 fork 뒤 보존됐고 보유 부모의 다음 nominal 전이가 독립 모델 첫 전이와 맞았다. 자격 비용은 **1132tick/29world**다.

실제 미래 명령은 이 격리된 자격 검사에만 사용했다. 새 pilot 선택은 새 현재 모델 상태·새 모델 evidence만 사용했다. 이 자격을 새 명령 조합이나 더 큰 force 영역의 actual 자격으로 확대하지 않는다.

## 관측한 부모와 모든 선택

| 새 모델 부모 | C0 | P |
|---|---:|---:|
| 적용한 결정 / planner / guardian | 64 / 0 / 64 | 35 / 35 / 0 |
| 관측 raw ticks / 모델 경과 | 256 / 5.12초 | 140 / 2.80초 |
| 공식 finish | 없음·범위 검열 | 없음·선택36 전 기술 중단 |
| 최대 post 경로 오차 | 1.135m | 1.067m |
| 최대 raw hull 경로 오차 | 1.266m | 1.094m |
| 부모 최대 force ratio | 1.114724 | 1.407336 |
| clip / wheel samples | 6/1024 | 31/560 |
| damage / 적용 구간 safety·진행 | 0 / 통과 | 0 / 통과 |

관측 경과를 lap/남은 시간으로 쓰지 않았다. 부모99개의 선택 첫 모델 전이는 선택 child와 body/wheel/raw hull·phase·clip flag 차이0을 통과했다. 부모 state/RNG/memory와 실제 root ledger는 불변 게이트를 통과했고 branch memory는 commit하지 않았다. 부모 FINISH_CONFIRM 단계에는 이번 중단 전 도달하지 않았다.

C0는64회 모두 nominal이었다. P의 fullgas 선택은1·3·11·14번째이고 나머지2·4–10·12–13·15–35는 nominal이다. alias 규칙에 따라 nominal과 fullgas가 같은 명령인 상태는 중복 candidate로 계산하지 않았다. P의35개 전체 receipt는 저장·복원 digest와 typed selector 재계산이 일치했다.

| P 적용 선택 구간 | root 기준 선택 C nominal finish witness |
|---|---:|
| 1–2 | [251,252]ticks |
| 3–10 | [249,250]ticks |
| 11–13 | [231,232]ticks |
| 14–35 | [215,216]ticks |

추가14번째 fullgas의 현재 상태 witness 이득은[0.30,0.34]초였다. 이후35번째까지 root 기준 witness bracket 변화는 없었다. 서로 겹치는 질의 이득은 합산하지 않았고, **이 witness는 중단된 실제 모델 부모의 finish가 아니다.** 최종 정책의 후속 상쇄 여부는 미관측이다.

두 새 부모가 실제로 관측한 공통 arc70/75/80/85%의 모델 시간 차이는 각각0.18–0.22/0.36–0.40/0.70–0.74/0.88–0.92초였다. 90/95%는 공통 관측이 없어None으로 남겼다. 공식 완주 이득도None이다. 자격 replay나 과거423/427의 finish를 새 기준선의 완료로 사용하지 않았다.

## 불안전 후보와 중단 경계

35질의의 고유 candidate86개 중 완료 finish witness82개, unsafe tail4개였다. 독립 반복은 별도 비용으로 계상했다. fullgas의15·21·22·23번째 질의 tail은 각각 추가18·11·9·8행동에서 불안전해져 순위에서 제외했고 finish 시간은None이었다. 이들 분기는 부모에 선택되지 않았다.

36번째 현재 상태에서 nominal과 neutralbrake는 각각 initial13·진행 게이트를 통과했고 독립 반복도 같았다. fullgas는 **initial8에서 `path_error_over3m`**, 최대 post 경로 오차3.509848m·q2.871085로 중단됐으며 독립 반복이 같았다. 이8행동은13행동을 채운 receipt가 아니고 공식 finish도 아니므로 기존419 규약에 입력할 수 없었다.

원오류는 `partial_initial_ineligible_419_receipt_stop_without_padding`이다. 이때 baseline의 initial13은 가용했지만, 첫 기술 오류 뒤 nominal/neutral의 tail을 이어 계산하거나36번째 선택을 부모에 적용하지 않았다. unsafe8을 padding·시간 추정·유효13으로 바꾸지 않았다. 현재 child와 code·원계획·부분 비용을 보존했다.

전체 미선택 candidate까지 포함한 최대 force ratio는 **4.060392**다. 이는 부모 최대1.407336이나36번째 실패 child의2.871085와 다른 표본 범위다. 더 큰 force·새14번째 명령 조합과 이후 상태는 actual 미검증이다. 서로 다른 관측 길이의 clip 수를 안전 개선 증거로 비교하지 않는다.

## 시간·비용과 보존

| 새 모델 tick 용도 | 필수 | 독립 반복 |
|---|---:|---:|
| 자격 replay·current 복원 | 564 | 564 |
| C0 guardian | 3262 | 3262 |
| P candidate initial13 | 4608 | 4608 |
| 같은 child의 C tail | 9993 | 9993 |

자격 보유 부모4tick과 새 부모396tick을 더해 **37,254tick/337world**다. 선택36의 불완전8행동과 반복도 이 비용에 포함된다. 초기13과 tail은 같은 child에서 이어 적분했고 이전/cached 비용 재청구0이다. 예약·확정 tick 일치·미확정0, zero-time contact setup337, 최대 보유world7/적분 순차1개였다.

whole model worker CPU **129.690초**, 실행 wall **128.900초**다. CPU에는 import·source 검사·snapshot/hash/I/O·정리와 제어를 포함한다. tag별 constructor/step 시간은 전체 query 비용을 대신하지 않는다. 실행 wall은 import 이후 meter부터이고 보고/git 전체 비용은 완전 계측하지 않았다.

성공 query CPU p95/최대는 C0 0.630/0.736초, P4.232/4.337초였고 wall p95/최대는0.631/0.739초,4.257/4.383초였다. 실패 질의 비용은 전체 worker에 포함됐으며 위 성공 분포에 넣지 않았다. 실시간성을 주장하지 않는다.

정적 CPU/wall0.714/0.717초, 저장 분석3.037/3.563초, 부분 중단 진단0.712/0.714초를 분리했다. 준비 wall148.306초는 초기 해석·worst-case 설계 제외의 부분 구간이며 준비 CPU·전체 보고 비용은 미측정이다.

새 실제/reset/actor/학습/SEALED/예비/추가 유료 자원은 모두0이다. 원장v448은 연구 잔여 **28,444**·최종 예비84,000/사용0·실제 누적1,319,620을 유지한다. 공식 main·Participants·사용자 변경·296·rollback·보호 자료와420–427 전체 파일을 보존했다. HOLDOUT/SEALED를 열지 않았고 raw map/seed/state/RNG/명령·전체 receipt는 비공개 경로에만 남겼다.

## 다음 판단

이번 확장 정책의 공식 model finish가 없으므로 후속 actual gate는 열지 않았다. 다음 검토 대상은 **initial H13 이전 unsafe/inadmissible 결과를 padding이나 시간 추정 없이 표현하는 별도 정적 protocol**이다. 기존13 horizon·gain·recipe·엄격 지배를 유지하는지 새 계획에서 검증해야 한다. 이번 stage에서는 schema/selector를 바꾸거나 재개하지 않았다.

64회 범위를 넘어 C0 완료를 보고하려면 새 연구 범위 또는 과거 대조 사용을 명시해야 한다. 모델 시간·같은 자료의 witness 양성을 독립 일반화·11초 도달·픽셀296 증명으로 확대하지 않는다. 새 모델 재시도·실제 검증·자동 연장은 시작하지 않았다.

[기계 판독 결과·모든 선택·중단 분기·비용](pilot428_result.json) · [427 실제 P12 기술 재현](recovery427_result.md)
