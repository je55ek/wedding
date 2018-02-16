import os.path

from wedding.model import PartyStore, EmailOpened


class EnvelopeImageHandler:
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

    def __handle(self, event):
        party_id = os.path.splitext(event['partyId'])[0]
        self.__parties.modify(
            party_id,
            lambda party: party._replace(rsvp_stage = EmailOpened)
        )
        return {
            'location': self.__prefix + f'{party_id}.png'
        }

    def create_handler(self):
        return lambda event, _: self.__handle(event)
