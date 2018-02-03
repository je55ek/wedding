from abc import abstractmethod
from typing import Generic, TypeVar

from marshmallow.exceptions import MarshmallowError
from toolz.functoolz import excepts

from wedding.general.model import JsonCodec


_A = TypeVar('_A')


class HttpResponse:
    @abstractmethod
    def as_json(self):
        pass


class MethodNotAllowed(HttpResponse):
    def as_json(self):
        return { 'status': 405 }


class NotFound(HttpResponse):
    def as_json(self):
        return { 'status': 404 }


class BadRequest(HttpResponse):
    def __init__(self, message):
        self.__message = message

    def as_json(self):
        return { 'status': 405, 'body': self.__message }


class RestResource(Generic[_A]):
    def __init__(self, codec: JsonCodec[_A]) -> None:
        self.__codec = codec

    def __route(self, event):
        method = event['httpMethod']
        query  = event.get('queryStringParameters', {})
        path   = event.get('pathParameters', {})

        def payload():
            return self.__codec.decode(event['body'])

        return (
            self._get   (           path, query) if method == 'GET'    else
            self._put   (payload(), path, query) if method == 'PUT'    else
            self._post  (payload(), path, query) if method == 'POST'   else
            self._delete(           path, query) if method == 'DELETE' else
            MethodNotAllowed
        )

    @staticmethod
    def __json_error(error: MarshmallowError) -> HttpResponse:
        return BadRequest(str(error))

    def __handle(self, event):
        response = excepts(
            MarshmallowError,
            self.__route,
            RestResource.__json_error
        )(event)

        return (
            response.as_json() if isinstance(response, HttpResponse) else
            self.__codec.encode(response)
        )

    def create_handler(self):
        return lambda event, _: self.__handle(event)

    def _get(self, path, query):
        return NotFound

    def _put(self, a: _A, path, query):
        return MethodNotAllowed

    def _post(self, a: _A, path, query):
        return MethodNotAllowed

    def _delete(self, path, query):
        return MethodNotAllowed
