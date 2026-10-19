605 — zero s400 exact 대조 완료, 고정 8개 residual 정책은 모두 조기 중단

604의 초기화 누락을 별도605에서 고쳤다. **새 source 초기→raw96 재구성,zero의s400 crossing hold끝raw304까지597의모든raw행·상태·이력·visited·tracker·clock·checkpoint·원537action/report가정확히일치**했다.604의raw156부분결과를zero완료로대체하지않았고,새prefix96의비용을새로청구했다.604코드·실패·비용은그대로다.

고정순서zero,H0..H7을모두평가했다.비영8개는아래조건에서중단했고,안전한양의s400개선후보가없어독립재생은실행하지않았다.미평가/비용검열후보는0이다. **이8개진폭·벡터와기존incumbent조합에대한결과**이며,연속6계수공간이나모든준비상태의물리적불가능성을입증하지않는다.

|후보|중단 위치|첫 원인|검증된 수치|
|---|---|---|---|
|H0|raw126 pre-force|FORCE|1.169364 >1.059|
|H1|raw161 pre-force|FORCE|1.059621 >1.059|
|H2|raw126 pre-force|FORCE|1.095789 >1.059|
|H3|raw156 post-tick|FOOTPRINT|0.406738m <0.50m|
|H4|raw154 pre-force|FORCE|1.074883 >1.059|
|H5|raw126 pre-force|FORCE|1.164373 >1.059|
|H6|hold40,raw156 직후|원537 NO_ADMISSIBLE_ACTION|20trial:forecast footprint12,force8|
|H7|raw126 pre-force|FORCE|1.094239 >1.059|

6개의force실패에서는해당raw의tick을적용하지않았다.H3는tick후margin위반으로멈췄다.H6는원537의유한grid/backup witness가action을반환하지않아해당decision의수정action을적용하지않았다.따라서H6를미래의실제적용충돌이나물리적force실패와혼동하지않는다.모두source의엄격한buffer판정이며native결과가아니다.문턱완화나실패후진폭변경은없다.

|zero 진단 plane|연속 COM chord 보간시간|20ms raw bracket|
|---|---:|---|
|old551 s200|3.854474059s|192→193|
|old551 s300|4.948917285s|247→248|
|old551 s400|6.054387012s|302→303|

s400의fraction은0.7193506226712343이고hold76의나머지raw304까지안전했다.수치ULP는8.881784197001252e-16초지만물리적시간단계는20ms이며보간정확도를공식기록해상도로해석하지않는다.s200/300은진단전용이며느린중간상태를prune하지않았다.100/500ms개선문턱은없었고,비영후보에는안전한s400시간자체가없어gain은null이다.

계산동작의수정은 **instance별 `geometry_context` 초기화한줄**이다.별도605namespace와필수검사/보존metadata외에평가·residual·재생등19개항목이604와같음을[정적대조](residual605_change_review.json)로확인했다.실제생성자/choose/evaluate/context/run을사용하는순수stub7그룹이hold39→40전환의root/path/backup/history/modelcounter/cost/max_ticks180000/context전달,zero/nonzero/영역밖bytes,helper연결과정리,독립clone격리,기술실패전체중단을검사했다.실제physics/537/evaluator호출은0이었다.등록후source전에이검사를다시통과했고실제source실행은1회다.

수정action은원incumbent의FINAL로미래인증됐다고취급하지않았다.원537의trial/FINAL비용은그대로청구하면서,정해진9개정책에새source-only직접strict적용검사를수행했다.모든적용pre-force와footprint/path/reference/clip/body/projection/상태gate·551path/reference/cap·원kernel200000은유지했다.603helper는새memo miss마다원Python fullmargin과비트대조했고 **12677회추가조회**를모두청구했다.불일치는없었다.

605의실제총비용은 **model15017시도/14793완료,외부force60068·내부59172·합119240,geometry58022**다.여기에는적용667시도/661완료와모든forecast/reject/FINAL이포함된다.geometry는namedmargin/projection43267+원Python대조12677+worldplane1980+residualtarget94+고정plane3+초기tracker1=58022로완전분해했다.각hold전에최악호출량과1174raw독립재생/cleanup을선예약했다.읽기감사·분석포함CPU약214.50초/wall215.64초(보수준비10초포함),최종정리여유30CPU/45wall을더해도5400/6600 이내다.상한은확대하지않았다.

[읽기감사](residual605_audit.json)25항목을통과했다.전체report가포함된실행당시result는원hash와함께Git밖에보존하고,공개집계에서는H6의전체report1개만비공개표시와trial수로대체했다.실험수치/결론은변경하지않았다.전체입력/명령/좌표/report/상태·힘/journal은비공개다.

native/world/reset/행동/새seed/HOLDOUT/SEALED/carry는0이다.기존privileged cold native13.22초·원장22211·reserve84000/사용0·main/Participants·승인종료2026-10-20 19:01:55KST를유지한다.공식전체기록·pixel/Agent.act준수·native admission/일반승격의주장은없다.후속실험이나자동재시도는없다.

[계약](residual605_contract.json),[검사](residual605_tests.json),[공개집계](residual605_result.json),[첫실패/비용분석](residual605_analysis.json),[실행코드](residual605.py),[stub](residual605_preflight.py),[공개projection](residual605_public.py)을보존한다.
