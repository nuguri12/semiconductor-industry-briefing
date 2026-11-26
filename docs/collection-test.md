# 수집 및 이메일 미리보기

## 오프라인 확인

```powershell
python -m briefing --input tests/fixtures/articles.json --email-check
```

fixture만 사용하며 공급자 API/RSS나 SMTP에 접속하지 않습니다.

## 현재 수집 소스

```powershell
python -m briefing --query '(Infineon OR ASE OR HYUNDAI OR MOBIS OR 반도체 OR 장비 OR 자동차)' --hours 24 --limit 10
```

- **GDELT DOC API:** 글로벌 기사 후보의 제목·도메인·관측시각·원문 링크만 수집합니다. GDELT가 링크한 언론사 기사 본문은 가져오지 않습니다.
- **과기정통부 보도자료 RSS:** [공식 RSS 주소 안내](https://www.msit.go.kr/contents/cont.do?mId=173&mPid=147&sCode=user)의 보도자료 feed를 확인합니다. 기간과 명시 검색어로 피드 항목을 필터링합니다.
- 소스별 결과를 공통 형식으로 합치고 정확히 같은 URL을 제거한 뒤 번갈아 선정합니다. 한 소스의 오류는 다른 소스 결과를 지우지 않고 상태에 남깁니다. 상한이 1건이면 두 소스를 모두 담을 수 없습니다.
- MVP는 제목·출처·링크·관측 시각 또는 발행일만 출력합니다. RSS 설명(description), 기사 본문, AI 요약은 사용하지 않으며 RSS 검색은 제목에만 적용합니다.
- **산업통상부 RSS:** 공식 게시판 RSS 버튼의 `/kor/article/ATCL3f49a5a8c/rss`에 빈 POST로 접속합니다. 제목·출처·링크·날짜만 사용합니다. 네이버 API는 권한 확인 전 연결하지 않습니다.

GDELT는 관측 시각을 발행 시각으로 표시하지 않습니다. 날짜만 제공되는 RSS는 조회 시작일~종료일에 포함되는지 판단하고 시각을 만들어내지 않습니다. 날짜 범위는 정확한 24시간보다 넓을 수 있습니다.

사용자 승인(2026-11-26)에 따라 유효 기사가 있으면 일부 소스 실패·무효 항목 제외를 경고하고 정상 기사만 발송합니다. 전부 실패하거나 유효 기사가 0건이면 발송하지 않습니다. 기존 기업명 4개에 국내 검증용 `반도체 OR 장비 OR 자동차` 추가도 승인되었습니다.

## API 키가 필요한 후보 소스

현재 연결된 GDELT와 과기정통부 RSS는 API 키가 필요하지 않습니다. 추가 후보 중 키/인증정보가 필요한 소스는 다음과 같습니다.

| 소스 | 자격증명 | 신청·발급 페이지 | 프로젝트 상태 |
|---|---|---|---|
| OpenDART | 인증키 필요 | [인증키 신청/관리](https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do) | 기업 공시용 후보, 아직 미연결 |
| NAVER API HUB 검색 | NCP 이용 신청 후 Application 인증정보 필요 | [이용 신청·Application 등록](https://guide.ncloud-docs.com/docs/apihub-application) | 권리 확인 전 보류. 발급 페이지와 [현행 약관](https://developers.naver.com/products/intro/terms/terms.md)은 별도 확인 |

인증정보 발급은 API 사용을 위한 기술 절차입니다. AI 입력, 저장, 이메일 배포 권한까지 승인하는 것은 아닙니다. Naver의 현행 이전 일정은 [공식 공지](https://developers.naver.com/notice/article/32530)를 참고하세요.

## 이메일 미리보기와 발송

[이메일 초안 형식](email-template.md)을 검토하세요. `--email-check`는 검증된 메일을 미리보기만 합니다. 실제 발송에는 `--send`, 명시적 `--to`, 안정적인 `--delivery-id`, SMTP 환경변수가 필요합니다. 응답 불명인 발송은 자동 재시도하지 않습니다.

저장소 루트 `.env`에 `.env.example`의 SMTP 항목을 설정합니다. Gmail에서는 일반 계정 비밀번호가 아닌 발급된 앱 비밀번호를 `SMTP_PASSWORD`에 입력하고 `SMTP_FROM`과 `SMTP_USERNAME`을 발신 계정으로 맞춥니다. `.env`는 Git에 올리지 않습니다.

```powershell
# 실제 수집 후 이메일 미리보기: 발송하지 않음
python -m briefing --query '(Infineon OR ASE OR HYUNDAI OR MOBIS OR 반도체 OR 장비 OR 자동차)' --hours 24 --limit 10 --email-check --to nuguri12@gmail.com

# 실제 발송: 같은 브리핑의 재실행은 같은 ID를 사용
python -m briefing --query '(Infineon OR ASE OR HYUNDAI OR MOBIS OR 반도체 OR 장비 OR 자동차)' --hours 24 --limit 10 --send --to nuguri12@gmail.com --delivery-id briefing-YYYY-MM-DD-recipient-v1
```

예시 ID의 날짜를 해당 브리핑 날짜로 바꾸고 동일 건에는 그대로 재사용합니다. 새 ID는 새 발송으로 취급됩니다. 기본 이력 파일 `.briefing-deliveries.sqlite3`는 동일 폴더에 보존하세요. 삭제하거나 다른 실행기로 옮기면 이전 중복 방지 이력이 사라집니다. `failed`·`unknown`·`sending` 상태도 자동 재전송하지 않으므로 원인과 수신 여부를 확인한 뒤 처리합니다.

2026-11-26 앱 비밀번호를 사용한 합성 테스트 메일의 SMTP 발송과 Gmail 받은편지함 수신을 확인했습니다. 이는 실제 뉴스 소스 품질이나 정기 운영의 검증을 뜻하지 않습니다.

## 저장한 결과의 재사용

`--json` 출력은 `schema_version: 1`을 포함한 정규화 결과다. UTF-8로 `output/`에 저장한 뒤 같은 파일을 `--input`으로 미리보기와 발송에 사용한다. 소스 상태, 수집 시각, 검색어, 날짜 정밀도와 기사 순서를 보존한다. 저장 결과 입력에서는 `--limit`으로 재선별하지 않는다. 기존 GDELT fixture 입력도 지원하지만, 이전의 버전 없는 정규화 결과는 새로 수집해야 한다.

`--send`와 `--email-check` 또는 `--json`의 동시 지정은 오류로 처리한다. 실제 발송에는 검토한 저장 파일과 고정된 발송 ID를 사용한다. 서로 다른 실시간 조회를 미리보기와 발송에 사용하면 기사 목록이 달라질 수 있다.

## 2026-11-26 MVP 실행 결과

코드 기준: `db1f1e4` 이후 작업 트리 변경. 검증 시각은 KST 20:21~20:25경이다. 최종 판정은 **미완료: 실제 관련 기사 미확보**다. 이번 실행에서 이메일은 보내지 않았다.

| 기준 | 결과 | 증거 |
|---|---|---|
| M1 | 미통과 | 기업명 24시간, 국내 산업 검색어 24/72시간 조회. GDELT는 각 요청의 제한된 재시도 후 HTTP 429. MSIT는 정상 응답이나 관련 기사 0건. |
| M2 | 실제 기사 검토 대기 / 구현 검증 통과 | 저장 결과 왕복 시 필드·소스 상태 보존, 잘못된 값·중복 URL 거부 회귀 테스트. |
| M3 | 실제 기사 기준 대기 / 빈 결과 및 모의 검증 통과 | 실제 빈 결과의 `--email-check` 종료 0. SMTP·ledger 미호출 테스트 통과. |
| M4 | 미수행 | 유효 기사 0건이므로 실제 발송과 새 수신 확인을 수행하지 않음. 과거 합성 메일 성공으로 대체하지 않음. |
| M5 | 모의 검증 통과 / 실제 기사 재실행 대기 | 저장 결과를 같은 ID로 두 번 실행해 SMTP 호출 1회. unknown·failed 재시도 방지 테스트 통과. |
| M6 | 통과 | 부분 실패·빈 결과·잘못된 입력·실패·응답불명 테스트 통과. 실제 빈 결과의 `--send` 종료 2, 발송 이력 파일 해시 불변. |

MSIT 공식 RSS 메타데이터 50건의 날짜는 11월 16~26일이었다. 지정 국내 검색어와 일치하는 유일한 항목은 11월 20일자 「과기정통부, 인공지능 반도체 업계 현안 점검...국제 협력·공급망 대응 모색」으로 72시간 범위 밖이었다. 따라서 이번 빈 결과는 피드 연결 실패나 날짜 파싱 실패가 아니다.

실행: `python -m unittest discover -s tests -v` — 37개 통과. 실제 조회에는 계획의 기업명/국내 검색어, `--hours 24` 또는 `72`, `--limit 5 --json`을 사용했다. 저장 결과에 `--json`, `--email-check`, `--send`를 각각 적용해 동일성·미리보기·빈 결과 차단을 확인했다. `--send`는 빈 결과 차단을 확인하는 실행으로 SMTP에 도달하지 않았다.

로컬 증거는 Git 제외 디렉터리 `output/mvp-20261126/`에 있다: `corporate-24.json`, `industry-24.json`, `industry-72.json`, 각 stderr, `feed-metadata.json`, `local-checks.json` 및 미리보기/차단 로그. 정규화 JSON에는 소스별 수집 건수·오류 종류·HTTP 상태를 기록한다. 키나 자격 증명은 기록하지 않았다.

계획 대비 추가 보완: 발송과 출력 옵션 충돌을 차단하고, 소스별 건수·오류를 JSON에 남겼다. 수집 기간을 72시간 밖으로 늘리거나 새 소스를 추가하지 않았다. 재개 조건은 GDELT 정상 응답 또는 MSIT의 조회 기간 내 관련 기사 확보이며, 확보 후 같은 저장 결과로 M2~M5의 라이브 검증을 이어간다.

## 2026-11-26 후속 검증: 실제 기사 전달 성공

산업통상부를 세 번째 소스로 추가한 후 KST 20:39 수집에서 당일 반도체 관련 1건을 확보했다. GDELT 실패, MSIT 정상 0건, MOTIR 정상 1건이다. 제목·원문 페이지 접근·출처·날짜를 확인하고 저장 JSON으로 `--email-check`를 통과했다. 기존 승인된 테스트 수신자에게 `mvp-live-motir-20261126-01`로 한 번 발송해 ledger sent와 Gmail INBOX의 제목·전체 본문·링크를 대조했다. 같은 파일·발송 ID로 재실행 시 종료 0, ledger 해시 불변, Gmail 검색 결과는 동일 메일 1건이었다.

M1~M6의 로컬 경로는 **제한 사항을 포함한 완료**로 판정한다. 수집 소스 범위가 두 곳에서 세 곳으로 확대됐으며 GDELT 정상화와 장기 커버리지는 미완료다. DB/예약 운영 완료를 뜻하지 않는다. 실제 결과는 `output/mvp-motir-20261126/`의 live JSON, preview, send, replay 로그에 있다. 개인정보가 있는 원본은 Git 제외한다.

전체 테스트 49개 중 46개 통과, PostgreSQL 실통합 3개는 격리 DB URL 미설정으로 건너뛰었다. 소스·동일 입력 재사용·SQLite 발송 안전장치 및 DB 실패 차단은 검증했고, PostgreSQL SQL 적용·동시성·권한은 아직 검증하지 않았다.

## 아직 구현하지 않은 범위

LLM 요약, 외부 기사 본문 수집, OpenDART 공시 수집, 예약 실행은 아직 구현하지 않았습니다. Neon 운영 DB, 외부 감시, Gmail API/OAuth도 현재 로컬 MVP의 선행 조건이 아닙니다. 실제 뉴스 종단 검증 상태는 `project_memories/STATE.md`를 따릅니다.
