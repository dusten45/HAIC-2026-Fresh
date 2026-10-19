# 578 — 저장 증거로 문제 표현 선택, 다음 실험은 미실행

현재 검증된 source 기록은 공식 **13.20초**, 연속 hull 교차 **13.1935880668초**다. **1초 이상 회수할 수 있는 손실은 아직 검증되지 않았다.** 이번 단계는 기존 DEV 테이프·집계의 읽기 전용 분석이다. source/native 실행, force 호출, LP·비선형 최적화, 새 FD·보정, HOLDOUT·SEALED 사용은 모두 0이다. 폐기된 연구를 재개하거나 추가 자원을 사용하지 않았다.

## 시간 배분과 실제 관측

[재현 분석](reframe578_analyze.py)과 [수치 결과](reframe578_analysis.json)는 source의 660개 채점 raw만 사용한다. 마지막 661번째 확인 raw 20ms를 더하지 않는다. 아래는 **소요 시간 분류**이며, 각 구간이 불필요하게 낭비한 시간이라는 뜻이 아니다.

| 배타적 분류 | 소요 시간 | COM 이동 거리 | COM 속도 중앙값 | 관측된 제약 근접 |
|---|---:|---:|---:|---|
| 기존 launch 24 holds | 1.92s | 81.17m | 42.01m/s | 가속 raw 96/96 |
| 직선 가속·주행·감속 | 2.76s | 251.81m | 94.71m/s | reference 여유 <0.1: 37raw, path >2.9: 9raw |
| 고정 경로 곡률 코너 | 4.58s | 311.35m | 66.78m/s | force >1.05: 14raw, footprint <0.6: 6raw |
| 장애물 근접 | 1.34s | 99.95m | 70.05m/s | force >1.05: 6raw, footprint <0.6: 9raw |
| 코너·근접 뒤 회복 창 | 2.60s | 225.40m | 87.31m/s | reference 여유 <0.1: 32raw, path >2.9: 3raw |

분류 순서는 launch→장애물 근접→코너→회복→나머지다. 근접은 COM에서 저장 obstacle disk까지 여유 <8m, 코너는 고정 경로 |곡률|≥0.0125/m, 회복은 직전 코너·근접 뒤 arc 35m 이내다. 이는 한 번 고정한 진단 규칙이며, 장애물의 인과 비용이나 차체 충돌 여유를 대신하지 않는다. 코너·근접·회복의 합계 8.52초를 개선 기회로 환산하지 않는다.

동일 고정 progress 경계를 사용한 551 대비 현재 테이프의 실제 관측은, s800에서 약 **22.88ms 앞서지만 s800→900에서 16.77ms를 되갚는다**는 것이다. 최종 공식 차이는 13.22→13.20초의 한 quantum이다. 마지막 구간의 차이를 전부 연속 물리 개선으로 해석하지 않는다. 이는 566의 초반 이득 뒤 상쇄와 일관되며, 다음 파일럿에도 후속 구간 유지 게이트가 필요한 이유다.

## 모델에 의존하는 숫자의 한계

현재 trajectory를 고정하고 각 tracking sample의 COM 속도를 reference+4.85로 즉시 바꾼 포화 proxy는 합계 **0.73624초**다. 현재 경로·sample을 고정하고 가속·yaw·접지 전환을 무시하므로 개선 예측이나 물리적 상한이 아니다.

저장 경로를 따라 계산한 별도의 비물리적 시간 proxy는 다음과 같다.

| 계산 | 시간 | 해석 |
|---|---:|---|
| 551 저장 launch 속도 profile | 13.50147s | 실제 source 시간과 다른 진단 적분 |
| reference+4.85, COM 90 상한 포함 | 12.71172s | 555와 비교하기 위한 제한된 계산 |
| reference+4.85, 90 상한 제외 | 12.46788s | 가속·경로·자세 도달 가능성을 증명하지 않음 |
| 555 연속 정상상태 branch | 11.50699s | 전이·도달 가능성 없는 낙관 시계 |
| 555 branch를 같은 reference+4.85와 90에 제한 | 12.90070s | 역시 도달 가능한 정책이나 성능 보장이 아님 |

90m/s는 이 비교의 설계 상한이다. 현재 source COM은 약94.85m/s에 도달하므로 이를 물리적 최고속도로 쓰면 안 된다. 11.99초까지는 공식 시간 기준 1.21초, 같은 거리의 평균 속도 약10.09% 증가가 필요하다. 위 proxy 어느 것도 그 기회를 검증하지 않는다. 541 native13.66과 현재 source13.20은 서로 다른 정책이므로 차이0.46초를 모델 오차라고 부를 수도 없다.

## 577이 검사한 공간의 실제 크기

573 대비 명령이 바뀐 곳은 holds123..165의 **43개**다. 최대 조향 변화는 **0.0000239909rad**로 ±0.4 기준 약 **0.0060%**, 최대 signed pedal 변화는 **0.0002399683**이다. 실제 hull 개선은 **14.4436µs**이고 공식 raw660은 그대로다.

고정된 여섯 방향의 기존 선형 예측에서 radius0.012의 총 nominal 기회는 약 **24.09µs**다. 처음 네 window 방향은 해당 unconstrained box gradient의 약1.68e-7, 5.56e-8, 3.05e-7, 1.19e-6만 남기고, 뒤 둘도 약0.58%, 3.88%다. 이는 투영된 국소 표현의 빈약함을 보여 주며, 전체 제어 공간의 불가능성 증명이 아니다. 24회 직접 source 중 안전14/실패10, force 실패4·footprint 실패6이 있었다. 실패10개 중8개는 기존 선형 물리 slack 예측이 모두 0 이상이었으므로 실제 결합 동역학도 문제였다. 단순히 step을 크게 하는 후속 sweep은 선택하지 않는다.

## 계약과 설계 가정 구분

| 항목 | 성격과 이번 판단 |
|---|---|
| 도로·장애물·차체, 물리 action domain, 시간·방문·tracker | 평가/물리 계약. 그대로 보존 |
| footprint≥0.5, path≤3, body<100, force 및 launch/tracking prefix clipping, reference+4.85 | 채택한 안전·인증 계약. 숫자가 자연법칙이라는 뜻은 아니지만 임의 완화 금지 |
| 551 고정 reference·경로, 기존 lookahead, cap90, 기존 backup와 PP 구조 | 설계 가정. 현재 strict 비교에서는 유지하되 방법 선택 시 물리 필연성과 구별 |
| 첫34 holds 고정 | 577의 국소 연구 가정. launch24 뒤 추가10 holds=0.80초까지 고정할 물리적 근거는 없음 |
| launch24 holds 고정 | 다음 작은 실험에서 비교를 단순화하기 위한 가정. 물리적 최적성 주장은 없음 |
| yaw aperture, 추가500ms 개선 게이트 등 | 이전 실험의 비교/승격 기준. 사용자 안전 조건이나 도달 가능성 정의로 오용 금지 |
| source full state | 진단 도구. native에서 허용되는 관측 또는 픽셀 정책으로 주장하지 않음 |

## 세 가지 이상 방법군의 비교

541·551·555와 기존 [380 방법군 검토](methods380_result.md), 562·566 기록을 함께 사용했다. 부모가 전달한 선행 full-read 판단의 요약을 근거로 활용했으며, 비공개 원문을 새로 직접 읽었다고 주장하지 않는다. W01–16 명칭은 기존 작업의 정규화이지 원문 공식 분류라는 주장도 아니다.

| 방법군 | 저장된 증거 | 현재 선택 |
|---|---|---|
| 경로·속도 구조 변경/retiming | [541](joint541_result.md)은 known DEV 실제14.22→13.66, 560ms. [551](whole551_result.md)은 source13.66→13.22, 440ms; native 미검증. 각각의 결합 변경 효과이며 성분별 합산 인과 효과는 아님 | 큰 변화의 근거는 있으나 즉시 거대 전역 NLP를 시작할 근거는 부족 |
| 도달 가능한 full-state 조향·경로·페달 전환 | [552](defect552_result.md)의 상태 의존 braking은 원 계약에서 COM 제동 거리 약12.57m 단축, lap gain 아님. [553](dynamic553_result.md)은 greedy pedal/backup의 yaw·joint 결합 실패. [562](handoff562_result.md)는 바뀐 자세에서 기존 feedback이 안전 완주했지만 전체 시간 개선0 | **한 코너와 다음 경계까지의 유한 beam을 선택**. 작은 tangent basis와 pedal-only backup에서 벗어나 실제 reachable 전환을 검사 |
| 정확한 이산 정상 궤도·trim graph | [555](drift555_result.md)의11.507초는 합성 평형; 첫 source Euler step부터 실패한 fixture 존재 | 도달·전이·현재 reference와의 관계가 미해결. 여러 trim을 최적화하는 두 번째 연구선은 시작하지 않음 |
| source/native fidelity·픽셀/학습 정책 | 현재577 native는 미검증. 서로 다른 정책의 source/native 차이로 fidelity 손실을 추정할 수 없음. 380의 과거 MPC/학습 실패도 보존 | 이번 native0. 의미 있는 source whole 개선 후 별도 계약으로 판단. 새 대형 RL·유료 학습 작업 없음 |

따라서 선택 근거는 ‘1초가 보인다’가 아니다. **실제 도달 가능한 코너 상태에서 결합된 기하·전환만으로100ms를 얻고80ms를 유지할 수 있는가**가 가장 저렴하게 남은 핵심 불확실성이다. 시간·안전 관측은 source 계약 범위에 한정한다.

## 다음 단일 반증 실험 — 제안만 등록

[기계 판독 계약](reframe578_next_contract.json)의 상태는 **PROPOSED_NOT_EXECUTED**다. 구현·시뮬레이션은 이번 단계에서 실행하지 않았다.

- 기존 launch24 holds를96raw 실제 source로 재구성한 prehold25에서 시작한다. 독립4raw identity probe도 비용에 넣는다. 전체 상태·visited·tracker·clock·누적 clipping 이력을 보존한다.
- 매 hold마다 lookahead target의 정상 방향 offset −0.75/0/+0.75m와 fullgas/coast/brake0.125/brake0.25를 조합한12개 및 factual action 한 개를 검사한다. 최대13 children,4raw/edge, beam 폭4다. 조향 공식·열거·중복·순위·동률 규칙은 계약에 고정했다.
- A는 최대28holds, 고정 world s200면에서 **보수적인 raw 시간 bracket 이득≥100ms**, baseline 교차 속도−0.15m/s 이상을 요구한다. factual1슬롯을 실제 평가로 보호한다. 저장 행동을 추가하는 것만으로 baseline 경로가 살아 있다고 가정하지 않는다.
- A에서 정해진 규칙으로 선택한 한 상태로 B를 단 한 번 진행한다. 최대20holds, 고정 s300면에서 **원 baseline 대비 총이득≥80ms 유지**, 같은 속도 여유 기준을 요구한다. 변경된 실제 checkpoint에서 이어 가며 factual pose나 cache로 이동하지 않는다.
- 통과 hold의 남은 raw까지 strict 검사한다. 목표면 미도달·게이트 실패는 예산·깊이·폭을 늘리지 않고 종료한다. source 부적격 child는 즉시 prune, body/domain/integrity/IO/cost 오류는 전체 hard stop이다. 안전 계약은 그대로다.
- A·B가 모두 통과한 한 계획만 최대288raw 초기 source 독립 replay 한 번으로 완전 상태·힘·이력·시간·checkpoint 일치를 확인한다. 최종 정책 승격이나 whole/native 실행을 자동 허용하지 않는다.

계획된 최악 비용은 **96+4+4×13×4×(28+20)+288=10,372 attempted raw**다. 선행 force 실패도 attempted raw로 차감한다. hard cap은 model 완료틱/attempted raw 각각11,000, force44,000, geometry11,000, **CPU400s·wall540s**, native0이다. 이는 577의 실측 총 CPU388.09s/14,331틱을 이용한 비용 가늠이며 새 방법의 실제 비용 측정값은 아니다. 실험 전 구현 검사와 재현 로그를 준비하되 이 계약에서 추가 optimizer나 내부 rollout을 숨겨 넣지 않는다.

이 pilot이 실패하면 이 유한 표현을 닫는다. 성공해도 증거는 s300까지이며 이후 상쇄·공식 finish·native·1초 기회는 미검증으로 남긴다. 그때만 새 whole-lap 유지 계약을 제안한다. 승인 종료 뒤 시작·자동 연장은 없고 지정 클라우드만 사용한다.

## 검증·보존

분류 합13.20초, 첫136raw 상태/힘 동일, 첫34 commands 보존, 공통 spatial gate 존재를 저장 기록으로 확인했다. 551의 오래된 테이프에는 clock/before-root가 없어20ms 누적과 이전 post-state로 정규화했다. 최초 schema 오류 기록은 private에 보존했고 simulator를 재실행하지 않았다. 분석의 최종 성공 실행 CPU·wall은 JSON에 기록했으며 이전 읽기 전용 준비 비용은 별도 보수 charge로 명시한다.

이번 단계 research 잔여22,758, reserve84,000/사용0은 변하지 않는다. HOLDOUT·SEALED는 계속 미사용이다. 공개물은 기술 분석·집계·제안 계약뿐이며 원시 계획·상태·journal·비공개 원문은 저장소 밖에 남는다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31, Participants·사용자 변경·기존 백업·이전 실패를 보존한다.
