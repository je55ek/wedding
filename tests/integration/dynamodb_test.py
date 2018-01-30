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
trekkies = create_party(
    'trekkies',
    guest('jean luc', 'jpicard'),
    guest('data', 'data'),
    guest('deanna', 'dtroi'),
    guest('geordi', 'glaforge')
)


def test_put():
    store.put(trekkies)
    assert store.get(trekkies.id) == trekkies
    store.delete(trekkies.id)


def test_put_all():
    store.put_all([trekkies])
    assert store.get(trekkies.id) == trekkies
    store.delete(trekkies.id)


def test_get_all():
    store.put(trekkies)
    assert first(store.get_all()) == trekkies
    store.delete(trekkies.id)


def test_delete():
    store.put(trekkies)
    store.delete(trekkies.id)
    assert len(list(store.get_all())) == 0


def test_modify():
    store.put(trekkies)
    store.modify(trekkies.id, lambda party: party._replace(title ="Flying Js"))
    assert store.get(trekkies.id).title == "Flying Js"
    store.delete(trekkies.id)
