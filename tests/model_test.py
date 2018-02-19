from tests.data_generators import guest, create_party
from wedding.model import *


john  = guest('John' , 'john' , 'id1')
jane  = guest('Jane' , 'jane' , 'id2')
jerry = guest('Jerry', 'jerry', 'id3')
party = create_party(
    'does',
    john,
    jane
)


def test_party_roundtrip():
    schema = PartySchema(many=False)
    assert schema.loads(schema.dumps(party).data).data == party


def test_optional_email():
    no_email = guest('John', None)
    schema = GuestSchema(many=False, strict=True)
    assert schema.loads(schema.dumps(no_email).data).data == no_email


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


def test_get_guest():
    assert get_guest(john.id)(party) == john


def test_remove_guest():
    assert jane in party.guests
    assert john in party.guests

    without_john = remove_guest(john.id)(party)

    assert jane     in without_john.guests
    assert john not in without_john.guests


def test_set_new_guest():
    assert john      in party.guests
    assert jane      in party.guests
    assert jerry not in party.guests

    with_jerry = set_guest(jerry)(party)

    assert jerry in with_jerry.guests
    assert john  in with_jerry.guests
    assert jane  in with_jerry.guests


def test_modify_guest():
    modified_party = modify_guest(
        john.id,
        lambda guest: guest._replace(first_name = 'Joe')
    )(party)

    expected_john = guest('Joe', 'john', john.id)
    assert expected_john in modified_party.guests
