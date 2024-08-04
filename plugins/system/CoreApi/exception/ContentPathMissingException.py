from src.exceptions.HttpClientException import HttpClientException


class ContentPathMissingException(HttpClientException):
    @property
    def code(self) -> int:
        return 400

    @property
    def description(self) -> int:
        return "Valid path is required"
