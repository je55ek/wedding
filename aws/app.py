import boto3
from configargparse import ArgParser

from wedding.general.resource import StoreBackedResource
from wedding.model import *
from wedding.rsvp import EnvelopeImageHandler


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
    parser.add_argument(
        '--envelope-bucket',
        env_var = 'ENVELOPE_BUCKET',
        default = 'http://s3.amazonaws.com/flyingj-wedding-envelope-images/'
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
        driver_store(
            dynamo.Table(args.drivers_table)
        )
    ).create_handler()


passengers_handler = \
    passengers_resource(
        passenger_group_store(
            dynamo.Table(args.passengers_table)
        )
    ).create_handler()


envelope_handler = \
    EnvelopeImageHandler(
        args.envelope_bucket,
        party_store(
            dynamo.Table(args.parties_table)
        )
    ).create_handler()
