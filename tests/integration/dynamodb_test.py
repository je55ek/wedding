import boto3

from toolz.itertoolz import first

from wedding.general.aws.dynamodb import DynamoDbStore
from wedding.model import Party, PartyCodec
from wedding.general.model import JsonEncoder
from tests.data_generators import create_party, guest


table = boto3.resource('dynamodb').Table('Parties')
store = DynamoDbStore[str, Party](
    table,
    JsonEncoder[str](lambda i: {'id': i}),
    PartyCodec
)
kellys = create_party(
    'kellys',
    guest('jesse', 'jkelly'),
    guest('pepino', 'pepulon'),
    guest('jenny', 'jykelly'),
    guest('greba', 'gkelly')
)


def test_put():
    store.put(kellys)
    assert store.get(kellys.id) == kellys
    store.delete(kellys.id)


def test_put_all():
    store.put_all([kellys])
    assert store.get(kellys.id) == kellys
    store.delete(kellys.id)


def test_get_all():
    store.put(kellys)
    assert first(store.get_all()) == kellys
    store.delete(kellys.id)


def test_delete():
    store.put(kellys)
    store.delete(kellys.id)
    assert len(list(store.get_all())) == 0


def test_modify():
    store.put(kellys)
    store.modify(kellys.id, lambda party: party._replace(title = "Flying Js"))
    assert store.get(kellys.id).title == "Flying Js"
    store.delete(kellys.id)
