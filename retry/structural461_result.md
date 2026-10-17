# 461 — reference·추종·경로/제어 구조의 저장 분석

**새 실제 행동/reset/model tick/world/seed/학습/HOLDOUT/SEALED/예비/유료 자원0이다.** 실제442P13.760초와458P14.000초를 저장 raw 자료로만 분석했다. 공통 후반 정책에서 초기 pulse의 hybrid 이득이 남은460 결과를 유지하며, 초기 pulse 단독 손해라고 해석하지 않는다. 다음 한 실험은 [통합 계약](design461_next.md)으로만 동결했고 실행하지 않았다.

## 시간 항등식: 무엇이 차이를 차지하는가

기존 canonical projection의 COM velocity·tangent 내적sigma, body forward `[-sin(angle),cos(angle)]`, COM/origin raw hull 정의를 유지했다. 동일 frozen reference의 squared-speed 선형 보간을 구간별 정확히 적분한 `rho(s)=∫ds/r(s)`를 reference clock으로 정의한다. 이 clock과 아래 합성 항등식은 이번 저장 계산의 signed bookkeeping 규약이며 유일한 분해나 인과 기여가 아니다.

positive-progress FIRST_LAP의 각20ms interval에서 `D=Δrho/Δs`, COM speed `v`, body forward와 tangent의 cosine `c`, origin velocity의 tangent 성분 `sigma_o`라 두면

`dt = Δrho + dt(1-vD) + dt*v(1-c)D + dt(vc-sigma)D + dt(sigma-sigma_o)D + [dt*sigma_o*D-Δrho]`

다. 각각 reference clock·속도 추종·heading·body-slip 보정·origin/COM 보정·geometry/sample 잔차다. 마지막 항에는 유한 interval/투영 노드/kinematics 차이가 남는다. 음수 항을0으로 바꾸거나 잔차를 숨기지 않는다. 각 interval과 집계의 폐쇄를 검증했다.

|항, 초|442P|458P|458P−442P|
|---|---:|---:|---:|
|reference clock|8.946947|8.947897|+0.000950|
|속도 추종|3.097247|3.346947|+0.249700|
|heading|0.047969|0.036004|−0.011965|
|body-slip 보정|−0.006336|−0.006359|−0.000023|
|origin/COM 보정|−0.001042|−0.000977|+0.000065|
|geometry/sample 잔차|−0.104783|−0.103511|+0.001272|
|**적격 interval 합**|**11.980**|**12.220**|**+0.240**|
|공통pre23까지 관측 prefix|1.760|1.760|0|
|profile 끝을 가로지르는 제외 interval|0.020|0.020|0|
|**자기 official native lap**|**13.760**|**14.000**|**+0.240**|

마지막 제외 interval과 confirmation 영역에 FIRST_LAP 식을 외삽하지 않았다. 두 적격 interval의 마지막 공간점이 조금 달라 reference clock에도0.000950초 차이가 있다. 정확히 같은pre23→profile end의 reference clock은 두 경우 모두8.960214초다. heading/body-slip의 직접 projection 항이 작다는 결과가 steering/경로/횡력이 속도에 미치는 간접 영향을 배제하지는 않는다.

공통 공간 경계의20ms 실제 통과 bracket에서 prefix1.76초와 같은reference clock을 빼면 다음과 같다. 보간하지 않았고 두 arm의 common boundary는 같다.

|pre23 대비m|442P reference 대비 초과|458P reference 대비 초과|
|---:|---:|---:|
|450|2.441–2.461|2.081–2.101|
|510|2.620–2.640|2.320–2.340|
|570|2.723–2.743|2.543–2.563|
|630|2.762–2.782|2.762–2.782|
|690|2.888–2.908|2.988–3.008|
|750|2.898–2.918|3.098–3.118|

즉 추가0.24초는 이 규약에서 주로 longitudinal speed deficit로 나타난다. 이는 실제 선택·이력·reference/힘 근사·sample hold가 섞인 결과이며 speed controller가0.25초를 독립적으로 낭비했다는 인과 주장은 아니다.

## 원래 식과 reference의 제약 의미

[profile 생성](racing258_plan.py)의 곡률 상한은 `min(100,sqrt(lateral_allowance/abs(curvature)))`이고, 정지 출발/제한하지 않은 finish 속도에서 고정4회의 backward brake·forward drive 전달을 한다. [질량/allowance 구성](racing258_run.py)은 실제 source 질량과 rolling wheel inertia를 근사해 상수 drive/brake/lateral allowance를 만든다. 도로 폭·차량 footprint·obstacle clearance·steering curvature는 고정 line의 feasibility 문제이며 현재 actual tracking의 exact tyre 제약을 직접 푸는 것은 아니다.

[frozen pace 생성](pace268_profile.py)은 all-road/grip1·축별 하중 분담·근사 공동 마찰 특징을 사용해 노드를 배율 조정한다. [실제 연결](paired417_common.py)은 free_profile.speed에 그 pace를 곱하며 다시 제약에 투영하지 않는다. 현재 scaled squared-speed gradient는−223.40..+106.92m/s²이고,238개 segment 중54개가 원래 brake allowance의 크기를,166개가 상수 drive allowance를 초과한다. scaled lateral demand/base allowance 최대비는2.417이다. allowance 자체에 보수 계수가 있으므로 이 숫자를 실제 물리 위반 개수나 안전 상한으로 해석하지 않는다.

기본 profile clock15.316710초는 pace 후10.027245초가 된다. 이는 원하는 profile의 clock일 뿐 달성 가능 시간·전역 하한·11.99초 가능성 증명이 아니다. 따라서 실제 lap와의3.73/3.97초 차이를 모두 추종 결함이나 회수 가능한 시간이라고 부를 수 없다.

[현재 executor](signed417_executor.py)는 `ff=f*sigma/r`, `raw=ff+1.5*(r-v)`이고 [pedal map](scalar392_audit.py)은 이를 clipping한 뒤 gas/brake로 근사 변환한다. canonical position은 hull origin, velocity는 COM이다. 기존 sigma와 실제 origin arc 변화의 차이는 위 보정/잔차에 공개했다. launch/finish는 별도 정의역이다. 검증 가능한 nominal pedal은 저장값과 float32로 exact 일치했다.

[source wrapper](source_vehicle_transition.py)는 같은 명령을4rawtick 유지하지만 [Car](../core/vendor/car_dynamics.py)는 매 tick gas 상승≤0.1, 즉시 gas 하강, wheel omega brake, 종·횡력 공동 vector clipping을 처리한다. 그래서 요청 가속도는 실제 차체 가속도의 exact 역함수나 안전 cap이 아니다. raw20ms 속도 변화로 actuator를 새로 식별하지 않았다.

## target 미만 braking과 실제 제어 반응

명목식이 under-target braking을 요구한 action은442P34개,458P37개다. 그중 현재 action을 포함한 저장 H13의 target 최소가 초기 속도보다 낮은 경우는26/24개다. 이들에는 미래 곡선 감속 준비라는 설명이 충분히 남는다. 이13action 범위는 관측 진단일 뿐 더 먼 미래/경로/마찰 안전을 증명하지 않는다.

반면 nominal brake를 유지하는 action 안에서 현재 상태로 식을 다시 계산하면 가속이 되는 노출은442P5action/0.20초,458P7action/0.32초다. 다음 sample에 신호가 바뀐 사실은 구조적 불일치의 관측 근거이며 그 brake를 제거해도 안전하다는 증명은 아니다.

458P의 선택 rootpre126은 +522.612m, prefix10.00초다. 첫80ms에 속도가 약7.74m/s 감소했고, 뒤60ms에서는 재계산 raw 식이 가속을 요구한다. 저장된 이후13명목 target 모두가 초기 속도보다 높다. 이 구간에는 target 저하를 미리 준비한다는 설명이 상대적으로 약하다. 다만 더 빠르게 갔을 때의 actual 힘/접촉/경로 결과는 미관측이다. 같은 구간 첫 action에서 바퀴 하나 이상 clipping은2rawtick이었고 이후13행동은 모두 nominal이었다.

시간 항을 실제 선택별로 교차 집계했다. nominal 명령 아래 속도 추종 항은442P3.0210초,458P3.2530초이며 fullgas 아래는0.0495/0.0366초다. 그 상태는 이전 선택의 영향도 받으므로 명령별 독립 효과가 아니다. 전체 적격 구간의 실제 brake 노출은2.96/2.80초, clipping1.70/1.18초다. 더 빠른442P에서 이 노출이 더 크므로 단순히 brake/clipping을 적게 하면 빨라진다고 결론낼 수 없다. gas ramp 부족 적분0.4425/0.4792는 **pedal 차이×초**이며 잃은 lap 초가 아니다. 모든 제어별 시간 항은 JSON에 남겼고 시간 분해와 중복 합산하지 않았다.

## 두 구조 가설 중 하나 선택

**H2A: reference/힘/경로의 근사 가정 불일치.** pace 뒤 reference의 속도/gradient·횡력 요구가 exact coupled tyre/actuator/경로 응답과 어긋나 큰 속도 deficit을 낼 수 있다. 현재 자료는 이 가능성을 보여주지만 feasibility 재계산이나 actuator 식별을 완료하지 않았다. path/steering은 유지하고 가설을 보류한다.

**H2B: 시작점 미분 feedforward와80ms hold의 불일치.** piecewise squared-speed 노드의 기울기가 바뀌는데 시작점 ff를 유지하는 것이 일부 구간에서 brake를 과도하게 지속할 수 있다. 선택한 root는 저장 evidence가 명확하고 기존 recipe로 표현 가능해 가장 작은 반증에 적합하다.

저장 pure 계산에서 `[r(s+sigma*.08)-r(s)]/.08`만으로 ff를 바꾸면 qualified action149/152개 중24/27개의 pedal이 달라진다. under-target braking 중 원래 brake가 유지되는 action은34/31개라 음의 ff 일괄 삭제가 아니다. 이는 각 저장 상태에서의 대안 명령 계산이고 궤적 평가가 아니다. pre126의 대안 전체 float32 명령은 기존 fullgas first recipe와 exact 같다. 다음 비교는 이 한 action만 바꾸고 이후 동일 guardian를 사용한다. secant 법칙을 전체 궤적에 적용하는 실험으로 확대하지 않는다.

## 비용·공간·재현·보존

현재 분석은 [재현 코드](analyze461.py)와 [하나의 통합 저장 gate](static461.py)로 수행했다. constructor/step/native env를 금지한 상태에서도 과학적 집계가 exact 재현됐고, 항등식 폐쇄·nominal 식·root state/memory/ledger·full float32 recipe alias·다음 비용 산식이 통과했다. 변경하지 않은 입력 hash는 private manifest와 공개 집계에 묶었다. source9개와 protected/original18개의 hash도 확인했다. 최종 저장 분석 측정은CPU3.360초/wall3.367초(입력370개)이며 physics 비용은0이다. 통합 저장 gate 비용은 공개 gate에 별도로 남겼고 개발/보고/Git 전체 overhead를 완전 계측했다고 주장하지 않는다. raw state/명령벡터/좌표/seed/RNG는 공개하지 않았다. 전체 원논문을 새로 읽었거나 다른 방법 전체가 실패했다고 주장하지 않는다.

다음 **설계만**의 planned는43650ticks/839worlds, 제안 hard49152/896·CPU1800초/wall2400초·순차1·actual0이다. 각 query 독립2회를 유지한 두 whole parent 각1회이므로 whole-arm 반복 성공을 주장하지 않는다. source qualification1458/41, fixed-first2query208/4, guardian198query41184/792, parent800/2를 모두 포함했다. 독립 비용 검토도 일치했다. 정책 JSON에서 예산을 계산하며 planned가 hard를 넘거나 산식에 누락이 있으면 적분 전에 실패한다.

공간은 읽기만 점검했다. 현재 `/tmp` 약5.47GB, workspace 약1.74GB 여유다.457 raw3162796546bytes/48689ticks와460 raw3821319539bytes/67343ticks 중 최대64959.16bytes/tick을 사용했다. hard49152×관측최대×1.25+512MiB reserve=약4.528GB라 현재 `/tmp`에 조건부로 들어간다. 짧은 world의 고정 receipt/header 등 때문에 경험적 추정은 보장 upper bound가 아니다. 다음 시작 직전 free를 다시 읽고 공간/IO 오류면 전역 중단하며 삭제/이동/재시도/상한 확대/새 유료환경을 쓰지 않는다. tmp 공유/영속성을 가정하지 않으며 raw 소실은 재현 한계다. 코드·집계·hash와 full private manifest는 workspace에 보존한다.

v474 연구26695·예비84000/사용0과main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·사용자 변경·원본/백업/보호자료를 유지했다. 종료2026-10-20 19:01:55 KST 이후 새 실험·자동 연장 없음이다. 지금까지 확인한 dominant time 항과 국소 hold 충돌을 남겼으며, actual 일반화와 남은1.77–2.01초 전체 원인은 여전히 미해결이다.
