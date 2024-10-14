class UserInteraction:
    GREEN = '\033[92m'
    RESET = '\033[0m'

    @staticmethod
    def _print_green(text: str):
        print(f"{UserInteraction.GREEN}AI: {text}{UserInteraction.RESET}")

    @staticmethod
    def greeting():
        UserInteraction._print_green("Что вас интересует?")
        return input("User: ")

    @staticmethod
    def get_context():
        UserInteraction._print_green("Можете предоставить больше контекста?")
        return input("User: ")

    @staticmethod
    def get_input(prompt: str) -> str:
        UserInteraction._print_green(prompt)
        return input("User: ")