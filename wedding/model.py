from marshmallow.fields import String, Boolean, Integer, DateTime
from marshmallow.validate import Range
from toolz.functoolz import excepts

from wedding.general.aws.dynamodb import DynamoDbStore
from wedding.general.model import JsonCodec, codec, required, optional, build, JsonEncoder
from wedding.general.store import Store
from wedding.rsvp_stage import RsvpStageField, NotInvited

EmailAddress, EmailAddressSchema = build('EmailAddress', {
    'username': required(String),
    'hostname': required(String)
})
EmailAddressCodec: JsonCodec[EmailAddress] = codec(EmailAddressSchema(strict=True))


Guest, GuestSchema = build('Guest', {
    'id'         : required(String),
    'first_name' : required(String, 'firstName'),
    'last_name'  : required(String, 'lastName'),
    'email'      : optional(EmailAddressSchema),
    'attending'  : optional(Boolean)
})
GuestCodec: JsonCodec[Guest] = codec(GuestSchema(strict=True))

Party, PartySchema = build('Party', {
    'id'        : required(String),
    'title'     : required(String),
    'local'     : required(Boolean),
    'guests'    : required(GuestSchema, many=True),
    'inviter'   : required(EmailAddressSchema),
    'rsvp_stage': optional(RsvpStageField, 'rsvpStage', missing = NotInvited.shows)
})
PartyCodec: JsonCodec[Party] = codec(PartySchema(strict=True))


Passenger, PassengerSchema = build('Passenger', {
    'first_name': required(String, 'firstName'),
    'guest_id'  : required(String, 'guestId'  )
})
PassengerCodec: JsonCodec[Passenger] = codec(PassengerSchema(strict=True))


Phone, PhoneSchema = build('Phone', {
    'area'    : required(Integer, validate = Range(200, 999)),
    'exchange': required(Integer, validate = Range(200, 999)),
    'line'    : required(String , validate = lambda s: 0 <= excepts(ValueError, int, -1)(s) <= 9999)
})
PhoneCodec: JsonCodec[Phone] = codec(PhoneSchema(strict=True))


Contact, ContactSchema = build('Contact', {
    'phone': required(PhoneSchema),
    'email': required(EmailAddressSchema)
})
ContactCodec: JsonCodec[Contact] = codec(ContactSchema(strict=True))


PassengerGroup, PassengerGroupSchema = build('PassengerGroup', {
    'id'          : required(String                    ),
    'passengers'  : required(PassengerSchema, many=True),
    'arrival'     : required(DateTime                  ),
    'contact_name': required(String, 'contactName'     ),
    'contact'     : required(ContactSchema,   many=True)
})
PassengerGroupCodec: JsonCodec[PassengerGroup] = codec(PassengerGroupSchema(strict=True))


Driver, DriverSchema = build('Driver', {
    'id'         : required(String             ),
    'first_name' : required(String, 'firstName'),
    'last_name'  : required(String, 'lastName' ),
    'contact'    : required(ContactSchema      ),
    'capacity'   : required(Integer            ),
    'available'  : required(Boolean            ),
    'passengers' : optional(PassengerGroupSchema, many=True)
})
DriverCodec: JsonCodec[Driver] = codec(DriverSchema(strict=True))


PartyStore = Store[str, Party]
DriverStore = Store[str, Driver]
PassengerGroupStore = Store[str, PassengerGroup]


def party_store(dynamo_table) -> PartyStore:
    return DynamoDbStore[str, Party](
        dynamo_table,
        JsonEncoder[str](lambda i: {'id': i}),
        PartyCodec
    )


def driver_store(dynamo_table) -> DriverStore:
    return DynamoDbStore[str, Driver](
        dynamo_table,
        JsonEncoder[str](lambda i: {'id': i}),
        DriverCodec
    )


def passenger_group_store(dynamo_table) -> PassengerGroupStore:
    return DynamoDbStore[str, PassengerGroup](
        dynamo_table,
        JsonEncoder[str](lambda i: {'id': i}),
        PassengerGroupCodec
    )
