# 278 — GAE λ 0.95 / 1.0 쌍대 TRAIN 진단 종료

275 checkpoint2의 actor·critic·Adam에서 두 arm을 시작했다. 공통 noise seed27801, shuffle seed27802와 TRAIN 순서를 고정했고 λ만 바꿨다. 각 arm 추가8,192 유효 action·8 update, 최종 checkpoint10만 평가했다. 첫 rollout의 관측·행동·보상·value·경계 배열은 완전히 같았다. 이후 궤적은 정책에 따라 달라진다. 최종 Adam step은 각각320이다.

| 지정 TRAIN | 대조 λ=.95 | 후보 λ=1 | 저장된240 기준 |
|---|---:|---:|---:|
| N0 | 24.30초, damage .4 | 25.16초, damage .6 | 23.62초 |
| N2 | 68 action 충돌 DNF | 70 action 충돌 DNF | 21.56초 완주 |

λ1은 N0에서 대조보다 .86초 느렸고 N2 실패를 해결하지 못했다. 두 arm 모두 완주1/2로240의2/2에 못 미쳤다. 알려진 TRAIN 두 도로의 단일 seed 진단이므로 일반화나 λ의 보편적 효과를 주장하지 않는다. 승격·자동 연장 근거가 없으며 챔피언240을 유지한다. DEV/HOLDOUT/SEALED는 사용하지 않았다.

학습은 대조23완주·6실제DNF·8수집cut, λ1은23완주·7실제DNF·8cut이었다. 기술 중단·손실은0이다. 평가 네 주행은 모두 정상 종료했고 두 충돌은 실제DNF이며 검열0이다. 복구 시 살아 있는 학습/평가 PID가 없고 최종 ZIP 및 각8쌍의 기존 pixel-only 추론 일치 receipt가 완료됨을 확인했다. 학습이나 완료된 검사를 반복하지 않고 미실행 평가 네 건만 실행했다.

관측된 실제 terminal의 suffix reward로 계산한 수집 시점 critic RMSE는 대조1.021 → λ1 .877, bias(V−G)는 −.666 → −.299였다. 에피소드 균등 RMSE는1.054 →1.014이며 sample-weighted 설명분산은 .021 →−.106이다. 첫 update 이후 표본 궤적이 달라 독립적인 critic 개선 검증은 아니다. 같은 표본에 대한 update 직후 RMSE .953/.757은 in-sample이다. cut의1,202/1,334표본은 실제 MC에서 제외했다. λ1도 cut에서는 마지막 V를 bootstrap하므로 전체 MC가 아니다. 277의 과거3관측 predictor RMSE 2.191% 개선은 작은 긍정 증거로 유지하며, 임의5%문턱으로 무효화하지 않는다. 이번에는 입력을 고정했다.

실제 비용은 학습16,384 + 평가757 = **17,141 wrapper action**이다. 기준240의 재실행은0이다. 병렬 학습 elapsed532.723초, 평가39.915초; 병렬 두 arm 시간을 합산해 elapsed로 표기하지 않았다. 물리 tick은 학습65,468·평가3,027, reset tick은 별도3,825·204다. 누적922,072 + 연구 잔여2,928 + 최종 예비84,000 = 승인 한도1,009,000. 예비 사용0, 추가 유료 자원0. 원시 궤적·checkpoint·최종 ZIP·ledger는 비공개에 보존했다.

상세 수치와 archive SHA256은 `ppo278_result.json`, 재현 코드는 `ppo278_prepare.py`, `ppo278_train.py`, `ppo278_finalize.py`, `ppo278_eval.py`에 있다. 다음 실험은 시작하지 않았다.
