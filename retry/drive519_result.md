# 519 — 가속 참조가 큰 활성 구간이지만, 한 수정의 물리 모델 이득은0.32초

**새 native action/reset/world0.** 실제518 full trace를 분해한 뒤, 상수 forward25만 source rear/power 기반 forward 규칙으로 바꾼 한 후보를 시험했다. 모델은 안전하게 finish를 추정했지만20.70→20.38초,0.32초 이득으로 사전0.50초 기준에 미달했다. carry 추가 시험·실제 재검증을 제안하지 않는다. 원래 실제 기록은20.70초 그대로다.

## 실제 시간·저속·힘 분해

[분석 계약](audit519_contract.json) · [읽기 전용 분석](audit519_trace.py) · [12구간/zone/활성도 집계](audit519_result.json) · [관측 경계 대조](audit519_sampling.json).

공식 finish 이후 confirmation raw는 시간 합계에서 제외했다.12개 참조 arc bin 경계는20ms 사이 선형 배분이며 공식 구간 타이밍보다 높은 정밀도를 주장하지 않는다. 아래 활성도는 reference squared-speed segment의 기울기/상한으로 분류한 배타적 label이며 시간 손실의 인과 분해가 아니다.

|100의 실제 구간 label|시간|40m/s 미만(post)|gas/brake 시간|평균 source 복합 힘 비율|
|---|---:|---:|---:|---:|
|고정 출발|1.92s|1.18s|1.92 /0s|0.590|
|forward25|10.22s|2.24s|10.04 /0.18s|0.480|
|backward45|5.44s|0.94s|0.16 /5.28s|0.266|
|곡률/전이|2.68s|1.98s|2.04 /0.64s|0.415|
|top80|0.44s|0s|0.06 /0.38s|0.059|

저속6.34초를 기하 zone으로 보면 고정 출발1.18초, 코너4.02초, 진입20m0.68초, 탈출20m0.46초다. 실측75m/s 이상 시간0.78초와 reference top80 활성0.44초도 서로 다른 지표다. 따라서 높은 속도에서 보낸 시간이 짧은 것은 단순 top80 포화만으로 설명되지 않는다. 이 관측만으로 top80 변경의 효과 상한을 정하지도 않는다. pre-force 속도 기준의 저속 시간은6.36초이며 기존6.34초는 post20ms 기준이다. 두 값의0.02초 차이를 원본 오류나 새로운 손실로 취급하지 않았다.

actual100 경로 COM chord 합987.93m와 참조 path995.45m는 다른 측정이다.12개 bin 시간은1.21–2.26초 범위이고, bin5/9/11/12 등 중저속·코너 구간이 크다. 장애물 포함 전체 sampled 여유와 실제 source force/clipping도 함께 집계했으며, 주행 clipping0을 모든 가속의 충분한 여유 증명으로 바꾸지 않는다.

scalar 참조 clock은80에서22.17454초,100에서20.96114초다. 실제는각21.94/20.70초로 오히려 clock보다 빠르다. 경로/참조/추종 차이가 있으므로 **clock은 실현 가능한 최적 하한도, actual−clock은 회수 가능한 제어 손실도 아니다.**

## 과거13.640초와 비교해 확인할 수 있는 범위

499 공개 분석의 canonical line은842.884m, 현재 참조는995.445m다. 둘 다 공식 트랙 길이가 아니며 같은 track/state identity는 확인되지 않았다. 유실 raw 복구·보호 평가·이전 연구 실행은 하지 않았다.

읽기 전용으로 확인한 [258 경로 코드](racing258_plan.py)는16계수 spline offset을 고정 예산으로 최적화하고 top100·source/power 기반 forward·brake91.1687를 사용한다. [268 pace 코드](pace268_profile.py)는 약1.5배의 속도 pace를 다루고, [417 실행기](executor397.py)는 frozen line/node와 gain1.5를 사용한다. 현재는 Gaussian 장애물 우회 경로, top80/forward25/backward45/gain2다. 단,472의 늦은 P4는 별도 projected nodes를 사용했으므로 이 코드 기본값을13.640초 실행의 모든 실제 node 값으로 단정하지 않는다.

경로 설계·제어 제한이 훨씬 공격적인 공개 코드 구조와 서로 다른 canonical 길이는 확인된다. 그러나 현재와 과거의6초 이상 차이를 트랙/경로/제어로 수치 배분할 동일 조건 증거는 없다. 예를 들어258 공개 예시 path는1142m여서499의842m와도 같지 않다. 더 빠른 옛 기록의 모든 원인을 복원했다고 주장하지 않는다.

## 선택한 한 수정과 모델 반증

[사전 모델 계약](drive519_contract.json) · [후보](drive519_control.py) · [순수 검사](test_drive519.py) · [모델 실행](drive519_model.py) · [결과](drive519_model_result.json).

forward25 활성10.22초와 source/power 방식의 구조 차이를 근거로, 해당 forward bound만 `min(35.01888,80000/(29.24979×(node_v+2.7)))`로 바꿨다. first-lap launch envelope도 같은 forward 규칙으로 일관되게 계산하되 실제 첫24고정gas0.32는 유지한다. 경로·lateral100·top80·backward45·steering·gain·pedal map은 바꾸지 않았다. 단순 lateral-budget 반복 탐색이 아니다. 이 node 공식은 source 기반 steady convention이며 gas ramp/복합 tyre 응답의 exact 한계가 아니다.

기존518 cold100 모델1036ticks는 SHA/정책/경로 동일성을 확인해 재사용했다. 새 cold 후보가 전체 안전·모델 source-style finish 및0.50초 이득을 통과할 때만, 가장 긴 forward25 구간1.70초의 시작 action47 실제 저장 상태에서 같은 두 법칙을 비교하기로 했다. 안전 기준은518의 margin0.50m/path3m/주행 참조오차5m/s/force1.25·clipping10%와 source-style finish를 유지했다. 이 단계는 결과와 관계없이 native0이다.

새 모델은283/283 방문, finish 추정20.38초, 최소 여유0.979789m, path error1.203440m, 참조 초과4.317375m/s, 주행 force peak0.934112/clipping0으로 안전 gate를 통과했다. 그러나 이득0.32초<0.50초여서 **실질 효과 미달**, carry는0회로 조기 종료했다. scalar clock은20.96114→19.84840초로1.11274초 줄었지만 이를 실제 gain으로 쓰지 않았다. 한 고정 후보의 제한된 결과이며 forward 계획 방법군을 기각하지 않는다.

## 왜 참조 clock 이득이 그대로 실현되지 않았는가

[저장 진단 코드](drive519_diagnose.py) · [진단](drive519_diagnosis.json).새 trajectory/후보/native 없이 저장된 hold의 명령 포화와 실현 속도 차분만 확인했다.

새 후보는 mapped acceleration 상한35.01888에8.32초 머물렀다(기존 모델0초). 양의 feedforward·gas 구간의 평균 참조속도 부족은1.44→3.25m/s, 평균 실현 가속은23.25→28.31m/s²였다. 이때 평균 gas는0.466→0.580이고 full gas 시간은양쪽0이다. **conventional 가속 명령 ceiling 포화와 실제 gas/타이어 포화는 다르다.** 참조가 더 빨라지자 같은 pedal map의 ceiling 때문에 feedback 보정 여유가 줄어든다는 기계적 근거다. 별도 인과 ablation을 하지 않았으므로 이것만을 유일 원인으로 단정하지 않는다.

현재 후보는 native 재검증 대상으로 올리지 않는다. 다음 검토 가치가 있는 것은 가속 실행층을 실제 단기 응답과 맞추는 문제다. 이것은 이번에 시도하지 않은 별도 수정이며, 참조만 더 공격적으로 바꾸거나 상한을 계속 올리는 대체안으로 실행하지 않았다.

## 비용·보존

[검증/비용 집계](drive519_summary.json).실제 두 full trace 분석·sampling 경계 대조·저장 진단의 적분0, 새 후보 모델1020ticks/4080wheel force 평가를 사용했다. 기존1036model ticks는 재사용이며 새 비용으로 중복 계산하지 않았다. pure1test는 closed forward/backward 제약과 다른 필드 불변을 검사했고 새 integrator step0이다.

worker 합계CPU15.751068초/wall15.755138초, 준비/publication allowance3CPU/3wall를 별도로 표시했다. 분석60CPU/90wall·모델180CPU/240wall·전체300CPU/420wall 안이다. native action/reset/world0, 연구 **24938**, 예비 **84000/used0** 불변이다. private11files/5,647,436B로96MiB/512files 이하이고 원시 입력·명령은 비공개다. 연결 중단 알림 뒤 기존 결과/source/input SHA를 확인해 완료된 모델을 중복 실행하지 않았다.

main·Participants·사용자 변경·백업·기존518 기록을 보존했고 지정 cloud·단일 작업·승인 종료2026-10-20 19:01:55 KST를 유지한다. 새 seed·보호 평가 조회·옛 연구 실행·유료 자원0이다.
