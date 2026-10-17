# 448 — known DEV native +60m transfer

**같은 known DEV pre23 root에서 첫 fullgas 한 번 뒤 own nominal을 사용한 native arm이 공통+60m를 [1.22,1.24]초에 통과했다.** nominal은 [1.58,1.60]초로, native 국소 이득은 **[0.34,0.38]초**다.447 live 모델의 crossing 구간과 일치했다. 두 arm의 native 사실과 현재 입력 검증이 모두 유효하며, 전체 lap·픽셀 정책·새 조건 일반화 개선으로 합산하지 않는다.

## 사전 계약과 선행 게이트

명시적448 지시에 따라 두 arm·각22행동 prefix·root 이후 최대26행동·+60m 경계·첫 pulse만을 고정했다. 사전 계획과 source/code hash, 기존 실제 권위 경계, 원장v467·권한·보호 파일·main 기준을 동결했다. 실제96 wrapper/reset2, 모델 planned5624/hard6144 ticks·128 worlds, model CPU180초/wall300초, actual exclusive CPU90초/wall180초, worker 순차1 상한이다. 최초 source/fidelity/ledger/memory/RNG/안전/진행/반복/기술/자원/기한 오류에서 전체 중단하며 pulse·경계·허용 오차 조정과 실험 재시도는 없다.

모델/실제 적분 전 정적 fixture 최초203개 시도에서 상한 테스트가 실제 함수를 대역으로 우회한 오류를 발견했다. 원본 source·plan·실패·로그를 비공개 pre-model-v1에 보존했다. 실제 상한 함수를 호출하도록 fixture 연결을 고치고 memory 음성 fixture도 존재하는 C.s 필드를 쓰도록 수정했다. 실행 정책·허용 오차·상한은 그대로이며 **정적207개 통과** 후에만 worker를 한 번 시작했다. 이는 적분 전 fixture 수정이며 실험 실행 실패를 재시도한 것이 아니다.

실제 reset 전 SourceG1은 **216 ticks/6 worlds**로 완료했다. 원래444 before-constructor/current input의 state·memory·actual ledger·global RNG를 써서 nominal/fullgas의 H13 독립2회와 held 첫 전이1회씩을 재검증했다. 두 branch 모두 원래 H13 rows/state/memory와 정확히 같았다. nominal은 실제442/439의13행동 source gate와 fresh-current 첫 전이 비교를 통과했고, counterfactual은 이 단계에서 actual-qualified로 표시하지 않았다. held state/memory/RNG 보존·명령·첫 전이·독립 반복을 확인했다.

## 실제 실행과 사실 경계

known condition과 기존 setup RNG를 그대로 썼으며 새 seed나 split을 고르지 않았다. 각 native prefix22행동은 자기 charged ticket의 실제 사실을 먼저 commit하고 실제442 pre/post·memory·nominal·command·raw 기록 및 기존417 source fidelity에 대조했다. 각 pre23의 전체 physical/wrapper/observation/RNG/nominal 이전 controller root는 원래442와 정확히 같았고, 후보는 완료된 baseline과도 정확히 같았다. baseline native 성공 후에만 candidate arm을 시작했다.

root 이후에는 **매 실제 명령마다 현재 실제 입력**에서 독립 model2개를 새로 만들었다. first recipe는 candidate pre23에서만 fullgas이며 나머지는 own nominal이다. 모델 guard는 최대H13 또는 공통+60m의 첫 crossing을 포함하는 wrapper까지이며, 물리 안전·진행/기한·정확 반복·현재 nominal/memory·원래 actual parent state/RNG/ledger 보존을 검사했다. 유한 guard를 finish ranking 증거나 실제 DONE 권위로 쓰지 않았다. prefix는 고정된 사실 재현이며 이 fresh query 수에 포함하지 않는다.

| arm | prefix/이후 행동 | 실제 행동 | 검증된 current 전이 | +60m raw tick bracket | 시간 bracket |
|---|---:|---:|---:|---:|---:|
|nominal|22/20|42|20|79–80|1.58–1.60초|
|첫 fullgas 후 nominal|22/16|38|16|61–62|1.22–1.24초|

양쪽 모두 `NATIVE_EXIT60_VERIFIED`, 오류 없음이다.80개 실제 호출 모두 성공한 native dispatch·clock·사실 기록이 있고 미확정 행동은0이다. root 이후36개 current 전이 모두 기존439의 실제 관측 유래 ledger, fresh-current memory/input, 기하 유도 progress/goal 비교 구간, 정확 goal-side/age/clock/deadline/DONE 및 body/wheel/raw hull 검사를 통과했다. **native 사실 commit 뒤 forecast를 비교**하는 경계를 유지했고 모델 값을 실제 사실로 commit하지 않았다. clipping 불일치는0이다. 진행량 모델/실제 차이 최대는 nominal4.7541e-7m, candidate7.1345e-7m였다. 이는 관측한 현재 전이의 검증이며 모든 미래 상태의 사전 보장으로 확대하지 않는다.

nominal80rawticks·candidate64rawticks가 root 이후 실행됐으며 crossing은 각각 그 내부79–80/61–62 구간이다. native 시계를 직접 관측했으므로 미래 모델 시계를 대신 쓰거나 마지막 wrapper 전체 시간을 crossing으로 반올림하지 않았다. 공식 lap finish를 수행·추정하지 않았다. baseline42개의 native rows는 기존442 C0의 처음42개와 정확히 같았다.

## 공통 경계에 남은 terminal debt

| native +60m 양끝 body 표본 범위 | nominal | candidate |
|---|---:|---:|
|속력 m/s|56.1136–56.7673|61.8972–62.5680|
|yaw rad/s|−0.03799–−0.01159|−0.19583–−0.00756|
|path error m|0.00418–0.02797|0.14832–0.19560|
|절대 heading error rad|0.02170–0.02193|0.03909–0.03924|

lower crossing의 동일 preclip phase에서 wheel force ratio 최대는 nominal0.76805/candidate0.78114, lateral slip 범위는 −0.14061..0.06012/−0.36348..0.42255m/s였다. joint angle·omega·longitudinal slip 전체 범위도 [집계 JSON](transfer448_result.json)에 남겼다. upper body 표본과 lower preclip force를 혼동하지 않았고, 이 표본 범위를 연속시간 보장으로 표시하지 않았다.

국소 native transfer는 확인됐지만 candidate의 path/heading·yaw/slip 차이가 남아 **terminal debt 해소는 미판정**이다. 더 높은 속력 자체를 debt로 규정하거나 모든 상태 일치를 요구하지 않는다. 이번 범위의 이득이 이후 제동·코너에서도 남는지, 또는 이후 비용으로 소모되는지는 별도 가설이다.447/446의 같은 pulse 모델 이득이나442의 전체 lap1.32초와 더하지 않는다.

## 비용·종료·다음 최소 가설

실사용은 **실제80 wrapper/reset2**, raw action320 + reset102 = **422 native ticks**다. 모델은 **2712 ticks/78 worlds**: source216/6, baseline fresh guards1456/40, candidate fresh guards1040/32다.72개의 current model stream과6 source stream의 observer posts2712가 reserved2712와 일치했다. 실제/main·모델 단위는 다르며 과거 비용을 재청구·환급하지 않았다.

| worker exclusive 비용 | CPU초 | wall초 |
|---|---:|---:|
|actual|35.2023|35.6065|
|model|65.9476|66.4111|
|whole worker|101.2459|102.1111|

actual에는 reset·제어·snapshot·native 물리/observer·사실 commit·forecast 비교·IO가 포함되며 model region은 제외한다. model에는 source/fresh-query 생성·복원·물리/observer·검사·receipt/IO·cleanup이 포함된다. 순수 solver 비용이나 모든 프로젝트 overhead의 완전 계측은 아니다. 별도 정적 두 시도 CPU15.2719/17.5683초, 저장 감사 약2.93초이며 추가 적분은 없다. hard/planned 비용·시간·횟수 상한을 모두 지켰다.

마지막 checkpoint는 **2026-10-17 16:16:29 KST**이며 새로운 실행·예약 없이 종료했다. v468은 실제80만 차감해 연구 잔여 **27,436**, 누적 실제 **1,320,628**, 예비 **84,000/사용0**이다. HOLDOUT/SEALED·학습·새 seed·추가 유료 자원은0이다. 유효 종료 **2026년10월20일19:01:55 KST**와 main dfb7a2de2178825ca5c5ce20bab01ba67052ba31·Participants·보호 ZIP·사용자 변경·backup을 유지했다. raw 상태·seed·명령·RNG·비공개 승인 자료는 공개하지 않았다.

다음 최소 검증안은 **관측된 native +60m 이후 다음30m에서 이득이 남는지**를 묻는 bounded model-only 비교다. 두 native wrapper-end root를 복원해 own nominal만 원래 root+90m까지 최대13행동, 독립2회와 held1회/branch로 제안한다. nominal native448 최종 전체 상태는 기존442 pre43과 정확히 같음을 저장 자료에서 확인했으므로 baseline의 다음 factual 기록을 source gate에 재사용할 수 있다. baseline gate를 통과한 뒤 candidate를 여는 순서를 유지한다. source/contrast 재사용을 한 번만 청구하면 worst **216 ticks/6 worlds**, hard256/8·CPU60초/wall120초·actual0이다. native wrapper-end 시각 차이와 +60m wrapper 잔여를 정확히 계산하고 closed-native solver warm-start 복원 한계를 표시한다. 도달 실패·겹침·음수 효과도 그대로 남긴다. 이는 native +90m나 terminal debt 전체 해소의 증명이 아니다. [다음 설계](next448_design.json)는 **제안만 했고 실행·예약하지 않았다.**

[실행/동결](transfer448.py) · [native 경계](native448.py) · [fresh-current guard](query448.py) · [SourceG1](qualify448.py) · [상한/비용](meter448.py) · [정적 fixture](test_transfer448.py) · [저장 감사](analyze448.py).
