# 웹 게시판 (Web Board)

계정 없이 누구나 조회·등록·수정·삭제할 수 있는 웹 게시판입니다. 수정/삭제는 작성 시 입력한 비밀번호가 일치해야 가능합니다.

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| Web Server | Nginx (8080 / 443) |
| Frontend | React 19, TypeScript, React Router, Vite (개발 서버 5173), Tailwind CSS 4 |
| Backend | Python 3.13, FastAPI, Uvicorn (8000), SQLAlchemy, SQLite |
| 패키지/런타임 관리 | uv(Python), npm(Node), mise(런타임 버전 고정) |

브라우저는 항상 Nginx(8080)에만 접속합니다. 개발 모드에서는 Nginx가 `/`를 vite(5173)로, `/api/`를 uvicorn(8000)으로 프록시하고, 운영 모드에서는 `/`를 `Frontend/dist`의 정적 파일로 서빙합니다.

## 프로젝트 구조

```
board/
├── dev.ps1              # 세 서버를 한 번에 start/stop/status/restart (PowerShell)
├── nginx/
│   ├── dev.conf        # 개발용 (/ -> vite, /api/ -> uvicorn)
│   └── prod.conf       # 운영용 (/ -> Frontend/dist, /api/ -> uvicorn)
├── Frontend/
│   ├── src/
│   │   ├── pages/         # BoardList, BoardDetail, BoardWrite, BoardEdit
│   │   ├── components/    # CommentSection 등 페이지 간 공유되지 않는 조립 컴포넌트
│   │   ├── api/client.ts
│   │   └── lib/format.ts
│   └── dist/            # npm run build 산출물 (직접 수정 금지)
├── Backend/
│   ├── app/
│   │   ├── main.py        # FastAPI 진입점
│   │   ├── database.py    # SQLAlchemy 엔진/세션, SQLite FK(PRAGMA) 설정
│   │   ├── models/        # ORM 모델 (post, comment)
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── repository/     # DB 접근 (raw SQL / ORM 병기)
│   │   ├── services/       # 비즈니스 로직 + security.py(해싱)/errors.py(공통 예외)
│   │   └── routers/        # API 엔드포인트
│   ├── data/board.db      # SQLite 데이터 파일 (커밋 대상 아님)
│   └── tests/              # pytest (routers / services / repository)
├── logs/, temp/          # nginx가 요구하는 런타임 디렉터리 (.gitkeep만 추적)
└── .run/                 # dev.ps1이 남기는 PID/로그 (커밋 대상 아님)
```

## 사전 준비

- [mise](https://mise.jdx.dev/) 설치 후 프로젝트 루트에서 `mise install` (`.mise.toml`에 Python 3.13 / Node 22 고정)
- [uv](https://docs.astral.sh/uv/) 설치
- Nginx 설치 (설정은 시스템 기본 설정이 아닌 `nginx/dev.conf`, `nginx/prod.conf`만 사용)
  - Windows: `winget install --id nginxinc.nginx` (설치 직후에는 새 터미널을 열어야 PATH가 반영됩니다)

## 빠른 실행 (Windows, `dev.ps1`)

Backend/Frontend/Nginx 세 개를 매번 따로 띄우는 대신, 프로젝트 루트에서 스크립트 하나로 관리할 수 있습니다.

```powershell
.\dev.ps1 start            # 세 서버 모두 기동
.\dev.ps1 status           # 상태 확인 (프로세스/포트)
.\dev.ps1 stop             # 세 서버 모두 종료
.\dev.ps1 restart          # stop 후 start
.\dev.ps1 start -Env prod  # 운영 모드 (vite 대신 Frontend/dist를 nginx가 직접 서빙)

.\dev.ps1 logs                                # 전체 로그 마지막 부분 출력
.\dev.ps1 logs -Service backend               # backend/frontend/nginx/nginx-access/nginx-error 중 선택
.\dev.ps1 logs -Service nginx-error -Follow   # 실시간 tail (Ctrl+C로 종료)
```

기동 후 브라우저는 `http://localhost:8080`으로 접속합니다. Backend/Frontend 로그는 `.run/backend.log`, `.run/frontend.log`에, Nginx 로그는 `logs/access.log`, `logs/error.log`에 쌓입니다.

## 개발 환경 실행 (수동)

`dev.ps1`이 내부적으로 하는 일을 직접 하나씩 실행하는 방법입니다. 세 프로세스를 각각 띄운 뒤 브라우저는 `http://localhost:8080`으로만 접속합니다.

```bash
# 1) 백엔드
cd Backend
uv sync
uv run python -m uvicorn app.main:app --reload --port 8000

# 2) 프론트엔드
cd Frontend
npm install
npm run dev

# 3) Nginx (프로젝트 루트에서)
nginx -p "$(pwd)" -c nginx/dev.conf
```

- 격리 확인: `uv run which python` → `.venv` 내부 경로 (Windows는 `.venv\Scripts\python.exe`), `mise current` → `.mise.toml`과 버전 일치
- Nginx 종료: `nginx -p "$(pwd)" -c nginx/dev.conf -s stop` (Windows에서는 `taskkill /IM nginx.exe /F`)

## 운영 환경 실행

```bash
cd Frontend && npm run build   # Frontend/dist 생성
cd Backend && uv run python -m uvicorn app.main:app --port 8000
nginx -p "<project-root>" -c nginx/prod.conf
```

또는 `.\dev.ps1 start -Env prod` (사전에 `npm run build`로 `Frontend/dist`를 최신 상태로 만들어 두어야 합니다).

## 테스트

```bash
cd Backend
uv run pytest
```

`routers` / `services` / `repository` 공개 함수마다 테스트가 있으며, 실제 `data/board.db`가 아닌 인메모리 SQLite(테스트 전용 DB)를 사용합니다.

## API 개요

베이스 경로: `/api` (Nginx 경유 시 `http://localhost:8080/api`)

| 메서드 | 경로 | 설명 | 비밀번호 필요 |
| --- | --- | --- | --- |
| GET | `/posts?page=1` | 목록 조회 (10개씩 페이지네이션) | - |
| GET | `/posts/{id}` | 상세 조회 (조회수 +1) | - |
| POST | `/posts` | 게시글 작성 | 필수 (본문에 포함) |
| PUT | `/posts/{id}` | 게시글 수정 | 필수 (본문에 포함, 불일치 시 403) |
| DELETE | `/posts/{id}` | 게시글 삭제 | 필수 (본문에 포함, 불일치 시 403) |
| GET | `/posts/{post_id}/comments` | 댓글 목록 조회 | - |
| POST | `/posts/{post_id}/comments` | 댓글 작성 | 필수 (본문에 포함) |
| DELETE | `/posts/{post_id}/comments/{comment_id}` | 댓글 삭제 | 필수 (본문에 포함, 불일치 시 403) |

비밀번호는 평문으로 저장하지 않고 `hashlib.pbkdf2_hmac` + 솔트로 해싱해 저장합니다 (`app/services/security.py`, post/comment 공통).

## 데이터 모델

**posts**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | str (UUID) | 서버에서 생성 |
| title | str | 1~100자 |
| content | str | 1자 이상 |
| author | str | 1~50자 |
| view_count | int | 기본 0 |
| created_at / updated_at | datetime | 서버가 관리 |

**comments**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | str (UUID) | 서버에서 생성 |
| post_id | str (FK → posts.id) | `ON DELETE CASCADE` — 게시글 삭제 시 댓글도 함께 삭제됨 |
| author | str | 1~50자 |
| content | str | 1자 이상 |
| created_at | datetime | 서버가 관리 |

SQLite는 기본적으로 외래키 제약을 강제하지 않으므로, `database.py`에서 연결마다 `PRAGMA foreign_keys=ON`을 켜서 cascade 삭제가 실제로 동작하도록 했습니다.

## repository 계층 규칙

모든 DB 접근은 `app/repository/`에서만 수행하며, 각 함수는 raw SQL(`text()`)과 SQLAlchemy ORM 두 가지 구현을 1:1로 병기합니다. 기본은 SQL이 활성화된 상태이고, 바로 아래 ORM 구문은 주석 처리되어 있습니다. 필요 시 두 블록을 서로 바꿔 활성화해도 동일하게 동작하도록 각 블록이 자체 `return`까지 포함해 독립적으로 완결되어 있습니다.

## 자주 겪는 문제 (Windows)

- **`npm install`/`npm run dev` 실행 시 `PSSecurityException` (스크립트 실행 불가)**
  PowerShell 실행 정책 때문입니다. `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` 실행 후 다시 시도하세요. (`dev.ps1`은 `npm.cmd`를 직접 호출해서 이 문제를 겪지 않습니다.)

- **uvicorn 기동 시 `[WinError 10013] 액세스 권한에 의해 숨겨진 소켓에 액세스를 시도했습니다`**
  다른 프로세스가 8000번 포트를 쓰고 있거나, Hyper-V/WSL2가 부팅 시 동적으로 예약한 포트 범위에 8000이 포함된 경우입니다.
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue   # 점유 프로세스 확인
  netsh interface ipv4 show excludedportrange protocol=tcp             # 예약 범위 확인
  net stop winnat; net start winnat                                    # Hyper-V/WSL 예약 문제 해결
  ```

- **`nginx: [emerg] CreateFile() ".../conf/nginx.conf" failed`**
  `-c` 옵션 없이 `-p`만 준 경우 나타납니다. 반드시 프로젝트 루트에서 `-p`와 `-c`를 함께 지정하세요: `nginx -p "<project-root>" -c nginx/dev.conf`.

- **nginx 실행 후 셸이 응답 없음**
  일부 환경에서 `nginx.exe`가 데몬화 후 제어권을 바로 안 돌려주는 경우가 있습니다. 일반 PowerShell 콘솔에서 직접 실행하면 정상적으로 백그라운드로 뜹니다. 스크립트에서 다루려면 `Start-Process`로 fire-and-forget 하세요 (`dev.ps1` 참고).
