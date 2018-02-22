import boto3
import logging
from configargparse import ArgParser

from toolz import get

import wedding.invitation
from wedding.general.resource import StoreBackedResource
from wedding import rsvp, model
from wedding.general.functional import option


def parties_resource(store: model.PartyStore):
    return StoreBackedResource[model.Party](store, model.PartyCodec)


def drivers_resource(store: model.DriverStore):
    return StoreBackedResource[model.Driver](store, model.DriverCodec)


def passengers_resource(store: model.PassengerGroupStore):
    return StoreBackedResource[model.PassengerGroup](store, model.PassengerGroupCodec)


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
        default = 'http://s3.amazonaws.com/flyingj-wedding/envelopes/'
    )
    parser.add_argument(
        '--template-bucket',
        env_var = 'TEMPLATE_BUCKET',
        default = 'flyingj-wedding/templates',
        help    = 'S3 bucket name and prefix where templates are kept'
    )
    parser.add_argument(
        '--invitation-template',
        env_var = 'INVITATION_TEMPLATE',
        default = 'invitation_template.html',
        help    = 'S3 key of the invitation template'
    )
    parser.add_argument(
        '--rideshare-template',
        env_var = 'RIDESHARE_TEMPLATE',
        default = 'rideshare_template.html',
        help    = 'S3 key of the rideshare-form template'
    )
    parser.add_argument(
        '--rsvp-template',
        env_var = 'RSVP_TEMPLATE',
        default = 'rsvp_template.html',
        help    = 'S3 key of the rsvp template'
    )
    parser.add_argument(
        '--rsvp-summary-template',
        env_var = 'RSVP_SUMMARY_TEMPLATE',
        default = 'rsvp_summary_template.html',
        help    = 'S3 key of the rsvp summary template'
    )
    parser.add_argument(
        '--thank-you-template',
        env_var = 'THANK_YOU_TEMPLATE',
        default = 'thank_you_template.html',
        help    = 'S3 key of the thank-you-for-your-RSVP template'
    )
    parser.add_argument(
        '--not-found-url',
        env_var = 'NOT_FOUND_URL',
        default = 'http://www.flyingjs4.life/404.html'
    )
    parser.add_argument(
        '--rideshare-url',
        env_var = 'RIDESHARE_URL',
        default = '/rideshare?guest={{guestId}}&party={{partyId}}&local={{local}}&rideshare={{rideshare}}',
        help    = 'URL template for the ride sharing form.'
    )
    parser.add_argument(
        '--decline-url',
        env_var = 'DECLINE_URL',
        default = '/decline.html',
        help    = 'URL of the page to show when a whole party is not attending.'
    )
    parser.add_argument(
        '--thank-you-url',
        env_var = 'THANK_YOU_URL',
        default = '/thanks?firstName={{firstName}}',
        help    = 'URL template for the thank-you page.'
    )
    parser.add_argument(
        '--homepage-url',
        env_var = 'HOMEPAGE_URL',
        default = 'https://www.flyingjs4.life/index.html',
        help    = 'URL of the Flying Js wedding website homepage!'
    )
    parser.add_argument(
        '--verbosity',
        env_var = 'VERBOSITY',
        default = logging.getLevelName(logging.WARNING),
        help    = f'Logging verbosity. One of: {",".join(logging._nameToLevel.keys())}',
        type    = lambda level: logging._nameToLevel[level.upper()]
    )
    return parser


args   = argument_parser().parse_args()
dynamo = boto3.resource('dynamodb')
logging.basicConfig()
logger = logging.getLogger('life.flyingjs4.wedding')
logger.setLevel(args.verbosity)
logger.debug('New lambda instance initialized')


def _template_getter():
    template_bucket = args.template_bucket.split('/')[0]
    templates       = boto3.resource('s3').Bucket(template_bucket)
    template_prefix = option.cata(
        lambda prefix: prefix + '/',
        lambda: ''
    )(get(1, args.template_bucket.split('/'), None))

    return lambda key: templates.Object(template_prefix + key).get()['Body'].read().decode('utf-8')


get_template = _template_getter()


party_store           = model.party_store          (dynamo.Table(args.parties_table   ))
driver_store          = model.driver_store         (dynamo.Table(args.drivers_table   ))
passenger_group_store = model.passenger_group_store(dynamo.Table(args.passengers_table))


parties_handler    = parties_resource   (party_store          )
drivers_handler    = drivers_resource   (driver_store         )
passengers_handler = passengers_resource(passenger_group_store)


envelope_handler = \
    wedding.invitation.EnvelopeImageHandler(
        args.envelope_bucket,
        party_store
    )


invitation_handler = \
    wedding.invitation.InvitationHandler(
        lambda: get_template(args.invitation_template),
        args.not_found_url,
        party_store
    )


rsvp_handler = \
    rsvp.RsvpHandler(
        lambda: get_template(args.rsvp_template),
        lambda: get_template(args.rsvp_summary_template),
        args.rideshare_url,
        args.not_found_url,
        args.decline_url,
        party_store,
        logger
    )


ride_share_handler = \
    rsvp.RideShareHandler(
        lambda: get_template(args.rideshare_template),
        args.not_found_url,
        args.thank_you_url,
        party_store,
        logger
    )


thank_you_handler = \
    rsvp.ThankYouHandler(
        lambda: get_template(args.thank_you_template),
        args.homepage_url
    )
