# 273 — 적법 공동 residual 정책의 실행 조향 메모리 대조

**작은 적법 후보를 찾았다.** 고정한 − 방향 정책에서 실제 반환 조향을 메모리에 반영하면 O0/N0가23.46/23.00초로 완주했다. 240보다 각각0.20/0.62초 빠르며 무접촉·무손상이다. 다만 주 게이트의4/4 완주는 실패했고, 두 알려진 DEV 도로의 후보 탐색 결과이므로 챔피언은 변경하지 않았다.

| DEV·고정 방향 |원래 nominal 조향 메모리 |실제 반환 조향 메모리 |공통 완주 시간 차이 |
|---|---:|---:|---:|
| O0·+ |24.30초, damage0.2 |23.98초, damage0 |−0.32초 |
| O0·− |24.02초, damage0.2 |**23.46초, damage0** |−0.56초 |
| N0·+ |crash131, damage1 |off_track175, damage0.6 |산출하지 않음 |
| N0·− |23.62초, damage0.2 |**23.00초, damage0** |−0.62초 |

240은 O0 23.66초·N0 23.62초다. 메모리 방식별3/4 완주로 완주 수는 같다. 공통 완주3쌍은 모두 실행 메모리 쪽이 빠르지만, N0 + 정책의 실패는 해결하지 못했다. 전체6완주·실제 DNF2·censor0·기술 오류0이다. 모든 실행은325행동 상한보다 일찍 끝났다. N0 +의 실패 시간이 늦어진 것을 완주 시간 개선으로 대신하지 않는다.

## 실제 근거로 선택한 가설

244의 보상은 이미 complete `2−T/160`, actual DNF `p−1`로 공식 episode 완주 시간과 정렬돼 있었다. 245에서도 보상/완주 순위 역전 근거가 없었다. 따라서 보상 오류를 새 가설로 꾸미지 않았다. PPO244는8,192 training actions·8updates의 **16→2 pedal actor**, ARS247은4개 antithetic 방향의 **pedal-only actor와 단 한 update**였다. 둘 다 조향을 고정했다. 단독 pace/경로 전이·목표점 교체·전역 pedal 변형·위치 knot·fallback 조정은 이번에 사용하지 않았다.

새 질문은 **현재240 위의 feature-conditioned 3채널 episode 정책에서 실행한 조향과 다음 정책의 steering memory를 맞추는 것이 유용한가**다. 이전189의 짧은 공동 기동도 실행 조향을 메모리에 반영했고, 더 오래된 observer/모방 정책에는 action history가 있었다. 따라서 공동 제어나 history 자체가 처음이라는 주장은 하지 않는다. 이번 새 대조는 현재240에서 같은 전체-episode 공동 residual의 **nominal-memory 대 executed-memory**를 직접 짝지어 비교한 것이다. 교사 행동 회귀도, CEM/ARS update를 이름만 바꾼 학습도 아니다.

## 실행 전에 고정한 작은 실험

TRAIN231 mean/std와 원래240의16개 적법 feature를 사용한다. 기존6개 DEV의240 feature cache에서 road-balanced latent RMS0.2가 되도록 seed273의 Gaussian17×3 방향 **한 개**를 정규화했다. 동일한 방향의 ± 두 정책, 동일한 residual 크기 `[steer0.015,gas0.03,brake0.02]×tanh(latent)`를 썼다. 조향은±0.4, pedals는0..1로 clip한다. 매 행동의 독립 noise·새 fit·parameter grid·optimizer update는 없다.

두 메모리 방식 모두 original240 path·nominal controller·head·global scales를 먼저 실행한 뒤 동일한 공동 residual을 더한다. 대조군은 원래 nominal `previous_steer`를 유지하고, 실행군은 **실제 반환 float32 steering command**로 갱신한다. 다음 행동의 route connection·nominal smoothing·feature7·actor는 자신이 소유한 메모리를 사용한다. 이것은 실제 wheel joint/yaw를 알고 있다는 뜻은 아니다. Pedal actuator state·가림·미래 경로 관측의 충분성도 이번에 해결했다고 주장하지 않는다.

고정 순서로 O0/N0×±×2memory, 총8회였다. 예상2,368 native, 상한2,600·회당325를 사전에 기록했으며 상한은 censor로 취급했다. 실제 DNF가 나와도 다른 예정 대조를 생략하지 않았다. Actor 입력은 pixels뿐이고 GT·teacher·도로ID·전체 지도는 없다. 현재 관측과 자기 메모리에서 계산한 공동 actions만 환경에 전달한다. Damage는 진단이며 보상·선택에 추가하지 않았다.

## 검증과 게이트 해석

Zero residual16쌍에서240 action·feature·memory가 정확히 일치했다. Active8개 산술 검사, 실제2,089개 행동의 원래 head/scales·공동 residual/clip·메모리 선택·다음 feature7 연결을 모두 재구성했다. Archive 원본·모듈 hash·한 CPU/thread·금지 read/import·actor 회수도 통과했다.

사전 **주 게이트**는 executed-memory4/4 완주, 최소3/4 matched pair 시간 개선, 어떤 pair도80ms 넘게 악화하지 않는 것이었다. N0 +의 DNF로 **실패**했다. 사전 별도 **후보 게이트**는 실행 메모리의 고정 sign 하나가 두 도로 모두240보다 빠르게 완주하는 것이며, **− sign만 통과**했다. 결과 뒤 기준을 바꾸지 않았다. 공통 완주만의 평균−0.50초를 실패 pair까지 포함한 효과로 확대하지 않는다.

이는 특정 작은 공동 정책의 실행 메모리 정렬에 양성 신호가 있다는 근거다. + 방향의 실패와 단일 direction·각1회 실행 때문에 일반적인 안전성·학습 수렴·원인 하나를 확정하지 않는다. PPO나 ARS 방법군 전체를 기각하지 않으며, GT oracle19초대 기록과 이번 적법23초대 기록을 혼동하지 않는다.

동결한 −/executed 정책을 **비공개 standalone ZIP**으로 묶었다. Worker 실행과16쌍의 action·feature·memory 일치를 확인했으며 native 재주행은0이다. 현재 챔피언이나 공식 자격 확인을 마친 제출물은 아니다. SHA256: `065c55255ae02f425e094b0706ca46bad708013a5271beb7910608426ac96449`.

## 다음 선택과 실제 처리량

다음 최소 선택은 **동결한 −/executed 후보를 나머지6개 기존 DEV에서 regression gate**하는 것이다. 재학습·방향 추가·계수 변경보다 이를 먼저 권한다. 이 도로들도 이미 연구에 사용된 DEV이며 독립 HOLDOUT이 아니다. Baseline 예상1,499 native·약74초, 회당650 상한으로 총3,900 native를 확보하려면 현재 잔여516 외에 **추가3,384 native**가 필요하다. 이번에는 새 대조를 실행하지 않았다.

넓은 DEV 완주 게이트를 통과할 때만, 더 긴 적법 공동 episode-policy 학습을 권한다. 목적 있는 예시 규모는16×2,048=**32,768 training actions**와 최종6개 DEV·미리 등록한 fresh DEV2개에서240와 짝지은 평가 최대6,500회, 합계 **39,268 native**다. 최종 모델만 평가하며 중간 screen/checkpoint 선택은 하지 않는 설계다. 현재 실측20.36native/초 기준 약32분이다. 이는 검토용 학습 배정량이며 수렴에 필요한 양을 증명한 수치는 아니다. 기존8,192-action PPO나 단일 ARS update보다 충분한 목적 있는 학습을 평가하려는 규모이고, 앞 게이트 실패 시 깊은 학습을 시작하지 않는다. 이 추가량을 자동 승인·집행하거나 예비에서 가져오지 않았다.

## 실제 비용·보존

새 **2,089 native**, raw step8,349틱·reset408틱, 평가 wall102.59초·evaluator CPU84.09초·actor CPU18.42초다. Offline preflight45회·1.71초, ZIP 대조36회를 별도로 기록했다. Baseline materialization·새 teacher label/fit·geometry solve·model physics·유료 자원은0이다.

**B920000 = 누적835484 + 연구516 + 예비84000(사용0)**. 연구 전체를 잔액 때문에 폐기하지 않고 후보·다음 게이트와 조건부 학습 비용을 남겼다. 챔피언240·main·Participants·백업·사용자 변경·HOLDOUT·SEALED는 보존했다. Raw 관측·seeds·parameter arrays·ZIP·실행 receipt는 비공개로 남겼다.

[집계](joint273_result.json) · [고정·대조 검증](joint273_prepare.py) · [pixel actor](joint273_worker.py) · [실행기](joint273_run.py) · [ZIP builder](joint273_build.py)
