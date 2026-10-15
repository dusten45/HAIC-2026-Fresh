333의 단일 steering 개입에서 B는 72번째 행동까지 생존했다. 첫 contact는 A와 같은 68번째지만, 이후 contact가 지속되지 않아 최종 damage는 A 1.0 대비 B 0.2였다. 이는 고정된 후속 명령 아래 한 명령이 접촉 지속·회복에 영향을 준 국소 증거다. 완주나 일반 정책 개선은 검증하지 않았다.

| 공통 관측 구간 1–72 | 기존 실제 A | 신규 B |
|---|---:|---:|
| 첫 contact | 68 | 68 |
| contact 행동 | 68–72 | 68만 |
| 최종 damage | 1.0 | 0.2 |
| 공식 crash/종료 | 72번째 crash | 없음; 72 protocol stop |
| 고유 방문 tile | 70/292 | 73/292 |
| 끝점 속도 | 10.783m/s | 42.945m/s |
| 완주 | 아니오 | 관측하지 않음 |

두 arm의 첫 contact 시각은 실제 환경 시간 [6.38,6.46]초 구간이며 같은 장애물의 hull fixture 접촉이 기록됐다. fixture는 저장된 wrapper 끝점만 확인한 결과다. 끝점 pose 차이는 위치 13.783m, B−A heading −1.272rad였다. 원시 pose·속도·fixture·damage 변화 및 행동별 고유 진행량은 비공개 trace에 보존했다.

330과 331 A의 전체 72개 명령·73개 관측 stack 및 features/audit/nominal memory/collision/damage/종료의 일치를 다시 확인했다. 기존 A exact replay가 명확하여 새 A를 중복 실행하지 않았다. 저장 관측 66회에서 새 관측기의 원래 정책 상태 일치와 개입 계산의 332 일치를 확인한 뒤 native 실행을 시작했다.

B는 저장된 331 A 명령 1–65를 그대로 실행했다. 66번째 steering만 현재 직접 검출을 입력한 기존 routing·목표 선택·controller 법칙의 출력으로 바꿨다. 66번째 페달과 67–72의 모든 명령은 저장된 A 그대로였다. 저장 결과에서 전체 명령 차이가 66번째 steering 한 원소뿐임을 검증했다. 따라서 이것은 하나의 실행 명령 개입이며 ‘현재 검출만 쓰는 완전한 정책’의 성능이 아니다.

개입 전에 66개 관측 stack, 65개 명령, 수집 물리 상태, 직렬화 정책 메모리, 추적 가능한 RNG 및 코드·설정의 일치 게이트를 통과했다. 64번째의 직접 RNG 비교와, RNG를 사용하지 않는 기존 step 계약 아래 65번째까지의 상태 유지도 확인했다. OpenCV 숨은 RNG 상태와 Box2D 숨은 solver 상태는 직접 확인하지 못했다. 원래 계산 steering과 실행 steering을 구분했고, nominal memory는 실제 관측에서 계산한 원래 controller 업데이트를 유지했다. 직접 검출 probe 계산은 정책 상태와 RNG를 바꾸지 않았다. GT는 평가기 진단에만 사용했다.

증거는 ‘접촉 자체 회피’보다 같은 첫 접촉 이후 지속 양상이 달라졌다는 해석을 지지한다. crash·damage·속도·진행량을 함께 비교했으며 damage 증가를 자동 veto로 두지 않았다. 결과가 같거나 나빴더라도 이 한 명령의 충분성만 반증했을 것이다. stale 좌표 결함 전체나 충돌 불가피성을 판정하지 않는다. B의 72 생존은 이후 완주나 다른 도로의 개선을 의미하지 않는다.

다음 후보는 **합법적인 ego-motion 회전·이동으로 stale point를 운반하면서 가린 장애물을 보존하는 구성 요소**다. 유효한 기존 영상 affine transform을 우선 쓰고, 사용할 수 없는 구간에는 현재 HUD yaw/speed로 얻는 body-frame SE(2) 근사를 검토한다. 좌표 갱신은 `p_next = R(-delta_yaw) (p_old - estimated_body_displacement)`이며 yaw 부호·좌표·샘플 시간·HUD 양자화와 지연을 저장된 TRAIN 증거에서 확인해야 한다. norm speed만으로 횡이동을 알 수 없으므로 전방 이동 근사는 한계로 남긴다. 실제 GT 변환은 오차 진단 전용이며 제어 입력으로 쓰지 않는다.

가림 중 현재 검출이 없다는 이유로 기존 point를 삭제하지 않고 기존 radius·age·중복 제거 규칙을 유지한다. 우선 저장된 333 관측과 실제 pose 기록 및 기존 GT가 있는 TRAIN 가림 사례에서 원래 tracker와 운반 구성 요소만 바꾼 비교를 제안했다. N2의 접촉 직전 검출만으로 가림 보존을 검증했다고 주장하지 않는다. 새 fit·임계값 탐색·horizon 확대 없이 오차, 중복 hazard, 실제 가림 장애물 보존과 routing 변화를 확인하는 단계이며 이번 작업에서는 실행하지 않았다.

72번째까지 보기 위해 승인된 최소 연구 예산 1 native를 사전 등록했다. 신규 B 72행동, raw step 288 tick/reset 51 tick을 사용했다. native wall 5.686초, evaluator CPU 4.943초, actor CPU 0.738초였다. 저장 관측 검증은 66회, wall 1.369초이며 native 0회다. 신규 fit·source physics rollout·유료 자원·보호 split 사용은 없다. 연구 잔여는 0, 최종 예비 84000은 그대로다. 추가 native 실험이나 자동 예산 확대는 하지 않았다.

Champion296, TRAIN registry, 원본과 사용자 변경, DEV/HOLDOUT/SEALED 및 main 기준을 보존했다. 공개 파일에는 일반 재현 코드와 집계 결과만 포함했다. 비공개 문서·GT·픽셀·모델·seed 및 상세 기록은 공개 저장소 밖에 보존했다. 승인 종료는 2026-10-17 19:01:55 KST이며 자동 연장은 없다.
