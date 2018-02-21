import json
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union, Optional, Iterable

from marshmallow.exceptions import MarshmallowError
from toolz.functoolz import excepts, partial, compose
from toolz.dicttoolz import merge
from toolz.itertoolz import isiterable

from wedding.general.aws.rest.responses import HttpResponse, MethodNotAllowed, NotFound, BadRequest, InternalServerError
from wedding.general.model import JsonCodec, Json
from wedding.general.functional import option


_A = TypeVar('_A')


class LambdaHandler(ABC):
    METHOD_FIELD = 'httpMethod'
    QUERY_FIELD = 'queryStringParameters'
    PATH_FIELD = 'pathParameters'

    @abstractmethod
    def _handle(self, event):
        pass

    def __call__(self, event, context):
        return self._handle(event)


class RestResource(Generic[_A], LambdaHandler):
    def __init__(self, codec: JsonCodec[_A]) -> None:
        self.__codec = codec

    def __payload(self, event):
        body = json.loads(event['body'])
        return option.cata(
            partial(compose(list, map), self.__codec.decode),
            lambda: self.__codec.decode(body)
        )(body.get('items'))

    def __route(self, event):
        method   = event[self.METHOD_FIELD].upper()
        query    = event.get(self.QUERY_FIELD) or {}
        path     = event.get(self.PATH_FIELD ) or {}
        maybe_id = path.get('id')

        if method == 'GET':
            return option.cata(
                self._get,
                lambda: self._get_many(query)
            )(maybe_id)
        elif method == 'POST':
            body = self.__payload(event)
            return (
                self._post_many(body) if isinstance(body, list) else
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

    @staticmethod
    def __internal_error(error: Exception) -> HttpResponse:
        return InternalServerError(str(error))

    @staticmethod
    def __handler(exc, handler):
        return lambda f: excepts(exc, f, handler)

    @staticmethod
    def __multiple_items(result) -> bool:
        return isiterable(result) and not isinstance(result, dict) and not RestResource.__isnamedtuple(result)

    @staticmethod
    def __isnamedtuple(x):
        x_type = type(x)
        bases = x_type.__bases__

        if len(bases) != 1 or bases[0] != tuple:
            return False

        fields = getattr(x_type, '_fields', None)
        return isinstance(fields, tuple) and all(type(n) == str for n in fields)

    def _handle(self, event):
        safe_route = compose(
            self.__handler(Exception       , self.__internal_error),
            self.__handler(MarshmallowError, self.__json_error    )
        )(self.__route)

        result = safe_route(event)

        response = (
            result.as_json() if isinstance(result, HttpResponse) else
            {
                'statusCode': 200,
                'body': json.dumps(
                    { 'items': [self.__codec.encode(item) for item in result] } if self.__multiple_items(result) else
                    self.__codec.encode(result)
                )
            }
        )

        return merge(response, {'isBase64Encoded': False, 'headers': {'Access-Control-Allow-Origin': "*"}})

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
