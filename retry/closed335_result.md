335의 실제 closed-loop B는 72행동 동안 contact·damage 없이 생존했다. 고정된334 fallback-only archive를 reset부터 사용하고, 자기 관측에서 계산한 steer/gas/brake를 매번 모두 실행했다. 기존 A는 contact68–72 후72번째에 crash했다. 이는 N2의 이 국소 구간에서 수정 tracker가 자기 방문 상태에서도 작동했다는 증거이며, 완주·일반화·champion 승격은 아니다.

| 공통 구간 1–72 | 재사용한 실제 A | 신규 B |
|---|---:|---:|
| 첫 contact / contact 행동 수 | 68 / 5 | 없음 / 0 |
| 끝점 fixture contact | 같은 장애물 hull 접촉 | 없음 |
| 최종 damage | 1.0 | 0.0 |
| 종료 | 72번째 공식 crash | 72 protocol stop |
| 고유 tile / 전체 | 70/292 | 73/292 |
| 끝점 속도 | 10.783m/s | 41.939m/s |

끝점 위치 차이는13.474m, B−A heading 차이는−1.368rad였다. A의 첫 contact 실제 시간은 [6.38,6.46]초 wrapper 구간이다. fixture는 저장된 wrapper 끝점만 관측한 범위이며 raw substep 전체 목록이 아니다. 원시 pose·속도·조향·페달·메모리·접촉·고유 진행량과 전후 물리 상태는 비공개 기록에 보존했다.

실행 전 기존330/331 A의 전체72명령·73관측·state/memory/종료 재현 근거와 source/config/hash를 확인했다. 새 OFF72 관측 재계산도 실제 A의 명령·features·메모리·직렬화 정책 상태를 정확히 재현했다. 새 ON72 캐시도334의 고정 픽셀 결과와 일치했다. A 자격이 명확하여 새 A를 중복 실행하지 않았고 자동144를 실행하지 않았다.

좌표·시간·reset·optical 보존·합법 정보 게이트를 통과했다. ON archive와 observer는334 그대로이며 추가 source 수정은 없다. actor에는 실제 픽셀/HUD와 자신의 메모리만 전달했다. GT는 평가기에서만 수집했다. 처음65개 실제 명령과66개 입력 stack이 A와 일치했다. 공통 구간에서 ON 정책 상태는 같은 입력의 자격 확인 캐시와 맞았고, 이용 가능한 물리 상태와 RNG도 비교했다. 초기 기본 pose 비교는333 B가 실제 측정한 동일 prefix를 이용했으며, 없는 과거 A의 초기 GT를 만들지 않았다. A의 실제 수집 physics는64 이후 따로 일치했다.

차이가66일 것이라고 강제하지 않았다. 실제 관측된 첫 명령·actor state·nominal memory 차이는66번째였고, 입력 픽셀 차이는67번째였다. 이후7행동 모두 steering/gas/brake가 각각 A와 달랐다. 메모리 갱신은 자기 관측에서 계산한 원래 controller 법칙을 유지했고 모든 반환 제어를 그대로 실행했음을 저장 기록에서 확인했다. 333처럼 steering66만 바꾸거나 후속 저장 명령을 고정한 실험이 아니다.

OpenCV의 숨은 RNG와 Box2D solver 내부 상태는 직접 측정하지 못했다. 접근 가능한 RNG는 기록된64 경계 및 reset 이후 step이 RNG를 사용하지 않는 source 계약과 비교했다. 실제 가림은 미검증이며 미검출을 가림으로 부르지 않는다. 72까지 contact가 없다는 결과로 이후 구간이나 다른 도로의 안전을 주장하지 않는다. damage를 독립 자동 veto로 쓰지 않았고, 공식 종료·진행량·접촉 지속과 함께 해석했다.

334의 혼합된 정적 증거도 그대로 유지했다. 원래6도로 전체 최근접 순차 평균은24.400→25.294m, 단일 fallback 최근접 RMSE는44.439→44.721m로 악화했다. 반면 사후 fixture 출생 대응 subset의 paired fallback 평균은4.640→2.752m, p99는19.486→13.674m로 개선됐다. 원래 이전 점1324개 중 이 대응이 있는 점은664개였다. 이번 국소 물리 결과가 미해결 대응이나 가림 보존을 해결한 것은 아니다.

연구 예산72를 별도 사전 등록해 총 B=1,366,199로 만들었다. 실제 신규 B72 native, raw step288 tick/reset51 tick, wall11.074초, evaluator CPU10.124초, actor CPU0.947초였다. 새 A는0회다. 사전 저장 관측 재계산144회는 wall3.492초/evaluator CPU2.101초/actor CPU1.859초였으며 native를 쓰지 않았다. 누적 native는1,282,199, 연구 잔여0, 최종 예비84,000 보존이다. 새 학습·별도 source physics rollout·유료 자원·보호 split 사용은 없다. 등록 전 구문 오류는 컴파일 단계에서 고쳤고 실험 재시도는 없었다.

다음 구분 실험은 제안만 남겼다. 고정 후보가72 이후에도 버티며 N2를 공식 완주하는지, 기존296 N2의 실제 완주363행동/29,000ms에 근거한 상한363으로 새 B 한 번을 reset부터 관찰한다. 이미 닫힌335 환경을 무료 재개하거나 teleport할 수 없으므로 검증된 prefix72와 이후 최대291을 모두 포함한 별도 연구예산363이 필요하다. 이 상한이 후보의 완주를 보장하지는 않으며 cap 도달 시 미완주는 protocol censoring이지 DNF가 아니다.

실행 전335의 실제72 prefix 재현과 archive/설정/메모리/물리/RNG를 재검증하고, 예상 밖 불일치·공식 종료·363 cap·승인 종료에 중단한다. reseed·sweep·자동 horizon 확대는 하지 않는다. 기존 OFF A 증거가 불명확하면 실행 전에 중단하고 추가 A72 비용을 별도 보고한다. 새 예산이나 다음 실험은 이번335에서 등록·실행하지 않았다. 공식 완주가 관측된 경우에만 N2 완주 개선을 말하고, 같은 TRAIN 한 사례로 일반화나 승격을 하지 않는다.

Champion296, TRAIN registry, 원본·사용자 변경, main·backup·Participants 및 DEV/HOLDOUT/SEALED를 보존했다. 공개 파일에는 일반 재현 코드와 집계 결과만 포함하며 비공개 문서·raw GT·pixels·모델·private seeds는 공개하지 않았다. 승인 종료는2026-10-17 19:01:55 KST다.
