from collections import namedtuple
from functools import partial
from typing import Generic, Callable, Dict, Any, Union, Type, Optional, Mapping, TypeVar

from marshmallow import Schema, post_load
from marshmallow.fields import Field, Nested
from toolz import merge, valfilter

from wedding.general.functional.option import not_none


V = TypeVar('V')
Json = Union[Dict[str, Any]]


class JsonEncoder(Generic[V], Callable[[V], Json]):
    def __init__(self, encode: Callable[[V], Json]) -> None:
        self.__encode = encode

    def __call__(self, value: V) -> Json:
        return self.__encode(value)


class JsonDecoder(Generic[V], Callable[[Json], V]):
    def __init__(self, decode: Callable[[Json], V]) -> None:
        self.__decode = decode

    def __call__(self, value: Json) -> V:
        return self.__decode(value)


class JsonCodec(Generic[V]):
    def __init__(self,
                 encode: JsonEncoder[V],
                 decode: JsonDecoder[V]) -> None:
        self.__encode = encode
        self.__decode = decode

    def encode(self, value: V) -> Json:
        return self.__encode(value)

    def decode(self, value: Json) -> V:
        return self.__decode(value)


def codec(schema: Schema) -> JsonCodec[V]:
    return JsonCodec[V](
        lambda v: schema.dump(v).data,
        lambda j: schema.load(j).data
    )


def required(cls: Union[Type[Schema], Type[Field]],
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


def optional(cls: Union[Type[Schema], Type[Field]],
             name: Optional[str] = None,
             **kwargs) -> Field:
    return required(
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


def build(name: str,
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