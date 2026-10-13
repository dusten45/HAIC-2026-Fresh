# 281 — 실제 closed-loop 완주 outcome label

N0/N2의 기존240 길이296/270에서25%·50%에 가장 가까운 유효 pre-action query를 실행 전에 고정했다: **N0 73·148, N2 67·136**. 낮은query로 tie-break하며 결과를 보고 옮기지 않았다. 네 위치×gas-upper·brake-lower·steering+.015·steering−.015의16주행을 모두 실행했다.

매 action 현재pixel240 명령을 계산하고3action 동안 한 채널만 개입했다. gas-upper/brake-lower는249의현재nominal±.5→clip→고정240scale→clip 공식이며 steering은현재240명령±.015,clip±.4다. 모든실제 반환action을commit하고 steering memory·최근이력 일치를 검증했다. 이후모든채널을pixel240으로 돌려 공식종료까지 주행했다. snapshot을restore하거나 다른실행기의controller history를 가져오지 않았다.

| TRAIN 위치 | gas-upper | brake-lower | steering+ | steering− | 최선 outcome label |
|---|---:|---:|---:|---:|---|
| N0 73, 기준23.62초 | 23.26 | 23.54 | 23.90 | 23.62 | gas-upper,−.36초 |
| N0 148, 기준23.62초 | 23.60 | 23.48 | 23.66 | 23.58 | brake-lower,−.14초 |
| N2 67, 기준21.56초 | 21.18 | 21.40 | 22.22 | off_track314action | gas-upper,−.38초 |
| N2 136, 기준21.56초 | off_track346action | crash216action | 22.08 | 21.28 | steering−,−.28초 |

**16개 비교 모두 관측·baseline 명령 prefix 및 동일 snapshot boundary가 정확히 일치했다.** 13완주·3실제DNF·검열0·native기술오류0. 기준 no-change 전체trace는 재사용했고 재주행0이다. 완주시간이엄격히작아진8macro만positive outcome이며 나머지8개는baseline label이다. 각위치의네후보중최단시간을택한최선label은 위와같다. .02초 개선도양성으로남겼고 최소이득문턱을 만들지 않았다. 단일주행의수치단축이며 반복/독립일반화 근거가 아니다.

기존251 짧은frozen-future-steering label은 차례로 brake-lower/brake-lower/baseline/brake-lower였고 실제outcome 최선label은3/4위치에서달랐다. 특히 N2 67은기존baseline tie였지만실제gas-upper가.38초개선했고, N2 136의기존brake-lower는실제crash였다. 실제완주기반신호가존재하지만 후보집합(steering추가),현재pixel macro,목표도함께달라 **horizon만의인과효과**로주장하지않는다. 같은macro라도위치별로이득/실패가달라무조건반복정책의근거로쓰지않는다.

최소후속은현재네label상태의저장pixel-feature를이용한작은오프라인학습실행가능성확인으로native0이다. 실제정책진단이별도로필요하면N0/N2각650상한,총최대1,300을계획할수있다. 다만네상태·두도로로classifier일반화를검증할수없다. 이번에는classifier학습·새정책평가·DEV/HOLDOUT/SEALED·추가도로를실행하지않았고챔피언240을유지했다.

실제비용 **4,592 native =prefix1,680+macro48+continuation2,864**, 승인총10,400내다. 모든prefix·초기화포함병렬actual elapsed205.293초,runnerCPU330.927초,actorCPU53.156초(별도worker)다. 물리tick18,355·reset tick816. 오프라인no-change566action/commit검사9.281초와사전observer직렬화오류시도.936초를별도기록했다. 오류는실제주행전에수정돼native손실0이다. grant부터결과closure까지284.411초는수정·orchestration시간도포함한다. 두도로의elapsed합을병렬elapsed로표기하지않았다. source model physics0·유료자원추가0.

누적927,800 + 연구잔여6,200 + 최종예비84,000 = **B1,018,000**. 배정추가9,000을한번반영했고예비사용0. raw관측·snapshot·trace·개별receipt는비공개에보존했다. 집계는 `outcome281_result.json`, 코드는 `outcome281_prepare.py`, `outcome281_worker.py`, `outcome281_run.py`다.
