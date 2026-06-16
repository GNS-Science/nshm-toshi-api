"""
Schema parity diff — compare two GraphQL schemas at the SDL level.

Designed to catch the exact class of bugs that surfaced this session:
  - Types missing from one side (e.g. ToshiFile renamed to File)
  - Fields missing from one side (e.g. GeneralTask.subtask_result)
  - Field type mismatches (e.g. file_size: BigInt vs Int)
  - Mutations missing from one side (e.g. update_automation_task)
  - Enum value drift (e.g. DISAGG task type)
  - Union member drift

Inputs are two SDL strings (or files). Output is a structured diff dict
plus a markdown report. Designed for CI: `--fail-on-diff` exits 1 when
unexpected divergence is found, so a workflow step can gate merges.

Implementation uses graphql-core's parser (already a transitive dep via
strawberry-graphql) rather than the introspection JSON because SDL is
the canonical comparable representation and works for any schema that
can emit SDL — both Graphene (`print_schema(root_schema)`) and
Strawberry (`schema.as_str()`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graphql.language import parse
from graphql.language.ast import (
    DocumentNode,
    EnumTypeDefinitionNode,
    FieldDefinitionNode,
    InputObjectTypeDefinitionNode,
    InputValueDefinitionNode,
    InterfaceTypeDefinitionNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    ObjectTypeDefinitionNode,
    ScalarTypeDefinitionNode,
    UnionTypeDefinitionNode,
)


def _type_to_str(node) -> str:
    """Render a type AST node back to SDL form (e.g. '[String!]!')."""
    if isinstance(node, NonNullTypeNode):
        return f"{_type_to_str(node.type)}!"
    if isinstance(node, ListTypeNode):
        return f"[{_type_to_str(node.type)}]"
    if isinstance(node, NamedTypeNode):
        return node.name.value
    return str(node)


def _args_to_dict(field: FieldDefinitionNode) -> dict[str, str]:
    """{arg_name: rendered_type} for a field's arguments."""
    return {a.name.value: _type_to_str(a.type) for a in field.arguments}


def _fields_to_dict(field_defs) -> dict[str, dict]:
    """{field_name: {type: ..., args: {...}}} for object/interface fields."""
    out = {}
    for f in field_defs:
        entry: dict = {"type": _type_to_str(f.type)}
        if isinstance(f, FieldDefinitionNode) and f.arguments:
            entry["args"] = _args_to_dict(f)
        out[f.name.value] = entry
    return out


def _input_fields_to_dict(field_defs) -> dict[str, str]:
    """{field_name: rendered_type} for input object fields."""
    return {f.name.value: _type_to_str(f.type) for f in field_defs if isinstance(f, InputValueDefinitionNode)}


def extract_types(sdl: str) -> dict[str, dict]:
    """Parse SDL → {type_name: {kind, ...}} dict suitable for diffing."""
    doc = parse(sdl)
    return _extract_types(doc)


def _extract_types(doc: DocumentNode) -> dict[str, dict]:
    types: dict[str, dict] = {}
    for defn in doc.definitions:
        if not hasattr(defn, "name"):
            continue
        name = defn.name.value
        if isinstance(defn, ObjectTypeDefinitionNode):
            types[name] = {
                "kind": "object",
                "interfaces": sorted(i.name.value for i in defn.interfaces),
                "fields": _fields_to_dict(defn.fields),
            }
        elif isinstance(defn, InterfaceTypeDefinitionNode):
            types[name] = {
                "kind": "interface",
                "fields": _fields_to_dict(defn.fields),
            }
        elif isinstance(defn, UnionTypeDefinitionNode):
            types[name] = {
                "kind": "union",
                "members": sorted(t.name.value for t in defn.types),
            }
        elif isinstance(defn, EnumTypeDefinitionNode):
            types[name] = {
                "kind": "enum",
                "values": sorted(v.name.value for v in defn.values),
            }
        elif isinstance(defn, InputObjectTypeDefinitionNode):
            types[name] = {
                "kind": "input",
                "fields": _input_fields_to_dict(defn.fields),
            }
        elif isinstance(defn, ScalarTypeDefinitionNode):
            types[name] = {"kind": "scalar"}
    return types


def _diff_object_or_interface(legacy: dict, poc: dict) -> dict:
    l_fields = legacy["fields"]
    p_fields = poc["fields"]
    l_names = set(l_fields.keys())
    p_names = set(p_fields.keys())

    type_mismatches = {}
    args_mismatches = {}
    for name in l_names & p_names:
        if l_fields[name]["type"] != p_fields[name]["type"]:
            type_mismatches[name] = (l_fields[name]["type"], p_fields[name]["type"])
        # Compare args if either side has them
        l_args = l_fields[name].get("args", {})
        p_args = p_fields[name].get("args", {})
        if l_args != p_args:
            args_mismatches[name] = {
                "args_only_in_legacy": sorted(set(l_args) - set(p_args)),
                "args_only_in_poc": sorted(set(p_args) - set(l_args)),
                "arg_type_mismatches": {
                    a: (l_args[a], p_args[a]) for a in set(l_args) & set(p_args) if l_args[a] != p_args[a]
                },
            }

    out = {}
    only_l = sorted(l_names - p_names)
    only_p = sorted(p_names - l_names)
    if only_l:
        out["fields_only_in_legacy"] = only_l
    if only_p:
        out["fields_only_in_poc"] = only_p
    if type_mismatches:
        out["field_type_mismatches"] = type_mismatches
    if args_mismatches:
        out["field_arg_mismatches"] = args_mismatches

    # Interface list diff (objects only)
    if legacy["kind"] == "object" and poc["kind"] == "object":
        l_ifaces = set(legacy.get("interfaces", []))
        p_ifaces = set(poc.get("interfaces", []))
        if l_ifaces != p_ifaces:
            out["interfaces_only_in_legacy"] = sorted(l_ifaces - p_ifaces)
            out["interfaces_only_in_poc"] = sorted(p_ifaces - l_ifaces)

    return out


def _diff_input(legacy: dict, poc: dict) -> dict:
    l_fields = legacy["fields"]
    p_fields = poc["fields"]
    l_names = set(l_fields.keys())
    p_names = set(p_fields.keys())

    out = {}
    only_l = sorted(l_names - p_names)
    only_p = sorted(p_names - l_names)
    if only_l:
        out["fields_only_in_legacy"] = only_l
    if only_p:
        out["fields_only_in_poc"] = only_p

    type_mismatches = {
        name: (l_fields[name], p_fields[name]) for name in l_names & p_names if l_fields[name] != p_fields[name]
    }
    if type_mismatches:
        out["field_type_mismatches"] = type_mismatches
    return out


def _diff_enum(legacy: dict, poc: dict) -> dict:
    l_vals = set(legacy["values"])
    p_vals = set(poc["values"])
    out = {}
    if l_vals - p_vals:
        out["values_only_in_legacy"] = sorted(l_vals - p_vals)
    if p_vals - l_vals:
        out["values_only_in_poc"] = sorted(p_vals - l_vals)
    return out


def _diff_union(legacy: dict, poc: dict) -> dict:
    l_mems = set(legacy["members"])
    p_mems = set(poc["members"])
    out = {}
    if l_mems - p_mems:
        out["members_only_in_legacy"] = sorted(l_mems - p_mems)
    if p_mems - l_mems:
        out["members_only_in_poc"] = sorted(p_mems - l_mems)
    return out


def diff_schemas(legacy_sdl: str, poc_sdl: str) -> dict:
    """Top-level diff. Returns a dict with the divergences between the two SDL inputs."""
    legacy = extract_types(legacy_sdl)
    poc = extract_types(poc_sdl)

    legacy_names = set(legacy.keys())
    poc_names = set(poc.keys())
    in_both = legacy_names & poc_names

    type_diffs: dict[str, dict] = {}
    for name in sorted(in_both):
        leg = legacy[name]
        p = poc[name]
        if leg["kind"] != p["kind"]:
            type_diffs[name] = {"kind_mismatch": (leg["kind"], p["kind"])}
            continue
        kind = leg["kind"]
        if kind in ("object", "interface"):
            d = _diff_object_or_interface(leg, p)
        elif kind == "input":
            d = _diff_input(leg, p)
        elif kind == "enum":
            d = _diff_enum(leg, p)
        elif kind == "union":
            d = _diff_union(leg, p)
        else:
            d = {}
        if d:
            type_diffs[name] = d

    return {
        "types_only_in_legacy": sorted(legacy_names - poc_names),
        "types_only_in_poc": sorted(poc_names - legacy_names),
        "type_diffs": type_diffs,
    }


def has_any_diff(diff: dict) -> bool:
    return bool(diff["types_only_in_legacy"] or diff["types_only_in_poc"] or diff["type_diffs"])


def format_report(diff: dict) -> str:
    """Render a diff dict as markdown."""
    lines: list[str] = ["# Schema Parity Report", ""]

    if diff["types_only_in_legacy"]:
        lines.append(f"## Types in legacy but not in POC ({len(diff['types_only_in_legacy'])})")
        for t in diff["types_only_in_legacy"]:
            lines.append(f"- `{t}`")
        lines.append("")

    if diff["types_only_in_poc"]:
        lines.append(f"## Types in POC but not in legacy ({len(diff['types_only_in_poc'])})")
        for t in diff["types_only_in_poc"]:
            lines.append(f"- `{t}`")
        lines.append("")

    if diff["type_diffs"]:
        lines.append(f"## Per-type differences ({len(diff['type_diffs'])} types)")
        for name in sorted(diff["type_diffs"]):
            d = diff["type_diffs"][name]
            lines.append(f"\n### `{name}`")
            if "kind_mismatch" in d:
                lk, pk = d["kind_mismatch"]
                lines.append(f"- **kind differs**: legacy=`{lk}` poc=`{pk}`")
                continue
            for key, label in (
                ("fields_only_in_legacy", "Fields only in legacy"),
                ("fields_only_in_poc", "Fields only in POC"),
                ("values_only_in_legacy", "Enum values only in legacy"),
                ("values_only_in_poc", "Enum values only in POC"),
                ("members_only_in_legacy", "Union members only in legacy"),
                ("members_only_in_poc", "Union members only in POC"),
                ("interfaces_only_in_legacy", "Interfaces only in legacy"),
                ("interfaces_only_in_poc", "Interfaces only in POC"),
            ):
                if d.get(key):
                    lines.append(f"- **{label}:**")
                    for item in d[key]:
                        lines.append(f"  - `{item}`")
            if d.get("field_type_mismatches"):
                lines.append("- **Field type mismatches (legacy → poc):**")
                for f, (lt, pt) in sorted(d["field_type_mismatches"].items()):
                    lines.append(f"  - `{f}`: `{lt}` → `{pt}`")
            if d.get("field_arg_mismatches"):
                lines.append("- **Field argument mismatches:**")
                for f, am in sorted(d["field_arg_mismatches"].items()):
                    parts = []
                    if am.get("args_only_in_legacy"):
                        parts.append(f"only-legacy={am['args_only_in_legacy']}")
                    if am.get("args_only_in_poc"):
                        parts.append(f"only-poc={am['args_only_in_poc']}")
                    if am.get("arg_type_mismatches"):
                        parts.append(f"type-mismatches={am['arg_type_mismatches']}")
                    lines.append(f"  - `{f}`: {'; '.join(parts)}")

    if not has_any_diff(diff):
        lines.append("✅ Schemas are at full parity (no divergences detected).")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diff a legacy GraphQL SDL against a Strawberry POC SDL")
    parser.add_argument("legacy", help="Path to legacy SDL file")
    parser.add_argument("poc", help="Path to POC SDL file")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with status 1 if any divergence is found (suitable for CI gate)",
    )
    args = parser.parse_args(argv)

    legacy_sdl = Path(args.legacy).read_text()
    poc_sdl = Path(args.poc).read_text()

    diff = diff_schemas(legacy_sdl, poc_sdl)

    if args.format == "json":
        sys.stdout.write(json.dumps(diff, indent=2, default=str))
    else:
        sys.stdout.write(format_report(diff))

    if args.fail_on_diff and has_any_diff(diff):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
