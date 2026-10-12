240 — 동결배율후보 패키지 검증과 챔피언 갱신

**239에서검증한동결후보를챔피언으로반영했다.** 현재232archive·manifest는원래위치와비공개rollbackmanifest에보존했다. 외부제출·파일전송·첨부는없다.

239신규HOLDOUT에서232 2/4→후보3/4, 상실완주0·공동2도로평균1.77초단축이었다. H1양쪽crash와후보의더이른실패(82행동/86타일 vs149/141), H0손상0.4→0.8은그대로기록한다. 완전한안정성이나모집단성공률을주장하지않는다.

정확한scale **[1.412502928638687, 0.8138581028883641]**, theta **[0.3453632574088313, -0.20596924895119462]**를포함한238/239 archive를byte-identical 복사해재사용했다. 원래232의최종clipped gas/brake에각scale을곱하고[0,1]clip하는정책뿐이며head·정규화·steering·16특징·nominal기억은변경하지않았다. 패키지SHA256 `ae944d7d9e2fda02fc05936bcf245613a81fade5f2f3edc1f6ead68e9bed8d31`다.

239의명령캐시925개에서실제패키지act의후처리조합이원래전/후명령과bit-exact였다. 당시캐시에픽셀관측이나16특징은없어전체pixelreplay를했다고주장하지않는다. 비공개검증평가기에서원래base출력대신저장pre-scale명령을공급해실제compiled 후처리를확인했고전체archive byte동일성및기존232의입력/head검증을재사용했다. 이검증대체는최종실행패키지에없다. GT/도로좌표/교사/시나리오/로그runtime의존성·금지import·직접파일접근은기존boundary와패키지정적검사로확인했다.

**공식기본runner knownDEVF2 한주행: 20.98초완주,damage0.2,native263/500.** 기존238의같은DEV F2시간과일치한다. 원래runner소스·5초reset/act·95%FinishLineTracker를그대로두고wholecall을읽기전용profile로측정했다. smoke는패키지검증이며독립성능확인이아니다.

전체safe_act(스레드생성/대기포함) median/p95/max 6.064/15.084/24.404ms, 전체reset0.492ms,invalid/timeout0. 공식원격서버/새머신동등성은아직인증하지않았고SEALED는닫혀있다.

재현은지정실행기안에서보존한232archive와정확한theta로기존scale238_build.build를사용하거나검증된238archive를그대로쓸수있다. 이번에는archive재생성0회다. 공식smoke계측명령은다음과같으며추가실행을자동승인하지않는다.

```bash
python -I retry/submission240_smoke.py --package EXTRACTED_PACKAGE --repository REPOSITORY --contract PRIVATE_CONTRACT.json --directory NEW_PRIVATE_RUN_DIRECTORY
```

비용: native263, wall17.848초·CPU18.405초, rawstep/reset1,050/51틱. 누적769,505+연구잔여2,495+예비84,000(사용0)=B856,000. 재훈련·HOLDOUT재주행·SEALED·추가유료자원·자동후속실험은없다. 지정클라우드·main·Participants·백업·사용자변경·승인종료2026-10-16 19:01:55 KST를보존한다.

[공식runner 계측 supervisor](submission240_smoke.py) · [결과·정확한파라미터·패키지hash](submission240_result.json)
