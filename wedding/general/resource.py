from typing import TypeVar, Iterable

from wedding.general.aws.rest.lambda_resource import RestResource
from wedding.general.aws.rest import responses
from wedding.general.model import JsonCodec, Json
from wedding.general.store import Store


_A = TypeVar('_A')


class StoreBackedResource(RestResource[_A]):
    def __init__(self,
                 store: Store[str, _A],
                 codec: JsonCodec[_A]) -> None:
        super().__init__(codec)
        self._store = store

    def _get(self, key: str):
        return self._store.get(key) or responses.NotFound(f'No record with key {key}')

    def _get_many(self, query: Json):
        return self._store.get_all()

    def _post(self, a: _A):
        self._store.put(a)
        return responses.Created()

    def _post_many(self, a: Iterable[_A]):
        self._store.put_all(a)
        return responses.Created()

    def _delete(self, key: str):
        self._store.delete(key)
        return responses.NoContent()
