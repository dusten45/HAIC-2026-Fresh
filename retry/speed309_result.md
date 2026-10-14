# 309 — legal 속도 오차 조건부 final pedal 배율 CEM

**TRAIN winner는 296이다.** 신규16개 후보×18 TRAIN의288개 공식 결과를 모두 관측했지만 최다 완주는16/18로296의17/18보다 적었다. 등록한 규칙대로 미개봉297 DEV12는 열지 않았고 champion296·240 rollback을 유지했다. 추가 후보·basis·반경·계수 조정·승격은 없다.

실제296 코드에서 같은 호출의 f[4]는 legal feedback speed v, f[6]는 선택 pixel target의 nominal goal q, f[0]는 target 없음 flag임을 확인했다. `e=clip((v-q)/6,-1,1)`, `w=(max(-e,0),1-abs(e),max(e,0))`를 고정했다. Gas/brake 각각 under/near/over 세 log multiplier를 두고 **원래296 final clip 이후** `clip(p*exp(w·theta),0,1)`로 반환한다. Target 없음 또는 비유효 finite/nonnegativev/q는 exact296을 반환한다. Head·기존 global scale·controller 계수·steering·직접 memory는 byte/동일호출 기준으로 보존했다. 나중의 trajectory와 따라서 steering stream까지 baseline과 같다는 뜻은 아니다. Zero theta는 저장된304개 실제 입력에서 행동·feature·memory가 정확히 같았다.

RNG309/PCG64, mean0, sigma0.04의 diagonal CEM 2세대×8개를 결과 전에 등록했다. 각 theta는 ±log(1.25)로 clip해 실제 배율0.8~1.25이며 재추출은 없다. Cached296 theta0를 archive에 포함했다. 완전 관측18개만 **완주 수 내림차순→자신의 완주 평균 시간→thetaL2→등록 순서**로 정렬한다. 각 세대 전체 완료 후 상위3 archive로 mean/variance를 old0.5·elite0.5(population variance) 갱신하고 sigma floor0.015를 적용했다. 두 세대 draw·clip·rank·elite·갱신·RNG state를 저장 기록으로 재현했다. Elite는1세대296/g1p2/g1p6,2세대296/g1p2/g2p2였다.

| 후보 | 완주 | 자체 완주 평균 초 | 추가/손실 vs296 | 공통 완주 | 공통 평균 Δ초 |
|---|---:|---:|---:|---:|---:|
| 296 cache | 17/18 | 22.894 | 0/0 | 17 | +0.000 |
| g1p1 | 13/18 | 23.568 | 1/5 | 12 | +0.527 |
| g1p2 | 16/18 | 22.796 | 1/2 | 15 | -0.475 |
| g1p3 | 14/18 | 23.023 | 0/3 | 14 | +0.621 |
| g1p4 | 11/18 | 23.271 | 0/6 | 11 | +0.384 |
| g1p5 | 15/18 | 23.199 | 1/3 | 14 | +0.319 |
| g1p6 | 15/18 | 22.456 | 1/3 | 14 | -0.533 |
| g1p7 | 11/18 | 23.073 | 0/6 | 11 | +0.318 |
| g1p8 | 13/18 | 22.737 | 0/4 | 13 | +0.428 |
| g2p1 | 12/18 | 22.443 | 0/5 | 12 | +0.335 |
| g2p2 | 15/18 | 22.408 | 0/2 | 15 | -0.443 |
| g2p3 | 12/18 | 22.595 | 1/6 | 11 | -0.085 |
| g2p4 | 14/18 | 22.680 | 1/4 | 13 | +0.197 |
| g2p5 | 12/18 | 22.802 | 0/5 | 12 | -0.370 |
| g2p6 | 12/18 | 22.938 | 0/5 | 12 | +0.403 |
| g2p7 | 13/18 | 23.515 | 0/4 | 13 | +0.532 |
| g2p8 | 12/18 | 22.263 | 0/5 | 12 | +0.178 |

새 후보 최상위는 g1p2 **16/18**, 자체 평균22.796초다. 추가 완주1·손실2, 공통15개 평균−0.475초였으나 완주 수 감소를 상쇄하지 않는다. 표의 자체 평균은 서로 다른 성공 도로 집합에 조건부라 전체18 평균이나 독립적인 속도 개선으로 해석하지 않는다. 공통 시간·추가/손실은 별도 진단이며 individual road·damage veto로 순위를 바꾸지 않았다. 새 후보의 실제DNF·기술 오류·검열·미실행을 구분했고, 이번에는 모든16 후보가 완전 관측이며 오류/검열0이다.

모든78,221개 행동에서 지정 basis·exp multiplier·최종 clip과 steer/memory를 확인했다. 유효 target에서77,103개 pedal 변경, target 소실 등 fallback1,118개는 같은 현재 상태의exact296이었다. 관측된 multiplier 범위는0.90965~1.10052로 고정 bounds 안이었다. Original296의 모델·head·controller/route/tracker dependencies와 base root가 모든 후보에서 그대로였으며288개 episode의 actor와 simulator process를 회수했다. 이 고정16개 탐색이296을 넘지 못했다는 결과이며 전체 조건부 제어나 다른 학습의 불가능성은 아니다.

실제 비용 **78,221/85,000 TRAIN native**, DEV **0/10,000**, raw step312,581 / reset14,688 tick이다. 전체 search wall **2,285.314초(약38.09분)**, runner CPU 합계3,105.166초·별도 actor CPU686.648초였다. 최대2개 병렬 episode wall 합계4,005.530초는 전체 elapsed와 다르다. Parameter draw16, source forecast physics·teacher·새 유료 자원0, unconfirmed charged native0이다. Zero-replay/문서/도구 orchestration 시간은 search wall과 별도다. Closure의 좌표 설명을 theta0-relative296 final-pedal로 고친 보고 필드 변경은 source 사본/hash를 보존했고 제어·recipe·결과나 native를 바꾸지 않았다.

승인된 연구+90,000을 반영한 종료 예산은 **누적1,226,459 + 연구 잔여19,541 + 최종 예비84,000 = B1,330,000**이다. 미개봉297 DEV12·HOLDOUT·SEALED·예비를 사용하지 않았다. Main·Participants·사용자 변경·기존 결과·백업·296과 이전 rollback chain을 보존했다. 공개는 일반 코드·집계이며 개별theta/model/ZIP·seed·raw trace·개인 문서는 비공개다. 자동 재튜닝·새 실험은 없다.
