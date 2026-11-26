# 추가 소스 검토 — 2026-11-26

판정 기준: 산업 관련성(반도체 제조·장비·공급망·자동화), 실제 피드 접근, 최신성, 사용 범위, 기존 소스와 중복, 무료/키 필요 여부. 피드가 있다는 이유로 본문 재배포나 AI 요약 권한을 추정하지 않는다. 이번 구현은 제목·출처·링크·날짜만 사용한다.

| 소스 | 확인한 근거 | 적합성 및 한계 | 판정 |
|---|---|---|---|
| 산업통상부 MOTIR | 공식 게시판 RSS 버튼의 POST action, 실제 RSS 10건, 당일 반도체 관련 1건 | 국내 산업정책·공급망·투자 협력에 적합. 최근 10건 피드라 수집 간격이 길면 누락 가능. 글로벌 장비 시장을 대표하지 않음 | **세 번째 기본 수집기로 추가**, 무료·키 없음 |
| NIST Manufacturing / Electronics | 공식 RSS 목록, 실제 각 40건 응답. 두 피드 모두 11월 24일 CHIPS R&D 지원 관련 자료 포함 | 제조기술·계측·표준·미국 반도체 정책 보완. 행사와 미래 일정이 섞이고 두 피드가 중복됨. 상업 시장 속보 빈도는 낮음 | **차기 후보**. 뉴스 URL만 선별하고 영문 검색어·중복 처리 후 활성화. 무료 공개 피드·키 없음 |
| Infineon 공식 보도자료 | 공식 페이지에서 11월 24일 발표와 반도체 공장·차량·로봇 관련 발표 확인 | 지정 기업 추적에는 높음. 자사 홍보 편향, RSS/API 계약과 자동 수집 조건은 미확인 | 후보. 현재 자동 수집 미연결, 비용/키 조건도 미확인 |
| Siemens 공식 Press | 공식 RSS 안내는 있으나 확인된 안내가 2014년 자료 | 산업 자동화 적합성은 높지만 현재 endpoint·사용 조건의 추가 검증 필요 | 보류. 과거 RSS 안내만으로 활성화하지 않음 |
| 전문매체 eeNews Europe / Automation.com | 공식 소개·콘텐츠 제출 안내 확인 | 업계·장비 보완 가능. 실제 RSS endpoint와 이메일 재사용 조건은 이번에 확인하지 못함 | 보류. 무료 열람을 자동 수집 허가로 간주하지 않음 |

## 실제 적용

- endpoint: `https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/rss`
- 공식 RSS 버튼과 같은 빈 POST 사용. HTML 크롤러는 운영 경로에 추가하지 않음.
- MSIT RSS/Atom 파서를 재사용. 날짜만 있는 항목은 날짜 정밀도를 유지하고 본문·설명·첨부파일은 결과에서 제외.
- GDELT/MSIT/MOTIR를 독립 호출하고 URL 중복 제거 후 소스별로 번갈아 선택. 한 소스 실패로 다른 소스 결과를 지우지 않음.
- 저작권 정책은 KOGL 표시 확인과 출처 명시를 요구한다. 일반 정책이나 페이지 공통 푸터를 개별 본문 이용 허가로 해석하지 않는다. 향후 본문/요약 도입 시 항목별 확인 필요.

## 실제 결과

24시간 국내 검색어 `(반도체 OR 장비 OR 자동차)`: GDELT 실패, MSIT 정상 0건, MOTIR 정상 1건. 대상은 11월 26일 「한-일 정부와 민간, 반도체·AI 등 미래성장 협력 논의」다. 정상 원문 페이지 접근, 제목·당일 날짜·링크·출처를 확인했다. 받은편지함에서 동일 본문과 링크를 확인했다. 새 소스 덕분에 실제 기사 전달을 검증했지만 자동화 장비의 글로벌 상업 뉴스 부족은 남는다.

로컬 증거: Git 제외 `output/motir-feed.xml`, `output/nist-review.json`, `output/mvp-motir-20261126/`. 조회 시점 표본이므로 전체 보도량이나 장기 안정성을 뜻하지 않는다.

## 공식 근거

- [산업통상부 보도자료 및 RSS 버튼](https://www.motir.go.kr/kor/article/ATCL3f49a5a8c)
- [산업통상부 저작권 정책](https://www.motir.go.kr/kor/contents/81)
- [검증한 원문 링크](https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/172458/view)
- [NIST 공식 RSS 안내](https://www.nist.gov/coo/nist-rss-feeds): [Manufacturing](https://www.nist.gov/news-events/manufacturing/rss.xml), [Electronics](https://www.nist.gov/news-events/electronics/rss.xml)
- [Infineon 공식 보도자료](https://www.infineon.com/about/press/press-releases)
- [Siemens 과거 RSS 전환 안내](https://press.siemens.com/global/en/pressrelease/rss-feed-switched-over-new-corporate-structure-october-1-2014-please-check-your-rss)
- [eeNews 소개](https://www.eenewseurope.com/en/about/), [Automation.com 콘텐츠 안내](https://www.automation.com/en-us/submit-content)
