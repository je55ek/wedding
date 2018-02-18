from logging import Logger
from urllib.parse import parse_qs
from typing import Any, Dict, Optional

import pystache
from botocore.exceptions import ClientError
from marshmallow import fields
from toolz.dicttoolz import assoc, valmap, dissoc, valfilter
from toolz.functoolz import partial
from toolz.itertoolz import first

from wedding import TemplateResolver
from wedding.general.aws.rest import LambdaHandler
from wedding.general.aws.rest.responses import TemporaryRedirect, HttpResponse, Ok, InternalServerError
from wedding.general.functional import option
from wedding.general.model import optional, required, build, JsonCodec, codec
from wedding.model import PartyStore, Party, RsvpSubmitted, get_guest, Guest


def _parse_bool(s: str) -> bool:
    return s.lower() == 'true'


class _RsvpFormData:
    PARTY_ID_FIELD = 'partyId'
    GUEST_ID_FIELD = 'guestId'

    def __init__(self,
                 guest_id: str,
                 party_id: str,
                 attending: Dict[str, bool]) -> None:
        self.__guest_id = guest_id
        self.__party_id = party_id
        self.__attending = attending

    def __str__(self):
        return (
            f'RSVP Form Data: ' +
            f'{_RsvpFormData.PARTY_ID_FIELD}={self.party_id} ' +
            f'{_RsvpFormData.GUEST_ID_FIELD}={self.guest_id} ' +
            f'attending={self.attending}'
        )

    def __repr__(self):
        return self.__str__()

    @property
    def guest_id(self) -> str:
        return self.__guest_id

    @property
    def party_id(self) -> str:
        return self.__party_id

    @property
    def attending(self) -> Dict[str, bool]:
        return self.__attending

    @staticmethod
    def parse(raw_form: str):
        form_data = valmap(
            first,
            parse_qs(
                raw_form,
                strict_parsing=True
            )
        )
        return _RsvpFormData(
            guest_id  = form_data[_RsvpFormData.GUEST_ID_FIELD],
            party_id  = form_data[_RsvpFormData.PARTY_ID_FIELD],
            attending = valmap(
                _parse_bool,
                dissoc(
                    form_data,
                    _RsvpFormData.GUEST_ID_FIELD,
                    _RsvpFormData.PARTY_ID_FIELD
                )
            )
        )


RideShareQuery, RideShareQuerySchema = build('RideShareQuery', {
    'local'    : required(fields.Bool           ),
    'guest_id' : required(fields.Str , 'guestId'),
    'party_id' : required(fields.Str , 'partyId'),
    'rideshare': optional(fields.Bool           )
})
RideShareQueryCodec: JsonCodec[RideShareQuery] = codec(RideShareQuerySchema(strict=True))


class RsvpHandler(LambdaHandler):
    def __init__(self,
                 rsvp_template: TemplateResolver,
                 rsvp_summary_template: TemplateResolver,
                 rideshare_url_template: str,
                 not_found_url: str,
                 parties: PartyStore,
                 logger: Logger) -> None:
        """Create a new instance of the :obj:`RsvpHandler` class.

        Args:
            rsvp_template: A callable that returns the HTML template for the RSVP page.
            rsvp_summary_template: A callable that returns the HTML template for the RSVP summary page.
            rideshare_url_template: A pystache template for the URL of the ridesharing form. Must contain variables
                `local`, a boolean, `guestId`, a string, `partyId`, a string, and `rideshare` a boolean.
            not_found_url: URL of the page to redirect to if a party is not found in the database.
            parties: Store for :obj:`Party` instances.
            logger: Interface for emitting log messages.
        """
        self.__parties               : PartyStore        = parties
        self.__not_found             : TemporaryRedirect = TemporaryRedirect(not_found_url)
        self.__rsvp_template         : TemplateResolver  = rsvp_template
        self.__rideshare_url_template: str               = rideshare_url_template
        self.__summary_template      : TemplateResolver  = rsvp_summary_template
        self.__logger                : Logger            = logger

    @staticmethod
    def __render(template: str,
                 context: Dict[str, Any]) -> HttpResponse:
        return Ok(
            pystache.render(
                template,
                context
            )
        )

    @staticmethod
    def __rsvp_context(party: Party,
                       guest_id: str) -> Dict[str, Any]:
        return {
            'partyId': party.id,
            'guestId': guest_id,
            'guests' : [
                {
                    'id'       : guest.id,
                    'firstName': guest.first_name,
                    'lastName' : guest.last_name,
                    'attending': guest.attending or True
                }
                for guest in party.guests
            ]
        }

    def __summary_context(self,
                          party: Party,
                          guest_id: str) -> Dict[str, Any]:
        def log_error():
            self.__logger.error(f'Guest {guest_id} not found in party {party.id}')
            return False

        return assoc(
            self.__rsvp_context(party, guest_id),
            'rideshare',
            option.cata(
                lambda guest: guest.rideshare,
                log_error
            )(get_guest(guest_id)(party))
        )

    def __get(self, event):
        party_id: str = event['partyId']
        guest_id: str = event['guestId']

        maybe_get_context, get_template = option.fmap(
            lambda party:
            (partial(self.__summary_context, party), self.__summary_template) if party.rsvp_stage == RsvpSubmitted else
            (partial(self.__rsvp_context   , party), self.__rsvp_template   )
        )(self.__parties.get(party_id))

        return option.cata(
            lambda get_context: self.__render(
                get_template(),
                get_context(guest_id)
            ),
            lambda: self.__not_found
        )(maybe_get_context)

    def __post(self, event):
        raw_form: str = event['query']
        form = _RsvpFormData.parse(raw_form)

        try:
            party = self.__parties.modify(
                form.party_id,
                lambda party: party._replace(
                    rsvp_stage = RsvpSubmitted,
                    guests = [
                        guest._replace(attending = form.attending[guest.id])
                        for guest in party.guests if guest.id in form.attending
                    ]
                )
            )
        except ClientError as exc:
            self.__logger.error(
                f'RSVP submitted for party "{form.party_id}", but database operation failed with error "{exc}. ' +
                f'Raw form data = {raw_form}, parsed form data = {form}'
            )
            return InternalServerError('Something has gone horribly wrong...please call Jesse and let him know!')

        maybe_guest = option.fmap(get_guest(form.guest_id))(party)

        def redirect(guest: Guest):
            rideshare_query = RideShareQuery(
                local     = party.local  ,
                guest_id  = form.guest_id,
                party_id  = form.party_id,
                rideshare = guest.rideshare or False
            )
            return TemporaryRedirect(
                pystache.render(
                    self.__rideshare_url_template,
                    RideShareQueryCodec.encode(rideshare_query)
                )
            )

        return option.cata(
            redirect,
            lambda: self.__not_found
        )(maybe_guest)

    def _handle(self, event):
        method = event[self.METHOD_FIELD].upper()
        return (
            self.__get (event) if method == 'GET'  else
            self.__post(event) if method == 'POST' else
            self.__not_found
        ).as_json()


class RideShareHandler(LambdaHandler):
    def __init__(self,
                 local_template: TemplateResolver,
                 out_of_town_template: TemplateResolver,
                 not_found_url: str,
                 thank_you_url: str,
                 parties: PartyStore,
                 logger: Logger) -> None:
        """Create a new instance of the :obj:`InvitationHandler` class.

        Args:
            local_template: A callable that returns the HTML template for the ride-share page for in-town guests.
            out_of_town_template: A callable that returns the HTML template for the ride-share page for out-of-town
                guests.
            not_found_url: URL of the page to redirect to if a party is not found in the database.
            thank_you_url: Mustache template of URL to redirect users to after ride-share form submission.
                Template must accept a variable `firstName` of type string.
            parties: Store for :obj:`Party` instances.
            logger: Interface for emitting log messages.
        """
        self.__local_template       = local_template
        self.__out_of_town_template = out_of_town_template
        self.__not_found            = TemporaryRedirect(not_found_url)
        self.__thank_you_url        = thank_you_url
        self.__parties: PartyStore  = parties
        self.__logger               = logger

    def __get(self, query: RideShareQuery) -> HttpResponse:
        return Ok(
            pystache.render(
                self.__local_template() if query.local else self.__out_of_town_template(),
                {
                    'guestId'  : query.guest_id,
                    'rideshare': query.rideshare
                }
            )
        )

    def __post(self, query: RideShareQuery) -> HttpResponse:
        try:
            party = self.__parties.modify(
                query.party_id,
                lambda party: party._replace(
                    guests = [
                        guest._replace(rideshare = query.rideshare)
                        for guest in party.guests if guest.id == query.guest_id
                    ]
                )
            )
        except ClientError as exc:
            self.__logger.error(
                f'Ride share preference submitted for guest "{query.guest_id}" in party "{query.party_id}", ' +
                f'but database operation failed with error "{exc}. Query data = {query}'
            )
            return InternalServerError('Something has gone horribly wrong...please call Jesse and let him know!')

        maybe_guest = option.fmap(get_guest(query.guest_id))(party)

        return option.cata(
            lambda guest: TemporaryRedirect(
                pystache.render(
                    self.__thank_you_url,
                    { 'firstName': guest.first_name }
                )
            ),
            lambda: self.__not_found
        )(maybe_guest)

    def _handle(self, event):
        method = event[self.METHOD_FIELD].upper()
        query  = RideShareQueryCodec.decode(event['query'])
        return (
            self.__get (query) if method == 'GET'  else
            self.__post(query) if method == 'POST' else
            self.__not_found
        ).as_json()


class ThankYouHandler(LambdaHandler):
    def __init__(self, thank_you_template: TemplateResolver) -> None:
        self.__get_template = thank_you_template

    def _handle(self, event):
        first_name: Optional[str] = event.get('firstName')
        return Ok(
            pystache.render(
                self.__get_template(),
                valfilter(option.not_none, { 'firstName': first_name })
            )
        ).as_json()
