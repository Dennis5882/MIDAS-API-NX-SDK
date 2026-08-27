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


def _render_types(modules: dict[str, ast.Module], type_keys: set[tuple[str, str]]) -> str:
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


def _load_resources() -> list[dict[str, Any]]:
    sys.path.insert(0, str(PYTHON_SRC))
    import midas_nx  # noqa: PLC0415
    from midas_nx.db.base import DbResource  # noqa: PLC0415

    for module in pkgutil.walk_packages(midas_nx.__path__, midas_nx.__name__ + "."):
        importlib.import_module(module.name)

    coverage = json.loads((ROOT / "docs" / "coverage.json").read_text(encoding="utf-8"))
    coverage_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in coverage["endpoints"]:
        coverage_by_endpoint[entry["endpoint"]].append(entry)

    payload_defaults = _contract_payload_defaults()

    resources: list[dict[str, Any]] = []
    for cls in _all_subclasses(DbResource):
        endpoint = cls.ENDPOINT
        matches = coverage_by_endpoint.get(endpoint, [])
        resources.append(
            {
                "className": cls.__name__,
                "exportName": _camel(cls.__name__),
                "endpoint": endpoint,
                "name": cls.NAME or cls.__name__,
                "products": sorted(cls.PRODUCTS),
                "methods": sorted(cls.METHODS),
                "pythonModule": cls.__module__,
                "modulePath": _module_parts(cls.__module__),
                # Present only for endpoints with a contract rule; see
                # _contract_payload_defaults().
                **(
                    {"payloadDefaults": payload_defaults[endpoint]}
                    if endpoint in payload_defaults
                    else {}
                ),
                "manual": [
                    {
                        "name": match.get("name"),
                        "chapterFile": match.get("chapter_file"),
                        "status": match.get("status"),
                    }
                    for match in matches
                ],
            }
        )
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
                    for key in ("className", "endpoint", "name", "products", "methods", "pythonModule")
                }
                if "payloadDefaults" in value:
                    metadata["payloadDefaults"] = value["payloadDefaults"]
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
    modules: dict[str, ast.Module], type_keys: set[tuple[str, str]]
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
                {field: value[field] for field in ("endpoint", "method", "pythonFunction", "pythonModule")},
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


def main() -> None:
    resources = _load_resources()
    modules = _source_modules()
    resource_keys = {(item["pythonModule"], item["className"]) for item in resources}
    type_keys = _collect_type_classes(modules, resource_keys)
    operations = _operation_specs(modules, type_keys)
    tables = _table_specs(modules)
    _attach_payload_types(resources, type_keys)
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    TYPESCRIPT_SRC.joinpath("generated").mkdir(parents=True, exist_ok=True)

    manifest = {
        "$schema": "./typescript-resources.schema.json",
        "source": {
            "pythonPackage": "midas-nx",
            "coverageLedger": "docs/coverage.json",
        },
        "resourceCount": len(resources),
        "resources": resources,
    }
    (SCHEMA_DIR / "typescript-resources.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    coverage = json.loads((ROOT / "docs" / "coverage.json").read_text(encoding="utf-8"))
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
        _render_types(modules, type_keys), encoding="utf-8"
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
        ]
    )
    (TYPESCRIPT_SRC / "generated" / "tables.ts").write_text(
        generated_tables, encoding="utf-8"
    )
    print(
        f"Generated {len(resources)} TypeScript DB resources, "
        f"{len(operations)} operations, {len(tables)} table wrappers, "
        f"and {len(type_keys)} payload types"
    )


if __name__ == "__main__":
    main()
