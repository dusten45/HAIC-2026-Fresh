343의 결과는 **의도한 차량 근처 제어 효과에 미노출·불충분**이다. 새 O2 baseline A와 정확한 342 규칙 B를 각각 독립 reset에서 160 native까지 실행했다. B의 관측 조건은 137 출생점에서 활성화되어 137–145에 hard routing footprint를 보류했지만, 경로·target·목표 속도·전체 제어·정상 명목 메모리는 한 번도 바뀌지 않았다. 따라서 규칙에 대한 국소 유해 반례도, 회피 안전성 통과도 아니다. 과거 영상의 146 개입이나 상한 연장을 강제하지 않았다.

두 arm은 current334ON/H1과 동일한 동결 모델·detector·tracker·association·dedup·age·expiry·near scheduling·장애물 수·최소 거리 특징·controller·lookahead를 사용했다. 차이는 정확히 342의 픽셀 도로 이웃 지지 0 표시를 routing 입력에 적용하는지뿐이다. 과거 O2 수집 정책이 다르므로 A를 새로 실행했다. GT는 저장·사후 평가에만 사용했고 actor 입력이나 실제 진행 중단 조건에 쓰지 않았다.

처음 전체 제어가 자연스럽게 달라지기 전까지 reset·도로·명령·픽셀·actor·tracker·수집 physics·확인 가능한 RNG를 비교하도록 등록했다. 실제로 제어 차이가 발생하지 않아 **160개 명령과 161개 입력이 끝까지 일치**했다. source raw tick마다 읽기만 한 접촉 fixture·시각·hit 상태·위치·속도·타일 기록도 같았다. 두 arm은 모두 자기 반환 제어를 그대로 실행하고 자기 정상 명목 메모리를 갱신했다. 저장 명령·146 개입·명목 메모리 override는 없었다. 숨은 solver 상태와 OpenCV 숨은 RNG를 직접 측정했다는 주장은 하지 않는다.

| 실제 구간 1–160 | A | B |
|---|---:|---:|
| native / reset | 160 / 1 | 160 / 1 |
| collision event | 0 | 0 |
| raw collision flag | 0/640 | 0/640 |
| 관측된 fixture touching | 없음 | 없음 |
| damage | 0 | 0 |
| 고유 타일 | 161/289 | 161/289 |
| 끝점 속도 | 47.511m/s | 47.511m/s |
| off-track counter | 0 | 0 |
| 공식 retirement / finish | 없음 / 없음 | 없음 / 없음 |
| 기록 상태 | 160 protocol censor | 160 protocol censor |

모든 raw step의 0.02초 끝점에서 fixture 쌍과 hit 상태를 관측했으며 새 hit·touching 구간은 없었다. 접촉 fixture·최초 시각·지속 기록은 따라서 빈 목록이다. 이는 관측된 raw endpoint와 실제 collision flag의 결과이며 숨은 solver substep의 정밀 접촉 시간표를 발명하지 않았다. 두 arm 모두 마지막 160까지 타일 진행이 있었으나 finish flag와 lap time은 없다. damage 0이나 생존을 공식 성공으로 바꾸지 않았다.

실제 새 관측에서 선택된 것은 137단계의 면적 6 출생점 하나였다. 출생 시 사후 기하 라벨은 미해결이고 GT와 멀다는 이유로 오검출 정답을 만들지 않았다. B는 이 계보를 원래 age 8까지인 137–145 동안 tracker에 남긴 채 routing에서만 보류했다. 원래 만료는 다음 146 입력에서 일어났다. 과거 수집 영상의 146 차량 근처 출생점과 같은 점이라는 가정을 하지 않는다. 현재 정책의 방문 상태가 달랐다는 사실이 이번 노출 설계의 한계다.

보류된 현재 점과 A의 선택 경로 사이 최소 중심 거리는 3.8268m로, 기존 router의 2.6m+관측 반경 1.2m 여유보다 최소 0.0268m 바깥이었다. 이 값은 결과 설명용이며 새 cutoff가 아니다. footprint 보류가 선택 경로·제어를 바꾸지 않았다는 실제 기록과 함께 해석했고, 연속 차량 swept clearance나 장애물 안전성을 입증하는 수치로 쓰지 않았다. 사후 fixture 지지 출생·직접 검출의 routing 누락은 0이지만, 효과에 미노출된 pair이므로 유해성 가설을 기각할 수 없다.

| 비용 | A | B | 합계 |
|---|---:|---:|---:|
| 실행 wall | 19.079s | 18.628s | 37.706s |
| 부모 process CPU | 16.374s | 16.157s | 32.532s |
| actor CPU | 2.670s | 2.473s | 5.144s |
| reset wall | 0.483s | 0.515s | 0.998s |
| 실제 raw step+render wall | 7.410s | 6.593s | 14.003s |
| raw 접촉 관측 wall | 0.201s | 0.181s | 0.381s |
| pre/post capture wall | 6.889s | 6.368s | 13.256s |
| journal wall | 0.171s | 0.187s | 0.358s |
| 압축 저장 wall | 0.028s | 0.026s | 0.054s |

실제 raw step은 640 tick씩 총 1,280, reset은 51 tick씩 총 102였다. 관측기는 각 원래 raw.step을 정확히 한 번 호출한 뒤 읽기만 했고 별도 source physics rollout은 0이다. raw step 시간에는 render가 포함되므로 순수 solver 비용으로 부르지 않는다. 전체 wall에는 startup·hash·IPC 등도 포함되며 일부 초기·최종 검증·코딩·보고는 위 sub-timer 밖이다. 기술 오류와 복구 native·추가 reset은 0이었다. 새 threshold·추가 arm·학습·다른 split·추가 예산·유료 자원은 없다.

연구 비용은 등록 상한 그대로 **320 native와 환경 reset 2회**였다. 누적 native 1,283,122, 연구 잔여 1,116, 최종 예비 84,000, 총 운영 상한 1,368,238을 보존했다. 160 이후 새 실행·자동 연장은 없었다.

다음 최소 실험은 **native 0의 source-policy 노출 캐시 확인**으로 제안한다. 기존 O2의 첫 160개 저장 입력에서 실제 그 영상을 만든 동결 296 수집 정책 baseline과 동일한 도로 이웃 지지 0 규칙을 한 번씩 비교한다. 정확한 비용은 저장 정책 actor 320회, 저장 픽셀용 actor reset 2회, native·환경 reset·학습·sweep 0이다. 먼저 원래 수집 제어·특징·정상 메모리를 재현하고, 원래 source tracker의 계보 메타데이터만 따르며 tracker·모델·규칙을 바꾸지 않는다. 지지점 누락·재현·무결성 실패면 중단하고, 다시 미노출이면 불충분으로 남긴다. 아직 실행하거나 예약하지 않았다.

이 캐시의 정보 가치는 과거 차량 근처 반증 대상이 해당 영상을 실제 만든 정책에서 자연스럽게 제어에 영향을 주는지를 확인하는 데 있다. 현재334ON/H1의 방문 상태와 과거 영상이 다르므로, 그 상태를 현재 정책이 도달한 것처럼 취급하지 않는다. 다음 캐시는 baseline 맥락을 명시적으로 바꾸는 별도 질문이며 343을 재해석하거나 규칙을 tuning하는 작업이 아니다. 노출을 확인하면 실제 검증을 별도 설계할 수 있으나, 캐시 자체로 회피·현재 H1 안전성·완주를 주장하지 않고 새 native를 자동 승인하지 않는다.

한 번의 알려진 TRAIN 도로 비교이며 실제 가림·재질 안전성은 계속 미검증이다. 334의 전체 지표 악화와 사후 subset 개선을 함께 보존하고 champion296·main·backup·공식 Participants·사용자 변경과 DEV/HOLDOUT/SEALED를 유지했다. 일반 코드와 집계만 공개하며 원문·개인 자료·회고·추출본·raw GT·픽셀·모델·private seeds는 공개하지 않았다. 승격은 없고 승인 종료는 2026년 10월 17일 19:01:55 KST다.
