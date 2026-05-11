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

import flask
from graphql import OperationType
from graphql import parse as gql_parse
from graphql.language.ast import OperationDefinitionNode
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


def _is_mutation(query: str, operation_name: str | None = None) -> bool:
    """
    Return True if the selected GraphQL operation is a mutation.

    Uses the graphql-core AST parser so it correctly handles multi-operation
    documents, operationName selection, fragments, comments, and arbitrary
    whitespace — all the things a regex cannot.

    Fails closed: returns True (i.e. treats as mutation) if the document
    cannot be parsed, so a malformed body never bypasses write-scope enforcement.
    """
    if not query:
        return False
    try:
        doc = gql_parse(query)
    except Exception:
        return True  # fail closed
    ops: list[OperationDefinitionNode] = [d for d in doc.definitions if isinstance(d, OperationDefinitionNode)]
    if operation_name:
        ops = [o for o in ops if o.name and o.name.value == operation_name]
    return any(o.operation == OperationType.MUTATION for o in ops)


def _extract_graphql_args(request_body_bytes: bytes) -> tuple[str, str | None]:
    """
    Extract (query, operationName) from a GraphQL HTTP request body.
    Returns ('', None) if the body cannot be parsed.
    """
    if not request_body_bytes:
        return '', None
    content_type = flask.request.content_type or ''
    if 'application/json' in content_type:
        try:
            body = json.loads(request_body_bytes)
            return body.get('query', ''), body.get('operationName')
        except (json.JSONDecodeError, TypeError):
            return '', None
    if 'application/graphql' in content_type:
        try:
            return request_body_bytes.decode('utf-8', errors='replace'), None
        except Exception:
            return '', None
    return '', None


# ---------------------------------------------------------------------------
# Header extraction
# ---------------------------------------------------------------------------


def _get_auth_context():
    """
    Extract auth context set by the Lambda Authorizer.

    serverless-wsgi exposes requestContext.authorizer as request.environ['serverless.authorizer'].
    Fall back to X-Auth-* headers for local/e2e testing without API Gateway.
    """
    authorizer_ctx = flask.request.environ.get('serverless.authorizer') or {}

    user_id = authorizer_ctx.get('userId') or flask.request.headers.get('X-Auth-Userid') or 'anonymous'
    scopes_str = authorizer_ctx.get('scopes') or flask.request.headers.get('X-Auth-Scopes') or ''
    auth_method = authorizer_ctx.get('authMethod') or flask.request.headers.get('X-Auth-Method') or 'none'
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
        flask.g.current_user = {'userId': 'local-dev', 'scopes': {SCOPE_READ, SCOPE_WRITE}, 'authMethod': 'bypass'}
        return None

    # Only enforce on /graphql path
    if not flask.request.path.startswith('/graphql'):
        return None

    # OPTIONS preflight — always allow (CORS)
    if flask.request.method == 'OPTIONS':
        return None

    # Log auth-related headers to verify authorizer context injection
    auth_headers = {k: v for k, v in flask.request.headers if 'amzn' in k.lower() or 'auth' in k.lower()}
    logger.info('[middleware] auth-related headers: %s', auth_headers)

    user_id, scopes, auth_method = _get_auth_context()

    # Attach to Flask g for use in resolvers / logging
    flask.g.current_user = {'userId': user_id, 'scopes': scopes, 'authMethod': auth_method}

    logger.info('[middleware] userId=%s scopes=%s method=%s', user_id, scopes, auth_method)

    # Read-only check — every authenticated user needs at least toshi/read
    if SCOPE_READ not in scopes:
        logger.warning('Access denied for %s: missing %s', user_id, SCOPE_READ)
        raise Forbidden(f'Missing required scope: {SCOPE_READ}')

    # Mutation check — mutations need toshi/write
    if flask.request.method == 'POST':
        query, operation_name = _extract_graphql_args(flask.request.get_data())
        if _is_mutation(query, operation_name) and SCOPE_WRITE not in scopes:
            logger.warning('Mutation blocked for %s: missing %s', user_id, SCOPE_WRITE)
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
    logger.info('Auth middleware registered' + (' [BYPASS: TESTING or SLS_OFFLINE]' if TESTING or IS_OFFLINE else ''))
