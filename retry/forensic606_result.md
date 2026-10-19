606 — 저장 로그 대조 완료, 새 평가 0회

기존605의실패행과zero동일raw행,원명령/수정명령bytes,외부·내부wheel반환순서를읽어대조했다.새tick·chooser·force/geometry evaluator·native는모두0이다.명령의절대값·상태·좌표는공개하지않고차이·비율·분류만집계했다.같은raw대조는같은clock이며대부분같은물리상태대조가아니다.

raw126에모인H0/H2/H5/H7의관측

- 네경우모두raw125와126의명령이같다.새hold명령변화는raw125에있었고,zero에도약-0.04405의hold간조향변화가있었다.후보의해당변화는-0.04680..-0.04123으로zero보다일괄커진것도아니다.
- 조향command한계·pedal한계의동시포화는없었다.이전tick에기록된앞servo rate도3rad/s한계미만이었다.네경우의현재pedal은brake영역이며,양의netpedal residual약0.01727..0.01740은brake를줄이는방향이다.
- 명령·물리상태·wheel heading은이미raw97부터zero와달랐다.raw126직전중심위치차이는0.530..0.614m,속도차이는+2.549..+2.601m/s였다.누적상태변화와다음raw의횡력상승에부합하지만조향/페달각각의인과효과는분리하지못한다.
- H0/H7의기록된target offset은직전hold와같고,H2/H5는변했다.따라서네경우공통원인을그시점의target-offset점프로단정할수없다.target좌표/normal과unclamped PP residual은저장되지않아새geometry계산없이segment전환영향을복원하지않았다.

|실패|최대바퀴|zero 동일raw ratio|후보ratio|저장post-clip force의횡성분제곱비중|
|---|---|---:|---:|---:|
|H0/raw126|앞1|1.056561|1.169364|96.48%|
|H2/raw126|앞1|1.056561|1.095789|95.98%|
|H5/raw126|앞1|1.056561|1.164373|96.44%|
|H7/raw126|앞1|1.056561|1.094239|95.93%|
|H4/raw154|뒤2|1.052296|1.074883|25.90%|
|H1/raw161|뒤2|0.996870|1.059621|20.59%|

모든바퀴0..3의ratio·clipped·post-clip종횡성분변화/마찰한계·omega_drive/braked변화는[분석JSON](forensic606_analysis.json)에있다.원래unsaturated종횡force와slip속도는저장되지않아재계산하지않았다.표의제곱비중은저장된clipped성분의산술집계이며원인기여율이아니다.H4는gas영역netpedal을소폭줄였는데도뒤2에서실패해모든실패를즉시pedal증가하나로설명할수없다.

H1의더좁은같은상태대조

605에남은원FINAL첫raw와수정명령의실제pre-force는steer latch를제외한물리상태가정확히같다.앞0/1의force항은같고뒤바퀴가달라졌다.

|바퀴|같은상태 원FINAL ratio|수정명령 ratio|
|---|---:|---:|
|앞0|0.697412|0.697412|
|앞1|0.783672|0.783672|
|뒤2|1.056463|1.059621|
|뒤3|0.997836|1.000668|

실제netpedal은선택된incumbent보다+0.006555였다.원force_rows는새action[0]/planar.steer를읽지않고현재wheel heading과pedal항을사용한다.조향은tick의servo/yaw/heading변경을거쳐후속raw에영향을준다.따라서이저장입력쌍은현재pedal항변화와즉시gate초과가함께나타난사례이며,선택후residual합성이인증경계를벗어났다는증거다.이를전체정책이나native차량의분리된인과효과로확대하지않는다.원FINAL을수정명령의인증으로사용할수없음도재확인됐다.

H3와H6

- H3는같은hold명령을유지한raw153..156에서margin이1.547→1.135→0.756→0.406738m로줄었다.zero의같은raw156은0.956543m다.실패시현재조향residual은작아도,직전상태는zero와위치3.020m·body angle약-0.220rad차이가있었다.path1.052<3,force1.0211<1.059,clip0.02083<0.10등다른적용gate는통과했다.누적자세/경로변화와일치하지만최소margin의bodypart·road/obstacle기여label이없어어느부품/경계인지추정하지않았다.
- H6의마지막실제상태는margin0.556759m로safe다.원537은첫조향값하나에서pedal20개만시험했다.8개는pre-force즉시실패,12개는**첫forecast tick**에서margin0.270732..0.287641m로실패했다.모든12개에서앞servo rate두개가한계에닿았다.이전적용명령→원nominal조향변화는-0.061833이고zero의같은전환은+0.022478이었다.이는현재nominal조향으로고정된유한집합의초기실패이며,미래11개backup때문에늦게탈락한사례가아니다.수정명령은적용되지않았고다른조향의feasibility는평가되지않았다.

설계상차이와다음단일제안 — 미실행

605는조향을고정한원537의pedal선택뒤에residual을붙였다.원537의인증은그앞단명령/backup witness에대한것이다.조향과최종pedal을후보생성단계에서함께구성한뒤해당pair를검사하면최종적용명령의경계를직접검사할수있다.이변경만으로안전한pair나주행개선이보장되지는않는다.

[단일제안](forensic606_next_proposal.json)은**같은저장H1 raw160상태의작은joint-pair검사**다.같은상태의원FINAL positive witness가있어이경계를검사하기에적합하다.원537zero호출/원행동4raw를정확히재현한뒤,이미기록된원조향/수정조향두값과고정netpedal grid를결합해최종pair부터12hold인증한다.전pair를검사하며느린준비상태를진행도로prune하지않는다.shifted조향에서feasible pair가없으면이유한집합가설을반증하고종료한다.있으면기록된수정pedal에가장가까운pair하나를새FINAL·4raw적용·4raw독립명령재생으로검사한다.진폭반복·FD/Jacobian·실패penalty는없다.

제안상한은originalchoose1회·jointbatch1회,model4096/4096,force합32768,geometry20000,준비감사포함CPU240/wall300초다.원kernel200000과모든숫자gate를유지한다.이것은local feasibility게이트이며전체residual미래정책·s400시간·공식lap의증거가아니다.실행코드나새평가는시작하지않았다.

시간과종료상태

reader는12:19:49UTC에종료표식을썼고상태확인시살아있는reader는없었다.최초읽기에서pre-force실패행에없는post_failure키를처리하는parser오류를수정했으며물리평가는없었다.기록된reader시간은CPU/wall약5.64초(보수5초포함),parser복구와2개보충읽기에각1초를추가계상하면약8.65초다.**그러나코드작성·정리를포함한전체작업경과는사용자관측약12분으로300초를넘겼다.전체wall한도준수로보고하지않는다.**상태요청뒤분석확대를중단하고기존결과만정리했다.연결·도구장애는없었다.

원장22211·reserve84000/사용0·기존비용·main/Participants·승인종료2026-10-20 19:01:55KST는보존한다.기존privileged cold native13.22초와11초대가설은변경없다.[읽기계약](forensic606_contract.json),[보충집계](forensic606_refinement.json),[종료메타데이터](forensic606_closeout.json),[reader](forensic606.py)를보존하며원문/좌표/명령은비공개다.
