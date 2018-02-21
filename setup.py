from setuptools import setup, find_packages

setup(
      name        = 'wedding',
      version     = '1.0.16',
      description = 'Flying Js serverless wedding RSVP application.',
      author      = 'Jesse',
      license     = 'MIT',
      packages    = find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      install_requires = [
          'toolz == 0.9.0',
          'marshmallow == 2.15.0',
          'configargparse == 0.12.0',
          'pystache == 0.5.4'
      ],
      tests_require = [
          'pytest == 3.3.2'
      ],
      extras_require = {
          'typecheck': ['mypy == 0.550'],
          'local': ['boto3 == 1.4.8', 'botocore == 1.8.5'],
          'aws': ['awscli == 1.14.32']
      }
)
