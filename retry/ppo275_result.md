# 275 — 공동 PPO의 실제 rollout/update 비용·안정성 파일럿

**실제 on-policy PPO 두 update를 완료했다.** 유효2,048 training actions에서 actor/critic 각각64개 minibatch optimizer step과 nonzero gradient·정책 평균 변화를 확인했다. 첫 수집 중 worker의 float32 경계 검사 오류로216회를 잃었으나 수정 후 재발·NaN·state/action 불일치는 없었다. 최종 정책의 DEV 성능 평가는 하지 않았고240 챔피언을 유지한다. 274의 고정 − 후보는 미채택이며 그 계수를 재사용하거나 조정하지 않았다.

## 고정 recipe와 실제 변화

현재240은 actor deterministic residual0에서 정확한 출발점이다. 입력은 기존16개 pixel-derived feature를 TRAIN231 mean/std로 정규화한 값과 최근 **자기가 실행한3개 action**·유효성 mask12개, 총28차원이다. Actor28→32tanh→3(1,027params), critic28→32tanh→1(961params), float64·CPU1thread이며 output layer를0으로 초기화했다. 입력에 GT pose/velocity·progress·시간·damage·roadID는 없다.

Gaussian latent STD0.2, tanh residual 범위 steer/gas/brake0.015/0.03/0.02, 최종 steering±0.4·pedals0..1이다. Lookahead/path/head/scales는240 그대로다. 반환 조향이 baseline과 같으면 원래float64 nominal memory를 보존해 **zero residual action과state를 정확히 재현**한다. 다른 조향이면 반환 float32명령을 memory로 저장한다. 항상float32(memory)=실제 steering이고, action history는 commit한 실행 명령만 담는다.

Rollout1,024·4epoch·minibatch128·actor/critic Adam LR3e−4·PPOclip0.1·KL중단0.01·gradient norm0.5·gamma1·GAEλ0.95를 한 번 정했다. Raw latent3D Gaussian likelihood를 tanh/action clip 전에 저장한다. 244 보상을 재사용해 공식 완주 return`2−T/160`, 실제 DNF`p−1`에 정확히 합산되는 것을 검사했다. Damage는 reward가 아니다.

완주/실제 DNF bootstrap0, rollout cut은 적법 다음 입력의 critic value로 bootstrap하고 GAE trace를 끊는다. 다음 episode는 history를 reset한다. Worker의 **act→commit**으로 실제 action/memory를 연결하고, cut peek는 복사된 controller만 계산해 소유 state·history를 바꾸지 않는다. Critic 입력도 actor와 같은 적법28차원이다. 학습 중 source 접근은 환경 실행·reward에만 사용한다.

| Update |실제 minibatch steps(각net) |actor gradient 최대(clip전) |mean 변화RMS |최종 KL |value MSE 전→후 |
|---|---:|---:|---:|---:|---:|
|1,1,024actions |32 |2.030 |0.00726 |0.00198 |0.03686→0.02571 |
|2,2,048actions |32 |2.271 |0.00950 |0.00338 |0.03353→0.02190 |

두 update 모두4epoch를 완료했고 KL중단은 없었다. Critic gradient 최대0.189/0.199, 모델·ratio는 finite다. 이는 무작위 ± 후보를 학습으로 부른 결과가 아니라 실제 Adam update다. 단, value fit·작은 mean 변화가 episode 성능 향상을 증명하지 않는다.

## Episode와 기술 복구

| 수집 batch |TRAIN road |공식/수집 결과 |native |
|---|---|---:|---:|
|1 |O0 |완주23.98초 |300 |
|1 |N0 |완주26.08초 |327 |
|1 |O2 |완주21.20초 |266 |
|1 |N1 |rollout cut·bootstrap |131 |
|중단 |N2 |기술 중단·공식 종료 미확인 |216 |
|2 |N3 |완주18.66초 |234 |
|2 |O0 |완주25.22초 |316 |
|2 |N0 |완주24.76초 |310 |
|2 |O2 |rollout cut·bootstrap |164 |

성공 수집8episode는6완주·실제 DNF0·collection cut2다. 별도 N2기술 중단1개를 DNF나 정상 bootstrap cut으로 바꾸지 않는다. 유효 optimizer 데이터는5/6 TRAIN road에 걸치며 N2의216개 미완료 buffer는 optimizer에 들어가지 않았다. 마지막 DEV screen은 학습·선택·평가에 사용하지 않았다. 위 시간은 Gaussian noise가 들어간 **training trajectory**로, deterministic final actor의 성능 대조가 아니다. O0/N0 변화도 방향이 엇갈려 초기 학습 성능 개선을 주장하지 않는다.

오류는 float32의0.4≈0.40000000596를 float64 상수0.4와 비교해 유효 commit을 거부한 구현 문제였다. Native0인 작은 재현에서 같은 assert를 확인했고 bounds를float32로 맞춰±0.4 검사를 통과했다. Action law·hyperparameters는 바꾸지 않았다.

중단된 N2는 재주행하지 않았다. 첫 checkpoint의 actor/critic·optimizers를 복구하고 이미 사용한noise draws를 건너뛴 뒤 다음 road N3에서 이어갔다. 당초3×1,024개 유효 samples에 손실216회를 더하면3,288회로 가용3,179회를 넘으므로, rollout 길이나epoch를 임의로 줄이지 않고 같은recipe의 두 update로 마감했다. 원래 source·실패 기록·복구 plan/hash·checkpoint를 비공개로 보존했다.

Zero residual16쌍의240 action/조향/tracker state 재현, commit/history/reset·pure peek, Torch와3D logprob 일치를 사전 확인했다. 실제2,048개 samples의 likelihood·실행 action·terminal bootstrap을 재구성했다. 학습된 mean actor를 **pixels와 own history만 쓰는 NumPy ZIP**으로 묶고 Torch 실행과16쌍의 action/state 일치를 확인했다. ZIP은 비공개이며 성능·공식 자격 확인을 마친 후보가 아니다.

## 처리량·후속 배정 추천

수정 후1,024회 수집/update는59.02초, **17.35 native/초**였다. 두 실행 phase 전체는128.33초·2,264 native, optimizer 계산은합계0.38초로 현재 비용 대부분이 환경/관측/IPC 수집이다. Base IPC+actor/value+commit latency 중앙값10.53ms·p9519.53ms·최대165.02ms이며 이는 학습 pipeline 측정치이지 공식 ZIP inference benchmark가 아니다.

추천은128k가 아닌 **총65,536 유효 training actions,64개 동일1,024-rollout update**다. 두 update의 기술 안정성은 확인했으나 성능 향상 증거가 없어 먼저 낮은64k 규모로 실제 episode 학습을 평가하는 설계다. 현재checkpoint2의2,048개를 포함하면 추가 training **63,488회**, 동일 recipe로62update가 남는다. 모든6TRAIN을round-robin으로 계속 사용한다.

후속 training 전에 새 DEV screen2개를 등록·고정하고 학습/모델 선택에는 쓰지 않는다. **최종 checkpoint 하나만**6TRAIN regression과 새screen2개의240 paired 비교로 평가한다. Training6회+fresh screen baseline/candidate4회, 각650 상한으로 평가 cap **6,500 native**다. Collection cuts·actual DNF·예산 censor는 계속 구분한다. Nonfinite·history/action/logprob 오류·승인/예산 한도는 중단 조건이며, 단순 초반 DNF로 방법군을 종료하거나 중간 screen으로 모델을 고르지 않는다.

추가 training/evaluation cap은 **69,988회**, 현재 연구915회 외에 최소 **69,073회**가 필요하다. 실무 배정 추천은 **연구+70,000 native**, 수정 후 처리량을 보수적으로 적용하면 약**67분**이다. 이는 고정 실험 규모/비용안이지 수렴 보장이나 실행 승인이 아니다. 더 긴 학습·예산 증액·자동 연장·예비 사용은 이번에 실행하지 않았다.

## 비용과 보존

이번 비용 **2,264 native = 유효2,048 + 기술 손실216**이다. 성공 수집의 raw step8,181틱·reset408틱은 기록돼 있다. 중단 episode의 raw tick/actor CPU 세부는 durable trace에 남지 않아 전체 측정치로 꾸미지 않았으며 native ledger216회는 보존했다. 등록된 episode actor CPU는20.56초 lower bound, evaluator CPU합계105.85초·초기화6.30초다. 별도 offline 검사·ZIP 확인은 native0이다.

**B924000 = 누적839085 + 연구915 + 예비84000(사용0)**. 새 baseline 주행·DEVscreen·GTteacher/모델물리·유료 자원은0이다. main·Participants·백업·사용자 변경·챔피언240·HOLDOUT·SEALED를 유지했다. Checkpoints·arrays·ZIP·raw자료·receipt는 비공개로 보존했다.

[집계·후속recipe](ppo275_result.json) · [학습기](ppo275_train.py) · [모델·목적함수](ppo275_model.py) · [act/commit/peek worker](ppo275_worker.py) · [고정·사전검사](ppo275_prepare.py) · [pixel-only ZIP builder](ppo275_build.py)
