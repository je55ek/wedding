from typing import Optional

from wedding.functional import option
from wedding.model import Guest, Email, Party


def guest(first_name: str, maybe_username: Optional[str]) -> Guest:
    return Guest(
        id = 'id',
        first_name = first_name,
        last_name = 'Doe',
        email = option.fmap(lambda username:
            Email(
                username = username,
                hostname = 'doe.com'
            )
        )(maybe_username),
        invited = False,
        attending = False
    )


def create_party(*guests) -> Party:
    return Party(
        id = 'id',
        title = 'Some Family',
        guests = list(guests)
    )