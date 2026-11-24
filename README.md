# Semiconductor and Automation Equipment Briefing

반도체·자동화 장비 산업 소식을 무료 공개 소스에서 모으고, 출처 이용 조건에 맞춰 링크 또는 짧은 요약으로 정리하는 MVP입니다. 네이버 API 권한 검토는 별도 작업으로 보류합니다.

## 현재 수집 알고리즘

1. GDELT에서 글로벌 뉴스 후보의 제목, 출처, 관측 시각, 원문 링크를 수집합니다. GDELT는 발견용 색인으로만 쓰며 연결된 언론사 기사 본문을 자동으로 가져오거나 AI에 보내지 않습니다.
2. 과학기술정보통신부 보도자료 RSS를 독립적으로 읽고, 요청 시간 범위와 검색어에 맞는 항목을 고릅니다.
3. 두 소스의 결과를 공통 필드로 정규화하고 URL 기준으로 중복을 제거합니다. 한 소스가 실패하면 다른 소스 결과를 보존하고 소스별 상태를 표시합니다.
4. RSS가 제공한 설명이 있으면 짧은 설명으로 표시합니다. 별도 AI 요약은 아직 구현하지 않았습니다. 공공누리 이용조건은 개별 자료에서 확인해야 합니다.
5. 산업통상부 RSS는 공식 보도자료 목록과 공공누리 제1유형을 확인했지만, 피드 주소를 구현에 연결하기 전까지 후보 소스로 문서에만 등재합니다. 네이버 검색 API는 AI 처리·재배포 권한 확인 후 별도 적용합니다.

## 소스 목록

| 소스 | 현재 상태 | 비용/접근 | API 키/인증 | 발급·신청 안내 | 역할·이용 범위 |
|---|---|---|---|---|---|
| [GDELT DOC API](https://gdeltproject.org/data.html) | 연결됨 | 공개 API | 불필요 | — | 글로벌 기사 후보 발견. GDELT 자체 데이터는 출처 표시. 언론사 원문 권리는 별도이므로 제목·링크 중심 |
| [과기정통부 보도자료 RSS](https://www.msit.go.kr/contents/cont.do?mId=173&mPid=147&sCode=user) | 연결됨 | 무료 RSS | 불필요 | — | 국내 과학기술·ICT·반도체 R&D 정책/성과. 개별 자료의 공공누리 표시를 확인한 경우에만 설명문 활용 |
| [산업통상부 보도·참고자료](https://www.motir.go.kr/kor/article/ATCL3f49a5a8c) | 후보, endpoint 확인 전 | 무료 RSS | 불필요 | RSS 버튼에서 공식 feed URL 확인 필요 | 산업·공급망·투자·정책. 게시판은 공공누리 제1유형을 안내 |
| [OpenDART](https://opendart.fss.or.kr/intro/main.do) | 후보 | 원칙적으로 무료 API, 호출 한도 있음 | **필요** | [인증키 신청/관리](https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do) | 기업 투자·계약·실적 공시 보조. 뉴스가 아니라 공시 데이터 |
| [NAVER API HUB 검색 API](https://guide.ncloud-docs.com/docs/apihub-overview) | 보류 | 한시적 무료 안내, 요금 정책 재확인 필요 | **필요** (NCP 신청 후 Application 인증정보 발급) | [이용 신청·Application 등록 안내](https://guide.ncloud-docs.com/docs/apihub-application) | 네이버 뉴스 검색. 키 발급과 이 프로젝트의 이메일·AI 이용 권한은 별개이며, 권리 확인 전 호출하지 않음 |

공개 RSS가 있다고 기사 본문을 AI 요약하거나 메일로 재배포할 권한까지 생기는 것은 아닙니다. 출처별 이용조건과 항목별 공공누리 표시를 기록하고, 허용된 자료에만 요약을 적용합니다.

### API 키가 필요한 후보 소스 신청

- **OpenDART:** 개인/기업 계정으로 신청해 인증키를 발급받습니다. 기업 계정은 담당자 승인 절차가 있을 수 있습니다. [인증키 신청/관리](https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do)
- **NAVER API HUB:** NCP 계정으로 서비스 이용을 신청하고 Application을 등록하면 인증정보가 발급됩니다. [신청·등록 절차](https://guide.ncloud-docs.com/docs/apihub-application), [개발자센터에서 API HUB로 이관 안내](https://developers.naver.com/notice/article/32530)
- NAVER 인증정보를 발급받아도 검색 결과를 이메일로 제공하거나 AI에 입력할 권한이 자동으로 생기는 것은 아닙니다. 이용 전 [현행 약관](https://developers.naver.com/products/intro/terms/terms.md)과 사용 범위를 확인합니다.

## 실행

```powershell
python -m briefing --query '(Infineon OR ASE OR HYUNDAI OR MOBIS)' --hours 24 --limit 25
python -m briefing --input tests/fixtures/articles.json --email-check
```

`--input`은 오프라인 fixture이며 네트워크를 호출하지 않습니다. 실제 이메일은 `--send --to ... --delivery-id ...`와 SMTP 환경변수가 필요합니다. 불명확한 SMTP 결과는 자동 재발송하지 않습니다.

이 작업에서는 외부 소스 실호출과 이메일 발송을 하지 않았습니다. 기존 테스트는 수집기 변경에 맞춰 별도 정비가 필요합니다.
