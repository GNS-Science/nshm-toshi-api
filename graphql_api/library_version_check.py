#! library_version_check.py
"""
This module simply attempts to import botocore and boto3 and to report their respective versions.

This is required because in serverless deployments we rely on the AWS lambda environment to have these
pre-installed in the lambda PythonX installation. But this has recently lead to some version conflicts:

e.g.
 - https://stackoverflow.com/questions/75887656/
   botocore-package-in-lambda-python-3-9-runtime-return-error-cannot-import-name
 - https://github.com/boto/boto3/issues/3648

Hopefully logging output from this modulw will aid in diagnosing such issues in the future.
"""

import importlib.util
import logging
import sys
from typing import List

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# from https://docs.python.org/3/library/importlib.html#importing-programmatically
def check_import(name):
    spec = importlib.util.find_spec(name)
    if spec:
        log.info('module %s has spec" %s ' % (name, spec))
    else:
        log.warning('unable to find_spec for module %s' % name)
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    log.info('library: "%s" has version: %s' % (name, module.__version__))


def log_library_info(lib_names: List[str] = None):
    lib_names = lib_names or ['botocore', 'boto3']
    for name in lib_names:
        check_import(name)