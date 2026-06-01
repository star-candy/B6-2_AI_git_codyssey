import argparse  # cli상에서 입력된 명령어 인자를 처리하기 위한 라이브러리

from controllers import AppController


def main():
    # 명령어를 담아낼 parser 객체 생성
    parser = argparse.ArgumentParser(description="AI기반 GIT Commit/PR 자동 생성기")
    # command 규칙 생성, commit과 pr만 가능하도록 구성, help로 설명 추가
    parser.add_argument(
        "command", choices=["commit", "pr"], help="실행할 명령어 (commit 또는 pr)"
    )
    # --model 옵션 추가, 기본값은 "gpt-4.0-mini", help로 설명 추가
    parser.add_argument(
        "--model", default="gpt-4.0-mini", help="사용할 모델을 지정합니다."
    )
    parser.add_argument(
        "--temperature", type=float, default=0.3, help="생성 다양성 조절 (기본값: 0.3)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=500, help="최대 생성 토큰 수 (기본값: 500)"
    )
    # action='store_true' 설정을 통해 해당 단어가 옵션으로 적힐 시 True로 설정
    parser.add_argument(
        "--safe-mode", action="store_true", help="diff 민감 정보 마스킹 및 전송량 제한"
    )

    args = parser.parse_args()  # 사용자의 cli 입력을 파싱하여 분석, args에 전달

    app = AppController(args)
    if args.command == "commit":
        app.run_commit()
    elif args.command == "pr":
        app.run_pr()


if __name__ == "__main__":
    main()
