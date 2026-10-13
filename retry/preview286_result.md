# 286 — 현재pixel 전체경로 preview steering 실제 반증

**고정 후보는완주·시간게이트에서탈락해종료했다.** O0는26.68초완주(240보다+3.02초),N0는297action에crash(damage1,296/325타일)로완주를잃었다. 검열·기술오류·기록누락은0이다. 계수수정·나머지TRAIN·새후보를실행하지않았다.

선택한가설은240이현재pixel경로를단일lookahead목표·원곡률로축약해앞쪽경로형상과steering actuation을버린다는것이다.258~272의GT계획과단순legal이식은좋은전역경로/속도reference만으로pixel제어가개선됨을보이지못했고,281~283의outcome selector는도로별일반화에서실패했다. 그래서학습/selector/gain/traction변형대신**전체관측경로에대한연속finite-preview steering 최적화**를선택했다. 과거GT세계macro순위·frozen futuresteering label·두frame경로합성도재사용하지않았다.

후보입력은현재240의pixel path,적법HUD feedbackspeed,자기previous steering뿐이다. sourcewheelbase3.24m·steering motor속도상한3rad/s·오차gain50·rawtick.02초를고정운동학모델에썼다. wrapper당네substep,최대8action(.64초)이되경로가관측된arc길이를넘으면horizon을줄이고2미만이면240을유지했다. 보이지않는tail은외삽하지않았다.

관측path에서예측거리별목표점을고정하고,예측위치의제곱오차+`L²×steering변화²`를최소화했다. baseline현재steering을상수sequence로초기화하고유한차분Jacobian·**고정2GaussNewton update**·clip±.4만썼다. 동일모델목적을줄이지못하면baseline을유지했다. 이목적감소는실제시간/안전성보장이아니다. gain·horizon·가중치sweep·label학습·GT입력·source Box2D model rollout은0이다. prototype의입력은적법하지만공식제출package적격검증을주장하지않는다.

| 기존 TRAIN | 실제 결과 | 저장240 | 변화 |
|---|---|---|---|
| O0 | 26.68초완주,damage0 | 23.66초완주 | +3.02초 |
| N0 | 297action crash,296/325타일 | 23.62초완주 | 시간비교불가·완주상실 |

O0/N0에서planner는333/296action에적용했고317/278action에서모델목적감소를받아steering을바꿨다. currentcall의240final pedals와반환steering memory는**631action모두보존**했다. 이후관측/경로/feature/pedals는자기실행의closed-loop로변한다. 위치목적의reference는각pre-action path에고정했으며매번원점에서새path를만드는거리를실제tracking개선으로보고하지않았다.

오류복구는새체계로확대하지않고NumPyscalar를기본scalar로변환하는작은함수와per-action journal,종료직후minimal receipt 저장으로수정했다. 첫16개저장관측에서observer의240명령일치·pedals보존·scalar직렬화를확인했고실제두주행의terminal receipt와631개journal행이모두남았다.285의미확인O0는303소비비용그대로보존했으며재주행하지않았다.

초기cap4,000·gate통과후다른네TRAIN cap8,000으로총12,000을실행전에배정했다. gate는O0/N0모두완주하고각각strict시간개선이다. 실패해후속8,000은사용하지않았다. 신규비용 **631native**,actual elapsed52.878초/runnerCPU44.315초,planner3.840초·별도actorCPU8.559초다. 고정운동학10,926rollout/297,256substep은양의Box2D적분과구분했다. source modelphysics0,실제physics2523tick/reset102tick. offline관측검사1.164초/native0이다.

현재모델은상수HUD속도에서tirefriction·sideslip·손상·미래pedal변화를생략하고,이전명령을wheel angle로근사하며sourcejoint torque/constraint를정확히복제하지않는다. 관측경로shape의내부목적이낮아져도실제폐루프완주/시간이좋아지지않았다. 이결과는고정후보의반증이며전체preview제어·표현방법의불가능성은아니다.

누적949,728 + 연구잔여30,272 + 최종예비84,000 =B1,064,000. 예비·HOLDOUT·SEALED·새DEV·학습·유료자원추가0. 챔피언240·main·Participants·백업을보존했다. raw path/trace·receipt는비공개,공개는 `preview286_control.py`, `preview286_worker.py`, `preview286_prepare.py`, `preview286_run.py`, `preview286_result.json`의코드와집계다.
