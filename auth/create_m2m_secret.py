"""
create_m2m_secret.py — Mint a Cognito M2M app client and store its credentials
in AWS Secrets Manager.

Reads pool config from auth/auth_config.json (written by post_deploy.py after
serverless deploy). Run once per new M2M consumer (or to rotate — see
rotate_m2m_secret.py for the safe swap flow).

Usage:
    python auth/create_m2m_secret.py --profile <admin-profile> --stage dev

Output: prints the secret ARN. Consumers set NZSHM22_TOSHI_M2M_SECRET_ARN to
that value (consumed by nshm_toshi_client.ToshiTokenManager).

The SM container itself is provisioned by serverless.yml (ToshiM2MSecret); this
script populates its SecretString. If the container doesn't exist yet (e.g.
running before first deploy) the script will create_secret instead.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import boto3
import click

AUTH_DIR = Path(__file__).parent
AUTH_CONFIG_FILE = AUTH_DIR / 'auth_config.json'

DEFAULT_SCOPES = 'toshi/read toshi/write'


def load_config() -> dict:
    if not AUTH_CONFIG_FILE.exists():
        raise click.ClickException(
            f'auth_config.json not found at {AUTH_CONFIG_FILE}.\nRun: python auth/post_deploy.py'
        )
    with open(AUTH_CONFIG_FILE) as f:
        return json.load(f)


@click.command()
@click.option('--profile', default='default', show_default=True, help='AWS CLI profile name')
@click.option('--region', default=None, help='AWS region (default: from auth_config.json)')
@click.option('--stage', required=True, help='Deployment stage (dev|test|prod) — used to derive default secret/client names')
@click.option('--scopes', default=DEFAULT_SCOPES, show_default=True, help='Space-separated OAuth scopes for the M2M client')
@click.option('--secret-name', default=None, help='Secrets Manager secret name (default: toshi-m2m-<stage>)')
@click.option('--client-name', default=None, help='Cognito app client name (default: toshi-m2m-<stage>-<YYYYMMDD>)')
def main(profile: str, region: str | None, stage: str, scopes: str, secret_name: str | None, client_name: str | None) -> None:
    """Create a Cognito M2M app client and store credentials in Secrets Manager."""
    config = load_config()
    pool_id = config['user_pool_id']
    region = region or config['region']

    if secret_name is None:
        secret_name = f'toshi-m2m-{stage}'
    if client_name is None:
        client_name = f'toshi-m2m-{stage}-{datetime.now(timezone.utc).strftime("%Y%m%d")}'

    session = boto3.Session(profile_name=profile, region_name=region)
    cognito = session.client('cognito-idp')
    sm = session.client('secretsmanager')

    click.echo(f'Pool:        {pool_id}')
    click.echo(f'Region:      {region}')
    click.echo(f'Client name: {client_name}')
    click.echo(f'Secret name: {secret_name}')
    click.echo(f'Scopes:      {scopes}')

    click.echo('\nCreating Cognito M2M app client ...')
    try:
        resp = cognito.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName=client_name,
            GenerateSecret=True,
            AllowedOAuthFlows=['client_credentials'],
            AllowedOAuthScopes=scopes.split(),
            AllowedOAuthFlowsUserPoolClient=True,
        )
    except cognito.exceptions.InvalidParameterException as e:
        raise click.ClickException(f'Cognito rejected the client config: {e}') from e

    client_id = resp['UserPoolClient']['ClientId']
    client_secret = resp['UserPoolClient']['ClientSecret']
    click.echo(f'  ClientId: {client_id}')

    secret_value = json.dumps({'client_id': client_id, 'client_secret': client_secret})

    click.echo(f'\nWriting to Secrets Manager: {secret_name} ...')
    try:
        sm.describe_secret(SecretId=secret_name)
        sm.put_secret_value(SecretId=secret_name, SecretString=secret_value)
        secret_arn = sm.describe_secret(SecretId=secret_name)['ARN']
        click.echo('  Updated existing secret')
    except sm.exceptions.ResourceNotFoundException:
        created = sm.create_secret(
            Name=secret_name,
            Description=f'Cognito M2M client_id + client_secret for {stage}',
            SecretString=secret_value,
        )
        secret_arn = created['ARN']
        click.echo('  Created new secret')

    click.echo('\n=== Done ===')
    click.echo(f'Set this in the consumer environment:')
    click.echo(f'  NZSHM22_TOSHI_M2M_SECRET_ARN={secret_arn}')
    click.echo(f'\nReminder: authorizer COGNITO_CLIENT_ID env var must include {client_id}')
    click.echo('(comma-separated allowlist — see auth/authorizer/handler.py)')


if __name__ == '__main__':
    main()
