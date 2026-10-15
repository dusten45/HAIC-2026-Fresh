338의128번째 steering 단일 개입은 충돌·종료를 해소하는 국소 충분성을 통과하지 못했다. B는 동일 prefix127을 재현한 뒤128 steering만 바꿨지만, A와 같은132번째 첫 접촉 후136번째에 damage1.0으로 공식 crash했다. A와 정체 양상은 달랐고 B가2 tile 더 진행했으나, 첫 충돌과 retirement를 해결하지는 못했다. 이 결과를 모든 보존점이 무해하다는 결론이나 속도·lookahead 원인 확정으로 확대하지 않는다.

실행 전124–128의 cached 검증에서 실제 동결 package의 routing·route_target·controller를 사용했다. 현재 agent controller를 복제해 같은 speed와 nominal previous-steer를 넣었으며, 공개 helper의 steering 수식을 대신 쓰지 않았다. 원래 각 출력과 full actor state/memory를 먼저 재현한 뒤 직접 검출 입력과 비교했다. float32 출력은124–127에서 같고128에서 처음 달랐다. 129의 차이 크기를 보고 선택하지 않았다. 실제128 steering 변화는−0.0645839423이었다.

B의 reset 조건과 prefix1–127 명령·128개 입력 frame·actor/tracker state·nominal memory·수집 physics·접근 가능한 RNG를 검증했다. probe 계산 전후 상태 hash가 같았고 tracker 항목을 삭제하지 않았다. 같은128의 gas/brake 및 원래 controller의 nominal-memory 갱신을 보존했다. 129 이후에는 B의 자기 관측에서 원래 후보가 반환한 모든 제어를 실행했다. A의 후속 저장 명령을 강제하지 않았다. 정책 archive는 그대로이며 관측기의 순수 probe 연산만 추가됐다.

| 실제 공통 구간 1–136 | 재사용337 A | 신규 B |
|---|---:|---:|
| 첫 collision event | 132 | 132 |
| collision event 행동 | 132만 | 132–136 |
| damage | 0.2 | 1.0 |
| 고유 tile | 132 | 134 |
| 132 tile 이후 추가 진행 | 0 | 2 |
| 끝점 속도 | 1.388m/s | 7.664m/s |
| 공통 끝점 공식 종료 | 없음 | crash136 |

양쪽 모두 같은 장애물(index2)의 hull fixture touching이132–136 관측 끝점에서 유지됐다. B에는132번째 앞 wheel fixture contact도 기록됐다. collision event flag와 물리 touching 끝점은 다른 자료이므로 단순히 ‘독립 충돌5회’로 재해석하지 않았다. A 전체 기록은233 off_track이지만 B는136 공식 terminal에서 멈췄으므로 B의137–233 관측·명령은 만들지 않았다. B는 censoring이나233 protocol stop이 아니라 실제 DNF이며 finish flag·lap time은 없다.

damage 증가만으로 판정하지 않았다. B가2 tile 더 이동한 점도 보존했고, 같은 첫 접촉과 접촉 지속, 더 이른 공식 crash를 함께 비교했다. 이 특정 첫 steering 개입만으로 충분하다는 가설을 지지하지 않는 결과다. ‘막힘 양상이 완전히 같았다’고 주장하지 않는다. near-path/far-target의0.549rad 차이는 곡선 경로에서 정상일 수 있으며 결함 기준이나 개입 선택 기준으로 사용하지 않았다.

이번 비교는 후향적으로 선택된 기존 TRAIN N2 한 지점의 한 명령 시험이다. 전체 current-direct-only tracker의 효과나 일반 안전성은 검증하지 않았다. 원래 detector·radius·age·expiry·dedup·routing·controller·모델·lookahead는 바꾸지 않았고 학습·새 threshold·sweep·pedal 개입·새 도로·보호 split·승격은 없다. GT는 평가기 진단에만 썼다. OpenCV 숨은 RNG와 Box2D solver 내부 상태는 직접 측정하지 못했다.

상한233을 기존 연구1805 안에 사전 등록했고 추가 연구 예산은0이었다. 공식 crash에 따라 실제136 native에서 중단해 연구 잔여는1669다. 누적native1,282,569, 총 B1,368,238, 최종 예비84,000 보존이다. raw step544 tick/reset51 tick, wall17.133초/evaluator CPU15.249초/actor CPU1.877초, capture wall6.571초였다. cached actor128회와 실제 동결 routing/controller10호출은 wall2.318초였고, 실제 probe는2호출이었다. 초기 hash/data loading·build·최종 검증/보고 등 미계측 범위도 기록했다. 별도 source physics rollout·유료 자원은 없다.

다음 조치는 저장된 접근 영상에서 미해결 검출의 출생·보존·경로 의존성을 native0으로 분리하는 검토로 제안만 남겼다. 더 큰129 출력으로 자동 이동하거나, 단일 명령의 부정 결과만으로 기억 전체를 제거하거나, 속도·lookahead를 조정하지 않는다. 더 긴 기억 입력 개입을 시험하려면 별도 paired 계약이 필요하다. 이번338에서 다음 native는 실행하지 않았다.

334의 전체 최근접 집계 악화와 사후 fixture 대응 subset 개선을 모두 보존했다. 실제 가림 보존은 여전히 미검증이다. champion296·TRAIN registry·사용자 변경·main·backup·Participants·DEV/HOLDOUT/SEALED를 보존했다. 원문·회고·추출본·raw GT·pixels·모델·private seeds는 공개하지 않았고, 공개 파일은 일반 코드와 집계 결과뿐이다. 승인 종료는2026-10-17 19:01:55 KST다.
