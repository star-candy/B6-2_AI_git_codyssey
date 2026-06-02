import os
import sys
import dotenv


# 분리된 모델(Model)과 뷰(View)를 가져옵니다. (MVC 아키텍처 패턴 적용)
from models import GitModel, SecurityModel, AIModel
from views import ConsoleView


class AppController:
    """명령을 해석하고 Model과 View를 조율합니다. (Controller 역할)"""

    def __init__(self, args):
        # 사용자로부터 받은 명령줄 인자(CLI arguments)를 저장합니다.
        self.args = args
        # 출력을 담당할 View 객체를 생성합니다.
        self.view = ConsoleView()

        # [중요] API Key 검증 및 로드
        dotenv.load_dotenv()  # .env 파일에서 환경변수 로드

        api_key = os.environ.get("AI_API_KEY")
        if not api_key:
            # [중요] 예외 처리: API 키가 없으면 프로그램이 동작할 수 없으므로,
            # 사용자에게 알리고 즉시 종료(Exit 1: 에러 종료)합니다.
            self.view.print_error("AI_API_KEY 환경변수가 설정되지 않았습니다.")
            self.view.print_info('예) export AI_API_KEY="YOUR_KEY"')
            sys.exit(1)

        # 외부 서비스(OpenAI)와 통신할 AI 모델 객체 초기화
        self.ai_model = AIModel(api_key, args.model, args.temperature, args.max_tokens)
        self.git_model = GitModel()

    def _prepare_diff(self) -> str:
        """Git 변경 사항을 수집하고 안전 모드를 적용하는 핵심 전처리 함수입니다."""
        status = self.git_model.get_status()
        if not status:
            # [중요] 조기 종료(Early Return/Exit): 변경된 코드가 없다면
            # 불필요한 AI API 호출을 막기 위해 프로그램 정상 종료(Exit 0) 처리합니다.
            self.view.print_info(
                "변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다."
            )
            sys.exit(0)

        diff_text = self.git_model.get_diff()

        file_count = len(status.split("\n"))
        diff_lines = len(diff_text.split("\n"))

        self.view.print_info(f"Git status 수집 완료: {file_count}개 파일 변경 감지")
        self.view.print_info(f"Git diff 수집 완료: {diff_lines}줄")

        # [중요] 보안 및 비용 절감 로직 적용
        # 사용자가 --safe-mode 옵션을 켰을 때만 민감 정보를 마스킹하고 토큰 길이를 제한합니다.
        if self.args.safe_mode:
            self.view.print_info(
                "Safe Mode 동작: 민감정보 마스킹 및 길이 제한이 적용됩니다."
            )
            diff_text = SecurityModel.apply_safe_mode(diff_text)

        return diff_text

    def run_commit(self):
        # 1. Controller가 Model을 호출하여 데이터를 준비합니다.
        diff_text = self._prepare_diff()

        # [중요] 프롬프트 엔지니어링 (System Prompt)
        # AI에게 명확한 역할 부여("시니어 엔지니어")와 구체적인 출력 규칙(형식, 글자 수 제한 등)을
        # 지시하여 일관되고 퀄리티 높은 커밋 메시지를 유도합니다.
        system_prompt = (
            "너는 훌륭한 시니어 소프트웨어 엔지니어다. 제공된 git diff를 기반으로 커밋 메시지를 작성해라.\n"
            "규칙:\n"
            "1. 첫 줄은 커밋 제목으로 50자 이내(최대 72자)로 작성한다. (feat, fix, refactor 등의 컨벤션 사용)\n"
            "2. 두 번째 줄은 비우고, 세 번째 줄부터 본문을 작성한다.\n"
            "3. 본문에는 변경된 핵심 파일이나 모듈을 1~3개 언급해라.\n"
            "4. 핵심 변경 사항을 1~2개의 불릿 포인트(-)로 요약해라."
        )

        self.view.print_info("AI API 요청 중... (Commit Message)")
        try:
            # 2. 준비된 데이터와 프롬프트를 AI Model에 전달하여 텍스트를 생성합니다.
            result = self.ai_model.generate_text(
                system_prompt, f"Git Diff:\n{diff_text}"
            )
            self.view.print_info("커밋 메시지 생성 완료 (API 1회 호출)")

            # 3. 생성된 결과를 View를 통해 사용자에게 출력합니다.
            self.view.print_result("Commit Message", result)
        except Exception as e:
            # [중요] API 통신 실패, 네트워크 단절 등 예기치 못한 런타임 에러를 방어합니다.
            self.view.print_error(str(e))

    def run_pr(self):
        diff_text = self._prepare_diff()

        # [중요] PR용 특화 프롬프트
        # PR 양식(Why, What, How to Test)에 맞춰서 마크다운(Markdown) 형태로 출력하도록 강제합니다.
        system_prompt = (
            "너는 코드 리뷰를 요청하는 개발자다. 제공된 git diff를 기반으로 Pull Request 양식을 작성해라.\n"
            "규칙:\n"
            "1. 맨 첫 줄은 PR 제목으로, 80자 이내로 작성한다.\n"
            "2. 이후 아래의 3가지 섹션 헤더(##)를 반드시 포함한다.\n"
            "   ## Why\n"
            "   ## What\n"
            "   ## How to Test\n"
            "3. 각 섹션에는 최소 1개 이상의 불릿 포인트(-)가 있어야 한다."
        )

        self.view.print_info("AI API 요청 중... (Pull Request)")
        try:
            result = self.ai_model.generate_text(
                system_prompt, f"Git Diff:\n{diff_text}"
            )

            # [중요] 데이터 후처리 (Parsing & Formatting)
            # AI가 하나의 통짜 문자열로 반환한 결과를, 첫 줄(제목)과 나머지(본문)로 분리하여
            # 사용자에게 더 깔끔하고 가독성 좋게 보여주기 위한 텍스트 처리 과정입니다.
            lines = result.split("\n")
            title = lines[0] if lines else "제목 없음"
            body = "\n".join(lines[1:]).strip()

            self.view.print_info("PR 초안 생성 완료 (API 1회 호출)")
            self.view.print_result("PR Title", title)
            self.view.print_result("PR Body", body)
        except Exception as e:
            self.view.print_error(str(e))
