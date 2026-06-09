"""
Tests for the Relay 1 clientMutationId backwards-compatibility layer.

ADR-001 Phase 1: every mutation input/payload exposes `clientMutationId`
as a deprecated alias. Legacy Relay 1 clients sending it get their value
echoed back unchanged in the payload. Modern Relay 2 / Apollo clients can
omit it entirely.
"""

import pytest

from schema import schema


CREATE_WITH_CMI_MUTATION = """
mutation CreateWithCMI($input: CreateGeneralTaskInput!) {
    create_general_task(input: $input) {
        general_task { id title }
        clientMutationId
    }
}
"""

CREATE_WITHOUT_CMI_MUTATION = """
mutation CreateWithoutCMI($input: CreateGeneralTaskInput!) {
    create_general_task(input: $input) {
        general_task { id title }
        clientMutationId
    }
}
"""

CREATE_FILE_WITH_CMI_MUTATION = """
mutation CreateFileWithCMI($input: CreateFileInput!) {
    create_file(input: $input) {
        ok
        file_result { id file_name }
        clientMutationId
    }
}
"""


def test_input_accepts_client_mutation_id_and_payload_echoes(gql_context):
    """A clientMutationId passed in the input is echoed back in the payload."""
    cmi = "client-id-12345"
    result = schema.execute_sync(
        CREATE_WITH_CMI_MUTATION,
        variable_values={"input": {"title": "task with CMI", "clientMutationId": cmi}},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    payload = result.data["create_general_task"]
    assert payload["general_task"]["title"] == "task with CMI"
    assert payload["clientMutationId"] == cmi


def test_omitted_client_mutation_id_yields_null_in_payload(gql_context):
    """Modern Relay 2 / Apollo clients omit clientMutationId — payload returns null."""
    result = schema.execute_sync(
        CREATE_WITHOUT_CMI_MUTATION,
        variable_values={"input": {"title": "task without CMI"}},
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    payload = result.data["create_general_task"]
    assert payload["general_task"]["title"] == "task without CMI"
    assert payload["clientMutationId"] is None


def test_round_trip_works_on_other_mutations(gql_context):
    """The CMI compat field works on more than just GeneralTask mutations."""
    cmi = "file-create-cmi"
    result = schema.execute_sync(
        CREATE_FILE_WITH_CMI_MUTATION,
        variable_values={
            "input": {
                "file_name": "cmi-test.zip",
                "md5_digest": "abc",
                "file_size": 1024,
                "clientMutationId": cmi,
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    payload = result.data["create_file"]
    assert payload["ok"] is True
    assert payload["clientMutationId"] == cmi


def test_sdl_has_client_mutation_id_on_every_mutation_input():
    """All Create*/Update*/Append*Input types must expose clientMutationId."""
    sdl = schema.as_str()
    import re

    inputs = re.findall(r"input ((?:Create|Update|Append)\w+Input) \{[^}]+\}", sdl, re.DOTALL)
    assert len(inputs) > 15, f"expected many inputs, found {len(inputs)}"
    blocks = re.findall(
        r"input (?:Create|Update|Append)\w+Input \{[^}]+\}", sdl, re.DOTALL
    )
    for block in blocks:
        assert "clientMutationId: String" in block, f"missing clientMutationId in:\n{block}"


def test_sdl_has_client_mutation_id_on_every_mutation_payload():
    """All Create*/Update*/Append*Payload types must expose clientMutationId."""
    sdl = schema.as_str()
    import re

    payloads = re.findall(r"type ((?:Create|Update|Append)\w+Payload) \{[^}]+\}", sdl, re.DOTALL)
    assert len(payloads) > 10, f"expected many payloads, found {len(payloads)}"
    blocks = re.findall(
        r"type (?:Create|Update|Append)\w+Payload \{[^}]+\}", sdl, re.DOTALL
    )
    for block in blocks:
        assert "clientMutationId: String" in block, f"missing clientMutationId in:\n{block}"


def test_introspection_marks_client_mutation_id_deprecated():
    """The clientMutationId fields must surface as deprecated in introspection."""
    result = schema.execute_sync(
        """
        {
            __type(name: "CreateGeneralTaskInput") {
                inputFields(includeDeprecated: true) {
                    name
                    isDeprecated
                    deprecationReason
                }
            }
        }
        """
    )
    assert result.errors is None, result.errors
    fields = {f["name"]: f for f in result.data["__type"]["inputFields"]}
    assert "clientMutationId" in fields
    cmi = fields["clientMutationId"]
    assert cmi["isDeprecated"] is True
    assert "Relay 1" in cmi["deprecationReason"]


def test_introspection_marks_payload_field_deprecated():
    """Payload-side clientMutationId is also deprecated."""
    result = schema.execute_sync(
        """
        {
            __type(name: "CreateGeneralTaskPayload") {
                fields(includeDeprecated: true) {
                    name
                    isDeprecated
                }
            }
        }
        """
    )
    assert result.errors is None, result.errors
    fields = {f["name"]: f for f in result.data["__type"]["fields"]}
    assert "clientMutationId" in fields
    assert fields["clientMutationId"]["isDeprecated"] is True
