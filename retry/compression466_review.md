# 466 — 미래 raw evidence의 lossless streaming gzip 검토

**코드 조사만 했다. writer 구현·압축 실행·새 IO benchmark·physics/native 적분0, 기존 파일 삭제·이동·변환0이다.** 아래는 새 실행의 처음 생성하는 파일에만 적용할 설계다. 기존 JSON의 모든 field를 계속 비압축 보관해야만 과학적 증거가 되는 것은 아니다. 필요한 조건은 원래 정보의 완전복원, 명확한 실물파일 hash/권위 연결, 같은 시점의 실제 readback, 재현 reader 접근이다.

## 가장 작은 형식 변경과 호환 경계

먼저 **파일 단위**로 기존 serializer의 JSON bytes를 `JSONEncoder.iterencode → UTF-8 → gzip`에출력한다. 평문 전체파일을썼다압축하는것이아니라첫출력chunk부터압축한다. `.json.gz`/`.jsonl.gz`를명시하고stage manifest의logical name→physical path/encoding으로연결한다. gzip bytes를`.json`으로위장하거나숨은확장자탐색으로동일logical파일의두증거를섞지않는다. 기존평문입력은그대로읽는다.

이단계는매rawtick즉시append하는새observer가아니다. 기존observer의posts/actions·child.rows·frozen_row·raw복사목록과H13/final시점을유지한다. streamingencoder는거대한마지막JSON문자열생성을줄이지만`json_ready`의재귀복사나runtime목록을없애지는않는다. 목록을append journal/index로치환하는일은signature·H13 slicing·tail/pending증명까지바꾸므로별도변경이다. 이번설계에그비용을숨겨넣지않는다.

|검토경로|현재가정|미래명시적변경|
|---|---|---|
|receipt421_io save/load|평문read_text;receipt no-replace;canonical digest|새physical gzip경로,실제파일readback,oldcodec유지|
|loss389_analyze read/lines/sha|평문JSON/JSONL;sha는실제filebytes|read/lines에encoding adapter;sha의bytes의미유지|
|pilot433_meter input proof|저장receipt재로드→digest확인→fileSHA→constructor|descriptor의physicalpath/SHA를기록하고같은순서유지|
|observer435 runtime link/H13/final/dump|source manifest·constructor SHA·중복fullrecords|논리payload모든field유지,physical접근adapter와출력index연결|
|capture434 seal/continuation|실물boundary즉시readback·다시load한뒤tail허용|footer/fsync/readback완료전gate진행금지|
|qualify453·terminal410_run 등의직접read_text|trace평문splitlines|새출력용명시reader,old저장source그대로지원|
|closure glob/exists·retention|`*-observer-private.json`·plainpath탐색|descriptor/index열거와명확한실물존재검사|

이것은검토한핵심경로의호환성목록이지모든과거runner의전역호환완료선언이아니다. global monkeypatch보다새실행에주입한IO adapter와변경callsite목록을동결하는편이검증가능하다. `save_receipt`가반환하던semantic digest와새descriptor를혼동하지않아야한다. 새proof의path는실제gzip파일을가리키고hash는그실물bytes로검증한다. 기존sourcefile의SHA·이름·입력proof는변경하지않는다.

## 보존·hash·원자성

세hash를구분한다: **stored_sha256**(gzip실물bytes), **logical_sha256**(해제한기존JSON bytes), **receipt_digest**(기존sorted canonical JSON 의미hash). 기존`sha()`를갑자기해제bytes hash로바꾸면constructor→runtime-link체인을깨므로금지한다. descriptor가encoding/schema/version·logical/physical이름·bytes길이·세hash를묶는다. gzip의mtime와filenameheader도고정해재현성을명확히하되,성공의필수조건은올바른descriptor의실물hash이지다른압축구현과같은gzip bytes가아니다.

serializer의키입력순서·배열순서·float표현/−0.0·마지막newline을기존방식과맞춰logical bytes를보존한다. receipt의`json_ready/restore_bytes`와base64 marker를유지한다. 이codec은원래부터tuple→list,dataclass→dict를정규화하므로'모든Python객체타입보존'이라하지않고**기존JSON schema와복원bytes의lossless보존**이라한다. 수치반올림·표본생략·배열축약·원자료없이hash만남기기는없다.

임시gzip에footer까지완료→rawflush/fsync→원자publish→실제파일재개방→끝까지inflate/CRC·stored/logical SHA·schema·canonical digest확인→검증성공receipt반환순서다. receipt는기존hardlink no-replace,수정가능budget/progress는atomicreplace의서로다른뜻을유지한다. parentdirectory fsync와descriptor publication의완료도명시한다. descriptor는hash가확정된뒤작게atomicpublish하고,그이전파일은미인증orphan으로만보존한다. readback을원래메모리객체비교나hash파일존재로대신하지않는다.

명령전inputproof·constructor·첫step·H13 seal·pending continuation같은기존권위경계는해당readback이끝나야만진행한다. 다음적분전검증순서를그대로유지한다. 오류/손상/중복/공간·시간초과에서는추가적분을막고partial/orphan/error를보존하며기존정상file을덮지않는다. process crash중미완료file까지완전한증거라고주장하지않는다. 이는기존atomicwrite실패와마찬가지로유효한실험결과가아닌IO/resource중단이다.

## 공간 개선 가능성과 해결되지 않은 부분

기존검증archive에서463model은890158797→112828867B(12.68%),463native는537578277→38447814B(7.15%),465model은124327291→15095687B(12.14%)였다. 이는tar.gz후처리관측이며파일별gzip의보장압축률이아니다. 작은fileheader·dictionary범위·새descriptor/source증가분이다르다. 현재모델bytes/tick관측최대91890.089431와world고정비도계속보존한다.

예를들어지금제안한H13의plain payload약286MB를25%로계획하면compressed약72MB+검증descriptor/임시파일여유로줄어들가능성이있다. 현재두볼륨reserve와workspace복사몫에는여유가커질수있다. 하지만실행승인전새writer의압축률/peak/CPU를측정하고source증가분을반영해야한다. raw를먼저plain으로만든뒤gzip하는두벌disk peak는없애되,atomic교체old/new의동시존재·최대inflight gzip·실제readback·workspace보존복사를모두센다.

전체guarded예시60402ticks/1157worlds·hard65536은최신비율에서plain payload가약8.42GB다.25%라는경험적계획만써도약2.1GB에512MiB reserve/임시파일을더해야한다. /tmp기본압축증거는들어갈가능성이있지만현재workspace약904MB의**전수복사**에는안들어간다. 과거12.14%를그대로써도약1.02GB로workspace reserve전부터넘는다. 이미gzip인원본을다시tar.gz복사한다고12%를두번곱하면안된다.따라서lossless기록이공간을크게개선할여지는확인했지만전체guarded최악계획의완전한workspace보존문제를이미해결했다고선언하지않는다. 기존자료삭제나증거생략으로맞추지않는다.

## 검증 비용과 미래 선행 gate

463archive의압축·memberreadback·원본재hash는CPU14.106/wall14.670초,465는1.586/1.599초였다. 이것은미래개별writerbenchmark나순수gzip속도가아니다. 미래wholeworker예산에는serialization·압축·flush/fsync·전수해제/readback·JSONparse·세hash·descriptor·오류log·cleanup을포함하고,원래physics/observer시간과추가IO시간을따로집계하되전체cap을같이강제한다. 압축으로tick수가줄었다고세지않는다.

새API구현이승인되면**physics0의한통합fixture**를먼저제안한다. 새synthetic JSON/JSONL/receipt만써기존encoder논리bytes와압축해제bytes의exact일치·bytesmarker/float−0.0/순서/schema를검사한다. 실제파일재개방spy와readback완료이전integrationcallback금지,중복receipt·truncation/CRC/SHA/schema오류·짧은write·fsync/link실패·reserve부족의fail-closed를검사한다. sourceinputproof→constructorhash→runtime-link→H13seal→reload와closure/retentionreader를모두mockphysics로한번연결한다. 기존file은변환하지않는다.

이검증과구현의CPU/IO·실물압축률·최대singlefile/peak를기록한뒤에만새작은physics실험을별도계약으로검토한다. 현재466에서는어느writer도구현·실행하지않았고IO새성능실측0이다.
