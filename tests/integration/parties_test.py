import json

import boto3

from wedding.rest.parties import parties_resource
from wedding.model import party_store, PartyCodec
from tests.data_generators import guest, create_party


def test_it():
    store = party_store(boto3.resource('dynamodb').Table('Parties'))
    parties = parties_resource(store)

    party = create_party(
        guest('Pepino'),
        guest('Jesse' )
    )
    store.put(party)

    handler = parties.create_handler()

    response = handler(
        { 'httpMethod': 'GET' },
        None
    )

    assert len(response) == 1
    assert PartyCodec.decode(response[0]) == party, json.dumps(response[0], indent=2)
