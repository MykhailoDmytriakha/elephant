class UserInteraction:
    @staticmethod
    def greeting():
        print("AI: Что вас интересует?")
        return input("User: ")

    @staticmethod
    def get_context():
        print("AI: Можете предоставить больше контекста?")
        return input("User: ")

    @staticmethod
    def get_input(prompt: str) -> str:
        print(f"AI: {prompt}")
        return input("User: ")