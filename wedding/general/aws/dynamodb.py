from typing import TypeVar, Optional, Iterable

from botocore.exceptions import ValidationError, ClientError

from wedding.general.model import JsonEncoder, JsonCodec
from wedding.general.store import Store
from wedding.general.functional import option

K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')


class DynamoDbStore(Store[K, V]):
    """Data-store that uses AWS Dynamo DB."""

    def __init__(self,
                 dynamo_table                ,
                 key_encoder : JsonEncoder[K],
                 value_codec : JsonCodec  [V]) -> None:
        self.__table      = dynamo_table
        self.__encode_key = key_encoder
        self.__val        = value_codec

    def get(self, key: K) -> Optional[V]:
        return option.fmap(self.__val.decode)(
            self.__table.get_item(Key = self.__encode_key(key)).get('Item')
        )

    def get_all(self) -> Iterable[V]:
        get_more = True
        maybe_last_key = None

        while get_more:
            response = option.cata(
                lambda last_key: self.__table.scan(ExclusiveStartKey = last_key),
                self.__table.scan
            )(maybe_last_key)

            maybe_last_key = response.get('LastEvaluatedKey')
            get_more = maybe_last_key is not None

            for item in map(self.__val.decode, response.get('Items', [])):
                yield item

    def put(self, value: V) -> None:
        self.__table.put_item(Item = self.__val.encode(value))

    def put_all(self, values: Iterable[V]) -> None:
        try:
            with self.__table.batch_writer() as batch:
                for v in values:
                    batch.put_item(Item = self.__val.encode(v))
        except ValidationError as exc:
            raise RuntimeError(f'DynamoDB failed to put {list(values)}: {str(exc)}')
        except ClientError as exc:
            raise RuntimeError(f'DynamoDB failed to put {list(values)}: {str(exc)}')

    def delete(self, key: K) -> None:
        self.__table.delete_item(Key = self.__encode_key(key))
