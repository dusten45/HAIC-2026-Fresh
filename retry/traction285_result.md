# 285 — source friction-circle 기반 rear traction 진단

**고정후보는확대하지않는다.** 검증가능한N0는24.10초완주로240의23.62초보다.48초느렸고,O0는303native실행후종료기록저장오류로공식완주/시간을확인할수없다. O0를재실행하거나결과를추정하지않았다. 계수수정·추가도로·학습·독립평가0이다.

선택한병목가설은**rear wheel과회전이종·횡공용마찰budget을낭비한다**는것이다. source는wheel forward속도와rim속도차이에82를곱한종힘과lateral속도×82의횡힘을같은friction circle로clamp한다.235/254에서구동·제동상쇄와launch force포화가능성이관찰됐지만전역pedal상쇄실험은완주/시간을개선하지못했다. PPO연장·lambda·소표본selector·yawfeedback도승격근거가없어,이들계수재조정대신**현재wheel상태에조건부인source 역산 traction allocation** 하나를선택했다.

현재pixel240의path·steering·final brake는그대로둔다. 각rear wheel의현재vf/vs/omega·마찰·손상효과를GT로읽어횡힘후남는`F_long=sqrt(max(F_limit²−F_lateral²,0))`를구한다. 다음첫tick의rim속도상한으로omega를정하고,source의dt.02·enginepower·관성·`15×brake`를역산한gas상한을구한다. 공통gas는원래240gas와두wheel상한중최솟값이다. gas증가rawtick상한.1도진단힘계산에반영한다. reverse/invalid wheel상태와brake≥.9에는원본을유지한다. gain·smoothing·값sweep없이고정했다. GT wheel조건을사용해적법후보가아니다.

실행전gate는O0/N0 **둘다공식완주하고각각시간이엄격히감소**해야같은고정후보를나머지네TRAIN에확대하는것이었다. 신규baseline·modelphysics·새환경·유료자원은없다.

| TRAIN pilot | native | 공식결과 | 240대비 |
|---|---:|---|---|
| O0 | 303 | 종료trace/receipt export실패,미확인 | 계산하지않음 |
| N0 | 302 | 24.10초완주,damage .4 | +.48초 |

N0 gas변경은14/302action,평균gas는현재호출240 .47839→반환 .46967이었다. 첫tick rear longitudinal force의마찰잔여상한초과추정은22/602wheel표본→2/602로감소했지만완주시간은개선되지않았다. 이는실제차량상태에서의첫tick대수적추정이며별도물리rollout이아니다. steering·brake·previous-steer memory는302action 모두보존했다.

고정후보의한계:한wrapper의네tick중첫tick만역산하므로이후속도·tile접촉·횡힘변화를보장하지않는다. 이미큰omega는gas를0으로내려도즉시없어지지않는다. 공통gas의두wheel최솟값은비대칭traction을희생할수있다. lateral힘이이미마찰을넘거나pixel경로추종이틀린경우gas상한만으로해결하지못한다. 결과는이후보를지지하지않으며traction병목전체의불가능성을뜻하지않는다.

O0의bulk trace를종료시에저장하던중NumPy bool JSON직렬화가실패했다. 비용303은durable budget에남았지만terminal·rawtick·actorCPU는남지않아결측으로표기했다. 기존실행을중복하지않고scalar타입만수정한후미실행N0를한번진행했다. 앞으로의수집에는per-action journal과summary우선저장을넣었다. action공식·계수변경0이다. 이저장오류는실제DNF나cap검열로분류하지않는다.

총비용 **605native**에저장실패303을모두포함했다. 측정실행phase wall26.319+27.319=53.638초,runnerCPU43.969초다. N0의durable물리tick1206·reset51,실패phase물리tick은미확인이다. 검증가능한N0는DNF0·검열0이고O0종료분류는미확인이다. 누적949,097 + 연구잔여30,903 + 최종예비84,000 =B1,064,000. 예비사용0·유료추가0,챔피언240·main·Participants·백업·HOLDOUT·SEALED보존.

코드와집계만공개했다: `traction285_control.py`, `traction285_prepare.py`, `traction285_run.py`, `traction285_result.json`. raw GT/trace·실패phase·수정전source·receipt는비공개다. 다음판단은고정후보종료이며이번에후속계산을시작하지않았다.
