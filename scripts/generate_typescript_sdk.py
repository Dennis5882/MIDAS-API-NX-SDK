"""Generate the language-neutral endpoint manifest and TypeScript resources.

The Python implementation currently carries the reviewed endpoint metadata
(`ENDPOINT`, `NAME`, `PRODUCTS`, `METHODS`) while ``docs/coverage.json`` carries
the official-manual provenance and live-verification ledger.  This generator
joins those two sources so the npm SDK cannot silently drift from PyPI.

Generated files are committed.  CI reruns this script and fails if the working
tree changes, making an official-manual/Python update visible to both SDKs.
"""

from __future__ import annotations

import ast
import importlib
import json
import pkgutil
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = ROOT / "src"
TYPESCRIPT_SRC = ROOT / "packages" / "typescript" / "src"
SCHEMA_DIR = ROOT / "schema"

_DOC_ENDPOINTS = {
    "/doc/NEW", "/doc/OPEN", "/doc/CLOSE", "/doc/SAVE", "/doc/SAVEAS",
    "/doc/STAGAS", "/doc/IMPORT", "/doc/IMPORTMXT", "/doc/EXPORT",
    "/doc/EXPORTMXT", "/doc/ANAL",
}
_DESIGN_TABLE_ENDPOINTS = {
    "/DESIGN/RC/KDS-41-20-2022/TABLE",
    "/DESIGN/SRC/AIK-SRC2K/TABLE",
}
_POST_TABLE_LEDGER_ALIASES = {
    "/post/BEAMDESIGNFORCES", "/post/COLUMNDESIGNFORCES",
    "/post/BRACEDESIGNFORCES", "/post/WALLDESIGNFORCES",
    "/post/STEELMEMBERDESIGNFORCES", "/post/SRCBEAMDESIGNFORCES",
    "/post/SRCCOLUMNDESIGNFORCES",
    "/post/COLDFORMEDSTEELMEMBERDESIGNFORCES",
}
_TABLE_OPTION_NAMES = {
    "table_name": "tableName",
    "export_path": "exportPath",
    "node_elems": "nodeElements",
    "unit": "unit",
    "styles": "styles",
    "components": "components",
    "load_case_names": "loadCaseNames",
    "opt_cs": "constructionStage",
    "stage_step": "stageSteps",
    "parts": "parts",
    "story_names": "storyNames",
    "modes": "modes",
    "additional": "additional",
    "set_calculation_method": "calculationMethod",
}


def _all_subclasses(base: type) -> list[type]:
    found: list[type] = []
    for child in base.__subclasses__():
        found.append(child)
        found.extend(_all_subclasses(child))
    return found


def _camel(value: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    if not parts:
        return "resource"
    first, *rest = parts
    return first[:1].lower() + first[1:] + "".join(p[:1].upper() + p[1:] for p in rest)


def _jsdoc(value: str, indent: int) -> list[str]:
    """Render reviewed Python endpoint documentation into TypeScript JSDoc."""
    if not value.strip():
        return []
    pad = "  " * indent
    lines = [f"{pad}/**"]
    for raw_line in value.replace("*/", "* /").splitlines():
        # Some historical Python sources contain mojibake warning glyphs from
        # an older Windows encoding. Keep npm declarations readable and turn
        # a damaged leading marker into an explicit warning label.
        marker = ""
        if "\u26a0" in raw_line or "\U0001f6d1" in raw_line:
            marker = "WARNING: "
        elif "\u2705" in raw_line:
            marker = "VERIFIED: "
        normalized = (
            raw_line.replace("\u2014", " - ")
            .replace("\u2013", " - ")
            .replace("\u2192", " -> ")
            .replace("\u00b0", " degrees ")
        )
        line = re.sub(r"[^\x09\x20-\x7e]", "", normalized).rstrip()
        line = re.sub(r"^(\s*)\?+\s*", r"\1WARNING: ", line)
        line = re.sub(r"\s+\?+\s+", " - ", line)
        if marker:
            line = re.sub(r"^(\s*)", rf"\1{marker}", line, count=1)
        lines.append(f"{pad} * {line}" if line.strip() else f"{pad} *")
    lines.append(f"{pad} */")
    return lines


def _module_parts(module: str) -> list[str]:
    return [_camel(part) for part in module.removeprefix("midas_nx.").split(".")]


def _namespace(module: str) -> str:
    parts = module.removeprefix("midas_nx.").split(".")
    return "".join(part[:1].upper() + _camel(part)[1:] for part in parts) + "Types"


def _source_modules() -> dict[str, ast.Module]:
    modules: dict[str, ast.Module] = {}
    for path in sorted(PYTHON_SRC.joinpath("midas_nx").rglob("*.py")):
        relative = path.relative_to(PYTHON_SRC).with_suffix("")
        parts = list(relative.parts)
        if parts[-1] == "__init__":
            parts.pop()
        module = ".".join(parts)
        if not module:
            continue
        modules[module] = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return modules


def _import_map(module: str, tree: ast.Module) -> dict[str, tuple[str, str]]:
    imports: dict[str, tuple[str, str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            base = module.split(".")[: -node.level]
            if node.module:
                base.extend(node.module.split("."))
            origin = ".".join(base)
        else:
            origin = node.module or ""
        for alias in node.names:
            imports[alias.asname or alias.name] = (origin, alias.name)
    return imports


def _collect_type_classes(
    modules: dict[str, ast.Module], resource_keys: set[tuple[str, str]]
) -> set[tuple[str, str]]:
    imports = {module: _import_map(module, tree) for module, tree in modules.items()}
    classes = {
        (module, node.name): node
        for module, tree in modules.items()
        for node in tree.body
        if isinstance(node, ast.ClassDef) and (module, node.name) not in resource_keys
    }
    typed: set[tuple[str, str]] = set()
    for key, node in classes.items():
        if any(ast.unparse(base).split(".")[-1] == "TypedDict" for base in node.bases):
            typed.add(key)

    changed = True
    while changed:
        changed = False
        for key, node in classes.items():
            if key in typed:
                continue
            module, _ = key
            for base in node.bases:
                if not isinstance(base, ast.Name):
                    continue
                resolved = imports[module].get(base.id, (module, base.id))
                if resolved in typed:
                    typed.add(key)
                    changed = True
                    break
    return typed


def _unwrap_required(annotation: ast.expr) -> tuple[ast.expr, bool | None]:
    if isinstance(annotation, ast.Subscript):
        name = ast.unparse(annotation.value).split(".")[-1]
        if name == "NotRequired":
            return annotation.slice, False
        if name == "Required":
            return annotation.slice, True
    return annotation, None


def _type_expression(
    node: ast.expr,
    *,
    module: str,
    local_types: set[str],
    imports: dict[str, tuple[str, str]],
    all_types: set[tuple[str, str]],
) -> str:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            try:
                parsed = ast.parse(node.value, mode="eval").body
            except SyntaxError:
                return "unknown"
            return _type_expression(
                parsed,
                module=module,
                local_types=local_types,
                imports=imports,
                all_types=all_types,
            )
        if node.value is None:
            return "null"
        if isinstance(node.value, (str, int, float, bool)):
            return json.dumps(node.value)
        if node.value is Ellipsis:
            return "unknown"
    if isinstance(node, ast.Name):
        primitives = {
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "Any": "unknown",
            "object": "unknown",
            "None": "null",
            "dict": "JsonObject",
            "Mapping": "JsonObject",
        }
        if node.id in primitives:
            return primitives[node.id]
        if node.id in local_types:
            return node.id
        origin = imports.get(node.id)
        if origin in all_types:
            return f"{_namespace(origin[0])}.{origin[1]}"
        return "unknown"
    if isinstance(node, ast.Attribute):
        return _type_expression(
            ast.Name(id=node.attr),
            module=module,
            local_types=local_types,
            imports=imports,
            all_types=all_types,
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _type_expression(node.left, module=module, local_types=local_types, imports=imports, all_types=all_types)
        right = _type_expression(node.right, module=module, local_types=local_types, imports=imports, all_types=all_types)
        return f"{left} | {right}"
    if isinstance(node, ast.Subscript):
        name = ast.unparse(node.value).split(".")[-1]
        slice_node = node.slice
        if name in {"Optional"}:
            inner = _type_expression(slice_node, module=module, local_types=local_types, imports=imports, all_types=all_types)
            return f"{inner} | null"
        if name in {"List", "list", "Sequence", "Iterable"}:
            inner = _type_expression(slice_node, module=module, local_types=local_types, imports=imports, all_types=all_types)
            return f"Array<{inner}>"
        if name in {"Dict", "dict", "Mapping", "MutableMapping"}:
            args = slice_node.elts if isinstance(slice_node, ast.Tuple) else [ast.Name(id="str"), slice_node]
            value = _type_expression(args[-1], module=module, local_types=local_types, imports=imports, all_types=all_types)
            return f"Record<string, {value}>"
        if name in {"Union", "Literal"}:
            args = slice_node.elts if isinstance(slice_node, ast.Tuple) else [slice_node]
            rendered = [
                _type_expression(arg, module=module, local_types=local_types, imports=imports, all_types=all_types)
                for arg in args
            ]
            return " | ".join(dict.fromkeys(rendered))
        if name in {"Tuple", "tuple"}:
            args = slice_node.elts if isinstance(slice_node, ast.Tuple) else [slice_node]
            if len(args) == 2 and isinstance(args[1], ast.Constant) and args[1].value is Ellipsis:
                inner = _type_expression(args[0], module=module, local_types=local_types, imports=imports, all_types=all_types)
                return f"Array<{inner}>"
            return "[" + ", ".join(
                _type_expression(arg, module=module, local_types=local_types, imports=imports, all_types=all_types)
                for arg in args
            ) + "]"
        if name in {"Required", "NotRequired", "ClassVar"}:
            return _type_expression(slice_node, module=module, local_types=local_types, imports=imports, all_types=all_types)
    return "unknown"


_CONTRACT_TS_TYPES = {
    "string": "string",
    "number": "number",
    "integer": "number",
    "boolean": "boolean",
    "object": "JsonObject",
}


def _contract_field_type(
    field: dict[str, Any],
    indent: str,
    attach: dict[str, list[str]] | None = None,
    path: str = "",
) -> str:
    """Render one contract field as a TypeScript type.

    ``attach`` carries variant unions down to the fields that hold their
    discriminators, keyed by dotted field path so a gate nested several levels
    down attaches where it belongs rather than at the nearest root. Where one
    lands, the union is intersected with that object - inside the element type
    when the field is an array. See ``_contract_payload_type``.
    """
    kind = field.get("type")
    # `key` is absent when a caller renders a bare type rather than a member.
    key = field.get("key", "")
    here = f"{path}.{key}" if path else key
    branches = (attach or {}).get(here) if here else None
    if field.get("properties"):
        body = _contract_interface_body(field["properties"], indent + "  ", attach, here)
        inner = "{\n" + body + f"\n{indent}}}"
        if branches:
            union = "\n".join(f"{indent}  {line}" for line in branches)
            inner += " & (\n" + union + f"\n{indent})"
            if kind == "array":
                inner = f"({inner})"
        return f"Array<{inner}>" if kind == "array" else inner
    if kind == "array":
        item = (field.get("items") or {}).get("type")
        rendered_item = _CONTRACT_TS_TYPES.get(item, "unknown")
        minimum = field.get("minItems")
        maximum = field.get("maxItems")
        # A matching pair of bounds is an exact contract fact, not a runtime
        # guess. Preserve it as a tuple so TypeScript callers cannot submit a
        # too-short vector to a field such as /db/BODF's FV.
        if isinstance(minimum, int) and minimum == maximum:
            return "[" + ", ".join([rendered_item] * minimum) + "]"
        return f"Array<{rendered_item}>"
    if field.get("enum") and kind == "string":
        return " | ".join(f'"{value}"' for value in field["enum"])
    return _CONTRACT_TS_TYPES.get(kind, "unknown")


def _condition_text(entry: dict[str, Any]) -> str:
    """Render one `appliesWhen` entry, in either form the schema allows."""

    if "in" in entry:
        values = " or ".join(json.dumps(value) for value in entry["in"])
        return f"{entry['path']} is {values}"
    return f"{entry['path']} = {json.dumps(entry['equals'])}"


def _contract_interface_body(
    fields: list[dict[str, Any]],
    indent: str,
    attach: dict[str, list[str]] | None = None,
    path: str = "",
) -> str:
    lines: list[str] = []
    for field in fields:
        applies_when = field.get("appliesWhen", [])
        # The contract knows requiredness; the Python TypedDicts are all
        # `total=False`, so every field they produced was optional regardless
        # of what the manual said. This is the reversal paying for itself.
        #
        # A field the manual requires *within one branch* is not one every
        # payload carries, though. Typing it unconditionally required made
        # `/db/CCFC` demand `COEF` (only under TYPE="CONST") alongside
        # `SCALE_FACTOR` and `ITEM` (only under TYPE="USER"): no caller could
        # satisfy the type without sending fields their own branch does not
        # have. 49 fields across nine contracts were in that state, `/db/EPMT`
        # asking for all six plasticity models at once. The condition moves
        # into the doc comment, which is where a requiredness TypeScript
        # cannot express belongs.
        optional = "" if field.get("requirement") == "required" and not applies_when else "?"
        documentation = []
        if field.get("description"):
            documentation.append(" ".join(field["description"].split()))
        if applies_when:
            rendered = " and ".join(_condition_text(entry) for entry in applies_when)
            verb = "Required when" if field.get("requirement") == "required" else "Applies when"
            documentation.append(f"{verb} {rendered}.")
        if documentation:
            lines.append(f"{indent}/** {' '.join(documentation)} */")
        lines.append(
            f"{indent}{field['key']}{optional}: "
            f"{_contract_field_type(field, indent, attach, path)};"
        )
    return "\n".join(lines)


def _contract_payload_type(name: str, contract: dict[str, Any]) -> list[str]:
    """Render a contract payload without flattening conditional branches.

    A contract variant is a manual statement about one wire discriminator.  A
    TypeScript intersection with a discriminated union keeps that fact visible:
    callers must choose one documented branch instead of being offered a
    misleading interface containing every branch's fields at once.

    A variant's fields are siblings of the field it gates on, so each union
    attaches where its own discriminator lives - and only a root-level
    discriminator makes that the payload root. Six contracts gate on a field
    the manual nests: ``/db/SWIND`` and ``/db/SSEIS`` inside ``PARAMETERS``,
    ``/db/PRES``, ``/db/MCON`` and the KDS column-rebar endpoint inside an
    array element. Attaching those at the root published ``WIND_SPEED``,
    ``EXP_CATEGORY`` and ``PERIOD_APPR_X`` as top-level payload members, which
    is where the server does not look - the same defect the ``/db/BTMP``
    nesting fix corrected one level further down.

    Two of them branch on **two** axes at two depths: ``/db/SWIND`` selects a
    ``PARAMETERS`` shape with the root ``WIND_CODE`` and then branches again on
    ``PARAMETERS.INPUT_METHOD``. So the variants are grouped by where they
    attach and each group becomes its own union, rather than one union per
    contract.
    """

    fields = contract["fields"]
    variants = contract.get("variants", [])
    lines = ["  /** Generated from contracts/endpoints/. */"]
    if not variants:
        lines.append(f"  export interface {name} {{")
        lines.append(_contract_interface_body(fields, "    "))
        lines.append("  }")
        return lines

    groups: dict[str | None, list[dict[str, Any]]] = {}
    for variant in variants:
        groups.setdefault(_variant_attach_key(fields, variant), []).append(variant)

    nested = {
        key: _variant_union(_attach_base(fields, key), group)
        for key, group in groups.items()
        if key is not None
    }
    root = groups.get(None)

    lines.append(f"  export type {name} = {{")
    lines.append(_contract_interface_body(fields, "    ", nested or None))
    if root is None:
        lines.append("  };")
        return lines
    lines.append("  } & (")
    lines.extend(f"    {line}" for line in _variant_union(fields, root))
    lines.append("  );")
    return lines


def _attach_base(fields: list[dict[str, Any]], path: str) -> list[dict[str, Any]]:
    """The declared members of the object a nested union attaches to.

    Exhaustiveness is judged against the discriminator's own declaration, so it
    has to be looked up beside the branch rather than at the payload root.
    """
    for step in path.split("."):
        fields = next(
            (field.get("properties") or [] for field in fields if field["key"] == step), []
        )
    return fields


def _variant_union(base: list[dict[str, Any]], variants: list[dict[str, Any]]) -> list[str]:
    """One discriminated union, rendered without a leading indent.

    The caller decides how far in it sits, which is what lets the same union be
    emitted at the payload root or spliced into a nested object.
    """
    # A multi-value table is the manual's *shared* table only when it overlaps
    # another one: /db/FBLA states a table for ``FLOOR_DIST_TYPE = 1 or 2``
    # alongside its ``= 1`` and ``= 2`` tables, and emitting that as its own
    # union member would make two members match the same discriminator. Fold
    # its fields into every branch it covers instead.
    #
    # Overlap is what decides it, not the plural on its own. A table naming
    # several values that no other table names is an ordinary branch that
    # happens to cover more than one value - /db/PRES's ``FACE_EDGE_TYPE =
    # "FACE" or "PRES"`` against its separate ``= "EDGE"``. Treating every
    # plural table as shared dropped those branches entirely, because folding
    # keeps only the single-value ones: /db/PRES lost FORCES, /db/MVHL lost the
    # South African VEH_ZA, and /db/TDME lost four of its six code branches.
    shared = [
        v
        for v in variants
        if any("in" in c for c in v["when"])
        and any(_shared_covers(v["when"], other["when"]) for other in variants if other is not v)
    ]
    branches = [v for v in variants if v not in shared]
    if shared and branches:
        variants = [
            {**branch, "fields": branch["fields"] + [
                field
                for extra in shared
                if _shared_covers(extra["when"], branch["when"])
                for field in extra["fields"]
            ]}
            for branch in branches
        ]

    # A union of only the documented branches says every other value of the
    # discriminator is illegal, and the manual rarely gives a table for all of
    # them: /db/FBLA documents FLOOR_DIST_TYPE 1 to 4 and supplies tables for 1
    # and 2, so 3 and 4 became untypeable. Exhaustiveness has to be proven, not
    # assumed - a declared enum the branches cover exactly, or both values of a
    # boolean. Otherwise a trailing member carries the remaining values, and
    # denies each branch's own fields so a wrong-branch field is still an
    # error. Widening the enums the extractor cannot yet read is what would
    # narrow these unions again.
    base_by_key = {field["key"]: field for field in base}
    selectors: dict[str, set[str]] = {}
    for variant in variants:
        for condition in variant["when"]:
            if "." in condition["path"]:
                continue
            values = condition["in"] if "in" in condition else [condition["equals"]]
            selectors.setdefault(condition["path"], set()).update(
                json.dumps(value) for value in values
            )
    residual = [
        key
        for key in dict.fromkeys(
            field["key"] for variant in variants for field in variant["fields"]
        )
        if key not in base_by_key and key not in selectors
    ]
    exhaustive = all(
        _selector_is_exhaustive(base_by_key.get(path), values)
        for path, values in selectors.items()
    )

    lines: list[str] = []
    for index, variant in enumerate(variants):
        conditions = variant["when"]
        lines.append("{")
        # A condition path may be nested (``STR.SPEC_CODE``). Only a
        # discriminator declared beside this branch can be narrowed as one of
        # its properties; a deeper one is documentation the branch body already
        # carries, so it is not emitted twice.
        roots = [c for c in conditions if "." not in c["path"]]
        for condition in roots:
            if "in" in condition:
                union = " | ".join(json.dumps(value) for value in condition["in"])
                lines.append(f"  {condition['path']}: {union};")
            else:
                lines.append(f"  {condition['path']}: {json.dumps(condition['equals'])};")
        # A manually transcribed variant table often repeats its discriminator
        # as the first row (for example ``iMETHOD = 2`` followed by an
        # ``iMETHOD`` parameter row). The literal branch discriminator is the
        # more precise declaration; rendering the repeated general field would
        # create an illegal duplicate TypeScript property.
        narrowed = {condition["path"] for condition in roots}
        branch_fields = [field for field in variant["fields"] if field.get("key") not in narrowed]
        # One entry per line, because the caller indents this union line by
        # line to place it - a joined block would keep its own indentation and
        # land at the wrong depth wherever the union is not at the root.
        lines.extend(_contract_interface_body(branch_fields, "  ").splitlines())
        last = index == len(variants) - 1 and exhaustive
        lines.append("}" + ("" if last else " |"))
    if not exhaustive:
        lines.append("{")
        for key in residual:
            lines.append(f"  {key}?: never;")
        lines.append("}")
    return lines


def _variant_attach_key(fields: list[dict[str, Any]], variant: dict[str, Any]) -> str | None:
    """The dotted path of the object whose members this variant's fields join.

    That is the object holding its discriminator, at whatever depth the
    contract declares it - a gate found only at the nearest root would attach
    the branch above the object it belongs to, which is the bug this returns a
    full path to avoid.

    ``None`` means the payload root, either because the gate is a root field or
    because the contract declares it nowhere. The second case is left where it
    already was rather than given an invented home: ``/db/MVLD``'s
    ``LOAD_MODEL`` is declared inside a sibling variant, and no permitted source
    says which object holds it.

    A variant gating on two fields at two depths would have no single place to
    attach. None does, and one appearing is a contract to look at rather than a
    default to pick, so it raises.
    """
    attachments = set()
    for condition in variant["when"]:
        # Gates come in both spellings the corpus uses: a bare field name that
        # may live anywhere (`FACE_EDGE_TYPE`) and a path already rooted at the
        # payload (`PARAMETERS.INPUT_METHOD`). Resolving the last segment
        # against the contract's own tree answers both, and answers with the
        # canonical path rather than trusting the spelling.
        found = _field_path(fields, condition["path"].rsplit(".", 1)[-1])
        # The array marker is a rendering detail; the attach point is the field.
        parent = found.rsplit(".", 1)[0].replace("[]", "") if found and "." in found else None
        attachments.add(parent)
    if len(attachments) != 1:
        raise ValueError(
            "one variant's discriminators sit at different depths, so its branch "
            f"has no single place to attach: {sorted(c['path'] for c in variant['when'])}"
        )
    return attachments.pop()


def _selector_is_exhaustive(field: dict[str, Any] | None, values: set[str]) -> bool:
    """Whether the branches provably cover every value this selector allows.

    Only two things prove it. A declared ``enum`` is the contract's own list of
    legal values, so branches matching it leave nothing out. A boolean has
    exactly two. A prose description that happens to name three values is not
    evidence: reading it would be inferring the enum, which contracts forbid.
    """

    if field is None:
        return False
    if field.get("type") == "boolean":
        return values == {"true", "false"}
    declared = field.get("enum")
    return bool(declared) and {json.dumps(value) for value in declared} == values


def _shared_covers(shared_when: list[dict], branch_when: list[dict]) -> bool:
    """Whether a shared multi-value table applies to this single-value branch.

    True when every condition of the branch is satisfied by the shared table's
    own conditions on the same path - that is, the branch's value is among the
    values the shared table names.
    """
    by_path = {condition["path"]: condition for condition in shared_when}
    for condition in branch_when:
        extra = by_path.get(condition["path"])
        if extra is None:
            return False
        permitted = extra["in"] if "in" in extra else [extra["equals"]]
        if condition.get("equals") not in permitted:
            return False
    return True


def _is_contract_shadow_resource(endpoint: str) -> bool:
    """Whether this resource family is covered by the contract shadow gate."""

    return endpoint.startswith(("/db/", "/DESIGN/"))


def _contract_payload_fields() -> dict[str, dict[str, Any]]:
    """Payload fields for the contract-derived resource shadow path.

    Plain-function contracts are still parity-only in this migration stage.
    Letting them alter the generated npm types would begin the Stage 3 generator
    switch before its byte-identical shadow check has been completed.
    """
    contract_dir = ROOT / "contracts" / "endpoints"
    if not contract_dir.is_dir():
        return {}
    import yaml  # noqa: PLC0415

    found: dict[str, dict[str, Any]] = {}
    for path in sorted(contract_dir.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        # A contract carrying unmergedTables knows it is incomplete: the manual
        # names no wire discriminator for one of its tables. Its field list is
        # still worth having in the source of truth, but narrowing a published
        # payload type onto an admittedly partial list would break callers who
        # set a field the manual documents in the table nobody could merge.
        unmerged = (contract.get("extraction") or {}).get("unmergedTables")
        if (
            _is_contract_shadow_resource(contract.get("endpoint", ""))
            and contract.get("fields")
            and not unmerged
        ):
            found[contract["endpoint"]] = {
                "fields": contract["fields"],
                "variants": contract.get("variants", []),
            }
    return found


def _render_types(
    modules: dict[str, ast.Module],
    type_keys: set[tuple[str, str]],
    contract_types: dict[tuple[str, str], dict[str, Any]] | None = None,
    supplemental_contract_types: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> str:
    contract_types = contract_types or {}
    supplemental_contract_types = supplemental_contract_types or {}
    chunks = [
        "// Generated by scripts/generate_typescript_sdk.py. Do not edit by hand.",
        'import type { JsonObject } from "../types";',
        "",
    ]
    for module, tree in sorted(modules.items()):
        module_types = {name for owner, name in type_keys if owner == module}
        if not module_types:
            continue
        imports = _import_map(module, tree)
        chunks.append(f"export namespace {_namespace(module)} {{")
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or (module, node.name) not in type_keys:
                continue
            contract = contract_types.get((module, node.name))
            if contract is not None:
                # Sourced from the contract, not from this Python class. The
                # class only supplies the name and where it sits, so the two
                # SDKs keep the type names they already publish.
                chunks.extend(_contract_payload_type(node.name, contract))
                continue
            total = not any(
                keyword.arg == "total" and isinstance(keyword.value, ast.Constant) and keyword.value.value is False
                for keyword in node.keywords
            )
            bases: list[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id != "TypedDict":
                    rendered = _type_expression(base, module=module, local_types=module_types, imports=imports, all_types=type_keys)
                    if rendered != "unknown":
                        bases.append(rendered)
            extends = f" extends {', '.join(bases)}" if bases else ""
            chunks.append(f"  export interface {node.name}{extends} {{")
            for field in node.body:
                if not isinstance(field, ast.AnnAssign) or not isinstance(field.target, ast.Name):
                    continue
                annotation, explicit_required = _unwrap_required(field.annotation)
                required = total if explicit_required is None else explicit_required
                rendered = _type_expression(
                    annotation,
                    module=module,
                    local_types=module_types,
                    imports=imports,
                    all_types=type_keys,
                )
                optional = "" if required else "?"
                chunks.append(f"    {field.target.id}{optional}: {rendered};")
            chunks.append("  }")
        for name, contract in sorted(supplemental_contract_types.get(module, {}).items()):
            chunks.extend(_contract_payload_type(name, contract))
        chunks.append("}")
        chunks.append("")
    return "\n".join(chunks)


def _contract_payload_defaults() -> dict[str, dict[str, Any]]:
    """Read ``normalize_defaults`` rules out of contracts/endpoints/*.yaml.

    Payload normalization is *behaviour*, not metadata, which is precisely why
    it never survived the trip from Python to TypeScript: ``/db/NMAS``'s
    rmX/rmY/rmZ workaround lived inside ``NodalMass.create()``, so the npm
    package shipped a month after that fix without it and could still kill a
    live NX session. Reading the rule from the language-neutral contract instead
    means neither SDK can be the one that has it.

    Contracts are optional here on purpose: they are being introduced endpoint by
    endpoint, and an endpoint without one simply gets no defaults.
    ``scripts/validate_contracts.py`` is what fails CI when a contract exists and
    an SDK does not honour it.
    """
    contract_dir = ROOT / "contracts" / "endpoints"
    if not contract_dir.is_dir():
        return {}
    try:
        import yaml  # noqa: PLC0415
    except ImportError:  # pragma: no cover - dev dependency
        raise SystemExit(
            "contracts/ is present but PyYAML is not installed. "
            'Run: pip install -e ".[dev]"'
        ) from None

    defaults: dict[str, dict[str, Any]] = {}
    for path in sorted(contract_dir.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        merged: dict[str, Any] = {}
        for rule in contract.get("sdkRules", []):
            if rule.get("kind") == "normalize_defaults":
                merged.update(rule.get("values", {}))
        if merged:
            defaults[contract["endpoint"]] = merged
    return defaults


# Metadata keys that change what DbResource does at runtime, as opposed to
# describing the endpoint. Every one is derived from a contract rule.
_RUNTIME_BEHAVIOUR_KEYS = ("payloadDefaults", "rejectEmptyFields", "requiredExplicitFields")


def _field_path(fields: list[dict[str, Any]], key: str, prefix: str = "") -> str | None:
    """Where a contract declares ``key``, written the way a runtime walks it.

    An array field becomes ``ITEMS[].DIRECTION`` and an object field
    ``PARENT.CHILD``, so a rule that names a bare field key still reaches the
    right place when the manual nests it. Returns None when the contract does
    not declare the key at all, which the caller turns into an error rather
    than a silently skipped rule.
    """
    for field in fields or []:
        step = "[]" if field.get("type") == "array" else ""
        here = f"{prefix}{field['key']}"
        if field["key"] == key:
            return here
        found = _field_path(field.get("properties") or [], key, f"{here}{step}.")
        if found is not None:
            return found
    return None


def _contract_reject_rules() -> dict[str, dict[str, list[str]]]:
    """Read ``reject_request`` rules, split by what each one actually refuses.

    The sibling of ``_contract_payload_defaults()`` and there for the same
    reason: a rule written in one language reaches one language's users.

    ``rejects`` is what keeps the two apart, and it is a contract field rather
    than a guess because the kind alone does not say which check to run.
    ``empty_value`` is ``/db/MVHL``'s ``VEH_DEFAULT: {}`` - accepted by the
    server, stored as nothing, answered with a success-shaped body.
    ``omission`` is ``/db/PRES``'s ``DIRECTION`` - absent, so the server
    applies a documented default it then refuses. Running either check on the
    other's fields would be wrong in both directions.
    ``forbidden_combination`` travels to neither: those rules name several
    fields that are individually valid, and no generic runtime check follows
    from a field list alone.

    Field names are resolved against the contract's own field tree, so a rule
    may name the key the manual uses and the runtime still receives the path.
    """
    contract_dir = ROOT / "contracts" / "endpoints"
    if not contract_dir.is_dir():
        return {}
    import yaml  # noqa: PLC0415

    wanted = {"empty_value": "rejectEmptyFields", "omission": "requiredExplicitFields"}
    rules: dict[str, dict[str, list[str]]] = {}
    for path in sorted(contract_dir.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        for rule in contract.get("sdkRules", []):
            if rule.get("kind") != "reject_request":
                continue
            metadata_key = wanted.get(rule.get("rejects"))
            if metadata_key is None:
                continue
            for name in rule.get("fields", []):
                resolved = _field_path(contract.get("fields", []), name)
                if resolved is None:
                    raise ValueError(
                        f"{path.name}: sdkRule {rule['id']} names the field "
                        f"{name!r}, which the contract does not declare"
                    )
                bucket = rules.setdefault(contract["endpoint"], {}).setdefault(
                    metadata_key, []
                )
                if resolved not in bucket:
                    bucket.append(resolved)
    return rules


def _contract_resource_surfaces(resource_endpoints: set[str]) -> dict[str, dict[str, Any]]:
    """Read the contract-owned surface of each contracted resource.

    Class and module names remain compatibility anchors while the public npm
    tree is still organised like the existing SDK.  The endpoint, display
    name, products, methods and manual chapter are contract facts.  Keeping
    those two roles separate lets this Stage 3 shadow run replace only facts
    the contract actually owns, and leaves an uncontracted resource on the
    previous Python fallback path.
    """

    contract_dir = ROOT / "contracts" / "endpoints"
    if not contract_dir.is_dir():
        return {}
    try:
        import yaml  # noqa: PLC0415
    except ImportError:  # pragma: no cover - dev dependency
        raise SystemExit(
            "contracts/ is present but PyYAML is not installed. "
            'Run: pip install -e "[dev]"'
        ) from None

    surfaces: dict[str, dict[str, Any]] = {}
    for path in sorted(contract_dir.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        endpoint = contract.get("endpoint", "")
        if (
            not _is_contract_shadow_resource(endpoint)
            or endpoint not in resource_endpoints
            or not contract.get("fields")
        ):
            continue
        if endpoint in surfaces:
            raise ValueError(f"Duplicate resource contract for {endpoint}")
        surfaces[endpoint] = {
            "name": contract["name"],
            "products": sorted(contract["products"]),
            "methods": sorted({operation["method"] for operation in contract["operations"]}),
            "manualChapter": contract["source"]["manual"].get("chapterFile"),
        }
        # The published npm names, where the contract has taken ownership of
        # them. They are seeded from this generator's own committed output, so
        # they rename nothing; recording them is what stops a Python module
        # move from silently renaming an npm export.
        for key, value in (contract.get("surface") or {}).items():
            surfaces[endpoint][key] = value
    return surfaces


def _contract_resource_mismatches(resource: dict[str, Any], surface: dict[str, Any]) -> list[str]:
    """Compare a legacy SDK resource with the facts its contract owns.

    Endpoint labels are manual facts too. The manual and legacy surface use
    different dash typography in a few labels, which is presentation-only, but
    an endpoint string in place of a documented label is still a disagreement.
    """

    chapter = next(
        (manual.get("chapterFile") for manual in resource.get("manual", []) if manual.get("chapterFile")),
        None,
    )
    actual = {
        "name": resource["name"],
        "products": resource["products"],
        "methods": resource["methods"],
        "manualChapter": chapter,
    }
    # `surface` is optional: an endpoint whose contract has not taken the
    # names over stays on the Python fallback, exactly as it does for `name`.
    # Where it is present it is checked, so the two cannot drift apart.
    for key in ("className", "exportName", "modulePath"):
        if key in surface:
            actual[key] = resource.get(key)
    def same_value(key: str) -> bool:
        if key != "name":
            return actual[key] == surface[key]
        return actual[key].replace("\u2013", "-").replace("\u2014", "-") == surface[key].replace(
            "\u2013", "-"
        ).replace("\u2014", "-")

    return [
        f"{key}: SDK has {actual[key]!r}, contract has {surface[key]!r}"
        for key in actual
        if not same_value(key)
    ]


def _check_contract_payload_type_names(resources: list[dict[str, Any]]) -> None:
    """Fail if a contracted payload type name no longer matches the contract.

    Unlike the resource facts, this one cannot be checked while resources are
    loaded: `_attach_payload_types` chooses the name and
    `_contract_payload_types` may still rename it, when one legacy TypedDict
    served several endpoints whose contracts disagree. So it is checked here,
    against the name that will actually be published.
    """

    surfaces = _contract_surface_blocks()
    mismatches = [
        f"{resource['endpoint']}: payload type is "
        f"{resource.get('payloadTypeName')!r}, contract says "
        f"{surfaces[resource['endpoint']]['payloadTypeName']!r}"
        for resource in resources
        if "payloadTypeName" in surfaces.get(resource["endpoint"], {})
        and resource.get("payloadTypeName")
        != surfaces[resource["endpoint"]]["payloadTypeName"]
    ]
    if mismatches:
        raise ValueError(
            "contract surface differs from the generated payload types: "
            + "; ".join(mismatches)
        )


def _contract_surface_blocks() -> dict[str, dict[str, Any]]:
    """Every contract's `surface` block, keyed by endpoint."""

    contract_dir = ROOT / "contracts" / "endpoints"
    if not contract_dir.is_dir():
        return {}
    import yaml  # noqa: PLC0415

    blocks: dict[str, dict[str, Any]] = {}
    for path in sorted(contract_dir.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        surface = contract.get("surface")
        if surface:
            blocks[contract["endpoint"]] = surface
    return blocks


_RESOURCE_IDENTITY_KEYS = (
    "className",
    "exportName",
    "modulePath",
    "name",
    "products",
    "methods",
)


def _resource_identity(
    surface: dict[str, Any] | None, fallback: dict[str, Any] | None
) -> dict[str, Any]:
    """What npm calls a resource, contract first and Python second.

    The precedence is the whole point of the contract migration, so it lives in
    one function rather than inline in a loop: a fact the contract states is the
    fact, and the Python class answers only what no contract has claimed. A
    `fallback` of ``None`` is an endpoint no Python class declares - the contract
    then has to carry every key, and a missing one is a contract defect rather
    than something to guess.
    """

    surface = surface or {}
    fallback = fallback or {}
    identity: dict[str, Any] = {}
    for key in _RESOURCE_IDENTITY_KEYS:
        if key in surface:
            identity[key] = surface[key]
        elif key in fallback:
            identity[key] = fallback[key]
        else:
            raise KeyError(
                f"neither the contract surface nor a Python class supplies {key!r}"
            )
    return identity


_RESOURCE_SOURCE_COUNTS: dict[str, int] = {}


def _python_resource_classes() -> dict[str, dict[str, Any]]:
    """Every `DbResource` subclass the Python package declares, by endpoint.

    This is the *fallback* source now, not the primary one.  An endpoint whose
    contract carries a `surface` block gets its npm identity from the contract;
    this supplies the rest, plus the one fact no contract records - which Python
    module a class lives in, which the payload-type lookup still needs while 497
    of the 750 payload types come from Python TypedDicts rather than contracts.
    """

    sys.path.insert(0, str(PYTHON_SRC))
    import midas_nx  # noqa: PLC0415
    from midas_nx.db.base import DbResource  # noqa: PLC0415

    for module in pkgutil.walk_packages(midas_nx.__path__, midas_nx.__name__ + "."):
        importlib.import_module(module.name)

    classes: dict[str, dict[str, Any]] = {}
    for cls in _all_subclasses(DbResource):
        classes[cls.ENDPOINT] = {
            "className": cls.__name__,
            "exportName": _camel(cls.__name__),
            "endpoint": cls.ENDPOINT,
            "name": cls.NAME or cls.__name__,
            "products": sorted(cls.PRODUCTS),
            "methods": sorted(cls.METHODS),
            "pythonModule": cls.__module__,
            "modulePath": _module_parts(cls.__module__),
        }
    return classes


def _load_resources() -> list[dict[str, Any]]:
    """Build the npm resource list, contracts first and Python second.

    This used to iterate `DbResource` subclasses and let a contract correct the
    facts it owned, which meant a contract could never do more than annotate
    something Python had already declared.  It now iterates contracts that carry
    a `surface` block and takes the endpoint's whole npm identity from there,
    falling back to the Python class only for endpoints no contract covers.

    Python has not stopped mattering: `pythonModule` has no home in a contract
    and the payload-type lookup needs it, so `import midas_nx` is still
    load-bearing.  What changed is the direction - the contract is the source
    and Python fills its gaps, rather than the reverse.
    """

    python_classes = _python_resource_classes()

    coverage = json.loads((ROOT / "docs" / "coverage.json").read_text(encoding="utf-8"))
    coverage_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in coverage["endpoints"]:
        coverage_by_endpoint[entry["endpoint"]].append(entry)

    payload_defaults = _contract_payload_defaults()
    reject_rules = _contract_reject_rules()
    surfaces = _contract_resource_surfaces(set(python_classes))

    resources: list[dict[str, Any]] = []
    from_contract = 0
    for endpoint, fallback in sorted(python_classes.items()):
        manual = [
            {
                "name": match.get("name"),
                "chapterFile": match.get("chapter_file"),
                "status": match.get("status"),
            }
            for match in coverage_by_endpoint.get(endpoint, [])
        ]
        surface = surfaces.get(endpoint)
        if surface is not None:
            # The chapter comparison reads the ledger entry, so it has to
            # see one: the fallback dict is class facts only.
            mismatches = _contract_resource_mismatches({**fallback, "manual": manual}, surface)
            if mismatches:
                raise ValueError(
                    f"{endpoint}: contract resource shadow differs from the SDK: "
                    + "; ".join(mismatches)
                )
            from_contract += 1

        identity = _resource_identity(surface, fallback)
        resource = {
            "className": identity["className"],
            "exportName": identity["exportName"],
            "endpoint": endpoint,
            "name": identity["name"],
            "products": identity["products"],
            "methods": identity["methods"],
            # No contract records this. It is the Python module a class lives
            # in, and the AST payload-type lookup is still keyed by it.
            "pythonModule": fallback["pythonModule"],
            "modulePath": identity["modulePath"],
            # Present only for endpoints with a contract rule; see
            # _contract_payload_defaults().
            **(
                {"payloadDefaults": payload_defaults[endpoint]}
                if endpoint in payload_defaults
                else {}
            ),
            **reject_rules.get(endpoint, {}),
            "manual": manual,
        }
        if surface is not None:
            # Keep the coverage ledger's richer manual entry in the committed
            # manifest. Runtime npm metadata reads this contract-owned chapter.
            resource["contractManualChapter"] = surface["manualChapter"]
        resources.append(resource)

    _RESOURCE_SOURCE_COUNTS["contract"] = from_contract
    _RESOURCE_SOURCE_COUNTS["python"] = len(resources) - from_contract
    return sorted(resources, key=lambda item: (item["pythonModule"], item["className"], item["endpoint"]))


def _render_tree(resources: list[dict[str, Any]]) -> str:
    tree: dict[str, Any] = {}
    for resource in resources:
        node = tree
        for part in resource["modulePath"]:
            node = node.setdefault(part, {})
        name = resource["exportName"]
        if name in node:
            raise ValueError(f"Duplicate TypeScript resource name at {resource['modulePath']}: {name}")
        node[name] = resource

    def render(node: dict[str, Any], indent: int) -> list[str]:
        pad = "  " * indent
        lines = ["{"]
        for key, value in sorted(node.items()):
            if isinstance(value, dict) and "endpoint" not in value:
                nested = render(value, indent + 1)
                lines.append(f"{pad}  {key}: {nested[0]}")
                lines.extend(nested[1:-1])
                lines.append(f"{pad}  }},")
            else:
                metadata = {
                    key: value[key]
                    for key in ("className", "endpoint", "name", "products", "methods")
                }
                # Deliberately not pythonModule. The npm package used to ship
                # "midas_nx.db.static_loads" to JavaScript users, which said
                # nothing they could act on and quietly advertised that one
                # language was generated from the other. The manual chapter is
                # the language-neutral answer to the same question - where is
                # this endpoint documented.
                chapter = value.get("contractManualChapter") or next(
                    (m.get("chapterFile") for m in value.get("manual", []) if m.get("chapterFile")),
                    None,
                )
                if chapter:
                    metadata["manualChapter"] = chapter
                # Contract-derived runtime behaviour, listed in one place: a
                # rule that reaches the manifest and not this dict would be a
                # rule the npm package documents and never runs.
                for behaviour in _RUNTIME_BEHAVIOUR_KEYS:
                    if behaviour in value:
                        metadata[behaviour] = value[behaviour]
                encoded = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
                payload = value.get("payloadType", "JsonObject")
                lines.append(f"{pad}  {key}: defineDbResource<{payload}>({encoded}),")
        lines.append(f"{pad}}}")
        return lines

    return "\n".join(render(tree, 0))


def _constant_evaluator(tree: ast.Module):
    constants: dict[str, str] = {}

    def evaluate(node: ast.expr) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return constants.get(node.id)
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                elif isinstance(value, ast.FormattedValue):
                    resolved = evaluate(value.value)
                    if resolved is None:
                        return None
                    parts.append(resolved)
                else:
                    return None
            return "".join(parts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left, right = evaluate(node.left), evaluate(node.right)
            return left + right if left is not None and right is not None else None
        return None

    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = evaluate(node.value)
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                constants[target.id] = value
    return evaluate


def _operation_specs(
    modules: dict[str, ast.Module],
    type_keys: set[tuple[str, str]],
    products_by_endpoint: dict[str, list[str]],
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for module, tree in sorted(modules.items()):
        if module == "midas_nx.doc" or module.endswith(".post.base"):
            continue
        imports = _import_map(module, tree)
        local_types = {name for owner, name in type_keys if owner == module}
        evaluate = _constant_evaluator(tree)
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            call: ast.Call | None = None
            method = ""
            for candidate in ast.walk(node):
                if not isinstance(candidate, ast.Call):
                    continue
                called = ast.unparse(candidate.func).split(".")[-1]
                if called in {"_post", "post_argument"}:
                    call, method = candidate, "POST"
                    break
                if called in {"_get", "get_result"}:
                    call, method = candidate, "GET"
                    break
            if call is None or not call.args:
                continue
            endpoint = evaluate(call.args[0])
            if not isinstance(endpoint, str) or not endpoint.startswith("/"):
                continue
            products = products_by_endpoint.get(endpoint)
            if products is None:
                raise RuntimeError(
                    f"Operation {module}.{node.name} ({endpoint}) has no products in docs/coverage.json"
                )
            argument = next((arg for arg in node.args.args if arg.arg == "argument"), None)
            argument_type = "JsonObject"
            if argument is not None and argument.annotation is not None:
                rendered = _type_expression(
                    argument.annotation,
                    module=module,
                    local_types=local_types,
                    imports=imports,
                    all_types=type_keys,
                )
                if rendered not in {"unknown", "JsonObject"}:
                    for local_name in sorted(local_types, key=len, reverse=True):
                        rendered = re.sub(
                            rf"(?<![.A-Za-z0-9_]){re.escape(local_name)}\b",
                            f"Types.{_namespace(module)}.{local_name}",
                            rendered,
                        )
                    rendered = re.sub(
                        r"(?<![.A-Za-z0-9_])(\w+Types)\.", r"Types.\1.", rendered
                    )
                    argument_type = rendered
            operations.append(
                {
                    "exportName": _camel(node.name),
                    "endpoint": endpoint,
                    "method": method,
                    "products": products,
                    "pythonFunction": node.name,
                    "pythonModule": module,
                    "modulePath": _module_parts(module),
                    "argumentType": argument_type,
                    "noArgument": method == "POST" and argument is None,
                    "documentation": ast.get_docstring(node) or "",
                }
            )
    return operations


def _render_operations(operations: list[dict[str, Any]]) -> str:
    tree: dict[str, Any] = {}
    for operation in operations:
        node = tree
        for part in operation["modulePath"]:
            node = node.setdefault(part, {})
        node[operation["exportName"]] = operation

    def render(node: dict[str, Any], indent: int) -> list[str]:
        pad = "  " * indent
        lines = ["{"]
        for key, value in sorted(node.items()):
            if isinstance(value, dict) and "endpoint" not in value:
                nested = render(value, indent + 1)
                lines.append(f"{pad}  {key}: {nested[0]}")
                lines.extend(nested[1:-1])
                lines.append(f"{pad}  }},")
                continue
            metadata = json.dumps(
                {field: value[field] for field in ("endpoint", "method", "products")},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            if value["method"] == "GET":
                expression = f"defineGetOperation({metadata})"
            elif value["noArgument"]:
                expression = f"defineEmptyPostOperation({metadata})"
            else:
                expression = f"definePostOperation<{value['argumentType']}>({metadata})"
            lines.extend(_jsdoc(value["documentation"], indent + 1))
            lines.append(f"{pad}  {key}: {expression},")
        lines.append(f"{pad}}}")
        return lines

    return "\n".join(render(tree, 0))


def _table_specs(modules: dict[str, ast.Module]) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for module, tree in sorted(modules.items()):
        if not module.startswith("midas_nx.post.") or module.endswith(".base"):
            continue
        evaluate = _constant_evaluator(tree)
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            for candidate in ast.walk(node):
                if not isinstance(candidate, ast.Call) or not candidate.args:
                    continue
                called = ast.unparse(candidate.func).split(".")[-1]
                if called not in {"get_table", "_get_design_forces_table"}:
                    continue
                table_type = evaluate(candidate.args[0])
                factory = "fixed"
                if table_type is None and isinstance(candidate.args[0], ast.Name):
                    parameter_name = candidate.args[0].id
                    positional = node.args.args
                    defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
                    default_node = next(
                        (default for parameter, default in zip(positional, defaults) if parameter.arg == parameter_name),
                        None,
                    )
                    table_type = evaluate(default_node) if default_node is not None else None
                    factory = "variable"
                elif table_type is None and isinstance(candidate.args[0], ast.JoinedStr):
                    values = candidate.args[0].values
                    if (
                        len(values) == 2
                        and isinstance(values[0], ast.Constant)
                        and isinstance(values[0].value, str)
                        and isinstance(values[1], ast.FormattedValue)
                    ):
                        table_type = values[0].value
                        factory = "directional"
                if table_type is not None:
                    option_names = {
                        _TABLE_OPTION_NAMES[parameter.arg]
                        for parameter in node.args.args + node.args.kwonlyargs
                        if parameter.arg in _TABLE_OPTION_NAMES
                    }
                    tables.append(
                        {
                            "exportName": _camel(node.name),
                            "tableType": table_type,
                            "factory": factory,
                            "pythonFunction": node.name,
                            "pythonModule": module,
                            "modulePath": _module_parts(module)[1:],
                            "optionNames": sorted(option_names),
                            "documentation": ast.get_docstring(node) or "",
                        }
                    )
                break
    return tables


def _render_table_types() -> list[str]:
    """Emit every contracted TABLE_TYPE as a named constant.

    89 result tables share one route, selected by a `TABLE_TYPE` string. Both
    SDKs could always *reach* any of them by passing the raw string, but the
    Python package names each value (`TABLE_TYPE_REACTION_LOCAL`) while the npm
    package named only whichever one a wrapper defaulted to - so a variant like
    `REACTIONL` existed for anyone who already knew it existed, and for nobody
    else. Names come from `contracts/tables/*.yaml`, the same place both
    languages now take them from.
    """
    contract_dir = ROOT / "contracts" / "tables"
    if not contract_dir.is_dir():
        return []
    try:
        import yaml  # noqa: PLC0415
    except ImportError:  # pragma: no cover - dev dependency
        raise SystemExit(
            'contracts/ is present but PyYAML is not installed. Run: pip install -e ".[dev]"'
        ) from None

    entries: list[tuple[str, list[tuple[str, str, str]]]] = []
    for path in sorted(contract_dir.glob("*.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        variants = [
            (_camel(v.get("description") or v["value"]), v["value"], v.get("description", ""))
            for v in contract.get("tableTypes", [])
        ]
        if variants:
            entries.append((_camel(contract["name"]), variants))
    if not entries:
        return []

    lines = [
        "/**",
        " * TABLE_TYPE values, from contracts/tables/*.yaml.",
        " *",
        " * Pass one as `tableType` to the matching table wrapper to select a variant",
        " * other than its default.",
        " */",
        "export const tableTypes = {",
    ]
    for name, variants in entries:
        lines.append(f"  {name}: {{")
        for key, value, description in variants:
            if description:
                lines.append(f"    /** {description} */")
            lines.append(f'    {key}: "{value}",')
        lines.append("  },")
    lines += ["} as const;", ""]
    return lines


def _render_tables(tables: list[dict[str, Any]]) -> str:
    tree: dict[str, Any] = {}
    for table in tables:
        node = tree
        for part in table["modulePath"]:
            node = node.setdefault(part, {})
        node[table["exportName"]] = table

    def render(node: dict[str, Any], indent: int) -> list[str]:
        pad = "  " * indent
        lines = ["{"]
        for key, value in sorted(node.items()):
            if isinstance(value, dict) and "tableType" not in value:
                nested = render(value, indent + 1)
                lines.append(f"{pad}  {key}: {nested[0]}")
                lines.extend(nested[1:-1])
                lines.append(f"{pad}  }},")
            else:
                factory = {
                    "fixed": "defineTable",
                    "variable": "defineVariableTable",
                    "directional": "defineDirectionalTable",
                }[value["factory"]]
                option_names = " | ".join(json.dumps(name) for name in value["optionNames"])
                option_type = f"Pick<TableOptions, {option_names}>" if option_names else "Record<never, never>"
                lines.extend(_jsdoc(value["documentation"], indent + 1))
                lines.append(
                    f"{pad}  {key}: {factory}<{option_type}>({json.dumps(value['tableType'])}),"
                )
        lines.append(f"{pad}}}")
        return lines

    return "\n".join(render(tree, 0))


_SHARED_PAYLOADS: dict[tuple[str, str], str] = {
    ("midas_nx.db.load_combinations", "LoadCombinationGeneral"): "LoadCombinationPayload",
    ("midas_nx.db.load_combinations", "LoadCombinationConcrete"): "LoadCombinationConcretePayload",
    ("midas_nx.db.load_combinations", "LoadCombinationSteel"): "LoadCombinationPayload",
    ("midas_nx.db.load_combinations", "LoadCombinationSRC"): "LoadCombinationPayload",
    ("midas_nx.db.load_combinations", "LoadCombinationCompositeSteelGirder"): "LoadCombinationPayload",
    ("midas_nx.db.load_combinations", "LoadCombinationSeismic"): "LoadCombinationPayload",
    ("midas_nx.db.moving_loads", "TrafficLineLanes"): "TrafficLineLanePayload",
    ("midas_nx.db.moving_loads", "TrafficSurfaceLanes"): "TrafficSurfaceLanePayload",
    ("midas_nx.db.moving_loads", "Vehicles"): "VehiclePayload",
    ("midas_nx.db.moving_loads", "VehiclesTransverse"): "VehicleTransversePayload",
    ("midas_nx.db.moving_loads", "ConcurrentReactionGroup"): "StructureGroupNamesPayload",
    ("midas_nx.db.moving_loads", "ConcurrentJointForceGroup"): "StructureGroupNamesPayload",
    ("midas_nx.db.moving_loads", "VehicleClasses"): "VehicleClassPayload",
    ("midas_nx.db.moving_loads", "RailwayDynamicFactorByElement"): "RailwayDynamicFactorPayload",
    ("midas_nx.design.steel_kds", "CombinedRatioCalculationMethodForCircularSection"): "CombinedRatioCalculationMethodPayload",
    ("midas_nx.db.properties.hinge", "InelasticHingePropertyHyperSBeam"): "InelasticHingePropertyHyperSPayload",
    ("midas_nx.db.properties.hinge", "InelasticHingePropertyHyperSTruss"): "InelasticHingePropertyHyperSPayload",
    ("midas_nx.db.properties.hinge", "InelasticHingePropertyHyperSGeneralLink"): "InelasticHingePropertyHyperSPayload",
    ("midas_nx.db.properties.hinge", "InelasticHingePropertyHyperSPss"): "InelasticHingePropertyHyperSPayload",
}


def _attach_payload_types(
    resources: list[dict[str, Any]], type_keys: set[tuple[str, str]]
) -> None:
    for resource in resources:
        module = resource["pythonModule"]
        candidate = resource["className"] + "Payload"
        if (module, candidate) not in type_keys:
            candidate = _SHARED_PAYLOADS.get((module, resource["className"]), "")
        if candidate and (module, candidate) in type_keys:
            resource["payloadTypeName"] = candidate
            resource["payloadType"] = f"Types.{_namespace(module)}.{candidate}"
        else:
            resource["payloadType"] = "JsonObject"


def _contract_payload_types(
    resources: list[dict[str, Any]],
    contracts: dict[str, dict[str, Any]],
    type_keys: set[tuple[str, str]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    """Bind every contracted resource to its own contract-shaped npm payload.

    The legacy Python compatibility layer occasionally reuses one TypedDict for
    different endpoints.  After contracts become the TypeScript source, a map
    keyed only by that old name silently lets the last endpoint overwrite the
    first one's contract.  Keep one name only when all shapes match exactly;
    otherwise emit an endpoint-class-specific supplementary type.
    """

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for resource in resources:
        if resource.get("payloadTypeName") and resource["endpoint"] in contracts:
            grouped[(resource["pythonModule"], resource["payloadTypeName"])].append(resource)

    bound: dict[tuple[str, str], dict[str, Any]] = {}
    supplemental: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for (module, legacy_name), group in grouped.items():
        fingerprints = {
            json.dumps(contracts[resource["endpoint"]], ensure_ascii=False, sort_keys=True)
            for resource in group
        }
        if len(fingerprints) == 1:
            bound[(module, legacy_name)] = contracts[group[0]["endpoint"]]
            continue

        occupied = {name for known_module, name in type_keys if known_module == module}
        occupied.update(name for known_module, name in bound if known_module == module)
        occupied.update(supplemental[module])
        for resource in group:
            candidate = resource["className"] + "Payload"
            if candidate == legacy_name:
                # The endpoint that owns the original class keeps the published
                # name; its contract replaces the legacy definition in place.
                bound[(module, candidate)] = contracts[resource["endpoint"]]
                continue
            if candidate in occupied:
                candidate = resource["className"] + "ContractPayload"
            suffix = 2
            base = candidate
            while candidate in occupied:
                candidate = f"{base}{suffix}"
                suffix += 1
            occupied.add(candidate)
            supplemental[module][candidate] = contracts[resource["endpoint"]]
            resource["payloadTypeName"] = candidate
            resource["payloadType"] = f"Types.{_namespace(module)}.{candidate}"

    return bound, dict(supplemental)


def main() -> None:
    resources = _load_resources()
    modules = _source_modules()
    resource_keys = {(item["pythonModule"], item["className"]) for item in resources}
    type_keys = _collect_type_classes(modules, resource_keys)
    coverage = json.loads((ROOT / "docs" / "coverage.json").read_text(encoding="utf-8"))
    products_by_endpoint = {
        entry["endpoint"]: sorted(entry["products"])
        for entry in coverage["endpoints"]
    }
    operations = _operation_specs(modules, type_keys, products_by_endpoint)
    tables = _table_specs(modules)
    _attach_payload_types(resources, type_keys)
    contract_fields = _contract_payload_fields()
    contract_types, supplemental_contract_types = _contract_payload_types(
        resources, contract_fields, type_keys
    )
    _check_contract_payload_type_names(resources)
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    TYPESCRIPT_SRC.joinpath("generated").mkdir(parents=True, exist_ok=True)

    manifest = {
        "$schema": "./typescript-resources.schema.json",
        "source": {
            "pythonPackage": "midas-nx",
            "coverageLedger": "docs/coverage.json",
        },
        "resourceCount": len(resources),
        # `contractManualChapter` is an internal shadow-run input. It affects
        # npm runtime metadata but is deliberately not a new manifest surface.
        "resources": [
            {key: value for key, value in resource.items() if key != "contractManualChapter"}
            for resource in resources
        ],
    }
    (SCHEMA_DIR / "typescript-resources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    resource_endpoints = {item["endpoint"] for item in resources}
    operation_endpoints = {item["endpoint"] for item in operations}
    coverage_rows: list[dict[str, str]] = []
    missing: list[str] = []
    for entry in coverage["endpoints"]:
        endpoint = entry["endpoint"]
        canonical = (
            "/post/TABLE"
            if endpoint.startswith("/post/TABLE (") or endpoint in _POST_TABLE_LEDGER_ALIASES
            else endpoint
        )
        if canonical in resource_endpoints:
            surface = "resource"
        elif canonical in operation_endpoints:
            surface = "operation"
        elif canonical in _DOC_ENDPOINTS:
            surface = "doc"
        elif canonical in _DESIGN_TABLE_ENDPOINTS:
            surface = "designTable"
        elif canonical == "/post/TABLE":
            surface = "table"
        else:
            surface = "missing"
            missing.append(endpoint)
        coverage_rows.append({"endpoint": endpoint, "canonicalEndpoint": canonical, "surface": surface})
    if missing:
        raise RuntimeError(f"TypeScript SDK is missing coverage for: {', '.join(missing)}")
    coverage_manifest = {
        "source": "docs/coverage.json",
        "coverageRowCount": len(coverage_rows),
        "coveredRowCount": len(coverage_rows) - len(missing),
        "rows": coverage_rows,
    }
    (SCHEMA_DIR / "typescript-coverage.json").write_text(
        json.dumps(coverage_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    generated = "\n".join(
        [
            "// Generated by scripts/generate_typescript_sdk.py. Do not edit by hand.",
            'import { defineDbResource } from "../db-resource";',
            'import type { JsonObject } from "../types";',
            'import type * as Types from "./types";',
            "",
            f"export const resources = {_render_tree(resources)} as const;",
            "",
            f"export const resourceCount = {len(resources)} as const;",
            "",
        ]
    )
    (TYPESCRIPT_SRC / "generated" / "resources.ts").write_text(generated, encoding="utf-8")
    (TYPESCRIPT_SRC / "generated" / "types.ts").write_text(
        _render_types(modules, type_keys, contract_types, supplemental_contract_types), encoding="utf-8"
    )
    generated_operations = "\n".join(
        [
            "// Generated by scripts/generate_typescript_sdk.py. Do not edit by hand.",
            'import { defineEmptyPostOperation, defineGetOperation, definePostOperation } from "../operation";',
            'import type { JsonObject } from "../types";',
            'import type * as Types from "./types";',
            "",
            f"export const operations = {_render_operations(operations)} as const;",
            "",
            f"export const operationCount = {len(operations)} as const;",
            "",
        ]
    )
    (TYPESCRIPT_SRC / "generated" / "operations.ts").write_text(
        generated_operations, encoding="utf-8"
    )
    generated_tables = "\n".join(
        [
            "// Generated by scripts/generate_typescript_sdk.py. Do not edit by hand.",
            'import { defineDirectionalTable, defineTable, defineVariableTable } from "../post";',
            'import type { TableOptions } from "../post";',
            "",
            f"export const tables = {_render_tables(tables)} as const;",
            "",
            f"export const tableCount = {len(tables)} as const;",
            "",
            *_render_table_types(),
        ]
    )
    (TYPESCRIPT_SRC / "generated" / "tables.ts").write_text(
        generated_tables, encoding="utf-8"
    )
    contract_type_count = len(contract_types) + sum(
        len(types) for types in supplemental_contract_types.values()
    )
    payload_type_count = len(type_keys) + sum(
        len(types) for types in supplemental_contract_types.values()
    )
    print(
        f"Generated {len(resources)} TypeScript DB resources "
        f"({_RESOURCE_SOURCE_COUNTS['contract']} identified by a contract, "
        f"{_RESOURCE_SOURCE_COUNTS['python']} still by a Python class), "
        f"{len(operations)} operations, {len(tables)} table wrappers, "
        f"and {payload_type_count} payload types "
        f"({contract_type_count} of them from contracts, the rest still from Python)"
    )


if __name__ == "__main__":
    main()
