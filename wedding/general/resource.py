from typing import TypeVar, Generic, cast, Iterable
from toolz.itertoolz import isiterable
from wedding.general.aws.lambda_rest import RestResource
from wedding.general.store import Store
from wedding.general.model import JsonCodec
from wedding.general.functional import option


_K = TypeVar('_K')
_A = TypeVar('_A')


class StoreBackedResource(Generic[_K, _A], RestResource[_A]):
    def __init__(self,
                 store: Store[_K, _A],
                 codec: JsonCodec[_A]) -> None:
        super().__init__(codec)
        self._store = store

    def _get(self, path, _):
        return option.cata(
            self._store.get,
            lambda: self._store.get_all()
        )(path.get('id'))

    def _post(self, a: _A, path, query):
        maybe_id = path.get('id')
        if maybe_id is None and isiterable(a):
            self._store.put_all(cast(Iterable[_A], a))
        else:
            self._store.put(a)
