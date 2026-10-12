237 — 동결affine 위의 작은 identity/tanh 페달 추가 보정

**identity 2/2, tanh 2/2 실제DEV완주.** 아래주행은학습에포함된F0/F1 비교이며독립검증이아니다. 현재챔피언232를유지한다.

| DEV | 과거232 | identity | tanh | tanh−identity 공동완주 | damage identity/tanh |
|---|---:|---|---|---:|---|
| F0 | 27.40초 | 27.58초 | 27.46초 | -0.12초 | 0.2/0.4 |
| F1 | 25.40초 | 25.26초 | 26.04초 | +0.78초 | 0.6/0.8 |

추가망은16→4→2의78trainable파라미터,affine base34와정규화32상수는고정했다. identity/tanh 이외에는같은구조·seed237·hidden Normal(0,.25)·bias0·outputweight/bias0·Adam(.01,betas.9/.999,eps1e−8)·정확히1,000fullbatchstep이다. 두arm 초기추가출력0과초기명령의기준일치를확인했다. earlystop·sweep·추가threshold/scaling은없다.

손실은 `Σ weight×(fixed affine raw residual + network − teacher-minus-nominal target)² + ||theta−theta0||²`다. sample/channel mean으로나누지않아기존229weighted-SSE와λ1스케일을유지했다. old/new 그룹각1/2·그룹내TRAIN도로균등,총가중치는oldTRAIN행수다. 학습은기존affine처럼raw잔차SSE이며명령오차/추론시에만합산잔차±.5·pedal[0,1]clip을적용한다. bias를포함한추가78변화에L2를걸며fixedbase를재학습하지않았다.

각LOO에서해당도로의old/new모두를제외했고기존229해당fold affine와TRAIN전용정규화를재사용했다. fullfit은기존231단일affinebase와전체DEV정규화를동결한채모두사용했다. 수치미분78개로gradient를확인했고실행패키지명령/특징/조향/nominal기억과실제모든명령의저장모델재계산도일치했다.

| LOO held도로 | base gas/brake MAE | identity MAE | tanh MAE |
|---|---|---|---|
| F0 | 0.286940/0.098857 | 0.286941/0.098865 | 0.283039/0.097930 |
| F1 | 0.270816/0.159765 | 0.270791/0.159770 | 0.271932/0.160784 |
| F2 | 0.270003/0.102590 | 0.270127/0.102581 | 0.261577/0.102245 |
| F3 | 0.278077/0.102060 | 0.278080/0.102049 | 0.272407/0.101319 |

오차는held-road old/new 그룹을각절반으로평가했고도로macro는네도로균등평균이다.

| 모델 | macro MAE gas/brake | macro RMSE gas/brake | 잔차clip gas/brake | pedalclip gas/brake |
|---|---|---|---|---|
| baseline | 0.276459/0.115818 | 0.316487/0.178051 | 0.000000/0.000371 | 0.000000/0.036549 |
| identity | 0.276485/0.115816 | 0.316489/0.178053 | 0.000000/0.000371 | 0.000000/0.036549 |
| tanh | 0.272239/0.115569 | 0.316089/0.179267 | 0.027526/0.002730 | 0.004751/0.048247 |

tanh의LOO오차는F0/F2/F3에서감소했지만F1에서증가했다. identity는기존affine와거의같고parameter수가같아도함수는affine다. 오프라인오차·학습목적감소를실제완주/시간개선이나일반화로같이취급하지않는다.

| fullDEV arm | 실제변화 파라미터(정확비영/>1e−12) | 최대절대변화 | 초기/최종weightedSSE | Δ파라미터L2 |
|---|---|---:|---|---:|
| identity | 78/72 | 0.000100147 | 182.725099/182.725080 | 2.85482e-08 |
| tanh | 78/78 | 0.592876 | 182.725099/171.054614 | 4.53276 |

LOO별각78변화·loss·clip·modelhash는JSON에함께기록했다. strict비영값과1e−12보다큰변화를구분했으며후자는수치진단이지추가승격장벽이아니다. identity의극소변화를학습미실행으로취급하지않는다.

주행순서는F0identity→F0tanh→F1tanh→F1identity, 공유상한2,000으로고정했다. 각도로두arm 초기관측/물리상태/geometry/장애물hash는정확히일치한다. F1과거234기준hash도일치한다. F0과거232는전체resethash가없어동일archive/조건·물리hash·reset-source provenance로대응을확인하고그한계를유지했다. 230의LOO 주행은fullsinglehead 기준으로혼동하지않았다.

검열0, 미실행[], 기술오류None. 손상은진단이며새승인기준/최소개선폭은없다. steering·16입력·nominal기억·clip설정은변경하지않았고236상호배제와228분류기는쓰지않았다.

비용: **native1,331/2,000, wall55.444초**, fit10회×1,000step wall1.760초·CPU1.755초. evaluatorCPU45.215초·actorCPU10.198초,rawstep/reset5,321/204틱. 전체Agent/IPC계산분포는JSON, 최대act IPC27.203ms·reset4.961ms이며원래공식5초제한은그대로다. 새GT질의/rollout·새자료수집0회.

승인연구량+2,000을B842,000→844,000으로기록했다. 시작757,964+2,036+84,000이후누적759,295+연구잔여705+예비84,000(사용0)=844,000. 지정클라우드·main·Participants·백업·사용자변경·마감2026-10-16 19:01:55 KST를유지하고HOLDOUT·SEALED·추가유료자원·챔피언변경·자동후속실험은없다. 원관측·label·학습model·archive는지정실행기비공개로유지한다.

[고정학습코드](addition237_fit.py) · [Agent](addition237_agent.py) · [일회실행](addition237_run.py) · [패키지builder](addition237_build.py) · [익명결과·비용](addition237_result.json)
