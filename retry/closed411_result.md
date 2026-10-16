# 411 — 살아 있는 부모 자격과 상태 기반 O/C 실제 폐루프

**살아 있는 부모/무질의 대조 게이트를 통과한 뒤, O와 C를 각각 한 번 실제 폐루프로 실행해 둘 다 손상0으로 완주했다.** O는14.78초·개입0으로 기존 nominal을 보존했고, C는15.08초·pulse1회였다. C 개입은 현재 상태의 nominal 위험 예측 때문에 선택됐으며 결과 label이91번째였다. 이후 실제 상태에서98번 다시 질의했지만 반복 개입은 없었다. 이 알려진 N1의 GT 진단은 픽셀 champion296 승격·독립 일반화·안전 fallback 검증이 아니다. [집계/비용](closed411_result.json) · [동결 코드](closed411_run.py)

## 사전 동결과 실제 부모 게이트

전체 상한800 wrapper·reset6·모델60,000tick·1200world·CPU180초·실행 wall300초·동시1개를 등록했다. 구현 준비 시간은 별도로 계측했다. 학습·actor·SEALED·최종 예비·유료 자원 사용은0이다. reset 상태와 알려진 C pre91 상태에 각각 queried/unqueried 실제 환경을 한 번씩 만들었다. 게이트184 wrapper/reset4와 정책 O/C 각각 최대308 wrapper/reset1로 전체 상한을 맞췄다. 계획 SHA256은 `1e7d87951c5e3c84f762208b26fe3c5ff3d4975d665d0b038dfea877ea6e3d7b`다.

게이트에서는 원래 C prefix와 nominal 계산이404 기록에 일치해야 했다. target 현재 실제 부모는 살아 있는 상태로 두고 snapshot에서 독립 모델 질의를 수행했다. 질의 전후 **full 이용 가능 물리 상태·실제 controller memory·환경/Python/NumPy RNG·픽셀 hash·wrapper/finish 상태**가 정확히 같아야 했다. 그 다음 실제 부모에 **nominal 한 행동**을 적용하고, 새 reset/같은 prefix로 만든 **무질의 대조의 full 전후 상태·명령·raw tire·결과**와 정확히 비교했다. 게이트의 실제 행동은 선택 pulse가 아니라 명시적으로 nominal이었다.

reset과 C pre91 모두 통과했다. 그 nominal 한 행동의 모델-실제391 대조도 통과했다(reset 오차0, C 위치 오차0·속도/yaw 약3e−8). 첫 실패면 정책 주행을 열지 않도록 했으며, 이번에는 두 게이트가 끝난 뒤에만 O를 시작했다. source에 내보내지 않는 solver warm-start/manifold 전체의 비트 동일성을 주장하는 것은 아니다. 다만410에서 빠졌던 **살아 있는 실제 부모의 질의 후 실제 동작과 무질의 대조**를 이번에는 수행했다.

## 같은 선택기를 실제 현재 상태마다 적용

O에는 O nominal/memory, C에는 C nominal/memory를 적용했다. 현재 실제 nominal은 한 번 계산해 실제 memory를 갱신하고, 예측은 계산 전 memory의 독립 복사와 현재 actual snapshot에서 시작했다. branch의 미래 memory와 override 조향을 실제 controller memory로 복사하지 않았다.

현재 nominal13행동을 두 독립 world에서 예측·반복해 일치와 부모 불변성을 확인했다. nominal이 안전·진행 적격이면 실제 nominal을 그대로 실행했다. 불적격일 때만 기존 고정 pulse `[0,0,float32(0.3)]` 한 행동 후 같은 nominal feedback recipe를 두 번 예측해, 적격인 경우에만 첫 pulse를 적용했다. 이후에는 새 실제 상태에서 다시 판단했다. horizon13·3.24m 목표·13행동 고정 deadline 갱신·기존3m/충돌·손상/도로·grass/후진·domain 기준을 유지했다. 절대 시점·arc·seed에 의한 개입과 gain/horizon/후보 튜닝은 없었다.

매 질의의 살아 있는 부모 full 상태·memory·RNG 불변 검사도 계속했다. 총376회(게이트2+정책374) 모두 통과했다. 모델 미자격·두 recipe 불가·비용 초과·실제 안전 실패라면 검열 중단하며 불안전 nominal로 자동 복귀하지 않는 계약이었다. 이 중단 계약을 운전용 안전 fallback이라고 부르지 않는다.

## 새 실제 결과와 과거 대조

| 새 실제 주행, 각1회 | O+268 + 선택기 | C+268 + 선택기 |
|---|---:|---:|
|공식 lap |14.78초 |15.08초 |
|손상 / 안전 위반 |0 /0 |0 /0 |
|최대 경로 오차 |1.317m |1.379m |
|wrapper / 질의 수 |185 /185 |189 /189 |
|pulse 선택 수 |0 |1 |
|자기 과거 대조 대비 |0.00초 |0.00초 |

과거 대조는 **404 O의14.78초·손상0**과 **408 고정 pulse의15.08초·손상0 관측**이다. 별도 새로운 대조 arm을 동시에 만든 전체 랩 paired 비교가 아니다.408의 원래 terminal tick 기술 자격 실패는 그대로 보존한다. 이번411은 정상 partial tick 계약을 사전 적용한 별도 새 실제 주행이다.

O185행동의 명령·post 센서·nominal memory 전후가 과거 O와 정확히 같았다. 최종 이용 가능 physical/RNG/픽셀/wrapper도 같았다. 즉 이 알려진 episode에서 모델 질의가 O의 nominal 결과를 바꾸지 않았다. C도 결과적으로189행동의 명령·post·결과가 과거 고정 pulse 기록과 같았지만,91번째를 조건식에 넣어 강제한 것은 아니다. C91의 nominal 위험 예측이 불적격이고 pulse가 적격이어서 선택됐으며, 다음98개 실제 상태에서는 nominal이 적격이었다. O보다0.30초 느리므로 시간 개선으로 해석하지 않는다.

O165회·C168회 실제 milestone hit와 일관된 목표 갱신을 기록했고 실제 deadline 위반은0이었다. 각 실제 행동의 진행도 양수였으며 최소 약0.114m였다. 모델의 미래 목표 도달을 실제 도달로 대신하거나 deadline을 매 query마다 무조건 미루지 않았다.

공식 finish metadata와 timestamp를 현재 상태로 처리했다. O 마지막 행동은4 raw tick, C는3 raw tick이었고 각각16/12 wheel sample이 완전했다. C의 실제 controller DONE 전환도 통과했다. official timestamp에서 reset 시작 시각을 뺀14.78/15.08초를 사용했으며, 관측이 끝난 시각을 lap으로 바꾸지 않았다.

## 모델-실제 대조와 질의 지연

실제 선택된 첫 전이374개 모두391의 위치0.1m·속도0.5m/s·yaw0.05rad/s와 충돌/손상/접촉·raw tick/종료/finish timestamp 기준을 통과했다.

| 첫 전이 최대 오차 | O | C |
|---|---:|---:|
|위치 m |1.53e−5 |3.15e−5 |
|속도 m/s |2.30e−5 |2.29e−5 |
|yaw rad/s |4.04e−6 |1.04e−5 |
|시각 s |0 |0 |

읽기 전용 사후 감사에서는 실제 미래 개입과 recipe가 일치하는 저장 예측만 추가 대조했다. O185개·C177개 horizon에서4550개의 겹친 상태 비교가391 기준을 통과했다. C의12개 이전 nominal 예측 창은 뒤의 실제91번째 pulse로 행동 recipe가 달라져 제외했다. 이를 source 실패나 맞은 예측으로 억지로 세지 않았다. 최대 horizon 위치 오차는 O5.34e−5m·C3.81e−5m였다. 실제 미래는 평가자만 읽었고 선택/예측 입력에는 넣지 않았다.

| 질의 지연 | O max / p95 | C max / p95 |
|---|---:|---:|
|CPU |521 /338ms |633 /449ms |
|wall |525 /348ms |635 /454ms |

질의 구간은 현재 실제 nominal 계산 뒤의 full snapshot 캡처부터 독립 nominal 반복·필요 시 pulse 반복·불변성 검사·forecast 저장까지다. actual 환경 step과 바깥 latency journal 기록은 제외한다. 그 비용도 전체 CPU에는 포함됐다. 질의 실패는0이다. simulated control period80ms보다 p95가 길다. simulator는 질의 중 물리 시간을 진행하지 않으므로 이 공식 랩 시간과 실제 질의 지연은 다른 시계다. 실시간 가능성이나 contest inference 예산 적합성을 주장하지 않는다.

## 비용·보존과 한계

| 구간 | 실제 wrapper / reset | 모델 tick / world |
|---|---:|---:|
|실제 부모 게이트 |184 /4 |312 /6 |
|O 정책1회 |185 /1 |18,616 /370 |
|C 정책1회 |189 /1 |19,110 /380 |
|합계 |**558 /6** |**38,038 /756** |

실제 raw step2231tick·reset306tick, source0시간 접촉 구성756회를 따로 기록했다. wrapper558와 모델38,038tick 모두 확인됐고 미확인 청구는0이다. wrapper242회·모델21,962tick을 쓰지 않았다. worker CPU133.719초·wall135.255초, import/사전 확인 포함 whole-worker CPU134.415초였다. 읽기 전용 사후 감사 CPU0.318초·wall0.324초는 별도이며 두 CPU 합134.733초다. 준비 구현 wall166.957초는 추론/도구 지연을 포함한 별도 구간이고 구현 CPU는 완전 계측하지 않았다. 문서/git 전체 시간은 계측하지 않았다.

원장과 budget v431에 실제558회를 한 번 차감했다. 누적 실제 wrapper **1,317,730**, 연구 잔여 **30,334**, 최종 예비 **84,000·사용0**이다. 학습·actor·SEALED·추가 유료 자원·예비 사용은0이다. champion296·240 롤백·공식 main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·보호 자료·SEALED16·승인 종료2026-10-20 19:01:55 KST·원래408 실패를 보존했다. 실제/예측 raw 상태·명령열·RNG·snapshot·seed·지도/profile은 git 밖에 두고 집계와 코드만 공개한다.

새 증거는 **같은 알려진 N1에서의 실제 부모 비간섭과 상태 기반 선택기의 단일 폐루프 완주**다. 반복 개입은 이번 한 C 실행에서는 필요하지 않았지만 다른 조건에서의 안정성·독립 일반화·모델 미자격 시 안전 fallback·픽셀 관측·실시간 실행은 검증되지 않았다.296 승격·새 최적화·재주행·추가 pulse 탐색은 하지 않았다.
