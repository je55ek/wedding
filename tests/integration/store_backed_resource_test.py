import json

import boto3

from wedding.model import party_store, PartyCodec, PartySchema, Party
from wedding.general.model import codec
from wedding.general.resource import StoreBackedResource
from tests.data_generators import guest, create_party


store = party_store(boto3.resource('dynamodb').Table('Parties'))
parties_rest = StoreBackedResource[Party](
    store,
    codec(PartySchema(strict=True))
)
parties = [
    create_party('1', guest('Jim'), guest('Jane')),
    create_party('2', guest('Jam'), guest('John'))
]


def test_get_all():
    store.put_all(parties)
    response = sorted(
        json.loads(
            parties_rest(
                { parties_rest.METHOD_FIELD: 'GET' },
                None
            )['body']
        )['items'],
        key = lambda party: party['id']
    )
    for party in parties:
        store.delete(party.id)
    for server, expected in zip(response, parties):
        assert PartyCodec.decode(server) == expected


def test_get_one():
    store.put_all(parties)
    response = parties_rest(
        { parties_rest.METHOD_FIELD: 'GET', parties_rest.PATH_FIELD: { 'id': parties[0].id } },
        None
    )
    for party in parties:
        store.delete(party.id)
    assert PartyCodec.decode(json.loads(response['body'])) == parties[0]
