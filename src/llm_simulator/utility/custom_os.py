import os


class EnvironmentError(Exception):
    def __init__(self, missing_word: str) -> None:
        super().__init__(f"Missing environment variable: {missing_word}")


class CustomOS:
    @staticmethod
    def getenv(var_name: str, substitute: str | None = None) -> str:
        value = os.getenv(var_name)
        if value is None:
            if substitute is None:
                raise EnvironmentError(f"Environment variable {var_name} not found.")
            return substitute
        return value
