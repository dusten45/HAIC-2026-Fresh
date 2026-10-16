# 416 다음 최소 대조 제안 — 미실행·미예약

다음 후보의 baseline은 실패한 O tail이 아니라 **411에서 자격을 얻은 C 법칙과 기존 13행동 안전 guardian인 C0**로 한다. 비교 후보 Ctime은 같은 수치·phase·안전 계약을 쓰되, 같은 현재 상태에서 안전·진행·공통 exit를 통과한 recipe들의 도착 bracket을 비교해 이득이 확인된 첫 행동을 선택하는 방향이다. ‘nominal이 적격이면 무조건 통과’하던 C0에 시간 이득 선택을 추가할 수 있는지 한 상태에서 먼저 검사한다. 이것은 설계 제안이며 실행 파일·모델·실제 주행·예산 예약을 바꾸지 않았다.

첫 개발 상태는 저장411 C 경로에서 ‘원래 reference arc60–70%, 현재 C nominal brake>0, 현재 r−v≥5’인 첫 pre-state다. 미래 tire·미래 도착·실패를 선정 조건으로 쓰지 않는다. 저장 자료에서 해당 첫 상태는 **119번째 행동 직전**(원래 arc60.14%, r−v16.96m/s)이다. 이는 한 번의 개발 진입 상태 선정이며 배포 시점119 또는 arc 트리거를 정책으로 선언한 것이 아니다. 같은 C history118행동·full state·RNG·C memory를 재현한다. O의 상태를 C memory와 섞지 않는다.

한 상태에서 두 recipe만 등록한다.

- A: 현재 C nominal 첫 행동, 이후 자기 상태에서 C nominal 피드백13행동.
- B: 현재 nominal 조향은 유지하고 첫 행동만 gas1/brake0, 이후 같은 C nominal 피드백13행동.

branch의 memory를 실제 부모에 commit하지 않는다. 둘의 source13행동을 각각 독립 반복하고, 원래 arc의 진입+30m 공통 exit, 3.24m/13행동 진행, 기존 raw/post3m·도로·grass·충돌·손상·의미 있는 후진 기준을 지킨다. 모두 적격일 때만 bracket을 비교하고 B 상단이 A 하단보다0.08초 이상 빠를 때 다음 실제 대조를 제안한다. 실패 recipe 시간을 추정하지 않고 다른 pulse·시점·horizon·개발 창으로 재탐색하지 않는다.

선행 게이트는 실제 C prefix/nominal의 body·wheel·raw hull fidelity, 같은 계측 phase/COM metadata, 복원·독립성·부모/RNG 불변 및 phase/finish 계약이다. 416의 signed-sigma 대수 계약을 장래 구현한다면 A/B에 똑같이 적용하고 정상 영역의 기존 C 명령 일치를 다시 확인해야 한다. σ를0으로 자르지 않고, 의미 있는 후진 안전 중단과 r=0/LAUNCH/FINISH_CONFIRM/DONE 예외를 유지한다. 정확 vertex의 현재 거부 및 profile 기울기 점프는 남아 있다. 해당 상태에서 projection이 실제 보류되면 이 recipe를 중단하며 수치 epsilon으로 통과시키지 않는다. 별도 exact-input endpoint 분류 설계가 필요할 수 있으나416에서 구현하거나 자격 부여하지 않았다.

source를 통과하면 같은 prefix를 가진 실제 A/B 각각 한 번, suffix13행동만 대조하는 것이 최소 실제 범위다. prefix는 저장 C 명령을 재현하는 고정 GT 진단으로 둘 수 있으며 일반 배포 증거와 구분한다. 첫 변경 전이와13행동 source/actual body·wheel·raw hull 대조를 필수로 한다. 실제 suffix에서 기존 guardian의 더 먼13행동 예측이 개입을 바꾸면 그 사실·모델 비용·source와 달라진 명령을 기록한다. 예측 tail을 실제 guardian 동작과 같다고 가정하지 않는다. 시간 선택의 연속 반복이나 전체 lap 승격은 이 대조가 검증하지 않는다.

118 prefix+13 suffix의 실제 두 arm은 최소262 wrapper/reset2다. 단순 source prefix와 A/B 중복·후속 A 확인·부모 첫 전이만으로도736tick/6world가 필요하다. 이 수는 실제 suffix guardian의 추가 예측과 live-parent gate 비용을 포함하지 않은 하한이며 전체 비용 상한이 아니다. 다음 등록 전에 그 비용을 별도로 산정하고 hard cap을 정해야 한다. 지금은 어떤 native/model 자원도 예약하지 않는다. 국소 양성 이후에는 C tail을 포함한 carry 검증이 별도로 필요하며, 정지 재출발 대수·source 시간 순위만으로 안전한 완주·픽셀296 개선을 주장하지 않는다.

현재 C는 COM velocity와 origin projection을 사용한다는 [기준점 정정](domain416_point_contract.md)을 유지한다. 다음 대조의 두 arm은 동일한 이 기존 의미를 사용한다. origin velocity 수정까지 동시에 적용해 시간 선택 효과와 혼동하지 않는다. 현재COM식의수치검증을origin arc의exact chain-rule 증거로확대하지않는다.
