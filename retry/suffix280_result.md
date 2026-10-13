# 280 — pixel240 closed-loop suffix 실행 가능성 게이트

**기존 source clone은 필요한 기능을 지원하지 않아 선행 게이트에서 중단했다.** 새 simulator·policy 학습·macro·추가 도로·DEV 평가를 만들지 않았다. 과거12-step 물리 일치로 full suffix 일치를 주장하지 않는다.

기존251 TRAIN trace의 중간 pre-action query boundary를 성능 선택 없이 고정했다: N0 action148(기존296주행 중 prefix147/suffix149), N2 action136(기존270주행 중 prefix135/suffix135). 기존 실제pixel240 trace에는 모든관측·명령·post-action 물리 상태와 terminal이 있으며 수집 코드가 공식완주23.62초/21.56초를 확인했다. 완전한 baseline 관측·명령 trace가 있어 신규 실제주행은 필요하지 않았다. 원래 snapshot에는 controller 전체상태가 없어 완전한 clone대조 receipt로 간주하지 않는다.

두 snapshot으로 기존 `SourceVehicleTransition` world를 각각 생성해 body·wheel접촉·tile방문 복원을 확인했다. 두 경우 모두 body·방문상태는 일치한다. 그러나 다음이 빠져 있다.

- clone 렌더러와 실제 track좌표/road polygon·색·camera scene; `track`은 길이만 있는None목록이다.
- wrapper의4-frame pixel stack·관측 전처리 상태.
- 공식 finish-line tracker의기하·이전 side/position·qualification·crossing/time 상태. clone `terminal`은 crash/off_track만 처리하고 공식 complete와raw tick중 조기종료를 재현하지 않는다.
- snapshot의240 controller/planner·hazards·previous image history. 다른 실행기의 history를 가져오지 않았다.
- Box2D warm-start impulse·manifold/broadphase·island history도 clone되지 않는다.

따라서 두 **no-change pixel closed-loop suffix 자체는 실행하지 않았다.** 최초 수치 불일치는 측정하지 않았고 공식terminal 재현도 미검증이다. 지원 부재를 trajectory 불일치나정책 실패로 오인하지 않는다.

현재 가능한 대안은 (1) 저장된실제pixel trace를 사용한오프라인 actor 재생(변경trajectory label은 아님), (2) 공식실행기 한곳에서reset→비용을청구하는동일prefix→짧은개입→실제pixel240끝까지주행하는250방식, (3) 기존clone의짧은 supplied-control 물리진단이다. 이번에는어느추가대안주행도실행하지 않았다. source 기반 full completion counterfactual label은 아직만들수없다.

신규 native **0**, source positive-time physics tick **0**, 렌더링·actor 호출 **0**. snapshot world생성의0시간contact초기화2회, 생성합계.02596초; import·trace검사포함 전체audit3.987초/CPU3.943초다. rendering·actor포함full suffix비용은 실행불가로 측정하지 못했다. 기존reference수집 wall16.822/13.690초와actorCPU2.627/2.347초는 과거비용이며 신규청구하지 않는다.

누적923,208·연구잔여1,792·예비84,000을 유지했다. 챔피언240·HOLDOUT·SEALED·최종예비·main·Participants를 보존했다. raw snapshot/trace·source hash receipt는 비공개이며 코드는 `suffix280_audit.py`, 집계는 `suffix280_result.json`이다.
