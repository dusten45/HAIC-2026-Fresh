# 276 — 65,536 유효 action 공동 PPO의 최종 평가

**최종 checkpoint64는 미채택한다.** TRAIN4/6 완주로240의6/6보다 완주 수가 줄었고, 새 DEV screen은 양쪽2/2 완주·평균−0.03초였다. 전체 후보6/8 대2408/8이며 N0·N2는 실제 crash다. 평가 오류·검열·미실행은0이다. 중간 checkpoint 선택이나 평가 후 recipe 변경 없이240을 유지한다.

| 구분·도로 |240 |최종64 |paired 차이 |damage:240→후보 |
|---|---:|---:|---:|---:|
|TRAIN O0 |23.66초 |24.50초 |+0.84초 |0→0.2 |
|TRAIN O2 |20.98초 |20.70초 |−0.28초 |0.2→0 |
|TRAIN N0 |23.62초 |crash78 |— |0.2→1.0 |
|TRAIN N1 |17.08초 |18.12초 |+1.04초 |0→0.8 |
|TRAIN N2 |21.56초 |crash222 |— |0→1.0 |
|TRAIN N3 |18.76초 |18.66초 |−0.10초 |0.2→0 |
|fresh DEV S276-0 |23.60초 |23.64초 |+0.04초 |0.4→0.2 |
|fresh DEV S276-1 |17.60초 |17.50초 |−0.10초 |0→0 |

공통 완주4TRAIN 쌍 평균은 **+0.375초**, fresh2쌍은−0.030초, 전체 공통6쌍은+0.240초다. 두 실패는 paired 시간에서 제외했으며 전체8개 후보 평균 완주 시간은 정의하지 않는다. TRAIN 결과는 학습 도로의 regression이고 일반화 확증이 아니다. 새screen2개도 작은 DEV 표본이지 HOLDOUT/SEALED가 아니다. Damage는 진단이며 학습 reward나 별도 채택 gate에 넣지 않았다.

## 실제 학습과 일치성

275 checkpoint2의 actor/critic·Adam state·noise/shuffle RNG·road cursor9를 정확히 이어갔다. 여섯 TRAIN을round-robin으로 사용해 **추가63,488 유효 action·62update**, 기존2,048개와 합쳐 **65,536개·64update**를 완료했다. N2도49episode·9,396개 유효 sample이 정상 포함됐다. Parameter별 optimizer step은64→2,048로 이어졌고, actor와critic 모두 실제 gradient·update가 존재했다.

275의28-input(16pixel features+최근3개 실행 action/mask)·32tanh hidden·3-output actor,32hidden critic, float64·CPU1thread를 유지했다. GaussianSTD0.2, residual steer/gas/brake0.015/0.03/0.02, rollout1,024·4epoch·minibatch128·LR3e−4·PPOclip0.1·KL0.01·gradient norm0.5·gamma1·GAEλ0.95도 바꾸지 않았다. Reward는 공식 complete`2−T/160`, actualDNF`p−1`에 합산된다. Policy/critic 입력에는 GT pose/velocity·progress/time/damage·roadID가 없다.

추가 수집293episode는 **167완주·64실제 DNF·62rollout cut**이었다. Cut은 critic bootstrap과 GAE trace reset, 실제 종료는bootstrap0으로 처리했다. 기술 중단·sample 손실·물리 재주행은0이다. 모든62update가32개 minibatch step을 수행했고 KL epoch중단은 없었다. 최종 full-batch KL 범위는0.00086–0.00430으로 finite였다. 이 학습 주행에는 noise가 있으므로 최종 deterministic 정책의 성능으로 대신하지 않는다.

Action commit·자기 이력·다음 feature7·latent3D logprob는 학습 코드에서 확인했다. Zero residual 재현은275 검증을 재사용했고 새 일반 검증을 반복하지 않았다. 마지막64만 NumPy pixel-only ZIP으로 동결해 Torch mean actor와16쌍의 action/steering/tracker state 일치를 확인했다. Runtime은pixels와자기 반환 action 이력만 쓰며 critic·simulator/GT는 포함하지 않는다. ZIP/checkpoints는 비공개로 보존했고 공식 별도 자격 확인을 마친 제출물은 아니다.

## Screen과 평가 고정

학습 전에 source-only identity 등록으로 새 DEV2개를 고정했다. 기존 identity exclusion을 적용했으며 source coordinate3회·world/physics/renderer/policy0회, 성능·난이도 filtering0회였다. Screen은 학습/선택에 쓰지 않고 **checkpoint64 완료·동결 후** 처음 policy 평가했다. S276-0은240→candidate, S276-1은candidate→240 순서이며 reset pixel stack과 road geometry가 일치했다.

여섯 TRAIN의240 정확한 기록은 재사용했다. 최종 candidate8회와새screen baseline2회, 총10주행을 각각 한 번 실행했다. 첫 실패 뒤에도 나머지 평가를 모두 수행했다. 평가cap6,500·전체새nativecap69,988에 닿지 않았다. 이전/중간 모델을 고르거나 추가학습·gain 조정·재평가하지 않았다.

## 비용과 다음 판단

새 **65,846 native = 학습63,488 + 평가2,358**이며 fresh baseline516회가 평가에 포함된다. 학습3338.52초(**55.64분**,19.02native/초), 평가113.90초, 초기화2.48초다. 수집3321.61초·optimizer4.21초로 비용 대부분은 실제 수집이다. Evaluator CPU2847.19초·actor CPU610.14초다. Raw step은학습253,707틱·평가9,423틱, reset은14,943/510틱이다.

최종 candidate8개 주행의 실제 Agent inference 중앙값/p95/최대는 **5.82/12.61/35.47ms**, IPC 포함8.47/15.75/37.57ms다. Model-physics·GTteacher labels·외부 유료 자원은0이다.

승인된 연구+70,000만 반영했다. **B994000 = 누적904931 + 연구5069 + 최종예비84000(사용0)**. 지정 클라우드·main dfb7a2de·Participants·백업·사용자 변경·240 챔피언·HOLDOUT·SEALED를 보존했다. Raw trace·private checkpoints/arrays·원문·개인 회고는 공개 저장소에 올리지 않았다.

요청한 실제 학습량을 마쳤지만 **이 고정 recipe의 마지막 정책은 완주를 유지하지 못했다**. 이를 공동 PPO 방법군 전체의 불가능성이나 수렴 증명으로 확대하지 않는다. 128k로 자동 연장하거나 더 이른 checkpoint를 고를 근거도 없다. 다음 연구를 한다면 저장된 **TRAIN-only buffer의 credit assignment/critic state 근거**를 먼저 확인하는 편이 낫다. 현재 실패의 단일 원인은 분리되지 않았으며 이번에는 새 실험을 실행하지 않았다.

[집계](ppo276_result.json) · [등록·고정](ppo276_prepare.py) · [연속 학습기](ppo276_train.py) · [최종 export·일치검사](ppo276_finalize.py) · [최종 평가기](ppo276_eval.py)
