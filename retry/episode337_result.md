337 대체 episode는 기술 오류 없이 실행됐지만 **N2를 완주하지 못했다**. 실제335 prefix72를 정확히 재현한 뒤 계속 자기 관측에서 모든 제어를 실행했고, 132번째 접촉 이후 진행이 멈춰233번째 `off_track`으로 공식 종료됐다. 336의1행동 기술적 censoring과 구분되는 실제 DNF다. 335의72행동 국소 개선만으로 전체 episode feasibility가 성립하지 않았다.

| 실제337 결과 | 값 |
|---|---:|
| 등록 실제 상한 / 사용 행동 | 2038 / 233 |
| 335 실제 prefix 재현 | 72명령·73관측·actor state·memory·physics·접근 가능한 RNG 일치 |
| terminated / truncated | True / False |
| finish-qualified / finish / lap time | 없음 / 없음 / 미관측 |
| 고유 tile | 132/292 (45.21%) |
| collision event / 최종 damage | 132번째 한 번 / 0.2 |
| 공식 종료사유 | off_track |
| elapsed raw counter | reset50→982, limit8200 |

363이나 예산 한도에서 자른 결과가 아니다. 실제 reset counter50·warmup50·skip4를 확인했고 상한2038까지 허용했으나 그 전에 공식 retirement가 발생했다. official finish flag를 우선하며 truncated를 무조건 DNF로 처리하지 않는 기존 계약은 유지했다. 이번에는 finish flag가 없으므로 소급된 중심 통과 lap time도 없다.

serializer의 DamageEffects·NumPy 처리를 native0으로 검증하고 cached72 검증을 다시 통과한 뒤 실행했다. 수정336 runner와337 runner는 stage namespace 외 AST가 같으며 새 native 계측 필드를 추가하지 않았다. 정책·archive·worker·제어·물리·시간·N2 조건은 그대로였다. reset은 한 번, 새 A는0회였고 재시드·sweep·snapshot·teleport·저장 후속 명령 강제는 없었다. 실제 반환 steer/gas/brake가 모든233행동에서 그대로 실행됐음을 저장 자료로 검증했다. 72 이후에도 원래 정책의 메모리 갱신과 자기 방문 상태를 사용했다.

실패 최초 구간은 두 종류의 contact를 구분해야 한다. collision event는132번째 한 번이지만, 같은 장애물(index2)의 hull fixture touching은132–233의102개 연속 wrapper 끝점에서 관측됐다. tile 증가도132번째가 마지막이었다. 133–233에 새 tile 없이 음수 보상이101행동 연속되어 `off_track` counter가101이 됐다. 이 판정은 좌표만의 도로 이탈 증명이 아니다. 충돌 뒤 막힘·정체와 일치하는 측정이다. 초기 출발 구간에도 일시적인 음수 counter가 있었으나 최종 실패 streak와 혼동하지 않았다.

132번째 직전 속도44.510m/s가 접촉 후3.131m/s로 떨어졌다. 이후 같은 hull contact가 유지되고 진행이 멈췄다. 전체233입력 중 target/path 부재 flag는0회였다. 따라서 현재 증거에서 ‘경로가 사라져 정지했다’고 해석하지 않는다. damage0.2가 낮다는 이유로 성공이라 부르거나, damage 증가를 독립 자동 veto로 쓰지도 않았다. 공식 완주·종료·진행량을 우선 구분했다.

사후 정적 진단은 기존 필드만 읽었으며 새 native나 actor 호출은 없다. 접근124–132에서 실제 접촉 장애물의 현재 검출 중심 오차는0.023–0.297m였고 이 모든 구간의 optical affine은 승인 상태였다. 반면124번째에 새로 검출된 다른 점은 가장 가까운 실제 장애물에서도8.468m 떨어져 있었고 이후 보존됐다. 현재 실제 장애물 검출, 미해결 검출의 보존, routing 및 접근 속도·목표 추종을 분리해서 볼 필요가 있다. 이번 fallback 수정만의 순간 오류라고 확정하지 않는다.

같은 실제 픽셀과 기존 speed·nominal memory·routing/controller를 고정해 전체 보존점과 현재 직접 검출만의 routing을 비교했다. 원래 경로·steering을9장면 모두 정확히 재현한 뒤 비교했으며, steering 차이는128·129번째에만 있었다. 130–132는 같았다. 132번째 경로의 첫 구간과 먼 목표 heading은 약0.549rad 차이가 났다. 이 함수 수준 의존성은 물리 원인 증명이 아니며 실제 가림 보존 증거도 아니다. GT는 이 진단의 오차·fixture 확인에만 썼고 actor 입력에는 전달하지 않았다.

과거296 N2는 동일 case·archive 자격의363행동/29,000ms 공식 완주 기록이며 damage0.6이었다. 과거330 A는72번째 crash였다. 둘은 비교자료로 재사용했을 뿐 새 run으로 부르지 않았다. 과거296에는 새 실패 위치의 픽셀·pose·fixture가 없으므로 같은 행동 번호를 같은 공간 위치로 간주하지 않았다.

336의 실제1 native는 환급하지 않았다. 추가1을 등록한 총 B는1,368,238이었고 이번233을 차감해 누적native1,282,433·연구잔여1805·최종예비84,000이다. raw step932 tick/reset51 tick, wall25.155초/evaluator CPU22.340초/actor CPU2.850초, 물리 상태 capture wall10.081초였다. cached actor72회는 wall1.619초·actor CPU0.869초였다. 사후 routing18회는CPU2.122초이며 native0이다. 초기 hash/data 로딩·build·보고 등 미계측 범위도 기록했다. GT capture 포함 비용은 순수 simulator stepping 비용과 구별한다. 새 학습·source physics rollout·유료 자원은 없다.

다음 정보가 큰 비교는 새 실패를 겨냥한 단일 명령 진단으로 제안했다. 기존337 A를 기준으로 새 B가 동일 prefix128을 재현한 뒤, 129번째 steering만 현재 직접 검출을 입력한 기존 routing 출력으로 실행한다. 그 행동의 페달과 원래 nominal memory 갱신은 유지하고, 이후에는 자기 관측에서 원래 후보의 모든 제어를 실행한다. source에서 계산한 steering을 쓰므로 새 pulse 크기나 threshold를 탐색하지 않는다. 실제 접촉·막힘·진행을 공통233까지 비교하는 prefix128+개입1+관찰104=상한233 native이며 현재1805 안에 들어간다. 이번에는 실행하지 않았다.

이 후속 제안은 명시적인 국소 충분성 테스트로, 233 생존은 protocol stop이지 완주가 아니다. 같은 접촉·막힘·retirement라면 그 한 번의 이른 방향 변경만으로 충분하다는 가설을 반증한다. 효과가 없으면 near-path/far-target 추종과 높은 접근 속도를 분리하며, 자동 horizon 확대나 승인 optical 교체로 넘어가지 않는다. 전체 N2 feasibility gate가 실패했으므로 paired 다도로 성능 검증이나 champion 승격으로 확대하지 않았다.

334의 전체 최근접 순차 평균24.400→25.294m 악화, 대응 subset paired fallback 평균4.640→2.752m 개선을 모두 보존했다. 실제 가림은 여전히 미검증이다. 원문·회고·추출본·raw GT·pixels·모델·private seeds는 공개하지 않았으며, champion296·TRAIN registry·사용자 변경·main·backup·공식 Participants·DEV/HOLDOUT/SEALED를 보존했다. 승인 종료는2026-10-17 19:01:55 KST다.
