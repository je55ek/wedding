from marshmallow.fields import String, Boolean

from wedding.general.model import JsonCodec, codec, required, optional, build, JsonEncoder
from wedding.general.store import Store
from wedding.general.aws.dynamodb import DynamoDbStore


Email, EmailSchema = build('Email', {
    'username': required(String),
    'hostname': required(String)
})
EmailCodec: JsonCodec[Email] = codec(EmailSchema(strict=True))


Guest, GuestSchema = build('Guest', {
    'id'         : required(String),
    'first_name' : required(String, 'firstName'),
    'last_name'  : required(String, 'lastName'),
    'email'      : optional(EmailSchema),
    'invited'    : required(Boolean),
    'attending'  : required(Boolean)
})
GuestCodec: JsonCodec[Guest] = codec(GuestSchema(strict=True))


Party, PartySchema = build('Party', {
    'id'     : required(String),
    'title'  : required(String),
    'guests' : required(GuestSchema, many=True)
})
PartyCodec: JsonCodec[Party] = codec(PartySchema(strict=True))


PartyStore = Store[str, Party]


def party_store(dynamo_table) -> PartyStore:
    return DynamoDbStore[str, Party](
        dynamo_table,
        JsonEncoder[str](lambda i: {'id': i}),
        PartyCodec
    )
