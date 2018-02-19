from abc import ABC, abstractmethod
from typing import Optional, Callable

from marshmallow import ValidationError
from marshmallow.fields import String, Boolean, Integer, DateTime, Field
from marshmallow.validate import Range
from toolz.functoolz import excepts, curry, compose
from toolz.itertoolz import first

from wedding.general.aws.dynamodb import DynamoDbStore
from wedding.general.functional.error_handling import throw
from wedding.general.functional import option
from wedding.general.model import JsonCodec, codec, required, optional, build, JsonEncoder
from wedding.general.store import Store


class RsvpStage(ABC):
    def __str__(self):
        return f'RsvpStage({self.shows})'

    def __repr__(self):
        return self.__str__()

    @property
    @abstractmethod
    def shows(self) -> str:
        pass

    @staticmethod
    def instance(name: str, shows: str):
        return type(
            f'_{name}',
            (RsvpStage,),
            { 'shows': property(lambda _: shows) }
        )()


class RsvpStageField(Field):
    def _serialize(self, value, attr, obj):
        if not isinstance(value, RsvpStage):
            raise ValidationError(f'{attr} of {obj} is of type {type(value)}, expected an RsvpStage instance')
        return value.shows

    def _deserialize(self, value, attr, data):
        value = value.lower()
        return (
            RsvpSubmitted if value == RsvpSubmitted.shows.lower() else
            CardClicked   if value == CardClicked  .shows.lower() else
            EmailOpened   if value == EmailOpened  .shows.lower() else
            EmailSent     if value == EmailSent    .shows.lower() else
            NotInvited    if value == NotInvited   .shows.lower() else
            throw(ValidationError(f'"{value}" is not a recognized RSVP stage'))
        )


RsvpSubmitted = RsvpStage.instance('RsvpSubmitted', 'rsvp_submitted')
CardClicked   = RsvpStage.instance('CardClicked'  , 'card_clicked'  )
EmailOpened   = RsvpStage.instance('EmailOpened'  , 'email_opened'  )
EmailSent     = RsvpStage.instance('EmailSent'    , 'email_sent'    )
NotInvited    = RsvpStage.instance('NotInvited'   , 'not_invited'   )


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
    'attending'  : optional(Boolean),
    'rideshare'  : optional(Boolean)
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


@curry
def get_guest(guest_id: str,
              party: Party) -> Optional[Guest]:
    return excepts(StopIteration, first)(
        guest for guest in party.guests
        if guest.id == guest_id
    )


@curry
def remove_guest(guest_id: str,
                 party: Party) -> Party:
    """Create a function that removes a guest from a party.

    Args:
        guest_id: The ID of the guest to remove from the party.
            If the party does not contain a guest whose ID is `guest_id`, then the party is unmodified.
        party: The party to remove `guest` from.

    Returns:
        A new :obj:`Party` instance, equivalent to `party` except with the specified guest removed.
    """
    return party._replace(guests = [g for g in party.guests if g.id != guest_id])


@curry
def set_guest(guest: Guest,
              party: Party) -> Party:
    """Create a function that sets or replaces a guest in a party.

    Args:
        guest: The guest to add to the party, or to replace an existing guest with. If the party already contains a
            guest whose ID is equal to `guest.id`, then that guest is replaced with `guest`. Otherwise, `guest` is added
            to the party.
        party: The party to add `guest` to.

    Returns:
        A new :obj:`Party` instance, equivalent to `party` except with the specified guest added or updated.
    """
    without_guest = remove_guest(guest.id)(party)
    return without_guest._replace(
        guests = without_guest.guests + [guest]
    )


def modify_guest(guest_id: str,
                 modify: Callable[[Guest], Guest]) -> Callable[[Party], Party]:
    def _modify_guest(party: Party) -> Optional[Guest]:
        maybe_guest = get_guest(guest_id)(party)
        new_guest   = option.fmap(modify)(maybe_guest)
        return compose(
            set_guest   (new_guest),
            remove_guest(guest_id )
        )(party)

    return _modify_guest
