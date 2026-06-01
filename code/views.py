class ConsoleView:
    """터미널 환경에서의 출력 형식을 담당합니다."""

    @staticmethod
    def print_info(message: str):
        print(f"[INFO] {message}")

    @staticmethod
    def print_error(message: str):
        print(f"[ERROR] {message}")

    @staticmethod
    def print_result(title: str, content: str):
        print(f"\n--- {title} ---")
        print(content)
        print("-" * (len(title) + 8))
