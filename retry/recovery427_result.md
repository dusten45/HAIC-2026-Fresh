# 427: 종료 인증 복구 뒤 P12 실제14.080초 확인

**새427 계획에서 정적28개 → 독립 모델 확인 → P12 한 번 실제 재현을 통과했다. P12는177번째 실제 행동을 발행한 뒤 공식14.080초로 종료했다.** 저장425의176행동과 다음 질의 직전 full snapshot이 정확히 재현됐다. 마지막 실제1raw tick/4wheel sample과 실제 DONE을 확인했다.

425의 C0 **15.080초는 과거 대조**다. 새 P12와 그 차이는1.000초, 공식 crossing raw bracket 차이는[0.98,1.02]초다. **새 동시 pair는 아니며 C0를 다시 실행하지 않았다.** 알려진 DEV root의 동결 정책 기술 재현으로, 새 성능 탐색·픽셀296·독립 일반화·실시간성의 증거가 아니다.

## 새 gate와 변경 범위

계획 SHA-256은 `e5f97104b9e37a519a6d77ad763fa8fa061ad8a0824c2d8534e8d4ed60570c1b`다. 적분 전에426의 수정 모듈 `guardian426_confirmed.py`, 기존 assertions 모듈·통과 결과·수정 계획의 hash가 검증했던 값과 같은지 확인했다. 같은28개 정적 assertions를 새427 계획에서 다시 통과했다. 426 원정적 실패와 모델/실제 미개방 판정을 소급 변경하지 않았다.

guardian 종료 확인은 planner용 미래 finish 순위와 분리됐다. 현재 root에 이미 등록된 crossing의 확인은 model certificate로만 다루며 순위/Evidence/actual DONE 권한을 주지 않는다. planner는 기존 `Child`/419의 양의 미래 finish 비교·음수/zero-event 거부를 유지했다. selector·gain·세 recipe·horizon13·signed C·projection·실제 phase/confirmation corridor/action은 변경하지 않았다.

첫 정적·모델·fidelity 오류에서 actual을 차단하고, 실제 첫 안전·진행·fidelity·복원·정의역·부모/RNG·memory·ledger·비용 오류에서도 즉시 중단하도록 했다. 모델131,072ticks/1000world/CPU600초/wall900초, 실제310wrapper/reset1/모델 제외 CPU90초/wall180초, 정적60/120초·적분 순차1개를 동결했다. qualification 포함 최악129,890tick/795world로 상한 안에 뒀다.

## 저장425 root의 독립 모델 확인

425의 마지막 현재 snapshot에서 모델 부모를 보유하고 nominal을 새 모델에서 독립2회 확인했다. 두 모델 모두1raw tick 뒤 같은 `AT_ROOT_CONFIRMED_IN_MODEL`을 냈다. 완료 tracker의 후보 필드 정리·공식 model finish metadata와 기존 실패 child의 body/wheel/raw hull·phase·clip flag가 맞았다. 부모·입력 memory·global RNG·실제 ledger는 보존됐고 nominal 명령도 바뀌지 않았다.

이 certificate의 `planner_ranking_eligible=False`, `actual_done_allowed=False`를 확인했다. 이 단계에서는425 실제 `finish_time_s=None`이 그대로였다. qualification은 새2tick/3world(보유 부모 포함)였고 그 통과 뒤에만 실제 reset을 열었다.

## 실제 한 번의 재현과 공식 종료

P12만 같은 초기 상태/history118에서 새 reset 한 번으로 실행했다. 첫176행동의 명령·sensor/state·controller memory·raw hull/wheel·clip flag·terminal metadata가 저장425와 정확히 같았다. 177번째 질의 전 접근 가능한 full state/RNG/pixels/controller snapshot의 hash도425가 중단했던 최종 snapshot과 정확히 같았다. 질의 전후 hash는 같았고 분기 memory는 부모에 commit하지 않았다.

첫12번은 실제 현재 상태로419를 재계산했다. 선택은1·3·11번째 fullgas, 나머지 nominal이었다. 이후에는 기존 guardian만 사용했다. 선택열이나 q최대 위치를 실제 명령 트리거로 쓰지 않았다. 전체 receipt12개는 저장·복원/typed selector 재계산이 일치했다.

이번59회 실제 suffix 선택 전이는 body/wheel/raw hull·phase·finish metadata·raw tick·clip flag 차이0을 모두 통과했다. 실제 부모·memory·RNG·실제 ledger도59회 질의에서 보존됐다. 겹치는 일치 initial13 witness598개 대조는 통과했으며 독립 시행 수로 세지 않았다. 실제 관측만 실제 ledger에 반영했다.

| 실제 확인 지표 | 427 P12 |
|---|---:|
| reset / 실제 wrapper 행동 | 1 / 177 |
| prefix / suffix | 118 / 59 |
| 첫13 뒤 continuation 행동 | 46 |
| 공식 crossing 랩타임 | **14.080초** |
| reset 이후 crossing raw bracket | [703,704] |
| 확인까지 raw ticks | 705 |
| 마지막 실제 action | 1raw tick / 4wheel samples |
| 실제 controller 최종 phase | DONE |
| damage / 새 suffix neutral 개입 | 0 / 0 |
| 전체 post 경로 오차 최대 | 1.379m |
| suffix raw hull 경로 오차 최대 | 1.431m |
| 실제 최대 force ratio | 1.4584433 |
| suffix clip | 43/932 wheel samples |

마지막 guardian의 독립 모델 증거는 여전히 actual DONE 권한이 없었다. **실제 `env.step`으로177번째 행동을 발행한 뒤**, native 공식 finish와409의 정상 partial 계약을 확인하고 actual DONE을 기록했다. 공식 crossing은15.099999999999767, 확인 post는15.119999999999767이었다. 확인 시각을 랩타임14.100초로 대체하지 않고 공식 crossing 기준14.080초를 사용했다.

매 선택 첫 전이의 최대 body 위치 오차7.63e-6m, 속도1.53e-5m/s, wheel omega1.28e-5rad/s, force ratio5.14e-6 미만이었고 raw time·clip flag 차이는0이었다. 첫13 clip29/208, continuation14/724, 공통 prefix 포함 전체81/2820이었다. 기존 prefix의91번째 neutral과38개 clip은 새 suffix 개입 효과로 세지 않았다. 이 유한 관측 구간의 자격을 다른 q영역·독립 환경으로 확대하지 않는다.

## 과거 C0와의 비교

425의 실제 C0는 이번 재실행이 아닌 과거15.080초 대조다. 같은 초기 상태·history118의 frozen 정책 결과와 비교하면 공식 lap 차이는1.000초다. raw20ms crossing bracket으로는[0.98,1.02]초이며 통계적 신뢰구간이 아니다.

| 같은 원래 경계 | 과거425 C0 대비 새427 P12 이득 |
|---|---:|
| 기존 국소 arc+30m exit | 0.04–0.08초 |
| arc70% | 0.18–0.22초 |
| 75% | 0.34–0.38초 |
| 80% | 0.60–0.64초 |
| 85% | 0.74–0.78초 |
| 90% | 0.80–0.84초 |
| 95% | 0.94–0.98초 |
| 공식 finish | 0.98–1.02초 |

보간·참조 clock·미완료 시간 추정은 쓰지 않았다. 424의 모델0.98–1.02초 기록은 모델 기록으로 유지하고 이번427의 새 실제 확인을 별도로 기록한다. 425의 공식 P finish 미관측·365행동 비용과426의 첫 정적 실패·추가 적분0 판정은 그대로다.

## 비용과 보존

| 새 모델 tick 용도 | 필수 | 독립 반복 |
|---|---:|---:|
| 저장425 pending root 확인 | 1 | 1 |
| P12 planner initial13 | 1664 | 1664 |
| 같은 child의 C tail | 5843 | 5843 |
| 첫 실제13 창 guardian | 52 | 52 |
| continuation guardian | 2041 | 2041 |

총 **19,202ticks/161worlds**다. qualification2tick/3world와 실제 재현 중 모델19,200tick/158world를 분리했다. 예약·확정 tick은 같고 미확정0, zero-time contact setup161, 최대 보유world6/적분 순차1개다. initial13+tail은 같은 child를 이어 적분했고 모델 부모의 추가 적분은0이었다.

새 실제 **177wrapper/reset1**(prefix118+첫suffix13+continuation46)만 이번에 차감했다. 176행동은 실제로 다시 실행한427 비용이며 이전425 비용을 재청구한 것은 아니다. C0 새 실행0,425/426 과거 비용의 중복 계상0이다.

모델 CPU **74.280초**/query wall **72.851초**, 모델 제외 실제 CPU **10.144초**/wall **10.102초**, worker 전체 CPU **84.546초**/실행 wall **83.068초**였다. 모델 CPU에는 import·source 검증·snapshot/hash/I/O/정리가 포함된다. tag별 constructor/step 시간은 전체 query 비용을 대체하지 않는다. 전체 worker에는 별도 setup/cleanup도 포함되고 최종 직렬화·보고/git은 완전 계측하지 않았다.

정적 CPU/wall0.606/0.609초, 저장 분석1.100/1.148초를 분리했다. 준비 wall3.693초는 기존 모듈을 재사용한 초기 source 검토 이후의 부분 구간이고 준비 CPU·초기 검토/설계 전체는 미측정이다. query wall p95/최대는4.291/4.466초로 실시간 실행 가능성을 주장하지 않는다.

원장v447은 **연구 잔여28,444 + 최종 예비84,000 + 실제 누적1,319,620 = 운영 상한1,432,064**다. 예비·actor·학습·SEALED·추가 유료 자원 사용0이다. 공식 main·Participants·사용자 변경·296·rollback·보호 자료와420–426 전체 파일을 보존했다. HOLDOUT/SEALED는 열지 않았고 map/seed/state/RNG/명령·전체 receipt는 비공개 경로에만 보존했다.

동결 정책의 기술 복구 재현은 통과했다. 추가 재시도·성능 탐색·독립 실험·자동 연장은 시작하지 않았다. 픽셀 관측 정책·독립 일반화·실시간성은 여전히 미검증이다.

[기계 판독 결과·비용](recovery427_result.json) · [426 정적 실패와 수정본](recovery426_result.md) · [425 원실패](carry425_result.md)
