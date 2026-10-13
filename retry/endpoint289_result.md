# 289 — horizon 끝 arc 구현 복구와 실제 대조

**endpoint 수정후에도두도로의일관된시간개선은없어고정목적후보를종료했다.** O0는24.36초(+.70초),N0는23.24초(−.38초)로둘다완주했고평균은240보다+.16초다. N0의실제개선은보존하지만적법챔피언/일반화근거로쓰지않는다. GT초기state를쓰는진단이다.

| 기존 TRAIN | 240 재사용 | 288 재사용 | 289 복구 후보 |
|---|---|---|---|
| O0 | 23.66초 | 24.00초 | **24.36초**,damage0 |
| N0 | 23.62초 | 23.58초 | **23.24초**,damage .2 |

구현차이는projection뿐이다. 288의forward-window/최고arc유지대신경로의현재연결segment와인접segment를따라거리감소방향으로투영branch를유지한다. 거리동률이면현재branch를유지하고,최종위치의직접arc좌표를반환한다. 전진뒤역행하면arc가감소한다. maximum-so-far나비음수진행증분누적을쓰지않는다. path뒤쪽의보이지않는경로는생성하지않는다.

저장된288반례는1m전진후원점으로돌아올때1→**0m**로복구됐다. 작은다섯예시에서전진4m,4→1m후진,원점복귀0m,가까운평행경로로점프하지않음,연결코너를지난다음branch 진입을확인했다. 이는기존계약의복구이며gain·threshold·가중치탐색이아니다.

288 journal에는후보별초기/최종좌표와Usequence가없어전체실제주행의선택불변을native0으로확정할수없었다. 다른baseline snapshot으로대체하거나결측을추정하지않고O0/N0수정후보를각각한번실제평가했다. baseline·288은재실행하지않았다. 이번에는두실행후보의좌표/U를private journal에추가해최소재현근거를남겼다.

source dynamics·GT초기상태·현재pixelcorridor·path·H규칙·2GN/epsilon1e−4/후보수2H+4·pedals·memory·tracking동률tie-break는288그대로다. 596actualaction의현재호출pedals/memory와terminal receipt를보존했다. 신규1,182개저장후보좌표에서수정endpoint값을native/modelphysics0으로재계산해일치를확인했다. 같은289좌표에서옛metric이새endpoint보다최대17.056m크게나왔고,투영trajectory의peak→endpoint감소는최대.986m였다. 이는새저장자료의metric차이이며288전체선택이얼마나달랐는지의추정은아니다.

O0는optimizer수락68/steering변경67action,초기/최종corridor feasible229/180,양쪽부적격fallback57이었다. N0는수락/변경55action,feasible229/185,fallback48이었다. 새로운모델·목적·perception·pedal제어를함께추가하지않았다. currentpixel corridor의morphology/가림추정·sampledcenter 제약·fallback비보장과GT source복원의warmstart누락은288의기존한계로남는다.

두주행정상종료:실제DNF·cap검열·기록오류0. 실제비용 **596native**,source **9,478clone·232,808positive-time tick**,0시간초기화9,478회다. 사전상한native4,000/sourcephysics2,560,000/clone80,000이내다. 실제physics2,382tick·reset102tick은별도다. actual elapsed267.941초/runnerCPU261.134초,별도actorCPU6.642초. world생성135.631초·적분58.085초,capture/optimizer포함planner226.266초는전체시간의구성요소다.

누적951,551 + 연구잔여28,449 + 최종예비84,000 =B1,064,000. 예비·HOLDOUT·SEALED·새DEV·학습·유료자원추가0. 챔피언240·main·Participants·백업보존. 공개는 `endpoint289_objective.py`, `endpoint289_control.py`, `endpoint289_prepare.py`, `endpoint289_run.py`, `endpoint289_result.json`의코드와집계다. raw후보좌표/GT/trace·receipt는비공개다. 임계값/가중치수정이나후속주행은시작하지않았다.
