from setuptools import setup

setup(
      name        = 'wedding',
      version     = '0.1',
      description = 'Flying Js serverless wedding RSVP application.',
      author      = 'Jesse Kelly',
      license     = 'MIT',
      packages    = ['wedding'],
      install_requires = [
          'boto3 == 1.4.8',
          'botocore == 1.8.5',
          'toolz == 0.9.0',
          'marshmallow == 2.15.0',
          'configargparse == 0.12.0'
      ],
      tests_require = [
          'pytest == 3.3.2'
      ],
      extras_require = {
          'typecheck': ['mypy == 0.550']
      }
)
