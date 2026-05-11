"""
create_users.py — Create Cognito test users and assign them to groups.

Reads user definitions from auth/test_users.json and pool config from
auth/auth_config.json (written by post_deploy.py after cdk deploy).

Usage:
    python auth/create_users.py --profile AdministratorAccess-595842668254

test_users.json format:
    [
      {
        "username": "scientist@example.com",
        "password": "Temp1234!",
        "groups": ["toshi-writers", "runzi-local"]
      },
      ...
    ]

Users are NOT managed by CDK (environment-specific, credentials gitignored).
They are deleted automatically when the User Pool is removed via `cdk destroy`.
"""

import json
from pathlib import Path

import boto3
import click

AUTH_DIR = Path(__file__).parent
AUTH_CONFIG_FILE = AUTH_DIR / 'auth_config.json'
USERS_FILE = AUTH_DIR / 'test_users.json'


def load_config() -> dict:
    if not AUTH_CONFIG_FILE.exists():
        raise click.ClickException(
            f'auth_config.json not found at {AUTH_CONFIG_FILE}.\nRun: python auth/post_deploy.py'
        )
    with open(AUTH_CONFIG_FILE) as f:
        return json.load(f)


def load_users() -> list:
    if not USERS_FILE.exists():
        raise click.ClickException(
            f'test_users.json not found at {USERS_FILE}.\nCreate the file with user definitions (gitignored).'
        )
    with open(USERS_FILE) as f:
        return json.load(f)


@click.command()
@click.option('--profile', default='default', show_default=True, help='AWS CLI profile name')
@click.option('--region', default=None, help='AWS region (default: from auth_config.json)')
def main(profile: str, region: str | None) -> None:
    """Create Cognito test users and assign them to groups."""
    config = load_config()
    users = load_users()

    pool_id = config['user_pool_id']
    region = region or config['region']

    session = boto3.Session(profile_name=profile, region_name=region)
    client = session.client('cognito-idp')

    click.echo(f'Creating users in pool: {pool_id}')

    for user in users:
        username = user['username']
        password = user['password']
        groups = user.get('groups', [])

        click.echo(f'\nEnsuring user: {username} ...')
        try:
            client.admin_create_user(
                UserPoolId=pool_id,
                Username=username,
                TemporaryPassword=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': username},
                    {'Name': 'email_verified', 'Value': 'true'},
                ],
                MessageAction='SUPPRESS',
            )
            client.admin_set_user_password(
                UserPoolId=pool_id,
                Username=username,
                Password=password,
                Permanent=True,
            )
            click.echo(f'  Created: {username}')
        except client.exceptions.UsernameExistsException:
            click.echo(f'  Already exists: {username}')

        for group in groups:
            try:
                client.admin_add_user_to_group(
                    UserPoolId=pool_id,
                    Username=username,
                    GroupName=group,
                )
                click.echo(f'  Added to group: {group}')
            except client.exceptions.ResourceNotFoundException:
                click.echo(f'  Warning: group not found: {group}')
            except Exception as e:
                click.echo(f'  Warning adding to {group}: {e}')

    click.echo('\n=== Users created ===')
    click.echo('Next step: python auth/toshi_auth.py login')


if __name__ == '__main__':
    main()
