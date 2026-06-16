"""
Tests for the Relay 1 clientMutationId backwards-compatibility layer.

ADR-001 Phase 1: every mutation input/payload exposes `clientMutationId`
as a deprecated alias. Legacy Relay 1 clients sending it get their value
echoed back unchanged in the payload. Modern Relay 2 / Apollo clients can
omit it entirely.
"""


from graphql_api.schema import schema

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

# Note: this test originally targeted `create_file`, but `create_file` was
# realigned to legacy's positional-arg SDL (no `input:` wrapper, no
# clientMutationId — see PR-after-#320). Picking another file-create mutation
# that still uses the input-wrapper form (and therefore still supports CMI).
CREATE_IS_WITH_CMI_MUTATION = """
mutation CreateISWithCMI($input: CreateInversionSolutionInput!) {
    create_inversion_solution(input: $input) {
        ok
        inversion_solution { id file_name }
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
    """The CMI compat field works on more than just GeneralTask mutations.

    Switched from create_file → create_inversion_solution because create_file
    was realigned to legacy SDL's positional-arg shape (no input wrapper, no
    CMI — matches what nshm-toshi-client/runzi actually send).
    """
    # Need a parent AutomationTask for the produced_by field.
    import base64  # noqa: PLC0415

    from graphql_api.data.dynamo import create_thing  # noqa: PLC0415

    at_data = create_thing(
        gql_context["dynamodb"],
        "AutomationTask",
        {"state": "done", "result": "success", "task_type": "INVERSION", "created": "2026-01-01T00:00:00Z"},
    )
    at_id = base64.b64encode(f"AutomationTask:{at_data['object_id']}".encode()).decode()

    cmi = "is-create-cmi"
    result = schema.execute_sync(
        CREATE_IS_WITH_CMI_MUTATION,
        variable_values={
            "input": {
                "file_name": "cmi-test.zip",
                "md5_digest": "abc",
                "file_size": 1024,
                "produced_by": at_id,
                "created": "2026-01-01T00:00:00Z",
                "clientMutationId": cmi,
            }
        },
        context_value=gql_context,
    )
    assert result.errors is None, result.errors
    payload = result.data["create_inversion_solution"]
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
