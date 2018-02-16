from abc import ABC, abstractmethod

from marshmallow import ValidationError
from marshmallow.fields import Field

from wedding.general.functional.error_handling import throw


class RsvpStage(ABC):
    def __str__(self):
        return f'RsvpStage({self.shows})'

    def __repr__(self):
        return self.__str__()

    @property
    @abstractmethod
    def shows(self) -> str:
        pass

    @property
    @abstractmethod
    def next_stage(self):
        pass

    @staticmethod
    def instance(name: str, shows: str, next_stage):
        return type(
            f'_{name}',
            (RsvpStage,),
            {
                'shows'     : property(lambda _: shows),
                'next_stage': property(lambda _: next_stage)
            }
        )()


RsvpSubmitted = RsvpStage.instance('RsvpSubmitted', 'rsvp_submitted', None         )
CardClicked   = RsvpStage.instance('CardClicked'  , 'card_clicked'  , RsvpSubmitted)
EmailOpened   = RsvpStage.instance('EmailOpened'  , 'email_opened'  , CardClicked  )
EmailSent     = RsvpStage.instance('EmailSent'    , 'email_sent'    , EmailOpened  )
NotInvited    = RsvpStage.instance('NotInvited'   , 'not_invited'   , EmailSent    )


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