import os.path
from logging import Logger
from urllib.parse import parse_qs
from typing import Callable, Any, Dict

import pystache
from botocore.exceptions import ClientError
from toolz.dicttoolz import assoc, valmap, dissoc
from toolz.functoolz import partial
from toolz.itertoolz import first

from wedding.general.aws.rest import LambdaHandler
from wedding.general.aws.rest.responses import TemporaryRedirect, HttpResponse, Ok, InternalServerError
from wedding.general.functional import option
from wedding.model import PartyStore, EmailOpened, Party, CardClicked, RsvpSubmitted, get_guest, Guest


TemplateResolver = Callable[[], str]


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


class EnvelopeImageHandler(LambdaHandler):
    def __init__(self,
                 envelope_url_prefix: str,
                 parties: PartyStore) -> None:
        """Create a new instance of the :obj:`EnvelopeImageHandler` class.

        Args:
            envelope_url_prefix: The URL prefix of all envelope PNG images.
            parties: Store for :obj:`Party` instances.
        """
        self.__prefix : str        = envelope_url_prefix
        self.__parties: PartyStore = parties

    def _handle(self, event):
        party_id = os.path.splitext(event['partyId'])[0]
        self.__parties.modify(
            party_id,
            lambda party: party._replace(rsvp_stage = EmailOpened)
        )
        return {
            'location': self.__prefix + ('/' if not self.__prefix.endswith('/') else '') + f'{party_id}.png'
        }


class InvitationHandler(LambdaHandler):
    def __init__(self,
                 get_template: TemplateResolver,
                 not_found_url: str,
                 parties: PartyStore) -> None:
        """Create a new instance of the :obj:`InvitationHandler` class.

        Args:
            get_template: A callable that returns the HTML template for the invitations.
            not_found_url: URL of the page to redirect to if a party is not found in the database.
            parties: Store for :obj:`Party` instances.
        """
        self.__parties     : PartyStore        = parties
        self.__redirect    : TemporaryRedirect = TemporaryRedirect(not_found_url)
        self.__get_template: TemplateResolver  = get_template

    def __render_invitation(self, guest_id: str, party: Party) -> HttpResponse:
        return Ok(
            pystache.render(
                self.__get_template(),
                {
                    'partyId': party.id,
                    'guestId': guest_id
                }
            )
        )

    def _handle(self, event):
        party_id = event['partyId']
        guest_id = event['guestId']

        self.__parties.modify(
            party_id,
            lambda party: party._replace(rsvp_stage = CardClicked)
        )

        return option.cata(
            lambda party: self.__render_invitation(guest_id, party),
            lambda: self.__redirect
        )(self.__parties.get(party_id)).as_json()


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

    def __rsvp_context(self,
                       party: Party,
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
            return TemporaryRedirect(
                pystache.render(
                    self.__rideshare_url_template,
                    {
                        'local': party.local,
                        'guestId': form.guest_id,
                        'partyId': form.party_id,
                        'rideshare': guest.rideshare or False
                    }
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
                 out_of_town_template: TemplateResolver) -> None:
        """Create a new instance of the :obj:`InvitationHandler` class.

        Args:
            local_template: A callable that returns the HTML template for the ride-share page for in-town guests.
            out_of_town_template: A callable that returns the HTML template for the ride-share page for out-of-town
                guests.
        """
        self.__local_template       = local_template
        self.__out_of_town_template = out_of_town_template

    def _handle(self, event):
        local     = _parse_bool(event['local'])
        guest_id  = event['guestId']
        # party_id  = event['partyId']
        rideshare = option.fmap(_parse_bool)(event.get('rideshare'))

        return Ok(
            pystache.render(
                self.__local_template() if local else self.__out_of_town_template(),
                {
                    'guestId'  : guest_id,
                    'rideshare': rideshare
                }
            )
        ).as_json()
