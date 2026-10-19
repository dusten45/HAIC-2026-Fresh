596 — 원537 feedback의 12hold 국소 통과, 완주·native 승격 없음

같은 actual raw156 checkpoint에서 원537 feedback을 hold40..51에 한 번 적용했다. **48raw 모두 strict 안전 기준을 통과했고 진행 거리 67.447284m를 얻었다.** 새 cold 정책은 577의 명령1..39 뒤40부터 원537 feedback을 계속 사용하는 별도 정책이다. 이번에 검증한 범위는 그중 12hold뿐이다. 이후 고정 tape로 되돌아가는 정책은 정의하지 않았다.

|동일 global raw204의 저장 비교|596 feedback|595 고정 명령|기존577 고정 source|
|---|---:|---:|---:|
|progress(m)|218.781214|219.105962|219.108333|
|COM speed(m/s)|86.401908|86.365628|86.365655|
|path error(m)|0.034775|3.011833|2.986114|
|path slack(m)|2.965225|−0.011833|0.013886|

비교는 기존595/577의 저장48row만 읽었고 다른 물리·force·geometry 계산은 하지 않았다. feedback의 종료 progress는595보다0.324748m 작고 speed는0.036280m/s 크다. 큰 path 여유 회복은 다음 전체 검증을 해볼 가치가 있는 **국소 feasibility 증거**다. 시간 이득·완주·native·carry·일반화·incumbent 승격 근거는 아니다. 고정 명령과 추종 정책의 여러 제어 선택이 함께 달라지므로 특정 steer/pedal 하나의 인과 효과로도 분리하지 않는다. 기존592/593/594 실패와595 진단은 그대로다.

실행 전 검증과 정책 보존

[동결 계약](feedback596_contract.json), [checkpoint gate](feedback596_checkpoint_gate.json), [순수 검사](feedback596_tests.json)를 source 시작 전에 기록했다. exact checkpoint SHA256은 `033b7c9b15e1e151a24897c26bd9aa046c4fbcd93bc2e65c629c0163e0f85590`다. 원537 정책 SHA256 `c5a3f3206979085150e8ecda4f96da4b76f74ff4e9064bc3f5b9e3eb8d62c771`,551 candidate/backup·reference·gains·원 유한 trial/FINAL·kernel200000 상한을 유지하고 이 실험의 더 작은 전역 비용 상한을 적용했다. 모델 입력은 exact actual raw156의 root/실제 이력/tracker/visited/clock/progress와 pin된 immutable roads다. native solver checkpoint를 복구했다는 주장은 없다.

순수 검사5개는 세계나 물리를 만들지 않는다. 원537 경계/복합 거절 순서, 독립 trial 이력, tick 전 힘 거절 계수, PATH/양방향 projection 분리, 합성 입력의 원 인증기와 수동 계측 summary 일치를 확인했다. 실제 실행에서는 매 chooser 전후 actual checkpoint hash가 같고,각 trial은 실제 tracking 이력에서 독립적으로 시작했다. **111개 원537 certificate summary가 수동 계측과 정확히 일치하고,선택된 새 FINAL의 첫4틱과 실제 적용48틱의 root·force·이력이 모두 일치했다.** 이 대조를 위해 별도 physics replay를 하지 않았다.

hold40..42는 각31certificate의 원 finite 탐색 후 SOURCE_RESPONSE를 선택했다. hold43..51은 각각 HIGH와 새 FINAL 두 certificate의 SOURCE_FULL이었다. 총111개 중66개는 안전 인증,43개는 FORCE_PEAK,2개는 CLIP_HISTORY 거절이었다. 내부 trial 거절은 원 정책의 정상 선택 과정이며 적용 실패나 새 정책 재시도가 아니다. 이 실행에서 forecast PATH/projection/footprint/reference 실패는 없었다. 거절 raw에는 tick 미실행,원인·ratio·누적 이력이 남고,완료 raw에는 footprint/reference/path/projection delta·양쪽 한계·분리 flags가 남는다.

|적용48raw 안전 집계|실측|기준|
|---|---:|---:|
|최소 footprint(m)|0.679156|≥0.50|
|최대 path error(m)|0.776362|≤3|
|최대 외부 force ratio|1.058441741|≤1.059|
|최대 실제 prefix clip|9.868421%|≤10%|
|종료 tracking 이력|31/432|실제 시작15/240에서 누적|
|최대 reference excess(m/s)|−0.468582|≤4.85|
|모든 forecast+적용 최대 body 속도(m/s)|86.440459|<100|

원537 forecast admission의 binary64 값1.0590000000000002와 실제 적용의 literal1.059는 각각 원 구현 그대로 유지했다. 적용은 원 late568 strict raw 순서와 tracker/visited/clock 갱신을 재사용했다. first no-safe-action/적용 strict/domain/기술/비용/기간 실패 즉시 중단 조건과 재시도 금지는 사전 고정했고,이번에는 실패 없이 선언한48raw에서 종료했다. 다음 continuation은 실행하지 않았다.

비용과 감사

|계수|실제|사전 상한|
|---|---:|---:|
|model 시도 /완료|3,276 /3,231|각18,480|
|적용 source 시도 /완료|48 /48|각48|
|forecast 시도 /완료|3,228 /3,183|위 model 총량에 포함|
|외부 /내부 wheel force|13,104 /12,924|각73,920|
|force 합계|26,028|147,840|
|geometry 전체|9,551|40,000|
|source CPU /wall(초)|39.774888 /44.880896|450 /600|
|준비·검사·등록·분석·감사 CPU /wall(초)|16.246869 /15.450113|30 /45|
|전체 CPU /wall(초)|56.021756 /60.331009|480 /645|

시도와 완료 차이45는 force/clip에서 tick 전에 거절된 forecast다. 새 FINAL·거절 trial·적용과 내부 wheel oracle까지 모두 포함했다. geometry9551은 preflight2+forecast footprint3294+forecast projection3183+내부 nominal/steering projection2976+적용 footprint/projection96이다. 기존595 제안의37346 최악 추정에는 내부 nominal/steering projection이 빠져 있었다. 실행 전에 이를 정정하고 cap40000은 유지했다. 다음 hold마다4526회를 보수적으로 예약했다. 최악12hold가 전부 이 상한에 들어간다고 가정하지 않았으며,부족하면 비용 중단하도록 했다.

[실측 결과](feedback596_result.json)와 [읽기 감사](feedback596_audit.json)를 보존했다. 감사23개는 입력/코드/runtime pin,16,585event journal chain,원summary/FINAL 일치,원시 계수와 비용·안전·이력·국소 범위·미승격을 확인해 모두 통과했다. 감사는 physics/force/geometry/native0이며 결과 생성 뒤의 감사1.230462CPU/1.230540wall과 보조2초를 합계에 별도 추가했다. 사전 읽기·순수 검사 등은 보수적10초 선차감과 실행 프로세스 측정에 포함했다. 문서/Git 대기를 물리 비용으로 주장하지 않는다.

native/world/reset/행동0,DEV만 사용하고 HOLDOUT/SEALED0,연구 잔액22,548·reserve84,000/사용0을 유지했다. 다른 환경·유료 자원·FD·solver·새 seed0이다. raw/checkpoint/commands/좌표·원문·journal은 지정 클라우드 Git 외부 비공개로 보존하고 공개는 기술 코드·hash·집계뿐이다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants와 기존 백업·사용자 변경을 유지했다.

기간 판정 정정과 다음 조치

앞선596 응답은 최초 승인 종료10월16일만 적용해 최신 사용자 연장/계속 진행 지시를 누락했다. 제공된 transcript evidence를 적용하여 **기존 승인 종료10월20일19:01:55KST/10:01:55UTC**로 정정했다. 자동 연장을 만든 것이 아니다. 기존 응답·결과는 삭제하지 않았다. 재개 전596 디렉터리/시작 표식/결과/프로세스가 없음을 확인하고 독점 생성 표식으로 중복 실행을 막았다. [정정 기록](feedback596_date_correction.json)에 기술적 경위를 남겼으며 개인 원문은 포함하지 않았다.

[다음 단일 제안](feedback596_next_proposal.json)은 이 새 cold 정책의 전체 source 완주 검증이다. 국소 pass와 큰 path 여유 회복 때문에 검증 가치가 있지만 원래 source 초기화에서의 전체 안전·종료·시간을 별도로 확인해야 한다. 전체 safe finish가 나올 때만 명령 tape 독립 재생 검증을 진행하는 별도 계약을 제안한다. 이 후속 실험은 source/native 모두0이고 자동 시작하지 않았다.
