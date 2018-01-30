from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterable, Callable, Optional


from wedding.functional import option

K = TypeVar('K')
V = TypeVar('V')


class Store(ABC, Generic[K, V]):

    @abstractmethod
    def get(self, key: K) -> Optional[V]:
        pass

    @abstractmethod
    def get_all(self) -> Iterable[V]:
        pass

    @abstractmethod
    def put(self, value: V) -> None:
        pass

    @abstractmethod
    def put_all(self, values: Iterable[V]) -> None:
        pass

    @abstractmethod
    def delete(self, key: K) -> None:
        pass

    def modify(self, key: K, transform: Callable[[V], V]) -> Optional[V]:
        value = option.fmap(transform)(self.get(key))
        if value:
            self.put(value)
        return value
