"""
Lambda entry point shim for the Strawberry/FastAPI POC.

The POC lives in spike/strawberry_poc/ and uses root-relative imports
(e.g. `from data.search import ...`). Lambda's working directory is the
repo root, so we insert the POC directory into sys.path before the POC
modules are imported. This lets the POC remain self-contained without
restructuring its imports.

Handler in serverless.yml: strawberry_poc_handler.handler
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike", "strawberry_poc"))

from app import handler  # noqa: E402, F401 — re-export for Lambda
