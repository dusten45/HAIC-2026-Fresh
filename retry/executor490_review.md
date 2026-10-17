# 490 실행기 입력에 대한 독립 정적 검토

검토 범위는 소스 식과 소비 인터페이스이다. 489 후보 좌표나 성능 자료를 열지 않았으며, 함수 import/호출, 테스트, 경로 생성·변환·탐색, 프로파일 계산, world 생성·reset·step을 하지 않았다. 아래 수치 식은 소스 계약이며 새 후보에 대한 측정 결과가 아니다. 현재 허용된 구성 결과는 실행기 **입력**이며 주행 가능성의 인증이 아니다.

## 입력의 동일성과 소비 경로

`racing258_plan.py:33–43`의 `profile`은 입력 polyline의 닫힌 각 변 길이와 꼭짓점 곡률에서 N+1 속도 노드를 만든다. 초기 속도만 0이고 마지막은 자유 종료 속도이다. 정확히 네 번 역방향 제동/순방향 구동 패스를 시행한다. 경로가 닫혔다고 속도 노드 0과 N을 같게 만들면 계약이 바뀐다.

`pace267_profile.py:4–12`는 8개 pace knot의 주기 보간이며, `pace268_profile.py:4–21`은 세 고정 계수와 곡률·가감속 압력 특징을 사용하는 다른 함수이다. 490에서는 등록한 기존 계수와 후자의 정확한 출처를 고정해야 하며, 두 레시피를 혼용하거나 재학습해서는 안 된다. 특징의 lateral/drive/brake는 all-road/grip1 및 동일 axle lateral load를 가정한 대리량이다. wheel contact나 순간 tire force 인증이 아니다.

`paired417_common.py:18–23`의 `policy`는 `CoherentExecutor` 생성 후 `nodes = free_profile.speed * pace`로 다시 지정한다. 따라서 최종 P4 노드가 이 경로를 통하여 이중 pace 배율 없이 전달되는지, 최종 소비 노드의 float64 bytes와 SHA를 별도로 확인해야 한다. 생성자 검증은 이 재지정 이후 노드에 자동 재실행되지 않는다. 입력 gate에서 N/N+1 크기, finite/nonnegative, launch 0/그 외 양수, 양의 모델 상수, ds와 실제 line 변 길이의 원래 연산 순서 일치, source별 L 누적합 규약을 명시한다. frozen 489 line의 직렬화 bytes와 소비 line bytes는 일치해야 하며 spline/resampling을 끼우지 않는다.

## 투영과 연속성의 한계

`signed417_executor.py:12–28`과 `executor397.py:12–28`의 투영은 닫힌 모든 선분에 대한 전역 최근접이다. exact float64 거리 tie가 동일 꼭짓점으로 귀착하면 정해진 한쪽 선분을 선택하고, 서로 다른/비인접 최근접점 tie는 domain error이다. 일반 꼭짓점은 outgoing, FIRST_LAP/FINISH_CONFIRM의 node0은 incoming terminal이다. near-tie를 검출하거나 tolerance로 합치는 규칙은 없다.

비자교 경로라도 멀리 떨어진 두 선분의 Voronoi 경계를 지나는 off-reference 위치에서는 최근접 선분/arc가 불연속 전환할 수 있다. **유일 최근접**이라는 한 점의 조건과 단순 polyline만으로 전체 off-reference tube에서 투영의 연속성은 보장되지 않는다. `_advance`의 shortest-period unwrap(`signed417_executor.py:37–43`)도 이러한 전환을 올바른 주행 진도로 인증하지 않는다. 정확히 반주기만 거부하며 그보다 작은 비물리적 arc 이동은 자동 거부하지 않는다.

`_reference`는 같은 선분에서 squared-speed를 선형 보간하고 `f=(v[j+1]^2-v[j]^2)/(2 ds[j])`를 쓴다. 공유 노드의 target r은 일치해도 tangent, sigma=velocity·tangent 및 f는 꼭짓점에서 바뀔 수 있다. `act:82–85`는 `f*sigma/r+1.5*(r-speed)`를 pedal로 바꾼다. 이는 고유 interior 선분에서의 point-derivative 법칙이며 80ms held action의 정확한 secant나 연속 가속도 보증이 아니다. 417은 sigma<-0.1만 거부하지만 397은 sigma<0을 거부한다. 사용하는 실행기와 별도 safety gate를 명시하고 이 차이를 숨기지 않는다. finish 후보/확인/공식 DONE은 별도 tracker와 history 인증을 필요로 한다.

권장 정적 진단은 노드 양쪽 r/f/tangent/sigma 식, 비인접 경쟁 투영 거리 gap 및 arc 차이의 정의, source seam/phase 규칙이다. 향후 실제 관측에서는 pre-position·COM velocity에 대한 최근접 선분/두 번째 경쟁 선분, 정확 tie, 가까운 경쟁 gap, arc delta, cursor와의 불일치, raw/command accel과 clipping을 기록한다. near-tie gap은 진단값이며 새 fallback·정책 선택 규칙이 아니다. 임의 off-reference 위치를 검사하지 않은 결과에 전 tube 보증을 붙이지 않는다.

## P4와 가감속 경계

`analyze466.py:8–15`의 `project_four`는 기존 속도 상한 노드를 감소시키는 고정 네 번 패스이다. 역방향은 상수 brake_accel, 순방향은 왼쪽 노드 속도의 `min(rear_traction_accel,80000/(v+2.7)/effective_mass)`를 사용한다. 이는 4 m/s² 제한도 고정점 수렴 인증도 아니다. 마지막 순방향 감소가 이웃 제동 잔차에 미치는 영향까지 포함해 최종 모든 discrete forward/backward q 잔차를 따로 보고해야 한다. 실제 네 패스 후 실패한 잔차를 추가 패스로 보정하면 승인 범위를 벗어난다.

`scalar392_audit.py:pedals`는 raw 가속도를 상수 drive/brake 경계로 clip하고 gas/brake를 각각 [0,1]로 제한한다. 부호에 따라 한쪽만 양수이다. engine 제한은 gas clip에 다시 나타나므로 clipped scalar acceleration과 실제 실현 가속도는 동일하지 않다. 구간 내 속도 상승 시 왼쪽 속도 기준의 engine 상한이 구간 전체의 상한을 인증하지 않는다. 최종 노드·ds에서 두 q 잔차, 구간 engine worst-endpoint demand, 동일 위치 lateral/longitudinal/combined circle 대리량을 구분해 보고하는 것이 적절하다(`analyze466.py:17–32`). 대리량 통과도 동역학 인증은 아니다.

`bootstrap485.py:43–47`의 mass/effective_mass는 기존 native car의 저장 질량 출처로 고정할 수 있으며 새 car를 생성할 필요가 없다. wheel 회전 관성의 등가 질량과 hull+wheel 병진 질량은 서로 다른 역할이다. `core/vendor/car_dynamics.py:152–158,174–231`에서 steering servo rate가 제한되고 gas/brake가 wheel angular velocity를 바꾼 뒤 longitudinal/lateral force가 공동 clip된다. 따라서 정적 curvature/profile/drive/brake 경계만으로 steering lag, slip, off-road grip, force competition 또는 충돌 회피를 보장할 수 없다.

## 향후 별도 승인 시 최소 게이트 제안

1. 같은 이미 알려진 DEV 조건과 정확한 frozen line/profile/pace/P4/model/소스 SHA를 사용한다. 이번 구성의 데이터 선택이나 경로 변경을 하지 않는다. input schema·source gate 실패는 중단이며 새 후보 생성은 없다.
2. fresh source는 한 번의 계상된 native 준비에서 full state/memory/RNG/GoalLedger와 첫 전이를 인증한다. 기존 world를 몰래 재사용하지 않고 reset 내부 warmup까지 charge한다. 독립 cold restore 두 개와 held-first 재현을 같은 출처 context에서 선행 인증한다. warm 연속 실행의 controller/history·pending/finish와 모델 실제 continuation을 cold 검사와 구분한다.
3. 선행 source/cold/warm 검증을 통과한 경우에만 별도 고정 상한의 단일 native continuation을 검토한다. charge-before-call, fact commit-before-forecast comparison, 50Hz raw/80ms action 경계, terminal 1–4 tick 예외, 최종 cleanup 포함 시간·저장 cap을 사전 등록한다. geometry 통과를 whole/native 통과로 승격하지 않는다.
4. margin 정책 비교는 그 후 새 계약으로만 연다. CONTROL/variant는 동일한 state·before-memory·ledger·RNG와 동일 candidate bitset/eligibility/first command repeat proof를 공유해야 한다. root/history/pending gate, 두 독립 branch와 held 검증, 공통 own 시간 구간/root-inclusive margin·사전 효과 cut, no-information/root-dominating/inconclusive 기준을 동결한다. unsafe·infeasible·censored를 구분하며 한쪽 실패를 성공의 필요조건으로 사후 추가하지 않는다. 실제 비교 전 worst-case worlds/ticks/queries/native/reset 상한을 합산하고, 이 문서는 어떤 후속 실행도 자동 승인하지 않는다.
