589 — feasible seed를 보존한 corridor 기하 후보 한 개, 정적 개선만 확인

551의 원래 기하를 정확한 feasible seed로 보존하고 첫 코너의35개 법선 변위를 한 번 공동 최적화했다. **조밀한 finite-body 정적 검사를 통과한 개선 후보 한 개를 확보했다.** 국소 길이130→129.770050m, 기하 부담8.7801% 감소, 목적1→0.955214922다. 최소 정적 여유는1.452314→0.978395m로 줄어드는 교환이 있었다. source 동역학·native·동역학 FD·학습·새 speed profile은 모두0이며 시간·도달 가능성 개선은 미검증이다.

[실행 전 계약](corridor589_contract.json) · [기하/목적](corridor589_math.py) · [한 번 실행기](corridor589_design.py) · [결과](corridor589_result.json) · [읽기 감사](corridor589_audit.json) · [미실행 후속 제안](corridor589_next_contract.json)

기존533/551 확인과 표현 선택

[533](joint533_result.md)은 원 track 중심의 법선 offset273개와 periodic/launch speed 변수566개를 함께 두고 시간 목적·도로/차체 제약을 적용한839차원 trust-constr였다. 경로 길이978.609832m·peak curvature0.083906/m·독립 외곽 여유1.252015m를 보존했지만320회 뒤 최적성 수렴 gate는 통과하지 못했다. 533 자체의 물리 실행은0이다. 이후 [551](whole551_result.md)은 이 기하를 유지하고549 힘 결합 retiming으로 source440ms 개선·안전 완주를 관측했다. 이번589는533 solver 상태를 복구하거나 이전 실패를 재실행한 작업이 아니다.

588의 chord-based quintic은 유지하고 구제하지 않았다. 589는 **현재551 점 자체+현재 점의 중심차분 tangent에 수직인 법선 변위**를 사용한다. old station90..220 내부 원래 점 중 첫/마지막 점을 guard로 고정하고35개만 움직였다. 외부·경계 segment와 endpoint/tangent는 그대로다. 원점에서 offset0이면 원래 점이 bit-identical이며, projection으로 seed를 다른 경로에 옮기지 않는다.

±4m 숫자 스케일은533에서 차용했지만,533의 원 road 중심에 대한 절대 offset 범위와 이번551 seed 상대 범위는 **서로 다른 설계 영역**이다. 검증된 동역학 범위로 주장하지 않는다. 추가 선형 road/obstacle support-plane 안내 제약으로 corridor 안의 변위를 제한하고 road segment 순서를 보존했다. 글로벌 chord 단조성을 넣지 않았다. 안내 제약 자체도 seed에서 모두≥0인지 먼저 확인했으며 최소0.952113이었다. seed 불일치에 대한 복구·plane 조정은 없었다.

도로 안내 평면은 원 track 노드의 좌우 boundary와 actual8fixture의 고정 seed-heading support를 사용했다. 장애물은 seed COM에서 바깥쪽으로 향하는 고정 separating plane을 사용했다. 이는 빠른 solver 안내이며 실제 도로 union·유한 차체 안전 판정을 대신하지 않는다. 최종 검사는 기존 finite hull4/wheel4 polygon의 road union/finite boundary/obstacle-circle 여유가 권위를 갖는다.

한 목적·solver·채택 규칙

실행 전에 다음 한 설정을 코드·입력 hash와 함께 고정했다. 수치·가중치·형상·solver sweep은 없다.

- J=0.5×L/Lseed+0.5×C/Cseed. L은 old90..220과 겹치는 원 segment 비율로 정의한 국소 실제 polyline 길이다.
- C=R²Σκ²·dual_ds+R⁴Σ(Δκ)²/ds, R=3.24m. R은 source wheelbase=(80−(−82))×0.02에서 왔다. 두 항은 모두 길이 차원이고, seed 정규화 후 각 목적에 같은 상대 비중을 주는 단일 기하 설계 기준이다. 시간/force 최적 법칙으로 해석하지 않는다.
- κ는 signed atan2 인접 turn/평균 인접 ds이며 cost 구간 끝 node·join을 포함한다. Cseed>0을 검사하고 길이0/nonfinite는 기술 실패로 처리한다.
- SLSQP 한 번, 초기0, maxiter20, ftol1e−9, geometry objective 차분1e−5m(533의 기하 차분 스케일), 선형 안내 제약 Jacobian 고정. 이는 기하 FD이며 동역학 FD는0이다.
- 마지막 solver 방향 하나에서 α=1,1/2,…,1/2048 최대12개를 순서대로 검사한다. L/C 비악화와32ULP 초과 J 개선, bound·순서·endpoint·자기 교차·정적 차체를 통과하는 첫 형상만 선택한다. 없다면 원 seed를 반환한다. 이 기준은 이번 정적 질문의 채택 기준이며 물리 필요조건은 아니다.

6개 순수 검사 후 seed 전체 경로2,448개의 finite-body 배치를 검사했다. 각 segment를 ceil(ds/0.5)등분하고 양끝도 포함해 node의 양쪽 segment heading을 따로 확인했다. 정적 joint0 배치이며 샘플 간격≤0.5m다. 기존531의1.252m 추가 floor나 최소1m segment 규칙을 가져오지 않았다. seed는 최소1.4523141295m로0.50m를 통과해 solver를 시작했다.

한 번 실행 결과

SLSQP는 **20회 반복 상한/status9**로 종료했다. 수렴·최적성을 달성했다고 주장하지 않으며 추가 반복도 없다. 첫 최종 α=1 후보는 변경 영향을 받는 segment323배치에서 안전했고, 이어 독립 전체 경로2,447배치 감사도 같은 최소 여유로 통과했다. 한 개만 full-body line-search 검사했고 나머지11개를 실행하지 않았다.

|지표|원551 seed|선택된 한 후보|
|---|---:|---:|
|국소 길이|130.000000m|129.770050m|
|전체 실제 arc 길이|978.609832m|978.379882m|
|bending 항|1.616561417m|1.523348116m|
|curvature-transition 항|0.102103696m|0.044415946m|
|합 C|1.718665113m|1.567764062m|
|정규화 J|1|0.955214922|
|최대 절대 곡률|0.083905958/m|0.076932932/m|
|전체 정적 최소 여유|1.452314130m|0.978394570m|

국소 길이는0.229950m, C는8.7801%, transition 항은56.4992%, peak curvature는8.3105% 줄었다. 동시에 최소 정적 여유는0.473920m 줄었다. 실제 force/clipping/body·미래 동역학 여유가 늘었다는 증거는 아니다. 길이나 J의 개선을 랩 시간으로 환산하지 않았다.

변경 노드는35개, 최대 point/normal 변위0.411904238m다. s90/220의 위치 및 boundary tangent 오차는 모두0이며 외부·guard 점은 정확히 동일하다. 도로의 국소 segment 순서와 sampled 전체 경로의 비인접 자기 교차0을 확인했다. 새 ds/arcs/κ를 실제 점에서 계산했고, oldstation은 원 node identity label로 별도 보존했다. 후보 전체 true arc는978.379881665296m다. 목표면의 old progress와 새 arc를 동일시하지 않는다.

전체 후보 artifact SHA256은 **`1949cafe137cf06d16c25e354ed306bac393c40c838cc124d838b49a6e88f9b3`**다. 점·offset·oldstation/truearc·반복 벡터·정적 pose journal은 지정 클라우드 저장소 밖 비공개다. 공개 집계에는 원시 좌표를 넣지 않았다.

검증 범위와 다음 별도 계약

이번 결론은 **표본 정적 안전을 유지하면서 고정 기하 목적을 개선한 한 후보**까지다. segment 표본 사이의 연속 공간 보장, 실제 joint/wheel/slip 준비, source 도달 가능성, 속도 계획의 전역 안전, 공식 완주·native·11초대는 모두 미검증이다. 원래551 source의 작은 forecast/force/clip 여유를 이 결과로 확대한 것으로 해석하지 않는다. 588을 소급 통과시키거나 578/555의 낙관 proxy를 실행 성능으로 쓰지 않았다.

[별도 미실행 제안](corridor589_next_contract.json)은 이 hash 한 개에549식 cap90·축별 종횡 힘 결합 retiming을 한 번 적용하고 profile을 주행 결과 전에 고정한 뒤, 원래577 initial→s400 positive에서 raw96 full checkpoint를 확보해 단일 source prefix와 s400 유지 시험을 하는 것이다. old observed curvature를 새 reachability 증거로 복사하지 않는다. feedback537/launch540 코드는 유지하되 primary/backup의 새 기하·truearc/profile 입력은 별도 고정한다. backup에는 원 road node association을 검증한 명시적 min-profile mapping을 제안했으며 이번에는 배열을 생성하지 않았다.

이는551 path/reference identity를 바꾸는 별도 문제 계약이다. path3/reference4.85 숫자, 도로/장애물/유한 차체·원 source domain/body<100·force/누적 clipping 등 안전은 유지하며 old551 기준 편차도 별도 보고해야 한다. 원래 첫96raw 계약을 새 reference로 소급 평가하지 않는다. 후속 source의 모든 forecast/FINAL/실패 비용과 최대416raw exact replay를 포함한 상한·첫 실패·비개선·승격 조건을 제안에 명시했다. 현재 speed profile·source feedback·whole/native 실행은0이고 자동 시작 권한은 없다.

비용·감사·보존

|항목|실제|상한|
|---|---:|---:|
|solver/major iterations|1 / 20|1 / 20|
|최종 full-body line-search 형상|1|12|
|full-body/support geometry pack|5,264|15,000|
|objective+constraint 평가(감사 포함)|846|10,000|
|geometry FD 열 / dynamics FD|700 / 0|사전 계수 / 0|
|CPU(준비·테스트·실패/반복·정적·감사·보수적 보조 비용)|104.072819초|600초|
|wall(같은 계산 단계 누적)|102.628749초|800초|

geometry5,264=proxy support46(실제35+synthetic11)+seed2,448+후보323+최종 전체 감사2,447이다. geometry FD700=35×20이며 실제 동역학/force는0이다. objective781+constraint63=844에 저장 감사의 재계산2를 더했다. cache hit41도 objective query 상한에 포함했다. 모든20회 반복·line-search·실패 비용을 보존하고 실행 도중 상한을 늘리지 않았다. 평가 중 geometry와 CPU/wall 감사 여유를 먼저 예약했다.

runtime CPU101.683381초/wall100.539868초에는 준비 예비10초·import·검사·전체 solver/정적 감사를 포함했다. 후속 읽기 감사CPU0.389438초/wall0.088881초와 보수적 보조2초를 합산했다. 대화·편집 대기를 과학 실행 시간으로 주장하지 않는다.6개 순수 검사와 입력/코드/계약 hash·모든 geometry 계수/최솟값·endpoint/normal표현·major iterate·원장·main 검사는 모두 통과했다. 추가 solver·geometry query·profile·source로 검사를 반복하지 않았다.

실제13.66초/source13.20초,연구22,758·reserve84,000/사용0을 유지한다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,Participants·사용자 변경·533/551·588·이전 실패·백업을 보존했다. 새 world/HOLDOUT/SEALED/학습/별도 유료 자원0이며 종료2026-10-20T10:01:55UTC를 연장하지 않았다. 이번에는 선택된 기하와 미실행 후속 제안만 보존한다.
