# 477 고정 pre23/P4 모델 비교 — 두 법칙 모두 미완주로 종료

승인된 단일 비교를 한 번 실행했다. 기존 P4와 첫 raw minimax 할당 P4 모두 경로3m 기준으로 **UNSAFE**, 안전한 자기 finish는 없었다. 후보는 승격하지 않고 종료했다. 완주 시간 이득·전체 P4/제어 계열의 불가능성을 주장하지 않는다. actual/native/reset/actor/HOLDOUT/SEALED는 모두0이다.

## 실행 계약과 통합 게이트

동일한 저장 pre23 full root·memory·RNG·actual ledger와 고정 P4 nodes를 사용했다. nominal은 행동당 한 번만 호출하고 복사한 float32 명령의 활성 pedal만 변경했다. 조향·참조·피드백·controller memory·80ms hold를 유지했다. 실제 current wheel GetWorldVector/linearVelocity/omega/gas/tiles/grip/engine을 읽었고 저장 미래 telemetry는 명령 입력으로 사용하지 않았다. 선택 후 첫 raw telemetry는 힘 항등 검증에만 사용했다.

source35world/1,137ticks, Original·기존P4·할당P4의 독립H13/held9world/324ticks, 후보 pending3world/3ticks로 **47world/1,464ticks 통합 게이트를 통과**했다. pending은 full ForecastLedger 설치 후 Stream을 생성하는 RestoredParent를 사용했다. 두 독립 후보와 held own-step의 AT_ROOT 공식 확인 event가 일치했고 actual DONE 권한은 없었다. 두 whole 모두 자신의 H13과 정확히 연결됐다. 후보의 모든 dispatch는 독립 경계/rank 검증과 첫 raw gas/brake/omega/종횡력/ratio의 정확 일치를 통과했다.

최초 등록은 physics0 상태에서 검토 후 보존했다. pending ledger provenance와 임시파일 상한을 실행 전에 고쳐 `477-revision1`로 재등록했으며, 모델 실행은 이 등록에서 한 번뿐이다. 등록 SHA는 `a5695c469d717faacbcf87104dab4d5d5e9540a2fb8a1469aa9b53532daa5c01`이다.

## 두 whole 결과

| 항목 | 기존 P4 | 할당 P4 |
|---|---:|---:|
| 행동 / positive raw ticks | 51 /204 | 74 /296 |
| own H13 연결 | 정확 일치 | 정확 일치 |
| 최초 raw 경로 위반 물리 시각 | 6.82초 | 8.66초 |
| root 이후 최초 위반 시간 | 4.04초 | 5.88초 |
| 최초 위반 arc | 324.368m | 431.108m |
| 최초 위반 경로 오차 | 3.115m | 3.069m |
| wrapper 종료 시각 | 6.86초 | 8.70초 |
| 전체 최대 경로 오차 | 4.003m | 3.740m |
| 전체 최대 요구력/한계 비율 | 3.959 | 2.883 |
| clipping 휠 표본 /전체 | 82 /816 | 130 /1,184 |
| 안전한 자기 finish | 없음 | 없음 |

마지막 wrapper는 기존80ms hold를 유지하므로 첫 위반 뒤 두 raw가 더 포함된다. 최초 위반과 wrapper 종료를 구분했고 공통 안전 구간 분석은 첫 위반에서 검열했다. 노출 길이가 다른 전체 clipping 표본 수나 최대 비율만으로 안전 원인·성능 우열을 결론내리지 않는다. 기존 P4의 51행동 전체 raw 행은 473의 P4와도 정확히 일치했다.

## 실제 개입과 공통 공간·시간

두 whole은 **첫46행동/184raw까지 모든 행이 정확히 같았다.** 후보 whole74회 계산 중7회 실제 pedal이 변했고7회 모두 첫 raw M이 엄격히 줄었다. 첫 개입은47행동, 물리6.46초/root+3.68초/arc302.295m였다. gas0.780729→최대 동률 float32 약1.61e−15, 첫 raw M0.752139→0.496378이었다. 거의0인 값은 실제 반올림 plateau의 최대 해이며 epsilon이나 임의 pulse가 아니다. 나머지 개입은69∼74행동이었다.

| 물리6.82초의 동일 raw 시각 | 기존 P4 | 할당 P4 |
|---|---:|---:|
| arc | 324.368m | 324.137m |
| 경로 오차 | 3.115m | 0.660m |
| 속도 | 64.034m/s | 62.363m/s |
| 해당 raw 최대 힘 비율 | 3.213 | 0.558 |
| 그때까지 안전 기준 | 최초 위반 | 통과 |

5m 공통 arc 그리드에서도 같은 위치를 통과하는 raw 시간 구간을 비교했다. arc305/310/315/320m의 old-minus-allocation 시간 괄호는 모두[-0.02,+0.02]초로 겹쳤다. arc320m 경로 오차는 기존1.844m/할당0.493m였다. 시간 이득의 증거가 아니라 비슷한 도달 시간에서 경로 차이가 난 저장 모델 결과다. 원본 20ms 동일 시간·5m 공통 공간 표는 비공개 raw에, 말단 집계는 `compare477_spatial.json`에 있다. 위치는 사후 진단값이며 정책 트리거로 사용하지 않았다.

첫 개입 wrapper의 실제 M은4raw 동안0.496→0.395→0.213→0.046으로 줄었지만,69행동에서는0.528→0.684→0.858→1.053으로 다시 커졌다. 마지막74행동은 첫 raw0.974 뒤0.523→0→0이어도 경로가3m를 넘었다. 따라서 **첫20ms 목적값의 최적화/감소는80ms 또는 전체 안전 인증이 아니다.** 이 모델에서 첫 실패 구간을 피했으나 다음 구간에서 실패했으므로 안전 회복 승격과 가상 완주 이득을 부여하지 않는다. 실패 후 법칙·가중치·root·hold·안전 기준을 바꾸거나 재실행하지 않았다.

## 실측 비용·원장·보존

모든 자격47world와 두 whole을 원장에 반영했다: **1,964 positive ticks/charged1,964/49 confirmed worlds**, 계획3,674ticks/49worlds와 charged hard4,096 이내다. whole는204+296=500ticks/2worlds다. allocator는 root27+pending3+whole74=**104회**(상한304), 측정 집계CPU0.816초/wall0.812초이며 호출별0.25CPU/0.5wall 및 집계120/180초 제한에 걸리지 않았다.

worker 전체 CPU55.444초/wall55.038초다. 별도 분석·공간 분석·전체 파일 readback 함수 CPU까지 측정한 소계는57.850초다. 각 후처리 interpreter 시작과 최종 메타데이터 작업을 정확 계측값으로 가장하지 않으며, 후처리에 보수적으로30CPU초를 청구해 **전체 CPU 청구85.444초/상한600초**로 기록했다. worker 종료 후 대기까지 포함한 readback 마감 wall은220.10초/상한900초였다. 최종 publication에서 남은 마감 시간도 다시 확인한다.

현재 source manifest 증가는856B로 등록 허용8,808B 이내다. /tmp 필요1,123,694,279B 대 등록 여유2,325,364,736B, workspace 필요603,979,776B 대 여유858,480,640B였다. 입력4KiB/증명8KiB, own-reference64KiB, runtime-link256KiB, constructor/firststep/input2MiB, 기타 atomic 파일32MiB 상한을 쓰기 전에 검사했다. 모델 raw536,491,719B와 allocator 추가16MiB, temp32MiB, 각 볼륨 reserve512MiB를 유지했다. quota는 역사적 atomic writer의 출력 bytes를 유지하며 크기를 선검사한다.

새 모델 raw는 /tmp 단일 사본 **156,385,162B/602파일**이다. 모든 파일을 두 번 열어 전체 길이·SHA와 JSON을 확인했다. 새 압축/아카이브·workspace raw 복제는0이다. 초기 physics0 등록4파일도 별도 길이·해시 검증과 함께 보존했다. 기존 파일 삭제/이동, 기존 raw·백업·공식 Participants·main 기준·사용자 변경 훼손은 없다. 보호18파일과 actual query 원장 v476의 해시는 그대로다. per-run `budget.json`과 비공개 `stage477-model-ledger-private.json`에 모델 비용을 기록했고 actual 원장을 차감하지 않았다.

실행 중 단계별 체크포인트와 비공개 workspace 마감 체크포인트를 남겼다. full before 입력·P4 nodes·RNG bytes·계획·버전·전체 manifest·재현 조건은 비공개 workspace에 있고 공개 커밋에는 코드·집계만 둔다. /tmp가 사라지면 해시만으로 raw를 복구할 수 없다. 명시적 연장 근거 SHA `3b0dc9c16c5356e107e73dbd8a8f88e75a2434f9e24f046358783fbde8307078`, 종료 **2026-10-20 19:01:55 KST**를 유지하며 자동 연장이나 후속 실험은 없다.
