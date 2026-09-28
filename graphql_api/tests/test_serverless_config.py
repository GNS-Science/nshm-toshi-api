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


@pytest.mark.skip(
    reason="ES_ENDPOINT and the ElasticSearchInstance resource are out of the template for the "
    "#379 resource-import window; the follow-up PR restores both, and these guards with them."
)
def test_graphql_function_has_es_endpoint_from_domain(graphql_env):
    endpoint = graphql_env.get("ES_ENDPOINT")
    assert endpoint, "graphql function has no ES_ENDPOINT — indexing is off on every stage"
    assert endpoint == {"Fn::Join": ["", ["https://", {"Fn::GetAtt": ["ElasticSearchInstance", "DomainEndpoint"]}]]}


def test_es_endpoint_absent_during_import_window(graphql_env):
    """
    Deliberate, and temporary (#379): ES_ENDPOINT was a GetAtt on the detached
    ElasticSearchInstance. While it is unset, prod indexes nothing — objects
    created in this window need backfilling. Delete this test when the follow-up
    PR restores ES_ENDPOINT.
    """
    assert "ES_ENDPOINT" not in graphql_env


def test_graphql_function_indexes_the_live_index(sls, graphql_env):
    # search.py's fallback is "toshi-index-mapped" (hyphens); the live index is
    # toshi_index_mapped (underscores). Without ES_INDEX, writes land in a new,
    # unmapped index that weka never reads.
    assert graphql_env.get("ES_INDEX") == "${self:custom.esIndex}"
    assert sls["custom"]["esIndex"] == "toshi_index_mapped"
    assert graphql_env.get("ES_REGION")


@pytest.mark.skip(
    reason="ES_ENDPOINT and the ElasticSearchInstance resource are out of the template for the "
    "#379 resource-import window; the follow-up PR restores both, and these guards with them."
)
def test_es_endpoint_excluded_only_on_test(sls):
    """
    ES_ENDPOINT is dropped exactly where the domain is (test), nowhere else.

    Missing the exclusion leaves test's ES_ENDPOINT GetAtt pointing at an excluded
    resource, failing the deploy-test deploy; excluding it elsewhere turns prod
    indexing off.
    """
    endpoint_path = "functions.graphql.environment.ES_ENDPOINT"
    rules = sls["custom"]["serverlessIfElse"]
    matching = [r for r in rules if endpoint_path in r.get("Exclude", []) + r.get("ElseExclude", [])]
    assert len(matching) == 1, f"expected one serverlessIfElse rule excluding {endpoint_path}, found {len(matching)}"
    [rule] = matching
    assert rule["If"] == '"${self:custom.stage}" == "test"'
    assert endpoint_path in rule.get("Exclude", [])
    assert endpoint_path not in rule.get("ElseExclude", [])
    assert "resources.Resources.ElasticSearchInstance" in rule["Exclude"]


def test_role_can_write_to_domain(sls):
    es_statements = [
        s for s in sls["provider"]["iamRoleStatements"] if any(a.startswith("es:") for a in s.get("Action", []))
    ]
    assert es_statements, "no es:* IAM statement — signed writes would be denied"
    actions = {a for s in es_statements for a in s["Action"]}
    assert {"es:ESHttpPut", "es:ESHttpPost"} <= actions


@pytest.mark.skip(
    reason="ES_ENDPOINT and the ElasticSearchInstance resource are out of the template for the "
    "#379 resource-import window; the follow-up PR restores both, and these guards with them."
)
def test_es_domain_is_retained(sls):
    """
    The prod domain must survive `sls remove` and any update that replaces it
    (#379). weka reads it directly and nothing in this repo references it, so
    losing it would be silent here and immediate for users.
    """
    domain = sls["resources"]["Resources"]["ElasticSearchInstance"]
    assert domain.get("DeletionPolicy") == "Retain"
    assert domain.get("UpdateReplacePolicy") == "Retain"


def test_alarm_matches_logged_marker(sls):
    resources = sls["resources"]["Resources"]
    metric_filter = resources["IndexingFailureMetricFilter"]["Properties"]
    alarm = resources["IndexingFailureAlarm"]["Properties"]

    assert INDEX_FAILURE_MARKER in metric_filter["FilterPattern"]
    assert metric_filter["LogGroupName"] == {"Ref": "GraphqlLogGroup"}
    [transform] = metric_filter["MetricTransformations"]
    assert (alarm["Namespace"], alarm["MetricName"]) == (transform["MetricNamespace"], transform["MetricName"])
    assert alarm["AlarmActions"] == [{"Ref": "IndexingAlarmTopic"}]


def test_template_values_are_ascii(sls):
    """
    Non-ASCII in template *values* breaks CloudFormation resource import: the CI
    deploy mangled an em dash in an alarm description into "?", so no locally
    generated template could match the deployed one and the import was refused
    (#379). Comments are exempt — they never reach CloudFormation.
    """
    offenders = []

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and any(ord(c) > 127 for c in node):
            offenders.append(f"{path}: {ascii(node)[:80]}")

    for section in ("resources", "functions", "provider", "custom"):
        walk(sls.get(section), section)

    assert not offenders, "non-ASCII in template values:\n" + "\n".join(offenders)
