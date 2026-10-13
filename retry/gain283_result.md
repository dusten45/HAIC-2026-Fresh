# 283 — 공식return 이득 ridge의 저장outcome LORO 진단

**실패 비용을target에넣어도 고정회귀선택은21/24완주로baseline24/24·282트리22/24보다나빴다.** 반복정책시험·추가수집·새정책평가를시작하지않는다. 목적함수를바꿔도현재작은표본의선택일반화문제가남았다.

기존24개상태·96macro outcome만사용했다. complete의return은`2−T/160`,실제DNF는`p−1`이며same-state no-change return을빼서네target을만들었다. 10개DNF 모두공식실행기에서직접저장한terminal receipt의visited/total_tiles가있어정확한progress를얻었다. per-action trace에는progress가없지만terminal result에측정된counts가있으며추정·보간·누락채우기0이다. 완주T는공식20ms해상도의저장lap_ms다. baseline gain은정확히0이다.

적법pixel feature16개만훈련fold mean/std로정규화한multi-output affine ridge **lambda1**을고정했다. intercept는비정규화하며정규화상수는훈련도로만사용했다. 0에가까운std<1e−12는1로처리했다. 각fold20상태의6LORO fit과최종24상태fit총7회,feature·lambda·threshold 탐색0이다. 예측이득의유일한양수최대macro만선택하고모두비양수거나정확한최대값동률이면baseline으로abstain했다. road ID는fold 분리에만사용했다.

| 동일24상태의저장outcome조회 | 완주 | 평균목적return차이 | 공통완주시간차 | abstain |
|---|---:|---:|---:|---:|
| baseline | 24/24 | 0 | 0 | 24 |
| 283 ridge LORO | **21/24** | **−.27584** | −.00095초,21건 | **8** |
| 282 tree LORO | 22/24 | −.19123 | +.04182초,22건 | 2 |
| 항상gas-upper | 20/24 | −.38853 | +.01800초,20건 | 0 |
| 항상brake-lower | 23/24 | −.08593 | +.01304초,23건 | 0 |
| 항상steering+ | 22/24 | −.19124 | +.18455초,22건 | 0 |
| 항상steering− | 21/24 | −.30096 | +.10381초,21건 | 0 |

목적return차이는실패를포함한전체24상태평균이며공통완주시간차이는각전략이완주한조건부부분집합이다. 실패의가상완주시간은넣지않았다. ridge의완주부분집합시간은거의동률이지만세실패로전체목적return은크게악화했다. baseline 평균return1.869104, ridge1.593263이다. ridge의sum return차이는−6.620188이다.

LORO 선택분포baseline8/gas5/brake5/steering+3/steering−3,목적return 개선7·동률8·악화9이다. 실제실패선택은N2 query67 steering−,N2 query136 gas-upper,N3 query58 steering−였다. 도로별abstain은O0/O2/N0/N1/N2/N3 각각0/2/1/2/2/1이다. 최종24상태fit은baseline10/gas4/brake5/steering+4/steering−1을예측했지만in-sample이다. 이평가는한번개입후pixel240으로돌아간기록의개발진단이며반복실행정책성능·독립평가가아니다.

신규native **0**,모델physics **0**,render/actor/새정책주행 **0**. fit·조회.1838초/CPU.1279초,export복구.0608초/CPU.0532초다. NumPy정수JSON직렬화오류1회를저장계수·예측으로복구했고추가fit0·native손실0이다. 7개훈련통계·normal equation과96개actual receipt hash를검증했다. 모델·정규화·raw target/progress·정확한예측은비공개에보존했다.

누적947,898·연구잔여32,102·최종예비84,000·B1,064,000을유지했다. 유료자원추가0,챔피언240·HOLDOUT·SEALED·main·Participants·백업보존. 코드는 `gain283_ridge.py`, 집계는 `gain283_result.json`이다.
