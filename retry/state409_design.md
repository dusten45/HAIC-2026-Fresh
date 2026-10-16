# 409 — 행동번호 대신 현재 상태의 위험·진행 예측을 쓰는 개입 설계

**설계만 작성했다. 새로운 rollout·source 적분·최적화·주행은0이다.** [기계 판독 설계·비용 산식](state409_design.json) · [종료 계측 교정](terminal409_result.md)

407/408의91번째 pulse는 실패 위치를 알고 고른 사후 GT 개입이다. 이를 일반화하려면 '91번에 제동'을 '현재 상태에서 원래 nominal이13행동 안에 안전·진행 조건을 위반하고, 같은 상태의 고정 pulse 대안은 조건을 만족할 때만 개입'으로 바꿔야 한다. 이 새 feedback 정책의 성능은 고정 pulse의15.08초로 대신 검증할 수 없다.

## 관측과 모델의 선행 조건

| 층 | 필요한 현재 정보와 자격 | 현재 남은 제한 |
|---|---|---|
|GT 진단 상태 |hull pose/velocity/yaw, 바퀴 joint/omega/gas/brake/steer·접촉·마찰·손상, 현재 도로/장애물 geometry, 현재 nominal/controller memory, phase/finish 상태 |source 복원은 solver warm-start·broadphase/island history를 보존하지 않는다.391의 위치0.1m·속도0.5m/s·yaw0.05rad/s·이산 상태 자격을 적용한 것은 일부 상태뿐이다. |
|픽셀 관측 |허용된 영상·과거 영상/자기 행동만으로 ego pose/속도/yaw·도로/장애물/진행·actuator memory 및 불확실성을 추정 |GT full snapshot·seed/track ID·공식 미래 상태를 actor에 넘길 수 없다. wheel slip/접촉/마찰의 식별 가능성과 오차 경계가 검증되지 않았다. 현재 구현된 pixel 대체물이 아니다. |
|예측 |현재 상태와 기억의 독립 복사에서 원래 nominal을 자기 예측 상태로13행동 계산; 접촉·손상·도로·후진·domain과 진행을 함께 평가 |몸체 동역학만 맞거나 yaw만 맞는 것으로 후보 효과·제어 성능 자격을 대신하지 않는다. 불확실성이 안전 여유보다 크면 '위험'이 아니라 모델 미자격으로 분리한다. |
|공식 종료 |현재 finish tracker/phase를 복제해 예측 raw tick마다 같은 인과 규칙으로 갱신하고, 정상 terminal에서는1–4 tick과 최대13행동을 정확히 처리 |현재 `SourceVehicleTransition`은 finish tracker를 제외하고 항상4 tick을 적분하며406 Controller는 finish 정보를 빈 dict로 넣는다. 종료 근처의 domain 이탈을 위험으로 오인할 수 있다. 이번 계측 교정이 이 모델 한계까지 고친 것은 아니다. |

픽셀 추정 오차는391의 GT 모델 오차와 별개다. 두 오차를 합친 상태/접촉 불확실성 아래에서 안전 조건이 유지되는지 별도 자격이 필요하다. 현재 수치로 추정 신뢰도나 안전 margin을 임의로 정하거나 이번 실패에 맞춰 slip/yaw 문턱을 학습하지 않는다. source 불확실성·복원 실패·지원하지 않는 종료 phase를 단순 위험 판정으로 바꿔 제동하지 않는다.

## 최소 두 recipe의 조건부 규칙

고정 horizon은13행동, full action당4 raw tick·0.08초이며 정상 terminal이면 더 짧게 끝날 수 있다. 대안은 기존 것 둘뿐이다: 원래 nominal feedback, 또는 **현재 첫 행동만 `[0,0,float32(0.3)]` 후 같은 nominal feedback**. 제동·조향 분해 실험이나 새로운 gain/pedal/steering 후보 탐색은 없다.

1. 현재 nominal을 실제 controller에서 한 번 계산하고 계산 전/후 memory를 보존한다. 예측 branch는 그 계산 전 memory의 복사에서 한 번 계산한다. 실제 적용 후에는 실제 nominal memory만 commit하고 예측 memory나 override 조향을 실제 memory로 복사하지 않는다.
2. 현재 위치에서 상대 진행 목표3.24m·13행동 deadline을 둔다. 현재 목표를 실제로 달성할 때만 목표/deadline을 갱신한다. 매 tick 새13행동을 부여해 정지/후퇴를 무한 허용하지 않는다. 절대 행동번호·절대 시간·실패 arc/구간·track/seed를 발동 조건으로 쓰지 않는다. projection은 현재 geometry의 진행 계산에만 쓰며 기억한 위험 위치와 비교하지 않는다.
3. nominal을 최대13행동 예측한다. 기존3m·충돌/손상·접촉/grass·후진 조건과 현재 정책의 선언된 domain, 남은 deadline 내 목표 달성을 따로 판정한다. 공식적으로 유효한 예측 finish는 terminal 성공 조건으로 다루어 결승선 이후 가상의 목표를 요구하지 않아야 한다. 이를 위해 먼저 finish-aware 모델 자격이 필요하다.
4. **nominal이 안전하고 진행도 적격이면 항상 그대로 통과**시킨다. 다른 후보의 미세 진행 점수가 좋다는 이유로 성공 nominal을 바꾸지 않는다. nominal이 선언된 안전/진행/domain에서 불적격일 때만 같은 현재 상태의 pulse recipe를 예측하고, 그 recipe가 모든 조건을 만족할 때 첫 pulse만 적용한다. 그 뒤 다음 현재 상태에서 같은 규칙을 다시 평가한다.
5. source/관측/지원 phase 미자격은 판단 불가로, 잘 정의된 rollout의 정책 domain 이탈은 recipe 불가로 구분한다. 둘 다 불가이거나 계산 상한을 넘으면 연구 실행을 검열 중단한다. 알려진 불안전 nominal로 자동 복귀하지 않는다. 실제 배포에는 별도로 검증된 action-safe fallback이 필요하며, 현재 설계의 연구 중단을 운전 안전 보장으로 부르지 않는다.

재발동은 현재 상태에만 의존한다. 따라서 새 정책은 여러 번 pulse를 낼 수 있으며 이는407/408의 '한 번만' 실험과 다르다. 진행 deadline만으로 recursive feasibility·반복 제동 방지·성공한 이전 계획의 보존이 증명되지는 않는다. retained suffix의 안전 fallback을 쓰려면406의 재검증 원칙에 따른 별도 자격과 비용 계약이 필요하다. 이번에는 이를 추가 후보로 실행하거나 성능을 주장하지 않았다.

기존406 결과를 **새 예측 없이** 이 논리의 예로 대입하면 reset/O pre92는 nominal 통과, C pre91은 pulse 개입이 된다. 세 상태는 이미 선택된 알려진 benchmark이므로 오탐률·일반화 검증이 아니다. force/limit 포화는 성공 O에도 있었으므로 그 값만으로 트리거를 만들지 않는다. q/slip은 진단 지표로만 남긴다.

## 계산 비용과 실행 가능성

406의 전체4024 tick·66 world 비용6.216 CPU초를 단순 환산한 값이다. prefix·복원·후보·journal이 섞인 집계 비율이므로 단일 query 지연 측정이나 상한은 아니다. 새 관측기·snapshot·terminal observer·independence 검사 구성에 따라 비용이 바뀐다.

| 작업 | 최대 모델 tick | 집계 비율 환산 CPU |
|---|---:|---:|
|nominal13 한 번 |52 |약80ms |
|nominal + pulse13 |104 |약161ms |
|둘 다 독립 반복해 자격 대조 |208 |약321ms |
|189개 boundary에서 nominal만 |9,828 |약15.18초 |
|189개 boundary에서 항상 둘 다 |19,656 |약30.37초 |

0.08초는 simulated control period다. 이를 contest의 실제 CPU 허용 시간과 동일하다고 가정하지 않으며, 반대로 이 표로 실시간 가능하다고도 주장하지 않는다. 앞으로 재구성·관측·rollout·현재 제어·journal의 CPU/wall을 분리해 max/p95와 전체 랩 비용을 측정해야 한다. 지연을 줄이려고 horizon·gain·판정 주기를 사후 변경하지 않는다. 현재 대안은 model query 수·미자격률·반복 개입 수에 따른 비용을 그대로 기록하는 것이다.

## 오탐과 기존 성공 O+268 영향 검증 계획 — 미실행

검증 대상 nominal은 원래 실행기의 법칙을 유지한다. **O 기록에서는 O의 nominal/memory**, C 기록에서는 C의 nominal/memory로 예측한다. 성공 O 상태에 C 실행기를 넣은 결과를 O 보존 검증이라고 부르지 않는다. stored 미래는 evaluator만 읽으며 trigger/controller에는 전달하지 않는다.

- **먼저 source/종료/분기 자격:** snapshot·memory·RNG/부모 불변성, 두 독립 참조 및 candidate 반복, actual nominal13의391 기준, 정상 terminal partial tick을 통과해야 한다. 종료-aware 모델을 만들었다는 이유만으로 자격을 가정하지 않는다. 첫 source/동역학/독립성 실패는 이후 검증도 중단한다.
- **정해진 모든 기존 창:** O185행동의 완전13행동 창173개와 terminal을 포함한 마지막12개, C103행동의 완전 창91개를 시간순으로 검사하는 설계다. 실패를 잘 맞춘 창만 고르지 않는다. C의 마지막12개는 실제 실패 이후의 미래가 없어 별도 검열 항목이며 안전 음성으로 세지 않는다. 관측된 실패가 이미 창 안에 있으면 위험 양성이라는 사실만 기록할 수 있다. 창들은 겹치므로276개의 독립 episode로 세지 않는다.
- **지표를 분리:** 저장 실제 nominal 창이 안전·진행 적격인데 위험/진행 실패를 예측하면 오탐, 실제 알려진 위반을 안전하다고 예측하면 미탐으로 집계한다. source 미자격은 오탐/정답에 섞지 않고 availability와 원인으로 보고한다. 최종 pulse의 모델상 안전은 실제 pulse 효과의 정답이 아니다. 기존407의 한 반사실 실제 대조만 별도 근거로 남긴다.
- **O 영향 선행 게이트:** 자격을 통과한 O 창에서 nominal이 실제로 안전·진행 적격이면 개입0을 요구한다. 오탐·불필요한 pulse가 하나라도 나오면 이후 실제 비교로 승격하지 않고, 이번 데이터로 threshold를 고쳐 계속하지 않는다. 양쪽 모두 유효할 때 무조건 nominal을 택하는 규칙으로 작은 score 차이의 불필요한 개입을 피한다. source 계산이 O의 memory/RNG를 건드리지 않는지도 확인해야 한다.
- **알려진 양성/진행 게이트:** 현재 상태만으로 C pre91의 위험과 pulse 적격을 재현해야 하고 reset에서는 nominal 전진·deadline 유지가 확인돼야 한다. 이는 개발 sanity check이며 새 독립 성공으로 세지 않는다. 미탐·모두 불가·반복 제동·과도한 계산 비용은 중단 사유다.
- **그 다음 실제 영향은 별도 승인 범위:** 향후 source 게이트 후에만 실제 C wrapper의 폐루프 개입 횟수/위치·첫 새 실패·공통 arc·공식 시간·손상을 평가하고, O+268도 기존 O를 유지한 제어에서14.78초·손상0·명령/기억 보존 및 추가 계산비용을 비교해야 한다. 알려진 N1의 성공으로 일반화를 주장하지 않는다. 독립 DEV의 사전 고정·분리 검증이 추가로 필요하며, 이번에 새 DEV/HOLDOUT/SEALED를 조회하지 않았다. 기존 HOLDOUT 노출 이력을 지워 깨끗한 검증으로 부르지 않는다.

미래 stored-source 검증의 비용 예시는276 query×최대4 branch×52 tick + 보수적 prefix1152 = **58,560 tick**이다. nominal/pulse 각각 독립 반복하는 최악 예산이며 branch 초기화는최대1106회다. 제안 상한60,000 tick·1200 world·CPU180초·wall300초·동시1·native/actor/학습/SEALED/예비0은 **실행되지 않은 설계**다. 실제 측정이 아니고 이번 자원을 예약·등록한 것도 아니다. terminal 자격 또는 앞 게이트가 실패하면 뒤 창을 진행하지 않도록 설계한다. 새로운 목적 최적화·gain sweep은 포함하지 않는다.

## 이번 작업의 경계

원래408 결과/코드/계획/분석/비용은 바꾸지 않았다.15.08초 공식 관측과 원래 기술 자격 실패를 동시에 유지한다. 새 시뮬레이션·actor·학습·SEALED는0이고 연구30,892·최종 예비84,000·사용0을 유지한다. 이 문서는 현재 상태 기반 개입이 아직 갖추지 못한 관측·source 종료·비용·오탐·배포 fallback 조건을 명시한 설계이며, 새 정책의 성능 결과가 아니다.
