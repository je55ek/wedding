import os.path
from logging import Logger
from typing import Callable, Optional, Any, Dict

import pystache
from toolz.dicttoolz import assoc
from toolz.itertoolz import first
from toolz.functoolz import partial

from wedding.general.aws.rest import LambdaHandler
from wedding.general.aws.rest.responses import TemporaryRedirect, HttpResponse, Ok
from wedding.general.functional import option
from wedding.model import PartyStore, EmailOpened, Party, CardClicked, RsvpSubmitted


TemplateResolver = Callable[[], str]


class EnvelopeImageHandler(LambdaHandler):
    def __init__(self,
                 envelope_url_prefix: str,
                 parties: PartyStore) -> None:
        """Create a new instance of the :obj:`EnvelopeImageHandler` class.

        Args:
            envelope_url_prefix: The URL prefix of all envelope PNG images.
            parties: Store for :obj:`Party` instances.
        """
        self.__prefix  = envelope_url_prefix
        self.__parties = parties

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
        self.__parties = parties
        self.__redirect = TemporaryRedirect(not_found_url)
        self.__get_template = get_template

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
                 not_found_url: str,
                 parties: PartyStore,
                 logger: Logger) -> None:
        """Create a new instance of the :obj:`RsvpHandler` class.

        Args:
            rsvp_template: A callable that returns the HTML template for the RSVP page.
            rsvp_summary_template: A callable that returns the HTML template for the RSVP summary page.
            not_found_url: URL of the page to redirect to if a party is not found in the database.
            parties: Store for :obj:`Party` instances.
        """
        self.__parties = parties
        self.__redirect = TemporaryRedirect(not_found_url)
        self.__rsvp_template = rsvp_template
        self.__summary_template = rsvp_summary_template
        self.__logger = logger

    @staticmethod
    def __render(template: str,
                 context: Dict[str, Any]) -> HttpResponse:
        return Ok(
            pystache.render(
                template,
                context
            )
        )

    def __get_rideshare(self,
                        party: Party,
                        guest_id: str) -> Optional[bool]:
        try:
            return first(guest.rideshare for guest in party.guests if guest.id == guest_id)
        except StopIteration:
            self.__logger.error(f'Guest {guest_id} not found in party {party.id}')
            return False

    def __rsvp_context(self,
                       party: Party,
                       guest_id: str) -> Dict[str, Any]:
        return {
            'partyId': party.id,
            'guestId': guest_id,
            'local'  : party.local,
            'guests' : [
                {
                    'id'        : guest.id,
                    'first_name': guest.first_name,
                    'last_name' : guest.last_name,
                    'attending' : guest.attending
                }
                for guest in party.guests
            ]
        }

    def __summary_context(self,
                          party: Party,
                          guest_id: str) -> Dict[str, Any]:
        return assoc(
            self.__rsvp_context(party, guest_id),
            'rideshare',
            self.__get_rideshare(party, guest_id)
        )

    def _handle(self, event):
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
            lambda: self.__redirect
        )(maybe_get_context).as_json()


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
        local     = event['local'  ]
        guest_id  = event['guestId']
        rideshare = event.get('rideshare')

        return Ok(
            pystache.render(
                self.__local_template() if local else self.__out_of_town_template(),
                {
                    'guestId'  : guest_id,
                    'rideshare': rideshare
                }
            )
        ).as_json()
