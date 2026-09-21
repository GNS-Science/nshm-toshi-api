"""
Regression guard for the deployed search config (#378).

Nothing else in the suite sees the deployed config: conftest points
ES_ENDPOINT at a testcontainers ES, so tests pass whether or not serverless.yml
wires the graphql Lambda to the real domain. That is how a migration left
writes going to localhost:9200 for three months. These tests read serverless.yml
directly and fail if the wiring goes missing again.

They run in CI before every deploy (deploy-aws-lambda.yaml calls the test
workflow first).
"""

from pathlib import Path

import pytest
import yaml

from graphql_api.data.search import INDEX_FAILURE_MARKER

SERVERLESS_YML = Path(__file__).parents[2] / "serverless.yml"


class _CfnLoader(yaml.SafeLoader):
    """SafeLoader that tolerates CloudFormation short-form tags (!Ref, !GetAtt, ...)."""


def _cfn_tag(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node, deep=True)
    else:
        value = loader.construct_mapping(node, deep=True)
    return {tag_suffix: value}


_CfnLoader.add_multi_constructor("!", _cfn_tag)


@pytest.fixture(scope="module")
def sls():
    return yaml.load(SERVERLESS_YML.read_text(), Loader=_CfnLoader)


@pytest.fixture(scope="module")
def graphql_env(sls):
    return sls["functions"]["graphql"]["environment"]


def test_graphql_function_has_es_endpoint_from_domain(graphql_env):
    endpoint = graphql_env.get("ES_ENDPOINT")
    assert endpoint, "graphql function has no ES_ENDPOINT — indexing is off on every stage"
    assert endpoint == {"Fn::Join": ["", ["https://", {"Fn::GetAtt": ["ElasticSearchInstance", "DomainEndpoint"]}]]}


def test_graphql_function_indexes_the_live_index(sls, graphql_env):
    # search.py's fallback is "toshi-index-mapped" (hyphens); the live index is
    # toshi_index_mapped (underscores). Without ES_INDEX, writes land in a new,
    # unmapped index that weka never reads.
    assert graphql_env.get("ES_INDEX") == "${self:custom.esIndex}"
    assert sls["custom"]["esIndex"] == "toshi_index_mapped"
    assert graphql_env.get("ES_REGION")


def test_es_endpoint_excluded_only_on_test(sls):
    """ES_ENDPOINT may be dropped where the domain is excluded (test), nowhere else."""
    for rule in sls["custom"]["serverlessIfElse"]:
        excludes = rule.get("Exclude", []) + rule.get("ElseExclude", [])
        if "functions.graphql.environment.ES_ENDPOINT" in excludes:
            assert rule["If"] == '"${self:custom.stage}" == "test"'
            assert "functions.graphql.environment.ES_ENDPOINT" not in rule.get("ElseExclude", [])
            assert "resources.Resources.ElasticSearchInstance" in rule.get("Exclude", [])


def test_role_can_write_to_domain(sls):
    es_statements = [
        s for s in sls["provider"]["iamRoleStatements"] if any(a.startswith("es:") for a in s.get("Action", []))
    ]
    assert es_statements, "no es:* IAM statement — signed writes would be denied"
    actions = {a for s in es_statements for a in s["Action"]}
    assert {"es:ESHttpPut", "es:ESHttpPost"} <= actions


def test_alarm_matches_logged_marker(sls):
    resources = sls["resources"]["Resources"]
    metric_filter = resources["IndexingFailureMetricFilter"]["Properties"]
    alarm = resources["IndexingFailureAlarm"]["Properties"]

    assert INDEX_FAILURE_MARKER in metric_filter["FilterPattern"]
    assert metric_filter["LogGroupName"] == {"Ref": "GraphqlLogGroup"}
    [transform] = metric_filter["MetricTransformations"]
    assert (alarm["Namespace"], alarm["MetricName"]) == (transform["MetricNamespace"], transform["MetricName"])
    assert alarm["AlarmActions"] == [{"Ref": "IndexingAlarmTopic"}]
