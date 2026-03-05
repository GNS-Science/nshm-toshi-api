"""
Lambda Authorizer for nshm-toshi-api.

Validates JWTs issued by AWS Cognito and returns an IAM policy.
Also accepts legacy x-api-key for backward compatibility during transition.

Environment variables (required):
    COGNITO_USER_POOL_ID   e.g. ap-southeast-2_Abc123
    COGNITO_REGION         e.g. ap-southeast-2
    COGNITO_CLIENT_ID      expected audience (access token uses client_id, not pool)

Environment variables (optional):
    LEGACY_API_KEY         if set, this x-api-key value is also accepted (backward compat)

Deployment:
    See spike/auth/README.md for Lambda deployment instructions.
    Add to serverless.yml functions section:

        jwtAuthorizer:
          handler: spike/auth/authorizer/handler.handler
          environment:
            COGNITO_USER_POOL_ID: ${env:COGNITO_USER_POOL_ID}
            COGNITO_REGION: ${self:provider.region}
            COGNITO_CLIENT_ID: ${env:COGNITO_CLIENT_ID}
            LEGACY_API_KEY: ${env:LEGACY_API_KEY, ''}

    And on the graphql POST/GET events:
        authorizer:
          name: jwtAuthorizer
          resultTtlInSeconds: 300
          identitySource: method.request.header.Authorization
          type: token
"""
import json
import logging
import os
import time
from functools import lru_cache
from urllib.request import urlopen

import jwt  # PyJWT
from jwt import PyJWKClient

logging.getLogger().setLevel(logging.INFO)  # ensure Lambda root logger captures INFO
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JWKS cache — reused across warm Lambda invocations
# ---------------------------------------------------------------------------

_jwks_client = None


def get_jwks_client():
    """Return a cached PyJWKClient for the Cognito JWKS endpoint."""
    global _jwks_client
    if _jwks_client is None:
        pool_id = os.environ['COGNITO_USER_POOL_ID']
        region = os.environ['COGNITO_REGION']
        jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json'
        logger.info(f'Initialising JWKS client: {jwks_url}')
        _jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
    return _jwks_client


# ---------------------------------------------------------------------------
# IAM policy builder
# ---------------------------------------------------------------------------

def build_policy(principal_id, effect, resource, context=None):
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

def validate_cognito_token(token):
    """
    Validate a Cognito JWT.

    Returns (principal_id, scopes_str) on success.
    Raises jwt.exceptions.* on failure.
    """
    pool_id = os.environ['COGNITO_USER_POOL_ID']
    region = os.environ['COGNITO_REGION']
    client_id = os.environ.get('COGNITO_CLIENT_ID', '')

    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    expected_issuer = f'https://cognito-idp.{region}.amazonaws.com/{pool_id}'

    # Access tokens have audience = client_id; id tokens have audience = client_id
    decode_options = {'verify_exp': True}
    algorithms = ['RS256']

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=algorithms,
        issuer=expected_issuer,
        options=decode_options,
    )

    # Verify token_use: accept both access and id tokens
    token_use = payload.get('token_use', '')
    if token_use not in ('access', 'id'):
        raise jwt.InvalidTokenError(f'Invalid token_use: {token_use}')

    # For access tokens, audience is the client_id claim (not 'aud')
    if token_use == 'access':
        token_client_id = payload.get('client_id', '')
        if client_id and token_client_id != client_id:
            raise jwt.InvalidAudienceError(
                f'client_id mismatch: expected {client_id}, got {token_client_id}'
            )

    principal_id = payload.get('username') or payload.get('sub', 'unknown')
    scopes = payload.get('scope', '')

    return principal_id, scopes, payload


def validate_legacy_api_key(token):
    """Check if token matches the legacy x-api-key value."""
    legacy_key = os.environ.get('LEGACY_API_KEY', '')
    if not legacy_key:
        return False
    return token == legacy_key


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event, context):
    """
    Lambda authorizer handler.

    Input event (TOKEN type):
        {
            "authorizationToken": "Bearer <jwt>" | "x-api-key <key>",
            "methodArn": "arn:aws:execute-api:..."
        }
    """
    method_arn = event.get('methodArn', '*')
    auth_header = event.get('authorizationToken', '')
    scheme = (auth_header.split(' ', 1)[0].lower()) if auth_header else '(none)'

    print(f'[jwtAuthorizer] INVOKED scheme={scheme} arn={method_arn}')
    logger.info(f'[jwtAuthorizer] INVOKED scheme={scheme} arn={method_arn}')

    if not auth_header:
        logger.warning('No authorization token provided')
        raise Exception('Unauthorized')

    # Parse the Authorization header
    parts = auth_header.split(' ', 1)
    scheme = parts[0].lower() if parts else ''
    token = parts[1] if len(parts) > 1 else ''

    # Legacy x-api-key fallback
    if scheme in ('x-api-key', 'apikey') or (len(parts) == 1 and validate_legacy_api_key(auth_header)):
        raw_key = token or auth_header
        if validate_legacy_api_key(raw_key):
            logger.info('Authorizing via legacy x-api-key')
            return build_policy(
                'legacy-api-key',
                'Allow',
                method_arn,
                context={'userId': 'legacy', 'scopes': 'toshi/read toshi/write', 'authMethod': 'apikey'},
            )
        else:
            logger.warning('Invalid legacy API key')
            raise Exception('Unauthorized')

    # JWT Bearer token
    if scheme != 'bearer':
        logger.warning(f'Unknown authorization scheme: {scheme}')
        raise Exception('Unauthorized')

    if not token:
        logger.warning('Bearer token is empty')
        raise Exception('Unauthorized')

    try:
        start = time.perf_counter()
        principal_id, scopes, payload = validate_cognito_token(token)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(f'JWT validated in {elapsed_ms:.1f}ms for principal: {principal_id}')

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
        raise Exception('Unauthorized')
    except jwt.InvalidTokenError as e:
        logger.warning(f'Invalid token: {e}')
        raise Exception('Unauthorized')
    except Exception as e:
        logger.error(f'Authorization error: {e}', exc_info=True)
        raise Exception('Unauthorized')
