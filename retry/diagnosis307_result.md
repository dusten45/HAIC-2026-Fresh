# 307 — 306 실패 분해와 다음 큰 방향

**새 head/teacher 학습보다 longitudinal control의 참조 진행 위상을 먼저 반증한다.** 306의 0/18은 유지한다. 이번에는 저장된 581 라벨·6,350 rollout 행동과 원본 코드만 읽었으며 native·source physics·teacher query·fit은 모두 0이다. 아래 분포는 기술 통계이며 새 정책 점수나 검증 성공을 만들지 않는다.

306 라벨 상태의 평균 gas/brake와 최종 출력 fit 오차는 다음과 같다. Raw teacher pedals는 그 teacher의 첫 조향과 H12 후속 조향 아래 선택된 명령이다. 296과 첫 조향이 84~93%에서 다른 것은 **조작의 결합 증거**이며, 그 조향 불일치가 0/18의 실제 단독 원인이라는 인과 대조는 없다.

| 수집 TRAIN | 296 평균 g/b | teacher 평균 g/b | fit 출력 평균 g/b | fit MAE g/b |
|---|---:|---:|---:|---:|
| T2950 | 0.466/0.075 | 0.242/0.258 | 0.305/0.117 | 0.278/0.259 |
| T2953 | 0.490/0.078 | 0.278/0.085 | 0.301/0.116 | 0.270/0.127 |
| T2956 | 0.495/0.078 | 0.354/0.075 | 0.311/0.098 | 0.299/0.123 |
| T2959 | 0.507/0.079 | 0.347/0.105 | 0.317/0.113 | 0.288/0.129 |
| O0 | 0.496/0.078 | 0.342/0.061 | 0.312/0.107 | 0.283/0.117 |
| O2 | 0.488/0.076 | 0.292/0.079 | 0.309/0.117 | 0.261/0.132 |

도로균등 label MAE는 원래296 gas/brake **0.347/0.142 → head 0.280/0.148**, head RMSE는 **0.319/0.196**이다. In-sample에서도 brake MAE가 좋아지지 않았다. Label 상태 delta ±0.5 clip은 두 채널 모두 0%, 최종 clip은 gas 0~1%·brake 2.0~3.2%다. Teacher의 동시 양수 pedal은 0%인데 fit 출력은 96.8~98.0%다. 이는 분리된 가속/제동 명령을 affine 평균이 혼합하는 근거다. 동시 pedal 제거 236·246·257 및 guard301/303도 이미 실패했으므로 같은 후처리를 다시 제안하지 않는다.

Rollout 전체에서 delta clip은 gas **52.52%**, brake **3.42%**, 최종 clip은 **1.83%/7.65%**다. 581 label의 각 feature min/max를 하나라도 넘는 행동은 **22.68%**(도로균등 19.71%)이며 도로별 0.37~56.14%다. Coordinate box 안도 joint feature 조합이 학습됐다는 뜻은 아니고, 밖도 실패 원인으로 판정한 것이 아니다. Z>3 진단과 mean/p10/median/p90·실제 correction 크기는 JSON에 있다.

모든 도로에서 반환 pedal의 큰 차이(max채널 절대차 ≥0.1)는 **첫 native1**에 시작했다. 첫 범위 이탈은 아래처럼 그 뒤다. 예를 들어 O0 첫 입력에서 같은 상태296의 gas/brake 0.578/0.027이 0.455/0.061로 바뀌었다. ±0.1은 사후 기술 통계 정의이며 제어나 승격 문턱으로 쓰지 않았다. **회귀 외삽 이전부터 큰 개입이 있었으므로 OOD만으로 실패를 설명하지 않는다.** 범위가 거의 안 벗어난 T2950/T2954/T2955/T2956 등도 DNF였다. 초기 몇 행동의 raw 기록은 비공개로 남겼다.

| TRAIN | feature box 이탈 | gas delta clip | brake delta clip | 첫 box 이탈 native |
|---|---:|---:|---:|---:|
| O0 | 0.8% | 5.7% | 0.0% | 161 |
| O2 | 39.2% | 80.9% | 0.0% | 221 |
| N0 | 49.4% | 72.7% | 14.2% | 175 |
| N1 | 56.1% | 84.9% | 0.0% | 126 |
| N2 | 40.1% | 67.4% | 19.2% | 86 |
| N3 | 0.8% | 41.8% | 0.0% | 144 |
| T2950 | 0.4% | 58.8% | 0.0% | 82 |
| T2951 | 34.8% | 26.0% | 0.0% | 254 |
| T2952 | 3.6% | 0.5% | 0.0% | 214 |
| T2953 | 23.1% | 63.6% | 0.0% | 166 |
| T2954 | 1.1% | 51.6% | 0.0% | 85 |
| T2955 | 0.4% | 36.2% | 0.0% | 167 |
| T2956 | 0.6% | 32.8% | 0.0% | 208 |
| T2957 | 1.6% | 2.1% | 0.0% | 88 |
| T2958 | 48.7% | 42.5% | 0.4% | 111 |
| T2959 | 17.2% | 63.1% | 2.9% | 230 |
| T29510 | 35.0% | 62.1% | 4.9% | 62 |
| T29511 | 1.8% | 60.6% | 0.0% | 149 |

224는 teacher 궤적의 오프라인 모방 오차가 줄었으나225 실제 학생은1/4였다. 226 pedal-only는 F2를23.02초에 완주했지만 F1은 전 타일 방문 뒤에도 finish 없이 DNF였다. 229는 학생 상태 재라벨링473개에서 gas MAE 일부 감소·brake 증가를 보였고 집계 head의 새 closed-loop 결과는 없다. 249의 frozen-steering H12 frontier 이득은250의 여섯 실제 짧은 pulse에서 확인됐지만 lap 이득은5/6·평균 −0.213초였다. 이를 연속 affine으로 만든251은0/8이다. 281의 실제 끝까지 outcome 라벨도3/4 위치에서251과 달랐으며, 그것을 일반화하거나 categorical macro를 새 이름으로 반복할 근거가 아니다(290 최종0/8). 따라서 또 다른 first-action pedal 회귀, 동일 pulse classifier, 단순 head 용량/clip 변경을 다음 방향으로 택하지 않는다.

원본 환경에서 physics는50 FPS·20ms, native는최대4 tick·80ms다. 공식 lap은 카메라 준비 뒤 simulation time부터 결승선 중심 통과 tick까지다([README](../README.md), [runner](../local_runner.py)). 95% 고유 타일은 자격뿐이고 출발 영역 이탈→뒤쪽 진입→정방향 중심 통과→앞쪽 영역 이탈이 필요하다. Forward speed>1e−4·lateral/forward≤4와 결승선 폭 조건도 있다([finish](../core/finish_line.py)). 101회 연속 음수 native 보상이 off_track이며 도로 바깥과 동일하지 않다([wrapper](../env_wrapper.py)). Reward의 tile 보너스는 공식 lap 순위가 아니다. 경로는 그 자격·finish·retire와 road/grass 물리·장애물을 만족해야 하며, 정확한 중심선 전체 길이를 반드시 따라야 하는 규칙은 아니다.

현재 TRAIN O0/N0의 이미 측정된258 선택 free reference 길이는 **1,142.06/1,150.46m**다. 이는 현재296이 실제 달린 거리나 전역 최단 자격 경로가 아니다. 현재296의18개 실제 주행거리 합계는 기존 공개 결과에 없다. 296의 speed goal/ceiling과 near/curvature 법칙은 controller 선택이며 최종 learned pedal이 실제 속도를 강제하지 않는다. Source의 engine/friction·wheel actuator와265에서 확인한 설치 Box2D **2m/20ms=100m/s** 수치적 translation ceiling은 별개다. Car front-joint ±0.4rad·motor3rad/s도 별개다([dynamics](../core/vendor/car_dynamics.py)). 선택 경로의 거리/평균속도나 L/100을 전역 lap 하한·10초 불가능 증명으로 쓰지 않는다.

258 free GT actual O0/N0 **21.86/22.12초**,259 최소 변위 reference **22.52/21.74초**로 경로 목적 변경의 평균 차이는0.14초이고 방향도 섞였다. 265 동일258 경로의1.5 pace는 **19.70/20.20초**,268 frozen condition pace는 **19.40/19.90초**였다. 269는 O2/N1/N3 **18.52/14.78/15.94초**를 보였지만 N2는 fixed solver infeasible로 미실행이다. 같은 경로 constant1.5는 O2/N1에서 target52.37/72.75m/s인데 gas0/brake0.3로 거의 정지해 DNF였다. 이는 낮은 tracking error·양의 목표 속도가 완주를 보장하지 않는 실제 근거다. 266 acceleration clamp 제거는2/2 DNF,267 위치 pace knots는40ms training gain 뒤 transfer+2초였으며 다시 제안하지 않는다.

큰 합법 개선의 축을 모두 확보했다는 결론은 아니다. **Reference path 단독**은258/259에서 일관된 큰 이득을 보이지 않았고271의 GT경로→240 이식도2/2 느렸다. **Longitudinal reference/진행 위상**은 같은 경로265~269에서 큰 차이와 정체를 보여 먼저 분리할 가치가 있다. **Perception/phase state**는 그 효과를 pixels로 옮길 때 실제 참조 진행 속도를 얻는 미해결 조건이다;260~262·263·270·305 실패가 있어 있다고 가정하지 않는다. **다른 policy 학습**도276·278·290과 이번306 실패 뒤, 새 head/RL를 바로 더 돌릴 근거가 약하다. 이는 각 방법군의 불가능성이나 GT 기록이 legal 정책으로 전이된다는 주장은 아니다.

다음 실험 **하나만 제안**한다. 258 cached feasible 경로와 constant1.5 profile·기존 follower를 고정한 **5 TRAIN(O0/N0/O2/N1/N3) GT 진단**에서 spatial feedforward의 진행 위상만 바꾼다. 현재 [258 follower](racing258_run.py)와 [269 follower](pace269_run.py)는 `a_ff=(q_next²−q_here²)/(2ds)=q*dq/ds`를 쓰며 실제 속도가q보다 작아도 같은 음의 feedforward를 낸다. 제안은 q>0에서 이를 `v_parallel/q`로 곱하는 것이다. v_parallel은 현재 GT velocity의 선택 선분 tangent 투영이며, q==0의 standing-start singular boundary는 원래feedforward를 유지한다. Norm-speed feedback·gain·양/음 acceleration clamp·gas/brake inverse·steering/cursor/메모리·path/profile·lap-wrap branch는 그대로다. 완벽한 phase tracking을 가정한 원식을 실제 phase advance에 연결한다는 **가설**이며 증명된 코드 버그 수정은 아니다.

기존265/269 constant1.5 기준 **3/5 완주**를 재사용하고 후보만5회 실행한다. 완주 수 증가 또는 동률의 공통 완주 평균 시간 엄격한 개선이면 가설을 남기고, 같거나 나쁘거나 미상일 때 변형 없이 닫는다. N2의 기존 solver-blocked 상태는 유지하며 DNF로 세지 않고 새 solve도 하지 않는다. 예상 **약1,250 native·약1분**, 제안 cap4,000은 현재 잔여8,977 안이다. 새 source forecast physics·geometry solve·fit은0이며 실제 simulator 비용은 반드시 native로 센다. 224~251/306 pedal 라벨 전이,266 clamp 해제,267/268 pace parameter 탐색,263/270 pixel profile/goal 이식,261/305 경로 기억과 다르다. GT 진단일 뿐 제출 정책이 아니고, 양성이어도 legal phase 추정의 별도 근거 없이는 distill·승격하지 않는다. **아직 구현·등록·실행하지 않았다.**

이번 집계 계산 wall **0.149초·CPU0.174초**는 analyzer 범위이며 원문 읽기·판단·문서/git 시간을 포함하지 않는다. Native/source physics/fit/query는0, 연구 잔여 **8,977**, 예비 **84,000**·현재296·240 rollback·DEV/HOLDOUT/SEALED와 main/Participants/사용자 변경/기존 결과를 보존했다. 원시 trace·모델·window·개인 자료는 비공개이며 공개는 일반 analyzer와 집계다.
