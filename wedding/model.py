from collections import namedtuple
from typing import Mapping, Tuple, Type, NamedTuple

from marshmallow import Schema
from marshmallow.decorators import post_load
from marshmallow.fields import Field, Nested, String, Boolean
from toolz.dicttoolz import valfilter


def _required(cls, name = None, **kwargs):
    return cls(
        **valfilter(
            lambda x: x is not None,
            {**kwargs, 'load_from': name, 'dump_to': name}
        )
    )


def _build(name: str,
           fields: Mapping[str, Field]) -> Tuple[type, Type[Schema]]:
    cls = namedtuple(name, fields.keys())

    @post_load
    def to_namedtuple(self, data):
        return cls(**data)

    schema = type(
        '{}Schema'.format(name),
        (Schema,),
        {**fields, '_to_namedtuple': to_namedtuple}
    )

    return cls, schema


Email, EmailSchema = _build('Email', {
    'username': _required(String),
    'hostname': _required(String)
})


Guest, GuestSchema = _build('Guest', {
    'id'         : _required(String             ),
    'first_name' : _required(String, 'firstName'),
    'last_name'  : _required(String, 'lastName' ),
    'email'      : Nested   (EmailSchema        ),
    'invited'    : _required(Boolean            ),
    'attending'  : _required(Boolean            )
})


Party, PartySchema = _build('Party', {
    'id'     : _required(String),
    'title'  : _required(String),
    'guests' : Nested(GuestSchema, many = True, required = True)
})
