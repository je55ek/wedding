from configargparse import ArgParser
from wedding.general.resource import StoreBackedResource
from wedding.model import *
import boto3


def parties_resource(store: PartyStore):
    return StoreBackedResource[Party](store, PartyCodec)


def drivers_resource(store: DriverStore):
    return StoreBackedResource[Driver](store, DriverCodec)


def passengers_resource(store: PassengerGroupStore):
    return StoreBackedResource[PassengerGroup](store, PassengerGroupCodec)


def argument_parser():
    parser = ArgParser()
    parser.add_argument(
        '--parties-table',
        default = 'Parties',
        env_var = 'PARTIES_TABLE'
    )
    parser.add_argument(
        '--drivers-table',
        default = 'Drivers',
        env_var = 'DRIVERS_TABLE'
    )
    parser.add_argument(
        '--passengers-table',
        default = 'Passengers',
        env_var = 'PASSENGERS_TABLE'
    )
    return parser


args = argument_parser().parse_args()
dynamo = boto3.resource('dynamodb')


parties_handler = \
    parties_resource(
        party_store(
            dynamo.Table(args.parties_table)
        )
    ).create_handler()


drivers_handler = \
    drivers_resource(
        party_store(
            boto3.resource('dynamodb').Table(args.drivers_table)
        )
    ).create_handler()


passengers_handler = \
    passengers_resource(
        party_store(
            boto3.resource('dynamodb').Table(args.passengers_table)
        )
    ).create_handler()
