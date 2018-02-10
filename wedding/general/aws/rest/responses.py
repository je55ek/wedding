from typing import Dict, Any, Optional
from abc import abstractmethod, ABC

from wedding.general.functional import option


class HttpResponse(ABC):
    def __init__(self, body: Optional[str] = None) -> None:
        self.__body = option.cata(
            '{{ "message": "{}" }}'.format,
            lambda: ''
        )(body)

    @property
    @abstractmethod
    def status_code(self) -> int:
        pass

    @property
    def body(self) -> Optional[str]:
        return self.__body

    def as_json(self) -> Dict[str, Any]:
        return {
            'statusCode': self.status_code,
            'body': self.body,
            'isBase64Encoded': False
        }


class Created(HttpResponse):
    @property
    def status_code(self):
        return 201


class NoContent(HttpResponse):
    @property
    def status_code(self):
        return 204


class MethodNotAllowed(HttpResponse):
    @property
    def status_code(self):
        return 405


class NotFound(HttpResponse):
    @property
    def status_code(self):
        return 404


class BadRequest(HttpResponse):
    @property
    def status_code(self):
        return 405


class InternalServerError(HttpResponse):
    @property
    def status_code(self):
        return 500

    def __init__(self, message):
        super().__init__(message)
