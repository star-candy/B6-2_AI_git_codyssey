import subprocess  # 코드 내에서 명령어를 실행하기 위한 모듈

# import requests  # AI 모델과 통신하기 위한 HTTP 요청을 보내는 모듈
import re  # 정규표현식 처리를 위한 모듈
import requests  # HTTP 요청을 보내기 위한 모듈


class GitModel:
    """Git 명령어 실행 및 결과 수집을 담당합니다."""

    # git status와 git diff 명령어를 실행하여 결과를 반환하는 메서드입니다.
    # subprocess.run을 사용하여 명령어를 실행하고, 결과를 캡처하여 문자열로 반환합니다.
    @staticmethod
    def get_status() -> str:
        # working dir, staging area의 변경사항을 보여줌 (요약본)
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.strip()

    @staticmethod
    def get_diff() -> str:
        # 변경된 모든 사항을 가져오기 위해 HEAD 사용
        # 마지막 커밋(HEAD) 이후 모든 변경사항 보여줌 (코드수준 변경사항)
        result = subprocess.run(
            ["git", "diff", "HEAD"], capture_output=True, text=True, encoding="utf-8"
        )
        return result.stdout.strip()


class SecurityModel:
    """민감 정보 필터링 및 텍스트 제한을 담당합니다."""

    @staticmethod
    def apply_safe_mode(diff_text: str, max_lines: int = 200) -> str:
        # 1. 길이 제한 (비용 및 토큰 방지) 200줄이 넘어가면 자른다
        lines = diff_text.split("\n")
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append(f"\n... (안전 모드: diff가 길어 {max_lines}줄로 잘렸습니다.)")
        # 배열 형태로 분할된 lines를 다시 하나의 몬자열로 통합한다.
        masked_text = "\n".join(lines)

        # 2. 민감 정보 마스킹 (간단한 정규식 적용)
        # re.sub(찾을_패턴, 바꿀_글자, 원본_텍스트) 형태로 동작
        # r == raw string, \를 이스케이프 문자로 인식하지 않도록 함
        # [] 내부 중 하나라도 일치하면 찾는다, +는 앞 문자가 1회 이상 반복 의미
        # \.는 . 문자 자체를 의미 (정규식에서 .은 모든 문자 의미하므로 이스케이프 필요)
        masked_text = re.sub(
            r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            "[EMAIL_MASKED]",
            masked_text,
        )
        # {}바로 앞 규칙이 최소 20회 이상(,) 반복되는 패턴을 찾아서 [API_KEY_MASKED]로 대체한다.
        masked_text = re.sub(r"(AI[a-zA-Z0-9]{20,})", "[API_KEY_MASKED]", masked_text)
        return masked_text


class AIModel:
    """requests 라이브러리를 사용해 직접 REST API 통신을 담당합니다."""

    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 1. 주소(URL): 어떤 모델을 사용할지 URL에 명시합니다.
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def generate_text(self, system_prompt: str, user_content: str) -> str:
        # 2. 헤더(Headers): API 키와 데이터 형식을 지정합니다.
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        # 3. 데이터(Payload): Gemini REST API 규격에 맞춘 JSON 구조입니다.
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }

        try:
            # POST 요청 전송
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=15
            )
            response.raise_for_status()

            # 4. 응답(Response) 파싱: 복잡한 JSON 구조에서 텍스트만 추출합니다.
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Gemini REST API 호출 중 오류 발생: {e}")
