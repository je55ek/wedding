import os.path

import pystache

from wedding.general.aws.rest import LambdaHandler
from wedding.general.aws.rest.responses import TemporaryRedirect, HttpResponse, Ok
from wedding.general.functional import option
from wedding.model import PartyStore, EmailOpened, Party, CardClicked
from wedding import TemplateResolver


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