# Git 커밋 및 PR 자동 생성 CLI 도구 (B6-2)

## 1단계: 사전 환경변수 설정
### 파이썬 사전 환경설정 및 API KEY 세팅 진행

- 1-1 가상환경 세팅
```bash
python -m venv venv #venv 이름으로 가상환경 생성
source venv/Scripts/activate #가상환경 실행 -> deactivate
pip install google-generativeai # gemini api 통신 위한 패키지 설치
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