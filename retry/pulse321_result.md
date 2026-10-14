321 — 선택된 세 도로의 joint pulse 성분 반증 완료

**Joint의 이득·손실을 한 성분으로 일괄 설명할 수 없었다.** T2950은 joint만 완주했고 steering-only A·brake-only B는 모두 실패했다. N2는 두 단독 arm 모두 완주했으나 joint는 실패했다. T2954는 A와 joint가 실패하고 B가 완주했다. 알려진 결과 뒤에 선택한 세 도로의 진단이며 일반화 검증이 아니다. 현재296과319/320의 원래 결과를 유지한다.

기존321 실행·등록이 없음을 확인하고 T2950/N2/T2954 및 두 arm을 결과 전에 고정했다. 319의 geometry·HUD·horizon·sampling·trigger·latch·수치·pulse 길이를 그대로 재사용했다. A는 같은 trigger에서 선택한 steering만 적용하고 원래 최종 gas/brake를 유지한다. B는 원래 최종 steering을 유지하고 gas0·brake `max(original,.5)`만 적용한다. B에서도 원래의 counterfactual steering 대안 gate를 그대로 계산하므로 B의 제동 효과를 기하 모델이 예측했다는 뜻은 아니다. Source physics·GT runtime·fit/PPO는 없다.

원래296과 joint의 세 도로별 native 중 큰 값은335/363/344로 합계1,042였다. 두 arm의 예상2,084에319의 도로별 최대 증가20×6=120을 더해 **2,204 cap**을 먼저 등록했다. 잔여456에 **1,748**을 추가한 v328의B총액은1,354,420이며 예비84,000은 보존했다. 이는 고정 여섯 평가에만 적용한 배정량이다.

평가 순서는 T2950 A/B, N2 B/A, T2954 A/B로 고정했고 정상 DNF 이후에도 나머지 arm을 건너뛰지 않았다. 모든 조건을 공식 ended/truncated까지각 한 번 실행했다. 같은 road의 A/B **전체 pre-action 픽셀 hash·controller/tracker state·previous image·hazard age**가 trigger에서 정확히 같았다. 319/320 joint의 개입 전 prefix 행동·feature·memory와 trigger의 base·HUD speed/yaw/joint·tracked obstacle·대안 score/선택도 정확히 일치했다. 예전 joint에는 전체 픽셀 hash가 없으므로 그 원시 픽셀을 새로 비교했다고 주장하지 않는다.

| 도로 / trigger | A 실제 변경 steering | 유지한 원래 gas/brake | B steering 유지·실제 pedal 변경 |
|---|---:|---:|---|
| T2950 /151 | −0.056311→−0.136311 | 0.465692 /0.036544 | steering−0.056311, gas0·brake0.5 |
| N2 /65 | +0.029698→+0.109698 | 0.395908 /0.055237 | steering+0.029698, gas0·brake0.5 |
| T2954 /82 | −0.146499→−0.226499 | 0.227011 /0.054888 | steering−0.146499, gas0·brake0.5 |

각 arm에서 실제 변경은 정확히1action이었다. A는 실행 steering을 memory에 기록했고, B는 원래 steering이므로 기존 nominal memory의 정확한 정밀도를 유지했다. 이후에는 각자의 실제 관측과 memory로 원래296을 실행했다. 설정·trigger·threshold를 결과 뒤에 바꾸지 않았다.

다음 표의 각 칸은 **공식 결과 / damage / 첫 contact action**이다. Baseline·joint는 검증된 기존 결과를 재사용하고 추가 주행하지 않았다. Baseline contact는300과 정확한294 g1p4 N2 trace에서 확인했으며 N2 archive·결과가 현재296 comparator와 일치했다.

| 도로 | 296 baseline | Joint319/320 | A steering-only | B brake-only |
|---|---|---|---|---|
| T2950 | off_track315 /0.2 /184 | **26.72초 /0 /없음** | crash193 /1.0 /184 | off_track319 /0 /없음 |
| N2 | 29.00초 /0.6 /65 | crash227 /1.0 /223 | **21.82초 /0 /없음** | **23.10초 /0.4 /66** |
| T2954 | 27.44초 /0 /없음 | off_track272 /0.2 /172 | off_track208 /0 /없음 | **27.98초 /0 /없음** |

선택 세 도로의 완주는 baseline2/3·joint1/3·A1/3·B2/3다. B는 baseline 두 완주를 모두 유지했지만 T2950 추가는 없다. 공통 N2/T2954 차이는 **−5.90초/+0.54초**, 평균 **−2.68초**다. A는 N2에서−7.18초였지만 T2954를 잃고 T2950은 crash했다. Joint가 완주한 T2950을 A/B가 모두 잃어 joint와 각 arm의 공통 완주 시간은 없다. 미완주 시간이나 다른 완주 집합의 평균으로 이를 대신하지 않았다.

T2954에서는 steering-only가 baseline의 완주를 잃고 brake-only가 유지해 steering 변경과 연관된 손실 증거가 있다. 그러나 N2는 어느 단독 성분도 완주를 잃지 않았고 **두 성분의 결합만 실패**해 단순한 한 성분 책임 설명을 반증했다. T2950은 어느 단독 성분도 joint의 구조 효과를 보존하지 못했다. 제동만으로 충분하다는 보편 결론도, 조향만 해롭다는 결론도 내리지 않는다. 성분 추가의 효과는 이후 closed-loop state 변화까지 포함하며 선형적인 기계력 효과 분리가 아니다.

후속 비교를 제안한다면 **B를 그대로 고정한 전체18 TRAIN 비교**에 한정할 근거가 있다. 이 진단에서는 두 joint 손실 도로를 보존하고 baseline 대비 공통 시간이 개선됐지만 선택 편향이 있으므로 아직 champion 개선은 아니다. A의 전체 확대나 joint 재승격은 제안하지 않는다. B의 이번 세 결과를 재사용하고 남은15개를 한 번씩 실행하는 비용 계획은 기존296의 해당15개 비용 **4,168 + 보수적20×15 allowance300 = cap4,468**이다. 잔여572 기준 추가 연구량은 **3,896**이며 예비는 쓰지 않는다. 이 계획을 이번에 등록·집행하거나 새 DEV를 열지 않았다. B의 모델 경고 품질과 전체 정책 성능은 별도로 검증해야 한다.

실측은 **native1,632/2,204**, raw step6,528·reset306틱, wall113.512초·runner CPU83.878초·actor CPU27.177초다. 공식 끝점6개·실제 DNF3·기술 오류0·검열0·미관측0이고 모든 actor를 회수했다. Baseline/joint의 기존6개 결과는 중복 청구하지 않았다. 새 source physics·fit/PPO·유료 자원·별도 파일 전송/첨부는0이다.

V329 원장은 **누적1,269,848 + 연구 잔여572 + 예비84,000 = B1,354,420**이다. 처음 등록한1,748 이외의 추가 확장0·예비 사용0이며296·240 rollback·main·Participants·backup·개인 원문을 보존했다. 일반 코드·집계만 기존 연구 브랜치에 commit/push하고 raw pixel·GT·state·ZIP·model은 비공개로 유지한다. DEV/HOLDOUT/SEALED·승격·자동 확대는 없다.

[성분만 분리한 Agent](pulse321_agent.py) · [고정 평가·동일성 검증](pulse321_stage.py) · [결과·contact·pulse·비용](pulse321_result.json)
