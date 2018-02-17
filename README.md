# Flying Js Serverless Wedding Reservation System

## Structure

```
.
├── aws                 AWS deployment resources
│   └── resources       templates and static web resources
├── environment.yml     conda environment definition
├── setup.py            python setuptools package definition
├── tests               python tests
├── wedding             python package
└── README.md           this file
```

## Development

### Quick Start

`conda` is used to create an isolated development environment.

The first time you work on this project:
```bash
$ cd wedding
$ conda env create
```

Every time you work on this project:
```bash
$ source activate wedding
```

### Adding Dependencies

Check conda for packages with `conda search`. If packages are available in
the conda repositories, use `conda install` to install them. Otherwise, use
`pip`.

Add development and runtime dependencies to `environment.yml`.

Add *only runtime* dependencies to `setup.py`.

### AWS Credentials

During local development, add an AWS access key and secret key to
`~/.aws/credentials`.

### Tests

After activating the project's `conda` environment, simply run
```
(wedding) $ pytest
```

## Deployment

When you are ready to deploy changes to AWS, simpy run
```
$ cd wedding/aws
$ make deploy
```
