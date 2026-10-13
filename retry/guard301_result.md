# 301 — near nominal-zero gas guard의 고정 pilot

**pilot gate가 탈락해 나머지 16 TRAIN은 실행하지 않고 종료했다.** guard는 T2950을 완주했지만 기존 296이 완주한 T2954를 잃었다. 두 정책은 각각 1/2 완주이며 공통 완주 도로가 없어 시간 개선을 비교할 수 없다. champion296·DEV 봉인·240 rollback은 유지했다.

기존301 실행이나 stage 디렉터리가 없는 것을 확인한 뒤 한 번만 등록했다. 정확한 296의 원래 모듈을 그대로 포함하고, 최종 반환 단계에 `feature8 == 1 and feature14 == 0`일 때 gas만 0으로 하는 wrapper를 추가했다. feature8은 기존 near flag, feature14는 같은 호출의 nominal gas다. steering·brake·계수·perception·head·직접 controller memory는 변경하지 않았다. 이후 관측이 바뀌므로 과거 baseline의 전체 steering/brake stream까지 같다는 주장은 아니다.

T2950/T2954 후보 두 주행을 공식 종료까지 평가했다. 기준은300에서 새 신호와 함께 수집한 정확한 296 결과를 재사용했다. 완주 수가 더 많거나, 같은 수에서 공통 완주 평균 시간이 엄격히 짧을 때만 남은 16 TRAIN을 실행하도록 사전에 고정했다. 전체 cap은 6,000 native이며 이번에는 champion 변경과 DEV 평가를 허용하지 않았다.

| pilot | 300의296 기준 | gas guard |
|---|---|---|
| T2950 | 실제 off_track DNF / 315 native / damage0.2 | 26.66초 완주 / damage0.0 |
| T2954 | 27.44초 완주 / damage0.0 | 실제 off_track DNF / 184 native / damage0.4 |

**paired 추가 완주 1·손실 1, 공통 완주 0**이다. 26.66초와27.44초는 서로 다른 도로의 성공 시간으로 평균 속도 개선의 근거가 아니다. 특정 baseline 도로 손실을 독립 veto로 사용한 것이 아니라 완주 수 동률과 시간 비교 불가능 때문에 사전 gate가 탈락했다. 남은 16개 결과를 DNF나 미완주로 계산하지 않았다.

guard는 T2950에서48개 행동(첫 활성 69), T2954에서13개 행동(첫 활성 21)에 적용됐다. T2950의 접촉은 0, T2954의 접촉은native 83/86 두 번이었다. T2954 종료 시 guard는 비활성이었고 반환 gas는약 0.633, HUD feedback 속도는 0이었다. 실제 GT 위치·wheel·진행은 이번에 수집하지 않았으므로 현재 정지/접촉의 물리적 고유 원인이나300과 동일 위치의 첫 이탈을 복원하지 않았다.

300에서 관측한 nominal-zero/최종 양의gas 불일치를 제거하는 개입은 한 도로의 충돌/완주 결과를 바꿨지만 다른 도로의 완주를 잃었다. 단순히 그 관계를 강제하면 두 실패가 함께 해결된다는 가설은 이 pilot에서 지지되지 않는다. 개입은 옛 충돌 직전만이 아니라 더 이른 행동부터 작동하므로 T2950 회복을 마지막 접근 구간 gas 하나의 순수 효과로 단정하지 않는다. guard 방법군 전체나 기존 목표/관측 설계의 불가능성을 주장하지 않는다. 다른 gate·계수·후보를 추가 평가하지 않았다.

검증은296 원모듈·모델·계수의 정확한 보존, 기존 상태에서 계산한 before/after와 지정 식, 모든 518개 행동의 steering/brake 및 memory 보존, 두 공식 종료 결과, gate 재계산, 프로세스 회수와 compile을 확인했다. guard 활성 및 gas 변경은 61개 행동이었다. 기술 오류·예산검열·중복실행은0이다.

실제 비용 **518/6,000 native**, raw step2,070/reset102 tick, source model physics·새 parameter draw·유료 자원 0이다. 전체 실제 wall 20.541초, episode runner CPU 합계 25.118초, 별도 actor CPU 5.458초다. 두 병렬 episode의 wall 합계 32.221초는 전체 경과시간과 다르다.

종료 누적 **1,137,085 + 연구 잔여 8,915 + 최종 예비 84,000 = B1,230,000**이다. 예비·HOLDOUT·SEALED·297 DEV 12·다른 환경을 사용하지 않았으며 main·Participants·사용자 변경·기존 백업과296~300 원결과를 보존했다. 공개는 일반 코드와 집계만 포함하고 모델 parameter·ZIP·raw trace·도로 identity는 비공개로 보관한다.
