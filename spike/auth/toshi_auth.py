"""
Toshi Auth CLI — scientist and automation token management.

Usage:
    python toshi_auth.py login         # Device flow: print URL+code, poll, save token
    python toshi_auth.py token         # Print current Bearer token (auto-refresh)
    python toshi_auth.py whoami        # Decode and display JWT claims
    python toshi_auth.py m2m-token     # Client credentials flow for automation/Runzi

Token storage: ~/.toshi/credentials (JSON)

Configuration (reads spike/auth/cognito_config.json OR env vars):
    TOSHI_COGNITO_CONFIG   path to cognito_config.json (default: spike/auth/cognito_config.json)
    TOSHI_CLIENT_ID        override automation client_id (for m2m-token)
    TOSHI_CLIENT_SECRET    override automation client_secret (for m2m-token)
"""
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import click


CREDENTIALS_PATH = Path.home() / '.toshi' / 'credentials'
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'cognito_config.json')
DEVICE_POLL_INTERVAL = 5  # seconds
DEVICE_TIMEOUT = 300  # 5 minutes


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_cognito_config():
    config_path = os.environ.get('TOSHI_COGNITO_CONFIG', DEFAULT_CONFIG_PATH)
    if not os.path.exists(config_path):
        raise click.ClickException(
            f'Cognito config not found at {config_path}.\n'
            'Run: python spike/auth/cognito_setup.py --profile <your-aws-profile>'
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
    CREDENTIALS_PATH.chmod(0o700)
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
# Device Authorization Grant flow (RFC 8628)
# ---------------------------------------------------------------------------

def device_flow_login(config):
    """Initiate device authorization and poll for token."""
    domain = config['cognito_domain']
    client_id = config['scientist_client_id']
    scopes = 'openid email profile toshi/read toshi/write'

    # Step 1: Request device code
    device_auth_url = f'https://{domain}/oauth2/device_authorization'
    try:
        resp = http_post_form(
            device_auth_url,
            {
                'client_id': client_id,
                'scope': scopes,
            },
        )
    except Exception as e:
        raise click.ClickException(
            f'Device authorization request failed: {e}\n'
            'Note: Cognito requires HTTPS hosted domain. Ensure the pool domain is active.'
        )

    device_code = resp['device_code']
    user_code = resp['user_code']
    verification_uri = resp.get('verification_uri_complete', resp.get('verification_uri'))
    interval = resp.get('interval', DEVICE_POLL_INTERVAL)
    expires_in = resp.get('expires_in', DEVICE_TIMEOUT)

    click.echo('\n=== Toshi Login ===')
    click.echo(f'Open this URL in your browser:')
    click.echo(f'\n  {verification_uri}\n')
    click.echo(f'Or go to {resp.get("verification_uri")} and enter code: {user_code}')
    click.echo(f'\nWaiting for authentication (expires in {expires_in}s)...')

    token_url = f'https://{domain}/oauth2/token'
    deadline = time.time() + expires_in

    while time.time() < deadline:
        time.sleep(interval)
        try:
            token_resp = http_post_form(
                token_url,
                {
                    'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                    'client_id': client_id,
                    'device_code': device_code,
                },
            )
            if 'access_token' in token_resp:
                return token_resp
            error = token_resp.get('error', '')
            if error == 'authorization_pending':
                click.echo('.', nl=False)
                continue
            elif error == 'slow_down':
                interval += 5
                continue
            else:
                raise click.ClickException(f'Token error: {error} — {token_resp.get("error_description", "")}')
        except Exception as e:
            if 'authorization_pending' in str(e):
                click.echo('.', nl=False)
                continue
            raise

    raise click.ClickException('Device flow timed out. Please try again.')


def refresh_token(config, refresh_tok):
    """Use refresh token to get new access token."""
    domain = config['cognito_domain']
    client_id = config['scientist_client_id']
    token_url = f'https://{domain}/oauth2/token'

    return http_post_form(
        token_url,
        {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'refresh_token': refresh_tok,
        },
    )


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
            'Set TOSHI_CLIENT_ID and TOSHI_CLIENT_SECRET, or run cognito_setup.py first.'
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
# CLI commands
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """Toshi API auth helper — manage JWT tokens for nshm-toshi-api."""


@cli.command()
def login():
    """Interactive login via Device Authorization Grant (works from SSH terminals)."""
    config = load_cognito_config()
    token_resp = device_flow_login(config)

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
    config = load_cognito_config()
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
    config = load_cognito_config()
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


if __name__ == '__main__':
    cli()
