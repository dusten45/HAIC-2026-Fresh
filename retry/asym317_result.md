317 — 현재 296 기반 matched PPO pilot 완료, champion 개선 없음

**B와 C는 각각 5/6 완주로 cached 296의 6/6보다 적었다.** 두 arm 모두 N2의 완주를 잃었다. C는 B와 같은 완주 집합에서 평균 **+124ms** 느려, 이번 고정 pilot에서 asymmetric critic의 정책 개선을 지지하지 않았다. 296을 유지하고 승격·중간 선택·추가 학습·자동 확대를 하지 않는다. 316의 C−A 불확실성과 완주 episode 예측 악화는 그대로 보존한다.

시작 전에 기존 317 등록·프로세스·결과가 없음을 확인했다. 승인된 추가 연구량 **20,189**를 v323 원장에 반영해 연구 잔액 22,384·B1,350,189로 만들었고, 예비 84,000은 보존했다. 이 확장은 이번 학습16,384+평가cap6,000 pilot에만 적용했다.

두 arm의 base는 정확한 현재296 ZIP이다. Actor는 legal28→hidden32→3, mean residual0에서 시작한다. 학습 중에는 공통 Gaussian noise를 사용하며 residual bounds(.015,.03,.02), likelihood·reward·GAE λ.95·Adam·LR·minibatch·epoch·KL stop·executed-action memory를 같게 했다. 현재296의 저장 TRAIN legal feature로 만든 공통 정규화를 고정했다. 316 ridge 계수·기존 PPO checkpoint·teacher label은 가져오지 않았다.

Critic은 두 arm 모두31입력→hidden32→1이다. B의 추가3개 입력은0, C는 현재 **pre-action progress·damage·elapsed/160**이다. 추가 입력 weight를0으로 초기화하고 모든 초기 actor/critic tensor를 같게 했다. 네트워크는S를 예측하고 `V=S_hat−offset`으로 변환하며, critic target도 GAE의 remaining target에 **동일한 현재 offset을 더해** S 단위로 학습한다. 다음 상태 bootstrap 역시 해당 다음 상태의 offset을 빼며 terminal은V0, collection cut은 실제 다음 상태에서 bootstrap한다. Actor 입력·export에 privileged 상태를 넣지 않았다.

캐시에서 zero mean actor가296 행동·features·memory와 정확히 같은12개 입력을 확인했다. 실제 첫 1,024개 rollout의 X·latent·old mean/logp·reward·value·next value·offset·S value·done/cut·base/실행 행동이 두 arm에서 정확히 일치했다. 이 게이트를 통과하기 전에는 첫 update로 진행하지 않았다. 이후 궤적은 각자의 학습 결과에 따라 달라질 수 있으며 강제로 맞추지 않았다.

이번 live reset에서는 실제 progress를 관측할 수 있다. Critic과 offset에는 그 값을 쓰되, 기존 reward의 초기 `previous_progress=0` 회계는 변경하지 않았다. 따라서 관측된 terminal reward suffix에 현재 offset을 더한S는 첫 행에서만 **final score+알려진 reset progress**, 나머지 행에서는final score가 된다. 이 알려진 첫 행 차이를 임의로 제거하거나 reset state를0으로 가정하지 않았다. 두 arm에 같은 회계를 적용하고 모든 실제 terminal episode에서 이 관계를 검증했다. 종료 정보·미래 관측·episode 길이·road/policyID는 critic 입력이 아니다.

두 arm은 각각 **8,192 action·8 update·256 optimizer step**을 완료했다. 학습 관측 terminal은 B28개(완주22/DNF6), C27개(완주24/DNF3), collection cut은각 8개이며 기술 중단0이다. 이 수집 집계는 서로 달라진 on-policy 궤적의 결과로, 독립적인 최종 정책 성능 비교를 대신하지 않는다.

저장 journal의 이전 POST-step 행으로 전체 **16,384개 pre-state**를 독립 재구성했다. Legal28 actor 입력과31 critic 입력을 분리하고, pre offset·다음 offset·S/V·terminal/cut bootstrap을 확인했다. GAE delta 두 표현의 최대 차이는 **2.22e−16**이었다. 최종 B의 추가 critic weight norm은0, C는0.719593이었다. 이는 C의 입력이 실제 학습에 사용됐다는 증거이며 좋은 정책의 증명은 아니다.

최종 checkpoint8만 actor-only Numpy runtime으로 export했다. Arm별12개 캐시 입력에서 Torch/Numpy 행동·features·실행 memory가 정확히 일치했다. Export의 actor 첫 층은32×28이며 critic·progress·damage·offset·checkpoint는 없다. 원래 296 root는 runtime base로 바이트 그대로 보존했고 원래 nonroot member도 모두 동일하다. 원시 모델·ZIP·buffer는 비공개로 유지했다.

결과 전에 고정한 기준은 **완주 수 우선, 동률이면 공통 완주 평균 시간의 엄격한 개선**이다. 최소 개선폭·개별 완주 손실 veto·damage veto는 없다. 기존 여섯 TRAIN을각 arm 한 번씩 고정 AB/BA 순서로 평가했고, baseline은 정확한296 캐시를 재사용했다.

| 기존 TRAIN | cached296 | B offset-only | C asymmetric |
|---|---:|---:|---:|
| O0 | 24.32초 | 24.20초 | 24.36초 |
| N0 | 24.04초 | 24.36초 | 24.14초 |
| O2 | 22.36초 | 21.48초 | 22.62초 |
| N1 | 17.86초 | 17.74초 | 17.98초 |
| N2 | 29.00초 | off_track,166action | off_track,166action |
| N3 | 19.72초 | 19.68초 | 18.98초 |

B/C는 모두 5/6 완주, C−B 공통5개 평균차이는 **+124ms**로 C가 느렸다. Baseline 296과 비교하면 둘 다 추가0·손실1이다. 공통5개에서 B는−168ms, C는−44ms지만 조건부 시간 개선은 완주 손실을 뒤집지 않는다. N2 damage는B0.2·C0.6이며 독립 진단으로 남긴다. 실제 평가 DNF 2·기술 오류 0·검열 0·미관측 0으로, 12개 공식 끝점을 모두 관측했다. C가 B보다 좋더라도296보다 나쁘면 champion 개선이 아니라는 기준을 그대로 적용했다.

실측 비용은 **19,415/22,384 native = 학습16,384 + 평가3,031**이다. Raw step77,585틱·reset4,233틱, 학습 병렬 elapsed715.361초(**11.92분**)·평가248.637초다. 병렬 두 arm의 wall을 합산해 elapsed로 쓰지 않았다. Training CPU1,076.962초·evaluation CPU205.018초·actor CPU281.660초를 기록했다. Source forecast/model physics·유료 추가 자원0이며 지정 cloud만 사용했다. 준비·캐시 qualification·audit·게시 시간은 위 native 실행 시간 합계에 포함하지 않았다.

V324 원장에 실제 비용을 반영해 **누적 1,263,220 + 연구 잔여 2,969 + 예비 84,000 = B1,350,189**이다. Reserve 사용 0이며 허가 한도에 닿지 않았다. 모든 학습·평가 actor를 회수했다. 296·240 rollback·main 기준·Participants·backup·개인 원문 및315/316의 기존 결과를 보존한다. DEV/HOLDOUT/SEALED·중간 checkpoint 성능 선택·hyperparameter 탐색·승격·자동 확대는 없다.

이번 결과는 같은 여섯 알려진 TRAIN·한 noise/shuffle seed·8 update의 matched pilot이다. 수렴 증명이나 asymmetric critic 방법군 전체의 불가능성으로 확대하지 않는다. 316의 평균 예측 정보가 이 설정의 실제 actor 개선으로 이어지지 않았다는 증거로 보존하며, 추가 예산·학습·모델 선택을 자동 시작하지 않는다.

[동일 초기화·비용 charge](asym317_model.py) · [훈련·S/V 회계](asym317_train.py) · [독립 경계 검증](asym317_verify.py) · [최종 실행·집계](asym317_stage.py) · [결과·비용](asym317_result.json)
