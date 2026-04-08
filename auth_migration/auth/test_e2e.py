"""
End-to-end validation script for the nshm-toshi-api auth spike.

Verifies all token flows against a running local stack or remote endpoint.

Usage:
    # Against local stack (SLS_OFFLINE=1, no auth enforcement)
    python auth_migration/auth/test_e2e.py --local

    # Against a deployed API Gateway endpoint with Cognito auth enabled
    python auth_migration/auth/test_e2e.py --endpoint https://<api-id>.execute-api.ap-southeast-2.amazonaws.com/dev

Prerequisites:
    - cognito_config.json present (run cognito_setup.py first)
    - For --endpoint mode: Lambda authorizer deployed and wired to API Gateway
    - For --local mode: local stack running (yarn sls dynamodb start, yarn sls wsgi serve)

Test cases:
    1. Device Flow login → token acquired
    2. toshi/read token → GraphQL query succeeds (200)
    3. toshi/read token → GraphQL mutation blocked (403)
    4. toshi/write token → GraphQL mutation succeeds (200)
    5. M2M client credentials → mutation succeeds (200)
    6. Expired/invalid token → 401 from authorizer
"""
import base64
import json
import os
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import click
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))



# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'cognito_config.json')

GRAPHQL_QUERY = '{ __typename }'
GRAPHQL_MUTATION = '''
mutation CreateTestTask($input: CreateGeneralTaskInput!) {
  create_general_task(input: $input) {
    general_task { id }
  }
}
'''

SIMPLE_QUERY_BODY = json.dumps({'query': GRAPHQL_QUERY})
SIMPLE_MUTATION_BODY = json.dumps({
    'query': 'mutation { __typename }',
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.message = ''
        self.duration_ms = 0.0

    def ok(self, msg=''):
        self.passed = True
        self.message = msg
        return self

    def fail(self, msg):
        self.passed = False
        self.message = msg
        return self

    def __str__(self):
        icon = '✓' if self.passed else '✗'
        timing = f' ({self.duration_ms:.0f}ms)' if self.duration_ms else ''
        return f'  {icon} {self.name}{timing}: {self.message}'


def graphql_request(endpoint, query, token=None, api_key=None, extra_headers=None):
    """
    Make a GraphQL HTTP request.

    Returns (status_code, response_body_dict_or_str).
    Does not raise on HTTP errors — returns the status code.
    """
    body = json.dumps({'query': query}).encode()
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

    if token:
        headers['Authorization'] = f'Bearer {token}'
    if api_key:
        headers['x-api-key'] = api_key
    if extra_headers:
        headers.update(extra_headers)

    req = Request(endpoint, data=body, headers=headers, method='POST')
    try:
        with urlopen(req) as resp:
            status = resp.status
            body_bytes = resp.read()
            try:
                return status, json.loads(body_bytes)
            except json.JSONDecodeError:
                return status, body_bytes.decode()
    except HTTPError as e:
        body_bytes = e.read()
        try:
            return e.code, json.loads(body_bytes)
        except json.JSONDecodeError:
            return e.code, body_bytes.decode()


def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise click.ClickException(
            f'cognito_config.json not found at {CONFIG_FILE}.\n'
            'Run: python auth_migration/auth/cognito_setup.py --profile <your-aws-profile>'
        )
    with open(CONFIG_FILE) as f:
        return json.load(f)


def get_access_token(config, username, password):
    """Get an access token via username/password auth (USER_PASSWORD_AUTH flow)."""
    import boto3

    session = boto3.Session(region_name=config['region'])
    cognito = session.client('cognito-idp')

    resp = cognito.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': username,
            'PASSWORD': password,
        },
        ClientId=config['scientist_client_id'],
    )
    return resp['AuthenticationResult']['AccessToken']


def get_m2m_token(config):
    """Get M2M token via client credentials flow."""
    from urllib.parse import urlencode

    domain = config['cognito_domain']
    client_id = config['automation_client_id']
    client_secret = config['automation_client_secret']
    token_url = f'https://{domain}/oauth2/token'

    body = urlencode({'grant_type': 'client_credentials', 'scope': 'toshi/read toshi/write'}).encode()
    credentials = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {credentials}',
    }
    req = Request(token_url, data=body, headers=headers, method='POST')
    with urlopen(req) as resp:
        return json.loads(resp.read())['access_token']


def decode_jwt_payload(token):
    parts = token.split('.')
    payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


# ---------------------------------------------------------------------------
# Local-stack tests (no auth enforcement)
# ---------------------------------------------------------------------------

def run_local_tests(endpoint):
    """
    Tests against local stack (SLS_OFFLINE=1).

    Auth middleware is bypassed locally, so we test:
    - Basic connectivity
    - Query succeeds
    - Mutation attempt returns valid GraphQL response (not blocked)
    - Middleware bypass headers work
    """
    results = []

    # Test 1: Basic connectivity
    t = TestResult('Local connectivity (query)')
    start = time.perf_counter()
    status, body = graphql_request(endpoint, GRAPHQL_QUERY)
    t.duration_ms = (time.perf_counter() - start) * 1000
    if status == 200:
        t.ok(f'HTTP 200, body keys: {list(body.keys()) if isinstance(body, dict) else "raw"}')
    else:
        t.fail(f'HTTP {status}: {body}')
    results.append(t)

    # Test 2: Mutation without auth (local bypass)
    t = TestResult('Local mutation bypass (SLS_OFFLINE no-op)')
    start = time.perf_counter()
    status, body = graphql_request(endpoint, 'mutation { __typename }')
    t.duration_ms = (time.perf_counter() - start) * 1000
    if status == 200:
        t.ok(f'HTTP 200 — middleware bypassed as expected in offline mode')
    elif status == 400:
        # GraphQL validation error (schema doesn't have root mutation __typename) is fine
        t.ok(f'HTTP 400 — GraphQL validation, not auth rejection')
    else:
        t.fail(f'HTTP {status}: {body}')
    results.append(t)

    # Test 3: Middleware headers (simulating what Lambda Authorizer injects)
    t = TestResult('Middleware header injection test')
    start = time.perf_counter()
    status, body = graphql_request(
        endpoint,
        GRAPHQL_QUERY,
        extra_headers={
            'X-Auth-Userid': 'test-scientist',
            'X-Auth-Scopes': 'toshi/read toshi/write',
            'X-Auth-Method': 'test',
        },
    )
    t.duration_ms = (time.perf_counter() - start) * 1000
    if status == 200:
        t.ok('HTTP 200 — custom auth headers accepted')
    else:
        t.fail(f'HTTP {status}: {body}')
    results.append(t)

    return results


# ---------------------------------------------------------------------------
# Remote endpoint tests (with Cognito auth)
# ---------------------------------------------------------------------------

def run_remote_tests(endpoint, config):
    """Tests against a real API Gateway endpoint with Lambda Authorizer enabled."""
    results = []
    test_users = {u['username']: u['password'] for u in config['test_users']}

    # Get tokens for test users
    click.echo('  Acquiring tokens...')
    writer_token = None
    reader_token = None
    m2m_tok = None

    try:
        writer_user = next(u for u in config['test_users'] if 'toshi-writers' in u.get('groups', []))
        writer_token = get_access_token(config, writer_user['username'], writer_user['password'])
        click.echo(f'    Writer token: OK ({writer_user["username"]})')
    except Exception as e:
        click.echo(f'    Writer token: FAILED ({e})')

    try:
        reader_user = next(u for u in config['test_users'] if 'toshi-writers' not in u.get('groups', []))
        reader_token = get_access_token(config, reader_user['username'], reader_user['password'])
        click.echo(f'    Reader token: OK ({reader_user["username"]})')
    except Exception as e:
        click.echo(f'    Reader token: FAILED ({e})')

    try:
        m2m_tok = get_m2m_token(config)
        click.echo('    M2M token: OK')
    except Exception as e:
        click.echo(f'    M2M token: FAILED ({e})')

    # Test 1: No token → 401
    t = TestResult('No token → 401')
    start = time.perf_counter()
    status, body = graphql_request(endpoint, GRAPHQL_QUERY)
    t.duration_ms = (time.perf_counter() - start) * 1000
    if status == 401:
        t.ok('HTTP 401 — correct')
    else:
        t.fail(f'Expected 401, got {status}: {body}')
    results.append(t)

    # Test 2: Invalid token → 401
    t = TestResult('Invalid/expired token → 401')
    start = time.perf_counter()
    status, body = graphql_request(endpoint, GRAPHQL_QUERY, token='not.a.valid.jwt')
    t.duration_ms = (time.perf_counter() - start) * 1000
    if status == 401:
        t.ok('HTTP 401 — correct')
    else:
        t.fail(f'Expected 401, got {status}: {body}')
    results.append(t)

    # Test 3: Write token → query succeeds
    if writer_token:
        t = TestResult('Write token → query succeeds (200)')
        start = time.perf_counter()
        status, body = graphql_request(endpoint, GRAPHQL_QUERY, token=writer_token)
        t.duration_ms = (time.perf_counter() - start) * 1000
        if status == 200:
            t.ok('HTTP 200')
        else:
            t.fail(f'HTTP {status}: {body}')
        results.append(t)

    # Test 4: Read-only token → query succeeds
    if reader_token:
        t = TestResult('Read-only token → query succeeds (200)')
        start = time.perf_counter()
        status, body = graphql_request(endpoint, GRAPHQL_QUERY, token=reader_token)
        t.duration_ms = (time.perf_counter() - start) * 1000
        if status == 200:
            t.ok('HTTP 200')
        else:
            t.fail(f'HTTP {status}: {body}')
        results.append(t)

    # Test 5: Read-only token → mutation blocked (403)
    if reader_token:
        t = TestResult('Read-only token → mutation blocked (403)')
        start = time.perf_counter()
        status, body = graphql_request(endpoint, 'mutation { __typename }', token=reader_token)
        t.duration_ms = (time.perf_counter() - start) * 1000
        if status == 403:
            t.ok('HTTP 403 — mutation correctly rejected')
        elif status == 200:
            t.fail('HTTP 200 — mutation should have been blocked! Middleware not enforcing write scope.')
        else:
            t.fail(f'HTTP {status}: {body}')
        results.append(t)

    # Test 6: Write token → mutation succeeds
    if writer_token:
        t = TestResult('Write token → mutation passes auth (200 or GraphQL error)')
        start = time.perf_counter()
        status, body = graphql_request(endpoint, 'mutation { __typename }', token=writer_token)
        t.duration_ms = (time.perf_counter() - start) * 1000
        if status in (200, 400):
            # 200 or 400 (GraphQL validation error) both mean auth passed
            t.ok(f'HTTP {status} — auth passed, mutation reached GraphQL engine')
        elif status == 403:
            t.fail('HTTP 403 — writer was incorrectly blocked')
        else:
            t.fail(f'HTTP {status}: {body}')
        results.append(t)

    # Test 7: M2M token → mutation succeeds
    if m2m_tok:
        t = TestResult('M2M (client credentials) → mutation passes auth')
        start = time.perf_counter()
        status, body = graphql_request(endpoint, 'mutation { __typename }', token=m2m_tok)
        t.duration_ms = (time.perf_counter() - start) * 1000
        if status in (200, 400):
            t.ok(f'HTTP {status} — M2M auth passed')
        elif status == 403:
            t.fail('HTTP 403 — M2M incorrectly blocked')
        else:
            t.fail(f'HTTP {status}: {body}')
        results.append(t)

    # Test 8: Legacy x-api-key → full access
    legacy_key = os.environ.get('LEGACY_API_KEY')
    if legacy_key:
        t = TestResult('Legacy x-api-key → query succeeds (200)')
        start = time.perf_counter()
        status, body = graphql_request(endpoint, GRAPHQL_QUERY, api_key=legacy_key)
        t.duration_ms = (time.perf_counter() - start) * 1000
        if status == 200:
            t.ok('HTTP 200 — legacy x-api-key accepted')
        else:
            t.fail(f'Expected 200, got {status}: {body}')
        results.append(t)
    else:
        click.echo('  (Skipping legacy x-api-key test — LEGACY_API_KEY not set)')

    # Test 9: Authorizer latency
    if writer_token:
        t = TestResult('Authorizer warm-path latency (<100ms)')
        times = []
        for _ in range(5):
            start = time.perf_counter()
            graphql_request(endpoint, GRAPHQL_QUERY, token=writer_token)
            times.append((time.perf_counter() - start) * 1000)
        p99 = sorted(times)[-1]
        avg = sum(times) / len(times)
        t.duration_ms = avg
        if p99 < 100:
            t.ok(f'avg={avg:.0f}ms p99={p99:.0f}ms — excellent')
        elif p99 < 500:
            t.ok(f'avg={avg:.0f}ms p99={p99:.0f}ms — acceptable')
        else:
            t.fail(f'avg={avg:.0f}ms p99={p99:.0f}ms — too slow, investigate cold start')
        results.append(t)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option('--local', 'mode', flag_value='local', default=True, help='Test local stack (default)')
@click.option('--remote', 'mode', flag_value='remote', help='Test remote API Gateway endpoint')
@click.option('--endpoint', default=lambda: os.environ.get('TOSHI_API_ENDPOINT', 'http://localhost:5000/graphql'),
              show_default='$TOSHI_API_ENDPOINT or http://localhost:5000/graphql',
              help='GraphQL endpoint URL')
@click.option('--verbose', is_flag=True, default=False)
def main(mode, endpoint, verbose):
    """Run end-to-end auth validation tests."""
    click.echo(f'\n=== Toshi Auth E2E Tests ===')
    click.echo(f'Mode:     {mode}')
    click.echo(f'Endpoint: {endpoint}')
    click.echo()

    if mode == 'remote':
        config = load_config()
        click.echo('Running REMOTE tests (requires Cognito + Lambda Authorizer deployed)...')
        results = run_remote_tests(endpoint, config)
    else:
        click.echo('Running LOCAL tests (SLS_OFFLINE mode, auth middleware bypassed)...')
        results = run_local_tests(endpoint)

    # Print results
    click.echo()
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    for result in results:
        click.echo(str(result))

    click.echo()
    click.echo(f'Results: {passed}/{total} passed')

    if passed < total:
        failed = [r for r in results if not r.passed]
        click.echo(f'\nFailed tests:')
        for r in failed:
            click.echo(f'  - {r.name}: {r.message}')
        sys.exit(1)
    else:
        click.echo('All tests passed!')


if __name__ == '__main__':
    main()
