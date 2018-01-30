from typing import TypeVar, Optional, Iterable

from wedding.model import JsonCodec, JsonEncoder
from wedding.store import Store
from wedding.functional import option


K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')


class DynamoDbStore(Store[K, V]):
    """Data-store that uses AWS Dynamo DB."""

    def __init__(self,
                 dynamo_table                ,
                 key_encoder : JsonEncoder[V],
                 value_codec : JsonCodec  [V]) -> None:
        self.__table      = dynamo_table
        self.__encode_key = key_encoder
        self.__val        = value_codec

    def get(self, key: K) -> Optional[V]:
        return option.fmap(self.__val.decode)(
            self.__table.get_item(Key = self.__encode_key(key))['Item']
        )

    def get_all(self) -> Iterable[V]:
        return map(self.__val.decode, self.__table.scan()['Items'])

    def put(self, value: V) -> None:
        self.__table.put_item(Item = self.__val.encode(value))

    def put_all(self, values: Iterable[V]) -> None:
        with self.__table.batch_writer() as batch:
            for v in values:
                batch.put_item(Item = self.__val.encode(v))

    def delete(self, key: K) -> None:
        self.__table.delete_item(Key = self.__encode_key(key))
