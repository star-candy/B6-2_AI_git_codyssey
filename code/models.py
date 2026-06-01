import subprocess  # 코드 내에서 명령어를 실행하기 위한 모듈
import requests  # AI 모델과 통신하기 위한 HTTP 요청을 보내는 모듈
import re  # 정규표현식 처리를 위한 모듈


class GitModel:
    """Git 명령어 실행 및 결과 수집을 담당합니다."""

    # git status와 git diff 명령어를 실행하여 결과를 반환하는 메서드입니다.
    # subprocess.run을 사용하여 명령어를 실행하고, 결과를 캡처하여 문자열로 반환합니다.
    @staticmethod
    def get_status() -> str:
        result = subprocess.run(
            ["git", "status", "--short"], capture_output=True, text=True
        )
        return result.stdout.strip()

    @staticmethod
    def get_diff() -> str:
        # 변경된 모든 사항을 가져오기 위해 HEAD 사용
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()
