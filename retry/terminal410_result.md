# 410 — 종료-aware source 자격과 저장 창 검사

**현재 finish tracker·phase를 인과적으로 복제한 source 모델이 자격을 통과했고, O185개·C91개 저장 창 검사를 완료했다.** source 미자격·안전/진행 오탐·미탐은0이었다. O에서는 pulse 질의/선택0, C에서는 알려진 실패를13행동 안에 포함하는 pre91에서만 고정 pulse를 질의해 적격으로 선택했다. 이는 **알려진 N1의 겹친 저장 창 검사**이며, 새로운 실제 feedback 정책·안전 fallback·픽셀296의 검증이 아니다. [집계 결과](terminal410_result.json) · [모델](terminal410_model.py) · [동결 검사 코드](terminal410_run.py)

## 구현과 사전 동결

기존 `SourceVehicleTransition`과408의 원래 코드/계획/실패 결과는 수정하지 않았다. 새 모델은 현재 physical snapshot 외에 **현재 finish tracker 전체 필드·raw clock·elapsed counter**를 복제한다. raw tick마다 기존 Car/Box2D를 먼저 적분하고, 현재 위치/속도/방문 진행률로 같은 `FinishLineTracker.update`를 호출한다. 후보 crossing 시각과 뒤의 확인 시각을 구분하며, 공식 finish·환경 terminal 시 action repeat를1–4 tick에서 종료한다. C controller는 복제된 현재 phase/memory와 모델의 현재 finish metadata로 계산하고, 모델 finish 뒤에만 DONE을 갱신한다.

모델60,000 tick·1200 world·CPU180초·wall300초·동시1개·native/actor/학습/SEALED/예비/유료0을 등록했다. 두 recipe는 기존 nominal feedback과 첫 행동 `[0,0,float32(0.3)]` 후 같은 nominal feedback뿐이다. horizon13, 목표3.24m·13행동 deadline을 유지하고, 목표를 실제 과거 prefix에서 달성했을 때만 갱신했다. 각 창에서 무조건 deadline을 새로 주지 않았다. 정상 예측 공식 finish도 종료 성공으로 처리했다.

O에는 O 법칙과 O memory, C에는 C 법칙과 C memory를 사용했다. branch에는 현재 snapshot·현재/과거에서 복원한 memory·현재 목표/deadline만 전달했다. 실제 미래 명령/상태는 evaluator만 읽었다. nominal이 적격이면 pulse를 질의하지 않았고, 불적격일 때만 고정 대안을 독립 두 번 평가했다. step/실패 arc를 트리거에 넣거나 오탐 뒤 기준·gain·horizon을 조정하지 않았다. 계획 SHA256은 `893b64be68a7bbedc95f796c6b3430a0e93926ccf551527ea961b240a205c365`이다.

## 먼저 통과한 자격

정적 검사에서는 tracker 후보/확인 시각과 복사본 독립성, 현재 timestamp의 DONE 허용·미래 timestamp 거부, 정상 partial record와 누락 표본 거부를 확인했다. 이 단계에는 world 생성·양의 물리 적분이 없었다.

그 뒤 모델로 저장된 실제 명령 prefix를 인과적으로 재생했다. O185행동740tick, C103행동412tick,408 pulse의188행동752tick이 관측 위치·속도·yaw·시각·도로 접촉·손상/충돌·raw tick 수·종료 metadata 기준을 통과했다. C 실패를 재현한 것은 fidelity 통과이지 원래 C의 안전 통과가 아니다.

| 독립 nominal 자격 | 예측 행동 / raw tick | 실제 대조·독립 반복 |
|---|---:|---|
|O reset |13 /52 |통과 |
|O pre92 |13 /52 |통과 |
|C pre91 |13 /52 |불안전 nominal 재현·pulse 전후 참조 반복 통과 |
|O pre185 |1 /4 |공식 finish·timestamp 재현 |
|408 pulse pre189 |1 /3 |정상 partial finish·timestamp·모델 C DONE 통과 |

새 world의 body/tile/progress/finish 상태 복원을 확인하고, 모든 branch에서 입력 snapshot·controller memory·전역 RNG 불변 및 독립 world 결과의 정확한 반복을 요구했다. C pre91에서는 pulse 두 반복 뒤 nominal을 다시 비교했다. 이 자격들 전에는 전체 창을 평가하지 않았고, 첫 모델/복원/독립성/fidelity 실패면 이후 창을 모두 중단하도록 했다. 이번에는 해당 실패가 없었다.

부모는 실제 명령 prefix를 재생하고 snapshot을 캡처한 뒤 닫았다. 따라서 검사한 불변성은 **부모 snapshot 표현/입력·memory·RNG와 새 world 간 반복**이다. branch 이후 살아 있는 연속 부모를 한 step 더 진행시켜 대조하는 별도 검사는 하지 않았다. solver warm-start·broadphase/island history의 비트 복원도 주장하지 않는다.

## O185 → C91 순서의 창 결과

| 분류 | O+268 | C+268 |
|---|---:|---:|
|완료한 겹친 창 |185 |91 |
|실제 nominal 안전 / 불안전 창 |185 /0 |90 /1 |
|source 미자격 |0 |0 |
|안전 오탐 / 미탐 |0 /0 |0 /0 |
|진행 오탐 / 미탐 |0 /0 |0 /0 |
|예측 / 실제 진행 실패 |0 /0 |0 /0 |
|nominal domain 실패 / 두 recipe 불가 |0 /0 |0 /0 |
|pulse 질의 / 적격 선택 |0 /0 |1 /1 |

각 창의 nominal을 두 독립 world에서 먼저 봉인/반복한 후 저장 실제와 대조했다. 최대 위치 오차는 **5.34e−5m**, 속도3.82e−5m/s, yaw1.76e−5rad/s였고 시각 차이는0이었다.391 기준과 종료/접촉/손상·raw tick 수·finish timestamp를 전부 통과했다. 예측의 안전·진행 판정과 실제 nominal 창의 판정이 일치했다.

O의173개 창은13행동 전체가 있고 마지막12개는 공식 finish가 먼저 나오는 정상 종료 창이다. 이12개를 모델 실패나 검열로 세지 않았다. C는 실제 실패까지13행동이 모두 있는91개 창만 검사했다. C의 마지막12개는 실패 후 미래가 없는 별도 검열 영역이며 음성/성공 창으로 만들지 않았다. **276개는 독립 episode가 아니며, 안전 음성275개·양성1개도 독립 표본의 일반화 성능으로 해석하지 않는다.** 실제 경로가 안전한 창을 위험으로 예측하면 오탐, 알려진 위반을 안전으로 예측하면 미탐으로 분리했고, source 자격 실패는 이 지표에 섞지 않도록 했다.

C의 유일한 선택은 pre91에서 나왔다. 이 인덱스는 결과의 진단 label이며 조건식이 아니다. 현재 상태의 nominal 안전 불적격·진행 적격과 고정 pulse의 안전/진행 적격이 선택 이유다. 저장된408의 같은 pulse 이후13행동을 evaluator로 추가 대조했을 때도391 기준을 통과했다. 새 실제 반사실 주행을 한 것은 아니다.

O에서 모델상 개입0이라는 사실은 기존 성공 O의 nominal 보존에 유리한 관측이다. 실제 actor에 모델 질의를 붙여 실행한 결과나 추가 계산 지연까지 보존됐다는 증거는 아니다. 또 C 창들은 원래 C의 궤적이다. 실제 pulse 뒤의 달라진 상태에서 트리거가 재발동하는 폐루프 궤적은 검사하지 않았다. 따라서408의 고정 pulse15.08초를 이번 상태 기반 정책의 랩 시간으로 사용하지 않는다.

## 실제 비용과 남은 조건

| 구간 | 양의 모델 tick / world |
|---|---:|
|prefix와 사전 자격 |2334 /15 |
|O 창 |18,616 /370 |
|C 창 |9568 /184 |
|합계 |**30,518 /569** |

0시간 접촉 구성도569회로 따로 기록했다. tick 예약/확인30,518·미확인0이며29,482tick을 쓰지 않았다. 모델 worker CPU57.950초·wall58.957초, import/사전 확인을 포함한 whole-worker CPU58.715초였다. 정적 검사 본체는CPU0.019초·wall0.021초, 그 프로세스 전체 CPU0.922초였다. 두 프로세스 CPU 합59.637초, 계측된 모델+정적 실행 wall 합58.978초다. 자격/창별 CPU는 별도로 계측하지 않았으므로 위 구간 비용은 tick/world로만 분리했다.

사전 구현·정적 준비 wall은246.247초로 별도 기록했다. 이 값은 추론/도구 대기까지 포함하며 구현 CPU는 완전 계측하지 않았다. 이를 모델+정적 계측 구간과 합하면305.225초이고 문서/git 시간은 별도다. 등록한300초 실행 guard는 모델·정적 실행 구간에 적용했으며, 작업 전체가300초 안에 끝났다고 보고하지 않는다. 저장 결과의 읽기 전용 사후 감사는CPU0.123초·wall0.127초였다.

실제 wrapper/reset·actor·학습·SEALED·유료 자원·예비 사용은0이다. 원장과 budget v430에 모델 비용을 한 번 반영했고 연구 **30,892**·최종 예비 **84,000·사용0**·누적 실제 wrapper1,317,172를 유지했다. champion296·240 롤백·공식 main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·보호 자료·SEALED16·승인 종료2026-10-20 19:01:55 KST·원래408 기술 실패는 보존했다. raw 미래 예측·snapshot·명령열·seed·지도/profile은 git 밖에 둔다.

이번에 해결한 것은 이 N1 자료에서의 종료-aware nominal 모델 자격과 조건식의 저장 경로 분류다. 남은 조건은 실제 상태 기반 개입 후의 반복 발동/진행·안전 fallback, 독립 상태의 일반화, 픽셀 관측의 식별/불확실성, 실제 질의 지연 max/p95와 자원 계약이다. 모델/정책/296 승격이나 추가 실제 실행을 자동으로 하지 않았다.
