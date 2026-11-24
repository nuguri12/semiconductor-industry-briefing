# 수집 및 이메일 미리보기

## 오프라인 확인

```powershell
python -m briefing --input tests/fixtures/articles.json --email-check
```

fixture만 사용하며 공급자 API/RSS나 SMTP에 접속하지 않습니다.

## 현재 수집 소스

```powershell
python -m briefing --query '(semiconductor OR automation OR robotics)' --hours 24 --limit 10
```

- **GDELT DOC API:** 글로벌 기사 후보의 제목·도메인·관측시각·원문 링크만 수집합니다. GDELT가 링크한 언론사 기사 본문은 가져오지 않습니다.
- **과기정통부 보도자료 RSS:** [공식 RSS 주소 안내](https://www.msit.go.kr/contents/cont.do?mId=173&mPid=147&sCode=user)의 보도자료 feed를 확인합니다. 기간과 명시 검색어로 피드 항목을 필터링합니다.
- 소스별 결과를 공통 형식으로 합치고 동일 URL을 제거합니다. 한 소스의 오류는 다른 소스 결과를 지우지 않고 상태에 남깁니다.
- RSS의 설명(description)은 항목에 `공공누리 제1유형` 또는 `KOGL Type 1` 권리표시가 실려 있을 때만 요약 필드로 씁니다. 그 외에는 제목·링크만 사용하며 설명문은 검색에도 이용하지 않습니다. 배포 전 각 자료의 권리 표시를 확인합니다.
- 산업통상부 RSS는 공식 게시판이 공공누리 제1유형을 안내하지만 정확한 feed endpoint를 아직 확인하지 않아 후보 목록에만 둡니다. 네이버 API도 이용 권한 확인 전에는 연결하지 않습니다.

GDELT는 관측 시각을 발행 시각으로 표시하지 않습니다. 공급자별 실패·빈 결과·무효 결과는 상태로 구분합니다. 부분·빈·무효 결과는 실제 이메일 발송을 막습니다.

## API 키가 필요한 후보 소스

현재 연결된 GDELT와 과기정통부 RSS는 API 키가 필요하지 않습니다. 추가 후보 중 키/인증정보가 필요한 소스는 다음과 같습니다.

| 소스 | 자격증명 | 신청·발급 페이지 | 프로젝트 상태 |
|---|---|---|---|
| OpenDART | 인증키 필요 | [인증키 신청/관리](https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do) | 기업 공시용 후보, 아직 미연결 |
| NAVER API HUB 검색 | NCP 이용 신청 후 Application 인증정보 필요 | [이용 신청·Application 등록](https://guide.ncloud-docs.com/docs/apihub-application) | 권리 확인 전 보류. 발급 페이지와 [현행 약관](https://developers.naver.com/products/intro/terms/terms.md)은 별도 확인 |

인증정보 발급은 API 사용을 위한 기술 절차입니다. AI 입력, 저장, 이메일 배포 권한까지 승인하는 것은 아닙니다. Naver의 현행 이전 일정은 [공식 공지](https://developers.naver.com/notice/article/32530)를 참고하세요.

## 이메일 미리보기와 발송

[이메일 초안 형식](email-template.md)을 검토하세요. `--email-check`는 검증된 메일을 미리보기만 합니다. 실제 발송에는 `--send`, 명시적 `--to`, 안정적인 `--delivery-id`, SMTP 환경변수가 필요합니다. 응답 불명인 발송은 자동 재시도하지 않습니다.

## 아직 구현하지 않은 범위

LLM 요약, 외부 기사 본문 수집, OpenDART 공시 수집, 예약 실행은 아직 구현하지 않았습니다. 본문 요약은 각 출처의 AI 처리·내부 배포 조건을 확인한 후 추가합니다. 이 변경에서는 실 RSS 요청과 이메일 발송을 하지 않았습니다.
