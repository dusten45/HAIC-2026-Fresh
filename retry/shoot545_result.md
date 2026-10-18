# 545 — 안전한 궤적에서 직접 source shooting, 유한6회 내 유용 개선 없음

541의 안전한32hold 궤적을 새로 재현해 초기해로 두고,**차체 동역학·장애물 여유·공통 공간 통과 시간**을 함께 계산하는 제약 최적화를 한 번 수행했다. 초기해는 feasible이고128raw 상태 replay가 정확히 일치했다. 그러나 SLSQP6회 내 채택 가능한 feasible 갱신해는0개였다. 마지막갱신안은3.72ms 빠르지만여유.499819m<.50m였다. 사전규칙대로 초기해를유지했고효과0이다.5ms학습gate실패로feedback복귀검증·전체모델·실제비교는미실행이다. 실제기준 **13.66초**,연구 **22,758**,예비 **84,000/사용0** 그대로다.

## 새 문제와 이전 실패의 구분

531의 smooth surrogate 개선/profile 시간악화,532–533 미수렴,534 nominal1.609m/동적.437m 실패와544 반대편차 보상의 명목장애물.380m 실패를모두보존했다. 기존solver·마지막iterate·경로최적화를재개하지않았다.

이번에는541의기존feasible경로·cap90·profile·추종기를시작점으로한다. 새경로를임의로만들어정적gate로선별하지않는다. source모델에서실제state에해당하는COM/휠gas·omega·joint·yaw·접촉과전체hull/wheel자세를전파하고,그변수에안전제약을건다. 과거512처럼비영점steering을고정하지않으며,최적화prefix의명령은각hold별변수이고feedbacksuffix의재계획을별도검증하도록했다. 알려진DEV의privileged offline기계적검사이며pixel제출/실제최적주행/전역최적성의증거가아니다.

## 실행 전에 고정한 문제 정의

- **초기조건:** 저장541 실제55행동직전,54완료·runningclip이력31/480. 같은541정책으로55–86의32hold를새로전파해안전한초기궤적을확보한다.선택된32개명령의고정sequence replay가원모델상태128raw와정확히일치해야한다.
- **변수:** 앞20hold각각steer와signedpedal의보정40개.정규화steer보정에는기존clamp.4를곱하고signedpedal은원래[-1,1]범위를유지한다.20hold이후12hold는초기궤적의고정후속명령이다.이는수치미분을쓰는한개의공동제약문제이며gas값별성능sweep/다중초기화가아니다.
- **시간목적:** 저장541의79행동끝COM위치를지나는공통세계좌표평면을사용한다.평면normal은동결참조tangent이고양쪽같다.각20msraw의첫crossing bracket과선형보간시간을계산한다.서로다른경로arc진행량이나곡률surrogate를시간으로대체하지않는다.미통과수치trial의2.58초확장값은infeasible domain처리일뿐성능값이아니다.
- **raw동적제약:** 내부force≤1.059,전체footprint≥.50m,참조초과≤4.85m/s,path오차≤3m,누적clip≤10%,기존projection단조/이동량제약,모든body<100m/s.수치문제에는body≤99.999로두었다.외부1.06/물리1.25/불확실성.19/buffer.001/원안전기준을완화하지않는다.비유효body domain에서는추가전파를중단하고infeasible처리한다.unsafe offline trial은배포하지않는다.
- **말단제약:**32hold에서초기해대비path오차+.10m/속도heading오차+.02rad/yaw오차+.05rad/s/양의참조부족+.15m/s이내.공통평면속도는기준−.15m/s이상,heading/yaw오차는각각+.02/+.05이내다.terminal은각자의station에서평가하며동일위치효과분해로해석하지않는다.
- **유한수치법:** SLSQP한번,maxiter6/ftol1e-6/정규화finite-differenceeps1e-4,총400rollout이내.초기해를포함해callback에서accepted이고모든제약을지킨점중통과시간이최소인해를진행중보존한다.결과를보고다른iterate/수치미분점을사후선택하지않는다.수렴·최적성을전제로한승격은없다.
- **학습/성능분리:**freshfeasible shooting시간개선≥5ms일때만앞20hold최적명령뒤12hold를기존541feedback으로바꾼검증을허용한다.그검증도모든동적/말단제약,최소여유≥기준−.002m,보수적crossing시간이득 `baseline.lower−candidate.upper≥20ms`가필요하다.큰순간속도이득은요구하지않는다.국소sequence는전역정책이아니며실제승격에는별도cold/carry/전체효과gate가필요하다.이번실제cap은0이며조건부1000행동/2resets한도를호출하지않았다.

## 안전한 초기화와 원오류 보존

새541baseline32hold는안전했고최소여유.527152m·최대body95.47875m/s였다.최초replay도안전했지만,메모리`asdict`의tuple과저장JSON의list를그대로비교해solver전assertion에서중단됐다.원코드·traceback·결과·12,013틱/CPU132.572초를보존했다.이것을과학가설실패나새solver회차로꾸미지않았다.

별도복구계약은**완료baseline을그대로재사용**하고비교만canonicalJSON으로정규화했다.수치오차허용치를도입하지않았다.128raw전체state의canonical직렬화가정확히같았다.원counter/힘/geometry/이미실행한1rollout을선차감하고CPU/wall은원상한의잔여분만등록했다.원래95,000틱/CPU1800/총400rollout과SLSQP6회상한을늘리지않았다.실제solver실행은복구뒤의1회뿐이다.

## 유한 실험 결과

| 항목 | 결과 |
|---|---:|
|초기궤적 공통평면 보간시간|1.999999570s,raw bracket[1.98,2.00]s|
|solver종료|status9,Iteration limit reached|
|반복/목적함수평가|6 /246|
|총물리rollout(replay·최종확인포함)|249|
|제약을만족한평가점(replay/미분점포함)|53|
|채택가능한feasible callback갱신|**0**|
|사전규칙으로선택한해|안전한초기해|
|선택해시간이득|**0s**|
|feedback검증/실제|미실행/0회|

마지막callback6은callback5와같은현재해였다.목적은1.996281039초로초기보다3.7185ms빨랐지만,최소동적여유 **.499819350m**로.50미만이었다.공통평면속도90.21530m/s는초기90.36512보다약.14982m/s낮아허용말단속도경계에가까웠다.참조초과4.849984m/s도4.85경계에가까웠다.반면힘peak.985605와clip6.4583%는상대적으로여유가있었다.이trial의시간이득을안전성공이나최적값으로인정하지않았다.원인이이제약들뿐이라는물리하한증명도아니다.

수치미분점을포함한저장평가점의사후진단에서feasible최고보간이득은 **2.6421ms**였다.이점은callback채택해가아니며사후구조에사용하지않았다.5ms학습기준에도못미친다.53점은독립주행/서로다른정책집단이아니라같은초기상태의수치평가이며,작은보간차이를20ms해상도의실제성능으로해석하지않는다.

최종해는새freshreplay로다시검사했고초기해와명령·128raw상태가같았다.선택해의전체force/footprint/참조/body/말단제약을지켰다.채택하지않은unsafe trial과선택해의안전을분리했다.수렴하지않았다는이유만으로모든feasible trajectory의빠른해가없다고결론내리지않는다.

## 계산비용과 확장성 판단

원오류와복구를합친비용은 **43,757모델틱·적분내휠계산175,028회·별도명시힘175,752회·geometry44,298회·CPU540.402초/wall540.622초**다.원95,000틱/450,000힘/100,000geometry/CPU1800/wall2100이내다.복구증분은31,744틱이며원12,013을이중합산하지않았다.249rollout의raw31,872와baseline의planner/실행11,885틱이합계와일치한다.총rollout249는solver246평가에replay/cache/fresh확인을구분해센것이다.

현재densefinite-difference40변수/128raw창은유한cloud예산에서실행가능했다.그러나171hold전체에동일방식을그대로확장하면342변수/343rollout×684raw= **234,612틱/한Jacobian**이라는비용산술이된다.추가전파없이계산한가정값이며실행하지않았다.기존kernel200,000을한번의dense미분만으로초과하므로단순더긴solver/전체차원확장은채택근거가없다.후속방법에는구조화된민감도/희소화와feasible갱신방식의검토가필요하다.

저장감사는소스/입력pins·baseline1회/재사용·정확replay·callback선택규칙·모든249rolloutcounter·원budget유지·후속미실행을새모델/실제호출0으로확인했다.준비CPU.117초·감사.071초는별도이며대화/편집/Git까지정확히잰전체비용이라고주장하지않는다.

새실제행동/reset/world·새seed·HOLDOUT/SEALED·다른환경·유료자원0이다.연구22,758·예비84,000/사용0을유지했다.원시root/지도/명령/수치변수/궤적/profile/seed/RNG는저장소밖비공개에두고공개는코드·계약·집계뿐이다.main `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`·Participants·사용자변경·기존실패·백업을보존한다.추가실험/반복증액은하지않았으며종료 **2026-10-20 19:01:55 KST**와자동연장금지는유지한다.
