# 306 — frozen221의 최종 pedal delta head 한 번 학습·평가

**후보 0/18 대 정확한 296의 17/18 완주로 미채택한다.** 수집 6 TRAIN에서도 0/6 대 5/6, 나머지 12 TRAIN에서는 0/12 대 12/12였다. 공통 완주가 없어 시간 개선을 계산할 수 없다. 18개 모두 한 번 공식 종료까지 실행했으며 기술 오류·예산 검열은 0이다. Champion296·240 rollback을 유지하고 다른 후보·재학습·DEV·승격은 진행하지 않았다.

295 새 12 TRAIN manifest의 위치 0·3·6·9(T2950/T2953/T2956/T2959), 원래 여섯 TRAIN의 앞 두 도로 O0/O2를 결과 전에 고정했다. Exact296을 각 한 번 실행해 총 1,754개 행동 직전의 legal 16 features·최종 행동·pixels와 기존 capture API의 전체 source 필드를 확보했다. 여섯 결과는 저장된 296과 일치했다. 차체·바퀴·관절·actuator·도로/노면·방문·damage·무진행 counter·실제 touching obstacle fixture pairs를 직접 수집했다. 300 truth/geometry로 접촉 이력을 가정하거나 불완전 자료를 snapshot으로 재사용하지 않았다.

이 source capture는 Box2D 내부 solver snapshot이 아니다. 기존 frozen221 모델은 warm-start impulse·manifold/broadphase·island 순서·finish-line 상태를 복제하지 않는다. 이번 capture의 실제 접촉 이력은 제공했으며 모든 581 query의 기존 초기화 검사는 통과했다. 이를 모든 미래 전이의 정확성으로 확대하지 않는다. 새 simulator는 구축하지 않았고 frozen221 oracle 및 주요 source hash를 확인해 그대로 썼다.

Native 1·4·7…의 첫 최대 100개 상태를 도로마다 offline으로 질의했다. 실제 query 수는 순서대로 **100·100·98·89·100·94, 합계 581/600**이다. 짧은 episode의 몫을 다른 도로로 옮기지 않았다. Teacher nominal pixel actor는 각 실제 관측을 보고 실제 296 행동을 feedback 받았으며 GT는 evaluator의 teacher/진단에만 있었다. 현재 상태에서 선택한 teacher의 첫 최종 pedal에서 296의 최종 pedal을 뺀 값을 라벨로 삼았다. 옛 라벨·DEV·HOLDOUT·SEALED는 fit에 쓰지 않았다.

이번 TRAIN 라벨만 도로별 가중치 합 N/6으로 표준화(mean/std, std floor 1e-6)하고 16 features+bias의 17×2 ridge를 **λ=1·bias 비정규화로 한 번** fit했다. Delta를 ±0.5로 clip한 뒤 exact296의 최종 pedal에 더하고 0..1 clip한다. Scale을 재적용하지 않는다. Steering·직접 memory·원래 head·다른 계수·route·관측은 보존했다. 저장 입력 1,754개에서 zero-delta 행동·feature·memory가 bit exact였다. 동결된 head를 전체 18 TRAIN에서 한 번씩 평가하며 기준은 저장 결과를 재사용했다.

| TRAIN | 저장 296 | 후보 결과 | 후보 native | damage |
|---|---|---|---:|---:|
| O0 | 24.32초 | off_track DNF | 262 | 0.6 |
| O2 | 22.36초 | off_track DNF | 362 | 0.6 |
| N0 | 24.04초 | off_track DNF | 344 | 0.0 |
| N1 | 17.86초 | off_track DNF | 285 | 0.0 |
| N2 | 29.00초 | off_track DNF | 583 | 0.0 |
| N3 | 19.72초 | off_track DNF | 244 | 0.4 |
| T2950 | off_track DNF | off_track DNF | 228 | 0.0 |
| T2951 | 21.04초 | off_track DNF | 388 | 0.4 |
| T2952 | 21.14초 | crash DNF | 221 | 1.0 |
| T2953 | 23.80초 | off_track DNF | 420 | 0.0 |
| T2954 | 27.44초 | off_track DNF | 190 | 0.0 |
| T2955 | 23.86초 | off_track DNF | 271 | 0.0 |
| T2956 | 23.32초 | off_track DNF | 308 | 0.2 |
| T2957 | 25.40초 | off_track DNF | 189 | 0.0 |
| T2958 | 24.48초 | off_track DNF | 226 | 0.2 |
| T2959 | 21.18초 | off_track DNF | 907 | 0.0 |
| T29510 | 18.94초 | off_track DNF | 597 | 0.0 |
| T29511 | 21.30초 | off_track DNF | 325 | 0.0 |

추가 완주 0·손실 17이다. 실제 종료는 off_track 17개·crash 1개였다. Off_track은 공식 무진행 사유이며 GT 없이 물리적 도로 이탈·정지·역진행의 고유 원인으로 해석하지 않는다. 모든 6,350개 평가 행동에서 pedal이 변경됐으며 지정 delta 식·최종 clip·steering/memory 보존을 검증했다. 동작하지 않은 head 비교는 아니다.

Teacher는 그 pedal과 함께 다른 조향을 실행할 것으로 예측했다. 첫 조향부터 도로별 84.0·92.0·89.8·93.3·87.0·86.2%에서 296과 달랐다. 학생은 그 첫 조향과 후속 teacher 조향을 실행하지 않는다. H12 plan이나 retained shadow suffix의 성공 예측을 pedal-only 학생의 성공으로 전이할 수 없으며, 후속 조향을 실제로 맞춘 대조도 없다. 이 불일치·source 복원 한계·회귀 근사·새 폐루프 상태 분포가 함께 남아 실패의 단일 원인을 분리하지 않는다. 이번 한 head가 실패했다는 결과이며 teacher transfer·학습 방법군 전체의 불가능성은 아니다.

실제 비용은 **8,104/12,000 native = 수집 1,754 + 평가 6,350**, raw step 32,413 / reset 1,224 tick이다. Collection wall 78.578초·evaluation wall 193.069초, runner CPU 합계 341.035초·legal actor CPU 69.490초·수집 teacher pixel actor CPU 15.985초를 기록했다. Source capture wall은 별도 cost JSON에 있다.

Offline teacher는 **25,550 source clone·1,224,796 positive-time physics tick·0시간 초기화 25,550회**, query CPU 528.857초(모델/순위 포함)·teacher phase wall 553.136초였다. Fit wall 0.0137초·CPU 0.0522초, zero replay wall 16.840초이며 zero replay의 actor CPU 전체 합은 저장되지 않아 미상으로 둔다. Zero replay native는 0이다. 단계별 wall은 측정 범위가 달라 전체 프로젝트 시간으로 대신하지 않는다. 추가 유료 자원·다른 환경은 0이다.

승인된 연구 +10,000을 반영한 종료 예산은 **누적 1,147,023 + 연구 잔여 8,977 + 최종 예비 84,000 = B1,240,000**이다. 예비 사용은 0이며 main·Participants·사용자 변경·이전 결과·백업과 모든 DEV 봉인을 보존했다. 공개에는 일반 코드와 집계만 포함하고 pixels·full capture·teacher 설정/라벨·model·ZIP·raw trace는 비공개다. 다음 판단은 현재 296 유지와 이 head의 폐기이며 자동 후속 실험은 없다.
