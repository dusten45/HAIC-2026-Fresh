346은 **후보의 공식 완주 가능성을 확인했다.** 같은 O2와 동일한 296+342 고정 규칙으로 새 reset부터 실행해 **283 native에서 공식 finish**, lap time **22,620ms**, 고유 진행량 **281/289타일**을 기록했다. 300 상한까지 남은 실행은 하지 않았다. 이는 단독 후보의 한 사례 완주 결과이며 과거 기준선 대비 우열·안전성·일반화·승격을 주장하지 않는다.

345 B의 명령 160개·입력 161개와 actor 전체 상태·tracker·규칙 계보·정상 메모리·수집 physics·접근 가능한 RNG·raw tick 관측을 모두 재현했다. 이후 161–283은 자기 관측에서 반환한 전체 제어와 정상 메모리로 진행했다. 300은 이 160 prefix를 포함한 총상한이며 추가 300이 아니다. 저장된 후속 제어를 실행하거나 닫힌 world의 solver 상태를 snapshot으로 복원하지 않았다.

| 공식 결과 | 값 |
|---|---:|
| 실제 native / 등록 상한 | 283 / 300 |
| prefix 재현 / 이후 진행 | 160 / 123 |
| 환경 reset | 1 |
| 공식 finish | true |
| lap time | 22,620ms |
| 고유 타일 | 281/289 |
| 종료 이유 | official_finish |
| 실제 DNF / protocol censor | false / false |
| 첫 접촉 / 최종 damage | 46 / 0.2 |

종료 플래그는 terminated false, truncated true였지만 finish flag와 finish timestamp가 있으므로 timeout이나 protocol censor가 아니다. raw counter는 1,182/8,200으로 TimeLimit에 도달하지 않았다. finish qualification은 raw 22.90초, 소급 center-crossing finish는 23.64초, 선언 시각은 23.66초였다. post-reset 시작 1.02초를 뺀 **23.64−1.02=22.62초**가 lap time이다. 283×0.08초나 선언 시각으로 lap을 대신 계산하지 않았다. source의 qualification 후 center crossing 규칙이 공식 종료 기준이며 모든 타일 방문을 요구한 것으로 바꾸지 않는다.

접촉은 46의 장애물 0 fixture 0과 wheel index 3 fixture 0 한 건이었다. hit 시각은 raw 4.68–4.70초 구간이고 touching은 4.70·4.72초 끝점에서 관측됐다. 이후 새 접촉 event는 없고 damage는 0.2였다. 접촉·damage는 진단이며 이 값으로 공식 순위를 바꾸지 않는다. 마지막 속도는 46.811m/s, 마지막 타일 증가는 280단계였다.

고정 규칙은 146 출생점을 146–148, 새 203 출생점을 203–211에 hard routing 입력에서 보류했다. detector·tracker·원래 fallback·association·dedup·age·expiry·near 일정·장애물 수·최소 거리 특징·모델·controller·lookahead는 유지했다. 두 점 모두 사후 의미 라벨은 미해결이고 지지 출생점의 routing 누락은 없었다. 원래 도로 이웃 지지가 0이라는 픽셀 조건만 썼으며 단계·좌표·GT·미래 관측으로 선택하지 않았다. 완주했다는 사실만으로 실제 가림·재질 안전성을 보증하지 않는다.

실제 비용은 **283 native와 환경 reset 1회**, raw step 1,132 tick, reset 51 tick이었다. wall 27.499초, 부모 process CPU 24.487초, actor CPU 3.035초였다. reset wall 0.432초, 원래 raw step+render 9.610초, raw 접촉 관측 0.243초, capture 10.083초, journal 0.212초, 압축 저장 0.042초를 별도로 기록했다. 준비·hash·IPC는 전체 시간 또는 별도 범위에 있고 코딩·보고·최종 git 검증은 전체 계측이 아니다. raw 시간은 render를 포함하며 순수 solver 비용이 아니다. 추가 physics 진행·새 학습·sweep·유료 자원·기술 오류·복구 실행은 0이다.

누적 native는 **1,283,725**, 연구 잔여는 **513**, 최종 예비는 **84,000**이다. 등록한 300 중 미사용 17은 차감하지 않았다. 종료 뒤 자동 연장·새 split 개봉·champion 승격은 없다.

다음 가장 작은 유효 비교는 **새 원본 296 baseline A 한 번**, 최대 300 native로 제안한다. 이미 전체 실행이 검증된 346 B를 후보 arm으로 재사용하므로 B를 또 실행하지 않는다. 새 A는 345 A의 160 prefix를 재현하고, 동시에 346 B와 공유하는 reset·145 prefix의 actor·tracker·physics·접근 가능한 RNG를 직접 확인한 뒤 자기 관측·전체 제어·정상 메모리로 공식 종료 또는 300까지 진행한다. 이후에야 같은 O2의 공식 완료 여부와, 양쪽 완주 시 소급 lap time을 paired로 비교할 수 있다. 이번 346에서 그 비교를 이미 한 것처럼 보고하지 않았다.

다음 비용 상한은 **300 native, 새 A 1회·새 B 0회, reset 1회**, post-reset raw step 최대 1,200 tick이다. 현재 513에서 최대 사용 후 213이 남고 예비·추가 예산은 쓰지 않는다. 같은 모델·원본 tracker·고정 규칙을 유지하며 새 cutoff·arm·학습·split 변경은 없다. 공식 종료·상한·재현/무결성·승인 종료 중 먼저 도달하면 멈추고, finish 없는 상한은 censor다. 이 비교도 한 사례의 official objective만 다루며 일반 안전성·완주율·champion 채택으로 확대하지 않는다. 아직 실행·예약하지 않았다.

345의 노출된 국소 pair 검열, 343의 다른 정책 미노출, 344의 원본 정책 캐시 노출을 각각 보존한다. 334의 전체 지표 악화와 사후 subset 개선, 실제 가림 미검증도 유지했다. champion296·main·backup·공식 Participants·사용자 변경·DEV/HOLDOUT/SEALED를 보존했고 일반 코드·집계만 공개했다. 원문·추출본·개인 회고·raw GT·픽셀·모델·private seeds는 공개하지 않았다. 승인 종료는 2026년 10월 17일 19:01:55 KST다.
