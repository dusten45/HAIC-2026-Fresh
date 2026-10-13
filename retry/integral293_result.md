# 293 — 속도 오차를 기억하는 고정 가속 페달 적분 제어

**두 TRAIN 도로 모두 완주했지만 평균 4.02초 느려져 후보를 중단했다.** 나머지 네 도로는 게이트 탈락으로 실행하지 않았으며 계수 sweep·정책 학습·픽셀 predictor 재튜닝은 없다.

240의 고정 head는 현재 특징에서 페달을 계산한다. 이번에는 nominal 목표(feature6)와 HUD feedback 속도(feature4)의 지속 오차를 하나의 적분 상태로 기억해 final gas에만 더했다. 기존 nominal/head/global scale과 조향·brake·경로는 유지한다. 최근 PPO량/λ/범위 변경, 작은 counterfactual selector, yaw/traction/preview 목적 변경과 다른 longitudinal memory 개입이다.

`I += 0.08 × 0.08 × (target − feedback)`; gas는 `clip(basegas + I, 0, 1)`이다. 첫 0.08은 원래 nominal gas P slope, 둘째는 native 간격 0.08초이며 integration time은 사전 고정한 1초다. I는 [−1,1]에 제한하고 실행 gas 포화 바깥으로 오차가 더 밀면 적분을 보류한다. target이 없으면 I를 0으로 초기화한다. 첫 호출부터 같은 규칙을 적용했다. GT·미래 관측·도로 ID·보상은 제어에 쓰지 않았다.

사전 게이트: O0/N0 둘 다 완주하고 각자 cached240보다 엄격하게 빨라야 같은 설정으로 나머지 네 TRAIN을 실행한다. pilot 각 1,000, extension 각 917로 전체 상한 5,668을 고정했다. 기준선은 기존 정확한 기록을 재사용했고 재실행하지 않았다.

| 도로 | cached240 | 적분 gas 후보 | 시간 변화 | native |
|---|---:|---:|---:|---:|
| O0 | 23.66초 | 28.10초 | +4.44초 | 352 |
| N0 | 23.62초 | 27.22초 | +3.60초 | 341 |

완주 2/2, 실제 DNF 0, 검열 0, 실행 기술 오류 0. 후보 damage는 두 도로 모두 0.6이다. 첫 pre-action의 16개 특징은 기존291 baseline240 저장값과 float32 정밀도에서 일치했다. 모든 693개 journal 행동에서 고정 보정식·조향/brake 동일성·실제 조향 메모리를 재계산 확인했고 두 actor를 회수했다. 검증 코드의 16/28 feature shape 오류는 첫16개 비교로 수정했으며 추가 native 없이 통과했다.

적분 제어로 미래 관측도 바뀌므로 결과를 동일 궤적 위의 순수 head bias 측정으로 해석하지 않는다. 이 고정 적분 가속 후보는 공식 시간을 개선한다는 근거를 보이지 않았다. 적분 제어 방법군이나 전체 목표의 불가능성을 주장하지 않는다. 새 후보나 계수 변경을 자동으로 이어가지 않는다.

실제 비용 **693 native**, raw physics 2,767 tick/reset 102 tick, source model physics 0. runner wall 37.286초, CPU 30.600초, 별도 actor CPU 6.723초다. 누적 975,024 + 연구 잔여 4,976 + 최종 예비 84,000 = cap 1,064,000. 유료 자원·다른 환경·HOLDOUT·SEALED·예비 사용 0. champion240·main·Participants·백업·기존291/292 자료는 보존했다.

현재 개인 원문 문서 폴더는 비어 있어 원문 재열람은 하지 못했다. 저장소의 기존 적용 기록과 문제 계약 및 실제240 source를 근거로 짧게 후보를 선택했으며 개인 문서·raw trace·seed는 공개하지 않는다. 동일 호스트 pixel-only worker 검증이며 새 공식 제출 qualification은 아니다.
