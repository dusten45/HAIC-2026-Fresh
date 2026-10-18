# 563 — 피드백 terminal 목적의 첫 방향에서 전역 clipping/힘 게이트 탈락

**승격 0건, 새 source 시간 개선 0ms다.** 기존 안전 성공 궤적13.22초를 유지했다. 원 prefix부터 전체662raw를 독립 재전파해 매raw fullstate/힘,최종 tracker·visited·누적이력·시각 checkpoint와 finish가 정확히 일치했다. 실제 native 기록13.66초는 그대로다. source 근사 모델의 결과를 픽셀 정책의 실제 성능으로 부르지 않는다.

## 사전 설계와 실행 범위

561 첫 후보는 당시 aperture 기준에서 탈락한 기록을 보존한다.562가 그 변경 fullstate에서 기존551/537 피드백으로 전체 source 안전 완주13.22초를 확인했으므로,563의 새로운 시작 feasible trajectory로 사용했다. 원551 reference·전역 안전·출발/추적 clipping 이력과 mode 변화를 유지했다.새 pose aperture·yaw 일치·actuator baseline 복사·주기 terminal 조건은 없다.

원 행동1–34 prefix136raw를 재현하고,20hold35–54를 최적화 대상으로 두되55–67의 저장13hold를 유지했다. 그 handoff에서 실제 기존 피드백12hold68–79를 매 제안마다 새로 계산하는 수락 검사를 등록했다. 목적은 원551 행동75 endpoint의 고정 plane 도착 시각이고,원54/66 plane도 기록한다.terminal 뒤4hold까지 같은12hold 범위로 안전을 검사한다.원551 기준 상대 시각은1.6/2.56/3.28초이며 새 aperture나 임의 목표 위치가 아니다.

방향 예측에만 현재 incumbent의 저장 피드백12hold tape를 사용하는40열 float32 유한차분을 등록했다.예측을 closed-loop 미분으로 주장하지 않는다.국소 프로그램이 모든 전역 안전을 통과한 제안만 실제로 새 피드백을 계산한다.수락 조건은 실제 연결180raw 안전·terminal plane 도착 개선1μs 초과다.국소54/66 시각의 개별 비악화나5ms 개선은 요구하지 않는다.

최대3방향/3수락·6LP분기·3단일좌표 poll·총9제안·FD120열을 고정했다.각 방향은 prefix별 clipping rank 분기와 실제 관측 rank로 한 번 재구성한 분기를 검사하고,둘 다 실패하면 terminal 목적의 단일좌표 poll 한 번만 허용한다.고정 trust는 steer.003/pedal.03,poll은.0005/.005다.반경을 줄이며 통과할 때까지 반복하지 않는다.한 방향에서 수락0이면 종료한다.두 번의 작은 수락 이득 또는 예측 불일치에도 중단한다.

전체 CPU3,400초/wall4,000초,model228,800틱을 상한으로 고정했다.최종 whole feedback120,000틱/CPU1,600초와 독립 replay2,500틱/CPU60초는 별도 보존했다.제안 시작에는 finite20,000틱과 다음40열 방향 비용을 남겨야 한다.실행 전 source 해시와 입력 해시,독점 STARTED,phase별 finally 비용 FIRST·원자JSON ledger를 등록했다.승인 종료는 사용자 연장 승인에 따라2026-10-20 19:01:55KST이며 자동 연장하지 않는다.

## 관측된 반증

원 prefix136raw와 seed program132raw+562 저장 feedback48raw의 fullstate/힘이 정확히 일치했다.초기 tracking3/160,변경 handoff30/688과 전체 checkpoint가562와 같았다.시작 finite plane 시각은1.595715589/2.554756579/3.279204948초다.

첫 방향의40열을 새로 계산했다.두 LP 분기는 모두 해를 냈지만 재구성 분기의 float32 제어가 첫 분기와 같아 중복 물리 평가를 생략했다.실제 새 제안은2개다.

|제안|frozen-policy terminal 이득 예측|실제 프로그램 첫 위반|추가 관측|
|---|---:|---|---|
|rank LP|10.297692ms|행동41/raw2,clipping27/264=10.2273%|누적 최고12%;seed 대비 새 clipping7,해제0;힘 최고1.058259는 한도 안|
|terminal 좌표 poll|1.732920ms|행동38/raw1,힘1.059196564>1.059|clipping 최고10%;새 clipping1,해제0|

LP의 footprint최소.755065m,path최고2.652091m,원reference초과최고4.705764m/s는 각각의 전역 한도 안이었다.현재 제안의 직접 veto는 baseline pose 차이가 아니라 실제 누적 clipping이다.poll은 힘 한도에서 탈락했다.실제count/prefix order-stat을 적용했고,기존에 unclipped였던 표본의 새 clipping을 허용한 뒤 전역 한도로 판정했다.새 clipping 자체를 금지하지 않았다.

두 제안 모두 프로그램 단계에서 탈락했으므로 **fresh finite 피드백 실행0,새 후보 whole suffix 실행0,수락0**이다.위의 예측값을 실제 terminal 시간 개선이나 피드백 회복 시간으로 해석하면 안 된다.이번 자료는 새로운 continuation 평가기가 실제 후보에서 효과를 냈다는 증거도 아니다.정해 둔 선행 게이트에서 연구선 확대를 멈춘 결과다.

## 최종 성공 보존과 비용

finite incumbent가 시작 궤적과 동일했으므로,사전 계약에 따라562의 전체 피드백 선택 증거를 재사용하고 그 전체 명령 tape만 source로 독립 재전파했다.같은 정책 선택을 불필요하게 재실행하지 않았다.전체662raw가 정확히 일치했고 안전 finish13.219999999999807초를 확인했다.551 및562 대비 개선0ms다.비교 aperture를 다시 통과했다고 소급하지 않았다.

|범위|model틱|CPU초|wall초|
|---|---:|---:|---:|
|원 prefix|136|1.407390|1.426084|
|seed180+FD40×180+제안2×132|7,644|91.762850|91.803381|
|전체 독립 검증|662|10.090940|10.198212|
|실행기 전체(phase 밖 처리 포함)|**8,442**|**103.543072**|**103.743164**|

명시 힘33,768회·적분 내부 힘33,768회,geometry8,442회,body검사8,442회다.전체 source body 최고96.932332m/s<100이며 모든 사전 상한 안이다.이 실행기의 전체 CPU/wall은 생성자에서 계약/입력을 준비한 뒤부터 마지막 비용 저장 직전까지다.편집·초기 로딩·Git까지 포함한 작업 총비용으로 주장하지 않는다.560의 기존 비용 계측 공백도 이번 기록으로 메웠다고 주장하지 않는다.

읽기 전용 감사20항목이 source/입력 해시·등록·prefix/seed 정확성·실제 게이트 실패·최종 replay·비용·보존을 확인했다.감사는 model/force/geometry0이며 자체 CPU/wall은 audit JSON에 따로 있다.실행되지 않은 피드백/수락 검사의 조건부 감사 항목은 적용 대상0건임을 `scope_counts`/`not_exercised`로 명시했다.

실제 행동/reset/world·새seed·HOLDOUT/SEALED·예비·다른 환경·유료 자원 사용은 모두0이다.연구 잔여22,758·예비84,000을 유지했다.원시 상태·명령·FD·tape는 저장소 밖 비공개 디렉터리에 두었다.main 지정 커밋·Participants·기존 실패·백업·사용자 변경을 보존했다.

다음 설계에서 풀어야 할 장애물은 현재 rank 분기의 유한 이동에서 나타나는 clipping mode 변화와 힘 경계다.실제 피드백 회복 비용을 평가하려면 먼저 이 전역 게이트를 통과하는 제안이 필요하다.이번563에서 새 반경 탐색·분기 확장·추가 실험은 하지 않는다.

[사전계약](continuation563_contract.json) · [실행기](continuation563_model.py) · [결과](continuation563_result.json) · [비용](continuation563_cost.json) · [읽기 전용 감사](continuation563_audit.py) · [감사 결과](continuation563_audit.json)
