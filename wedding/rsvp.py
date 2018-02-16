import os.path

from wedding.model import PartyStore, EmailOpened


class EnvelopeImageHandler:
    def __init__(self,
                 envelope_bucket,
                 parties: PartyStore) -> None:
        self.__bucket  = envelope_bucket
        self.__parties = parties

    def __handle(self, event):
        party_id = os.path.splitext(event['partyId'])[0]
        self.__parties.modify(
            party_id,
            lambda party: party._replace(rsvp_stage = EmailOpened)
        )
        return {
            'location': self.__bucket + f'{party_id}.png'
        }

    def create_handler(self):
        return lambda event, _: self.__handle(event)
