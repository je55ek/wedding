import json

from wedding.general.aws.rest.responses import Created, InternalServerError


def test_no_message():
    created = Created()
    as_json = created.as_json()

    assert as_json['statusCode'] == created.status_code
    assert not as_json['isBase64Encoded']
    assert as_json['body'] == ''
    assert created.body == ''


def test_message():
    error = InternalServerError('some message')
    as_json = error.as_json()

    assert as_json['statusCode'] == error.status_code
    assert not as_json['isBase64Encoded']
    assert json.loads(as_json['body'])['message'] == 'some message'
    assert error.body == as_json['body']
