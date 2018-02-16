from tests.data_generators import guest, create_party
from wedding.model import *


def test_party_roundtrip():
    party = create_party(
        'does',
        guest('John', 'john'),
        guest('Jane', 'jane')
    )

    schema = PartySchema(many=False)
    assert schema.loads(schema.dumps(party).data).data == party


def test_optional_email():
    john = guest('John', None)
    schema = GuestSchema(many=False, strict=True)
    assert schema.loads(schema.dumps(john).data).data == john


def test_party_defaults():
    as_json = {
        "id": "flyingjs",
        "title": "The Flying Js",
        "local": True,
        "inviter": {
            "username": "john",
            "hostname": "doe.com"
        },
        "guests": []
    }
    assert PartyCodec.decode(as_json).rsvp_stage == NotInvited
