# 581 — 두 hold의 source viability와 독립 재현 통과

**결과: `EIGHT_RAW_VIABLE_EXACT_REPLAY`.** 선택된 안전 parent25를 원래 초기 상태부터124raw로 재구성한 뒤, wheel-slip alignment 법칙을 holds32/33에 한 번씩 계산해 각각4raw 유지했다. **8raw 모두 기존 안전 조건을 통과했고, 초기 상태부터 exact132raw replay 한 번도 일치했다.** 예산 중단·기술 오류·실패 raw는 없다.

이는 기존13개 pursuit 행동이 막힌 **한 source 상태에서의 짧은 viability 탈출**이다. 장기 경로 유지·기존 정책 복귀·s200·whole finish·시간 이득·native 성능은 실행하거나 입증하지 않았다. **source13.20/actual13.66초 incumbent는 그대로다.** 새로운 법칙·gain·부모·baseline sweep·자동 후속 실험은 없다.

## 계약·초기 계보·검사

580 제안과 commit `5b91de254c3e8cd2ec4daddd242335bba8bff18e`는 보존했다. source 전에 [581 계약](slip581_contract.json)을 고정했다. SHA256은 `c861f3693bc1c2f8b13957de661b8b2cd1a18501f9cdeb3955b913187f6b3342`이며 STARTED와 종료 후 값이 같다.

실제 import 파일709개의 dependency closure, 새 코드·[테스트](../tests/test_slip581.py) hash, static 초기 상태·path·ledger·`initial_visited`·selected private prefix 등 입력 hash를 시작/종료에 검사했다. `brake506_geometry`, `brake508_corridor`, `brake510_common`, `drive519_control`도 포함한다. source 호출 없는 검사10개가 통과했고, 두 검사 실행의 사용량을 [기록](slip581_tests.json)에 포함했다. 부호·개별 wheel offset·circular mean/degenerate domain·4raw 유지·첫 실패 중단·tuple/JSON prefix adapter·force 계수·내용 기반 checkpoint·단계 간 예산 예약을 검사했다.

[실행기](slip581_model.py)는 원 source 초기 root·tracker·visited·clock에서 저장31hold/124raw 명령 계보를 새로 실행했다. launch96raw는 모든 비교 필드가 일치했고, 변경 branch28raw도 저장된 root·force·history·progress·geometry·명령·시간 등 이용 가능한 필드가 일치했다. journal에 없었던 branch 전체 tracker/visited의 옛 값을 만들거나 다른 상태에서 이식하지 않았다. 실제 초기 lineage로 생성한 full checkpoint를 저장했다. 실패 child에서 시작하지 않았다.

[법칙](slip581_math.py)은 전륜별 `COM velocity+wheel offset`의 heading 두 개를 circular mean하고 body angle을 뺀 공통 joint 목표를 기존±0.4 domain과 부호로 변환한다. pedal은 absolute holds32/33의 factual 값이다. law 계산은 정확히2회이며, replay에서는 계산하지 않고 실제 선택한 명령을 재생했다. 원 force·clip·reference·footprint·path·body·projection predicate는 수정하지 않았다.

## 첫 hold와 둘째 hold의 실제 반응

| 지표 | hold32: raw125..128 | hold33: raw129..132 |
|---|---:|---:|
| 최대 force ratio | **0.735816** | **0.434201** |
| force 검사 직전 최대 횡성분 ratio¹ | 0.657314 | 0.389626 |
| 진행 변화 | +4.309182m | +3.922974m |
| COM 속도 시작→끝 | 53.6011→49.3978m/s | 49.3978→46.4242m/s |
| yaw 시작→끝 | 2.15804→1.44801rad/s | 1.44801→1.00336rad/s |
| 평균 front joint 시작→끝 | 0.137302→0.085988rad | 0.085988→0.057724rad |
| 평균 front rate의 최대 절댓값 | 2.565716rad/s | 1.413175rad/s |
| 최소 전체 footprint 여유 | **4.228457m** | **3.933513m** |
| 최대 path error | 1.242813m | 0.889827m |
| 최대 reference 초과 | 2.385872m/s | −1.337875m/s |
| 최대 body 속도 | 55.128238m/s | 50.449857m/s |
| tracking clipping counts | 0/112→0/128 | 0/128→0/144 |
| 새 clipped wheel samples | 0 | 0 |
| 안전 실패 raw | 없음 | 없음 |

¹ 저장된 wheel 운동학에서 `|82×lateral velocity|/friction`을 읽는 기술 통계다. 추가 source force 호출은 아니다. force ratio는 실제 외부 검사 결과이며 두 수치를 같은 것으로 취급하지 않는다. launch counts55/384도 그대로 유지됐다.

각 hold 첫 raw에서 servo가 목표에 도달했고 이후 해당 hold의 목표는 고정됐다. front 횡성분은 hold32 첫 raw 후0.06546, hold33 첫 raw 후0.04120까지 내려갔다. body yaw는 joint 전이와 함께 변했으므로 즉시 정렬된다는 가정 대신 실제4raw를 검사한 결과다.

| global raw | 최대 force ratio | 검사 전 front 횡성분 ratio | 적분 후 yaw(rad/s) | 적분 후 평균 front joint(rad) |
|---:|---:|---:|---:|---:|
|125|0.735816|0.657314|2.120095|0.085988|
|126|0.557140|0.065462|1.375268|0.085988|
|127|0.500486|0.356401|1.618277|0.085988|
|128|0.527030|0.316272|1.448006|0.085988|
|129|0.434201|0.325404|1.461444|0.057724|
|130|0.432213|0.041198|1.010839|0.057724|
|131|0.417322|0.188662|1.120432|0.057724|
|132|0.409644|0.165590|1.003365|0.057724|

## 옛 실패와의 비교 범위

기존13행동은 새로 평가하지 않았다. 저장579의 **같은 parent25·같은 factual pedal** 행동과 비교하면 첫 force vector·ratio가 정확히 같았다. steering 명령이 현재 force를 즉시 바꾸지 않는 순서와 일치한다. 이후 옛 행동의 두 번째 raw peak는 **1.199315>1.059로 실패**, 새 법칙은 **0.557140으로 통과**했다. 다른 steering이 joint/yaw 전이를 바꿔 이 한 source force 벽을 피했다는 근거다. 같은 시작 상태에서 모든 가능한 제어의 우열이나 일반적인 정책 성능은 증명하지 않는다.

raw132 endpoint는 저장 factual의 같은 raw보다 진행+1.012183m·COM 속도+4.409606m/s였다. 이 차이에는 이미 빨랐던 변경 prefix의 이득이 들어 있다. 새 법칙 적용 중 속도는53.601→46.424m/s로 감소했으며, 어느 비교도 이번0.16초의 feasibility 검사를 랩 시간 개선으로 바꾸지 않는다.

## 재현과 실제 비용

초기 source에서31hold prefix와 실제 두 intervention 명령을 재생한132raw가 최초 실행과 일치했다. 모든 저장 row 전체와 최종 checkpoint 내용의 일치를 별도 읽기 검토에서도 확인했다. object ID로 비교하지 않았다. journal1,322개 event의 chain이 유효하며264회 force/raw verdict 모두 실패가 없고, `ALIGNMENT_COMMAND`는2회다.

| 비용 | 실제 | 상한 |
|---|---:|---:|
| attempted raw / 완료틱 | **264 /264** | 각각300 |
| 외부 force 실제 wheel 호출 | **1,056** |1,200|
| 내부 적분 실제 wheel 호출 | **1,056** |1,200|
| force 합계 | **2,112** |2,400|
| geometry 검사 | **264** |300|
| runtime CPU /wall | **10.7449s /9.2925s** |25s /35s|
| 후속 읽기 감사·마감 charge 포함 CPU /wall | **11.6312s /10.1824s** |25s /35s|

단계별 CPU/wall은 준비4.560/2.711초, prefix2.746/2.930초, intervention0.215/0.227초, verification3.026/3.224초, runtime audit0.198/0.200초다. 준비에는 두 source0 검사 실행과 등록/hash 보수 charge가 포함된다. 후속 읽기 감사와 마감 charge를 포함한 audit도 약1.084/1.090초로3/5초 이내다. 모든 단계 한도를 지켰다. 과학 실행·감사 도구의 비용이며 대화·전체 Git 전달까지 잰 벽시계라는 주장은 아니다.

[실행 결과](slip581_result.json) · [원 비용](slip581_cost.json) · [읽기 감사](slip581_analysis.json) · [감사 코드](slip581_closeout.py)

이번 성공의 승격 범위는 **이 selected state에서8raw viability와 재현**까지다. native·whole·장기 유지·다른 부모·다른 법칙·추가 optimizer/FD/rollout은0이다. source13.20/actual13.66초 incumbent·research잔여22,758·reserve84,000/사용0을 보존했다. HOLDOUT·SEALED·별도 유료 자원 사용도0이다.

승인된 지정 클라우드에서만 수행했으며 종료2026-10-20 10:01:55UTC 전에 완료했다. 자동 연장이나 다음 실험은 없다. 원문·원시 상태·명령열·journal·재현 tape는 private에 남겼다. 공개물은 기술 코드·계약·집계뿐이며 main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·백업·이전 결과를 보존했다.
