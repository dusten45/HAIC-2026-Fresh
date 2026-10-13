# 290 — baseline 포함 discrete 3-action macro on-policy PPO

**고정 최종정책은후보0/8완주대240기준8/8로실패했다.** TRAIN0/6·freshscreen0/2이며8개모두실제DNF다. cap검열·기술오류·학습손실0이다. 중간checkpoint·samplingseed·macro크기·학습량을바꾸지않았고챔피언240을유지한다. 이결과는고정후보의평가이며categorical/macro방법전체의불가능성이나276대비단일원인효과를증명하지않는다.

새행동표현은baseline/gas-upper/brake-lower/steering+.015/steering−.015의다섯categorical class다. baseline class는exact240이며,선택한macro를최대3native동안유지하되매action현재pixel240명령을다시계산해한채널만개입했다. episode종료시즉시macro를끝냈다. 겹친개입·추가macro·크기탐색0이다.

실행전고정설정:적법feature16+자기최근action12의28입력,32-hidden tanh actor/critic,float64,actor1093/critic961parameters. 초기분포baseline.6/각macro.1,AdamLR3e−4각각,clip.1,KLstop.01,gradclip.5,4epochs·최대64decision/minibatch,entropy계수0이다. gamma1·GAElambda.95는macro decision단위다. 초기weightsseed290·training sampling29001·shuffle29002를고정했다. final은argmax로바꾸지않고학습categorical분포를**고정내부seed29007로episode마다reset해sampling**했다. road ID/GT state/progress/time은policy/critic입력에없으며GT는환경과공식reward에만썼다.

학습은새on-policy **16,373native·5,480macrodecision·16update**,38완주·27실제DNF·16collectioncut였다. native상한16,384의각1,024창에서완료된macro경계만cut하고1–2잔여slot은사용하지않는규칙으로총11native를남겼다. 44개짧은macro는실제terminal뿐이며terminal nextvalue0이다. cut은완료된3action의reward합과실제다음관측의value를bootstrap하고GAEcarry를끊었다. macro중간commitment를다른decision value로대체하지않았다. reward는기존complete`2−T/160`,DNF`p−1`목적의native증분합이며terminal합을실제결과와확인했다.

actor/critic각384optimizerstep을수행했다. initial→final parameter RMS변화는.01357/.05497이며모든update에서finitegradient·확률변화를확인했다. 최종훈련batch의평균분포는baseline.60190/gas.09127/brake.10293/steer+.10292/steer−.10098이다. 평균분포가초기prior와가깝고실제최종선택이안전성을보존하지못했다. critic의GAEtargetMSE를실제return정확성으로주장하지않는다.

새screen2개는학습전identity-only로등록·봉인했다. 이전screen과기존제외identity를피했고난도/성능선별0,학습에screen입력0이다. checkpoint16동결후에만screen을평가했다. final NumPy ZIP은host Torch와16개stochastic확률/macro/action/memory/history대조를통과했다. baseline class의학습action9,658건은원본명령과일치했으며전체16,373action의개입채널·history/memory경계를확인했다. 원시자료·모델·checkpoint·ZIP은비공개다.

| 최종후보 | 실제결과 | native |
|---|---|---:|
| O0 | off_track,damage .8 | 560 |
| O2 | crash | 393 |
| N0 | crash | 76 |
| N1 | crash | 446 |
| N2 | off_track,damage .4 | 163 |
| N3 | off_track,damage .8 | 186 |
| fresh S290-0 | crash | 377 |
| fresh S290-1 | off_track,damage .6 | 209 |

freshscreen의240baseline은23.52초/24.36초로둘다완주했다. 기존여섯TRAINbaseline은재사용해신규baseline주행0이다. 공통완주0이므로후보평균완주시간이나시간개선을계산하지않았다. 단일고정seed의stochastic최종주행각1회이며다른seed/argmax로결과를대체하지않았다.

실제비용 **19,382native =학습16,373+평가3,009**,총22,884상한내다. 평가에는8candidate2410+새screenbaseline599를포함한다. 학습runtime977.657초/CPU805.552초,평가193.211초/CPU161.303초,optimizer총.868초다. 별도actorCPU는학습172.064초/평가31.631초이며runnerCPU에중복합산하지않았다. 실제physics학습65,422tick·평가12,035tick,reset4,131/510tick. modelphysics·유료추가·예비사용0.

누적970,933 + 연구잔여9,067 + 최종예비84,000 =B1,064,000. main·Participants·백업·champion240·HOLDOUT·SEALED보존. 새학습/추가평가/seed선택을시작하지않았다. 공개는 `macro290_model.py`, `macro290_train.py`, `macro290_prepare.py`, `macro290_build.py`, `macro290_worker.py`, `macro290_finalize.py`, `macro290_eval.py`, `macro290_result.json`의코드와집계다.
