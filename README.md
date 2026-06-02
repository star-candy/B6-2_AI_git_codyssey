# Git 커밋 및 PR 자동 생성 CLI 도구 (B6-2)

## 1단계: 사전 환경변수 설정
### 파이썬 사전 환경설정 및 API KEY 세팅 진행

- 1-1 가상환경 세팅
```bash
python -m venv venv #venv 이름으로 가상환경 생성
source venv/Scripts/activate #가상환경 실행 -> deactivate
pip install -q -U google-genai # gemini api 통신 위한 패키지 설치
pip install python-dotenv #API KEY 외부 세팅 위한 패키지 설치
```

- 1-2 API KEY 세팅 (.env 파일)
```bash
#key value 형식으로 작성
AI_API_KEY="sk-your-api-key-here"
```

```python
import dotenv
dotenv.load_dotenv('.env파일의 경로') #env 파일 불러오기

api_key = os.environ.get("AI_API_KEY") #환경변수 불러오기
```
--------
### 실행 옵션 안내
#### python main.py command --model --temperature --max-tokens --safe-mode로 구성
- command
    - commit : 변경사항 확인 후 커밋 메시지를 ai가 작성한다.
    -  pr : 변경사항 확인 후 풀 리퀘 메시지를 ai가 작성한다.
- --model
    - 사용할 모델명을 명시한다.
    - 기본은 gemini-2.5-flash가 사용될 것
    - --model gemini-3.5 형식으로 변경 가능
- --temperature
    - 답변 생성 시 다양성 조절 파라미터
    - --temperature 0.5 등으로 수정 가능
- --max-tokens
    - 생성 가능 최대 토큰 수 조절 파라미터
    - --max-tokens 300 등으로 수정 가능
- --safe-mode
    - 민감정보 마스킹 및 길이 조절 파라미터 (200문장)
    - --safe-mode 명시 경우 사용됨
- --help
    - 옵션 사용방법 안내
    - python main.py --help로 확인 가능

----
### 예시 출력
- python main.py commit
```bash
[INFO] Git status 수집 완료: 1개 파일 변경 감지
[INFO] Git diff 수집 완료: 13줄
[INFO] AI API 요청 중... (Commit Message)
[INFO] 커밋 메시지 생성 완료 (API 1회 호출)

--- Commit Message ---
fix: .env 파일 경로를 macOS 환경에 맞게 수정

code/controllers.py
----------------------
```

- python main.py pr
```bash
[INFO] Git status 수집 완료: 1개 파일 변경 감지
[INFO] Git diff 수집 완료: 13줄
[INFO] AI API 요청 중... (Pull Request)
[INFO] PR 초안 생성 완료 (API 1회 호출)

--- PR Title ---
controllers.py에서 .env 파일 로딩 경로 수정
----------------

--- PR Body ---
## Why
- 현재 `.env` 파일 로딩 경로가 특정

```

### 주의 사항
- max token 값을 650 이상으로 증가시킬 경우 비용 청구 가능성 있음에 유의
- 상위 model로 수정시 비용 청구 가능성 있음에 유의
- api key, 이메일 등 명시 가능성 있음으로 --safe-mode 사용을 권장