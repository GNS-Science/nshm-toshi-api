"""
rotate_m2m_secret.py — Safely rotate Cognito M2M credentials.

Cognito user-pool app clients can't have their `client_secret` regenerated
in place. Rotation is a multi-step swap:

  1. Mint a new app client (generates a fresh client_id/client_secret pair).
  2. Optionally extend the authorizer's COGNITO_CLIENT_ID allowlist to include
     both OLD and NEW client_ids so in-flight callers stay valid.
  3. put_secret_value on the SM secret so new consumers fetch the new creds.
  4. Sleep ≥ 1 access-token TTL (default 1h) so any tokens minted with the
     old client_id expire naturally.
  5. Delete the old app client.
  6. Optionally narrow the authorizer's COGNITO_CLIENT_ID allowlist to just NEW.

Usage:
    python auth/rotate_m2m_secret.py \\
        --profile <admin-profile> --stage dev \\
        --old-client-id <existing-m2m-client-id> \\
        --authorizer-function nshm-toshi-api-dev-jwtAuthorizer

Pre-flight: capture the current --old-client-id from the Cognito console or
from the prior create_m2m_secret.py output.
"""

import json
import time
from datetime import UTC, datetime
from pathlib import Path

import boto3
import click

AUTH_DIR = Path(__file__).parent
AUTH_CONFIG_FILE = AUTH_DIR / 'auth_config.json'

DEFAULT_SCOPES = 'toshi/read toshi/write'
DEFAULT_TTL_SECONDS = 3700  # Cognito default access-token TTL is 1h; add buffer


def load_config() -> dict:
    if not AUTH_CONFIG_FILE.exists():
        raise click.ClickException(
            f'auth_config.json not found at {AUTH_CONFIG_FILE}.\nRun: python auth/post_deploy.py'
        )
    with open(AUTH_CONFIG_FILE) as f:
        return json.load(f)


def update_authorizer_allowlist(lambda_client, function_name: str, client_ids: list[str]) -> None:
    """Set the authorizer Lambda's COGNITO_CLIENT_ID env var to a comma-separated allowlist."""
    cfg = lambda_client.get_function_configuration(FunctionName=function_name)
    env = cfg.get('Environment', {}).get('Variables', {})
    env['COGNITO_CLIENT_ID'] = ','.join(client_ids)
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        Environment={'Variables': env},
    )
    click.echo(f'  Authorizer COGNITO_CLIENT_ID set to: {env["COGNITO_CLIENT_ID"]}')


@click.command()
@click.option('--profile', default='default', show_default=True, help='AWS CLI profile name')
@click.option('--region', default=None, help='AWS region (default: from auth_config.json)')
@click.option('--stage', required=True, help='Deployment stage (dev|test|prod)')
@click.option('--old-client-id', required=True, help='Existing M2M ClientId being rotated out')
@click.option(
    '--scopes', default=DEFAULT_SCOPES, show_default=True, help='Space-separated OAuth scopes for the new client'
)
@click.option('--secret-name', default=None, help='Secrets Manager secret name (default: toshi-m2m-<stage>)')
@click.option(
    '--new-client-name', default=None, help='New Cognito app client name (default: toshi-m2m-<stage>-<YYYYMMDD>)'
)
@click.option(
    '--ttl-seconds',
    default=DEFAULT_TTL_SECONDS,
    show_default=True,
    type=int,
    help='Sleep between cutover and old-client delete (≥ access-token TTL)',
)
@click.option(
    '--authorizer-function',
    default=None,
    help=(
        'Lambda fn name (e.g. spike-toshi-api-dev-jwtAuthorizer). If set, '
        'COGNITO_CLIENT_ID is updated to OLD,NEW for the overlap window, then NEW after delete.'
    ),
)
@click.option('--skip-delete', is_flag=True, help='Stop after cutover + sleep; perform delete manually later')
def main(
    profile,
    region,
    stage,
    old_client_id,
    scopes,
    secret_name,
    new_client_name,
    ttl_seconds,
    authorizer_function,
    skip_delete,
):
    """Rotate Cognito M2M credentials via a safe new-then-delete swap."""
    config = load_config()
    pool_id = config['user_pool_id']
    region = region or config['region']

    if secret_name is None:
        secret_name = f'toshi-m2m-{stage}'
    if new_client_name is None:
        new_client_name = f'toshi-m2m-{stage}-{datetime.now(UTC).strftime("%Y%m%d")}'

    session = boto3.Session(profile_name=profile, region_name=region)
    cognito = session.client('cognito-idp')
    sm = session.client('secretsmanager')
    lam = session.client('lambda') if authorizer_function else None

    click.echo(f'Pool:           {pool_id}')
    click.echo(f'Old client_id:  {old_client_id}')
    click.echo(f'New client:     {new_client_name}')
    click.echo(f'Secret:         {secret_name}')
    click.echo(f'Authorizer fn:  {authorizer_function or "(skipped)"}')
    click.echo(f'TTL sleep:      {ttl_seconds}s')

    click.echo('\n[1/6] Minting new Cognito M2M app client ...')
    resp = cognito.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName=new_client_name,
        GenerateSecret=True,
        AllowedOAuthFlows=['client_credentials'],
        AllowedOAuthScopes=scopes.split(),
        AllowedOAuthFlowsUserPoolClient=True,
    )
    new_client_id = resp['UserPoolClient']['ClientId']
    new_client_secret = resp['UserPoolClient']['ClientSecret']
    click.echo(f'  New ClientId: {new_client_id}')

    if lam:
        click.echo('\n[2/6] Extending authorizer allowlist to OLD,NEW ...')
        update_authorizer_allowlist(lam, authorizer_function, [old_client_id, new_client_id])
    else:
        click.echo('\n[2/6] Skipping authorizer update (--authorizer-function not provided)')

    click.echo(f'\n[3/6] Updating SM secret {secret_name} with new creds ...')
    sm.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps({'client_id': new_client_id, 'client_secret': new_client_secret}),
    )
    click.echo('  SM secret updated — new consumers will pick up on next fetch')

    if skip_delete:
        click.echo(f'\n[4-6] --skip-delete set. Old client {old_client_id} left in place.')
        click.echo('When ready, manually run:')
        click.echo(
            f'  aws cognito-idp delete-user-pool-client \\\n'
            f'    --user-pool-id {pool_id} --client-id {old_client_id} --profile {profile}'
        )
        return

    click.echo(f'\n[4/6] Sleeping {ttl_seconds}s for in-flight tokens to expire ...')
    time.sleep(ttl_seconds)

    click.echo(f'\n[5/6] Deleting old app client {old_client_id} ...')
    cognito.delete_user_pool_client(UserPoolId=pool_id, ClientId=old_client_id)
    click.echo('  Deleted')

    if lam:
        click.echo('\n[6/6] Narrowing authorizer allowlist to NEW only ...')
        update_authorizer_allowlist(lam, authorizer_function, [new_client_id])
    else:
        click.echo('\n[6/6] Skipping authorizer narrowing (--authorizer-function not provided)')

    click.echo('\n=== Rotation complete ===')
    click.echo(f'New client_id: {new_client_id}')


if __name__ == '__main__':
    main()
