# 304 — HUD wheel-angle를 경로 전환 비용의 기준으로 사용

**후보와 정확한 296 모두 1/2 완주이며 시간도 같아 파일럿 게이트를 탈락했다.** T2950은 off_track DNF, T2954는 27.44초 완주다. 첫 비교 뒤 O0·N0 확장이나 다른 변형을 실행하지 않았다. champion296과 240 rollback을 유지한다.

가설은 직전 명령과 실제 wheel angle이 어긋날 때 관측 wheel angle 기준의 전환 비용이 참조 전환을 줄이고 완주 우선 성능을 개선한다는 것이었다. 300의 충돌 후 역진행·target 전환·관절 지연과 현재 router의 command proxy 사용이 출발점이다. 변경은 기존 `speed * abs(next_smoothed_steer - previous_command) / 3` 비용항의 마지막 기준만 기존 248 HUD decoder의 `-front_joint_angle_proxy`로 바꾸는 것이다. 다음 조향의 smoothing에는 원래 command memory를 그대로 쓴다. HUD는 양자화·누출이 있는 추정값이며 정확한 물리 상태나 진행 방향으로 해석하지 않는다.

과거 GT planner 193/208/271/288은 지도·상태·모델 미래를 사용했지만 이번에는 현재 pixels만 사용하며 모델 rollout이 없다. Legal student 187은 target 규칙을, 248은 HUD를 넣은 학습형 pedal head를 바꿨지만 이번에는 fit 없이 경로 비용 기준 하나만 바꾼다. PPO276의 residual 학습과 CEM294/297의 공동 계수 탐색도 하지 않는다. 134의 command 기반 비용항·171의 tie 내 우회 방향 유지·253의 road image fusion과 달리 후보 그래프·mask·관측·tracker·목표점 산식은 유지한다. 284의 GT yaw 최종 조향 보정, 301/303 gas guard, 299 steering 중간값도 반복하지 않는다. 296 모델·계수와 기존 decoder는 그대로다.

결과 전에 TRAIN T2950·T2954를 고정하고, 완주 수 증가 또는 동률에서 엄격한 공통 완주 평균 시간 개선일 때만 TRAIN O0·N0를 한 번씩 추가하도록 등록했다. 총 native cap은 6,000이다. 기준 정책은 300의 정확한 296 저장 결과를 재사용했다. DEV·HOLDOUT·SEALED·champion 승격은 허용하지 않았다.

| TRAIN | 저장 296 | 304 후보 | 경로 선택 변경 |
|---|---|---|---:|
| T2950 | off_track DNF, 315 native, damage 0.2 | 같은 결과 | 0 |
| T2954 | 27.44초 완주, 344 native, damage 0 | 같은 결과 | 0 |

모든 659개 행동·legal feature·memory·접촉/종료 기록이 기준과 정확히 같다. 비용값은 각각 277·321개 호출에서 바뀌었지만, 여러 경로 후보가 있던 호출은 T2950에서 4개, T2954에서 0개뿐이었다. 그 네 호출에서도 선택이 바뀌지 않았다. 따라서 이 비교는 비용 기준의 실제 변경을 확인했으나 개선이나 새로운 실패를 보여주지는 않았다. 후보 집합에 선택지가 거의 없다는 관측을 남기며, wheel feedback이나 방향 추정 방법군 전체의 불가능성으로 확대하지 않는다. T2950의 기존 접촉 native 184와 target 소실 18개도 그대로다. 새 GT 자료나 영상은 수집하지 않았다.

실제 비용은 **659/6,000 native**, raw step 2,633 / reset 102 tick, wall 20.899초다. runner CPU 합계 30.255초·별도 actor CPU 6.653초, 병렬 episode wall 합계 39.320초를 기록했다. 학습·parameter draw·source-model physics·유료 자원은 0이다. 기술 오류·검열은 0이며 두 프로세스가 회수됐다. 패키지의 변경 범위와 659개 비용식·경로 순위를 검증했다.

종료 예산은 **누적 1,138,264 + 연구 잔여 7,736 + 최종 예비 84,000 = 1,230,000**이다. 예비와 모든 DEV 봉인을 유지하고, 공개에는 일반 코드·집계만 포함한다. main·Participants·사용자 변경·이전 결과·백업은 보존한다. 다음 한 조치는 TRAIN target 소실에서 직전 참조의 진행 방향을 보존하는 합법 후보를 만들 코드 근거가 있는지 확인하는 것이다. 이번 단계에서는 그 후보나 후속 실험을 실행하지 않았다.
