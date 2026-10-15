331 N2 고정 steering 페달 개입 진단을 종료했다. 두 arm 모두 68번째 행동에서 첫 contact, 72번째 행동에서 damage 1.0 및 공식 crash가 발생했다. 이 구간의 296 페달 교체는 contact 회피나 crash 회복을 보이지 않았다. 두 실패가 충돌의 불가피성을 증명하지는 않는다.

독립 reset 두 번에서 저장된 330 명령 1–64를 그대로 실행했다. 분기 직전 65개 관측 stack, 수집 가능한 물리 상태, 직렬화한 정책 메모리, Python/NumPy 및 환경 RNG 상태가 정확히 일치했다. A는 원래 330의 72개 명령·73개 관측 stack·features·selector audit·float64 nominal memory·collision·damage·종료를 모두 정확히 재현했다. 330 당시 저장하지 않은 물리 GT와의 직접 일치는 주장하지 않는다.

65–72의 실행 steering은 두 arm 모두 저장된 330 값으로 고정했다. A는 저장된 페달, B는 자기 관측에서 호출한 원래 296의 최종 페달(head와 global scales 포함)을 썼다. raw nominal 페달도 별도 기록했다. B의 페달은 8개 행동 모두 A와 달랐고, 계산 steering과 실행 steering은 6개 행동에서 달랐다. 144개 행동 모두 nominal memory는 계산된 원래 controller 업데이트를 유지했다. 따라서 완전한 정책 간 비교가 아닌, 같은 steering에서의 페달 개입이다.

| 결과 | A: 저장된 330 페달 | B: 같은 호출의 296 페달 |
|---|---:|---:|
| 첫 contact / 공식 crash 행동 | 68 / 72 | 68 / 72 |
| 최종 damage / 진행률 | 1.0 / 23.97% | 1.0 / 23.97% |
| 65–67 H1 속도 평균 절대오차 | 1.204m/s | 0.327m/s |
| 첫 contact H1 예측 속도 | 46.963m/s | 49.868m/s |
| 첫 contact 실제 HUD 속도 | 16.250m/s | 16.250m/s |
| 첫 contact 예측 / 실제 HUD 목표오차 | 7.354 / 23.359m/s | 8.079 / 25.538m/s |

68번째는 모두 6개 모델의 marginal support를 통과했다. 이 범위 검사는 contact 예측의 정확성을 보장하지 않았다. 69–72는 모두 support 밖이어서 selector가 296으로 fallback했다. 개입 B의 예측은 실제 고정 steering을 입력해 다시 계산했으며, 서로 다른 관측에서 나온 목표 q를 arm 간 동일 목표로 간주하지 않았다. branch 종료 위치 차이는 0.084m, heading 차이는 0.047rad였다.

첫 contact 시각은 두 arm 모두 실제 환경 시간 [6.38, 6.46]초 구간이다. wrapper가 네 raw tick의 collision을 합치므로 더 정밀한 발생 시각을 꾸며내지 않았다. OpenCV는 기존 setRNGSeed(0) 호출 이력이 같지만 숨겨진 RNG 상태 getter가 없어 직접 일치를 확인하지 못했다. 물리 상태 일치도 수집 필드에 한정되며 Box2D의 숨겨진 warm-start·broadphase·island 상태까지 포함하지 않는다. 이는 후향적으로 선택한 TRAIN 한 지점의 국소 진단이며 완주 성능이나 일반화 검증이 아니다.

총 144 native 행동, raw step 576 tick 및 reset 102 tick을 사용했다. 두 native 실행 wall 합은 11.288초, evaluator CPU 9.701초, actor CPU 1.576초였다. 저장된 관측 72회의 사전 actor 검증은 native 0회였다. 연구 잔여는 215→71, 최종 예비 84,000 및 champion296을 보존했다. 새 fit·source physics 실행·유료 자원·DEV/HOLDOUT/SEALED 개방·승격은 없다. 독립 검증은 추가 정책 호출이나 시뮬레이션 없이 통과했다.

다음 정보 가치가 큰 가설은 prefix64까지 누적된 경로 추적 상태가 첫 접촉에 관여한다는 것이다. 우선 저장된 픽셀·물리 측정으로 contact 기하와 경로 추적 오차를 확인하고, 그 증거가 있을 때 같은 페달 아래의 steering 개입을 별도 사전등록한다. 현재 두 실패만으로 이 원인을 확정하지 않는다. 추가 실험은 실행하지 않았다. 승인 종료는 2026-10-17 19:01:55 KST이며 자동 연장은 없다.

재현 코드는 `pedal331_run.py`, 픽셀 전용 observer는 `pedal331_worker.py`, 결과·비용 집계는 `pedal331_close.py`, 저장 증거 독립 검증은 `pedal331_verify.py`다. seed·모델 계수·정규화·ZIP·raw 픽셀·물리 GT·정책 상태·상세 trace 및 사전등록은 공개 저장소 밖에 보존했다.
