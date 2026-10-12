228 — 배타적 페달 모드·강도 학생의 고정 대조

**동시 페달은 제거됐지만 F1·F2 모두 공식 DNF였다. 챔피언을 유지한다.** 모드 표현 변경은 226의 pedal-only 회귀가 완주했던 F2에서도 완주 개선으로 이어지지 않았다.

표적은 실제 float32 gas>0/brake=0을 gas, brake>0/gas=0을 brake, 둘 다0을 coast로 정의했다. 교사1392행은 gas1148·brake244·coast0·동시 양수0이었다. 세 logits를 유지하고 classweight·pseudocount·threshold·λ sweep은 없었다. Coast 표적이 없으므로 그 성능은 평가할 수 없고, bias비정규화 missingclass의 정확한 최적점은 유한하지 않다. 고정 BFGS의 유한 근사 gradient종료를 검증했으며 coast가 학습됐다고 주장하지 않는다.

16개 실제 적법 특징은224와 같다. 도로3개에서만 정규화한 multinomial logistic(sumCE+L2λ1,bias비정규화)과 각 gas/brake모드의 학습행만 이용한 ridge강도회귀(λ1,bias비정규화)를 사용했다. BFGS0초기화·400회상한·gradient∞≤1e-6·고정Armijo를 결과 전에 정했다. 네fold는68/71/93/90회에서 수치기준을 충족했다. Steering과 nominal내부기억은 원래normal24 그대로며, argmax모드의 한 강도만[0,1]clip하고 coast는0/0이다.

| held-out DEV | 실제 모드 오차: affine→새 표현 | gas MAE | brake MAE |
|---|---:|---:|---:|
| F0 | 84.51%→15.49% | 0.25293→0.25398 | 0.08255→0.04262 |
| F1 | 98.20%→17.07% | 0.21100→0.23506 | 0.08995→0.05679 |
| F2 | 92.28%→21.07% | 0.24939→0.26921 | 0.08424→0.05996 |
| F3 | 92.63%→18.41% | 0.24385→0.26259 | 0.07888→0.05333 |

위 실제 모드 오차는 최종float32출력의0/양수 기준이며 affine동시 양수는 별도의 invalid모드로 오답 처리했다. 새 classifier의 argmax오차는 F0~F3 각각14.67%·17.07%·21.07%·18.41%이고, 강도clip후0으로 바뀐 출력을 포함한 실제 모드 오차와 구분한다. Brake MAE는 감소했지만 **gas MAE는 네fold 모두 증가**했다. 모드 오차 개선 일부는invalid출력의 구조적 제거이며 실제 주행 개선으로 해석하지 않았다.

| DEV | 과거201챔피언 | 과거226pedal-only affine | 새 모드 학생 | 종료행동 / 방문 |
|---|---|---|---|---|
| F1 | 34.08초 완주 | DNF(off_track) | DNF(crash) | 46 / 31/299 |
| F2 | 31.60초 완주 | 23.02초 완주 | DNF(off_track) | 142 / 47/289 |

과거대조는 새reset의관측·물리상태·geometry·장애물·nominal챔피언hash가 일치했고 반복 실행하지 않았다. 새 두 주행은 공식종료까지 진행했으며 총950상한 검열은 없었다. 공통완주가 없어서 paired시간이득을 계산하지 않았다. F0·F3 native 실행은 없다.

| DEV | gas/brake/coast 선택 | 모드전환 | 동시페달 | 첫충돌 / 마지막새방문 | 최종speed / counter |
|---|---|---:|---:|---|---|
| F1 | 46/0/0 | 0 | 0 | 30/30 | 2.196885/16 |
| F2 | 142/0/0 | 0 | 0 | 39/41 | 11.010053/101 |

두 도로에서 모든 행동이 gas모드였고 brake/coast 선택과 모드전환은0회였다. F1은damage1.0으로 crash, F2는마지막새방문41 뒤101행동 무진행으로 off_track이었다. F2최종speed11.01m/s이므로 이 종료도 정지로 처리하지 않는다. 평균 gas/brake는 F1 0.4959/0, F2 0.6582/0으로, 강도와 모드분포가 기존회귀와 함께 달라졌다. 동시페달제거만의 단독인과효과를 분리한 실험이라고 주장하지 않는다.

| DEV | speed≤0.001 정지행동 | 움직일때 nearest-road-tangent 반대이동 | tangent부호변화 | 실제시작선중심 crossing |
|---|---:|---:|---:|---:|
| F1 | 0 | 7/44 | 2 | 0 |
| F2 | 0 | 48/142 | 14 | 0 |

도로진행방향 진단은 실제speed≥1m/s에서 가장가까운roadtile의전방tangent·velocity 내적을 사용했다. 교차로나nearesttile전환에 민감하므로 완주방향의확정판정으로 삼지 않는다. 공식tracker의폭안중심선crossing은 매rawtick 관찰했고 둘 다 없었다. 기존F1의자격후역방향crossing구간까지 도달한 비교가 아니며 GT진단은 학생입력에 없었다.

| DEV | 전체학생 계산 중앙값/p95 ms | IPC포함 중앙값/p95/최대 ms |
|---|---|---|
| F1 | 5.787/12.593 | 8.909/17.947/20.406 |
| F2 | 1.734/7.777 | 4.241/11.017/13.660 |

비용: native**188/950**, closed-loop wall9.091초, evaluator CPU7.631초·학생CPU1.409초. 오프라인4classifier+8ridge는wall/CPU0.176/0.175초·BFGS합계322회다. cachedqualification12호출은native0이었다. 모델탐색0, 추가학습/재튜닝0, head+normalization은fold당936bytes다. 관측·모델·명령·진단캐시는 지정실행기에만 보관했다. 공식runner·5초reset/act제한을 유지했고 전체호출초과0건이며, 기존격리평가기 사용을 공식runner전체동등성 인증으로 주장하지 않는다.

누적750,232+연구잔여768+예비84,000(사용0)=B835,000. 기존챔피언·main·Participants·백업·사용자변경을 보존하고220·222HOLDOUT·SEALED를 쓰지 않았다. 마감2026-10-16 19:01:55 KST·지정클라우드를 유지하고 자동후속실험은 없다.

[고정 학습 코드](pedal_mode228_fit.py) · [학생 worker](pedal_mode228_worker.py) · [고정 실행 코드](pedal_mode228_run.py) · [익명 결과·비용](pedal_mode228_result.json)
