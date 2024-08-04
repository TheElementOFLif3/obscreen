from src.exceptions.HttpClientException import HttpClientException


class FolderNotFoundException(HttpClientException):
    @property
    def code(self) -> int:
        return 404

    @property
    def description(self) -> int:
        return "Folder not found"
