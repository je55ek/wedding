from typing import List

from wedding.general.resource import StoreBackedResource
from wedding.model import Party, PartyStore, codec, PartySchema


def parties_resource(store: PartyStore):
    return StoreBackedResource[str, List[Party]](
        store,
        codec(PartySchema(strict=True, many=True))
    )
