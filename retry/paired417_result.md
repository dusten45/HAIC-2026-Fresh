# 417 — C의 고정 첫 가속은 source 양성이지만 승격 폭에 미달했다

**두 recipe의 source 자격은 통과했으나 보장 시간 이득이0.04초로 사전 기준0.08초에 못 미쳤다. 실제 A/B는 실행하지 않았다.** A의 공통 exit 도착은0.50–0.52초, B는0.44–0.46초여서 source 이득 bracket은0.04–0.08초다. 상단0.08초를 보장 이득으로 취급하지 않았다. 다른 창·pulse·horizon·재주행 없이 이 recipe를 닫는다. H1 전체 실패나 C와 시간 선택의 일반적 불가능성을 뜻하지 않는다.

416 설계의 **C pre119·history118**을 그대로 사용했다. 개발 상태는 저장411 C에서 원래 arc60–70%, 현재 nominal brake>0, 현재 r−v≥5인 첫 상태다. 미래 tire나 미래 도착 시간을 선정에 쓰지 않았다. 경로·속도 노드·gain·조향 법칙을 고정했다.

원래397 C 파일을 보존하고 별도 [연구용 복사본](signed417_executor.py)을 만들었다. 유일한 변경은 strict `sigma<0` 정의역 거부를 기존 의미 있는 후진 기준 `sigma<−0.1`로 바꾼 한 줄이다. signed sigma를0으로 자르지 않았고 epsilon도 넣지 않았다. 차체 forward<−0.1 안전 중단, positive target·phase·finish·projection 및 COM/origin 의미는 유지했다. 물리 world를 만들기 전에 저장411 C 정상 nominal188행의 전체 float32 명령이 원래 C 및 실제 기록과 정확히 일치했다. 이는 미소 후진에서 실제 재출발을 검증한 결과가 아니다.

## 선행 source 검증

저장 C 실제 명령118행동(기존91행동의 neutral pulse 포함)을 연속 source 부모에서 재생했다. 실제 pre/post body·wheel과 매 행동 첫 raw hull pre-phase를 대조했다. nominal13행동 forecast A1을 먼저 저장한 뒤 실제 기록과 대조하고 A2를 독립 반복했다. B1/B2도 같은 상태·C memory에서 독립 반복했다. 이후 A를 다시 실행해 reference 불변을 확인하고, 살아 있는 연속 부모를 nominal13행동 진행시켜 복원 A와 full raw hull·wheel·body를 대조했다. 모든 복원·독립성·부모/입력/memory/RNG 불변 게이트를 통과했다.

| 항목 | 최대 차이 또는 결과 |
|---|---:|
| 정상 저장 C 명령 | 188/188 정확히 일치 |
| source prefix 실제 대조 | 118/118 통과 |
| nominal13 위치 | 1.376×10⁻⁵m |
| nominal13 속도 | 1.178×10⁻⁵m/s |
| nominal13 yaw rate | 9.805×10⁻⁶rad/s |
| nominal13 wheel omega | 1.852×10⁻⁵rad/s |
| nominal13 wheel force ratio | 5.937×10⁻⁶ |
| 연속 부모 vs 복원 A raw origin 위치 | 1.456×10⁻⁵m |
| A/B 각각 독립 반복·후속 A reference | 통과 |

기존 body391·wheel·raw hull 허용오차를 완화하지 않았다. COM local/mass/inertia도 기존 실제 계측 metadata와 일치했다. **411에는 actual 중간 raw hull이 저장돼 있지 않다.** 따라서 source full raw hull 자격은 연속 부모와 복원 분기의 같은 phase 대조이며, 과거 actual 중간 raw hull과의 대조라고 주장하지 않는다. 실제 기록과는 pre/post body·wheel·첫 raw pre-phase를 대조했다. 실제 단계가 열리면 raw hull을 직접 수집해 prefix·첫 변경 전이·일치 recipe 구간을 대조하도록 구현했지만 그 단계는 열리지 않았다.

## 고정 두 recipe와 공통 exit

A는 C nominal13행동이다. B는 첫 nominal 조향을 유지하고 gas1/brake0 한 번, 이후 자기 상태에서 같은 C nominal 피드백이다. 새 경로·다른 timing·연속 selector를 시험하지 않았다. 진행·안전·공통 exit는 원래 reference arc로 평가했다. 목표는3.24m, deadline은 기존13행동이며, 공통 exit는 등록한 진입 arc+30m다. 보간 도착 시간이나 가상 profile 시계는 사용하지 않았다.

| source 결과 | A nominal | B full-gas-first |
|---|---:|---:|
| exit 도착 raw tick bracket | [25,26] | [22,23] |
| exit 도착 경과 시간 | 0.50–0.52초 | 0.44–0.46초 |
| horizon | 13행동 | 13행동 |
| 13행동 원래 arc 진행량(source) | 67.064m | 75.707m |
| post 최대 원래 경로 오차 | 0.9995m | 0.9911m |
| 손상·도로/grass·충돌·후진 위반 | 0 | 0 |
| wheel 최대 force ratio | 0.9633 | 1.2478 |
| clipped wheel 표본 / 전체 | 0/208 | 26/208 |

B의 q>1은 source의 정상 벡터 clipping을 관측한 것이며 독립 안전 거부 조건으로 쓰지 않았다. 두 recipe 모두13행동·진행·안전·같은 exit를 통과했다. 수치 순위는 source에서 B가 빠른 양성이다. 다만 실제 반사실 순위·더 긴 C tail·완주에 대한 검증은 아니다.

승격 기준은 `B upper <= A lower − 4 raw ticks`였다. 이번에는 `23 <= 25−4=21`이 거짓이다. 보장 이득은2tick=0.04초이며 필요한4tick=0.08초에 미달한다. clock의 작은 float 차이에 맞춘 epsilon 대신 원래50Hz raw tick 정수로 판정했다. 실패 arm의 시간 추정은 없었다.

## 실제 단계와 비용

실제 단계의 조건부 코드에는 양쪽 동일한411 guardian(현재 nominal13행동 독립 반복, 미적격일 때만 고정 neutral-brake13행동 독립 반복)을 유지했다. B의 첫 고정 full-gas도 live 상태에서 별도 반복 예측으로 검증하고, 이후에는 같은 guardian만 적용하도록 했다. source와 달라지는 명령·matching-recipe fidelity·매 selected 첫 전이·살아 있는 실제 부모/RNG 불변과 모델 비용을 기록하도록 구현했다. **source 시간 게이트 미통과로 이 코드는 실행하지 않았고 compile 검증만 했다.** 실제 첫 변경 전이·actual live-parent 무영향·guardian suffix·새 signed 영역의 실제 자격을 주장하지 않는다.

모델8192tick/160world/CPU45초/wall90초, 실제400wrapper/reset2/CPU90초/wall180초, 동시1개의 상한을 사전에 동결했다. 모델 CPU/wall은 source 및 실제 guardian의 모델 구간에만, 실제 CPU/wall은 그 구간을 제외한 계정에 기록하는 구조다. model step은 tick에만, actual wrapper step은 native에만 청구한다.

이번 사용은 **모델784tick/6world, CPU1.703초/wall1.735초**다. prefix472tick, A/B 중복과 후속 A의260tick, 연속 부모13행동52tick으로784tick이며 zero-time contact setup6회도 별도로 셌다. 정상188행 대수 검증은 모델 계측 구간에 포함했다. 실제 wrapper/reset·guardian 모델 query는 모두0이다. worker 실행 CPU1.753초/wall1.784초, import 등을 포함해 마지막 직렬화 전 기록한 worker 전체 CPU2.443초다. 준비 wall225.779초는 별도이고 준비 CPU·보고/git 전체는 미계측이다. 계측 payload CPU0.0332초/wall0.0762초는 전체 tracer dispatch overhead의 완전한 측정이 아니며 비계측 재주행을 하지 않았다.

원장v437에서 실제 사용만 차감한 결과 연구29,880·예비84,000(사용0)으로 그대로다. 새 actual/reset·actor·학습·SEALED·예비·유료 자원 사용은0이다. champion296/rollback240·보호 자료·408 원기록·공식 main과 승인 기한을 유지했다. 개인 seed·지도·raw 상태·trace·RNG·명령열은 저장소 밖에 보관했다. [기계 판독 결과·비용](paired417_result.json).

동결 plan SHA256: `c6b04a4ea23a023419e82a0515f85fa48bd949afa30bfccb78b74e1255b584ea`.
