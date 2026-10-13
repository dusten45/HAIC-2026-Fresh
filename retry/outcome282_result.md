# 282 — 24 TRAIN 상태 outcome 수집 및 고정 작은 트리

**실제 개선 label은20/24상태에 있었지만, 고정 트리의도로별제외 선택은baseline보다못해 반복실행정책을시험할근거를확인하지못했다.** 후보label수집가능성과feature→안전한선택학습가능성은구분한다. 새정책주행·하이퍼파라미터탐색·챔피언승격은하지않았다.

여섯기존TRAIN길이의12.5%/25%/50%/75%에가장가까운유효query를결과확인전에고정했다.

| TRAIN | 고정 pre-action query |
|---|---|
| O0 | 37,73,148,223 |
| O2 | 34,67,130,196 |
| N0 | 37,73,148,223 |
| N1 | 28,52,106,160 |
| N2 | 34,67,136,202 |
| N3 | 28,58,118,175 |

각상태에gas-upper·brake-lower·steering+.015·steering−.015를현재pixel240명령의한채널에3action만개입한뒤실제pixel240으로공식종료까지주행했다. worker와macro공식은281그대로다. 실제반환steering memory·최근action history를검증했다. N0/N2의25%/50%16receipt를SHA확인후재사용하고나머지80주행만신규수집했다. 완료된주행은재시작하지않았다.

신규80건은**73완주·7실제DNF**, 검열0·비교불가0·기술오류/손실0이다. 모든prefix관측·명령·snapshot이정확히일치했다. 재사용포함96개macro결과는86완주·10DNF다. 기존no-change24개기준은모두완주다. baseline과네macro의완주/실패/시간을모두보존했다. label은실제공식시간이엄격히작아지는완주만택하며,baseline과동률이면baseline이다. finish는20ms physics tick시각을기록하고모든완주시간이해당해상도와일치했다. 임의최소이득문턱을추가하지않았다.

최선label분포는**baseline4,gas-upper4,brake-lower9,steering+3,steering−4**다. 도로별분포는집계JSON에있다. 기록된최선결과를사후선택한oracle는24/24완주·20개시간개선,평균−.1475초지만이는관측후최선선택의낙관적상한이다.

고정CART Gini·max_depth2·min_samples_leaf3을적법pixel feature16개만으로사용했다. sklearn추가설치없이결정적분할/동률규칙을구현했다. road ID는fold분리에만쓰고,action index·GT·미래결과는예측입력에넣지않았다. 한최종24상태fit과같은고정recipe의6개leave-one-road-out fit만수행했다. 최종fit의훈련정확도13/24는in-sample이며baseline예측5/24다. 훈련fit의선택분포는baseline5/gas5/brake14/steering±0이다.

| 저장된단일개입outcome조회 | 완주 | 실제DNF | 공통완주평균시간차 |
|---|---:|---:|---:|
| baseline | 24/24 | 0 | 0 |
| LORO 트리 | **22/24** | **2** | **+.0418초,22건** |
| 항상gas-upper | 20/24 | 4 | +.0180초,20건 |
| 항상brake-lower | 23/24 | 1 | +.0130초,23건 |
| 항상steering+ | 22/24 | 2 | +.1845초,22건 |
| 항상steering− | 21/24 | 3 | +.1038초,21건 |

공통완주평균은각전략에서완주한조건부부분집합이며실패를시간으로대입하지않았다. 실패포함전체평균완주시간은정의하지않는다. LORO 트리는정답label4/24(16.7%),abstain/baseline2/24이며선택분포baseline2/gas4/brake14/steering+0/steering−4다. 실제실패선택은N2 query136의brake-lower(crash),N3 query58의steering−(off_track)였다. 공통완주22건에서개선10·동률2·악화10이다. 반복정책으로확대하기전feature→선택의일반화와실패회피가해결되어야한다. 본평가는수집된snapshot에서단한번개입한결과조회이며반복정책성능이아니다.

신규비용 **20,098native =prefix8,436+macro240+continuation11,422**, 승인52,000이내다. baseline재주행0·모델physics0·기술손실0. 물리tick80,272·reset tick4,080. 여섯도로병렬elapsed574.099초,runnerCPU1,631.578초,별도actorCPU244.302초이며병렬elapsed에CPU/도로별시간을합산하지않았다. 분석.084초/CPU.078초,fit7회,새유료자원0.

추가배정46,000을한번반영했다. 누적947,898 + 연구잔여32,102 + 최종예비84,000 = **B1,064,000**. 예비사용0,챔피언240·HOLDOUT·SEALED·main·Participants·기존백업을보존했다. raw pixel/snapshot/trace·정확한트리threshold/모델은비공개이며공개는코드와집계뿐이다. 다음실험은시작하지않았다.
