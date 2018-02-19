from wedding.rsvp import RsvpFormData, RideShareFormData


def test_rsvp_form_parse():
    expected_party = 'someparty'
    expected_guest = 'someguest'
    form = RsvpFormData.parse(
        f'${RsvpFormData.PARTY_ID_FIELD}={expected_party}&' +
        f'${RsvpFormData.GUEST_ID_FIELD}={expected_guest}&' +
        'jba=true&jenny=true'
    )
