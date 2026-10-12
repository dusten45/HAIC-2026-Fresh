241 — 새DEV 네도로에서 챔피언240 단독 실패징후 조사

**추출전부터DEV로선언한새네도로에서240이4/4완주했다.** 비교후보/재튜닝은없다. 이번에는미완주·정체·방향반전이관측되지않아실패원인을확정하지않는다. 챔피언은그대로유지한다.

| 새DEV | 공식시간 | damage | 방문/전체 | 최초접촉행동 | 정체≥5 / 움직이는역방향 |
|---|---:|---:|---|---:|---|
| F0 | 23.62초 | 0.2 | 325/325 | 125 | 없음/없음 |
| F1 | 17.08초 | 0.0 | 238/238 | 없음 | 없음/없음 |
| F2 | 21.56초 | 0.0 | 292/292 | 없음 | 없음/없음 |
| F3 | 18.76초 | 0.2 | 256/256 | 199 | 없음/없음 |

기존294seed/292geometry와모든기록된DEV/HOLDOUT identity를제외했다. 최초벡터는geometry전fsync로저장했고재추출·identity충돌0회다. 원래identity-selector의ID/split태그만추출전에DEV로고정했으며공식source/RNG/geometry/장애물규칙·difficulty filter는변경하지않았다. AB/BA메타데이터는기존selector의미사용태그일뿐실제실행은240한arm×4도로한번이다.

실제policy의correct_pedals 호출인자16개를읽기전용관찰했다. 원래head를한번만호출하고추가vision/head모델질의는하지않았다. reset및매poststep원관측(N+1)·매preaction특징16·nominal/base232/최종240명령을같은실행기의비공개NPZ로저장했다. 정상학습자료가아닌GT후행변수는별도scene/진단으로분리했다. 모든현재명령은동결affine+정확한scale로재계산일치했고nominal기억연속성도확인했다.

정확한특징대응: index5 `2*x/max(forward²+x²,1e−6)`는선택된픽셀경로목표점의pure-pursuit곡률이며GT곡률이아니다. index8은실제near판단에따른lateral8vs24 플래그, index11은추적영상장애물수, index12는영상body좌표장애물의최소hypot거리(없으면100)다. index3은HUD ROI의기존선형속도, index4는기존template decoder/fallback의pedalfeedback 속도다. target_missing index0이1이면curvature가0이어도직선이라고해석하면안된다.

| 접촉도로 | 직전5개입력 near수 | 곡률범위 | feedback속도범위 | 평균실행 gas/brake | nominal brake평균 |
|---|---:|---|---|---|---:|
| F0 | 5/5 | -0.0646~0.0164 | 46.25~48.75m/s | 0.421/0.095 | 0.430 |
| F3 | 4/5 | -0.0523~0.0439 | 48.75~53.75m/s | 0.473/0.120 | 0.500 |

F0 접촉직전near가5/5이고곡률절대값이커지면서nominal은강한제동을요구했으나현재head+scale은gas를남기고제동을줄였다. F3는직전4개near=True에서접촉행동입력near=False로바뀌었고,영상장애물1개와약2.94m의근접범위는남아있었다. nearbinary만으로조건을걸면옆/뒤전환의매우가까운장애물을놓칠수있다. 원시전후명령/특징시퀀스는공개하지않고익명window집계만게시한다.

**다음반증가설은조건부제동두계수로제한하는것이타당하다.** 직선가속은240의gas/head/steering/기억그대로두고, 유효경로의기존곡률×feedback속도²에따른굽음수요와near+장애물수/영상거리위험수요를두basis로사용해brake배율만조절하는방향이다. 고정정규화는현재controller의lateral24/8·speed45 등기존상수에서정의할수있다. 아직그조건부함수나파라미터를만들거나학습하지않았다.

이것은접촉전조절의실험근거이며, 제동강화가더좋은완주/시간을준다는인과증거나실패도로수리보장은아니다. route_missing·경로선택·조향오류는제동배율만으로해결되지않을수있다. 미래입력은16개legal preaction특징으로만만들고GTgeometry·충돌후damage·방문counter·미래정보를추가하지않는다. 239HOLDOUT 실패도로/자료는읽거나DEV로가져오지않았다.

비용: **native1,015/2,200, wall45.114초**, evaluatorCPU35.607초·actorCPU8.369초, rawstep/reset4,055/204틱. private원관측/특징cache 6,877,642bytes. 전체Agent(읽기전용관찰포함)·IPC분포는JSON, 최대act IPC47.705ms·reset6.357ms다. 새GT모델질의/headfit0회.

공식종료4회, 검열0, 미실행[], 기술오류None. 누적770,520+연구잔여1,480+예비84,000(사용0)=B856,000. 지정클라우드·main·Participants·백업·사용자변경·챔피언240·마감2026-10-16 19:01:55 KST를보존한다. 모든HOLDOUT·SEALED는닫아두고추가유료자원·후보·자동후속실험은없다.

[추출전DEV등록](dev241_register.py) · [읽기전용특징worker](dev241_worker.py) · [일회주행/비공개cache](dev241_run.py) · [진단](dev241_analyze.py) · [익명결과·비용](dev241_result.json)
