345에서는 **차량 근처의 자연 제어 분기를 검증했고, 160까지 국소 유해 반례는 관측하지 못했다.** 원본 296 A와 342의 고정 관측 규칙만 더한 B를 각각 새 reset에서 실행했다. 양쪽 모두 finish 없이 160 상한에 도달했으므로 완주·완주율 개선·일반 안전성 통과는 아니다. 343의 다른 정책 미노출, 344의 source-policy 캐시 노출과도 구분한다.

145개 명령과 146개 입력, 최초 분기 전 새로운 전체 actor pickle·controller·tracker 상태, 수집 physics와 접근 가능한 RNG가 일치했다. 146에서 규칙이 자연스럽게 전체 제어를 처음 바꿨고 첫 입력 차이는 147에 발생했다. 146을 강제하거나 과거 영상·다른 정책의 실행을 새 A로 대체하지 않았다. 새 A가 과거 원본 입력·명령과 일치한 것은 추가 reference 확인일 뿐 이번 비교의 기준선은 새로 실행한 A다.

B는 146 출생 계보 하나의 hard routing footprint를 146–148에만 보류했다. tracker·detector·원래 fallback·association·dedup·age·expiry·near 일정·장애물 수·최소 거리 특징·모델·controller·lookahead는 그대로다. 계보의 사후 기하 라벨은 미해결이며 의미적 오검출 정답으로 바꾸지 않았다. 지지 출생점의 routing 누락은 없었다. 분기 후 각 arm은 자신의 실제 관측에서 전체 반환 제어와 정상 명목 메모리를 사용했다. 저장된 후속 제어나 memory override는 없다. fresh actor 상태 hash와 최종 반환 제어 audit를 추가한 것은 측정뿐이며 규칙·정책 변경이 아니다.

| 실제 구간 1–160 | 새 A | 새 B |
|---|---:|---:|
| native / 환경 reset | 160 / 1 | 160 / 1 |
| 첫 접촉 | 46 | 46 |
| 추가 접촉 event | 없음 | 없음 |
| damage | 0.2 | 0.2 |
| 고유 타일 | 158/289 | 158/289 |
| 끝점 속도 | 45.362m/s | 46.360m/s |
| off-track counter | 0 | 0 |
| 공식 retirement / finish | 없음 / 없음 | 없음 / 없음 |
| 최종 기록 | protocol censor | protocol censor |

같은 접촉은 장애물 0의 fixture 0과 car body 4, 즉 wheel index 3의 fixture 0 사이였다. 최초 hit는 raw 시간 4.68–4.70초 구간에 기록됐고 touching은 4.70·4.72초의 두 raw 끝점에서 관측됐다. 이것은 0.02초 간격의 표본이며 연속 접촉 시간이 정확히 0.04초였다고 주장하지 않았다. 접촉과 damage 0.2는 규칙 분기보다 훨씬 이른 공통 prefix의 사건이다. 이를 후보가 새로 일으킨 damage로 해석하지 않았다.

분기 후 146–160에는 양쪽 모두 collision event와 raw fixture touching이 0이었다. prefix 끝의 146타일에서 158타일까지 각각 12타일을 더 진행했고 damage 증가도 없었다. 끝점 위치는 약 0.08787m 달라졌다. B의 높은 끝점 속도나 작은 위치 차이만으로 공식 순위를 바꾸지 않는다. 입력이 갈라진 뒤 경로·target·페달·조향·메모리 차이는 폐루프 전체 변화이며 각 변수의 독립 효과가 아니다. 실제 가림·RGB·재질 안전성은 여전히 미검증이다.

| 측정 비용 합계 | 값 |
|---|---:|
| 실제 native / reset | 320 / 2 |
| raw step / reset tick | 1,280 / 102 |
| 실행 wall | 36.724s |
| 부모 process CPU / actor CPU | 32.128s / 4.566s |
| reset wall | 0.992s |
| 원래 raw step+render wall | 13.920s |
| raw 접촉 관측 / pre-post capture wall | 0.386s / 13.097s |
| journal / 압축 저장 wall | 0.336s / 0.065s |

raw 관측기는 각 원래 step을 한 번 실행한 뒤 읽기만 했으며 추가 source physics rollout은 0이다. raw 시간은 render를 포함하므로 순수 solver 비용으로 부르지 않는다. 전체 wall에는 준비·hash·IPC 등이 포함되지만 일부 코딩·보고·최종 검증은 위 sub-timer 밖이다. 구현 오류·기술 검열·복구 native·추가 reset·학습·sweep·유료 자원은 없었다.

등록 상한 320을 모두 사용해 누적 native는 **1,283,442**, 연구 잔여는 **796**, 최종 예비는 **84,000**이다. 추가 예산·다른 split·새 threshold·추가 arm·champion 승격은 없다. 160 상한 뒤 자동 연장하지 않았다.

다음은 같은 160 pair를 반복하는 대신 **변경 없는 후보의 공식 완주 가능성만 확인하는 단독 B 실행**을 제안한다. 새 reset에서 실제 345 B의 160개 명령·161개 입력·전체 actor·tracker·수집 physics·접근 가능한 RNG prefix를 재현한 뒤 자기 관측·전체 제어·정상 메모리로 계속한다. 닫힌 물리 world를 불완전한 snapshot으로 재개하지 않으며, 재실행하는 160 prefix도 비용에 포함한다. 새 A나 과거 A를 이번 실행의 비교 기준으로 대체하지 않는다. 이 질문은 후보가 finish에 도달하는지이지 baseline 대비 개선·우열이 아니다.

최대 비용은 **300 native, 환경 reset 1회**, post-reset raw step 최대 1,200 tick이다. 원본 baseline의 역사적 finish 280에 사전 여유 20을 둔 평가 상한이며 제어 cutoff가 아니다. 최대 사용 후 연구 잔여는 496이고 예비는 그대로다. 345의 정확한 B config·observer RNG seed로 prefix를 검증하며 공식 finish·retirement·300 상한·무결성·승인 종료 중 먼저 도달하면 멈춘다. 상한 생존은 finish 없는 censor다. finish flag를 먼저 확인하고 완주한 경우에만 소급 center-crossing lap time을 보고한다. 새 접촉·touching·타일 진행·속도·damage·지지점 누락을 함께 기록하되 새 A가 없는 단독 가능성 확인이므로 paired timing·공식 순위 개선을 주장하지 않는다. 아직 실행·예약하지 않았다.

이 선택은 노출 자체와 짧은 구간의 유해 반례 여부는 이미 paired로 확인한 상태에서, 남은 ‘이후 공식 종료가 무엇인가’를 최소 한 episode로 구분하기 위한 것이다. 최대 300/796 native를 쓰고 496을 남긴다. 완료해도 한 도로의 완료 가능성일 뿐 current334ON/H1·전체 도로·실제 가림 안전성이나 champion 채택을 입증하지 않는다.

334의 전체 지표 악화와 사후 subset 개선을 모두 유지했다. champion296·main·backup·공식 Participants·사용자 변경과 DEV/HOLDOUT/SEALED를 보존했다. 공개 범위는 일반 코드와 집계뿐이며 원문·추출본·개인 회고·raw GT·픽셀·모델·private seeds는 올리지 않았다. 승인 종료는 2026년 10월 17일 19:01:55 KST다.
