# 288 — pixel corridor 내 arc 진행 우선 선택

**고정 후보는종료한다.** 두도로모두완주했지만O0는240보다.34초느리고N0는.04초빠르며평균은**+.15초**다. 287보다는평균1.43초빨랐지만240전체시간개선근거는없다. 임계값·가중치수정·재실행·후속적법화0이다. 또한아래endpoint metric한계로요청된엄밀한목적대조를완전히검증했다고주장하지않는다.

| 기존 TRAIN | 240 재사용 | 287 재사용 | 288 실제 |
|---|---|---|---|
| O0 | 23.66초 | 25.66초 | **24.00초**,damage0 |
| N0 | 23.62초 | 24.78초 | **23.58초**,damage0 |

각도로한번공식종료까지실행했다. 실제DNF·검열·기술기록오류0,baseline재주행0이다. 모든596action의현재호출final pedals와steering memory를보존했다.

현재pixel의기존road threshold(.32,.47)·7×7closing·1.5pixel clearance·관측obstacle의2.6+radius exclusion으로corridor를추정했다. rows61이후/HUD는사용하지않았다. **corridor에GTfullroad를대체하지않았다.** 287과같은H개action-boundary 예측중심이mask안에있는initial/final trajectory만선택가능했다. mask밖·unknown endpoint는부적격이다. 아무후보도없으면exact240을반환했고이fallback의corridor안전성을주장하지않는다.

source dynamics·GT초기상태·현재pixel path·HUD/관측arc 기반H≤8·같은현재pedals유지·memory를287그대로썼다. 후보탐색은같은2GaussNewton·epsilon1e−4 유한Jacobian·clip±.4·평가수2H+4다. primary residual을남은arc로바꾸고tracking/rate가중치를primary에서뺐다. 현재경로의연속forward arc구간에순차투영하며한step arc증가는sampled이동거리이내로제한해접힌경로분기로뛰지못하게했다. feasible두후보중진행이큰것을택하고**진행이정확히동률일때만287trackingcost**로결정했다. sweep없다.

O0는sourceforward후보300action중initialfeasible214/final122,부적격양쪽fallback74,tracking동률40,steering변경23이었다. N0는294action중initial205/final100,양쪽fallback86,동률38,steering변경13이었다. 596action중steering변경36뿐이므로287대비시간회복을목적의독립효과로확정하지않는다. 요청된corridor제약과진행목적이함께들어간고정후보다.

**endpoint 목적의미검증항목:** 수집후짧은집계확인에서단조projection은예측위치가경로1m까지갔다0m로돌아와도metric1m를유지하는counterexample를확인했다. 이는forward frontier에가까우며엄밀한horizon끝arc가아니다. 실제선택된forecast에서이역행이발생했는지는저장자료로확인하지못했다. 결과를보고metric을수정해다시실행하지않고원래코드·실제성과·이한계를함께보존했다. 뒤쪽분기점프의제한이endpoint정확성을보장하지는않는다.

corridor도기존morphologicalhole repair를사용한관측추정이다. 정밀가림ownership·truefree road·연속전체vehicle footprint의안전증명은아니다. source의warm-startimpulse·manifold/broadphase·islandhistory누락과GT vehicle/wheelstate 의존도그대로다. 적법챔피언후보가아니다.

사전native4,000/sourcephysics2,560,000tick/clone80,000상한을유지했다. 실측 **596native**,source **9,462clone·230,360positive-time tick**,0시간초기화9,462회였다. 실제physics2,381tick·reset102tick은별도다. elapsed294.036초/runnerCPU286.494초,별도actorCPU7.368초. sourceworld생성154.841초·적분66.624초,capture/최적화포함planner246.802초는전체elapsed안의구성요소다. 유료자원추가0.

누적950,955 + 연구잔여29,045 + 최종예비84,000 =B1,064,000. 예비·HOLDOUT·SEALED·새DEV·학습0,챔피언240·main·Participants·백업보존. 공개는 `progress288_objective.py`, `progress288_control.py`, `progress288_worker.py`, `progress288_prepare.py`, `progress288_run.py`, `progress288_result.json`의코드와집계다. raw자료·journal·metric한계receipt는비공개다.
