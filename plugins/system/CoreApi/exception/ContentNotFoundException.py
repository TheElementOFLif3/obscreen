from src.exceptions.HttpClientException import HttpClientException


class ContentNotFoundException(HttpClientException):
    @property
    def code(self) -> int:
        return 404

    @property
    def description(self) -> int:
        return "Content not found"
