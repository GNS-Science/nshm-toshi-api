"""
Tests for graphql_api/api.py — auth middleware registration block.
"""
import importlib
import os
import sys
import unittest
from unittest import mock

import boto3
from moto import mock_aws

from graphql_api.config import REGION, S3_BUCKET_NAME


def _set_mock_aws_credentials():
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
    os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
    os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


def _reimport_api():
    """Force a fresh import of graphql_api.api so module-level code re-runs."""
    sys.modules.pop('graphql_api.api', None)
    return importlib.import_module('graphql_api.api')


class TestAuthMiddlewareRegistration(unittest.TestCase):
    """Test the try/except block that registers auth middleware on app startup."""

    def setUp(self):
        _set_mock_aws_credentials()

    def test_auth_middleware_registered_when_available(self):
        """register_auth_middleware is called with the Flask app when auth.middleware is importable."""
        mock_register = mock.MagicMock()
        fake_middleware = mock.MagicMock()
        fake_middleware.register_auth_middleware = mock_register

        with mock_aws():
            s3 = boto3.resource('s3', region_name=REGION)
            s3.create_bucket(Bucket=S3_BUCKET_NAME)
            with mock.patch.dict(sys.modules, {'auth.middleware': fake_middleware}):
                api = _reimport_api()
                mock_register.assert_called_once_with(api.app)

    def test_auth_middleware_import_error_is_swallowed(self):
        """ImportError from auth.middleware is caught; no exception propagates."""
        with mock_aws():
            s3 = boto3.resource('s3', region_name=REGION)
            s3.create_bucket(Bucket=S3_BUCKET_NAME)
            with mock.patch.dict(sys.modules, {'auth.middleware': None}):
                try:
                    api = _reimport_api()
                except ImportError:
                    self.fail('ImportError from auth.middleware was not caught in api.py')
                self.assertIsNotNone(api.app)

    def test_auth_middleware_import_error_logs_debug(self):
        """A debug message is logged when auth.middleware is unavailable."""
        with mock_aws():
            s3 = boto3.resource('s3', region_name=REGION)
            s3.create_bucket(Bucket=S3_BUCKET_NAME)
            with mock.patch.dict(sys.modules, {'auth.middleware': None}):
                with mock.patch('logging.Logger.debug') as mock_debug:
                    _reimport_api()
                    debug_messages = [str(call) for call in mock_debug.call_args_list]
                    self.assertTrue(
                        any('auth.middleware' in msg for msg in debug_messages),
                        f'Expected debug log about auth.middleware, got: {debug_messages}',
                    )
