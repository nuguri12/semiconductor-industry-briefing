# 수집 테스트

## 이메일 시험

미리보기는 --email-check --to nuguri12@gmail.com 으로 확인한다. 실제 발송에는 --send --to nuguri12@gmail.com --delivery-id test-20261121-01을 지정한다. 동일 시험 재실행 시 delivery-id를 유지한다. 발신 설정은 SMTP_HOST, SMTP_PORT(STARTTLS 기본 587), SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM 환경변수로 제공한다. 비밀번호는 채팅이나 저장소에 기록하지 않는다.

로컬 SQLite 파일 .briefing-deliveries.sqlite3에 발송 상태를 저장한다. 성공·실패·응답불명·전송중인 기존 ID는 자동 재전송하지 않는다. 파일을 지우거나 다른 ID를 쓰면 중복 방지가 적용되지 않는다. 이 방식은 로컬 시험용이며 운영 배포는 관리형 PostgreSQL 설계를 따른다. 빈 결과·부분 결과·전부 무효인 결과는 발송 보류한다. 실제 SMTP 수락과 수신함 도착은 별도 확인한다.

Python 표준 라이브러리로 GDELT 메타데이터를 수집한다. 응답 검증, 제목 공백·HTML entity 정리, HTTP(S) 링크 검사, 관측 시각 KST 변환 후 메시지 또는 JSON을 출력한다.

```powershell
python -m briefing --input tests/fixtures/articles.json
python -m briefing --query '(Infineon OR ASE OR HYUNDAI OR MOBIS)' --hours 24 --limit 10
python -m briefing --query 'Infineon' --json
python -m unittest discover -s tests -v
```

현재 PC의 Python 실행 파일은 C:/Users/User/AppData/Local/Programs/Python/Python314/python.exe다. PowerShell에서 해당 경로 앞에 &를 붙여 실행할 수 있다.

기본 조회는 최근 24시간·최대 25건이며 운영 시간창은 미정이다. 조회 상한 도달 시 누락 가능성을 표시한다. timeout은 요청당 45초, 응답 크기는 5 MB까지다. 오류는 종료 코드 1로 보고한다. 원문 전문 수집·번역·GPT 요약은 후속 범위다. seendate는 관측 시각으로 표시하며 원문 발행 시각으로 간주하지 않는다. 검색어 ASE 등의 잡음과 중복 병합 정책은 결과 확인 후 결정한다.

## 알고리즘과 실패 처리

1. 명시적으로 입력된 검색어와 조회 범위로 GDELT ArtList JSON 요청을 만든다. 네 검색어는 `(Infineon OR ASE OR HYUNDAI OR MOBIS)`로 묶을 수 있다.
2. HTTP 429·502·503·504는 최대 한 번 재시도한다. Retry-After의 초 또는 HTTP 날짜를 해석하고 최소 5초를 기다린다. 값이 없거나 잘못되면 5초를 사용한다. 서버 대기가 60초를 초과하면 더 일찍 재요청하지 않고 오류로 종료한다. 두 번째 실패, 인증 오류와 네트워크 오류는 그대로 보고한다. 실행당 최대 두 요청이다.
3. JSON과 articles 배열을 검사한다. 잘못된 응답은 오류로 종료한다. 항목별 제목·HTTP(S) URL·호스트·포트를 검사하고 자격 증명이나 제어문자가 든 URL은 제외한다. 제외 건수를 남긴다.
4. 제목의 HTML entity와 공백을 정리한다. 관측시각은 고정 형식 및 실제 날짜를 검사해 KST로 변환한다. 누락·오류는 null로 남긴다. 발행시각은 별도 미확인 필드다.
5. 기사 순서와 원문 링크를 보존해 메시지 또는 JSON을 출력한다. JSON status는 ok, empty, partial, invalid_records로 구분한다. 모든 항목이 무효일 때는 메시지에도 검증 제외 사실을 표시한다. 항목별 검증 제외는 정상 수집 결과의 진단 상태이며 종료 코드는 0이다.

테스트는 실제 대기·네트워크 호출을 모의 처리한다. 성공, 빈 응답, JSON 오류, 과대 응답, 재시도 제한과 Retry-After, 잘못된 URL·시간, 전체 무효 항목을 검증한다. 실제 GDELT는 이전 실행에서 HTTP 429를 반환했으므로 실수집 성공은 별도 확인 대상이다.

[GDELT 공식 안내](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
