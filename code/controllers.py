import os
import sys

# 분리된 모델과 뷰를 가져옵니다.
from models import GitModel, SecurityModel, AIModel
from views import ConsoleView


class AppController:
    """명령을 해석하고 Model과 View를 조율합니다."""

    def __init__(self, args):
        self.args = args
        self.view = ConsoleView()

        # API Key 검증
        api_key = os.environ.get("AI_API_KEY")
        if not api_key:
            self.view.print_error("AI_API_KEY 환경변수가 설정되지 않았습니다.")
            self.view.print_info('예) export AI_API_KEY="YOUR_KEY"')
            sys.exit(1)

        self.ai_model = AIModel(api_key, args.model, args.temperature, args.max_tokens)
        self.git_model = GitModel()

    def _prepare_diff(self) -> str:
        """Git 변경 사항을 수집하고 안전 모드를 적용합니다."""
        status = self.git_model.get_status()
        if not status:
            self.view.print_info(
                "변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다."
            )
            sys.exit(0)

        diff_text = self.git_model.get_diff()

        file_count = len(status.split("\n"))
        diff_lines = len(diff_text.split("\n"))

        self.view.print_info(f"Git status 수집 완료: {file_count}개 파일 변경 감지")
        self.view.print_info(f"Git diff 수집 완료: {diff_lines}줄")

        if self.args.safe_mode:
            self.view.print_info(
                "Safe Mode 동작: 민감정보 마스킹 및 길이 제한이 적용됩니다."
            )
            diff_text = SecurityModel.apply_safe_mode(diff_text)

        return diff_text

    def run_commit(self):
        diff_text = self._prepare_diff()

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
            result = self.ai_model.generate_text(
                system_prompt, f"Git Diff:\n{diff_text}"
            )
            self.view.print_info("커밋 메시지 생성 완료 (API 1회 호출)")
            self.view.print_result("Commit Message", result)
        except Exception as e:
            self.view.print_error(str(e))

    def run_pr(self):
        diff_text = self._prepare_diff()

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

            lines = result.split("\n")
            title = lines[0] if lines else "제목 없음"
            body = "\n".join(lines[1:]).strip()

            self.view.print_info("PR 초안 생성 완료 (API 1회 호출)")
            self.view.print_result("PR Title", title)
            self.view.print_result("PR Body", body)
        except Exception as e:
            self.view.print_error(str(e))
