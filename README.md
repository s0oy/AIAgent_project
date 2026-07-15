# AIAgent_project

Claude API를 활용해 AI 에이전트의 동작 원리를 하나씩 구현해보는 학습 프로젝트 모음입니다.
예제를 그대로 따라 치는 데서 멈추지 않고, **직접 문제를 발견하고 개선하는 것**을 목표로 합니다.

---

## 프로젝트 목록

| 프로젝트 | 설명 | 핵심 개념 |
|---------|------|-----------|
| [persona](./persona) | 페르소나 기반 실시간 스트리밍 챗봇 | System Prompt, SSE 스트리밍, 멀티턴 대화 |
| [playground](./playground) | 모델·파라미터 비교 플레이그라운드 | 모델 비교, temperature / max_tokens, 토큰·응답속도 측정 |

각 프로젝트 폴더 안에 상세 README가 있습니다.

---

## 공통 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/s0oy/AIAgent_project.git
cd AIAgent_project
```

### 2. 가상환경 및 의존성 설치

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. API 키 설정

[Anthropic Console](https://console.anthropic.com)에서 키를 발급받은 뒤, 루트에 `.env` 파일을 만듭니다.

```bash
cp .env.example .env
```

`.env` 파일에 발급받은 키를 입력합니다.

```
ANTHROPIC_API_KEY=sk-ant-...
```

> `.env`는 `.gitignore`에 등록되어 있어 저장소에 올라가지 않습니다.

### 4. 원하는 프로젝트 실행

```bash
python persona/app.py        # 페르소나 챗봇   (localhost:5000)
python playground/app.py     # 모델 플레이그라운드 (localhost:5001)
```

---

## 기술 스택

| 구분 | 사용 기술 |
|------|-----------|
| Language | Python |
| Web | Flask |
| LLM | Claude API |
| 실시간 통신 | Server-Sent Events (SSE) |
| 설정 관리 | python-dotenv |

---

## 저장소 구조

```
AIAgent_project/
├── persona/                # 페르소나 챗봇
│   ├── app.py
│   ├── templates/index.html
│   ├── static/style.css
│   └── README.md
├── playground/             # 모델 비교 플레이그라운드
│   ├── app.py
│   ├── templates/index.html
│   ├── static/style.css
│   └── README.md
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

> 이 저장소의 예제들은 수업에서 제공된 코드를 기반으로 시작해,
> 직접 구조를 분석하고 수정·확장한 학습 결과물입니다.
> 원본 대비 변경한 내용은 각 프로젝트의 README에 정리했습니다.