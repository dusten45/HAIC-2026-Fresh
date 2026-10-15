344는 **과거 O2 source-policy의 캐시 노출을 확인했다.** 실제 그 영상을 생성한 동결 296 정책에서 342의 고정 관측 규칙 하나만 추가하면 146의 경로·target·목표 속도·전체 제어가 달라졌다. 실제 주행이나 안전성·완주 개선을 검증한 결과는 아니다. 343의 current334ON/H1은 160까지 제어 효과에 미노출됐다는 결과도 그대로다.

source는 과거 306 O2 collection의 job, archive, ready 기록으로 식별했다. 원본은 `submission296.zip`의 SHA-256 `0a6c5e28…404a937`과 당시 `pedal306_worker.py` 조합이며, 역사적으로 로드된 모든 policy module hash가 일치했다. H1/current334ON으로 바꾸지 않았다. 원본 tracker는 optical 실패 시 HUD speed로 y만 이동하는 기존 fallback을 사용했다. 정책을 고친 것이 아니라 계보 표시 메타데이터가 이 원래 변환을 따르도록 했으며, 출생 성분의 1픽셀 8방향 도로 이웃 지지 0 조건은 342와 동일하다.

후보를 실행하기 전에 baseline 160개 입력에서 원본 명령·특징·nominal action·명목 메모리와 qualified 334 OFF tracker·경로를 모두 재현했다. 원본 trace에 전체 actor pickle이나 RNG snapshot은 저장돼 있지 않다. 따라서 그것까지 저장 원본과 일치했다고 주장하지 않았다. 당시 worker의 5개 상태 항목인 previous steer, lateral acceleration, hazard hash, previous-image hash, history hash는 원본 픽셀·검증된 tracker·원래 명령 이력·동결 source 상수로 재구성해 비교했다. 저장된 명목 메모리와 독립적으로 재구성한 상태 계약의 검증을 구분했다.

같은 원본 입력 160개에 baseline과 단일 후보를 적용했다. 두 arm은 자기 반환 제어 이력과 정상 명목 메모리를 사용했다. detector·tracker·association·dedup·age·expiry·near 일정·장애물 수·최소 거리 특징·동결 모델·controller·lookahead는 유지했다. actor는 기존 픽셀 전용 제한 안에서 실행했고 GT는 사후 평가기에만 있었다. 단계·좌표·GT·미래 관측은 규칙 조건에 없으며, 반경·밝기·면적 cutoff 탐색이나 추가 arm도 없다.

| 관측 항목 | 변화 구간 |
|---|---|
| 선택된 출생 계보 | 146, direct index 0, 면적 4, 도로 이웃 0 |
| hard routing footprint 보류 | 146–148 |
| 경로·target·목표 속도 | 146만 |
| float32 조향·페달·전체 제어 | 146–153 |
| 명목 메모리 | 146–160에서 관측, 이후는 미확인 |
| float32 제어 무변화 | 1–145 및 154–160 |

146에서 target은 baseline (−10.7649, 7.4361)에서 후보 (−10.5090, 7.8193)m로, 목표 속도는 7.906에서 8.011m/s로 바뀌었다. 최대 조향 차이는 약 0.002562rad였다. 이 크기가 작다는 이유로 안전성을 인정하지 않았다. 147부터 같은 고정 픽셀의 경로·target은 같아졌지만, 이전 조향을 사용한 정상 메모리의 재귀 효과로 제어 차이가 이어졌다. 154–160의 float32 제어는 같아도 float64 명목 메모리는 160에서 약 4.20×10⁻¹³ 차이가 남았다. 저장 범위 뒤 수렴을 관측한 것으로 쓰지 않았다.

선택된 출생점의 사후 기하 라벨은 여전히 미해결이며 false-positive 의미 정답은 아니다. fixture 지지 직접 검출 48개와 지지 출생 보존점 문맥 35개에서 routing 누락은 0이었다. 실제 RGB·의미 재질·가림 라벨은 없고, 이 표본에서 누락 0이라는 사실은 실제 잘리거나 가려진 장애물의 안전성을 보장하지 않는다. 실제 과거 O2 궤적은 baseline의 기록일 뿐 후보 캐시의 실제 궤적이 아니다.

343과 344는 같은 실험을 재판정한 것이 아니다. 343은 current334ON/H1의 실제 관측에서 137 출생점을 보류해도 제어가 같았던 실제 pair이고, 344는 원본 296 정책이 실제 생성한 과거 픽셀에서 노출을 확인한 별도 캐시다. 정책 맥락·방문 상태·원래 tracker fallback의 차이를 숨기지 않았다. 343의 미노출을 유해성 기각으로 바꾸거나, 344의 제어 차이를 실제 회피 개선으로 확대하지 않는다.

비용은 actor **320회**, 저장 픽셀용 actor reset **2회**로 상한을 지켰다. baseline 160을 먼저 완료·재현 검증한 뒤 후보 160을 실행했다. 기술 오류·복구 호출·복구 reset은 0이었다. actor phase wall 합계 5.405초, 부모 process CPU 1.311초, actor CPU 4.099초였고 source 식별·preflight·별도 원본 검증·코딩·보고·git 점검은 전체 계측이 아니다. 새 native·환경 reset·source physics·학습·sweep·유료 자원은 모두 0이다. 누적 native 1,283,122, 연구 잔여 1,116, 최종 예비 84,000을 보존했다.

다음 가장 작은 완전한 live-prefix 반증은 **동결 원본 296 baseline과 동일 규칙 후보를 O2에서 각각 새 reset으로 최대 160 native** 실행하는 pair로 제안한다. 최대 비용은 320 native와 환경 reset 2회이며, 현재 잔여에서 최대 사용 뒤 796이 남고 예비·추가 예산은 쓰지 않는다. 원본 collection에는 전체 actor pickle·확인 가능한 RNG snapshot이 없어, 이번 캐시만으로 그것까지 저장돼 있다고 간주해 과거 A를 완전한 live-prefix 기준으로 재사용하지 않는다. 이 결손을 피하는 두 fresh arm의 조건을 명시했다. 아직 실행하거나 예약하지 않았다.

이 pair는 343에서 빠졌던 source-policy의 차량 근처 노출에 대해 실제 새 접촉·막힘이나 지지점 누락이라는 국소 반례를 찾는 데 정보 가치가 있다. 원본 296의 detector·tracker·모델·controller·fallback은 두 arm에서 고정하고, 실제 reset·명령·픽셀·actor·tracker·수집 physics·확인 가능한 RNG를 최초 자연 분기까지 검증한다. 과거 픽셀과 146은 추가 reference일 뿐 개입을 강제하지 않는다. 이후에는 자기 관측·전체 제어·정상 메모리를 사용하며 공식 종료·160 상한·게이트·승인 종료 중 먼저 도달하면 멈춘다. 다시 노출이 없으면 불충분으로 남기고 자동 연장하지 않는다. 접촉 fixture·시각·지속, damage, 타일 진행, 속도, 공식 retirement·finish를 함께 비교하며 160 생존은 finish 없는 protocol censor다. 다른 baseline 맥락의 결과이므로 current H1·전체 도로의 안전성이나 완주율로 일반화하지 않는다.

334의 전체 지표 악화와 사후 subset 개선, 실제 가림 미검증을 유지했다. champion296·main·backup·공식 Participants·사용자 변경·DEV/HOLDOUT/SEALED는 보존했고 승격이나 새 주행은 없다. 일반 코드와 집계만 공개하며 원문·추출본·개인 회고·raw GT·픽셀·모델·private seeds는 올리지 않았다. 승인 종료는 2026년 10월 17일 19:01:55 KST다.
