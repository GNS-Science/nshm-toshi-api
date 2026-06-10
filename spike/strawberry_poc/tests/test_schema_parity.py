"""
Tests for tools/schema_parity.py — the legacy↔POC SDL diff tool.

Each "bugs caught this session" test reproduces a real schema-level
divergence that was discovered in production / manual smoketests, and
verifies the diff tool would have caught it earlier in CI.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.schema_parity import (  # noqa: E402
    diff_schemas,
    extract_types,
    format_report,
    has_any_diff,
    main,
)


# ── Unit tests: extractor ─────────────────────────────────────────────────────


def test_extract_types_picks_up_object_kind_and_fields():
    sdl = "type Foo { id: ID! name: String }"
    types = extract_types(sdl)
    assert types["Foo"]["kind"] == "object"
    assert types["Foo"]["fields"]["id"]["type"] == "ID!"
    assert types["Foo"]["fields"]["name"]["type"] == "String"


def test_extract_types_handles_interface_union_enum_input_scalar():
    sdl = """
    scalar BigInt
    interface Node { id: ID! }
    type Foo implements Node { id: ID! }
    union FooOrBar = Foo | Bar
    type Bar { id: ID! }
    enum Color { RED GREEN BLUE }
    input FilterInput { q: String limit: Int }
    """
    types = extract_types(sdl)
    assert types["BigInt"]["kind"] == "scalar"
    assert types["Node"]["kind"] == "interface"
    assert types["Foo"]["interfaces"] == ["Node"]
    assert types["FooOrBar"]["kind"] == "union"
    assert types["FooOrBar"]["members"] == ["Bar", "Foo"]
    assert types["Color"]["kind"] == "enum"
    assert types["Color"]["values"] == ["BLUE", "GREEN", "RED"]
    assert types["FilterInput"]["kind"] == "input"
    assert types["FilterInput"]["fields"] == {"q": "String", "limit": "Int"}


def test_extract_field_with_arguments():
    sdl = "type Query { node(id: ID!, deep: Boolean): String }"
    types = extract_types(sdl)
    field = types["Query"]["fields"]["node"]
    assert field["type"] == "String"
    assert field["args"] == {"id": "ID!", "deep": "Boolean"}


# ── Unit tests: diff primitives ───────────────────────────────────────────────


def test_diff_detects_type_only_in_legacy():
    legacy = "type Foo { id: ID! }"
    poc = "type Bar { id: ID! }"
    d = diff_schemas(legacy, poc)
    assert d["types_only_in_legacy"] == ["Foo"]
    assert d["types_only_in_poc"] == ["Bar"]


def test_diff_detects_field_only_in_legacy():
    legacy = "type Foo { id: ID! name: String }"
    poc = "type Foo { id: ID! }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["Foo"]["fields_only_in_legacy"] == ["name"]


def test_diff_detects_field_only_in_poc():
    legacy = "type Foo { id: ID! }"
    poc = "type Foo { id: ID! extra: Int }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["Foo"]["fields_only_in_poc"] == ["extra"]


def test_diff_detects_field_type_mismatch():
    legacy = "type Foo { size: BigInt }"
    poc = "type Foo { size: Int }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["Foo"]["field_type_mismatches"] == {"size": ("BigInt", "Int")}


def test_diff_detects_kind_mismatch():
    legacy = "type Foo { id: ID! }"
    poc = "interface Foo { id: ID! }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["Foo"]["kind_mismatch"] == ("object", "interface")


def test_diff_detects_enum_value_drift():
    legacy = "enum Color { RED GREEN BLUE }"
    poc = "enum Color { RED GREEN }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["Color"]["values_only_in_legacy"] == ["BLUE"]


def test_diff_detects_union_member_drift():
    legacy = "type A { id: ID! } type B { id: ID! } type C { id: ID! } union AB = A | B | C"
    poc = "type A { id: ID! } type B { id: ID! } union AB = A | B"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["AB"]["members_only_in_legacy"] == ["C"]


def test_diff_detects_argument_drift_on_field():
    legacy = "type Query { node(id: ID!, deep: Boolean): String }"
    poc = "type Query { node(id: ID!): String }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["Query"]["field_arg_mismatches"]["node"]["args_only_in_legacy"] == [
        "deep"
    ]


def test_diff_detects_interface_implementation_drift():
    legacy = "interface Node { id: ID! } interface FI { fn: String } type Foo implements Node & FI { id: ID! fn: String }"
    poc = "interface Node { id: ID! } type Foo implements Node { id: ID! fn: String }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["Foo"]["interfaces_only_in_legacy"] == ["FI"]


def test_diff_input_field_type_mismatch():
    legacy = "input CreateInput { file_size: BigInt }"
    poc = "input CreateInput { file_size: Int }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["CreateInput"]["field_type_mismatches"] == {
        "file_size": ("BigInt", "Int")
    }


def test_identical_schemas_produce_empty_diff():
    sdl = "type Foo { id: ID! } enum Color { RED }"
    d = diff_schemas(sdl, sdl)
    assert d == {"types_only_in_legacy": [], "types_only_in_poc": [], "type_diffs": {}}
    assert not has_any_diff(d)


# ── Bugs this tool would have caught this session ─────────────────────────────


@pytest.fixture
def legacy_minimal():
    """SDL fragment matching key legacy-schema declarations that the POC
    must mirror. Each field/type below corresponds to a real production
    issue we hit during the migration."""
    return """
        scalar BigInt
        type ToshiFile { id: ID! file_name: String file_size: BigInt }
        type GeneralTask {
          id: ID!
          title: String
          subtask_result: EventResult
          children(first: Int): TaskTaskRelationConnection
        }
        type TaskTaskRelationConnection {
          total_count: Int
          edges: [TaskTaskRelationEdge]
        }
        type TaskTaskRelationEdge { node: TaskTaskRelation }
        type TaskTaskRelation { parent: GeneralTask }
        type Mutation {
          update_automation_task(input: UpdateAutomationTaskInput!): UpdateAutomationTaskPayload
        }
        input UpdateAutomationTaskInput { task_id: ID! }
        type UpdateAutomationTaskPayload { task_result: AutomationTask }
        type AutomationTask { id: ID! }
        enum EventResult { SUCCESS FAILURE PARTIAL UNDEFINED }
        enum TaskSubType {
          INVERSION
          HAZARD
          DISAGG
          SCALE_SOLUTION
        }
    """


def test_catches_toshifile_to_file_rename(legacy_minimal):
    """Legacy has `ToshiFile`, an earlier POC iteration registered it as `File`.
    The diff must surface ToshiFile in legacy_only and File in poc_only."""
    poc = """
        type File { id: ID! file_name: String file_size: BigInt }
        type GeneralTask { id: ID! }
        scalar BigInt
    """
    d = diff_schemas(legacy_minimal, poc)
    assert "ToshiFile" in d["types_only_in_legacy"]
    assert "File" in d["types_only_in_poc"]


def test_catches_missing_update_automation_task_mutation(legacy_minimal):
    """Legacy defines `update_automation_task`; an earlier POC didn't wire it."""
    poc = """
        type Mutation { create_automation_task(input: ID!): String }
        type ToshiFile { id: ID! }
        type GeneralTask { id: ID! }
        scalar BigInt
    """
    d = diff_schemas(legacy_minimal, poc)
    mutation_diff = d["type_diffs"]["Mutation"]
    assert "update_automation_task" in mutation_diff["fields_only_in_legacy"]


def test_catches_subtask_result_missing_from_general_task(legacy_minimal):
    """Production crashed because GeneralTask.subtask_result was missing in POC."""
    poc = """
        type GeneralTask { id: ID! title: String }
        type ToshiFile { id: ID! }
        scalar BigInt
    """
    d = diff_schemas(legacy_minimal, poc)
    assert "subtask_result" in d["type_diffs"]["GeneralTask"]["fields_only_in_legacy"]


def test_catches_file_size_int_vs_bigint_mismatch():
    """The POC originally typed file_size as Int (32-bit), legacy uses BigInt.
    Production values >2GB silently failed validation."""
    legacy = "type ToshiFile { id: ID! file_size: BigInt }"
    poc = "type ToshiFile { id: ID! file_size: Int }"
    d = diff_schemas(legacy, poc)
    assert d["type_diffs"]["ToshiFile"]["field_type_mismatches"] == {
        "file_size": ("BigInt", "Int")
    }


def test_catches_missing_total_count_on_connection(legacy_minimal):
    """relay.ListConnection in POC didn't expose total_count until we added the
    custom connection subclass with override. The diff surfaces it as a missing field."""
    poc = """
        type TaskTaskRelationConnection { edges: [TaskTaskRelationEdge] }
        type TaskTaskRelationEdge { node: TaskTaskRelation }
        type TaskTaskRelation { parent: GeneralTask }
        type GeneralTask { id: ID! }
        type ToshiFile { id: ID! }
        scalar BigInt
    """
    d = diff_schemas(legacy_minimal, poc)
    assert "total_count" in d["type_diffs"]["TaskTaskRelationConnection"]["fields_only_in_legacy"]


def test_catches_disagg_enum_value_missing(legacy_minimal):
    """POC initially only tested HAZARD task_type. Missing DISAGG would be a real
    enum-value gap caught by the diff."""
    poc = """
        enum TaskSubType { INVERSION HAZARD SCALE_SOLUTION }
        type ToshiFile { id: ID! }
        type GeneralTask { id: ID! }
        scalar BigInt
    """
    d = diff_schemas(legacy_minimal, poc)
    assert "DISAGG" in d["type_diffs"]["TaskSubType"]["values_only_in_legacy"]


# ── Format + CLI smoke tests ──────────────────────────────────────────────────


def test_format_report_handles_empty_diff():
    sdl = "type Foo { id: ID! }"
    text = format_report(diff_schemas(sdl, sdl))
    assert "full parity" in text


def test_format_report_includes_all_categories(legacy_minimal):
    poc = """
        type File { id: ID! }
        type GeneralTask { id: ID! file_size: Int }
        scalar BigInt
    """
    text = format_report(diff_schemas(legacy_minimal, poc))
    assert "Types in legacy but not in POC" in text
    assert "Types in POC but not in legacy" in text
    assert "Per-type differences" in text


def test_cli_self_diff_returns_zero(tmp_path):
    sdl = tmp_path / "schema.sdl"
    sdl.write_text("type Foo { id: ID! }")
    exit_code = main([str(sdl), str(sdl), "--fail-on-diff"])
    assert exit_code == 0


def test_cli_fail_on_diff_returns_one(tmp_path, capsys):
    a = tmp_path / "a.sdl"
    b = tmp_path / "b.sdl"
    a.write_text("type Foo { id: ID! }")
    b.write_text("type Bar { id: ID! }")
    exit_code = main([str(a), str(b), "--fail-on-diff"])
    assert exit_code == 1


def test_cli_json_format(tmp_path, capsys):
    a = tmp_path / "a.sdl"
    b = tmp_path / "b.sdl"
    a.write_text("type Foo { id: ID! }")
    b.write_text("type Bar { id: ID! }")
    exit_code = main([str(a), str(b), "--format", "json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "Foo" in parsed["types_only_in_legacy"]
    assert "Bar" in parsed["types_only_in_poc"]
    # Without --fail-on-diff, exit is 0 even with divergences
    assert exit_code == 0
