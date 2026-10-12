232 — 동결 단일 학생의 제출 패키지와 챔피언 반영

**231의 동결 단일 페달 학생을 제출 ZIP의 Agent로 옮겨 챔피언으로 반영했다.** 기존 archive와 manifest는 비공개 롤백 기록 및 원래 위치에 보존했다. 외부 제출·파일 전송·첨부는 없다.

231의 신규 HOLDOUT 네 쌍은 두 정책 모두4/4 완주, 학생이각6.68·6.38·7.00·10.40초 빨랐으며 평균7.615초 단축이었다. 표본은네쌍이고일반적성능이나실패확률을확정하지않는다. 학생손상증가H0 0→0.2·H2 0→0.4는진단으로유지하며새승인장벽으로삼지않았다.

normal24 조향·nominal 내부기억·head·정규화·±0.5잔차clip·[0,1]페달출력은변경하지않았다. 기존nominal archive의모든모듈은byte-identical이고entrypoint만legal특징추출및동결head출력을통합했다. 기존DEV F0 저장관측368개를원래학생과새패키지에서순서대로처리해전명령이bit-exact였다. 231학생의기존저장특징1,158행에서도패키지보정출력이모두일치했다. 학습·새학습자료·HOLDOUT재주행·SEALED는없다.

패키지에는NumPy/OpenCV와기존pixel nominal 모듈·고정계수만들어간다. GTphysics·교사·world도로좌표·시나리오ID·평가로그를포함하거나읽지않는다. 모든py의금지import/동적실행/직접open과파일목록을검사했고clean package actor에서모듈출처·GT미import·보호파일미접근을확인했다. 선택환경의README고정NumPy1.26.0/OpenCV4.8.1.78을사용하며추가requirements가필요없다. CPUlocal확인이공식원격서버동등성을증명하지는않는다.

**공식기본local_runner를수정없이 알려진DEV F0에서한번실행: 27.40초공식완주, damage0.2, native343/600.** 초기도로·실제장애물hash는기존F0와일치했다. 원래95%FinishLineTracker와Thread 기반5초reset/act기본값을그대로썼다. 이주행은패키지실행검증이며새독립성능검증이아니다.

전체 safe_act 호출(스레드생성/대기포함): 중앙값6.172ms, p95 12.269ms, 최대18.024ms. 전체safe_reset 0.517ms, timeout/invalid0. 읽기전용supervisor profile로계측했으며계측코드는ZIP에서제외했다. runner파일hash와소스는변경하지않았다.

패키지SHA256: `247ba5f033ecc7ad5b0d92cf19f3408e15711b61ce8b3cfc2d223aba2df70239`. 크기15,833bytes·파일15개; headSHA256 `2b853adb8ddbe7ff82d9dabf88a66b3621d0baf1fdeb547d08cb74d7fa2ee9b1`. ZIP은지정실행기에만보관한다.

재현 명령(기존nominal archive를BASE.zip으로,출력을지정실행기안경로로지정):

```bash
python -m retry.submission232_build --base BASE.zip --parameters retry/single231_parameters.json --output OUTPUT.zip
python -I retry/submission232_smoke.py --package EXTRACTED_PACKAGE --repository REPOSITORY --contract PRIVATE_CONTRACT.json --directory NEW_PRIVATE_RUN_DIRECTORY
```

두번째명령은승인된knownDEV smoke재현용설명이며추가실행을승인하거나자동실행하지않는다. 실제232의계약·원본관측/특징·smoke로그·archive·버전manifest는비공개작업공간에보존했다.

비용: native343, wall24.162초, CPU24.876초, rawstep/reset 1,371/51틱. 누적755,986+연구잔여2,014+예비84,000(사용0)=B842,000. main·Participants·백업·사용자변경을보존했다. 승인종료2026-10-16 19:01:55 KST·지정클라우드·추가유료자원0·자동후속실험없음을유지한다.

[Agent 코드](submission232_agent.py) · [ZIP builder](submission232_build.py) · [공식 runner 계측 supervisor](submission232_smoke.py) · [결과 및 hash](submission232_result.json)
