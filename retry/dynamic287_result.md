# 287 — 286의 forward model만 source transition으로 교체

**source model/state를썼을때286보다결과가좋아졌지만240보다느려고정후보를종료한다.** 다른목적·pedals·gain·탐색으로바꾸지않았고후속적법화실험은시작하지않았다.

| 기존 TRAIN | 240 재사용 | 286 운동학 재사용 | 287 source model |
|---|---|---|---|
| O0 | 23.66초완주 | 26.68초완주 | **25.66초완주**,damage .2 |
| N0 | 23.62초완주 | 297action crash | **24.78초완주**,damage0 |

O0는286보다1.02초단축했고N0완주를복구했다. 그러나240대비+2.00/+1.16초로두도로평균+1.58초다. 실제DNF·검열·기술오류·기록누락0이다. 각도로공식종료까지한번만주행했고baseline/286을재주행하지않았다.

기술적으로286의control함수bytecode를그대로사용하면서globals의rollout함수만교체할수있었다. H는원래규칙인현재HUD속도·관측path arc길이로제한된최대8action이다. 0.08초간격reference·위치제곱오차+L²steeringrate 목적·현재base steering 상수초기화·유한차분epsilon1e−4·2GaussNewton update·clip±.4·목적감소acceptance를변경하지않았다. 실제closed-loop경로가달라지므로단계별H값이286의옛trace와항상같다는주장은하지않는다.

각예측은현재GT vehicle/wheel/body/contact/friction/staticfixture snapshot으로독립 `SourceVehicleTransition` world를만들었다. forecast hull위치를현재body의right/forward frame으로돌려같은pixel path reference와비교했다. source Car.step·Box2D·damage와실제초기velocity/omega를사용하고현재240final gas/brake를모든미래action에서그대로유지했다. 미래pixel·미래240명령을알고있다고가정하지않는다. horizon전체를예측하며새terminalfilter/penalty를추가하지않았다. renderer·공식finish clone·fullsuffix는필요하지않았다.

모든clone의초기body/tile복원을확인했고forecast전후live hull상태/시간이변하지않았다. **631actualaction의현재호출pedals·steering memory를보존**했다. 단계별clone수`2H+4`와physics `(2H+4)×H×4`가286의동일최적화평가횟수와맞음을저장journal에서확인했다. solver/목적을바꾼결과를model효과로포장하지않는다.

GT초기vehicle/wheel속도·yaw·omega·마찰/contact/staticfixtures를추가한privileged 모델이므로적법정책후보가아니다. tire dynamics만의독립원인효과는분리하지못한다. 특히286의HUD상수속도/이전명령wheel-angle근사를실제GTstate로대체한효과도같이들어간다. source구현은그대로지만world복원의warm-start impulse·manifold/broadphase·islandhistory는누락되어bit-exact futureclone을주장하지않는다. 동일epsilon의finiteJacobian도float32 Box2D/contact비매끄러움에민감할수있다.

사전상한은**20후보rollout/action×8horizon×4tick×4,000native =2,560,000source physics tick**,clone초기화최대80,000회였다. 실측은**631native**,source **10,372clone/265,984positive-time tick**,0시간contact초기화10,372회로상한내다. 실제환경physics2,523tick·reset102tick은별도다.

전체actual elapsed348.406초/runnerCPU339.761초,별도actorCPU8.383초. model world생성193.334초·적분83.744초이며capture/optimizer포함planner296.745초다. 이시간들은전체실행비용에포함된구성요소이므로합산해중복청구하지않았다. sourceforecast비용은native와별도기록했고새유료자원0이다.

누적950,359 + 연구잔여29,641 + 최종예비84,000 =B1,064,000. 예비·HOLDOUT·SEALED·새DEV·학습0,챔피언240·main·Participants·백업보존. 공개는 `dynamic287_control.py`, `dynamic287_prepare.py`, `dynamic287_run.py`, `dynamic287_result.json`의코드/집계뿐이며raw자료·journal·receipt는비공개다.
