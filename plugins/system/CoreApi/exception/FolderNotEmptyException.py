from src.exceptions.HttpClientException import HttpClientException


class FolderNotEmptyException(HttpClientException):
    @property
    def code(self) -> int:
        return 400

    @property
    def description(self) -> int:
        return "Folder is not empty"
