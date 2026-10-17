# 423: 실제 C0/P carry에서 공식 랩 0.640초 이득

**같은 초기 상태와 history118에서 C0/P를 각각 한 번 공식 종료까지 실행했다. C0 15.080초, P 14.440초로 실제 공식 랩 차이는 0.640초, raw crossing bracket 차이는 [0.62,0.66]초다.** 두 arm 모두 손상0·진행·안전·선택 첫 전이 fidelity를 통과했다. 이 결과는 알려진 DEV root의 특권 상태 기반 paired carry 한 번이다. 픽셀296·독립 일반화·실시간 실행의 증거로 확대하지 않는다. 새 독립 실험 없이 닫았다.

## 동결한 실행 계약

423 시작 전에 계획과 비용을 동결했다. SHA-256은 `5c38e6593e4808c37e8ae0314644bd194979128a1ec6d447853b0df8ca7bcc3a`다. 기존 초기 상태·history118·signed C·419 selector·gain·recipe·horizon·projection·진행 원장을 유지했다. C0는 기존 nominal13/독립 반복 guardian을 사용하고 nominal이 불가할 때만 기존 neutral13/독립 반복을 검사한다. P는 첫 세 **실제 현재 상태**에서 419의 세 recipe/같은 child의 C nominal tail/독립 반복을 재계산한 뒤 나머지는 같은 C0 guardian만 사용한다. 이후 새 planner 구간은 없다.

첫 안전·진행·fidelity·복원·정의역·부모/RNG·비용·기한 오류 또는 guardian 둘 다 불가에서 남은 arm까지 중단하도록 했다. 실제 상한620 wrapper/reset2/모델 제외 CPU120초/wall240초, 모델 전체65,536 ticks/1000 worlds/CPU240초/wall360초, 적분 순차1개와 기존 arm당308행동 상한을 적용했다. 재주행·새 window·gain·horizon·recipe는 없었다.

정적 사전 검사14개가 실제 문맥, 실제/예측 ledger 분리, 모델 관측의 실제 commit 거부, 저장 receipt 선택 재계산·복원, 비용 일정과 기존 종료 경계를 통과했다. planner의 FIRST_LAP gate는 첫 세 선택에만 적용하며 기존 guardian의 FINISH_CONFIRM 제어 법칙은 유지한다. 저장된 정상 partial finish와 미래 finish timestamp 거부, 공식 종료 후 DONE도 정적으로 검사했다. 이 사전 검사의 실제/모델 적분은0이었다.

## 422 재현과 실제 정책

두 arm의 초기 full state/RNG/pixels와 fork의 controller 계산 전후 memory·nominal이 저장422 및 두 arm 사이에서 일치했다. prefix118 및 첫 suffix13의 sensor·command·memory·body·wheel·raw hull·clip flag·finish metadata는 저장422와 **정확히 같았다**. 각 131번째 행동 직후의 full physical state/RNG/controller memory/pixels도 저장422의 종료 snapshot과 일치했다.

P는 실제 재계산으로 `fullgas → nominal → fullgas`를 선택했다. 세 receipt의 저장·복원과 typed selector 재계산도 일치했다. 421의 선택 기록은 계산 후 비교용으로만 읽었고 명령을 재생하지 않았다. 이후 C0/P의 새 guardian neutral 개입은 모두0이었다. 공통 prefix에는 이전 history의91번째 neutral 명령이 이미 포함되어 있다. 이를 새 suffix 개입0과 혼동하지 않는다.

실제 suffix 질의 C0 71/P63, 합계134회에서 접근 가능한 full parent·controller memory·global RNG·실제 진행 원장이 질의 전후 보존됐다. 분기 memory는 부모에 commit하지 않았다. 실제 관측만 실제 ledger에 반영했다. 각 실제 선택 첫 전이134개는 body/wheel/raw hull·controller phase·finish metadata·raw tick 계약을 통과했고 clip flag 차이는0이었다. 초기13 이후 continuation 첫 전이는 C0 58/P50개다.

| 실제 종료 지표 | C0 | P |
|---|---:|---:|
| 전체 실제 wrapper 행동 | 189 | 181 |
| root 이후 suffix / 첫13 이후 continuation | 71 / 58 | 63 / 50 |
| 공식 crossing 랩타임 | 15.080초 | 14.440초 |
| 공식 crossing raw bracket, reset 이후 | [753,754] | [721,722] |
| root 이후 남은 crossing bracket | 5.62–5.64초 | 4.98–5.00초 |
| 확인까지 실제 raw ticks | 755 | 722 |
| 마지막 wrapper의 정상 partial raw ticks | 3 | 2 |
| damage / 새 suffix neutral 개입 | 0 / 0 | 0 / 0 |
| 전체 실제 post 경로 오차 최대 | 1.379m | 1.379m |
| suffix raw hull 경로 오차 최대 | 1.266m | 1.340m |

공식 crossing timestamp를 관측한 raw clock에 정확히 대응시켰다. C0는 crossing 뒤 한 raw tick이 더 지난 시점에 wrapper가 종료를 확인했다. 이 늦은 확인 시각15.100초를 공식 랩타임으로 쓰지 않았다. P는 공식 crossing과 확인 시각이 같았다. 두 arm 모두 공식 종료 후 controller DONE을 확인했다. 미완료·검열 랩 추정은 없었다.

## 국소 이득의 후속 유지

실행 전에 고정한 같은 원래 arc marker와 기존 arc+30m exit의 raw20ms crossing bracket을 사용했다. 보간·참조 clock·남은 거리/속도 추정은 쓰지 않았다.

| 같은 경계에서 P의 실제 시간 이득 | bracket |
|---|---:|
| 기존 국소 arc+30m exit | 0.04–0.08초 |
| 원래 arc70% | 0.14–0.18초 |
| 75% | 0.22–0.26초 |
| 80% | 0.38–0.42초 |
| 85% | 0.46–0.50초 |
| 90% | 0.50–0.54초 |
| 95% | 0.60–0.64초 |
| 공식 finish | 0.62–0.66초 |

관측한 공통 경계에서 국소 이득은 상쇄되지 않고 공식 종료까지 남았다. 이제 이 실제 pair의 finish 이득을 보고할 수 있지만 421의 원래 모델 결과 자체를 실제 기록으로 바꾸지는 않는다. 417의 별도 국소 보장0.08초 gate 판정도 변경하지 않는다.

원래 421의 긴 witness와 명령 차이가 기존1e-6 허용치를 처음 넘은 지점은 C0 행동166(차이1.013e-6), P 행동170(1.326e-6)이었다. 양쪽 모두 현재 guardian은 nominal이었으며 neutral override는 아니었다. 이 지점부터 원래 witness의 명령 일치와 실제 feedback 정책 결과를 구분했다. 실제 정책의 새 현재 상태 질의와 첫 전이 검사는 끝까지 계속 통과했다. 따라서 이번 완주는 원래 명령열의 정확한 재생으로 설명하지 않는다.

## Clipping과 전이 검증

| wheel 표본 | C0 clip/전체 | P clip/전체 |
|---|---:|---:|
| 첫 suffix13 | 0/208 | 29/208 |
| continuation | 6/924 | 15/792 |
| suffix 합계 | 6/1132 | 44/1000 |
| 공통 prefix 포함 전체 실제 주행 | 44/3020 | 82/2888 |

suffix 최대 force ratio는 C0 약1.114719/P1.407334였다. P continuation만의 최대는1.240247이다. 공통 prefix의 기존 clipping38개를 새 intervention 효과로 세지 않았다. q>1 자체는 기존 규칙대로 독립 안전 veto로 쓰지 않았다.

매 선택 첫 전이의 최대 body 위치 오차는 C0 3.15e-5m/P1.53e-5m, 속도 오차2.29e-5/2.53e-5m/s, wheel omega 오차1.44e-5/1.18e-5rad/s, force ratio 오차4.82e-6/6.49e-6이었다. raw time 오차와 clip flag 차이는0이었다. 후속 명령이 일치하는 각 initial13 witness의 겹치는 비교834/718개도 기존 허용치와 clip flag 차이0을 통과했다. 이 수는 독립 실제 시행 수가 아니다. P 첫 두 witness는 세 번째 재계산된 fullgas가 들어가는 시점에 명령 일치 대조를 종료한422의 경계를 유지했다.

## 지연과 비용

| 실제 질의 지연 | C0 | P |
|---|---:|---:|
| query wall p95 | 0.679초 | 1.047초 |
| query wall 최대 | 0.718초 | 7.111초 |
| query CPU p95 | 0.669초 | 1.045초 |
| query CPU 최대 | 0.716초 | 7.082초 |

질의에는 모델 적분뿐 아니라 snapshot·hash·독립 반복·receipt I/O·정리를 포함한다. 특히 P 첫 세 긴 witness 질의는 비싸며, 시뮬레이션 랩타임 양성을 실시간 실행 가능성으로 해석하지 않는다.

| 모델 tick 용도 | 필수 | 독립 반복 |
|---|---:|---:|
| 첫 실제13 창의 guardian initial13 | 1196 | 1196 |
| 첫 실제13 창의 planner initial13 | 468 | 468 |
| 같은 planner child의 C tail | 1825 | 1825 |
| 실제 continuation의 guardian initial13 | 4953 | 4953 |
| 합계 | 8442 | 8442 |

총 **16,884 ticks/280 worlds**다. 첫 실제13 창 모델6,978 ticks/64 worlds와 continuation9,906 ticks/216 worlds를 분리했다. 첫13과 긴 tail은 같은 child를 이어 적분했고 초기13을 다시 적분·중복 청구하지 않았다. 이전 cached source 비용 재청구0, 인위적 모델 부모 적분0이다. 실제 부모는 **370 wrapper/reset2**(prefix236+첫suffix13 합26+continuation108)로 따로 계상했다. 예약·확정 tick은 같고 미확정0, zero-time contact setup280, 최대 보유world6/적분 순차1개였다.

모델 CPU **105.418초**(import 포함)/query wall **104.967초**, 모델 제외 실제 CPU **21.721초**/wall **21.647초**, worker 전체 CPU **127.292초**/실행 wall **126.767초**다. tag별 constructor/step 시간은 전체 query 비용을 대체하지 않는다. worker 전체에는 별도 미배분 setup/cleanup도 포함되며 최종 결과 직렬화·보고·git 비용은 완전 계측하지 않았다.

측정 준비 wall 구간97.360초는 초기 읽기·설계 제외이며 준비 CPU는 미측정이다. 정적 사전 검사 CPU/wall0.118/0.119초, 저장 분석1.091/1.114초를 별도 기록했다. 실제·모델 실행은 각 동결 상한 이내였다.

실제370만 차감한 원장v443은 **연구 잔여28,986 + 최종 예비84,000 + 실제 누적1,319,078 = 운영 상한1,432,064**다. 예비·학습·actor·SEALED·추가 유료 자원 사용은0이다. HOLDOUT/SEALED를 열지 않았고 공식 main·Participants·사용자 변경·champion296·rollback·보호 자료와420/421/422 전체 파일을 보존했다. map/seed/state/RNG/원명령·전체 receipt는 비공개 경로에만 보존했다.

이번 실제 paired carry는 통과했다. 다음 독립 실험은 시작하지 않았다. 남은 경계는 픽셀 관측 정책으로의 전환, 독립 일반화, query 지연이며 이번 결과로 이를 승격하지 않는다.

[기계 판독 결과](carry423_result.json) · [422 실제13 보정](calibrate422_result.md) · [421 모델 비교](pilot421_result.md) · [419 고정 선택 규칙](planner419_result.md)
