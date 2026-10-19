# 580 — 579의 수렴 원인과 다음 단일 반증 계약

**579는 다양한 물리 상태를 실제 만들었다. 처음부터 factual 복사본만 남은 것은 아니다.** 빠른 prefix는 한때 factual보다0.674m 앞섰으나, 첫 코너의 force 벽에서 살아남지 못했다. 진행도 ranking은 느린 준비 상태를 실제 버렸지만, **버린 상태가 이후 더 빨라졌다는 증거는 없다.** 다음에는 폭·step·offset 대신 **pure-pursuit 조향 표현 하나를 바꿔**, 전륜의 실제 속도에 정렬하는 기계적 슬립 feedback을 두 hold만 검사하는 계약을 제안한다. 이번에는 실행하지 않았다.

현재 기준은 **actual13.66/source13.20초**, 초 단위 회수 기회는 미검증이다. 이번580의 source/native/FD/optimizer·보호평가 사용은 전부0이다. 578·579 및 A 실패/B 미실행 기록을 보존했다.

## 무엇을 복원했는가

[분석 코드](forensic580_analyze.py)는579 전체 private journal **18,899개 event**의 hash chain을 확인하고, 기록된 상태·행동·force/history verdict를 **1,258개 child,97개 부모 instance,25개 깊이**로 연결했다. 저장된 열거·기하 projection·ranking 산술만 대조했으며, 어떤 다음 상태도 적분하거나 새 후보를 평가하지 않았다. 전체 trajectory를 다시 source 실행하지 않았다.

1,258개 행동의 byte identity·부모의 물리 root/이력·raw, 모든 깊이의 live/terminal 수와52개 최종 terminal의 ID·root·history·progress가 저장 기록과 일치했다. 분기별 최초 명령·물리 상태·tracking history 차이와 계보는 private 파생 graph에 남겼다. 공개 [집계](forensic580_analysis.json)에는 분포와 비공개 입력 hash만 있다.

동일성 key는 물리 root에서 다음 action이 덮어쓰는 steer target을 제외하고 launch/tracking counts·progress·global raw를 더한 **기록 가능한 상태**다. 매 raw의 tracker와 visited 전체는 journal에 없으므로 이를 full checkpoint/future equivalence라고 부르지 않는다. 그 제한 안에서 매 깊이1..24의 live4개는 서로 달랐고 정확히 하나만 factual이었다. 단순 중복 상태가 세 경쟁 슬롯을 모두 점유했다는 설명도 지지되지 않는다.

## 후보가 달라진 시점과 다양성

첫 변경 기회는 hold25이고 실제 물리 차이는 그 첫 raw인97부터 나타났다. 전체 child prefix1,258개 중1,233개에 명령 차이가 있고1,206개에 물리 차이가 기록됐다. 명령만 달라진 나머지를 actuator 무반응으로 단정하지 않는다. 적분 전 force 거절로 새 상태가 생기지 않은 경우도 포함한다. 최초 변경 hold25를 물려받은 descendant child는284개다. 이 수는 독립 실험이나 unique 초기 행동 수가 아니라 계보별 child 집계다.

아래 차이는 **같은 global raw의 factual 상태 대비 endpoint 기술 통계**이며, lap 이득이나 독립 인과 효과가 아니다.

| 지표 | 경쟁 live로 유지된72개 | 폭 제한으로 버린602개 |
|---|---:|---:|
| 진행 차이 범위 | −0.181~+0.674m | −0.943~+0.512m |
| 진행 차이 중앙값 | +0.00035m | −0.413m |
| 속도 차이 범위 | −3.518~+5.504m/s | −13.108~+5.075m/s |
| 속도 차이 중앙값 | −0.0056m/s | −5.956m/s |
| yaw 차이 범위 | −0.366~+0.743rad/s | −0.706~+0.976rad/s |
| rear omega 평균 차이 범위 | −9.982~+10.905rad/s | −27.795~+8.894rad/s |
| tracking clipped samples 차이 | −6~+2 | −11~+2 |

안전한 같은 깊이의 child 사이에서 최대 속도 span은13.108m/s, yaw span은1.287rad/s였다. 폭 탈락602개 중 yaw 차이 절댓값>0.01rad/s가581개, rear omega 평균 차이>1rad/s가546개, clipping count 차이가424개였다. 이 문턱은 고정한 설명용 눈금이며 새로운 안전·성능 gate가 아니다. lane offset+4 pedal 표현은 **조향·속도·wheel/history의 물리적 다양성을 만들었다.** 완료된 search raw의 front joint7,096개 중 rate cap에 걸린 것은422개(5.95%)뿐이므로, 일반적인 servo 포화 때문에 모든 행동이 같아졌다는 해석도 맞지 않는다.

## ranking이 버린 것은 무엇이고, 무엇이 미관측인가

폭 탈락602개 중545개는 factual보다1cm 이상 느렸고, 그중416개는 clipping count가 더 낮거나 |yaw|가 더 작았다. 현재 시점의 자원·yaw descriptor가 다르다는 증거다. 더 낮은 |yaw|가 항상 더 안전하거나 미래가 빠르다는 뜻은 아니다. 버린602개 중 기록 가능한 상태 key가 나중에 실제 확장된 부모로 다시 나타난 것은0개였다. 따라서 그 상태의 **후속 회복·시간 이득은 관측되지 않았다.**

구체적인 같은 부모 비교가 있다. hold31의 같은 prefix와 같은 steering을 가진 두 sibling 중, ranking이 버린 쪽은 유지된 쪽보다 진행0.1617m·속도3.1528m/s가 낮고 yaw0.1123rad/s·rear omega5.536rad/s가 낮았다. clipping count는 같았다. 버린 쪽도 factual보다는0.5124m 앞섰다. 현재 wheel 운동학에서 최대 횡성분 비율은 버린 쪽0.5892, 유지된 쪽0.6573이었다. 유지된 쪽의 다음13개 행동은 전부 실패했고, 버린 쪽의 미래는 실행되지 않았다.

즉 **서로 다른 준비 상태를 진행도 순위가 버렸다는 사실은 확인**했다. 그중 유용한 미래를 잃었다는 것은 아직 가능성이다. 이 둘을 합쳐 ‘폭을 늘리면 빨라진다’고 결론내리지 않는다.

## 빠른 prefix가 사라진 실제 위치

| 실패 | 집중 구간 | 부모별 집중 |
|---|---|---|
| REFERENCE191 | 전부 holds26..31, 실패 후 raw104..123 | 23부모에서 발생, 상위5부모가31.4% |
| FORCE313 | holds32..38에266개(85.0%), 전체 실패 요청 raw114..187 | 45부모에서 발생, 상위5부모가20.8% |

reference 거절은 fullgas만의 문제가 아니다. coast·brake primitive도 들어간다. 앞선 변경 상태의 속도·진행도와 그 위치에서 조회한 고정 reference의 결합을 무시하고 pedal 하나의 효과로 해석할 수 없다. force313개 중 peak wheel이 front index1인 것은279개(89.1%)였고, hold의 두 번째 raw 실패가231개였다.

가장 명확한 벽은 **hold31 끝의 빠른 경쟁 상태3개→hold32**다. 선두는 factual보다 진행+0.6741m·속도+4.0693m/s였다. 이3부모는 각각 기존13개 행동 **전부 raw2에서 FORCE 실패**했다. 그 자리에서 factual 부모는 안전 child6개를 만들었고 경쟁 슬롯이 다시 그 계보에서 채워졌다. 이후 holds33에서도 세 경쟁 부모의13개가 모두 실패했다. 이 과정은 ‘큰 gain gate가 처음부터 후보를 막음’과 다르다. source 안전 검사를 실제 통과하지 못한 것이다. 최종100ms gate는 모든 terminal을 생성한 뒤 적용됐으며, 그 문턱이 intermediate beam을 prune하지 않았다.

[후속 기록 산술](forensic580_closeout.py)로 stored wheel velocity·heading·friction에서 `|82×wheel lateral velocity|/friction`만 계산했다. 새 `force_rows`나 `wheel_response` 호출은 없다. hold32의39개 실패 raw에서 이 횡성분만의 비율 하한은 부모별 최소 **1.1764 /1.1451 /1.0730**으로 모두1.059를 넘었다. 전체 FORCE 실패 중231개도 횡성분만으로 한도를 넘는다.

이것은 **기록된 실패 상태에서 longitudinal force를 바꿔도 횡성분을 지울 수 없었다**는 source 식의 산술 설명이다. 다른 steering이 raw1의 servo/joint/yaw 전이를 바꿨을 때도 실패한다는 증명은 아니다. 현재 명령은 현재 wheel 방향의 force를 즉시 바꾸지 않으므로 실패 child에서 시작하는 복구 실험도 제안하지 않는다.

## 선행 증거와 다음에 바꿀 가정 하나

| 기록 | 이번 판단에 쓸 수 있는 근거 | 확대하면 안 되는 주장 |
|---|---|---|
| [541](joint541_result.md) | 결합된 launch/cap 구조 변경의 실제560ms 개선 | 구성 요소별 독립 효과의 합 |
| [551](whole551_result.md) | 경로·속도 retiming source440ms 개선 | 현재 reference/path의 물리 최적성, native440ms |
| [552](defect552_result.md) | 상태 의존 강한 제동으로 제동 거리 약12.57m 감소 | lap time 이득·임의 pedal 강화의 보편 타당성 |
| [555](drift555_result.md) | 정상 trim과 실제 이산 전이/도달 가능성이 달랐음 | 11.507초 시계를 실행 가능한 정책으로 사용 |
| [577](direct577_result.md) | projected tangent의 미세 변화로14.44µs | 전역 제어 공간의 무효나 단순 step 확대의 필요성 |
| [579](beam579_result.md) | 물리 다양성과 빠른 prefix가 존재했지만 국소 전륜 force 벽에 막힘 | 모든 다른 조향이나 버린 느린 상태도 실패 |

첫24 holds·고정551reference/path·pure pursuit는 모두 설계 가정이다. 현재 launch는 이미540에서 유래한 state 기반 변경을 포함하고 clipped55/384로 최종 정수 한도57에 가깝다. 처음0.48초42개, 다음0.80초13개, 마지막0.64초0개이며 후반 평균 gas는0.997이다. 이 사실이 global launch 최적성을 증명하거나 남은 이득을2clip만으로 제한하지는 않는다. 다만 손대지 않은 고정gas launch를 새로 개선하는 것처럼540을 재포장할 근거도 없다.

이번 선택은 **pure-pursuit 목표점으로 steering을 구성해야 한다는 가정 하나**다. 다른 방법군으로 **전륜 실제 속도에 기반한 기계적 슬립 정렬 feedback**을 선택한다. launch24와551reference/path는 그대로 두므로 reference를 완화해 force 벽을 우회하지 않는다. 새 경로/reference 계약도 이번에는 제안하지 않는다. 전역 launch 최적제어·AD/trim의 새 연구선은 시작하지 않았다.

관련 [543](velocity543_result.md)은 COM 속도 방향을 기준축으로 PP를 계산해 안전32hold와 작은 진행 차이를 관측했으나 사전 효과 gate에 실패했다. 이번은 PP 목표점·lookahead를 없애고 **각 frontwheel의 COM velocity+회전 offset**을 사용한다. 다른 reachable fast state의 두 hold만 검사하는 질문이며,543을 동일한 식이나 같은 state에서 재시도하는 것이 아니다. 그 차이만으로 성공을 예측하지 않는다.

## 다음 단일 반증 계약 — 미실행

[제안 계약](forensic580_next_contract.json)은 **PROPOSED_NOT_EXECUTED**다. 저장579에서 첫 hold32 force 벽의 가장 앞선 부모25를 선택했다. 이 부모는 실패 root가 아니라 **안전한124raw prefix 끝**이다. 정확한 command 계보와 expected available-state 기록은 private 파일로 고정했다. 미래 실행에서는 원래 initial source에서124raw를 새로 재구성하고 tracker·visited·launch/tracking·absolute clock을 그대로 이어야 한다. branch journal에 없던 full checkpoint의 동일성을 만들어내지 않는다.

새 법칙은 hold 시작마다 전륜별 `vi=COMvelocity+wheel.offset`의 heading을 계산하고, 두 heading의 circular mean을 공통 wheel 목표로 사용한다. body angle을 뺀 joint 목표를 ±0.4에 제한하고 기존 부호에 맞춰 float32 steering으로 바꾼다. pedal은 원 factual holds32/33 값 그대로다. **매 hold 한 번 계산해4raw 유지**하며, 두 번째 hold는 실제 변경 상태에서 새로 계산한다. 평균 방향이 정의되지 않거나 비유한이면 domain hard stop이다.

첫 action은 기존13개와 byte identity가 다르며, 가장 가까운 옛 steering과0.09922rad 차이가 있다. 이는 offset/step을 튜닝한 값이 아니라 parameter-free wheel 속도 식의 결과다. 공통 mean이 두 wheel을 정확히 동시에 정렬하거나 servo/yaw 반작용을 제거한다는 보장은 없다.

사전 gate는 다음과 같다.

1. hold32의4raw 원 안전 계약 통과 여부를 검사한다. 통과는 예전13행동의 raw2 벽을 이 한 법칙이 벗어났다는 좁은 관측이다. 실패하면 law·gain·부모를 바꿔 재시도하지 않는다.
2. 통과한 **같은 실제 state**에서 hold33을4raw 더 검사한다. 시간 이득·100ms/500ms를 사전 요구하지 않는다. 실패하면 첫 hold 관측과 유지 실패를 구분한다.
3. 두 hold가 모두 안전할 때만, exact commands를 초기 상태부터132raw 독립 replay 한 번으로 재현한다. full checkpoint는 내용으로 비교한다. 통과해도8raw local viability의 근거이며, s200·복귀·whole·native·시간 개선은 미검증이다.

최대 **124+8+132=264 attempted raw**, hard cap300/완료틱300, 외부 force1,200·내부1,200·합계2,400, geometry300, **CPU25s/wall35s**다. 준비·실패·검증·감사를 포함한다. 기존 launch2.5/최종 raw별15%, tracking1.059/누적10%, reference+4.85, footprint≥0.5/path≤3/body<100 및 관측·시간·action predicate를 그대로 사용한다. 추가 optimizer/FD/rollout/폭·깊이 확대·자동 후속 실행은 없다.

이 작은 gate는 초 단위 성능을 요구해 다른 방법의 feasibility 확인 자체를 막지 않는다. 동시에8raw 성공을 큰 개선으로 부르지도 않는다. 성공 시에만 별도 장기 유지 계약을 제안할 수 있고, 현재 incumbent는 그대로다.

## 검증·비용·보존

읽기 전용 graph 분석 CPU1.739s/wall1.490s, 후속 산술·집계 CPU0.690s/wall0.481s와 보수적인 보조 조회·마감 charge2s를 포함해 **CPU4.428s/wall3.970s**다. 이는 과학 분석 도구의 비용이며 대화/전체 Git 전달 시간을 포함한 벽시계라는 주장은 아니다. 모든579까지의 원본 파일은 수정하지 않았다. source/native/FD/optimizer·HOLDOUT·SEALED0, research잔여22,758/reserve84,000·사용0, 별도 유료 자원0이다.

분석은 기존 기술 기록과 부모가 전달한 선행 검토를 사용했다. 개인 원문을 새로 직접 읽었다고 주장하지 않으며, 원문·원시 상태·행동열·journal은 공개하지 않았다. main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, Participants·사용자 변경·백업·578/579 결과를 보존했다. 승인 종료는2026-10-20 10:01:55UTC이며 자동 연장·새 실험 없이 이 분석과 계약만 반환한다.
