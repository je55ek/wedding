from wedding.rsvp import RsvpFormData, RideShareFormData


expected_party     = 'someparty'
expected_guest     = 'someguest'
expected_rideshare = True


def test_rsvp_form_parse():
    form = RsvpFormData.parse(
        f'{RsvpFormData.PARTY_ID_FIELD}={expected_party}&' +
        f'{RsvpFormData.GUEST_ID_FIELD}={expected_guest}&' +
        'john=true'
    )

    assert form.attending['john']
    assert form.party_id == expected_party
    assert form.guest_id == expected_guest


def test_rideshare_form_parse():
    form = RideShareFormData.parse(
        f'{RideShareFormData.PARTY_ID_FIELD}={expected_party}&' +
        f'{RideShareFormData.GUEST_ID_FIELD}={expected_guest}&' +
        f'{RideShareFormData.RIDESHARE_FIELD}={expected_rideshare}'
    )

    assert form.rideshare == expected_rideshare
    assert form.party_id == expected_party
    assert form.guest_id == expected_guest
