"""
IAM Roles Setup for nshm-toshi-api SSO integration.

Creates IAM roles and policies for Runzi users:
  - toshi-runzi-local: workstation use (ECR pull, S3 read/write)
  - toshi-runzi-batch: + Batch submit/describe
  - toshi-runzi-admin: + Batch configure, ECR push/create

All roles have trust policy for Cognito Identity Pool (AssumeRoleWithWebIdentity).

Usage:
    python auth_migration/auth/iam_roles.py --profile test-account [--region ap-southeast-2]
    python auth_migration/auth/iam_roles.py --profile test-account --teardown  # Remove all roles

Outputs iam_roles_config.json in the same directory.

The identity pool ID is read from cognito_config.json (created by cognito_setup.py).
"""
import json
import os

import boto3
import click


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'iam_roles_config.json')
COGNITO_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'cognito_config.json')

ROLE_NAMES = {
    'local': 'toshi-runzi-local',
    'batch': 'toshi-runzi-batch',
    'admin': 'toshi-runzi-admin',
}

S3_BUCKETS = [
    'arn:aws:s3:::nshm-runzi-output-*',
    'arn:aws:s3:::nshm-runzi-output-*/*',
    'arn:aws:s3:::nshm-runzi-jars',
    'arn:aws:s3:::nshm-runzi-jars/*',
]

ECR_REPOS = [
    'arn:aws:ecr:*:*:repository/nshm-runzi-*',
]

BATCH_RESOURCES = [
    'arn:aws:batch:*:*:compute-environment/*',
    'arn:aws:batch:*:*:job-queue/*',
    'arn:aws:batch:*:*:job-definition/*',
    'arn:aws:batch:*:*:job/*',
]


def get_client(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client('iam')


def get_sts_client(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client('sts')


def build_trust_policy(identity_pool_id, region):
    """Build trust policy for Cognito Identity Pool."""
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Principal': {
                    'Federated': 'cognito-identity.amazonaws.com'
                },
                'Action': 'sts:AssumeRoleWithWebIdentity',
                'Condition': {
                    'StringEquals': {
                        'cognito-identity.amazonaws.com:aud': identity_pool_id
                    },
                    'ForAnyValue:StringLike': {
                        'cognito-identity.amazonaws.com:amr': 'authenticated'
                    }
                }
            }
        ]
    }


def build_local_policy():
    """Build policy for toshi-runzi-local role."""
    return {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'ECRRead',
                'Effect': 'Allow',
                'Action': [
                    'ecr:GetAuthorizationToken',
                    'ecr:BatchGetImage',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:DescribeRepositories',
                    'ecr:ListImages',
                ],
                'Resource': ['*'],
            },
            {
                'Sid': 'S3ReadWrite',
                'Effect': 'Allow',
                'Action': [
                    's3:GetObject',
                    's3:PutObject',
                    's3:ListBucket',
                    's3:PutObjectAcl',
                ],
                'Resource': S3_BUCKETS,
            },
        ]
    }


def build_batch_policy():
    """Build policy for toshi-runzi-batch role (extends local)."""
    policy = build_local_policy()
    policy['Statement'].append({
        'Sid': 'BatchRead',
        'Effect': 'Allow',
        'Action': [
            'batch:SubmitJob',
            'batch:DescribeJobs',
            'batch:ListJobs',
            'batch:TerminateJob',
            'batch:DescribeJobQueues',
            'batch:DescribeComputeEnvironments',
            'batch:DescribeJobDefinitions',
        ],
        'Resource': ['*'],
    })
    return policy


def build_admin_policy():
    """Build policy for toshi-runzi-admin role (extends batch)."""
    policy = build_batch_policy()
    policy['Statement'].append({
        'Sid': 'BatchAdmin',
        'Effect': 'Allow',
        'Action': [
            'batch:CreateComputeEnvironment',
            'batch:UpdateComputeEnvironment',
            'batch:DeleteComputeEnvironment',
            'batch:RegisterJobDefinition',
            'batch:DeregisterJobDefinition',
        ],
        'Resource': ['*'],
    })
    policy['Statement'].append({
        'Sid': 'ECRAdmin',
        'Effect': 'Allow',
        'Action': [
            'ecr:CreateRepository',
            'ecr:PutImage',
            'ecr:InitiateLayerUpload',
            'ecr:UploadLayerPart',
            'ecr:CompleteLayerUpload',
            'ecr:BatchDeleteImage',
        ],
        'Resource': ECR_REPOS,
    })
    return policy


def create_role(iam_client, role_name, trust_policy, policy_document):
    """Create IAM role with inline policy."""
    try:
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f'Runzi {role_name.replace("toshi-runzi-", "")} access role',
            MaxSessionDuration=3600,
        )
        click.echo(f'  Created role: {role_name}')
    except iam_client.exceptions.EntityAlreadyExistsException:
        click.echo(f'  Role already exists: {role_name}')

    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName=f'{role_name}-policy',
        PolicyDocument=json.dumps(policy_document),
    )
    click.echo(f'  Attached policy to {role_name}')


def create_roles(profile, region, identity_pool_id):
    """Create all three IAM roles."""
    iam_client = get_client(profile, region)

    trust_policy = build_trust_policy(identity_pool_id, region)

    roles_config = [
        ('local', build_local_policy()),
        ('batch', build_batch_policy()),
        ('admin', build_admin_policy()),
    ]

    for key, policy in roles_config:
        role_name = ROLE_NAMES[key]
        create_role(iam_client, role_name, trust_policy, policy)

    return {role_name: ROLE_NAMES[role_name] for role_name in ROLE_NAMES}


def teardown(iam_client, profile, region):
    """Delete all IAM roles."""
    for role_name in ROLE_NAMES.values():
        click.echo(f'Deleting role: {role_name} ...')
        try:
            iam_client.delete_role_policy(
                RoleName=role_name,
                PolicyName=f'{role_name}-policy',
            )
            iam_client.delete_role(RoleName=role_name)
            click.echo(f'  Deleted {role_name}')
        except iam_client.exceptions.NoSuchEntityException:
            click.echo(f'  Role not found: {role_name}')
        except Exception as e:
            click.echo(f'  Error deleting {role_name}: {e}')


@click.command()
@click.option('--profile', default='default', help='AWS CLI profile name', show_default=True)
@click.option('--region', default='ap-southeast-2', help='AWS region', show_default=True)
@click.option('--teardown', 'do_teardown', is_flag=True, default=False, help='Remove all IAM roles')
def main(profile, region, do_teardown):
    """Provision (or tear down) IAM roles for Runzi SSO integration."""
    iam_client = get_client(profile, region)

    if do_teardown:
        teardown(iam_client, profile, region)
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            click.echo(f'Removed: {CONFIG_FILE}')
        return

    cognito_config = {}
    if os.path.exists(COGNITO_CONFIG_FILE):
        with open(COGNITO_CONFIG_FILE) as f:
            cognito_config = json.load(f)

    identity_pool_id = cognito_config.get('identity_pool_id')
    if not identity_pool_id:
        raise click.ClickException(
            'Identity Pool ID not found in cognito_config.json.\n'
            'Run: python auth_migration/auth/cognito_setup.py first'
        )

    click.echo(f'Creating IAM roles for Identity Pool: {identity_pool_id} ...')

    role_arns = create_roles(profile, region, identity_pool_id)

    config = {
        'roles': {
            'toshi-runzi-local': role_arns['local'],
            'toshi-runzi-batch': role_arns['batch'],
            'toshi-runzi-admin': role_arns['admin'],
        },
        'region': region,
        'identity_pool_id': identity_pool_id,
    }

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    click.echo(f'\nConfig saved to: {CONFIG_FILE}')

    click.echo('\n=== IAM Roles Setup Complete ===')
    for role_name in ROLE_NAMES.values():
        click.echo(f'  {role_name}')

    click.echo('\nNext steps:')
    click.echo(f'  1. Update Identity Pool role mappings in AWS Console:')
    click.echo(f'     Cognito → Identity Pools → {identity_pool_id} → Edit → Role mappings')
    click.echo(f'  2. Or use AWS CLI:')
    click.echo(f'     aws cognito-identity set-identity-pool-roles --identity-pool-id {identity_pool_id} ...')
    click.echo(f'  3. Test: python auth_migration/auth/toshi_auth.py login && python auth_migration/auth/toshi_auth.py aws-creds')


if __name__ == '__main__':
    main()
