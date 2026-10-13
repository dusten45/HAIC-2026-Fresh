# 291 — 실제pixel augmentation의 작은 return 예측 비교

**pixel추가모델은heldroad RMSE를3.26%줄였지만,완주episode오차와complete/DNF분리는개선하지못했다.** 작은수치이득은보존하되test2episode와모델구조차이때문에현재16feature가놓친유의미한시각병목을확정하지않는다. 큰pixel PPO·새정책·추가fit을시작하지않았다.

276의durable npz는28feature·latent/likelihood·reward·value/경계뿐이고290journal에도원pixel관측이없었다. hash/feature에서영상을복원했다고주장하지않고다른실행기의pixel과terminal label을붙이지않았다. 기존6TRAIN에서240/frozen290을각한번,12episode로새관측과feature/reward를같은실행에서함께수집했다. 개별cap합계6,000을먼저고정했으며actual3,398native로끝났다. 2406완주·frozen2906실제DNF,검열·오류0이었다. 이는영상자료수집이며290의seed/argmax성능구제실험이아니다.

각pre-action의실제4×84×84graystack을exact round-trip 확인후lossless uint8로저장했다. 모델입력은고정2×2averagepool의4×42×42과현재legal28이다. 28은현재240pixel-derived feature16+자기과거3actualaction/availability12이며roadID·policyID·GT·time/progress·samplingseed·미래frame을입력하지않았다. 대상은같은episode에서실제관측된native reward의suffix합이다. complete전체합`2−T/160`,DNF`p−1`을terminal까지확인했고censor label을추정하지않았다.

N2두episode를**통째로test**로빼고O0/O2/N0/N1/N3의10episode만fit/정규화에썼다. 매3번째pre-action과마지막preterminal을사용해fit999/test146row였다. 인접frame을fit/test로섞지않았다. episode동일가중으로fitmean/std·loss·오차를계산했고heldroad자료는정규화에도쓰지않았다. 기존behavior정책들은이미6TRAIN을사용했으므로이heldroad는새predictor의fit제외이며독립경쟁평가가아니다.

고정feature MLP는28→150ReLU→1(4,501parameter),visual은4채널Conv8/16(k3,stride2)→2×2pool→64concat28→32ReLU→1(4,473parameter)이다. 두모델모두새초기화seed291,Adam.001·batch64·gradclip1·20epoch/320optimizerstep·float32CPU1thread를한번만썼다. 학습checkpoint/epoch/architecture/가중치grid0이다.

| N2 episode 균등 test | 28 MLP | pixel+28 CNN |
|---|---:|---:|
| RMSE | **.90034** | **.87101** |
| MAE | .80043 | .73320 |
| bias | −.33404 | −.12477 |
| complete episode RMSE | .85096 | .89931 |
| DNF episode RMSE | .94714 | .84176 |
| complete/DNF sign정확도 | 84.36% | 83.45% |

전체RMSE는3.26%작아졌지만이득은DNF쪽에있고complete는악화했다. 두모델모두episode평균prediction의부호로두heldepisode를구분했으며pixel이새분리능을보였다고확정할수없다. RMSE신호를임의의5%문턱으로무효화하지않지만통계적유의성·반복정책성능을주장하지않는다. 146row는두episode내에서강하게상관돼146독립test로취급하지않았다. capacity는가깝지만architecture가달라pixel만의인과효과가완벽히분리되지는않는다.

혼합240/frozen290behavior에서같은초기관측의미래return이다를수있고미래macro/RNG commitment는입력에없다. 따라서realizedreturn의불확실성도있으며보편적conditional value나시각정보전체의불가능성으로해석하지않는다. 다음판단은시각이득미확정으로큰pixel PPO를보류하는것이다.

비용 **3,398native =240영상수집1,574+frozen290영상수집1,824**,cap6,000내다. collection190.560초/runnerCPU158.042초·별도actorCPU32.393초. 전체예측분석4.095초/CPU4.087초,실제fit wall은MLP.534초/CNN2.291초였다. 실제physics13,585tick·reset612tick,modelphysics·새정책학습·유료자원0.

누적974,331 + 연구잔여5,669 + 최종예비84,000 =B1,064,000. 예비·HOLDOUT·SEALED·새DEV0,champion240·main·Participants·백업보존. rawpixel/feature/target·정규화·모델/예측은비공개이며공개는 `vision291_prepare.py`, `vision291_collect.py`, `vision291_fit.py`, `vision291_result.json`의코드와집계다.
