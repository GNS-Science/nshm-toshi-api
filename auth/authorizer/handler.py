"""
Lambda Authorizer for nshm-toshi-api.

Validates JWTs issued by AWS Cognito and returns an IAM policy.
Also accepts legacy x-api-key for backward compatibility during transition.

Environment variables (required):
    COGNITO_USER_POOL_ID   e.g. ap-southeast-2_Abc123
    COGNITO_REGION         e.g. ap-southeast-2
    COGNITO_CLIENT_ID      expected audience — comma-separated list of allowed client IDs

Environment variables (optional):
    LEGACY_API_KEY         if set, this x-api-key value is also accepted (backward compat)

Deployment:
    See auth/README.md for Lambda deployment instructions.
    Add to serverless.yml functions section:

        jwtAuthorizer:
          handler: auth/authorizer/handler.handler
          environment:
            COGNITO_USER_POOL_ID: ${env:COGNITO_USER_POOL_ID}
            COGNITO_REGION: ${self:provider.region}
            COGNITO_CLIENT_ID: ${env:COGNITO_CLIENT_ID}
            LEGACY_API_KEY: ${env:LEGACY_API_KEY, ''}

    And on the graphql POST/GET events:
        authorizer:
          name: jwtAuthorizer
          resultTtlInSeconds: 0
          identitySource: method.request.header.Authorization
          type: request
          # Note: REQUEST type passes all headers to Lambda. The handler also checks
          # x-api-key header, but API Gateway only gates on Authorization being present.
          # Legacy clients sending only x-api-key must use: Authorization: x-api-key <key>
"""

import logging
import os
import time
from typing import Any

import jwt  # PyJWT
from jwt import PyJWKClient
from jwt.types import Options

logging.getLogger().setLevel(logging.INFO)  # ensure Lambda root logger captures INFO
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JWKS cache — reused across warm Lambda invocations
# ---------------------------------------------------------------------------

_jwks_client = None


def get_jwks_client() -> PyJWKClient:
    """Return a cached PyJWKClient for the Cognito JWKS endpoint."""
    global _jwks_client
    if _jwks_client is None:
        pool_id = os.environ['COGNITO_USER_POOL_ID']
        region = os.environ['COGNITO_REGION']
        jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json'
        logger.info('Initialising JWKS client: %s', jwks_url)
        _jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
    return _jwks_client


# ---------------------------------------------------------------------------
# IAM policy builder
# ---------------------------------------------------------------------------


def build_policy(principal_id: str, effect: str, resource: str, context: dict[str, Any] | None = None) -> dict:
    """Build an IAM policy document for the Lambda authorizer response."""
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource,
                }
            ],
        },
    }
    if context:
        policy['context'] = context
    return policy


# ---------------------------------------------------------------------------
# Token validation
# ---------------------------------------------------------------------------


def validate_cognito_token(token: str) -> tuple[str, str, dict]:
    """
    Validate a Cognito JWT.

    Returns (principal_id, scopes_str, payload) on success.
    Raises jwt.exceptions.* on failure.
    """
    pool_id = os.environ['COGNITO_USER_POOL_ID']
    region = os.environ['COGNITO_REGION']
    client_id = os.environ.get('COGNITO_CLIENT_ID', '')

    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    expected_issuer = f'https://cognito-idp.{region}.amazonaws.com/{pool_id}'

    # Access tokens have audience = client_id; id tokens have audience = client_id
    decode_options: Options = {'verify_exp': True}
    algorithms = ['RS256']

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=algorithms,
        issuer=expected_issuer,
        options=decode_options,
    )

    # Only access tokens are accepted — id tokens carry no scope claims
    # and are intended for client-side identity, not API authorisation.
    token_use = payload.get('token_use', '')
    if token_use != 'access':
        raise jwt.InvalidTokenError(f'Invalid token_use: {token_use!r} — only access tokens accepted')

    # Cognito access tokens use client_id (not aud) to identify the intended audience.
    # COGNITO_CLIENT_ID may be a single value or comma-separated list (scientist + automation).
    token_client_id = payload.get('client_id', '')
    if client_id:
        allowed_ids = {c.strip() for c in client_id.split(',')}
        if token_client_id not in allowed_ids:
            raise jwt.InvalidAudienceError(
                f'client_id mismatch: expected one of {allowed_ids}, got {token_client_id}'
            )

    principal_id = payload.get('username') or payload.get('sub', 'unknown')
    scopes = payload.get('scope', '')

    # USER_PASSWORD_AUTH (boto3 InitiateAuth) issues tokens whose 'scope' claim contains
    # 'aws.cognito.signin.user.admin' rather than our custom resource-server scopes
    # (toshi/read, toshi/write). We derive the effective toshi scopes from the user's
    # Cognito group membership instead.
    if 'aws.cognito.signin.user.admin' in scopes:
        groups = payload.get('cognito:groups', [])
        toshi_scopes = []
        if 'toshi-readers' in groups or 'toshi-writers' in groups:
            toshi_scopes.append('toshi/read')
        if 'toshi-writers' in groups:
            toshi_scopes.append('toshi/write')
        scopes = ' '.join(toshi_scopes) if toshi_scopes else scopes

    return principal_id, scopes, payload


def validate_legacy_api_key(token: str) -> bool:
    """Check if token matches the legacy x-api-key value."""
    legacy_key = os.environ.get('LEGACY_API_KEY', '')
    if not legacy_key:
        return False
    return token == legacy_key


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------


def handler(event: dict, _context: object) -> dict:
    """
    Lambda authorizer handler.

    Input event (REQUEST type):
        {
            "headers": {"Authorization": "Bearer <jwt>", "x-api-key": "<key>", ...},
            "methodArn": "arn:aws:execute-api:..."
        }
    """
    method_arn = event.get('methodArn', '*')

    # REQUEST type: headers are in event['headers']
    headers = event.get('headers') or {}
    auth_header = headers.get('Authorization') or headers.get('authorization', '')
    api_key_header = headers.get('x-api-key') or headers.get('X-Api-Key', '')

    scheme = (auth_header.split(' ', 1)[0].lower()) if auth_header else '(none)'
    print(f'[jwtAuthorizer] INVOKED scheme={scheme} api_key_present={bool(api_key_header)} arn={method_arn}')
    logger.info('[jwtAuthorizer] INVOKED scheme=%s api_key_present=%s arn=%s', scheme, bool(api_key_header), method_arn)

    # Priority 1: x-api-key header (legacy clients)
    if api_key_header:
        if validate_legacy_api_key(api_key_header):
            logger.info('Authorizing via legacy x-api-key header')
            return build_policy(
                'legacy-api-key',
                'Allow',
                method_arn,
                context={'userId': 'legacy', 'scopes': 'toshi/read toshi/write', 'authMethod': 'apikey'},
            )
        else:
            logger.warning('Invalid legacy API key in x-api-key header')
            raise Exception('Unauthorized')

    if not auth_header:
        logger.warning('No authorization token provided')
        raise Exception('Unauthorized')

    # Parse Authorization header
    parts = auth_header.split(' ', 1)
    scheme = parts[0].lower() if parts else ''
    token = parts[1] if len(parts) > 1 else ''

    # Priority 2: Authorization: x-api-key <key>
    # Reached only when no bare x-api-key header was present (Priority 1 skipped).
    # Handles clients that have adopted the Authorization header but still use the legacy key
    # format, e.g. `Authorization: x-api-key <key>` or `Authorization: apikey <key>`.
    if scheme in ('x-api-key', 'apikey'):
        if validate_legacy_api_key(token):
            logger.info('Authorizing via legacy x-api-key in Authorization header')
            return build_policy(
                'legacy-api-key',
                'Allow',
                method_arn,
                context={'userId': 'legacy', 'scopes': 'toshi/read toshi/write', 'authMethod': 'apikey'},
            )
        else:
            logger.warning('Invalid legacy API key in Authorization header')
            raise Exception('Unauthorized')

    # Priority 3: JWT Bearer token
    if scheme != 'bearer':
        logger.warning('Unknown authorization scheme: %s', scheme)
        raise Exception('Unauthorized')

    if not token:
        logger.warning('Bearer token is empty')
        raise Exception('Unauthorized')

    try:
        start = time.perf_counter()
        principal_id, scopes, payload = validate_cognito_token(token)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info('JWT validated in %.1fms for principal: %s', elapsed_ms, principal_id)

        return build_policy(
            principal_id,
            'Allow',
            method_arn,
            context={
                'userId': principal_id,
                'scopes': scopes,
                'authMethod': 'jwt',
                'tokenUse': payload.get('token_use', ''),
            },
        )

    except jwt.ExpiredSignatureError:
        logger.warning('Token has expired')
        raise Exception('Unauthorized') from None
    except jwt.InvalidTokenError as e:
        logger.warning('Invalid token: %s', e)
        raise Exception('Unauthorized') from None
    except Exception as e:
        logger.error('Authorization error: %s', e, exc_info=True)
        raise Exception('Unauthorized') from None
