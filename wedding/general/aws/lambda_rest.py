import json
from abc import abstractmethod
from typing import Generic, TypeVar, Union, Optional, Iterable

from marshmallow.exceptions import MarshmallowError
from toolz.functoolz import excepts, partial
from toolz.itertoolz import isiterable
from toolz.dicttoolz import merge

from wedding.general.model import JsonCodec, Json
from wedding.general.functional import option


_A = TypeVar('_A')


class HttpResponse:
    @abstractmethod
    def as_json(self):
        pass


class Created(HttpResponse):
    def as_json(self):
        return { 'statusCode': 201 }


class NoContent(HttpResponse):
    def as_json(self):
        return { 'statusCode': 204 }


class MethodNotAllowed(HttpResponse):
    def as_json(self):
        return { 'statusCode': 405 }


class NotFound(HttpResponse):
    def as_json(self):
        return { 'statusCode': 404 }


class BadRequest(HttpResponse):
    def __init__(self, message):
        self.__message = message

    def as_json(self):
        return { 'statusCode': 405, 'body': self.__message }


class RestResource(Generic[_A]):
    METHOD_FIELD = 'httpMethod'
    QUERY_FIELD = 'queryStringParameters'
    PATH_FIELD = 'pathParameters'

    def __init__(self, codec: JsonCodec[_A]) -> None:
        self.__codec = codec

    def __payload(self, event):
        body = event['body']
        return option.cata(
            partial(map, self.__codec.decode),
            lambda: self.__codec.decode(body)
        )(body.get('items'))

    def __route(self, event):
        method   = event[RestResource.METHOD_FIELD]
        query    = event.get(RestResource.QUERY_FIELD) or {}
        path     = event.get(RestResource.PATH_FIELD ) or {}
        maybe_id = path.get('id')

        if method == 'GET':
            return option.cata(
                self._get,
                lambda: self._get_many(query)
            )(maybe_id)
        elif method == 'POST':
            body = self.__payload(event)
            return (
                self._post_many(body) if isiterable(body) else
                self._post(body)
            )
        elif method == 'DELETE':
            return option.cata(
                self._delete,
                lambda: self._delete_many(query)
            )(maybe_id)
        else:
            return MethodNotAllowed()

    @staticmethod
    def __json_error(error: MarshmallowError) -> HttpResponse:
        return BadRequest(str(error))

    def __handle(self, event):
        result = excepts(
            MarshmallowError,
            self.__route,
            RestResource.__json_error
        )(event)

        response = (
            result.as_json() if isinstance(result, HttpResponse) else
            {
                'statusCode': 200,
                'body': json.dumps(
                    { 'items': [self.__codec.encode(item) for item in result] } if isinstance(result, (map, list)) else
                    self.__codec.encode(result)
                )
            }
        )

        return merge(response, {'isBase64Encoded': False, 'headers': {}})

    def create_handler(self):
        return lambda event, _: self.__handle(event)

    def _get(self, key: str) -> Union[Optional[_A], HttpResponse]:
        return NotFound()

    def _get_many(self, query: Json) -> Union[Iterable[_A], HttpResponse]:
        return NotFound()

    def _post(self, a: _A) -> HttpResponse:
        return MethodNotAllowed()

    def _post_many(self, a: Iterable[_A]) -> HttpResponse:
        return MethodNotAllowed()

    def _delete(self, key: str) -> HttpResponse:
        return MethodNotAllowed()

    def _delete_many(self, query: Json) -> HttpResponse:
        return MethodNotAllowed()
