"""
Cognito Setup Script for nshm-toshi-api auth spike.

Creates all Cognito resources needed for the spike:
  - User Pool (toshi-spike)
  - Resource server with toshi/read and toshi/write scopes
  - App client for scientists (Device Authorization Grant, public)
  - App client for automation (Client Credentials, confidential)
  - Identity Pool with IAM role mappings
  - Test users

Usage:
    python auth_migration/auth/cognito_setup.py --profile test-account [--region ap-southeast-2]
    python auth_migration/auth/cognito_setup.py --profile test-account --teardown  # Remove all resources

Outputs cognito_config.json in the same directory.
"""
import json
import os
import time

import boto3
import click


COGNITO_IDENTITY_POOL_NAME = 'toshi-spike-identity-pool'


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'cognito_config.json')

POOL_NAME = 'toshi-spike'
RESOURCE_SERVER_IDENTIFIER = 'toshi'
SCIENTIST_CLIENT_NAME = 'toshi-scientist'
AUTOMATION_CLIENT_NAME = 'toshi-automation'
COGNITO_DOMAIN_PREFIX = 'toshi-spike-auth'

TEST_USERS = [
    {
        'username': os.environ.get('TOSHI_TEST_USER1_EMAIL', 'scientist@example.com'),
        'password': os.environ.get('TOSHI_TEST_USER1_PASSWORD', 'Scienti5t!'),
        'scopes': ['toshi/read', 'toshi/write'],
        'groups': ['toshi-writers'],
    },
    {
        'username': os.environ.get('TOSHI_TEST_USER2_EMAIL', 'readonly@example.com'),
        'password': os.environ.get('TOSHI_TEST_USER2_PASSWORD', 'Read0nly!'),
        'scopes': ['toshi/read'],
        'groups': ['toshi-readers'],
    },
    {
        'username': os.environ.get('TOSHI_TEST_USER3_EMAIL', 'runzi-local@example.com'),
        'password': os.environ.get('TOSHI_TEST_USER3_PASSWORD', 'RunziL0cal!'),
        'scopes': ['toshi/read', 'toshi/write'],
        'groups': ['runzi-local'],
    },
    {
        'username': os.environ.get('TOSHI_TEST_USER4_EMAIL', 'runzi-batch@example.com'),
        'password': os.environ.get('TOSHI_TEST_USER4_PASSWORD', 'RunziB4tch!'),
        'scopes': ['toshi/read', 'toshi/write'],
        'groups': ['runzi-batch'],
    },
    {
        'username': os.environ.get('TOSHI_TEST_USER5_EMAIL', 'runzi-admin@example.com'),
        'password': os.environ.get('TOSHI_TEST_USER5_PASSWORD', 'RunziAdm1n!'),
        'scopes': ['toshi/read', 'toshi/write'],
        'groups': ['runzi-admin'],
    },
]


def get_client(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client('cognito-idp')


def create_user_pool(client, region):
    click.echo(f'Creating User Pool: {POOL_NAME} ...')
    resp = client.create_user_pool(
        PoolName=POOL_NAME,
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True,
            }
        },
        AutoVerifiedAttributes=['email'],
        UsernameAttributes=['email'],
        Schema=[
            {
                'Name': 'email',
                'AttributeDataType': 'String',
                'Required': True,
                'Mutable': True,
            }
        ],
        AdminCreateUserConfig={
            'AllowAdminCreateUserOnly': True,  # Prevent self-registration in spike
        },
    )
    pool_id = resp['UserPool']['Id']
    click.echo(f'  Created pool: {pool_id}')
    return pool_id


def create_resource_server(client, pool_id):
    click.echo('Creating resource server: toshi ...')
    client.create_resource_server(
        UserPoolId=pool_id,
        Identifier=RESOURCE_SERVER_IDENTIFIER,
        Name='Toshi API',
        Scopes=[
            {'ScopeName': 'read', 'ScopeDescription': 'Read access to GraphQL queries'},
            {'ScopeName': 'write', 'ScopeDescription': 'Write access to GraphQL mutations'},
        ],
    )
    click.echo('  Created resource server with toshi/read and toshi/write scopes')


def create_user_pool_domain(client, pool_id, region):
    """Create a Cognito hosted UI domain (needed for Device Flow and Client Credentials)."""
    domain = f'{COGNITO_DOMAIN_PREFIX}-{pool_id.split("_")[1].lower()}'
    click.echo(f'Creating Cognito domain: {domain} ...')
    try:
        client.create_user_pool_domain(Domain=domain, UserPoolId=pool_id)
        click.echo(f'  Domain: {domain}.auth.{region}.amazoncognito.com')
    except client.exceptions.InvalidParameterException as e:
        if 'already exists' in str(e):
            click.echo(f'  Domain already exists: {domain}')
        else:
            raise
    return f'{domain}.auth.{region}.amazoncognito.com'


def create_scientist_client(client, pool_id):
    """Public client for Device Authorization Grant (scientists on SSH terminals)."""
    click.echo(f'Creating app client: {SCIENTIST_CLIENT_NAME} ...')
    resp = client.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName=SCIENTIST_CLIENT_NAME,
        GenerateSecret=False,  # Public client — no secret
        ExplicitAuthFlows=[
            'ALLOW_USER_PASSWORD_AUTH',
            'ALLOW_REFRESH_TOKEN_AUTH',
        ],
        AllowedOAuthFlows=['code'],
        AllowedOAuthScopes=[
            'openid',
            'email',
            'profile',
            f'{RESOURCE_SERVER_IDENTIFIER}/read',
            f'{RESOURCE_SERVER_IDENTIFIER}/write',
        ],
        AllowedOAuthFlowsUserPoolClient=True,
        SupportedIdentityProviders=['COGNITO'],
        # Device flow needs a callback that accepts the code — use localhost for spike
        CallbackURLs=['http://localhost:9999/callback'],
        LogoutURLs=['http://localhost:9999/logout'],
    )
    client_id = resp['UserPoolClient']['ClientId']
    click.echo(f'  Created scientist client: {client_id}')
    return client_id


def create_automation_client(client, pool_id):
    """Confidential client for Client Credentials (Runzi M2M)."""
    click.echo(f'Creating app client: {AUTOMATION_CLIENT_NAME} ...')
    resp = client.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName=AUTOMATION_CLIENT_NAME,
        GenerateSecret=True,  # Confidential client — has secret
        AllowedOAuthFlows=['client_credentials'],
        AllowedOAuthScopes=[
            f'{RESOURCE_SERVER_IDENTIFIER}/read',
            f'{RESOURCE_SERVER_IDENTIFIER}/write',
        ],
        AllowedOAuthFlowsUserPoolClient=True,
    )
    client_id = resp['UserPoolClient']['ClientId']
    client_secret = resp['UserPoolClient'].get('ClientSecret', '')
    click.echo(f'  Created automation client: {client_id}')
    return client_id, client_secret


def create_groups(client, pool_id):
    """Create user groups that map to scopes and IAM roles."""
    for group_name, description in [
        ('toshi-writers', 'Users with toshi/read + toshi/write access'),
        ('toshi-readers', 'Users with toshi/read access only'),
        ('runzi-local', 'Runzi users with local workstation AWS access (ECR, S3)'),
        ('runzi-batch', 'Runzi users with Batch submit access'),
        ('runzi-admin', 'Runzi users with Batch admin and ECR push access'),
    ]:
        click.echo(f'Creating group: {group_name} ...')
        try:
            client.create_group(
                GroupName=group_name,
                UserPoolId=pool_id,
                Description=description,
            )
        except client.exceptions.GroupExistsException:
            click.echo(f'  Group already exists: {group_name}')


def create_test_users(client, pool_id):
    """Create test users and assign to groups."""
    for user in TEST_USERS:
        username = user['username']
        click.echo(f'Creating user: {username} ...')
        try:
            client.admin_create_user(
                UserPoolId=pool_id,
                Username=username,
                TemporaryPassword=user['password'],
                UserAttributes=[{'Name': 'email', 'Value': username}, {'Name': 'email_verified', 'Value': 'true'}],
                MessageAction='SUPPRESS',  # Don't send welcome email
            )
            # Set permanent password (bypass force-change on first login)
            client.admin_set_user_password(
                UserPoolId=pool_id,
                Username=username,
                Password=user['password'],
                Permanent=True,
            )
            # Add to groups
            for group in user['groups']:
                client.admin_add_user_to_group(
                    UserPoolId=pool_id,
                    Username=username,
                    GroupName=group,
                )
            click.echo(f'  Created {username} in groups: {user["groups"]}')
        except client.exceptions.UsernameExistsException:
            click.echo(f'  User already exists: {username}')


def create_identity_pool(pool_name, user_pool_id, user_pool_arn, region, role_arns):
    """Create Cognito Identity Pool with role mappings by group."""
    identity_client = boto3.client('cognito-identity', region_name=region)

    click.echo(f'Creating Identity Pool: {pool_name} ...')
    resp = identity_client.create_identity_pool(
        IdentityPoolName=pool_name,
        AllowUnauthenticatedIdentities=False,
        CognitoIdentityProviders=[
            {
                'ProviderName': user_pool_arn,
                'ClientId': SCIENTIST_CLIENT_NAME,
            }
        ],
    )
    pool_id = resp['IdentityPoolId']
    click.echo(f'  Created pool: {pool_id}')

    click.echo('Setting up role mappings by Cognito groups ...')
    role_mapping = {}
    for group_name in ['toshi-readers', 'toshi-writers', 'runzi-local', 'runzi-batch', 'runzi-admin']:
        role_key = group_name.replace('toshi-', '').replace('runzi-', '')
        if role_key == 'readers':
            role_key = 'readers'
        elif role_key == 'writers':
            role_key = 'writers'
        role_arn = role_arns.get(role_key)
        if role_arn:
            role_mapping[group_name] = {
                'Type': 'Token',
                'MatchCriteria': {},
                'Rules': [
                    {
                        'MatchType': 'Contains',
                        'RuleClaim': 'cognito:groups',
                        'Value': group_name,
                    }
                ],
                'RoleARN': role_arn,
            }

    authenticated_role = role_arns.get('authenticated') or role_arns.get('writers')
    if authenticated_role:
        identity_client.set_identity_pool_roles(
            IdentityPoolId=pool_id,
            Roles={
                'authenticated': authenticated_role,
            },
            RoleMappings=role_mapping,
        )
        click.echo(f'  Configured role mappings for groups: {", ".join(role_mapping.keys())}')
    else:
        click.echo('  Skipping role mappings (run iam_roles.py first to get role ARNs)')

    return pool_id


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    click.echo(f'\nConfig saved to: {CONFIG_FILE}')


def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise click.ClickException(f'Config file not found: {CONFIG_FILE}. Run setup first.')
    with open(CONFIG_FILE) as f:
        return json.load(f)


def teardown(client, config):
    pool_id = config['user_pool_id']
    identity_pool_id = config.get('identity_pool_id')
    domain = config.get('cognito_domain', '').split('.')[0]
    region = config.get('region', 'ap-southeast-2')

    click.echo(f'Tearing down Cognito resources for pool: {pool_id}')

    if identity_pool_id:
        identity_client = boto3.client('cognito-identity', region_name=region)
        click.echo(f'Deleting Identity Pool: {identity_pool_id} ...')
        try:
            identity_client.delete_identity_pool(IdentityPoolId=identity_pool_id)
            click.echo('  Deleted Identity Pool')
        except Exception as e:
            click.echo(f'  Warning deleting Identity Pool: {e}')

    if domain:
        click.echo(f'Deleting domain: {domain} ...')
        try:
            client.delete_user_pool_domain(Domain=domain, UserPoolId=pool_id)
        except Exception as e:
            click.echo(f'  Warning: {e}')

    click.echo(f'Deleting User Pool: {pool_id} ...')
    try:
        client.delete_user_pool(UserPoolId=pool_id)
        click.echo('  Done.')
    except Exception as e:
        click.echo(f'  Error: {e}')

    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        click.echo(f'Removed: {CONFIG_FILE}')


@click.command()
@click.option('--profile', default='default', help='AWS CLI profile name', show_default=True)
@click.option('--region', default='ap-southeast-2', help='AWS region', show_default=True)
@click.option('--teardown', 'do_teardown', is_flag=True, default=False, help='Remove all Cognito resources')
def main(profile, region, do_teardown):
    """Provision (or tear down) Cognito resources for the nshm-toshi-api auth spike."""
    client = get_client(profile, region)

    if do_teardown:
        config = load_config()
        teardown(client, config)
        return

    # --- Create resources ---
    pool_id = create_user_pool(client, region)
    create_resource_server(client, pool_id)
    cognito_domain = create_user_pool_domain(client, pool_id, region)
    scientist_client_id = create_scientist_client(client, pool_id)
    automation_client_id, automation_client_secret = create_automation_client(client, pool_id)
    create_groups(client, pool_id)
    create_test_users(client, pool_id)

    user_pool_arn = f'cognito-idp.{region}.amazonaws.com/{pool_id}'
    iam_roles_config_file = os.path.join(os.path.dirname(__file__), 'iam_roles_config.json')
    if os.path.exists(iam_roles_config_file):
        with open(iam_roles_config_file) as f:
            iam_config = json.load(f)
        role_arns = {
            'readers': None,
            'writers': None,
            'local': iam_config['roles'].get('toshi-runzi-local'),
            'batch': iam_config['roles'].get('toshi-runzi-batch'),
            'admin': iam_config['roles'].get('toshi-runzi-admin'),
            'authenticated': iam_config['roles'].get('toshi-runzi-local'),
        }
        click.echo('\nLoaded IAM role ARNs from iam_roles_config.json')
    else:
        role_arns = {
            'readers': None,
            'writers': None,
            'local': None,
            'batch': None,
            'admin': None,
            'authenticated': None,
        }
        click.echo('\nNote: iam_roles_config.json not found. Identity Pool will be created without IAM role ARNs.')
        click.echo('Run iam_roles.py first for full setup.')

    identity_pool_id = create_identity_pool(
        COGNITO_IDENTITY_POOL_NAME,
        pool_id,
        user_pool_arn,
        region,
        role_arns,
    )

    config = {
        'user_pool_id': pool_id,
        'identity_pool_id': identity_pool_id,
        'region': region,
        'cognito_domain': cognito_domain,
        'issuer': f'https://cognito-idp.{region}.amazonaws.com/{pool_id}',
        'jwks_uri': f'https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json',
        'scientist_client_id': scientist_client_id,
        'automation_client_id': automation_client_id,
        'automation_client_secret': automation_client_secret,
        'scopes': {
            'read': f'{RESOURCE_SERVER_IDENTIFIER}/read',
            'write': f'{RESOURCE_SERVER_IDENTIFIER}/write',
        },
        'test_users': [{'username': u['username'], 'password': u['password']} for u in TEST_USERS],
    }

    save_config(config)

    click.echo('\n=== Cognito Setup Complete ===')
    click.echo(f'Pool ID:            {pool_id}')
    click.echo(f'Identity Pool ID:   {identity_pool_id}')
    click.echo(f'Region:             {region}')
    click.echo(f'Domain:             {cognito_domain}')
    click.echo(f'Scientist client:   {scientist_client_id}')
    click.echo(f'Automation client:  {automation_client_id}')
    click.echo('\nNext steps:')
    click.echo('  1. python auth_migration/auth/iam_roles.py --identity-pool-id {identity_pool_id}')
    click.echo('  2. Update Identity Pool role mappings with IAM role ARNs')
    click.echo('  3. python auth_migration/auth/toshi_auth.py login')
    click.echo('  4. python auth_migration/auth/toshi_auth.py aws-creds')


if __name__ == '__main__':
    main()
