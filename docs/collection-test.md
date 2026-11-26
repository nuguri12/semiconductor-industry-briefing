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
- 산업통상부 RSS는 공식 게시판이 공공누리 제1유형을 안내하지만 정확한 feed endpoint를 아직 확인하지 않아 후보 목록에만 둡니다. 네이버 API도 이용 권한 확인 전에는 연결하지 않습니다.

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

## 아직 구현하지 않은 범위

LLM 요약, 외부 기사 본문 수집, OpenDART 공시 수집, 예약 실행은 아직 구현하지 않았습니다. Neon 운영 DB, 외부 감시, Gmail API/OAuth도 현재 로컬 MVP의 선행 조건이 아닙니다. 실제 뉴스 종단 검증 상태는 `project_memories/STATE.md`를 따릅니다.
