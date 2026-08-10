# 웹 게시판(Web Board)
- 계정 없이 누구나 조회,등록,수정 변경 가능한 웹/앱 게시판
## 기술 스택
### Web Server
- Nginx (8080/443 포트) 
### Frontend
- React 19 / TypeScript
- 라우팅 : React Router
-빌드 도구: Vite (개발서버 5173 port)
- 스타일 : Tailwind CSS
- 패키지 관리: npm
### Backend
-Python 3.13 / Uvicorn (8000 port) / FastAPI / SQLite
## 환경 격리
- Python: uv로 관리하며 .venv/에 격리한다. pip와 전역 설치를 사용하지 않는다
- Node/React: npm install로 node_modules/에 격리한다. npm install -g를 사용하지 않는다
- 런타임 버전: mise로 고정한다 (.mise.toml에 Python·Node 버전 명시) 
- Nginx: 시스템에 설치하되, 설정은 프로젝트 내 nginx/dev.conf· nginx/prod.conf로만 관리한다. 
시스템 기본 설정(예 /opt/homebrew/etc/nginx/)을 수정하지 않는다
- 모든 실행 명령은 uv run 또는 npm run을 거친다 (전역 명령 직접 호출 금지) 
- 패키지 관리: uv (pip 사용 안한다)
- SQLite : uv로 관리하고 격리한다.
## 격리 상태 확인
- Python: `uv run which python` → `.venv/bin/python` 이어야 한다
- Node: `mise current` → `.mise.toml`의 버전과 일치해야 한다
## DB 구조
- SQLite 데이터 파일: data/board.db에 저장한다, 데이터 파일은 gitignore 에 등록하고 커밋하지 않는다.
- ORM : SQLAlchemy 사용한다.
## 실행 구조
개발과 운영 모두 Nginx를 경유한다. 
브라우저는 항상 Nginx에만 접속하며 vite(5173)와 uvicorn(8000)에는 직접 접속하지 않는다.
### 개발
/ : vite(5173)로 프록시 , /dist 를 사용하지 않는다.
### 운영
/ : Fronend/dist 를 사용한다.
## 프로젝트 구조
- Frontend/src/ : React 소스 (.tsx, .ts, .css)
- Frontend/dist/ : 빌드된 React 정적 파일(HTML/JS/CSS) , 직접 수정 금지(npm run build로 재생성)
- Frontend/package.json : 프론트 의존성, npm 명령은 Frontend/ 에서 실행한다.
- Backend
app/main.py : FastAPI 진입점
app/routers/ : API 엔드포인트 (백엔드 관문)
app/models/ : SQLAlchemy ORM 모델, DB 테이블 구조 정의
app/schemas/ : Pydantic 데이터 모델 (유효성 검사). API 요청/응답 검증
app/services/ : 비즈니스 로직
app/repository/ : DB 세션을 통해 쿼리(Query)를 실행하는 계층, 모든 데이터 처리는 repository에서만 한다.
app/database.py : DB관련 정의
data/board.db : 게시판 데이터 저장
tests/routers/
tests/services/ 
tests/repository/ 
tests/conftest.py : pytest 공용 설정
## 데이터 모델
### 게시판 데이터 구조 (모든 계층에서 동일하게 유지)
| 필드 | 타입 | 제약 | 설명 |
| id | str (UUID) | PK | 게시글 고유 ID |
| title | str | 필수, 1~100자 | 제목 |
| content | str | 필수, 1자 이상 | 본문 |
| author | str | 필수, 1~50자 | 작성자 |
| view_count | int | 기본 0 | 조회수 |
| created_at | datetime | 자동 생성 | 작성 시각 |
| updated_at | datetime | 자동 갱신 | 수정 시각 |
- id는 서버에서 UUID로 생성한다 (클라이언트가 지정하지 않는다).
-created_at / updated_at은 서버가 관리한다 (요청 본문으로 받지 않는다).
-updated_at은 수정 시각마다 갱신한다.
## 핵심 기능 (API 단위)
- 게시판 목록 조회
- 특정 게시물 조회
- 게시글 작성시 비밀번호 필수 입력
- 게시글 수정, 삭제 기능 , 비밀번호가 일치해야 수정,삭제 가능 하다.
- 10개의 게시글 마다 페이지 생성 한다.
- 상용 수준의 게시판 디자인 추가 한다.
## 프로젝트 용어
## 요구사항
- 모든 함수에 타입 힌트를 작성한다
- routers / services / repository의 공개 함수에는 pytest 테스트를 작성한다
- 테스트는 실제 data/board.db을 사용하지 않고 별도로 만들어서 테스트 한다
## 이중 표기 (SQL , ORM 병기)
- 이 프로젝트는 repository 계층의 모든 DB 접근을 raw SQL 과 SQLAlchemy ORM 2가지 방식으로 작성한다.
### 규칙
-SQLAlchemy 를 사용하지만 개발은 SQL을 직접 사용하도록 해주고 각 SQL마다 ORM Method 호출을 주석으로 해줘
-DB 접근 함수마다 두 구현을 모두 소스에 넣는다
1) raw SQL: text()를 사용해 실제 SQL 문자열을 직접 실행한다. 
2) ORM: 같은 동작을 하는 SQLAlchemy ORM 구문.
- 기본 상태는 SQL 활성 / ORM 주석 처리. 
- SQL과 ORM은 서로 완전히 동일한 결과를 반환해야 한다. 둘 중 하나만 실행해도 게시판이 정상 동작하도록 작성한다. 
- 각 SQL 바로 밑에, 대응하는 ORM 구문을 주석으로 붙인다. 두 방식이 1:1로 짝을 이루도록 배치한다.
## 규칙
- 현재 폴더에 가상환경을 만들고 활성화한후 개발 환경을 구성하고 가상환경 적정성을 확인후 개발 진행한다
- 데이터는 data/board.db에 저장한다
- 파일 읽기/쓰기는 storage.py에서만 처리한다 (다른 파일에서 직접 파일을 열지 않는다)
- 하나의 작업 단위(기능 추가, 버그 수정)가 끝나면 커밋을 제안한다, 커밋 메시지는 한국어로 작성한다
## 모든 설명과 주석은 한국어로 작성한다