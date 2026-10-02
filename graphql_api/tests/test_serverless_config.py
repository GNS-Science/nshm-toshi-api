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

import json
from pathlib import Path

import pytest
import yaml

from graphql_api.data.search import INDEX_FAILURE_MARKER

SERVERLESS_YML = Path(__file__).parents[2] / "serverless.yml"
PACKAGE_JSON = Path(__file__).parents[2] / "package.json"


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


def test_role_is_scoped_to_its_index(sls):
    """
    The domain policy defers to IAM, so this role *is* the graphql function's access
    (#379). It indexes one index; it has no business at the domain root — no _bulk,
    no index creation or deletion, no _cluster APIs — and no DELETE at all.
    """
    [statement] = [
        s for s in sls["provider"]["iamRoleStatements"] if any(a.startswith("es:") for a in s.get("Action", []))
    ]
    assert set(statement["Action"]) == {"es:ESHttpPut", "es:ESHttpPost", "es:ESHttpGet"}
    assert statement["Resource"] == [
        {
            "Fn::Sub": "arn:aws:es:${AWS::Region}:${AWS::AccountId}:domain/"
            "${self:custom.esDomainName}/${self:custom.esIndex}/*"
        }
    ]


def test_es_domain_is_retained(sls):
    """
    The prod domain must survive `sls remove` and any update that replaces it
    (#379). weka reads it directly and nothing in this repo references it, so
    losing it would be silent here and immediate for users.
    """
    domain = sls["resources"]["Resources"]["ElasticSearchInstance"]
    assert domain.get("DeletionPolicy") == "Retain"
    assert domain.get("UpdateReplacePolicy") == "Retain"


def test_es_domain_matches_the_live_domain(sls):
    """
    The template must describe the domain that exists (#379). It was wrong for six
    years — 6.2 / t2.small / gp2 against a live 7.10 / m7g.medium / gp3 — and a
    deploy could not correct it, which is why the resource was imported.

    EnableVersionUpgrade is not decoration: without it a version change is a
    replacement, and DomainName is set, so the deploy fails instead.
    """
    domain = sls["resources"]["Resources"]["ElasticSearchInstance"]
    props = domain["Properties"]
    # AWS::Elasticsearch::Domain cannot be imported, and has no EBSOptions.Throughput.
    assert domain["Type"] == "AWS::OpenSearchService::Domain"
    assert domain["UpdatePolicy"] == {"EnableVersionUpgrade": True}
    # the engine is unchanged — this is still Elasticsearch 7.10
    assert props["EngineVersion"] == "Elasticsearch_7.10"
    assert props["ClusterConfig"]["InstanceType"] == "m7g.medium.search"
    assert props["EBSOptions"] == {
        "EBSEnabled": True,
        "VolumeType": "gp3",
        "VolumeSize": 50,
        "Iops": 3000,
        "Throughput": 125,
    }
    # Adopting these would change the live domain; they are not ours to set here.
    for absent in ("LogPublishingOptions", "AdvancedOptions"):
        assert absent not in props


def test_domain_refuses_anonymous_requests(sls):
    """
    The domain used to admit unsigned requests, with es:* (deletes included), from
    one IP address, over plain http too (#379 item 3, #386). Every legitimate client
    signs its requests — the graphql function, the weka gateway, operators — and each
    was confirmed to be admitted by its own IAM policy before the rule was removed.

    Principal "*" is anonymous access. Any statement that grants it, with or without
    an IP condition, reopens the domain.
    """
    props = sls["resources"]["Resources"]["ElasticSearchInstance"]["Properties"]
    statements = props["AccessPolicies"]["Statement"]

    for statement in statements:
        assert statement["Principal"] != "*"
        assert statement["Principal"].get("AWS") != "*"
        assert "Condition" not in statement, "an IP condition means someone expects unsigned access"

    # the account (its root) defers to IAM: only principals whose own policy allows it
    # get in. The bare account id is the form AWS stores, so drift detection agrees.
    [statement] = statements
    assert statement["Effect"] == "Allow"
    assert statement["Principal"] == {"AWS": {"Ref": "AWS::AccountId"}}
    assert statement["Action"] == "es:ESHttp*"

    endpoint = props["DomainEndpointOptions"]
    assert endpoint["EnforceHTTPS"] is True
    # pinned to the live value, so CloudFormation cannot reset it to a weaker default
    assert endpoint["TLSSecurityPolicy"] == "Policy-Min-TLS-1-2-2019-07"


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


def test_lambda_concurrency_is_capped(sls):
    """
    reservedConcurrency is what bounds the bill: uncapped, a flood can hold the
    account's whole 1,000-execution pool at 4 GB each and starve every other
    function in the account.

    Both functions share one cap. Every request passes through the authorizer
    first, so a lower cap there would throttle graphql below its own.
    """
    cap = sls["custom"]["reserved_concurrency"]
    assert 0 < cap <= 200
    for name in ("graphql", "jwtAuthorizer"):
        assert sls["functions"][name]["reservedConcurrency"] == "${self:custom.reserved_concurrency}"


def test_deploy_applies_the_stage_throttle():
    """
    Serverless cannot set a throttle on a REST API stage, so it is not in
    serverless.yml at all: the `deploy` script applies it after the stack deploys.
    Drop that step and a recreated stage silently runs at the account default
    (10,000 req/s, shared with every other API in the account).

    Chained with `&&` after `serverless deploy`, so a throttle that cannot be
    applied fails the deploy rather than passing unnoticed.
    """
    deploy = json.loads(PACKAGE_JSON.read_text())["scripts"]["deploy"]
    steps = [step.strip() for step in deploy.split("&&")]
    assert steps[0].startswith("serverless deploy")
    assert steps[-1] == "bash scripts/stage_throttle.sh ${STAGE} apply"
    assert ";" not in deploy and "||" not in deploy, "a failed throttle step must fail the deploy"
    assert (PACKAGE_JSON.parent / "scripts" / "stage_throttle.sh").is_file()
