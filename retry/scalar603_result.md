603 — 지정 환경의 exact C kernel, 단일 core 3.940초

같은 저장 hold148에서 정상 choose **1회**가 CPU3.936815초/wall3.940054초였다.602의 정상 wall6.187087초 대비 한 표본에서2.247033초/36.32% 짧았다. **이 입력의 core 한 호출만5초 미만**이며,pixel·상태추정·thread/marshalling·실제Agent.act 전체나다른입력의준수를뜻하지않는다. 반복호출로좋은시간을고르지않았다.

환경에이미설치된 GCC14.2와현재CPython3.11.16개발헤더를사용했다.새설치·다른환경·유료자원은없다.변경은 [scalar C query/distance kernel](scalar603.c) 하나로,602의 road margin 내부 SAT·point-segment·ordered min 반복만컴파일했다.601cache·602의불변segment준비값·양방향/순회/min순서·inside/outside·부호0·기존pruning·모든안전/비용gate는유지했다.원동역학/정책/trial/horizon/정밀도/문턱은변경하지않았다.

`-fno-fast-math -fno-unsafe-math-optimizations -fno-associative-math -ffp-contract=off -fexcess-precision=standard -frounding-math -ftrapping-math -fno-tree-vectorize -fno-tree-slp-vectorize -mfpmath=sse -msse2` 등을동결했다.원천·compiler/cc1/as/ld·Python실행파일/헤더·libm/libc·옵션·생성binary의hash를보존했다.컴파일assert와runtime검사에서scalarbinary64(mantissa53,FLT_EVAL_METHOD0)·FE_TONEAREST를확인했다.기계어감사에서FMA와packedFP산술은없었다. min/max는C의fmin/fmax로대체하지않고원래의first-equal/NaN비교규칙을직접유지했다.

**hypot은원CPython `math.hypot` 객체를그대로호출**한다.독립적인C/libm hypot알고리즘으로바꾸지않아원반환값을유지했다.각scalar연산은원식의뺄셈·곱셈·덧셈·나눗셈순서를보존하고FMA/재결합을금지했다.새segment제외나거리근사는없다.이backend는지정runtime에대한구현이며,다른compiler/ABI나공식실행환경의확장모듈빌드·배포가능성은검증하지않았다.

602의동일한39개synthetic case에서반환binary64비트또는예외종류가일치했다.동점·signedzero·NaN/inf·퇴화·빈경계·SAT접촉·방문순서를포함하며78개새geometry평가를청구했다.601의격리/불변성8개검사도통과했다.저장774개원margin은baseline재평가없이읽고,새compiled평가774회에서 **774/774비트일치**를확인한뒤에만choose를시작했다.

정상choose는600~602의action bytes·전체report/trials/FINAL·4538개raw진단JSON·7176개wheel반환값을파일SHA까지재현했다. model906시도/888완료,외부force3624/내부3552,정상논리geometry2641회도동일하다.601memo145hit/774miss와196667개polygon-segment pair도유지됐다.이정확성범위에서helper를채택했다.

|별도 측정 범위|CPU|wall|
|---|---:|---:|
|import|1.073452s|0.303117s|
|입력·runtime/tool pin·복원|0.632526s|0.632232s|
|단일 compile·load|0.254119s|0.257289s|
|기계어·runtime 감사|0.075711s|0.076806s|
|synthetic·격리 검사|0.003989s|0.003029s|
|774 대조 context 준비|0.000000s(관측값)|0.003111s|
|774개compiled평가|2.075264s|2.075838s|
|대조 JSON/fsync|0.008019s|0.005251s|
|정상 context 준비|0.003069s|0.004882s|
|정상 core|3.936815s|3.940054s|
|출력 materialization·JSON/fsync|1.332177s|1.338370s|
|동등성 감사|0.011999s|0.008551s|

compile은정확히1회이며워밍업choose는없다. compiler등자식CPU0.273345초를총CPU에포함했다.읽기최종감사까지CPU14.520064/wall13.760287초(보수준비5초포함),최종요약여유5초를더해도전체300/420 이내다.상한을늘리지않았다. geometry78+774+2641=3493/15000,model906/888(각1536상한),force7176/12288이다.[최종감사](scalar603_audit.json)36항목을통과했다.

이좁은계산최적화선은여기서종료한다.지정cloud에서원수치결과를유지하는compiled helper의구현가능성을확인했으므로,후속주행연구의계산도구로재사용할근거가있다.11초대주행가설과남은1.24초의물리적단축은여전히미검증이고,기존단일privileged cold DEV native13.22초는그대로다.본작업의새native/world/reset/행동/solver/FD/seed/HOLDOUT/SEALED는모두0이다.원장22211·reserve84000/사용0·승인종료2026-10-20 19:01:55KST를유지한다.후속주행실험은실행하지않았다.

[사전계약·compiler/runtime/옵션](scalar603_contract.json),[검사](scalar603_tests.json),[집계](scalar603_result.json),[실행코드](compile603.py),[읽기감사](scalar603_audit.py)를보존한다. main/Participants·기존결과를보존하며기술코드·hash·집계만커밋한다.입력/좌표/명령/전체report/raw상태·힘/생성binary/compilerlog/기계어는Git밖비공개다.
