590 단일 retiming·s400 유지 시험 — 안전 통과, 시간 개선 실패

결과는 **SAFE_S400_NOT_IMPROVED**다. 589의 정적 개선 형상 하나에 고정549식 retiming을 한 번 적용한 후보는 실제 source에서 s400 통과 hold 전체를 안전하게 완료했으나, 원577 기준보다 **29.068543ms 느렸다**. 양의 연속 시간 이득이라는 사전 승격 조건을 충족하지 못해 독립 initial replay는0회다. 추가 형상·offset·solver·cap 탐색이나 whole/native 실행으로 이어가지 않는다. 정적 길이·곡률 목적 개선이 이 고정 정책의 동적 시간 개선을 보장한다는 가설은 이번 한 후보에서 지지되지 않았다. 모든 형상이나 정책의 최적성·불가능성을 판정한 결과는 아니다.

계약·형상·관측 경계

[사전 계약](retime590_contract.json), [source 직전 고정 계약](retime590_source_contract.json), [실측 결과](retime590_result.json), [읽기 전용 감사](retime590_audit.json)를 보존했다. 선택된 형상 SHA256은 `1949cafe137cf06d16c25e354ed306bac393c40c838cc124d838b49a6e88f9b3`다. 588 실패를 구제하거나 이전 실행을 중복하지 않았다. 승인 종료는 보존된 후속 정정 기록에 따른 2026-10-20 19:01:55 KST이며 자동 연장하지 않는다.

원 track의283노드와 old primary/backup 점의 동일성·순서, 원 centered tangent에 대한 법선 offset, 새 oldstation label을 검증한 후 한 번만 profile을 생성했다. 새 기하의 ds/arcs/curvature를 사용하고 old observed curvature를 복사하지 않았다. primary cap90, 축별 횡력과 종력을 결합한 nominal wheel bound0.999, backward-descending→forward-ascending, bisection40, periodic3pass로 고정했다. 실제 body mass7.301919967kg와 종방향 effective mass29.249793767kg를 구별했다. 계산된 nominal peak ratio는0.9990000000000001이다. 이는 동적 안전 인증이 아니다.

backup도 동일한 새 기하를 사용한다. periodic283개·launch284개 각각을 `min(new_primary_Q_i, 6400, old_backup_Q_i)`로 같은 원 node index에 매핑했다. old absolute arc 보간은 쓰지 않았다. 모든 배열과 코드·의존성·입력을 source 전에 hash로 고정했으며 profile artifact SHA256은 `b8c975fa5eae12f6c09e70e7852ffa4ac3cad3952f86d5a85ece1e89de80a61f`다.

positive 원577 initial→s400은304raw에서 crossing hold를 완료했다. 저장 원본과 모든 full row, raw96 및 끝의 complete checkpoint가 정확히 같았다. 실제 raw96 checkpoint를 독립 복제해 후보를 시작했다. raw1..96은 원 계약, raw97부터 새 primary/backup 계약이다. 전환 시 old/new progress81.08792499028122m로 차이0이며 물리 상태·clock·visited·tracker·누적 launch/tracking history는 변경하지 않았다. forecast별 history는 실제 시작 history에서 분리하고 실제 history를 덮어쓰지 않았다. 기존537 chooser와 fresh FINAL 인증을 유지했다.

고정 old551 world plane에서 첫 forward COM crossing만 잠그고 old projection±10m·old corridor3m를 별도로 판정했다. 통과 raw의 chord 보간 시간과 hold 전체4raw 안전을 모두 요구했다. 좌표나 plane normal은 공개하지 않는다. s200은 진단이고 s300/400은 유지 관측이다.

|고정 plane|원577 연속 시간(s) / raw bracket|후보 연속 시간(s) / raw bracket|후보−원(ms)|eligible / whole hold safe|
|---|---|---|---:|---|
|s200|3.851288680 / 192→193|3.878991197 / 193→194|+27.702517|양쪽 모두 true / true|
|s300|4.946815241 / 247→248|4.974221540 / 248→249|+27.406299|양쪽 모두 true / true|
|s400|6.051435037 / 302→303|6.080503580 / 304→305|+29.068543|양쪽 모두 true / true|

|후보 crossing 진단|s200|s300|s400|
|---|---:|---:|---:|
|보간 COM speed(m/s)|79.095100|94.842571|94.848331|
|보간 yaw(rad/s)|−0.247695|−0.233466|0.001843|
|crossing raw force peak ratio|0.781724|0.107308|0.200467|
|누적 tracking clipped/samples|31/392|31/612|31/836|
|crossing posttick footprint margin(m)|5.075264|4.995936|5.211076|
|new / old progress(m)|199.846825 / 200.079825|300.322359 / 300.552309|401.617890 / 401.847840|
|new / old path error(m)|0.211386 / 0.352217|0.211595 / 0.211595|0.116741 / 0.116741|
|new / old reference excess(m/s)|−4.697131 / −0.720572|4.842668 / 4.842668|4.831369 / 4.831369|

crossing snapshot의 여유는 hold 최솟값이 아니다. 별도로 전 실제 suffix212raw 전체가 strict 안전을 통과했으며 최소 footprint margin0.559112620m(기준0.50), 최대 force ratio1.058991474(기준1.059), 최대 새 path error1.515258684m, 최대 새 reference excess4.848768895m/s(기준4.85)였다. old path 최대1.633329250m·old reference excess 최대4.848768895m/s도 별도 기록했다. 작은 force/reference 여유를 넓은 강건성으로 해석하지 않는다. 원 source domain/body<100과 기존 clipping·launch·물리 판정도 유지했다.

후보는 raw96 이후53hold/212actualraw를 실행하고 s400 crossing hold 끝인 global raw308, episode6.16s에서 멈췄다. 끝 new progress407.306097850m·old progress407.536047713m, COM94.846897544m/s, yaw−0.157984508rad/s, 최대 절대 joint0.007798216rad다. 끝 tracking31/848, launch55/384이며 첫 actual 실패나 no-safe-action은 없었다. actual force 안전과 내부 rejected forecast의 위험 수치를 혼동하지 않는다.

예측·비용·검증

chooser53회, forecast/FINAL 인증1,031개를 모두 계수했다. 인증 결과는 통과376, force 거절462, clipping 거절7, reference 거절165, footprint 거절21이다. rejected 예측을 포함한 보고 최대 force19.545193·최대 clip fraction0.2·최소 margin0.440008m는 **실제 실행 경로 통계가 아니다**. 각 후보를 실제 prefix history로 독립 인증하고 거절 비용까지 포함했다.

|항목|실측 합계|사전 상한|
|---|---:|---:|
|실제 raw 시도/완료|516 = positive304 + candidate212|1,152|
|전체 raw 시도 / 완료 model tick|20,953 / 20,484|각60,000|
|external / internal wheel force 호출|83,812 / 81,936|260,000 / 240,000|
|force 호출 총합|165,748|500,000|
|geometry pack|21,517|65,000|
|profile bound 평가(읽기 감사 포함)|8,635|100,000|
|CPU(준비·실패·감사·보조 포함)|513.441560초|900초|
|wall(동일 실행 단계 누적)|557.334555초|1,100초|

raw 시도−완료469는 forecast preforce 거절로 tick하지 않은 경우다. external=4×20,953, internal=4×20,484이며 geometry=완료20,484+forecast root1,031+positive/candidate root2다. durable journal의 BEFORE_FORCE/FORCE_VERDICT, BEFORE/AFTER_TICK, BEFORE/VERDICT_GEOMETRY와 실제 호출 수를 대조했다. journal chain과 코드·의존성·배열 hash가 모두 맞았다.

runtime profile bound8,068=primary7,496+실제 backup min567+synthetic min5다. 감사에서 저장 배열567개의 min identity를 읽어 확인해8,635로 합산했다. profile bisection update6,120도 따로 남겼다. source0 감사는 새 profile/source/force/chooser를 실행하지 않았다. 대형 journal hash 후에 감사 시간을 확정해 CPU0.750747초/wall0.338550초를 포함했다. runtime CPU510.690813초/wall554.996005초(준비 예비10초 포함)에 이를 더하고 보수적 보조2초를 부과했다. 대화·편집 대기는 과학 실행 시간으로 주장하지 않는다. 사전 replay416raw 및 감사 여유를 항상 예약했고 실행 중 상한을 늘리지 않았다.

순수 검사6개와 저장 증거 감사26개 모두 통과했다. 결과는 비용 검열·기술 오류·source domain 중단이 아닌 **안전 통과 후 과학적 시간 비개선**이다. fullsafe s400 및32ULP 초과 양의 이득을 모두 요구한 replay gate는 음의 이득−0.029068543초 때문에 닫혔다. 100/500ms 임의 문턱으로 판정을 바꾸지 않았다.

승격·보존·한계

DEV 한 형상의 한 정책 prefix에 대한 결론이다. HOLDOUT/SEALED/new world/whole/native/새 dynamics FD/solver/학습/별도 유료 자원은 모두0이다. actual13.66초/source13.20초, 연구22,758·reserve84,000/사용0을 유지한다. 공식 완주·native 성능·11초대 개선은 검증하지 않았다. 이 연구선은 승격하지 않고 종료한다. 후속 실험 계약은 생성하거나 자동 실행하지 않는다.

원시 geometry·plane 좌표·상태·commands·checkpoint·chooser trial·journal은 지정 클라우드의 Git 외부 비공개 경로에 보존한다. 공개하는 것은 코드·계약·집계·해시와 이 보고서다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants, 사용자 변경, 기존 실패·백업을 보존했다.
