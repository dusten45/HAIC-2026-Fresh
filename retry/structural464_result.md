# 464 — 저장 분석 종료, 다음 반증은 PulseOnce 대 지속 S13

**새 model/native 적분·world/reset·seed·학습·HOLDOUT·SEALED·예비·유료 사용0이다.** 463의0.220초 실제 이득은462 모델[0.20,0.24]초와 부합하지만13.780초는 기존442P 최선13.760초보다0.020초 느리다. 최선·원본·실패 기록을 유지했고 v475 연구26346/예비84000·사용0을 변경하지 않았다.

[하나의 다음 설계](design464_next.md)와 [기계 판독 계약](design464_next.json)은 H2A(reference/힘/경로 근사 정합성)와 H2B(시작점 FF의80ms hold)를 구분한다. H2A의 scaled gradient·allowance 잔차와 speed deficit은 실제 reference 불가능성 증명이 아니다. lateral/base allowance 비2.417은 같은 점질량/allroad/grip1 가정에서 nominal 총 마찰의 약0.967배 횡력 요구이며 exact 바퀴별 feasibility 판정은 없다.

선택은 **같은 첫 fullgas 후 PulseOnce(기존 nominal 복귀) 대 S13(매80ms secant 재계산)**이다. 이미 고정한pre126 root를 쓰며 다른 위치·seed를 찾지 않는다. 저장463 PulseOnce의13행동 상태에 순수 식을 계산하면 첫 명령은 같고 이후 상대3·10·13번째 명령이 달라진다. 따라서 추가 개입이 존재한다는 gate는 통과했다. 이것은 저장 상태의 대안 명령 계산이며 S13의 새 궤적이나 성능 예측이 아니다. 그13상태 모두 lookahead가 node를 넘고3개는 내부 reference valley를 포함했으며, 그 창에서 endpoint가 가속을 요구하면서 내부 target이 현재속도보다 낮은 경우는0이었다. 전체 저장 trajectory에서는 그런 노출도 있어 endpoint 평균의 한계를 보존했다. 현재 집계는 pre23 이전을 포함한 모든 적격 FIRST_LAP 경계라461의 pre23 이후 집계와 분모가 다르다.

기존 guardian shadow는 첫 명령 뒤 old nominal로 돌아가므로 지속 secant를 인증하지 않는다. 선택 계약은 guardian/랭킹 없는 모델 법칙 진단이며, 각 trajectory의13행동 전체가 자기 법칙을 사용한다. steering 정책과 실제80ms hold·gas ramp·공동 tyre clipping·raw 안전 기준을 유지한다. 정의역·기울기 전환·내부 valley·예견 감속의 한계와 전체 적용 시 terminal handoff를 문서에 명시했다. H13을 지나 full guarded 정책이나 native 안전을 인증하지 않는다.

최소 미래 비용은 old source/current/pending1242ticks/35worlds +두 arm의 독립 H13 각2회·held 첫 전이 각1회216/6, 합계 **1458ticks/41worlds**다. 같은4개 trajectory로 자격 확인과 사전 고정 반증 지표를 계산해 별도 main을 반복하지 않는다. 주 지표는root+60m의 raw20ms 통과 bracket 차이, 보조는 동일1.04초 진행·속도/reference·힘/경로·guardian 없는 안전/진행 결과다. 독립 반복과 모든 gate, strict 양의 통과 bracket 및 종료 진행 이득을 통과해야 다음 전체 model 계약의 설계 근거를 얻는다. 음수·겹침·미도달·typed physical 거절·unsupported 기술 중단을 구분한다. 임의 시간 문턱·neutral 구조·자동 승격은 없다.

현재 /tmp 여유 **3667374080B**, workspace 마지막 읽기 **921534464B**다. latest raw 비율은463의85798.438265B/tick과 world고정769473B로 갱신했다. hard2048/64 기준25% 여유·world고정 별도 가산·종료512MiB를 포함한 모델 공간은 **788063307B**다. workspace에는 압축률에 기대지 않는 전체 raw archive 몫·10%·metadata32MiB·reserve512MiB까지 **846736979B**를 잡았다. 현재 조건부로 들어가지만 새 구현/source manifest와 최신 free를 시작 직전 다시 확인해야 한다. 기존 파일 삭제·이동0이다.

반면 전체 guarded model의예시4parent×70행동은 **60402ticks/1157worlds**, hard65536 기준약8.456GB/tmp로 현재 공간에 들어가지 않는다. exact future-guardian 재귀·native 이전은 그 예시에도 포함하지 않았으며 승인된 실행이 아니다. 저장 제한을 H2B 기술 실패로 판정하지 않는다.

[순수 계산 코드](design464_math.py)·[저장 분석](analyze464.py)·[통합 gate](static464.py)를 남겼다. 순수 산식/정의역/내부 valley/전체 비용5개 검사와 저장 분석은 constructor·step·native world를 금지한 상태에서 통과했고 forbidden 호출0이다. source·입력31개와 보호18파일 해시를 확인했다. 저장 분석 CPU0.483초/wall0.493초, 그 분석을 포함한 gate0.489/0.500초이며 둘을 중복 합산하지 않는다. startup/import·개발/문서/Git 전체 overhead를 완전 측정한 값은 아니다. 현재5개 산식 검사는 미래 controller memory/phase 연결·fresh source 자격을 대신하지 않는다.

[집계 JSON](structural464_result.json)과 private 입력 manifest·저장 대안 명령을 보존했다. 초기 문서 snapshot과 검토 전 manifest를 유지하고, memory once/prepared-input 연결·명령 분기 이후 factual 범위 조건을 더한 최종 계약 해시를 별도 정산했다. 수치 분석을 중복 실행하지 않았다. [11분 checkpoint](structural464_progress.json)에 실험 worker 없음·새 적분0·검토 단계가 남아 있다. 새 원문 완독/방법군 소진은 주장하지 않는다. 최신 종료2026-10-20 19:01:55 KST 이후 새 실험·자동 연장 없음이다.
