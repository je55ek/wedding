import boto3
from configargparse import ArgParser
from wedding.general.resource import StoreBackedResource
from wedding.model import Party, party_store, PartyCodec, PartyStore


def parties_resource(store: PartyStore):
    return StoreBackedResource[Party](
        store,
        PartyCodec
    )


def argument_parser():
    parser = ArgParser()
    parser.add_argument(
        '--parties-table',
        default = 'Parties',
        env_var = 'PARTIES_TABLE'
    )
    return parser


args = argument_parser().parse_args()


parties_handler = \
    parties_resource(
        party_store(
            boto3.resource('dynamodb').Table(args.parties_table)
        )
    ).create_handler()
