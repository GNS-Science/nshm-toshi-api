"""
Tests for auth/authorizer/handler.py.

Covers:
  - build_policy() — pure function, no mocking needed
  - validate_legacy_api_key() — env-var driven
  - handler() — full integration with mocked validate_cognito_token
"""

import os
import unittest
from unittest import mock

import jwt

import auth.authorizer.handler as handler_module
from auth.authorizer.handler import build_policy, handler, validate_legacy_api_key

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_ARN = 'arn:aws:execute-api:ap-southeast-2:123456789012:abc123/dev/POST/graphql'


def _event(authorization=None, x_api_key=None):
    headers = {}
    if authorization is not None:
        headers['Authorization'] = authorization
    if x_api_key is not None:
        headers['x-api-key'] = x_api_key
    return {'methodArn': FAKE_ARN, 'headers': headers}


# ---------------------------------------------------------------------------
# build_policy
# ---------------------------------------------------------------------------


class TestBuildPolicy(unittest.TestCase):
    def test_allow_policy_structure(self):
        policy = build_policy('user123', 'Allow', FAKE_ARN)
        self.assertEqual(policy['principalId'], 'user123')
        stmt = policy['policyDocument']['Statement'][0]
        self.assertEqual(stmt['Effect'], 'Allow')
        self.assertEqual(stmt['Action'], 'execute-api:Invoke')
        self.assertEqual(stmt['Resource'], FAKE_ARN)

    def test_deny_policy_structure(self):
        policy = build_policy('user123', 'Deny', FAKE_ARN)
        self.assertEqual(policy['policyDocument']['Statement'][0]['Effect'], 'Deny')

    def test_context_included_when_provided(self):
        ctx = {'userId': 'u1', 'scopes': 'toshi/read'}
        policy = build_policy('u1', 'Allow', FAKE_ARN, context=ctx)
        self.assertEqual(policy['context'], ctx)

    def test_context_absent_when_not_provided(self):
        policy = build_policy('u1', 'Allow', FAKE_ARN)
        self.assertNotIn('context', policy)

    def test_context_absent_when_none(self):
        policy = build_policy('u1', 'Allow', FAKE_ARN, context=None)
        self.assertNotIn('context', policy)


# ---------------------------------------------------------------------------
# validate_legacy_api_key
# ---------------------------------------------------------------------------


class TestValidateLegacyApiKey(unittest.TestCase):
    def test_returns_true_for_matching_key(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'secret123'}):
            self.assertTrue(validate_legacy_api_key('secret123'))

    def test_returns_false_for_wrong_key(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'secret123'}):
            self.assertFalse(validate_legacy_api_key('wrong'))

    def test_returns_false_when_env_var_not_set(self):
        env = {k: v for k, v in os.environ.items() if k != 'LEGACY_API_KEY'}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertFalse(validate_legacy_api_key('anything'))

    def test_returns_false_when_env_var_is_empty(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': ''}):
            self.assertFalse(validate_legacy_api_key(''))


# ---------------------------------------------------------------------------
# handler — no auth credentials provided
# ---------------------------------------------------------------------------


class TestHandlerNoCredentials(unittest.TestCase):
    def test_no_headers_raises_unauthorized(self):
        with self.assertRaises(Exception) as cm:
            handler(_event(), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')

    def test_empty_authorization_and_no_api_key_raises_unauthorized(self):
        with self.assertRaises(Exception) as cm:
            handler(_event(authorization=''), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')


# ---------------------------------------------------------------------------
# handler — legacy x-api-key header
# ---------------------------------------------------------------------------


class TestHandlerLegacyApiKeyHeader(unittest.TestCase):
    def test_valid_api_key_returns_allow(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
            result = handler(_event(x_api_key='mykey'), None)
        self.assertEqual(result['policyDocument']['Statement'][0]['Effect'], 'Allow')
        self.assertEqual(result['context']['authMethod'], 'apikey')
        self.assertEqual(result['principalId'], 'legacy-api-key')

    def test_valid_api_key_grants_read_write_scopes(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
            result = handler(_event(x_api_key='mykey'), None)
        self.assertIn('toshi/read', result['context']['scopes'])
        self.assertIn('toshi/write', result['context']['scopes'])

    def test_invalid_api_key_raises_unauthorized(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
            with self.assertRaises(Exception) as cm:
                handler(_event(x_api_key='wrong'), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')

    def test_api_key_header_takes_priority_over_authorization(self):
        """x-api-key header is checked before Authorization header."""
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
            # x-api-key valid + Authorization missing → should Allow via api key
            result = handler(_event(x_api_key='mykey'), None)
        self.assertEqual(result['context']['authMethod'], 'apikey')

    def test_api_key_header_case_insensitive(self):
        """RFC 7230 §3.2: header names are case-insensitive. The API Gateway
        client sends 'X-API-KEY' (all-caps); we must accept any casing."""
        for header_name in ('x-api-key', 'X-Api-Key', 'X-API-KEY', 'X-api-KEY'):
            with self.subTest(header=header_name):
                event = {'methodArn': FAKE_ARN, 'headers': {header_name: 'mykey'}}
                with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
                    result = handler(event, None)
                self.assertEqual(result['policyDocument']['Statement'][0]['Effect'], 'Allow')
                self.assertEqual(result['context']['authMethod'], 'apikey')


# ---------------------------------------------------------------------------
# handler — Authorization: x-api-key <key>
# ---------------------------------------------------------------------------


class TestHandlerAuthorizationApiKey(unittest.TestCase):
    def test_authorization_xapikey_scheme_valid(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
            result = handler(_event(authorization='x-api-key mykey'), None)
        self.assertEqual(result['policyDocument']['Statement'][0]['Effect'], 'Allow')
        self.assertEqual(result['context']['authMethod'], 'apikey')

    def test_authorization_apikey_scheme_valid(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
            result = handler(_event(authorization='apikey mykey'), None)
        self.assertEqual(result['policyDocument']['Statement'][0]['Effect'], 'Allow')

    def test_authorization_xapikey_scheme_invalid(self):
        with mock.patch.dict(os.environ, {'LEGACY_API_KEY': 'mykey'}):
            with self.assertRaises(Exception) as cm:
                handler(_event(authorization='x-api-key wrong'), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')


# ---------------------------------------------------------------------------
# handler — unknown / unsupported Authorization scheme
# ---------------------------------------------------------------------------


class TestHandlerUnknownScheme(unittest.TestCase):
    def test_unknown_scheme_raises_unauthorized(self):
        with self.assertRaises(Exception) as cm:
            handler(_event(authorization='Basic dXNlcjpwYXNz'), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')

    def test_bearer_empty_token_raises_unauthorized(self):
        with self.assertRaises(Exception) as cm:
            handler(_event(authorization='Bearer'), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')


# ---------------------------------------------------------------------------
# handler — Bearer JWT
# ---------------------------------------------------------------------------


class TestHandlerBearerJWT(unittest.TestCase):
    def _patch_cognito(self, return_value=None, side_effect=None):
        """Patch validate_cognito_token on the handler module."""
        return mock.patch.object(
            handler_module, 'validate_cognito_token', return_value=return_value, side_effect=side_effect
        )

    def test_valid_jwt_returns_allow(self):
        payload = {'token_use': 'access'}
        with self._patch_cognito(return_value=('alice@example.com', 'toshi/read toshi/write', payload)):
            result = handler(_event(authorization='Bearer faketoken'), None)
        self.assertEqual(result['policyDocument']['Statement'][0]['Effect'], 'Allow')
        self.assertEqual(result['principalId'], 'alice@example.com')
        self.assertEqual(result['context']['scopes'], 'toshi/read toshi/write')
        self.assertEqual(result['context']['authMethod'], 'jwt')

    def test_expired_jwt_raises_unauthorized(self):
        with self._patch_cognito(side_effect=jwt.ExpiredSignatureError('expired')):
            with self.assertRaises(Exception) as cm:
                handler(_event(authorization='Bearer expiredtoken'), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')

    def test_invalid_jwt_raises_unauthorized(self):
        with self._patch_cognito(side_effect=jwt.InvalidTokenError('bad sig')):
            with self.assertRaises(Exception) as cm:
                handler(_event(authorization='Bearer badtoken'), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')

    def test_unexpected_exception_raises_unauthorized(self):
        with self._patch_cognito(side_effect=RuntimeError('network error')):
            with self.assertRaises(Exception) as cm:
                handler(_event(authorization='Bearer sometoken'), None)
        self.assertEqual(str(cm.exception), 'Unauthorized')

    def test_valid_jwt_context_includes_token_use(self):
        payload = {'token_use': 'id'}
        with self._patch_cognito(return_value=('bob', 'toshi/read', payload)):
            result = handler(_event(authorization='Bearer faketoken'), None)
        self.assertEqual(result['context']['tokenUse'], 'id')

    def test_case_insensitive_bearer_scheme(self):
        """Authorization: BEARER should also be accepted."""
        payload = {'token_use': 'access'}
        with self._patch_cognito(return_value=('alice', 'toshi/read', payload)):
            result = handler(_event(authorization='BEARER faketoken'), None)
        self.assertEqual(result['policyDocument']['Statement'][0]['Effect'], 'Allow')


if __name__ == '__main__':
    unittest.main()
