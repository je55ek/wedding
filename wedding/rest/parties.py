from wedding.general.resource import StoreBackedResource
from wedding.general.model import codec
from wedding.model import Party, PartyStore, PartySchema


def parties_resource(store: PartyStore):
    return StoreBackedResource[Party](
        store,
        codec(PartySchema(strict=True))
    )
