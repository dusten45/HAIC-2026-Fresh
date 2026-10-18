# 501 — factual gate 통과, 고정 envelope 패키지는 exactEMPTY_SET로 탈락

**한 번의 screen을 닫았다.** factual472 명령 replay가149holds 전체를 통과한 뒤 후보를 한 번 실행했다. 후보35holds는 안전했지만 다음36번째 명령 선택에서 exact feasible 가속도 집합이 공집합이었다. 두 번째 cold와 held-first는 실행하지 않았다. threshold/상수/P4/경로/steering 변경·rescue·재시도0이다. 안전 공식 finish와13.14초 screening 기준은 통과하지 않았고11.99초나 실제 기록 갱신은 주장하지 않는다.

| 실제 실행 | worlds | holds | raw ticks | charged ticks | 결과 |
|---|---:|---:|---:|---:|---|
| factual472 calibration |1|149|594|596|등록된 전체 비교 통과, model official finish |
| 고정500 후보 |1|35|140|140|안전 prefix 뒤 exactEMPTY_SET;36번째 적분0 |
| 합계 |2|184|734|736|4world/448hold/1792tick 상한 이내 |

## 선행 gate와 원래 source 범위

원래472 retention manifest로23..171 before/after **298 receipts**의 길이·SHA·존재 필드를 전수 확인했다. 473 pre23 paired full root/state/memory/ledger/RNG와472 prefix22를 저장 자료로 연결했다. 기존473 Original의 source/13행 physical replay와 당시 동일명령 prefix3, P4 model 반복/held 범위를 보존했다. 새로운495 C4 자격이나 earlyP4 native 자격은 이전하지 않았다.

runtime501은 namespace만 격리하고 원래397/417 source를 사용한다.491 projection/executor로 교체하지 않았다. Applicable498 code/default/global/closure/exec gates, frozen nominal/one-memory call, 저장된473 own-chain 양성과 ledger 변조 음성 fixture가 통과했다. pure IO10tests와 실제 fullObserveMixin을 fakeworld로 호출한 capture lifecycle23tests에서 physicalconstructor/reset/step0을 확인했다. 89개의 writer/read/SHA alias를 연결했고 새 directtick·bundle·child·observer·stream·manifest·종료 기록은 같은 quota 경로를 사용했다.

## factual gate가 확인한 것

source body: position<=0.1m, speed magnitude<=0.5m/s, yaw<=0.05rad/s, time<1e−8s. wheel joint/omega/slip/force와 rawhull/COM 기준 및 clipping/grass/contact/collision/rawcount/terminal/officialevent의 기존 이산 검사를 유지했다. 439 outward geometry interval과 exact ledger goal-hit/age/clock/deadline/DONE 비교도149행 모두 통과했다. model event bracket은 root대비[593,594]ticks, 고정prefix88ticks 포함 upper13.640초다.

최대 wrapper post 위치 차이는 **0.001494758m**, 최대 progress 차이는 **0.001479177m**였다. whole replay의 재계산 nominal 최대 차이2.09957361221e-05, before+after memory가 전부 exact인 행은1개다. 이는 기존435/473처럼 미래 누적 drift를 기록하는 calibration이며, 이후 모든 행을 복사한 현재 입력의 fresh exact 제어 검증으로 바꾸지 않았다. 첫 copied-current nominal/memory exact gate는 별도로 통과했다.

모든 과거 tracker-post에는 **직접 damage/phase가 없다**. wrapper-return damage·hold phase를 tick 실측으로 채우지 않았다. 저장된 post 위치/속력/시각/tracker이산·event/contact/collision은 비교했고, 연속 tracker arithmetic은 자기 관측 post로 replay해 검증했다. 이 factual replay는 미래 명령을 쓰는 관측 재현용이며 온라인 baseline이 아니다. 후보에는 자기 현재 상태·고정P4와 단 한 번의 nominal memory update만 제공했고 factual 미래 object는 후보 호출 전에 제거했다. 새 모델 direct capture는 새로운 증거이며 과거 누락을 복원하지 않는다. factual 경로의 calibration이 새로운 후보 경로 전역의 모델 정확도나 native 성능을 인증하지는 않는다. 기존 source snapshot은 solver warm-start impulse·broadphase history를 복원하지 않는다는 한계도 유지한다.

## exact 공집합 증거와 해석

후보는 root이후2.80초, reset-relative episode **4.56초** 시점에서 멈췄다. 현재 속력95.486281m/s, canonical 진행속력95.485449m/s였다. admissible interval의 하단은 **−91.168734m/s²**다. 저장 상태에서 이 하단을 exact Fraction residual로 검사하니40개의 제약 위반이 남았다. 단조 feasible 집합의 하단이 불합격이므로 실제 연속 공집합이며 `EMPTY_BINARY64`, float32 mapping 미인증,8ULP 보정 한도나 저장/source 오류가 아니다.

첫 witness는0.839412m 앞 node속도93.810405m/s의 crossing 제약이다. 첫20ms 경계 안에 횡단하고, 가장 강한 허용 scalar 제동에서도 exact squared residual이 **+164.178671m²/s²**다. 36번째 명령은 dispatch하지 않았다. 35개 적분 prefix의 자체 tracker/state/memory/RNG/ledger chain과 direct capture/safety 검증은 통과했다. 공식 finish는 없고 episode finish upper는 null이다.

저장된35전이만 다시 읽으면 직전 hold scalar end-speed 예측94.639122m/s와 model end-speed95.486281m/s 사이에 **+0.847159m/s** 차이가 있다.35holds의 최대 절대 차이는2.130529m/s다. 후보의 최대 wrapper post patherror는1.390344m였다. 이는 선택 당시 scalar feasible한 명령이 다음 model 상태의 feasible 집합을 유지하지 못한 **이번 패키지의 제한된 반증**이다. surrogate·엔진/휠·projection 중 어느 성분이 원인인지 분리한 실험은 아니며, 종방향 계획·경로/preview 전체를 기각하지 않는다. 네20ms boundary+node crossing 검사는 경계 사이 연속 stopping envelope나 타이어 feasible 보증이 아니다.

## 비용·저장·재현

worker 회계는 CPU148.697312초/wall156.921996초이며 선행 준비 charge12CPU/20wall를 포함한다. `model.step` tag 배타 시간은 factual CPU2.431149초/wall2.440202초, candidate CPU0.652085초/wall0.654044초다. 이 값에도 기존 tracing/directcapture callback이 포함되며 비계측 성능 benchmark가 아니다. 나머지 worker 비용에는 법칙/비교·fullsnapshot·JSON/codec·durable IO·readback 등이 포함된다.

저장 전 최종 serialized bytes와 atomictemp를 검사했고512MiB free reserve를 유지했다. 기존481 semantic fullstate refs, 고정128KiB content interning/1MiB chunks, immutable versions를 사용했다. 작은 raw row마다 파일을 만들던8KiB 초안은 **물리 전에**128KiB로 고쳤고10puretests로 확인했다. directtick/bundle은 기존481 reader와 호환되는 형식으로 유지했다. 반복 fullhold summary는 immutable bundle refs와 exact decoded digest로 재구성되며 어떤 측정도 버리지 않았다.

새 raw는 **1147파일/86,200,874B**이며186fullstates·734directticks·184bundles·43other다. workspace 준비·오류·마감 기록은 별도로 합산했다. runtime Store 집계에는 external/control 예약이 들어가므로 실제 disk tally와 구분한다. 모든 raw를 길이·SHA·finite JSON/중복key 금지·semanticstate hash와 content/chunk 참조로 확인했다. logical→physical version map과5개 핵심 proof의 lossless roundtrip도 남겼다. 기존 raw/백업 복사·삭제·이동·archive 생성0이다. 원본은 지정 cloud의 `/tmp`에 한 벌만 있으며 host 소실 시 hash만으로 복구되지 않는다.

saved-only 마감 formatter가 기존 `shapecheck.body.errors` nesting을 한 단계 잘못 읽어 중단했다. raw/ref/source authentication과 exact witness 생성은 이미 완료된 상태였고 오류·원본 formatter를 보존했다. 완료 manifest를 재사용해 집계 key만 고쳤으며 물리 재실행0이다. 이 실패에 보수30CPU/wall, 최종 publication에10CPU/20wall allowance를 포함한 전체 workload 회계는 **CPU189.127697초/wall207.353768초**,600/900초 이내다. 대화 전체 경과시간의 실측이 아니다. raw+workspace+public 마감 산출물 모두256MiB/2688files 및 범주별 한도 이내임을 종료 tally로 확인한다.

연구26027·reserve84000/used0 불변. 실제 action/reset/새seed/allocator/HOLDOUT/SEALED0이다. 생성한2world 모두 body/joint0으로 닫혔고 live0, 추가 world0이다. main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·공식 Participants·기존 사용자 변경/백업을 보존했다. 승인 종료2026-10-20 19:01:55KST이며 이번 패키지는 승격 없이 닫고 자동 후속·연장은 없다.

[결과 집계](screen501_result.json) · [실행 계약 요약](screen501_contract.json)
