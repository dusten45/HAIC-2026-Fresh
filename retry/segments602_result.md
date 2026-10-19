602 — 정확한 segment 준비로 단일 정상 core 6.934→6.187초

같은 저장 hold148에서 **정상 choose 1회**를 실행했다. CPU6.183473초/wall6.187087초로,601의 정상 wall6.933844초보다 한 표본에서0.746757초/10.77% 짧았다. **여전히5초 초과**이며 반복 paired 추정이나 다른 입력·pixel·상태추정·실제Agent.act 전체 준수의 근거는 아니다. 현재 주행 성과인 단일 privileged cold DEV native13.22초와 분리한다.

원 의미는 각 차량 polygon과 road 경계 사이의 거리에서 시작한다. SAT상 분리되지 않으면 양의0을 반환하고,분리되면 원래 순서의 point-segment 거리 전체에서 최소를 택한다. 양방향 경계 segment를 모두 평가한다. 각 polygon의 모든 꼭짓점이 inclusive road AABB와 inside 검사(모든 cross가>=0 또는<=0)를 통과하면 거리에 양의 부호를,그렇지 않으면 음의 부호를 붙인다. 전체 margin은+inf에서 시작하는 순서 있는min으로,동점에서는 먼저 나온 값을 보존한다. 따라서 outside의-0과 polygon 순서도 의미에 포함한다.

변경은 [road margin용 segment 준비](segments602.py) 하나다. 불변 road 경계566개의 양방향 edge sequence와각dx/dy/d를 context에서 한 번 준비하고,현재 차량 polygon의 edge operands도 해당 polygon당 한 번 준비한다. 원 SAT·투영·t clamp·hypot 뺄셈·거리 배열·min 순서를 유지한다. 역방향의 반올림 결과가 다를 수 있으므로 방향을 합치지 않았다. obstacles·접촉·projection·물리·정책·trial/horizon/정밀도·안전 문턱은 바꾸지 않았다.601의 exact margin memo도 그대로다.

**새 lower-bound나 segment 제외는 없다.** 기존`lower>=distance`의 식·순회 순서·동점 skip을 그대로 유지했다. 따라서 새로운 제외 조건에 의존하는 정확성 주장은 없다. 합성 trace 검사에서 기존 방문 순서도 일치했다.39개 synthetic 비교(원 함수와새 함수 각각평가,총78query)가 경계·동점·퇴화·빈 경계·NaN/inf·signedzero·inside/outside·polygon 순서의 반환 비트 또는 예외 종류를 확인했다.601의 불변성·trial 격리8개 검사도 통과했다.

저장된774개 서로 다른 geometry 입력의 원 margin을 **새 baseline 호출 없이 재사용**했다.773개는post-tick footprint,초기1개는동일한초기check만실행한9개zero-tick report에서복원했다. 새 candidate evaluator774회를청구했고 **774/774가binary64비트까지일치**했다. 실제정상choose도600/601의action bytes·전체report/trials/FINAL·모든4538개raw진단JSON·601의7176개wheel반환값을파일SHA까지재현했다. model906시도888완료,외부force3624/내부3552도동일하다. 이범위의exact helper를채택하며추가구현이나재호출은하지않았다.

|별도 측정한 범위|CPU|wall|
|---|---:|---:|
|import|1.061951s|0.286626s|
|입력·저장case 복원·pin 검사|0.621451s|0.578740s|
|synthetic·격리 검사|0.002264s|0.002891s|
|저장값 대조용 context 준비|0.001297s|0.003575s|
|774개 새 candidate 평가|4.458902s|4.461039s|
|저장값 대조 기록 JSON/fsync|0.108688s|0.107175s|
|정상 호출 context 준비|0.001499s|0.004968s|
|정상 core|6.183473s|6.187087s|
|정상 출력 materialization·JSON/fsync|1.434598s|1.436404s|
|동등성 감사|0.005723s|0.008705s|

정상 호출의 논리 geometry2641회와footprint919회는모두그대로청구했다. 그중601memo의145hit·774miss도유지했다. 총geometry는78synthetic+774대조+2641정상=**3493/15000**,model906/888(각상한1536),force합7176/12288이다. 준비·읽기감사까지CPU18.955201/wall18.150078초(보수준비5초포함),최종요약여유5초를더해도240/300 이내다. [최종 감사](segments602_audit.json)28항목을통과했다. 원kernel200000도유지했다.

native/world/reset/행동/solver/FD/새seed/HOLDOUT/SEALED는0이다. 원장22211·reserve84000/사용0·승인종료2026-10-20 19:01:55KST를유지한다. main·Participants와기존결과를보존하고,원문/명령/좌표/전체report/원시상태·힘/774개대조기록은Git밖비공개로남겼다. 후속실험은없다.

[사전 계약](segments602_contract.json),[순수 검사](segments602_tests.json),[집계](segments602_result.json),[실행 코드](verify602.py),[읽기 감사 코드](segments602_audit.py)를보존한다.
