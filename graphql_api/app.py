"""
FastAPI + Mangum entry point.

Replaces Flask + serverless-wsgi. The Lambda handler is `app.handler`.

Local dev:
    uvicorn app:app --reload
    # GraphQL playground at http://localhost:8000/graphql

Lambda deploy:
    handler: spike/strawberry_poc/app.handler
    (adjust serverless.yml function definition)
"""

import os

import boto3
from fastapi import FastAPI, Request
from mangum import Mangum
from strawberry.fastapi import GraphQLRouter

from graphql_api.data.search import es_endpoint, es_index
from graphql_api.schema import schema

app = FastAPI(title="nshm-toshi-api (Strawberry POC)")


async def get_context(request: Request) -> dict:
    """
    Inject shared resources into the GraphQL context.

    In production, boto3 resource is created once per Lambda container.
    In tests, the moto-patched resource is passed via request.state.
    ES_ENDPOINT/ES_INDEX can be overridden via env vars or request.state.
    """
    dynamodb = getattr(request.state, "dynamodb", None) or boto3.resource("dynamodb", region_name="ap-southeast-2")
    return {
        "dynamodb": dynamodb,
        "es_endpoint": getattr(request.state, "es_endpoint", None) or es_endpoint(),
        "es_index": getattr(request.state, "es_index", None) or es_index(),
        "request": request,
    }


graphql_router = GraphQLRouter(schema, context_getter=get_context)  # type: ignore[arg-type]
app.include_router(graphql_router, prefix=os.environ.get("GRAPHQL_PATH", "/graphql"))

# Lambda entry point — replaces serverless-wsgi's wsgi_handler.handler
handler = Mangum(app)
