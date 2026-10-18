# 534 — 고정533 경로의 물리 모델 진단: 두 위험 짝 통과, cold 차체 여유 미달

**533의 마지막 경로를 한 글자도 바꾸지 않고 기존528 controller로 진단했다. 두 위험 root 짝은 안전했지만 cold가13.20초/165번째 hold의4번째raw에서 좌후륜 도로 여유0.437175m<모델0.50m로 중단됐다.** 완주·시간 개선을 확인하지 못했으며 carry/native는0이다.533의 수렴 실패는그대로 미승격이며534 진단과구분한다. 실제 검증 기록18.40초,연구24155·예비84000/used0 유지.

[새 계약](frozen534_contract.json) · [projection 보정](frozen534_projection.py) · [독립 초기화 확인](frozen534_projection_check.json) · [모델 실행](frozen534_model.py) · [원결과](frozen534_model_result.json) · [중단 자세 감사](frozen534_audit.json).

## 별도 진단 계약과 입력 고정

이번 질문은 “최적성 미수렴인 **이 정확한 경로+고정528 controller**가 모델상 안전하고 빠르게 완주하는가”였다. 추가 경로 최적화·다른 iterate 선택0이다.533 마지막 frozen-paths 파일을byte-identical로 복사하고 SHA `98b3eaf4eb335d95a588de33921d54c36ef4e1c2266d648980e6b52c114114d3`를534 입력으로 등록했다. 기존533의 표본기하/독립oracle 최소1.252015m·기존profile 재생성scalar14.407176초·설계speed 보수성을 SHA 동일성 아래 읽기 재사용했다. 수렴 통과로 수정하지 않았으며 최적성/전역 최적성/실제 gain을 주장하지 않는다.

기존528 source-response controller·조향·top80/back80/corner153/source-drive forward를 고정했고,backup100/top80/back45도 같은 후보 경로에 고정됐다. 새 정책·speed해 배포·gain 변경·여유 완화·새 seed는 없다. 실제 baseline 비교가 있었다면525 실제 policy와534 package 짝이며,528과의 경로-only 모델 차이와 구분한다.

기존 draft의 late-root signed projection 문제는534 helper로 독립 등록했다. 등록된 첫lap의 완료 이력에서 `completed>0`이고 초기 own-path s<0이면L을 더하고,cold signed seam과이후 연속 projection은 그대로 둔다. 위험 root baseline 저장 progress와초기오차0m,복구 참조63.877932/73.428023m/s를 확인했다. 실제 propagation 뒤에도 baseline 두 창 **192/192raw의 root state가 기존528 cache와 정확히 일치**해 baseline 재현을 확인했다. 미래 actual trace를 제어 입력으로 쓰지 않았다. 준비 단계의path연산 괄호오류는등록 전에 수정했으며 모델/force0이었다.

## 예산·중단·승격 순서

모델은 CPU360초/wall480초,적분120000ticks·별도 force oracle600000회,원래두위험root 각24hold/96raw의baseline/candidate짝 최대384execution ticks를 사전 고정했다. 모든 위험 짝 안전 시에만 cold,그 cold가전안전/source-style finish·525실제18.40대비모델≥0.50초·528cold모델대비≥0.10초/HIGH≥50%를 통과해야 carry였다. 동일actual518 before47 root의 fresh528 carry와후보carry도안전/finish 및각각525대비≥0.50초/528대비≥0.10초가필요했다. 전체통과시만native1000actions/2resets/2worlds/4102raw 한짝을 허용했다.

0.19불확실성/예측force1.06/물리1.25,참조초과5(528 내부4.85),tracking 누적clipping10%,geometry 모델0.50/native0.25m,path3m,launch24gas.32/peak2.5/clip15%,body<100/sourceTimeLimit/finish/관측·손상/one-hold prediction/source-force oracle/COM impulse gate는 유지했다. 실제wrapper attempt 사전 차감·finally close/body/joint0 정리도계약했고 실제world 생성0이다. 첫 위반에중단하며 rescue나추가후보는없다.

## 사전선택 두 위험 root: 모두 통과

|후보의96raw 창|장애물 진입|큰 곡률 진입|
|---|---:|---:|
|최소전체 hull/wheel 여유|1.086840m|0.839017m|
|최대추종거리|1.009755m|1.310613m|
|최대참조속도 초과|0.708666m/s|0m/s|
|running force peak|1.047751|1.049075|
|HIGH/RESPONSE|23/1|23/1|

같은 root에서 baseline528도각96raw를 안전완료했다. 위험 창은안전 선행 gate였으며 국소 시간 개선은요구하지 않았다. 경로별 end_progress는서로다른 arc 좌표이므로 차이를그대로 물리 진행 이득으로 보고하지 않았다.

## Cold 실패: force 기준을 통과해도 footprint 여유는 유지되지 않음

cold는660execution raw/165holds,모델시간13.20초에서 `MARGIN`으로 멈췄고 source-style finish는없었다. running force peak1.059686≤1.06,clip9/2256(0.399%)≤10%,최대참조초과3.708298≤5m/s,최대추종거리1.421656≤3m였다. launch peak2.255467≤2.5,clip46/384(11.98%)≤15%,최대COM79.893561m/s·body81.632675m/s<100도통과했다. **carry/native 승격은없고 시간 gain은null**이다.13.20초나14.407초scalar를완주 기록으로외삽하지 않는다.

저장 중단 자세의 읽기 전용 감사는 제한부위를 **세번째 바퀴(좌후륜)의 도로 여유0.437175m**로 확인했다. 해당바퀴 장애물 여유는31.477m로장애물이제한한것은아니다. 차체는아직 도로 안에있었으며 이결과를 실제충돌/실제도로이탈이라고부르지않는다.

중단시모델속도41.374383m/s,참조48.952395m/s,중심추종거리1.250157m,tangent대비heading차이−0.120377rad(약−6.90도)였다. 같은projection위치의 nominal 외곽직사각형 도로여유는1.608604m였지만,추종중인모델차체/바퀴자세의여유는0.437175m였다. 직전hold끝→실패시점에중심추종거리는1.421656→1.250157m로줄었는데여유는0.670754→0.437175m로줄어,중심거리만으로footprint안전을보장할수없음을보여준다. 자세/위치오차의동적효과를정량분해하거나새controller의효과를검증한것은아니다.

마지막action은 `RESPONSE`였고선택된최종12hold재인증 force peak1.059999997로통과했다. 시도후기각된HIGH의1.061571은배포action의인증값이아니다. 공유528의forecast는force/참조/path-distance를검사하지만전체footprint margin을검사하지않는다. 이번고정조합에서정적경로여유1.25m가실행중모델footprint여유0.50m를보장하지않는것을확인했다. 모든경로/추종기군의불가능성이나실제native실패로일반화하지않는다.

## 판단·비용·보존

534의답은 **두국소창은통과했지만전체cold의기하안전gate는실패했고,빠른완주의증거는없다**이다.남은연구문제는고정추종기의위치/heading과전체footprint를반영한안전여유다. 이번에는경로·controller·여유를수정하거나실패root에서재시도하지않았다.533수렴미완료와534모델반증을각각보존했다.

새적분 **19958ticks=384위험창execution+660coldexecution+18914forecast**다. 적분내source wheel force79832회,별도explicit force80780회,forecast577회다. 새경로최적화0,native action/reset/world0,연구24155·예비84000/used0 유지.

projection읽기CPU0.008128초/wall0.008127초,모델34.586170/34.591763초,읽기감사0.167760/0.168798초로합계 **새worker CPU34.762058초/wall34.768688초**다. 준비·소스확인·단순집계명확화·publication allowance3CPU/3wall는별도다. 원533 비용을다시차감하거나534와혼동하지않았다. 단일MODEL_STARTED/원중단trace와명령은비공개보존했다.

source/input SHA·528controller 함수동일성·고정533경로SHA·baseline 재현을검증했다. 공개물은코드/계약/집계뿐이며 지도·좌표·root·raw 궤적/명령·seed/RNG/case는비공개다. 지정cloud 단일작업/기존DEV만사용했고 HOLDOUT/SEALED·새seed·보호평가·별도유료자원0이다. main 지정SHA·Participants·사용자변경·기존백업·530~533 원실패를보존한다. 승인종료2026-10-20 19:01:55KST를자동연장하지않는다.
