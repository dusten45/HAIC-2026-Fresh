# 422: 현재 상태 planner의 실제 13행동 전이·clipping 보정

**C0/P 두 arm을 각각 한 번 실행해 실제 prefix 118행동과 suffix 13행동을 완료했다.** P는 실제 현재 상태에서 419 planner를 세 번 직접 재계산해 `fullgas → nominal → fullgas`를 선택했다. 이후 10행동은 기존 C0 guardian이 모두 nominal을 선택했다. P의 실제 force ratio 최대 1.407334와 clipping 29/208 wheel 표본을 관측했고, 매 선택 첫 전이와 일치 명령 구간의 body/wheel/raw hull·clip flag 대조를 통과했다. **이 증거는 해당 연속 선택 조합의 실제 13행동에 한정된다.** 421의 긴 모델 finish 이득 0.62–0.66초는 여전히 실제 결과가 아니다.

## 실행 전 계약과 선행 게이트

같은 418 초기 상태·history118·signed C·projection·gain·horizon·recipe·419 선택 규칙을 유지했다. C0와 P의 실제 초기 full state/RNG/pixels와 fork의 controller 계산 전후 memory·nominal이 저장된 418 및 두 arm 사이에서 같았다. 실제 prefix의 sensor/command/memory/post와 source body/wheel/raw hull도 통과했다. root의 nominal/fullgas 13행동은 질의 중 새 모델과 저장 418 실제 전이로 다시 대조했다.

실행 전 정적 검사 9개는 실제 문맥 gate, 실제/예측 ledger 분리, 모델 관측의 실제 commit 거부, 저장 421 receipt 세 개의 typed 선택 재계산, 실제 문맥 전체 receipt 저장·복원, full query 비용 일정을 통과했다. 정적 적분은 0이었다. 계획 SHA-256: `b6b390931ddef54c10068b7d21f39cb8ba42fead09c2d8cc991472f3bf9fb5a0`.

첫 안전·fidelity·복원·정의역·숫자·부모/RNG·비용·기한 오류와 guardian 둘 다 불가에서 전체 중단하도록 사전 동결했다. 실제 상한은 400 wrapper/reset2/모델 제외 CPU90초/wall180초, 모델 전체 상한은 32,768 ticks/128 worlds/CPU150초/wall240초/순차 적분1개였다. 새 window·gain·horizon·recipe·재주행·실제 전체 lap은 허용하지 않았다.

## 실제 결과와 모델 차이

| 지표 | C0 | P |
|---|---:|---:|
| 실제 prefix / suffix | 118 / 13 | 118 / 13 |
| 첫 세 현재 상태 선택 | nominal ×3 | fullgas → nominal → fullgas |
| 이후 guardian neutral 개입 | 0 | 0 |
| 같은 기존 arc+30m exit | 0.50–0.52초 | 0.44–0.46초 |
| 실제 최대 force ratio, suffix | 0.963277 | 1.407334 |
| suffix clipped wheel samples | 0/208 | 29/208 |
| damage / 실제 진행 deadline | 0 / 통과 | 0 / 통과 |
| 실제 공식 finish 관측 | 없음 | 없음 |

공통 국소 exit의 실제 이득은 raw bracket 차이 **[0.04,0.08]초**다. raw 20ms crossing bracket을 사용하고 보간하지 않았다. 이 값은 418의 국소 결과와 같은 bracket이며 이번 추가 선택 조합의 더 큰 국소 시간 이득으로 해석하지 않는다. 417의 보장 0.08초 gate 미달 판정도 변경하지 않는다. 짧은 보정의 종료를 lap 완료 또는 DNF 판정으로 쓰지 않는다.

P 세 실제 질의의 선택과 gain bracket은 421과 일치했다. 첫 질의 [0.58,0.62]초, 두 번째 bracket 중첩으로 nominal 유지, 세 번째 [0.02,0.06]초였다. 이들은 각 실제 현재 상태에서 계산한 **모델 witness** 차이다. 421 선택 기록은 질의 완료 뒤 비교용으로 읽었으며 명령 재생에 사용하지 않았다. 전체 receipt 세 개의 typed selector 재계산도 일치했다.

26회 실제 질의 모두 접근 가능한 full parent·controller memory·global RNG·실제 진행 원장을 보존했다. 분기 memory는 부모에 commit하지 않았고 실제 post 관측만 실제 ledger에 반영했다. 모든 실제 선택 첫 전이 26개에서 body/wheel/raw hull·phase·finish metadata·raw tick 계약을 통과했으며 clip flag 차이는 0이었다. P 첫 clipping은 history 기준121번째 행동의 raw3, rear wheel2였다.

| 매 선택 첫 전이의 최대 오차 | C0 | P |
|---|---:|---:|
| body 위치 | 7.63e-6m | 1.91e-6m |
| body 속도 | 1.37e-5m/s | 7.65e-6m/s |
| wheel omega | 1.01e-5rad/s | 1.15e-5rad/s |
| force ratio | 3.63e-6 | 3.13e-6 |
| raw hull origin 위치 | 3.82e-6m | 1.91e-6m |

기존 허용치는 변경하지 않았고 별도로 exact clip flag 차이 0을 검사했다. raw time 오차는 0이었다. 현재 선택의 initial13 witness를 후속 실제 명령이 일치하는 동안 대조한 누적 비교는 C0 91/P 69개다. 이는 겹치는 witness 대조 수이며 독립 실제 시행 수가 아니다.

P의 세 번째 선택에서 첫·둘째 witness가 예상한 nominal 대신 fullgas가 들어갔다. 해당 두 witness는 변경 전까지만 대조하고 비교를 종료했다. 이는 guardian override가 아닌 재계산된 정책 선택 차이이며, 세 번째 새 선택의 첫 전이와 새 witness의 후속 일치 구간은 계속 검사했다. guardian 명령 변경은 관측되지 않았다. 별도로 저장 421 부모의 첫 13행동과 실제 suffix 13행동도 양쪽 모두 명령 오차 1e-6 이내·body/wheel/raw hull 허용치·clip flag 차이 0을 통과했다. P의 이 대조에서 최대 body 위치 오차 8.53e-6m, 속도 2.24e-5m/s, force ratio 오차 6.77e-6이었다.

## 실제/모델 비용과 원장

| 모델 용도 | 필수 ticks | 독립 반복 ticks | worlds 합계 |
|---|---:|---:|---:|
| C0/P guardian initial13, 23질의 | 1196 | 1196 | 46 |
| P planner initial13, 3질의×3recipe | 468 | 468 | 18 |
| 같은 planner child의 C tail | 1825 | 1825 | 위 world 재사용 |
| 합계 | 3489 | 3489 | 64 |

모델 **6,978 ticks/64 worlds**, 예약·확정 tick 일치/미확정0, zero-time contact setup64, 최대 보유world6/적분 순차1개다. root 재자격 비용은 해당 질의에 포함된다. 실제 부모 262행동(공통 prefix236+suffix26)/reset2를 따로 계상했고 인위적 모델 부모 적분은 0이다. 이전 cached source 비용은 재청구하지 않았다.

모델 CPU **26.534초**(import 포함), 모델 질의 wall **26.013초**다. 문맥 캡처·hash·receipt I/O·정리도 모델 구간에 포함된다. tag별 측정은 constructor/step 구간이므로 전체 비용과 혼동하지 않는다. 모델을 제외한 실제 CPU/wall은 **14.812/14.799초**, worker 전체 CPU/실행 wall은 **41.413/40.879초**였다. 최종 결과 직렬화·보고·git 비용은 완전히 포함하지 않는다.

측정된 준비 wall 구간은 111.538초이나 초기 읽기·설계가 제외되며 준비 CPU는 미측정이다. 정적 사전 검사 CPU/wall 0.055/0.057초, 저장 분석 CPU 약0.291초를 별도로 기록했다. 준비·보고 비용을 모델 실행 비용에 숨기지 않았다.

새 실제 사용 262만 차감한 원장 v442: **연구 잔여29,356 + 최종 예비84,000 + 실제 누적1,318,708 = 운영 상한1,432,064**. 예비 사용·actor·학습·SEALED·추가 유료 자원은 0이다. 알려진 DEV root만 사용했고 HOLDOUT/SEALED는 열지 않았다. 420/421 전체 파일 manifest, 공식 main·Participants·기존 사용자 변경·champion296·rollback·보호 자료를 보존했다. map/seed/state/RNG/명령 원자료/전체 receipt는 비공개 경로에만 남겼다.

## 남은 경계

새 연속 선택 조합의 실제 13행동에서 q≈1.407 clipping 영역을 보정했다. 같은 최대 q를 보았다는 사실만으로 그 뒤 긴 tail의 모든 상태·진행·guardian·finish가 검증되지는 않는다. 421의 0.62–0.66초 긴 모델 이득, 실제 전체 lap, 픽셀 정책·질의 실시간성·독립 일반화는 미검증이다. 이 단계는 닫았으며 추가 실험·재주행·자동 연장은 시작하지 않는다.

[기계 판독 결과](calibrate422_result.json) · [421 모델 비교](pilot421_result.md) · [419 고정 선택 규칙](planner419_result.md) · [418 이전 실제 보정](calibrate418_result.md)
