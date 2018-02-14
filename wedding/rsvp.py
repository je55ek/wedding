from wedding.model import PartyStore


class EnvelopeImageHandler:
    def __init__(self,
                 envelope_bucket,
                 parties: PartyStore):
        self.__bucket  = envelope_bucket
        self.__parties = parties

    def __handle(self, event):
        party_id = event['partyId'][0:-4]
        self.__parties.modify(
            party_id,
            lambda party: party._replace(
                guests = [
                    guest._replace(invited = True)
                    for guest in party.guests
                ]
            )
        )
        return {
            'location': self.__bucket + f'{party_id}.png'
        }

    def create_handler(self):
        return lambda event, _: self.__handle(event)
