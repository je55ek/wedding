from typing import Optional

from wedding.general.functional import option
from wedding.model import Guest, EmailAddress, Party


def guest(first_name: str, maybe_username: Optional[str] = None) -> Guest:
    return Guest(
        id = 'id',
        first_name = first_name,
        last_name = 'Doe',
        email = option.fmap(lambda username:
            EmailAddress(
                username = username,
                hostname = 'doe.com'
            )
                            )(maybe_username),
        invited = False,
        attending = False,
        local = True
    )


def create_party(id: str, *guests) -> Party:
    return Party(
        id = id,
        title = 'Some Family',
        guests = list(guests)
    )
