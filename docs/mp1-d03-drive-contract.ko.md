# MP1 D-03 — Google Drive 읽기 전용 계약

## 범위

I-03은 OAuth Authorization Code와 PKCE 및 최소 읽기 전용 scope로 한 소유자의 Google Drive를 연결한다. 검색 후 선택 파일 읽기만 지원하며 전체 동기화, 쓰기, 삭제, 공유, 권한 변경은 하지 않는다.

## 데이터와 보안

Token은 private connection store에만 남고 export, event, log, engine, browser 응답에서 제외된다. 검색 metadata와 선택 발췌문은 소유자 로컬에 남는다. 외부 engine에는 기존 문서 승인 경계가 요청별 최소 선택 발췌문을 허용하기 전 Drive 내용을 전달하지 않는다.

## API와 acceptance

Connector는 connect, health, search, 선택 읽기, disconnect를 제공한다. Disconnect는 로컬 token 저장을 폐기하고 redacted audit metadata를 남긴다. Fixture는 PKCE state 불일치, 만료 token, scope 거절, 결과 redaction, 승인 거절, disconnect를 다룬다. 자동 테스트는 모든 경로를 다루며 I-03은 Drive 쓰기 capability를 추가하지 않는다.
