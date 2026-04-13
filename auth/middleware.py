"""
Flask Middleware prototype for nshm-toshi-api JWT auth enforcement.

Reads auth context injected by the Lambda Authorizer via API Gateway proxy headers,
then enforces scope-based access control:
  - GraphQL queries  → require toshi/read
  - GraphQL mutations → require toshi/write

**No-op** when TESTING=1 or SLS_OFFLINE=1 — local dev and tests are unaffected.

Integration in graphql_api/api.py:
    from auth.middleware import register_auth_middleware
    register_auth_middleware(app)

Or inline:
    from auth import middleware as toshi_middleware
    app.before_request(toshi_middleware.check_auth)
"""
import json
import logging
import re

from flask import g, request
from werkzeug.exceptions import Forbidden

from graphql_api.config import IS_OFFLINE, TESTING

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scope constants
# ---------------------------------------------------------------------------

SCOPE_READ = 'toshi/read'
SCOPE_WRITE = 'toshi/write'

# ---------------------------------------------------------------------------
# GraphQL operation detection
# ---------------------------------------------------------------------------

_MUTATION_RE = re.compile(
    r'^\s*mutation\b',  # explicit "mutation" keyword
    re.IGNORECASE | re.MULTILINE,
)


def _is_mutation(request_body_bytes):
    """
    Return True if the GraphQL request body contains a mutation.

    Handles both JSON-encoded bodies (standard) and form data.
    Does NOT parse the full GraphQL AST — regex on the 'query' field is sufficient
    for operation-level scope enforcement.
    """
    if not request_body_bytes:
        return False

    content_type = request.content_type or ''

    if 'application/json' in content_type:
        try:
            body = json.loads(request_body_bytes)
            query_str = body.get('query', '')
            return bool(_MUTATION_RE.search(query_str))
        except (json.JSONDecodeError, TypeError):
            return False

    if 'application/graphql' in content_type:
        try:
            return bool(_MUTATION_RE.search(request_body_bytes.decode('utf-8', errors='replace')))
        except Exception:
            return False

    return False


# ---------------------------------------------------------------------------
# Header extraction
# ---------------------------------------------------------------------------

def _get_auth_context():
    """
    Extract auth context set by the Lambda Authorizer.

    serverless-wsgi exposes requestContext.authorizer as request.environ['serverless.authorizer'].
    Fall back to X-Auth-* headers for local/e2e testing without API Gateway.
    """
    authorizer_ctx = request.environ.get('serverless.authorizer') or {}

    user_id = (
        authorizer_ctx.get('userId')
        or request.headers.get('X-Auth-Userid')
        or 'anonymous'
    )
    scopes_str = (
        authorizer_ctx.get('scopes')
        or request.headers.get('X-Auth-Scopes')
        or ''
    )
    auth_method = (
        authorizer_ctx.get('authMethod')
        or request.headers.get('X-Auth-Method')
        or 'none'
    )
    scopes = set(scopes_str.split()) if scopes_str else set()
    return user_id, scopes, auth_method


# ---------------------------------------------------------------------------
# Main middleware function
# ---------------------------------------------------------------------------

def check_auth():
    """
    before_request hook: enforce scope-based access on /graphql.

    No-op when TESTING=1 or SLS_OFFLINE=1.
    """
    # Skip for local dev and tests
    if TESTING or IS_OFFLINE:
        g.current_user = {'userId': 'local-dev', 'scopes': {SCOPE_READ, SCOPE_WRITE}, 'authMethod': 'bypass'}
        return None

    # Only enforce on /graphql path
    if not request.path.startswith('/graphql'):
        return None

    # OPTIONS preflight — always allow (CORS)
    if request.method == 'OPTIONS':
        return None

    # DEBUG: log all incoming headers so we can verify authorizer context injection
    auth_headers = {k: v for k, v in request.headers if 'amzn' in k.lower() or 'auth' in k.lower()}
    logger.info(f'[middleware] auth-related headers: {auth_headers}')

    user_id, scopes, auth_method = _get_auth_context()

    # Attach to Flask g for use in resolvers / logging
    g.current_user = {'userId': user_id, 'scopes': scopes, 'authMethod': auth_method}

    logger.info(f'[middleware] userId={user_id} scopes={scopes} method={auth_method}')

    # Read-only check — every authenticated user needs at least toshi/read
    if SCOPE_READ not in scopes:
        logger.warning(f'Access denied for {user_id}: missing {SCOPE_READ}')
        raise Forbidden(f'Missing required scope: {SCOPE_READ}')

    # Mutation check — mutations need toshi/write
    if request.method == 'POST':
        body = request.get_data()
        if _is_mutation(body) and SCOPE_WRITE not in scopes:
            logger.warning(f'Mutation blocked for {user_id}: missing {SCOPE_WRITE}')
            raise Forbidden(f'GraphQL mutations require scope: {SCOPE_WRITE}')

    return None


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_auth_middleware(app):
    """
    Register the auth middleware on a Flask app instance.

    Call this from graphql_api/api.py after creating the Flask app:

        from auth.middleware import register_auth_middleware
        register_auth_middleware(app)
    """
    app.before_request(check_auth)
    logger.info(
        'Auth middleware registered'
        + (' [BYPASS: TESTING or SLS_OFFLINE]' if TESTING or IS_OFFLINE else '')
    )
