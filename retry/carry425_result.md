# 425: 실제 전이 보정 통과 구간과 종료 경계 기술 중단

**C0는15.080초로 공식 종료했지만 P12는176행동 뒤,177번째 실제 행동 직전 guardian 모델의 `official_finish_not_after_root` 오류로 중단됐다. P의 공식 완주·전체 실제 이득은 미검증이다.** 마지막 실제 행동·실패한 질의의 독립 반복·재시도는 실행하지 않았다. 424의 모델 이득0.98–1.02초를 실제 기록으로 바꾸지 않았다.

사전 검사에서 이 종료 경계를 놓쳤다. 오류 이전에 완료된 P suffix58행동은 새11번째 선택과 더 큰 clipping 영역까지 body/wheel/raw hull·phase·finish metadata·clip flag 대조를 통과했다. 이는 관측 구간의 전이 보정이며 미관측 공식 finish를 대신하지 않는다.

## 실행 전 비용 경계와 규칙

계획 SHA-256: `7411f503fbcb8956f30d60232a5d4916ee8bc05be15678e6c05144497ab2e5f8`. 같은 초기 상태/history118/419 선택 규칙·gain·recipe·horizon13·signed C·projection을 동결했다. C0는 기존 guardian, P12는 첫12 실제 현재 상태에서 planner를 재계산한 뒤 같은 guardian만 사용한다. 모델 선택열이나 q최대 위치를 명령 트리거로 사용하지 않는다.

실제620 wrapper를 끝까지 모두 허용하면 모델 최악 비용이 상한을 넘을 수 있어 실행 전에 **arm당216행동·합계432행동**의 더 작은 계산 경계를 보고하고 동결했다. 12회 고유3recipe·독립 반복·최대 추가308행동 witness의 최악92,448tick과 나머지184회 guardian의 양쪽 recipe·독립 반복38,272tick을 합쳐 **130,720tick/808world**다. 승인 모델 상한131,072tick/1000world 안에 든다. 실제 승인 상한620/reset2/모델 제외 CPU120초/wall240초, 모델 CPU600초/wall900초/적분 순차1개를 유지했다. CPU/wall 중단은 더 일찍 발생할 수 있다.

실행 전 정적16개 검사가 원장·receipt·기존 종료 경계와 전체 최악 tick/world·실제 행동 경계를 통과했다. 첫 안전·진행·fidelity·복원·정의역·부모/RNG/memory/ledger·비용 오류 또는 guardian 둘 다 불가에서 즉시 전체 중단하도록 했다. **suffix58에서 기계적으로 중단한 것이 아니다.** 실제 P176행동은 arm cap216보다 작았고 모델 비용도 상한 아래였다. 다음 질의의 종료 인증 오류가 중단 원인이다.

## 실제 선택과 단계별 보정

두 실제 reset의 초기 full state/RNG/pixels와 history118 뒤 fork의 controller 계산 전후 memory·nominal이423 및 서로 간에 같았다. C0는 전체189행동의 명령·memory·body/wheel/raw hull·clip·finish metadata가 저장423과 정확히 일치했다. P는128행동까지 정확히 일치했고,129번째(suffix11) 새 fullgas가 들어가기 직전 pre-state와 memory도 정확히 같았다. 그 명령 변경 전까지 기존423 trajectory equality를 확인한 뒤, 이후 실제 정책과 새 선택 첫 전이 검사를 계속했다.

P의12회 실제 재계산 선택은 `fullgas, nominal, fullgas, nominal, nominal, nominal, nominal, nominal, nominal, nominal, fullgas, nominal`이었다. 결과적으로424와 같았지만 고정 재생하지 않았다. 12개 전체 receipt의 typed selector 재계산도 일치했다. source memory는 부모에 commit하지 않았고 실제 post 관측만 실제 ledger에 반영했다.

성공한129회 질의(C0 71/P58)의 실제 부모·memory·global RNG·ledger는 전후 같았고, 각 실제 선택 첫 전이의 body/wheel/raw hull·phase·finish metadata·raw tick 계약·clip flag 차이0을 통과했다. 일치하는 initial13 witness의 겹치는 비교는 C0 834/P585개로 기존 허용치와 clip flag 차이0을 통과했다. 이 수는 독립 실제 시행 수가 아니다.

공통 prefix의 기존91번째 neutral은 유지했다. 새 suffix guardian neutral 개입은 양쪽0이었다. 424의 긴 witness와1e-6보다 큰 명령 차이는 C0 행동166에서 처음 관측됐으며 nominal feedback 차이였다. P의 완료된58행동은 이 허용치 안에 있었지만, 실제 정책 기록을 모델 witness의 정확한 재생이나 미관측 완료로 취급하지 않는다.

| 실제 관측 결과 | C0 | P12 |
|---|---:|---:|
| 실제 행동 / suffix | 189 / 71 | 176 / 58 |
| 첫13 뒤 continuation 행동 | 58 | 45 |
| 공식 랩타임 | 15.080초 | 없음·기술 검열 |
| 마지막 실제 wrapper raw ticks | 3 | 4·비종료 |
| damage / 새 suffix neutral 개입 | 0 / 0 | 0 / 0 |
| 전체 실제 post 경로 오차 최대 | 1.379m | 1.379m |
| suffix raw hull 경로 오차 최대 | 1.266m | 1.431m |
| 첫 suffix13 clipped samples | 0/208 | 29/208 |
| continuation clipped samples | 6/924 | 14/720 |
| suffix clip 합계 | 6/1132 | 43/928 |

P의 실제 force ratio 최대 **1.4584433**까지 완료된 전이 대조를 통과했다. C0 suffix 최대는1.114719다. 공통 prefix를 포함하면 clip은 C0 44/3020/P81/2816이며 공통 prefix38개를 새 선택 효과로 세지 않았다. 이 관측 표본의 자격을 다른 상태나 전체 force 영역에 일반화하지 않는다.

관측한 같은 원래 arc crossing의 실제 이득은 국소 exit0.04–0.08초,70% 0.18–0.22,75% 0.34–0.38,80% 0.60–0.64,85% 0.74–0.78,90% 0.80–0.84,95% 0.94–0.98초였다. raw20ms bracket을 사용하고 보간하지 않았다. **공식 finish 차이는 없음**으로 남겼으며95% 이득이나 경과 시간을 남은 랩의 추정값으로 확장하지 않았다. 물리 DNF 판정도 아니다.

## 중단 원인과 정적 진단

실제176번째 post와 최종 실제 snapshot의 시각은15.099999999999767로 같고 실제 `finish_time_s`는None이다. 다음 nominal 계산은 기존 `FINISH_CONFIRM` phase에 들어갔고 후보 crossing 시각도 현재 root 시각과 같았다. 기존 제어기의 confirmation corridor 조건은 저장 기록에서 통과했다.

실패한 첫 guardian child만 한 model raw tick을 적분해 시각15.119999999999767에서 model finished를 예측했다. 이 model finish event 시각은 root와 같은15.099999999999767이었다. 공통 `Child`의 “공식 event는 root보다 뒤여야 한다”는 시간 인증이 상대 tick0을 거부했다. **이 모델 한 tick은 실제 행동177이 아니다.** 실제 공식 완료는 관측되지 않았다.

guardian의 짧은 종료 확인에도 planner용 엄격한 미래 finish 인증을 재사용한 경계 문제다. 저장 기록만 사용한 정적10개 검사로 현재 clock 보존·실제 finish 없음·기존 confirmation predicate·event AT_ROOT·모델만1tick 진전·기존419 음수 하한 bracket 거부·실제177 미발행·비용 cap 미도달을 확인했다. 새 모델/실제 적분은0이었다. 실패한130번째 query는 정상적인 post-parent 전체 게이트까지 완료하지 못했으며, 이를 성공한129회와 구분한다.

실행했던 코드·계획·오류·부분 child와 비용은 비공개 executed-source 사본/hash로 보존했다. 실행 코드나419의 시간 규칙을 약화하지 않았다. 다음 기술 작업은 **guardian 종료 확인 자격과 planner의 양의 미래 finish 순위를 분리하는 정적 수정·검증**이다. candidate/model completion을 actual DONE으로 바꾸거나 음수 bracket을 허용하는 우회는 제안하지 않는다. 이후 새 적분·실제 재실행은 별도 승인 범위다.

## 지연·비용과 원장

| 성공 질의 지연 | C0 | P12 |
|---|---:|---:|
| wall p95 / 최대 | 0.639 / 0.700초 | 6.486 / 7.236초 |
| CPU p95 / 최대 | 0.635 / 0.698초 | 6.465 / 7.210초 |

위 지연은 성공 질의만의 분포다. 실패한 마지막 query CPU/wall 약0.227/0.227초와 model1tick/world1도 전체 비용에 포함했다. snapshot·hash·독립 반복·I/O·정리를 포함하며 실시간성을 주장하지 않는다.

| 모델 tick 용도 | 필수 | 독립 반복 |
|---|---:|---:|
| 첫 실제13 창 guardian | 728 | 728 |
| P12 planner initial13 | 1664 | 1664 |
| 같은 child의 C tail | 5843 | 5843 |
| continuation guardian, 마지막 오류 포함 | 4732 | 4731 |

총 **25,933tick/299world**다. 마지막 필수1tick에서 오류가 나 반복은 시작하지 않았다. 예약·확정 tick은 같고 미확정0, zero-time contact setup299, 최대 보유world6/적분 순차1개였다. 초기13과 tail은 같은 child에서 이어 적분했고 캐시된 과거 비용·모델 부모 적분의 중복 청구는0이다.

실제는 **365 wrapper/reset2**(공통 prefix236+첫suffix13 합26+continuation103), 미확정0이다. 모델 CPU **139.211초**/query wall **138.415초**, 모델 제외 실제 CPU **20.989초**/wall **20.901초**, worker 전체 CPU **160.297초**/실행 wall **159.412초**다. per-tag constructor/step 시간은 전체 query 비용을 대체하지 않는다. whole worker에는 별도 setup/cleanup도 포함되며 최종 직렬화·보고/git은 완전 계측하지 않았다.

준비 wall107.943초는 초기 최악 비용 설계 제외의 부분 구간이고 준비 CPU는 미측정이다. 정적 사전 검사 CPU/wall0.339/0.341초, 저장 분석 CPU1.734초, 저장 경계 진단0.033/0.035초를 분리했다.

원장v445는 실제365만 차감해 **연구 잔여28,621 + 최종 예비84,000 + 실제 누적1,319,443 = 운영 상한1,432,064**를 유지한다. 예비·actor·학습·SEALED·추가 유료 자원 사용0이다. 공식 main·Participants·사용자 변경·champion296·rollback·보호 자료와420–424 전체 파일을 보존했다. HOLDOUT/SEALED는 열지 않았고 raw map/seed/state/RNG/명령·전체 receipt는 비공개 경로에만 남겼다.

이번 전체 carry는 **중단·미승격**이다. 완료된 새 전이/clipping 증거와 공식 랩 미관측을 함께 보존했다. 새 독립 실험·재시도·자동 연장은 시작하지 않았다.

[기계 판독 결과·중단 진단](carry425_result.json) · [424 모델 전용 pilot](pilot424_result.md) · [423 이전 실제 carry](carry423_result.md)
