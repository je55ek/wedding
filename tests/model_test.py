from tests.data_generators import guest, create_party
from wedding.model import *


def test_party_roundtrip():
    party = create_party(
        guest('John', 'john'),
        guest('Jane', 'jane')
    )

    schema = PartySchema(many=False)
    assert schema.loads(schema.dumps(party).data).data == party


def test_optional_email():
    john = guest('John', None)
    schema = GuestSchema(many=False, strict=True)
    assert schema.loads(schema.dumps(john).data).data == john
