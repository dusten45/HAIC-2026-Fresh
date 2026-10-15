347의 조건 일치 게이트를 통과해 공식 비교가 유효하다. **동일한 알려진 O2 조건에서 둘 다 완주했고, 원본 296 baseline A가 후보 B보다 260ms 빨랐다.** 이 사례에서 고정 규칙 후보는 공식 목적을 개선하지 못했다. 이를 전체 도로·실제 가림 안전성·현재 H1의 일반 성능으로 확대하지 않으며 champion을 승격하지 않았다.

이번에는 A만 새 reset에서 실행했다. B는 이미 검증된 346의 실제 283-action 기록을 재사용했으며 새 실행으로 세거나 다시 비용을 청구하지 않았다. archive·worker·모델·assets·나머지 config는 같고 차이는 고정 규칙 활성 여부뿐이다. 346에 고정한 환경 코드 hash, 초기화·case·RNG seed 및 runtime 제약을 유지했다. 실제 reset·초기 physics·RNG·정책 상태가 같았고, 분기 전 **145개 명령·146개 입력과 actor·tracker·physics·접근 가능한 RNG·raw tick 기록이 일치**했다. 자연스러운 첫 전체 제어 차이는 146이었다. 하나라도 불일치했다면 우열 비교는 무효이지만 이번에는 모두 통과했다.

새 A는 별도로 345 A의 160 prefix도 정확히 재현한 뒤 자기 관측·전체 반환 제어·정상 명목 메모리로 계속했다. 146을 강제하거나 이후 저장 제어를 실행하지 않았고 baseline·모델·tracker·lookahead·threshold를 바꾸지 않았다. 공식 종료가 300 상한보다 먼저 발생해 즉시 중단했다.

| 공식 결과 | 새 A | 기존 346 B |
|---|---:|---:|
| 이번 새 실행 | 1 | 0 |
| 해당 실제 episode native | 280 | 283, 기존 비용 |
| 공식 완주 | true | true |
| 공식 lap time | 22,360ms | 22,620ms |
| 고유 타일 | 285/289 | 281/289 |
| 접촉 event | 46에서 1회 | 46에서 1회 |
| damage | 0.2 | 0.2 |
| 실제 DNF / protocol censor | false / false | false / false |

lap은 post-reset 시작 1.02초에서 소급 center-crossing finish까지의 시간이다. A는 raw finish 23.38초에서 22.36초, B는 23.64초에서 22.62초다. finish flag를 먼저 확인했고 단순 action 수나 선언 시각으로 바꾸지 않았다. 둘 다 완주한 이 조건에서는 lap time으로 순서를 정한다. 고유 진행량·접촉·damage를 공식 순위의 대체 지표로 쓰지 않았다. 미래 완료 확률이나 다중 도로 순위를 추정한 결과도 아니다.

공통 접촉은 장애물 0 fixture 0과 car body 4, 즉 wheel index 3 fixture 0 사이였다. 두 기록 모두 최초 hit raw 구간 4.68–4.70초, touching 끝점 4.70·4.72초였고 추가 접촉은 없었다. 이는 분기보다 앞선 동일 사건이다. raw 0.02초 표본을 연속 solver 접촉 시간으로 발명하지 않았다. 숨은 solver와 OpenCV 숨은 RNG를 직접 측정했다는 주장은 하지 않으며, 수집 가능한 상태와 실제 공통 prefix의 일치를 증거로 삼았다.

기록상 qualification 시각은 A 22.32초, B 22.90초로 B가 580ms 늦었다. qualification 뒤 center crossing까지는 A 1,060ms, B 740ms로 B가 320ms 짧아 순 lap 차이는 260ms다. 이는 종료 시각의 산술 분해일 뿐, 146·203 계보나 특정 조향·페달이 독립적으로 몇 ms를 만들었다는 인과 분해가 아니다. 146 이후 실제 영상·경로·정상 메모리는 서로 달라진다.

이번 신규 비용은 **A 280 native, 환경 reset 1회**뿐이다. raw step 1,119 tick과 reset 51 tick, wall 39.403초, 부모 process CPU 35.529초, actor CPU 3.859초였다. reset wall 0.456초, raw step+render 12.057초, raw 접촉 관측 0.317초, capture 13.555초, journal 0.290초, 압축 저장 0.053초를 별도 기록했다. hash·IPC·준비·보고 등은 전체 또는 별도 계측 범위에 있으며 순수 solver 비용으로 부르지 않는다. 별도 source physics rollout·기술 오류·복구·학습·sweep·유료 자원은 0이다.

누적 native는 **1,284,005**, 연구 잔여는 **233**, 최종 예비는 **84,000**이다. 미사용 예약 20은 차감하지 않았고 346 B의 283을 다시 더하지 않았다. 새 split 개봉·승격·자동 추가 실행은 없다.

다음 최소 실험은 **native 0의 고정 상태 routing 진단**을 제안한다. 346 B에서 실제 보류가 있었던 12개 상태를 전부 사용해 각 상태에서 원래 filtered routing을 재현한 뒤 그 한 점의 footprint만 복원한다. 원본 296의 동결 routing·route_target에 같은 픽셀·속도·이전 조향·나머지 점을 넣는다. 비용은 routing 함수 **24회**, route_target **24회**, actor·native·환경 reset·학습·sweep **0**이다. original 경로·target 재현이 실패하면 기술 문제로 멈추고, 결과가 좋아 보이는 시점이나 새 cutoff를 고르지 않는다. 아직 실행·예약하지 않았다.

이 진단은 146과 새 203 계보가 각자 실제 방문한 상태에서 직접 routing에 영향을 줬는지와 이후 폐루프 결합 효과를 구분하는 저비용 근거다. A/B의 기존 raw 진행·qualification·finish 연대기도 함께 정렬하되, 260ms의 원인을 하나로 확정하거나 더 나은 threshold를 찾아 후보를 되살리는 작업으로 쓰지 않는다. 현지 비교에서는 후보가 개선되지 않았으므로 추가 native를 반복하기보다 연구 잔여 233을 기술적 contingency로 보존한다.

그와 함께 final readiness handoff에는 champion296 archive·manifest와 비승격 결정을 고정하고, 연구 233과 최종 예비 84,000의 회계를 분리해 둔다. 보호 split의 미개봉 sentinel만 확인하며 새 case 내용을 읽거나 개봉하지 않는다. 정확한 동결 artifact·공식 finish 지표·중단 조건으로 최종 검증 준비를 제안할 뿐 최종 검증을 자동 실행·예약하지 않는다. 실제 가림·재질 안전성과 다중 도로 일반화는 남은 불확실성이다.

334의 전체 지표 악화와 사후 subset 개선을 함께 유지했다. champion296·main·backup·공식 Participants·사용자 변경·DEV/HOLDOUT/SEALED를 보존했고 일반 코드와 집계만 공개했다. 원문·추출본·개인 회고·raw GT·픽셀·모델·private seeds는 올리지 않았다. 승인 종료는 2026년 10월 17일 19:01:55 KST다.
