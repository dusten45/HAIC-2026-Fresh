# 517 — 다음 코너까지 확장한 실제 동일 window에서도100 후보 이득 유지

**확장 전체 공통 window는6.167568→5.853378초로0.314190초 빨랐고,20ms bracket의 이득 하한0.280000초로 사전0.08초 gate를 통과했다.** 다음 코너 window 자체도0.128499초 빨라 후속 손실은 관측되지 않았다.516의0.149초에 suffix를 더한 계산이 아니라 새 begin/end 공간 사건으로 전체 구간을 직접 측정한 결과다. 공식 finish·전체 랩·11초대·13.640초 개선을 뜻하지 않는다.

## 복구 확인과 변경 범위

작업 시작 시 workspace는516 원격 commit `821f7edcc052bdc0e20f57dbf19b8336f6f4fe1f`에서 clean이었다.515/516 private 입력·118charge receipts가 존재했고516 native 계약의 source/input SHA가 일치했다. 연결 중단 때문에 완료된 실험을 재실행하거나 저장소를 초기화하지 않았다.

[사전 계약](speed517_contract.json) · [경로 연장](speed517_control.py) · [순수 검사](test_speed517.py).80/100 lateral budget 외에 새 gain·상한·필터는 도입하지 않았다. 기존100개 경로점과 arc를 exact 보존하고 같은 장애물 offset3.8m/폭16m 규칙으로150개 점까지 이어 붙였다. 연장부의 곡률·backward45/forward25 속도 pass는 동일 규칙으로 다시 계산했으며 기존 window의 속도 node도 exact였다. 직선/곡선 steering 함수와 pedal 변환은 그대로다. 미래 경로의 정보가 늘어난 연장이며 이전 endpoint 이후의 안전성을 가정하지 않았다.

전체 window는 기존 시작 arc99.031845m부터 다음 코너 종료40m 후 arc399.645235m까지다. 별도 downstream window는 다음 코너20m 전 arc311.945660m부터 같은 종료점까지이며 코너 진입/종료는331.945660/359.645235m다. 이는 고정 참조 경로의 arc 좌표이지 공식 트랙 거리/완주 판정이 아니다.

## 모델에서 먼저 반증한 것

[모델 실행](speed517_model.py) · [모델 결과](speed517_model_result.json).cold exact reset80/100 전체 궤적과,516 실제 wrapper-return 상태에서 각자 이어가는80/100 carry stress를 검사했다. carry 출발점·상태는 정책 결과로 서로 다르므로 whole time을 비교하지 않고 공통 downstream 사건 사이만 비교했다. 후보의 미래 입력에는 지도·현재 상태·자기 예측만 있고 실제 미래 관측은 없다.

네 모델 모두 full hull/wheel 도로·장애물 여유≥0.50m, 경로 오차≤3m, 참조 초과≤5m/s, force ratio≤1.25, clipping≤10%를 통과했다. 진행 projection jump도 perraw `[-0.5m,max(5m,2×COM이동거리)]` 안이어야 했고 통과했다. 이는 제어 gain 변경이 아닌 공간 사건의 유효성 검사다.

cold 전체 이득은0.314091초, downstream 이득은cold0.128573초·실제 carry0.128524초였다. 다음 진입 속도는약40.21→44.66m/s로 달라졌지만 후보 자체의 추종·힘·여유가 기준 안이었다. cold 초기 궤적의 이전51680/100 모델472행은 상태·명령 exact였다. 원 계약 설명의 `384+candidate232`는 행수 문구 오기이며 실제 gate 코드는240+232행 전체를 비교했다. [native 계약](speed517_native_contract.json)에 이 설명만 바로잡았고 기준/코드/모델 적분은 바꾸지 않았다.

네 안전 gate, cold 전체 이득≥0.08초, cold/carry downstream 시간 비악화를 모두 확인한 뒤에만 native로 진행했다. 모델이 solver warm-start나 모든 상태의 안전성을 복원/증명한 것은 아니다.

## 실제 전체 구간과 다음 코너 결과

[실행](speed517_native.py) · [실제 집계](speed517_native_result.json) · [전수 검증](speed517_summary.json).

같은 DEV를 새로 reset해80을 먼저 검증하고100을 실행했다. exact515 initial model/RNG/pixel와 두 reset 입력이 일치했고 첫24action·관측이 exact였다. 연장 주행에 포함된 이전516의118개 native action/관측/전후 모델 상태 기록도 모두 exact였다. 이는 전체 연장 실험 안의 재현 증거이며 별도 첫 구간 성과를 추가 합산하지 않았다.

| 실제 동일 공간 구간 |80|100|80−100 이득|
|---|---:|---:|---:|
| 전체 확장 window |6.167568s|5.853378s|0.314190s|
| 전체 duration bracket |[6.16,6.20]s|[5.84,5.88]s|하한0.28s|
| 다음 코너 window |2.196979s|2.068479s|0.128499s|
| 다음 duration bracket |[2.18,2.22]s|[2.06,2.10]s|하한 약0.08s|

downstream 이득을 전체 이득에 더하지 않는다. 두 arm 모두 전체 end를 통과해 불완전 prefix나 다른 길이의 종료를 비교하지 않았다.

| 다음 코너 상태·국소 안전 지표 |80|100|
|---|---:|---:|
| entry 보간 속력 |40.208415m/s|44.658456m/s|
| entry 포함 raw의 path error |0.658852m|0.743389m|
| entry 포함 raw의 yaw |−1.056269rad/s|−0.996874rad/s|
| entry 포함 raw의 heading error |0.041750rad|0.029403rad|
| corner exit 보간 속력 |30.165807m/s|31.400712m/s|
| downstream 최소 raw 여유 |1.240274m|1.198923m|
| downstream force ratio 최대 |0.797901|0.796093|
| downstream clipped wheel samples |0/440|0/416|

entry 속력은 사건 보간값이고 path/yaw/heading은 그 사건을 포함하는20ms raw 종료 관측이다. exact 동일 시각의 전 상태로 확대하지 않는다. 더 높은 진입 속도가 이번 다음 구간의 시간 손실이나 등록 범위 밖 위험으로 이어지지는 않았다.

전체 최소 여유는80에서0.989558m,100에서0.951831m로 첫 구간이 여전히 가장 좁았다. 전체 source force 최대는0.797901/0.900122, clipping0이었다.958raw행의 source 센서/효과/payload/마찰·관측·안전·projection 오류는0이다. source force oracle 최대 차이0.000209N, COM impulse 잔차0.0000209m/s였다. 후보 전체 한-hold 예측 최대 오차는 위치0.001227m/속도0.011402m/s/방향0.000535rad/yaw0.011450rad/s로 사전0.10/0.15/0.02/0.05 기준 안이었다. downstream 속도 예측 오차 최대도0.005460m/s였다.

## 판단·비용·보존

budget100의 국소 승격 범위를 **이 고정 경로의 첫 두 곡률 구간과 연결 구간**까지 확장한다. 독립 DEV/보호 평가/전체 랩 자격이나 무제한 트랙 적용은 아니다. 다음 검토는 같은 후보와 경로 규칙을 다음 미검증 구간으로 확장하는 모델 qualification이며, 이득을 코너 수만큼 곱하거나 최종 기록에서 빼지 않는다. 이번 잔여 상한으로 추가 주행·튜닝하지 않았다.

실제 **214actions/2resets/958rawticks=reset102+action856**, 모든 실제 호출 전charge214개와 전체4tick 완료를 전수 확인했다.2world 모두 body/joint0으로 닫혔다. 연구 **25686→25472**, 예비84000/used0이다.600actions/2resets/2502rawticks 상한 이내다.

모델 integrator **2096ticks=사전1240+native 예측856**, 별도 모델 wheel force 평가8384회다. pure1test는 새로운 integrator step0이다. 모델/native worker CPU37.824057초/wall37.838591초이며 준비·publication allowance2CPU/2wall를 별도로 표시한다. 전체360CPU/480wall/200000model ticks 안이고 계측 trace/observer 비용을 포함한다. 대화 전체 시간을 완전히 계측한 값은 아니다.

private1404files/11,470,982B로96MiB/4096files 이하이며 raw/state/지도/명령은 비공개다.214개 own-state 명령,958raw,precharge,source/input SHA를 대조했다. 과학 재실행·새 seed·보호 평가 조회·유료 자원0이다. 기존 main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·사용자 변경·백업·516 결과는 보존했다. 지정 cloud·단일 작업과 승인 종료2026-10-20 19:01:55 KST를 유지한다.
