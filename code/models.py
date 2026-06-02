import subprocess  # 코드 내에서 명령어를 실행하기 위한 모듈

# import requests  # AI 모델과 통신하기 위한 HTTP 요청을 보내는 모듈
import re  # 정규표현식 처리를 위한 모듈
from google import genai  # 구글 공식 패키지 임포트
from google.genai import types


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
    """최신 Gemini SDK(google-genai)를 통한 AI 모델 통신을 담당합니다."""

    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 1. 최신 방식: 전역 설정(configure) 대신 Client 객체를 인스턴스화합니다.
        # (OpenAI 패키지를 사용할 때와 구조가 완전히 동일해졌습니다.)
        self.client = genai.Client(api_key=api_key)

    def generate_text(self, system_prompt: str, user_content: str) -> str:
        try:
            # 2. 최신 방식: 설정(Config) 객체 안에 온도, 토큰, 그리고 시스템 프롬프트까지 한 번에 묶습니다.
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )

            # 3. 최신 방식: Client를 통해 텍스트 생성을 요청합니다.
            response = self.client.models.generate_content(
                model=self.model_name, contents=user_content, config=config
            )

            return response.text.strip()

        except Exception as e:
            raise RuntimeError(f"최신 Gemini API 호출 중 오류 발생: {e}")
