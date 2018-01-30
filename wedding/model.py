from collections import namedtuple
from typing import *

from marshmallow import Schema
from marshmallow.decorators import post_load
from marshmallow.fields import Field, Nested, String, Boolean
from toolz.dicttoolz import valfilter, merge
from toolz.itertoolz import partial

from wedding.functional.option import not_none


V = TypeVar('V')


class JsonEncoder(Generic[V], Callable[[V], Dict[str, Any]]):
    def __init__(self, encode: Callable[[V], Dict[str, Any]]):
        self.__encode = encode

    def __call__(self, value: V) -> Dict[str, Any]:
        return self.__encode(value)


class JsonDecoder(Generic[V], Callable[[Dict[str, Any]], V]):
    def __init__(self, decode: Callable[[Dict[str, Any]], V]):
        self.__decode = decode

    def __call__(self, value: Dict[str, Any]) -> V:
        return self.__decode(value)


class JsonCodec(Generic[V]):
    def __init__(self,
                 encode: JsonEncoder[V],
                 decode: JsonDecoder[V]) -> None:
        self.__encode = encode
        self.__decode = decode

    def encode(self, value: V) -> Dict[str, Any]:
        return self.__encode(value)

    def decode(self, value: Dict[str, Any]) -> V:
        return self.__decode(value)


def codec(schema: Schema) -> JsonCodec[V]:
    return JsonCodec[V](
        lambda v: schema.dump(v).data,
        lambda j: schema.load(j).data
    )


def _required(cls: Union[Type[Schema], Type[Field]],
              name: Optional[str] = None,
              **kwargs) -> Field:
    if issubclass(cls, Schema):
        cls = partial(Nested, cls)
    return cls(
        **merge(
            kwargs,
            valfilter(
                not_none,
                {
                    'load_from': name,
                    'dump_to': name
                }
            )
        )
    )


def _optional(cls: Union[Type[Schema], Type[Field]],
              name: Optional[str] = None,
              **kwargs) -> Field:
    return _required(
        cls,
        name,
        **merge(
            kwargs,
            {
                'missing': None,
                'default': None,
                'required': False
            }
        )
    )


def _build(name: str,
           fields: Mapping[str, Field]):
    cls = namedtuple(name, fields.keys())

    @post_load
    def to_namedtuple(_, data):
        return cls(**data)

    schema: Type[Schema] = type(
        '{}Schema'.format(name),
        (Schema,),
        {**fields, '_to_namedtuple': to_namedtuple}
    )

    return cls, schema


Email, EmailSchema = _build('Email', {
    'username': _required(String),
    'hostname': _required(String)
})
EmailCodec: JsonCodec[Email] = codec(EmailSchema(strict=True))


Guest, GuestSchema = _build('Guest', {
    'id'         : _required(String             ),
    'first_name' : _required(String, 'firstName'),
    'last_name'  : _required(String, 'lastName' ),
    'email'      : _optional(EmailSchema        ),
    'invited'    : _required(Boolean            ),
    'attending'  : _required(Boolean            )
})
GuestCodec: JsonCodec[Guest] = codec(GuestSchema(strict=True))


Party, PartySchema = _build('Party', {
    'id'     : _required(String),
    'title'  : _required(String),
    'guests' : _required(GuestSchema, many=True)
})
PartyCodec: JsonCodec[Party] = codec(PartySchema(strict=True))
