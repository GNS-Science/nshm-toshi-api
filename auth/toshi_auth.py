"""
Toshi Auth CLI — scientist and automation token management.

Usage:
    python toshi_auth.py login         # Username/password login, saves token to ~/.toshi/credentials
    python toshi_auth.py token         # Print current Bearer token (auto-refresh)
    python toshi_auth.py whoami        # Decode and display JWT claims
    python toshi_auth.py m2m-token     # Client credentials flow for automation/Runzi
    python toshi_auth.py aws-creds     # Exchange token for AWS STS credentials

Token storage:
    ~/.toshi/credentials (JSON)
    ~/.aws/credentials [toshi] (via aws-creds command)

Configuration (reads auth/auth_config.json OR env vars):
    TOSHI_COGNITO_CONFIG   path to auth_config.json (default: auth/auth_config.json)
    TOSHI_CLIENT_ID        override automation client_id (for m2m-token)
    TOSHI_CLIENT_SECRET    override automation client_secret (for m2m-token)
"""
import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import boto3
import click
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

CREDENTIALS_PATH = Path.home() / '.toshi' / 'credentials'
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'auth_config.json')


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_auth_config():
    config_path = os.environ.get('TOSHI_COGNITO_CONFIG', DEFAULT_CONFIG_PATH)
    if not os.path.exists(config_path):
        raise click.ClickException(
            f'Cognito config not found at {config_path}.\n'
            'Run: python auth/cognito_setup.py --profile <your-aws-profile>'
        )
    with open(config_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Credential file helpers
# ---------------------------------------------------------------------------

def load_credentials():
    if not CREDENTIALS_PATH.exists():
        return {}
    with open(CREDENTIALS_PATH) as f:
        return json.load(f)


def save_credentials(data):
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.parent.chmod(0o700)
    with open(CREDENTIALS_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    CREDENTIALS_PATH.chmod(0o600)


# ---------------------------------------------------------------------------
# JWT helpers (no signature verification — authorizer does that)
# ---------------------------------------------------------------------------

def decode_jwt_payload(token):
    """Decode JWT payload without verifying signature (for display only)."""
    parts = token.split('.')
    if len(parts) != 3:
        raise click.ClickException('Invalid JWT format')
    # Add padding
    payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def is_token_expired(token, buffer_seconds=60):
    """Return True if token expires within buffer_seconds."""
    try:
        payload = decode_jwt_payload(token)
        exp = payload.get('exp', 0)
        return time.time() >= (exp - buffer_seconds)
    except Exception:
        return True


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no requests dep for this CLI)
# ---------------------------------------------------------------------------

def http_post_form(url, data, auth=None):
    """POST application/x-www-form-urlencoded, return parsed JSON."""
    body = urlencode(data).encode()
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if auth:
        credentials = base64.b64encode(f'{auth[0]}:{auth[1]}'.encode()).decode()
        headers['Authorization'] = f'Basic {credentials}'
    req = Request(url, data=body, headers=headers, method='POST')
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Username / Password flow (USER_PASSWORD_AUTH via Cognito InitiateAuth API)
# ---------------------------------------------------------------------------

def password_flow_login(config):
    """Authenticate with email + password via Cognito USER_PASSWORD_AUTH."""
    region = config['region']
    client_id = config['scientist_client_id']

    email = click.prompt('Email')
    password = click.prompt('Password', hide_input=True)

    cognito = boto3.client('cognito-idp', region_name=region)
    try:
        resp = cognito.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': email, 'PASSWORD': password},
            ClientId=client_id,
        )
    except cognito.exceptions.NotAuthorizedException:
        raise click.ClickException('Invalid username or password.')
    except cognito.exceptions.UserNotFoundException:
        raise click.ClickException('User not found.')
    except Exception as e:
        raise click.ClickException(f'Authentication failed: {e}')

    if 'ChallengeName' in resp:
        raise click.ClickException(f'Unexpected auth challenge: {resp["ChallengeName"]}. Contact your administrator.')

    auth = resp['AuthenticationResult']
    return {
        'access_token': auth['AccessToken'],
        'id_token': auth.get('IdToken', ''),
        'refresh_token': auth.get('RefreshToken', ''),
        'token_type': auth.get('TokenType', 'Bearer'),
        'expires_in': auth.get('ExpiresIn', 3600),
    }


def refresh_token(config, refresh_tok):
    """Use refresh token to get a new access token via Cognito InitiateAuth."""
    region = config['region']
    client_id = config['scientist_client_id']

    cognito = boto3.client('cognito-idp', region_name=region)
    resp = cognito.initiate_auth(
        AuthFlow='REFRESH_TOKEN_AUTH',
        AuthParameters={'REFRESH_TOKEN': refresh_tok},
        ClientId=client_id,
    )
    auth = resp['AuthenticationResult']
    return {
        'access_token': auth['AccessToken'],
        'id_token': auth.get('IdToken', ''),
        'expires_in': auth.get('ExpiresIn', 3600),
    }


# ---------------------------------------------------------------------------
# Client Credentials flow (M2M / Runzi)
# ---------------------------------------------------------------------------

def client_credentials_flow(config):
    """Obtain access token via client credentials (no user context)."""
    domain = config['cognito_domain']
    client_id = os.environ.get('TOSHI_CLIENT_ID', config.get('automation_client_id', ''))
    client_secret = os.environ.get('TOSHI_CLIENT_SECRET', config.get('automation_client_secret', ''))

    if not client_id or not client_secret:
        raise click.ClickException(
            'Automation client credentials not found.\n'
            'Set TOSHI_CLIENT_ID and TOSHI_CLIENT_SECRET in .env, or run cognito_setup.py first.'
        )

    token_url = f'https://{domain}/oauth2/token'
    scopes = 'toshi/read toshi/write'

    resp = http_post_form(
        token_url,
        {
            'grant_type': 'client_credentials',
            'scope': scopes,
        },
        auth=(client_id, client_secret),
    )

    if 'access_token' not in resp:
        raise click.ClickException(f'Token error: {resp}')

    return resp['access_token']


# ---------------------------------------------------------------------------
# AWS Credentials flow (Cognito Identity Pool → STS)
# ---------------------------------------------------------------------------

def get_aws_credentials(config, access_token, profile='toshi'):
    """Exchange Cognito token for AWS STS credentials via Identity Pool."""
    region = config['region']
    identity_pool_id = config.get('identity_pool_id')

    if not identity_pool_id:
        raise click.ClickException(
            'Identity Pool ID not found in config.\n'
            'Run: python auth/cognito_setup.py'
        )

    cognito_identity = boto3.client('cognito-identity', region_name=region)

    click.echo(f'Getting Identity ID from pool: {identity_pool_id} ...')
    resp = cognito_identity.get_id(
        IdentityPoolId=identity_pool_id,
        Logins={
            f'cognito-idp.{region}.amazonaws.com/{config["user_pool_id"]}': access_token,
        },
    )
    identity_id = resp['IdentityId']
    click.echo(f'  Identity ID: {identity_id}')

    click.echo('Getting temporary AWS credentials ...')
    resp = cognito_identity.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={
            f'cognito-idp.{region}.amazonaws.com/{config["user_pool_id"]}': access_token,
        },
    )

    creds = resp['Credentials']
    click.echo(f'  AccessKeyId: {creds["AccessKeyId"]}')
    click.echo(f'  Expires: {datetime.fromtimestamp(creds["Expiration"] / 1000, tz=timezone.utc).isoformat()}')

    aws_credentials_path = Path.home() / '.aws' / 'credentials'
    aws_credentials_path.parent.mkdir(parents=True, exist_ok=True)

    config_content = ''
    if aws_credentials_path.exists():
        with open(aws_credentials_path) as f:
            config_content = f.read()

    import configparser
    parser = configparser.ConfigParser()
    parser.read_string(config_content)

    if profile not in parser.sections():
        parser.add_section(profile)
    parser.set(profile, 'aws_access_key_id', creds['AccessKeyId'])
    parser.set(profile, 'aws_secret_access_key', creds['SecretKey'])
    parser.set(profile, 'aws_session_token', creds['SessionToken'])
    parser.set(profile, 'region', region)

    with open(aws_credentials_path, 'w') as f:
        parser.write(f)

    aws_credentials_path.chmod(0o600)

    return profile


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """Toshi API auth helper — manage JWT tokens for nshm-toshi-api."""


@cli.command()
def login():
    """Login with email and password (works from SSH terminals and local machines)."""
    config = load_auth_config()
    token_resp = password_flow_login(config)

    creds = load_credentials()
    creds['access_token'] = token_resp['access_token']
    creds['id_token'] = token_resp.get('id_token', '')
    creds['refresh_token'] = token_resp.get('refresh_token', '')
    creds['token_type'] = token_resp.get('token_type', 'Bearer')
    creds['expires_at'] = time.time() + token_resp.get('expires_in', 3600)
    save_credentials(creds)

    payload = decode_jwt_payload(token_resp['access_token'])
    click.echo(f'\nLogged in as: {payload.get("username") or payload.get("sub", "unknown")}')
    click.echo(f'Scopes: {payload.get("scope", "none")}')
    exp = payload.get('exp', 0)
    click.echo(f'Expires: {datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()}')
    click.echo(f'\nToken saved to: {CREDENTIALS_PATH}')


@cli.command()
@click.option('--raw', is_flag=True, help='Print just the raw token string')
def token(raw):
    """Print current Bearer token, auto-refreshing if expired."""
    config = load_auth_config()
    creds = load_credentials()

    access_token = creds.get('access_token', '')
    refresh_tok = creds.get('refresh_token', '')

    if not access_token:
        raise click.ClickException('Not logged in. Run: python toshi_auth.py login')

    if is_token_expired(access_token):
        if not refresh_tok:
            raise click.ClickException('Token expired and no refresh token. Run: python toshi_auth.py login')
        click.echo('Token expired, refreshing...', err=True)
        try:
            token_resp = refresh_token(config, refresh_tok)
            access_token = token_resp['access_token']
            creds['access_token'] = access_token
            creds['expires_at'] = time.time() + token_resp.get('expires_in', 3600)
            if 'refresh_token' in token_resp:
                creds['refresh_token'] = token_resp['refresh_token']
            save_credentials(creds)
        except Exception as e:
            raise click.ClickException(f'Token refresh failed: {e}. Run: python toshi_auth.py login')

    if raw:
        click.echo(access_token)
    else:
        click.echo(f'Bearer {access_token}')


@cli.command()
def whoami():
    """Decode and display JWT claims (user, scopes, expiry)."""
    creds = load_credentials()
    access_token = creds.get('access_token', '')

    if not access_token:
        raise click.ClickException('Not logged in. Run: python toshi_auth.py login')

    payload = decode_jwt_payload(access_token)
    expired = is_token_expired(access_token, buffer_seconds=0)

    click.echo('\n=== Token Info ===')
    click.echo(f'Subject (sub):  {payload.get("sub", "n/a")}')
    click.echo(f'Username:       {payload.get("username") or payload.get("cognito:username", "n/a")}')
    click.echo(f'Issuer (iss):   {payload.get("iss", "n/a")}')
    click.echo(f'Audience (aud): {payload.get("aud") or payload.get("client_id", "n/a")}')
    click.echo(f'Scopes:         {payload.get("scope", "none")}')
    click.echo(f'Token use:      {payload.get("token_use", "n/a")}')

    exp = payload.get('exp', 0)
    exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
    status = 'EXPIRED' if expired else 'valid'
    click.echo(f'Expires:        {exp_dt.isoformat()} [{status}]')

    iat = payload.get('iat', 0)
    if iat:
        iat_dt = datetime.fromtimestamp(iat, tz=timezone.utc)
        click.echo(f'Issued at:      {iat_dt.isoformat()}')

    click.echo(f'\nGroups:         {payload.get("cognito:groups", [])}')


@cli.command('m2m-token')
@click.option('--raw', is_flag=True, help='Print just the raw token string (no "Bearer " prefix)')
def m2m_token(raw):
    """Obtain M2M (machine-to-machine) token via Client Credentials for Runzi/automation."""
    config = load_auth_config()
    access_token = client_credentials_flow(config)

    payload = decode_jwt_payload(access_token)
    exp = payload.get('exp', 0)
    exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)

    click.echo(f'M2M token obtained. Expires: {exp_dt.isoformat()}', err=True)
    click.echo(f'Scopes: {payload.get("scope", "none")}', err=True)

    if raw:
        click.echo(access_token)
    else:
        click.echo(f'Bearer {access_token}')


@cli.command('aws-creds')
@click.option('--profile', default='toshi', help='AWS credentials profile name', show_default=True)
def aws_creds(profile):
    """Exchange Cognito token for AWS STS credentials and write to ~/.aws/credentials."""
    config = load_auth_config()
    creds = load_credentials()

    access_token = creds.get('access_token', '')
    if not access_token:
        raise click.ClickException('Not logged in. Run: python toshi_auth.py login')

    if is_token_expired(access_token, buffer_seconds=300):
        refresh_tok = creds.get('refresh_token', '')
        if not refresh_tok:
            raise click.ClickException('Token expired and no refresh token. Run: python toshi_auth.py login')
        click.echo('Token expired, refreshing...', err=True)
        try:
            token_resp = refresh_token(config, refresh_tok)
            access_token = token_resp['access_token']
            creds['access_token'] = access_token
            creds['expires_at'] = time.time() + token_resp.get('expires_in', 3600)
            if 'refresh_token' in token_resp:
                creds['refresh_token'] = token_resp['refresh_token']
            save_credentials(creds)
        except Exception as e:
            raise click.ClickException(f'Token refresh failed: {e}. Run: python toshi_auth.py login')

    result_profile = get_aws_credentials(config, access_token, profile)

    click.echo(f'\nAWS credentials saved to profile [{result_profile}] in ~/.aws/credentials')
    click.echo(f'Use with: export AWS_PROFILE={result_profile}')
    click.echo(f'Or: aws --profile {result_profile} s3 ls')


if __name__ == '__main__':
    cli()
