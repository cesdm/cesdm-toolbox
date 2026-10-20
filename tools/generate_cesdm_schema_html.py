#!/usr/bin/env python3
# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""
generate_cesdm_schema_html.py
─────────────────────────────
Generate a self-contained HTML reference from a CESDM schema directory.

Usage
-----
    python generate_cesdm_schema_html.py [schema_dir ...] [output.html]

    schema_dir   One or more schema folders, loaded in order the same way
                 as build_model_from_yaml. The first folder's ``extends``
                 entries are loaded first, and each folder's
                 augmentations.yaml is applied to the existing classes.
                 Defaults to ./cesdm/schemas/base
    output.html  Path for the generated HTML file.
                 Defaults to cesdm_schema_ref.html

Requirements
------------
    pip install pyyaml
"""

from __future__ import annotations

import argparse
import html as _html
import json
import pathlib
import sys
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required.  Install it with:  pip install pyyaml")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Schema loading
# ─────────────────────────────────────────────────────────────────────────────

def load_attribute_registry(schema_dir: pathlib.Path) -> dict[str, Any]:
    """Merge all attribute definition files into one flat dict."""
    registry: dict[str, Any] = {}
    attr_dir = schema_dir / "attributes"
    if not attr_dir.exists():
        return registry
    for f in sorted(attr_dir.glob("*.yaml")):
        if f.stem.startswith("_"):
            continue
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        # Top-level may be {"attributes": {...}} or just the flat dict
        top = d.get("attributes", d)
        if isinstance(top, dict):
            registry.update(top)
    return registry


def load_relation_registry(schema_dir: pathlib.Path) -> dict[str, Any]:
    """Load relations/relations.yaml."""
    rel_file = schema_dir / "relations" / "relations.yaml"
    if not rel_file.exists():
        return {}
    try:
        d = yaml.safe_load(rel_file.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(d, dict):
        return {}
    return d.get("relations", d)


def load_entities(schema_dir: pathlib.Path) -> dict[str, dict]:
    """Load entity YAMLs from either legacy entities/ or semantic schema folders."""
    entities: dict[str, dict] = {}
    ent_dir = schema_dir / "entities"
    search_root = ent_dir if ent_dir.exists() else schema_dir
    for f in sorted(search_root.rglob("*.yaml")):
        if "attributes" in f.parts or "relations" in f.parts:
            continue
        if f.stem.startswith("_"):
            continue
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or "name" not in d:
            continue
        entities[d["name"]] = d
    return entities


def resolve_schema_dirs(paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """Prepend the primary schema's ``extends`` entries, as the model loader does."""
    if not paths:
        raise ValueError("At least one schema directory is required")
    repo = pathlib.Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from ear.schema_manifest import SchemaManifest

    primary = paths[0]
    manifest = SchemaManifest.load(primary if primary.is_dir() else primary.parent)
    existing = {p.resolve() for p in paths}
    bases = [ext for ext in manifest.extends if ext not in existing]
    return bases + list(paths)


_ATTR_USAGE_KEYS = {"id", "required", "default", "belongsToGroup"}
_REL_USAGE_KEYS = {"id", "required", "belongsToGroup", "default", "fixed"}


def _augmentation_item(item: Any, kind: str, group_name: str | None, source: pathlib.Path) -> dict:
    allowed = _ATTR_USAGE_KEYS if kind == "attribute" else _REL_USAGE_KEYS
    if isinstance(item, str):
        out = {"id": item}
    elif isinstance(item, dict) and "id" in item and set(item).issubset(allowed):
        out = dict(item)
    else:
        raise ValueError(
            f"Augmentation in {source} may only reference a registry id "
            f"with usage overrides, got {item!r}"
        )
    if group_name is not None:
        explicit = out.get("belongsToGroup")
        values = [explicit] if isinstance(explicit, str) else list(explicit or [])
        if explicit is not None and values != [group_name]:
            raise ValueError(
                f"Augmentation group '{group_name}' in {source} must not assign "
                f"a different belongsToGroup: {explicit!r}"
            )
        out["belongsToGroup"] = group_name
    return out


def _without_schema(item: Any) -> Any:
    """Compare schema objects without the package tag this generator adds."""
    if isinstance(item, dict) and "_schema" in item:
        return {k: v for k, v in item.items() if k != "_schema"}
    return item


def _attach_augmentation(entities: dict[str, dict], target: str, kind: str,
                         item: dict, source: pathlib.Path, package: str) -> None:
    if target not in entities:
        raise ValueError(f"Augmentation in {source} targets unknown class '{target}'")
    key = "attributes" if kind == "attribute" else "relations"
    declared = entities[target].setdefault(key, [])
    if not isinstance(declared, list):
        raise ValueError(f"{target}.{key} is not a list; cannot apply {source}")
    field_id = item["id"]
    stamped = dict(item)
    stamped["_schema"] = package
    for existing in declared:
        existing_id = existing if isinstance(existing, str) else existing.get("id")
        if existing_id != field_id:
            continue
        if _without_schema(existing) != _without_schema(stamped):
            raise ValueError(
                f"Augmentation conflict: {target} already declares {kind} "
                f"'{field_id}' with a different usage ({source})"
            )
        return
    declared.append(stamped)


def _apply_augmentation_block(entities: dict[str, dict], raw: Any, source: pathlib.Path,
                              package: str) -> None:
    if isinstance(raw, dict):
        entries = list(raw.items())
    elif isinstance(raw, list):
        entries = []
        for index, entry in enumerate(raw):
            if not isinstance(entry, dict):
                raise ValueError(f"Augmentation entry {index} in {source} must be a mapping")
            target = entry.get("target") or entry.get("entity_class")
            if not target:
                raise ValueError(f"Augmentation entry {index} in {source} has no target")
            entries.append((target, entry))
    else:
        raise ValueError(f"'augmentations' in {source} must be a mapping or list")

    for target, block in entries:
        if not isinstance(block, dict):
            raise ValueError(f"Augmentation for '{target}' in {source} must be a mapping")
        unknown = set(block) - {"attributes", "relations", "groups", "target", "entity_class"}
        if unknown:
            raise ValueError(
                f"Augmentation for '{target}' in {source} contains unknown keys: {sorted(unknown)}"
            )

        def collect(kind: str, values: Any, group_name: str | None = None) -> None:
            if not values:
                return
            if isinstance(values, str):
                values = [values]
            if not isinstance(values, list):
                raise ValueError(f"Augmentation list for '{target}' in {source} must be a list")
            for raw_item in values:
                item = _augmentation_item(raw_item, kind, group_name, source)
                _attach_augmentation(entities, str(target), kind, item, source, package)

        collect("attribute", block.get("attributes"))
        collect("relation", block.get("relations"))
        groups = block.get("groups") or {}
        if not isinstance(groups, dict):
            raise ValueError(f"Augmentation groups for '{target}' in {source} must be a mapping")
        for group_name, group_block in groups.items():
            if not isinstance(group_block, dict):
                raise ValueError(
                    f"Augmentation '{target}.groups.{group_name}' in {source} must be a mapping"
                )
            collect("attribute", group_block.get("attributes"), group_name)
            collect("relation", group_block.get("relations"), group_name)


def apply_augmentations(schema_dir: pathlib.Path, entities: dict[str, dict],
                        package: str | None = None) -> None:
    """Attach registry ids from augmentation documents onto classes already loaded."""
    if not schema_dir.is_dir():
        return
    for path in sorted(schema_dir.rglob("*.y*ml")):
        if "attributes" in path.parts or "relations" in path.parts:
            continue
        try:
            docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        except Exception:
            if path.name.startswith("augmentations"):
                raise
            continue
        for doc in docs:
            if isinstance(doc, dict) and "augmentations" in doc:
                _apply_augmentation_block(
                    entities, doc.get("augmentations"), path, package or schema_dir.resolve().name
                )


def _merge_registry(into: dict, part: dict, kind: str, source: pathlib.Path,
                    package: str) -> None:
    for field_id, spec in part.items():
        if field_id in into and _without_schema(into[field_id]) != _without_schema(spec):
            raise ValueError(
                f"Duplicate {kind} id '{field_id}' with different definitions while loading {source}"
            )
        if field_id not in into:
            if isinstance(spec, dict):
                spec = dict(spec)
                spec["_schema"] = package
            into[field_id] = spec


def load_schema(paths: list[pathlib.Path]) -> tuple[dict[str, dict], dict, dict]:
    """Load classes, attributes and relations the way ``build_model_from_yaml`` does.

    Parent schemas named by ``extends`` come first. A later directory adds
    its own classes and registries. ``augmentations.yaml`` then attaches
    registered fields to classes that already exist.
    """
    dirs = resolve_schema_dirs(paths)
    entities: dict[str, dict] = {}
    attrs_db: dict = {}
    rels_db: dict = {}
    for schema_dir in dirs:
        if not schema_dir.is_dir():
            raise FileNotFoundError(f"Schema directory not found: {schema_dir}")
        package = schema_dir.resolve().name
        _merge_registry(attrs_db, load_attribute_registry(schema_dir), "attribute", schema_dir, package)
        _merge_registry(rels_db, load_relation_registry(schema_dir), "relation", schema_dir, package)
        for name, entity in load_entities(schema_dir).items():
            if name in entities:
                raise ValueError(f"Class '{name}' is defined in more than one loaded schema")
            entity["_schema"] = package
            entities[name] = entity
        apply_augmentations(schema_dir, entities, package)
    return entities, attrs_db, rels_db


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Inheritance helpers
# ─────────────────────────────────────────────────────────────────────────────

def parents_of(name: str, entities: dict) -> list[str]:
    d = entities.get(name, {})
    p = d.get("parents", [])
    return [p] if isinstance(p, str) else list(p)


def all_ancestors(name: str, entities: dict, _visited: set | None = None) -> list[str]:
    """Return ancestor names breadth-first (parents, then grandparents…)."""
    if _visited is None:
        _visited = set()
    result = []
    for p in parents_of(name, entities):
        if p not in _visited:
            _visited.add(p)
            result.append(p)
            result.extend(all_ancestors(p, entities, _visited))
    return result


def _usage_schema(item: Any, owner: dict) -> str:
    """Package that attached a field, else the package that defined the class."""
    if isinstance(item, dict) and item.get("_schema"):
        return str(item["_schema"])
    return str(owner.get("_schema") or "")


def _usage_groups(item: Any) -> list[str]:
    """belongsToGroup values that the schema reference can filter."""
    if not isinstance(item, dict):
        return []
    raw = item.get("belongsToGroup") or []
    if isinstance(raw, str):
        raw = [raw]
    wanted = {"technical", "dispatch"}
    return [g for g in ("technical", "dispatch") if g in {str(x) for x in raw} and g in wanted]


def collect_inherited(name: str, entities: dict) -> tuple[list, list]:
    """
    Return (inherited_attrs, inherited_rels) — fields from ancestor classes
    that are NOT already declared on the entity itself.
    Each attr element: (id, required, schema, groups)
    Each rel  element: (id, required, target, description, schema, groups)
    """
    d = entities.get(name, {})
    seen_a = {a["id"] for a in (d.get("attributes") or [])}
    seen_r = {r["id"] for r in (d.get("relations") or [])}
    inh_a: list = []
    inh_r: list = []

    def _gather(pname: str, depth: int = 0) -> None:
        if depth > 12:
            return
        pe = entities.get(pname, {})
        for a in pe.get("attributes") or []:
            if a["id"] not in seen_a:
                seen_a.add(a["id"])
                inh_a.append((a["id"], a.get("required", False), _usage_schema(a, pe), _usage_groups(a)))
        for r in pe.get("relations") or []:
            if r["id"] not in seen_r:
                seen_r.add(r["id"])
                inh_r.append((r["id"], r.get("required", False), r.get("target", ""),
                              r.get("description", "") or r.get("comment", ""),
                              _usage_schema(r, pe), _usage_groups(r)))
        for pp in parents_of(pname, entities):
            _gather(pp, depth + 1)

    for p in parents_of(name, entities):
        _gather(p)

    return inh_a, inh_r


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Categorisation
# ─────────────────────────────────────────────────────────────────────────────

_ASSET_ROOTS       = {"EnergyAssetInstance"}
_REPR_ROOTS        = {"Result"}
_NETWORK_ROOTS     = {"NetworkNode"}
_TECH_TYPE_ROOTS   = {"EnergyTechnologyType"}

# Sub-categories within the "domain" bucket — used for tab labels and
# section grouping in the HTML.  Everything that is not an asset,
# result, or network node falls into domain by default because
# the YAML schemas do not carry an explicit category field; we infer it
# purely from the inheritance tree.
#
# The domain bucket therefore contains heterogeneous things:
#   - Technology types  (GeneratorType, StorageType, …) — EnergyTechnologyType tree
#   - Carriers          (Carrier, CarrierDomain, GeographicalRegion)
#   - Time-series       (Profile, TimestampSeries)
#   - Agents            (Agent, Household, EnergyCommittee, …)
#   - Abstract bases    (SemanticEntity, SystemAsset, Port)
#   - Run records       (DispatchRunRecord, EnergySystemModel)
#
# To give users a better label in the UI we call this tab "Domain & Types"
# and explain in the page header what it contains.

def categorise(name: str, entities: dict) -> str:
    """Assign a display category based on the inheritance hierarchy.

    Categories:
      asset   — descends from EnergyAssetInstance
      result  — descends from Result (the only classes that use the
                reportsOn pattern, one per analysis run; AVR/GOV/PSS
                controllers also stand alone but link via
                controlsGenerationUnit instead, so they fall into "domain"
                like any other non-asset, non-network entity)
      network — descends from NetworkNode
      domain  — everything else: technology types, carriers, time-series,
                agents, abstract base classes, run records, controllers, etc.
                "Domain" is a catch-all; the entities here do not share
                a single conceptual role — they are simply not assets,
                results, or network nodes.
    """
    ancestors = set(all_ancestors(name, entities)) | {name}
    if ancestors & _ASSET_ROOTS:
        return "asset"
    if ancestors & _REPR_ROOTS:
        # Abstract bases in the Result tree (Result, DispatchResult,
        # PowerFlowResult, DynamicResult) never have their own
        # reportsOn target, so they'd never be nested under any
        # asset card and would otherwise never appear anywhere in the
        # page at all. Route them into "domain" (Abstract Bases group)
        # instead, alongside every other abstract base class.
        if entities.get(name, {}).get("abstract"):
            return "domain"
        return "result"
    if ancestors & _NETWORK_ROOTS:
        return "network"
    return "domain"


def domain_subcategory(name: str, entities: dict) -> str:
    """Finer-grained label for entities in the domain bucket."""
    anc = set(all_ancestors(name, entities)) | {name}
    if anc & _TECH_TYPE_ROOTS:
        return "Technology Types"
    d = entities.get(name, {})
    if name in ("Carrier", "CarrierDomain", "GeographicalRegion",
                "NaturalResource"):
        return "Carriers & Geography"
    if name in ("Profile", "TimestampSeries"):
        return "Time Series"
    if name == "EnergySystemModel":
        return "Model Records"
    if name in ("SemanticEntity", "SystemAsset", "Port", "ConversionPort",
                "EnergyTechnologyType"):
        return "Abstract Bases"
    return "Other"


def views_for_asset(asset_name: str, entities: dict) -> list[str]:
    """Return all Result entities that have reportsOn → asset_name."""
    result = []
    for vname, vd in entities.items():
        if categorise(vname, entities) != "result":
            continue
        for r in (vd.get("relations") or []):
            targets = r.get("target", "")
            if isinstance(targets, str):
                targets = [targets]
            if asset_name in targets and r["id"] in ("reportsOn", "representsNode"):
                result.append(vname)
                break
    return sorted(result)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

def esc(s: Any) -> str:
    # Keep numeric 0. ``str(s or "")`` would render a minimum of 0 as blank.
    if s is None:
        return ""
    return _html.escape(str(s))


def _constraints_prose(c: Any) -> str:
    """Extract human-readable prose from a top-level constraints field.

    Some attribute definitions store their description as a list of strings
    under a top-level ``constraints`` key rather than in ``description``.
    This helper extracts that prose so it can be used as a fallback description.
    Returns empty string if ``c`` is not a list of strings.
    """
    if not c:
        return ""
    if isinstance(c, list):
        # Keep only items that look like prose (not "minimum: 0.0" style constraints)
        prose = [str(item) for item in c
                 if isinstance(item, str)
                 and ":" not in str(item)[:20]]
        return " ".join(prose).strip()
    if isinstance(c, str) and ":" not in c[:20]:
        return c.strip()
    return ""


def attr_meta_html(aid: str, attrs_db: dict) -> tuple[str, str]:
    """Return (meta_html, desc_html) for an attribute id."""
    a = attrs_db.get(aid, {})
    parts: list[str] = []

    v = a.get("value", {})
    if isinstance(v, dict):
        typ = v.get("type", "")
        if typ:
            parts.append(f"<span class='typ'>{esc(typ)}</span>")
        c = v.get("constraints", {})
        if isinstance(c, dict):
            if c.get("minimum") is not None:
                parts.append(f"min&nbsp;{esc(c['minimum'])}")
            if c.get("maximum") is not None:
                parts.append(f"max&nbsp;{esc(c['maximum'])}")
            if "enum" in c:
                opts = " | ".join(esc(x) for x in c["enum"])
                parts.append(f"<span class='enum'>{opts}</span>")
        default = v.get("default")
        if default is not None:
            parts.append(f"default&nbsp;{esc(default)}")

    u = a.get("unit", {})
    if isinstance(u, dict):
        uc = u.get("constraints", {})
        if isinstance(uc, dict) and "enum" in uc:
            ustr = " | ".join(esc(x) for x in uc["enum"])
            parts.append(f"<span class='unit'>{ustr}</span>")

    meta_html = " ".join(f"<span class='meta'>{p}</span>" for p in parts)

    # Description fallback chain:
    # 1. description  2. comment  3. top-level constraints list (some schemas
    #    put prose there instead of in description)  4. label  5. empty string
    desc = (
        a.get("description", "")
        or a.get("comment", "")
        or _constraints_prose(a.get("constraints"))
        or a.get("label", "")
        or ""
    )
    return meta_html, esc(str(desc))


def rel_info_html(rid: str, rels_db: dict, target_override: Any = "",
                  inline_desc: str = "") -> tuple[str, str]:
    """Return (targets_html, desc_html) for a relation id.

    inline_desc: description declared directly on the entity relation entry
    (overrides or supplements the global relation registry description).
    """
    r = rels_db.get(rid, {})
    targets = r.get("target", target_override or "")
    if isinstance(targets, str):
        targets = [targets] if targets else []
    if not targets and target_override:
        t = target_override
        targets = [t] if isinstance(t, str) else list(t)
    thtml = " | ".join(f'<a href="#{esc(t)}" class="ref">{esc(t)}</a>' for t in targets)
    # Prefer inline description (entity-level override), fall back to global registry
    desc = inline_desc or r.get("description", "") or r.get("comment", "")
    return thtml, esc(str(desc))


_PKG_LABELS = {
    "base": "Base",
    "powerflow": "Power flow",
    "dynamics": "Dynamic",
}

# Packages present on the page currently being built, in load order.
_page_packages: list[str] = []


def _pkg_label(schema: str) -> str:
    return _PKG_LABELS.get(schema, schema)


def _pkg_badge(schema: str) -> str:
    if not schema or schema == "base":
        return ""
    kind = {
        "powerflow": "pkg-power",
        "dynamics": "pkg-dynamic",
    }.get(schema, "pkg-other")
    return f'<span class="pkg {kind}">{esc(_pkg_label(schema))}</span>'


def _field_badge(schema: str, class_schema: str) -> str:
    """Mark a field that a package other than the class itself attached."""
    if len(_page_packages) < 2 or not schema or schema == class_schema:
        return ""
    return _pkg_badge(schema)


_GROUP_MARKS = (
    ("technical", "Technical", "grp-technical"),
    ("dispatch", "Dispatch", "grp-dispatch"),
)


def _group_badge(groups: list[str] | None) -> str:
    have = set(groups or [])
    return "".join(
        f'<span class="grp {css}">{label}</span>'
        for key, label, css in _GROUP_MARKS if key in have
    )


def _groups_attr(groups: list[str] | None) -> str:
    have = [key for key, _label, _css in _GROUP_MARKS if key in set(groups or [])]
    if not have:
        return ""
    return f' data-groups="{" ".join(have)}"'


def attr_row(aid: str, required: bool, attrs_db: dict, inherited: bool = False,
             schema: str = "", class_schema: str = "", groups: list[str] | None = None) -> str:
    meta, desc = attr_meta_html(aid, attrs_db)
    req  = '<span class="req">required</span>' if required else ''
    inh  = '<span class="inh">inherited</span>' if inherited else ''
    cls  = ' class="inherited"' if inherited else ''
    pkg  = f' data-pkg="{esc(schema)}"' if schema else ''
    return (f'<tr{cls}{pkg}{_groups_attr(groups)}>'
            f'<td class="aname">{esc(aid)}{req}{inh}'
            f'{_field_badge(schema, class_schema)}{_group_badge(groups)}</td>'
            f'<td>{meta}</td>'
            f'<td class="desc">{desc}</td>'
            f'</tr>')


def rel_row(rid: str, required: bool, target: Any,
            rels_db: dict, inherited: bool = False,
            inline_desc: str = "", schema: str = "", class_schema: str = "",
            groups: list[str] | None = None) -> str:
    thtml, desc = rel_info_html(rid, rels_db, target, inline_desc=inline_desc)
    req  = '<span class="req">required</span>' if required else ''
    inh  = '<span class="inh">inherited</span>' if inherited else ''
    cls  = ' class="inherited"' if inherited else ''
    pkg  = f' data-pkg="{esc(schema)}"' if schema else ''
    return (f'<tr{cls}{pkg}{_groups_attr(groups)}>'
            f'<td class="aname">{esc(rid)}{req}{inh}'
            f'{_field_badge(schema, class_schema)}{_group_badge(groups)}</td>'
            f'<td>{thtml}</td>'
            f'<td class="desc">{desc}</td>'
            f'</tr>')


def attr_table(rows_html: str, title: str = "") -> str:
    if not rows_html:
        return ""
    hdr = ""
    if title:
        hdr = f'<tr class="sub-hdr"><td colspan="3">{esc(title)}</td></tr>'
    return (f'<table>'
            f'<thead><tr><th>Attribute</th><th>Type / Constraints</th>'
            f'<th>Description</th></tr></thead>'
            f'<tbody>{hdr}{rows_html}</tbody>'
            f'</table>')


def rel_table(rows_html: str, title: str = "") -> str:
    if not rows_html:
        return ""
    hdr = ""
    if title:
        hdr = f'<tr class="sub-hdr"><td colspan="3">{esc(title)}</td></tr>'
    return (f'<table>'
            f'<thead><tr><th>Relation</th><th>Target</th>'
            f'<th>Description</th></tr></thead>'
            f'<tbody>{hdr}{rows_html}</tbody>'
            f'</table>')


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Entity card
# ─────────────────────────────────────────────────────────────────────────────

_issued_ids: set[str] = set()


def _html_id(name: str) -> str:
    """First use of a name keeps that id; later copies get a numeric suffix.

    A result such as TransmissionElement.PowerFlowResult is shown on every
    class it reports on. Repeating the same id would make every sidebar
    link land on the first copy.
    """
    if name not in _issued_ids:
        _issued_ids.add(name)
        return name
    n = 2
    while f"{name}-{n}" in _issued_ids:
        n += 1
    uid = f"{name}-{n}"
    _issued_ids.add(uid)
    return uid


def entity_card(name: str, entities: dict,
                attrs_db: dict, rels_db: dict) -> str:
    d = entities.get(name, {})
    # Entity description: use description, fall back to comment
    _edesc = d.get("description", "") or d.get("comment", "")
    desc   = esc(str(_edesc)).replace("\n", "<br>")
    plist = parents_of(name, entities)
    plinks = " ".join(
        f'<a href="#{esc(p)}" class="parent">{esc(p)}</a>' for p in plist
    )
    class_schema = str(d.get("_schema") or "")
    abs_badge = '<span class="abstract-badge">abstract</span>' if d.get("abstract") else ""
    pkg_badge = _pkg_badge(class_schema) if class_schema and class_schema != "base" else ""

    # Own attrs / rels
    own_a = [(a["id"], a.get("required", False), _usage_schema(a, d), _usage_groups(a))
             for a in (d.get("attributes") or [])]
    own_r = [(r["id"], r.get("required", False), r.get("target", ""),
              r.get("description", "") or r.get("comment", ""), _usage_schema(r, d),
              _usage_groups(r))
              for r in (d.get("relations") or [])]

    # Inherited
    inh_a, inh_r = collect_inherited(name, entities)

    a_rows = "".join(attr_row(a, req, attrs_db, schema=pkg, class_schema=class_schema, groups=gr)
                     for a, req, pkg, gr in own_a)
    a_rows += "".join(attr_row(a, req, attrs_db, True, schema=pkg, class_schema=class_schema, groups=gr)
                      for a, req, pkg, gr in inh_a)
    r_rows = "".join(rel_row(rid, req, tgt, rels_db, inline_desc=idesc, schema=pkg,
                             class_schema=class_schema, groups=gr)
                     for rid, req, tgt, idesc, pkg, gr in own_r)
    r_rows += "".join(rel_row(rid, req, tgt, rels_db, True, inline_desc=idesc, schema=pkg,
                              class_schema=class_schema, groups=gr)
                      for rid, req, tgt, idesc, pkg, gr in inh_r)

    tables = attr_table(a_rows) + rel_table(r_rows)

    # Result entities for this asset
    views_html = ""
    view_names = views_for_asset(name, entities)
    if view_names:
        vblocks: list[str] = []
        for vname in view_names:
            vblocks.append(_view_block(vname, entities, attrs_db, rels_db))
        views_html = (
            '<div class="views-section">'
            '<h4>Results</h4>'
            + "".join(vblocks) +
            '</div>'
        )

    card_pkg = f' data-pkg="{esc(class_schema)}"' if class_schema else ""
    return (
        f'<div class="card" id="{esc(_html_id(name))}"{card_pkg}>'
        f'<div class="card-header">'
        f'<span class="entity-name">{esc(name)}</span>{abs_badge}{pkg_badge}'
        f'<span class="parents">{plinks}</span>'
        f'</div>'
        f'<div class="entity-desc">{desc}</div>'
        f'{tables}'
        f'{views_html}'
        f'</div>'
    )


def _view_block(vname: str, entities: dict,
                attrs_db: dict, rels_db: dict) -> str:
    vd = entities.get(vname, {})
    class_schema = str(vd.get("_schema") or "")
    vp = parents_of(vname, entities)
    vplinks = " ".join(f'<a href="#{esc(p)}" class="parent">{esc(p)}</a>' for p in vp)
    pkg_badge = _pkg_badge(class_schema) if class_schema and class_schema != "base" else ""

    own_a = [(a["id"], a.get("required", False), _usage_schema(a, vd), _usage_groups(a))
             for a in (vd.get("attributes") or [])]
    own_r = [(r["id"], r.get("required", False), r.get("target", ""),
              r.get("description", "") or r.get("comment", ""), _usage_schema(r, vd),
              _usage_groups(r))
              for r in (vd.get("relations") or [])]
    vinh_a, vinh_r = collect_inherited(vname, entities)

    va = "".join(attr_row(a, req, attrs_db, schema=pkg, class_schema=class_schema, groups=gr)
                 for a, req, pkg, gr in own_a)
    va += "".join(attr_row(a, req, attrs_db, True, schema=pkg, class_schema=class_schema, groups=gr)
                  for a, req, pkg, gr in vinh_a)
    vr = "".join(rel_row(rid, req, tgt, rels_db, inline_desc=idc, schema=pkg,
                         class_schema=class_schema, groups=gr)
                 for rid, req, tgt, idc, pkg, gr in own_r)
    vr += "".join(rel_row(rid, req, tgt, rels_db, True, inline_desc=idc, schema=pkg,
                          class_schema=class_schema, groups=gr)
                  for rid, req, tgt, idc, pkg, gr in vinh_r)

    vtables = ""
    if va:
        vtables += (
            f'<table class="vtable">'
            f'<thead><tr><th>Attribute</th><th>Type / Constraints</th>'
            f'<th>Description</th></tr></thead>'
            f'<tbody>{va}</tbody></table>'
        )
    if vr:
        vtables += (
            f'<table class="vtable">'
            f'<thead><tr><th>Relation</th><th>Target</th>'
            f'<th>Description</th></tr></thead>'
            f'<tbody>{vr}</tbody></table>'
        )

    view_pkg = f' data-pkg="{esc(class_schema)}"' if class_schema else ""
    return (
        f'<div class="view-block" id="{esc(_html_id(vname))}"{view_pkg}>'
        f'<div class="view-header">'
        f'<span class="view-name">{esc(vname)}</span>{pkg_badge}{vplinks}'
        f'</div>'
        f'{vtables}'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Section builders
# ─────────────────────────────────────────────────────────────────────────────

_ASSET_GROUPS: list[tuple[str, list[str]]] = [
    ("Generation", [
        "GenerationUnit", "HydroGenerationUnit", "ExternalSupply",
    ]),
    ("Storage", [
        "HydroReservoir", "StorageUnit",
    ]),
    ("Transport / Network Assets", [
        "TransmissionLine", "Transformer", "GenericInterconnector",
        "HVDCLink", "TransmissionElement",
    ]),
    ("Demand", ["DemandUnit"]),
    ("Conversion", ["GenericConversionUnit"]),
]

_NETWORK_NAMES = [
    "NetworkNode", "ElectricalBus", "GasBus", "HeatBus",
    "HydrogenBus",
    "CarrierDomain", "Carrier", "GeographicalRegion",
    "Port", "ConversionPort",
]

_DOMAIN_SKIP = set(_NETWORK_NAMES)


def _declared_on(entities: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Classes that declare each attribute or relation themselves.

    Inherited use is not listed: the catalogue points at the class whose
    schema entry introduces the field.
    """
    attrs: dict[str, set[str]] = {}
    rels: dict[str, set[str]] = {}
    for name, d in entities.items():
        for a in d.get("attributes") or []:
            aid = a.get("id") if isinstance(a, dict) else None
            if aid:
                attrs.setdefault(aid, set()).add(name)
        for r in d.get("relations") or []:
            rid = r.get("id") if isinstance(r, dict) else None
            if rid:
                rels.setdefault(rid, set()).add(name)
    return (
        {k: sorted(v) for k, v in attrs.items()},
        {k: sorted(v) for k, v in rels.items()},
    )


def _class_links(names: list[str]) -> str:
    if not names:
        return '<span class="desc">—</span>'
    return ", ".join(
        f'<a href="#{esc(n)}" class="ref">{esc(n)}</a>' for n in names
    )


def _group_html(gname: str, members: list[str],
                entities: dict, attrs_db: dict, rels_db: dict) -> str:
    seen: set[str] = set()
    cards: list[str] = []
    for n in members:
        if n not in entities or n in seen:
            continue
        seen.add(n)
        cards.append(entity_card(n, entities, attrs_db, rels_db))
    if not cards:
        return ""
    return (
        f'<div class="group">'
        f'<h3 class="group-title">{esc(gname)}</h3>'
        + "".join(cards) +
        '</div>'
    )


def assets_html(entities: dict, attrs_db: dict, rels_db: dict) -> str:
    covered: set[str] = set()
    parts: list[str] = []
    for gname, members in _ASSET_GROUPS:
        avail = [n for n in members if n in entities]
        covered.update(avail)
        parts.append(_group_html(gname, avail, entities, attrs_db, rels_db))
    # Remaining assets not in predefined groups
    rest = [n for n, e in sorted(entities.items())
            if e.get("category") == "asset" and n not in covered]
    if rest:
        parts.append(_group_html("Other Assets", rest, entities, attrs_db, rels_db))
    return "".join(parts)


def network_html(entities: dict, attrs_db: dict, rels_db: dict) -> str:
    return "".join(
        entity_card(n, entities, attrs_db, rels_db)
        for n in _NETWORK_NAMES if n in entities
    )


def domain_html(entities: dict, attrs_db: dict, rels_db: dict) -> str:
    """Render domain entities grouped by their sub-category.

    Domain is a catch-all for everything that is not an Asset, Result,
    or Network node. Within it we distinguish:
      Technology Types — GeneratorType, StorageType, …
      Carriers & Geography — Carrier, CarrierDomain, GeographicalRegion
      Time Series — Profile, TimestampSeries
      Model Records — DispatchRunRecord, EnergySystemModel
      Abstract Bases — SemanticEntity, SystemAsset, Port, …
      Other — anything else
    """
    # Group by subcategory
    from collections import defaultdict
    groups: dict[str, list[str]] = defaultdict(list)
    for n, e in sorted(entities.items()):
        if e.get("category") != "domain" or n in _DOMAIN_SKIP:
            continue
        sub = domain_subcategory(n, entities)
        groups[sub].append(n)

    ORDER = ["Technology Types", "Carriers & Geography", "Time Series",
             "Model Records", "Abstract Bases", "Other"]
    parts: list[str] = []
    for sub in ORDER:
        names = groups.get(sub, [])
        if not names:
            continue
        cards = "".join(entity_card(n, entities, attrs_db, rels_db) for n in names)
        parts.append(
            f'<div class="group">'
            f'<h3 class="group-title">{sub}</h3>'
            f'{cards}'
            f'</div>'
        )
    return "".join(parts)


def attrs_catalogue_html(attrs_db: dict, declared: dict[str, list[str]],
                         groups: dict[str, list[str]] | None = None) -> str:
    rows = []
    for k, v in sorted(attrs_db.items()):
        meta, desc = attr_meta_html(k, attrs_db)
        # Label: prefer explicit label, fall back to formatted id
        label = esc(v.get("label", ""))
        u = v.get("unit", {})
        unit_str = ""
        if isinstance(u, dict):
            uc = u.get("constraints", {})
            if isinstance(uc, dict) and "enum" in uc:
                unit_str = " | ".join(esc(x) for x in uc["enum"])
        pkg = str(v.get("_schema") or "")
        badge = _pkg_badge(pkg) if len(_page_packages) > 1 and pkg and pkg != _page_packages[0] else ""
        field_groups = (groups or {}).get(k, [])
        data_pkg = f' data-pkg="{esc(pkg)}"' if pkg else ""
        rows.append(
            f'<tr class="cat-row" id="attr-{esc(k)}"{data_pkg}{_groups_attr(field_groups)}>'
            f'<td class="aname">{esc(k)}{badge}{_group_badge(field_groups)}</td>'
            f'<td style="color:var(--text)">{label}</td>'
            f'<td>{meta}</td>'
            f'<td style="font-family:var(--mono);font-size:11px;color:var(--accent3)">{unit_str}</td>'
            f'<td class="desc">{desc[:250]}</td>'
            f'<td class="usedby">{_class_links(declared.get(k, []))}</td>'
            f'</tr>'
        )
    return (
        '<div class="card" id="attribute-catalogue"><table>'
        '<thead><tr>'
        '<th>ID</th><th>Label</th><th>Type / Constraints</th>'
        '<th>Unit</th><th>Description</th><th>Declared on</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table></div>'
    )


def rels_catalogue_html(rels_db: dict, declared: dict[str, list[str]],
                        groups: dict[str, list[str]] | None = None) -> str:
    rows = []
    for k, v in sorted(rels_db.items()):
        targets = v.get("target", [])
        if isinstance(targets, str):
            targets = [targets]
        thtml = " | ".join(
            f'<a href="#{esc(t)}" class="ref">{esc(t)}</a>' for t in targets
        )
        desc = esc(str(v.get("description", ""))[:300])
        pkg = str(v.get("_schema") or "")
        badge = _pkg_badge(pkg) if len(_page_packages) > 1 and pkg and pkg != _page_packages[0] else ""
        field_groups = (groups or {}).get(k, [])
        data_pkg = f' data-pkg="{esc(pkg)}"' if pkg else ""
        rows.append(
            f'<tr class="cat-row" id="rel-{esc(k)}"{data_pkg}{_groups_attr(field_groups)}>'
            f'<td class="aname">{esc(k)}{badge}{_group_badge(field_groups)}</td>'
            f'<td>{thtml}</td>'
            f'<td class="desc">{desc}</td>'
            f'<td class="usedby">{_class_links(declared.get(k, []))}</td>'
            f'</tr>'
        )
    return (
        '<div class="card" id="relation-catalogue"><table>'
        '<thead><tr>'
        '<th>ID</th><th>Target(s)</th><th>Description</th><th>Declared on</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table></div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7.  Sidebar navigation
# ─────────────────────────────────────────────────────────────────────────────

def _nav_forest(
    names: list[str], entities: dict
) -> tuple[list[str], dict[str, list[str]]]:
    """Build a forest from *names* using each entity's ``parents``.

    A node is a root when none of its parents are in the same name set.
    Multi-parent entities attach under the first parent that is in the set
    (CESDM is almost entirely single-inheritance).
    """
    name_set = {n for n in names if n in entities}
    children: dict[str, list[str]] = {n: [] for n in name_set}
    roots: list[str] = []
    for n in sorted(name_set):
        parents_in = [p for p in parents_of(n, entities) if p in name_set]
        if not parents_in:
            roots.append(n)
        else:
            children[parents_in[0]].append(n)
    for kids in children.values():
        kids.sort()
    return roots, children


def _render_nav_tree(roots: list[str], entities: dict,
                     children: dict[str, list[str]],
                     seen: set[str]) -> str:
    """Render a nested, collapsible ``<ul>`` of nav links for *roots*."""
    items: list[str] = []
    for n in roots:
        if n in seen or n not in entities:
            continue
        seen.add(n)
        abs_cls = ' class="nav-abstract"' if entities[n].get("abstract") else ""
        pkg = str(entities[n].get("_schema") or "")
        data_pkg = f' data-pkg="{esc(pkg)}"' if pkg else ""
        kid_names = children.get(n, [])
        kids = _render_nav_tree(kid_names, entities, children, seen)
        if kids:
            items.append(
                f'<li class="nav-node has-kids"{data_pkg}>'
                f'<div class="nav-row">'
                f'<button type="button" class="nav-twist" aria-expanded="true" '
                f'aria-label="Toggle {esc(n)}"></button>'
                f'<a href="#{esc(n)}"{abs_cls}>{esc(n)}</a>'
                f'</div>'
                f'{kids}'
                f'</li>'
            )
        else:
            items.append(
                f'<li class="nav-node"{data_pkg}>'
                f'<div class="nav-row">'
                f'<span class="nav-twist-spacer"></span>'
                f'<a href="#{esc(n)}"{abs_cls}>{esc(n)}</a>'
                f'</div>'
                f'</li>'
            )
    if not items:
        return ""
    return '<ul class="nav-children">\n' + "\n".join(items) + "\n</ul>"


def sidebar_nav(entities: dict) -> str:
    """Single inheritance tree for all entities (no section headers)."""
    roots, children = _nav_forest(list(entities.keys()), entities)
    tree = _render_nav_tree(roots, entities, children, seen=set())
    if not tree:
        return ""
    return f'<li class="nav-tree">{tree}</li>'


# ─────────────────────────────────────────────────────────────────────────────
# 8.  CSS + JS (inline)
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """\
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

:root {
  --bg:       #0f1117;
  --surface:  #181c24;
  --surface2: #1e2330;
  --border:   #2a3045;
  --accent:   #4a9eff;
  --accent2:  #7ec8a4;
  --accent3:  #e5a050;
  --text:     #c8d0e0;
  --text-dim: #6b7899;
  --text-hi:  #eef2ff;
  --req:      #e05555;
  --inh:      #3a4a6b;
  --abstract: #6b4a9a;
  --mono:     'IBM Plex Mono', monospace;
  --sans:     'IBM Plex Sans', sans-serif;
  --nav-w:    300px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  font-size: 13px;
  line-height: 1.6;
  display: flex;
}

/* ── Sidebar ── */
#sidebar {
  width: var(--nav-w);
  min-height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  flex-shrink: 0;
  padding-bottom: 2rem;
}

.sidebar-logo {
  padding: 1.4rem 1.2rem 1rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.5rem;
}
.sidebar-logo h1 {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-family: var(--mono);
}
.sidebar-logo p { font-size: 11px; color: var(--text-dim); margin-top: 2px; }

#search {
  width: calc(100% - 1.6rem);
  margin: 0.6rem 0.8rem;
  padding: 0.45rem 0.7rem;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 12px;
  outline: none;
}
#search:focus { border-color: var(--accent); }
#search-status {
  display: block;
  margin: -0.15rem 0.9rem 0.35rem;
  min-height: 1.1em;
  font-size: 11px;
  color: var(--text-dim);
  font-family: var(--mono);
}
#search-empty {
  margin: 0.2rem 0 1.4rem;
  color: var(--text-dim);
  font-size: 13px;
}
.card, tr.cat-row { scroll-margin-top: 3.4rem; }

#nav-list { list-style: none; padding: 0.4rem 0 1rem; }
#nav-list .nav-tree { list-style: none; }
#nav-list .nav-children {
  list-style: none;
  margin: 0;
  padding: 0;
}
#nav-list .nav-children .nav-children {
  padding-left: 0.55rem;
  border-left: 1px solid var(--border);
  margin-left: 0.7rem;
}
#nav-list .nav-node { list-style: none; }
#nav-list .nav-node.collapsed > .nav-children { display: none; }
#nav-list .nav-row {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  min-width: 0;
}
#nav-list .nav-twist,
#nav-list .nav-twist-spacer {
  flex: 0 0 1.1rem;
  width: 1.1rem;
  height: 1.1rem;
}
#nav-list .nav-twist {
  border: none;
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  padding: 0;
  font-size: 9px;
  line-height: 1.1rem;
  border-radius: 2px;
}
#nav-list .nav-twist::before { content: "▼"; display: block; text-align: center; }
#nav-list .nav-node.collapsed > .nav-row > .nav-twist::before { content: "▶"; }
#nav-list .nav-twist:hover { color: var(--accent); background: var(--surface2); }
#nav-list a {
  display: block;
  flex: 1;
  min-width: 0;
  padding: 0.2rem 0.5rem 0.2rem 0.2rem;
  color: var(--text-dim);
  text-decoration: none;
  font-size: 12px;
  font-family: var(--mono);
  border-left: 2px solid transparent;
  transition: all 0.12s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
#nav-list a.nav-abstract { color: var(--text-dim); opacity: 0.75; font-style: italic; }
#nav-list a:hover { color: var(--text-hi); border-left-color: var(--accent); background: var(--surface2); opacity: 1; }
#nav-list a.active { color: var(--accent); border-left-color: var(--accent); opacity: 1; font-style: normal; }

/* ── Main ── */
#main {
  flex: 1;
  padding: 0 2rem 4rem;
  max-width: calc(100vw - var(--nav-w));
  overflow-x: hidden;
}

.page-header {
  padding: 2rem 0 1.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
}
.page-header h2 { font-size: 22px; font-weight: 300; color: var(--text-hi); letter-spacing: -0.02em; }
.page-header p  { font-size: 13px; color: var(--text-dim); margin-top: 0.4rem; }

/* ── Tabs ── */
.tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 50;
  padding-top: 0.5rem;
}
.tab-btn {
  padding: 0.6rem 1.4rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-dim);
  font-family: var(--mono);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.12s;
  letter-spacing: 0.04em;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-content { display: none; }
.tab-content.active { display: block; }

/* ── Groups / Cards ── */
.group { margin-bottom: 2.5rem; }
.group-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent3);
  font-family: var(--mono);
  margin-bottom: 1rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--border);
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-bottom: 1.2rem;
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  padding: 0.9rem 1.2rem 0.7rem;
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.entity-name { font-family: var(--mono); font-size: 14px; font-weight: 600; color: var(--text-hi); }
.abstract-badge {
  font-size: 10px; padding: 1px 6px; border-radius: 3px;
  background: var(--abstract); color: #dcc8ff;
  font-family: var(--mono); letter-spacing: 0.05em;
}
.parents { margin-left: auto; }
.parent {
  font-size: 11px; color: var(--text-dim); text-decoration: none;
  font-family: var(--mono); background: var(--surface);
  padding: 1px 6px; border-radius: 3px; border: 1px solid var(--border); margin-left: 4px;
}
.parent:hover { color: var(--accent); border-color: var(--accent); }

.entity-desc {
  padding: 0.7rem 1.2rem;
  font-size: 12px;
  color: var(--text-dim);
  line-height: 1.7;
  border-bottom: 1px solid var(--border);
  white-space: pre-line;
}
.entity-desc:empty { display: none; }

/* ── Tables ── */
table { width: 100%; border-collapse: collapse; font-size: 12px; }
table + table { border-top: 1px solid var(--border); }
thead tr { background: rgba(74,158,255,0.06); }
th {
  text-align: left; padding: 0.45rem 1.2rem;
  font-size: 10px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-dim);
  font-family: var(--mono); border-bottom: 1px solid var(--border);
}
td { padding: 0.4rem 1.2rem; border-bottom: 1px solid rgba(42,48,69,0.6); vertical-align: top; }
tr:last-child td { border-bottom: none; }
tr.inherited { opacity: 0.6; }
tr:hover { background: rgba(255,255,255,0.015); }
tr.sub-hdr td {
  background: rgba(74,158,255,0.04);
  font-size: 10px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--accent); font-family: var(--mono);
  padding: 0.35rem 1.2rem; border-bottom: 1px solid var(--border);
}

.aname { font-family: var(--mono); font-size: 12px; color: var(--accent2); white-space: nowrap; }
.desc  { color: var(--text-dim); font-size: 11px; max-width: 400px; }

.meta {
  display: inline-block; font-family: var(--mono); font-size: 11px;
  background: var(--surface2); border: 1px solid var(--border); border-radius: 3px;
  padding: 0 5px; margin: 1px 2px; color: var(--text);
}
.typ  { color: #7ec8ff; }
.unit { color: var(--accent3); }
.enum { color: #c8a0e8; font-size: 10px; }

.req {
  display: inline-block; font-size: 9px; padding: 0 5px; border-radius: 3px;
  background: var(--req); color: #fff; margin-left: 5px;
  font-family: var(--mono); vertical-align: middle;
}
.inh {
  display: inline-block; font-size: 9px; padding: 0 5px; border-radius: 3px;
  background: var(--inh); color: #aab; margin-left: 5px;
  font-family: var(--mono); vertical-align: middle;
}
.ref { color: var(--accent); text-decoration: none; font-family: var(--mono); font-size: 11px; }
.ref:hover { text-decoration: underline; }

/* ── Results ── */
.views-section {
  border-top: 2px solid var(--accent);
  background: rgba(74,158,255,0.03);
}
.views-section h4 {
  padding: 0.6rem 1.2rem 0.4rem;
  font-size: 10px; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--accent); font-family: var(--mono);
}
.view-block { border-top: 1px solid var(--border); margin-left: 1.2rem; }
.view-header {
  display: flex; align-items: baseline; gap: 0.5rem;
  padding: 0.5rem 0 0.3rem; flex-wrap: wrap;
}
.view-name { font-family: var(--mono); font-size: 12px; font-weight: 600; color: var(--accent); }
.vtable { font-size: 11.5px; border-top: 1px solid rgba(42,48,69,0.5); }
.vtable th  { font-size: 9.5px; padding: 0.35rem 1rem; }
.vtable td  { padding: 0.3rem 1rem; }
.vtable .aname { font-size: 11.5px; }

/* ── Legend ── */
.legend { display: flex; gap: 1.2rem; padding: 0.8rem 0; margin-bottom: 1rem; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-dim); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

@media (max-width: 768px) {
  #sidebar { display: none; }
  #main { max-width: 100vw; padding: 0 1rem 3rem; }
}

/* ── Domain info banner ── */
.domain-info {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent3);
  border-radius: 4px;
  padding: 0.8rem 1.2rem;
  font-size: 12px;
  color: var(--text-dim);
  line-height: 1.7;
  margin-bottom: 1.5rem;
}
.domain-info strong { color: var(--text); }
.domain-info code {
  font-family: var(--mono);
  font-size: 11px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 0 4px;
  color: var(--accent2);
}

/* ── Search highlight ── */
mark.hl {
  background: rgba(255, 213, 79, 0.35);
  color: inherit;
  border-radius: 2px;
  padding: 0 1px;
}

/* ── Filter bar ── */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0 1rem;
  flex-wrap: wrap;
}
.filter-bar label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-dim);
  cursor: pointer;
  user-select: none;
}
.filter-bar input[type=checkbox] {
  width: 14px; height: 14px;
  accent-color: var(--accent);
  cursor: pointer;
}
.filter-bar label:hover { color: var(--text); }
.filter-label {
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-dim);
}

.pkg {
  display: inline-block;
  margin-left: 8px;
  font-family: var(--sans);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  border-radius: 3px;
  padding: 0 5px;
  vertical-align: middle;
}
.pkg-base { color: var(--text-dim); border: 1px solid var(--inh); }
.pkg-power { color: var(--accent); border: 1px solid var(--accent); }
.pkg-dynamic { color: var(--accent3); border: 1px solid var(--accent3); }
.pkg-other { color: var(--text-dim); border: 1px solid var(--border); }
.grp {
  display: inline-block;
  margin-left: 8px;
  font-family: var(--sans);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.02em;
  border-radius: 3px;
  padding: 0 5px;
  vertical-align: middle;
}
.grp-technical { color: #c4b5fd; border: 1px solid #8b7cc9; }
.grp-dispatch { color: var(--accent2); border: 1px solid var(--accent2); }

.card.no-content { display: none; }

.usedby { font-size: 11px; line-height: 1.7; }
.usedby .ref { white-space: nowrap; }
"""

_JS = """\
// ── Tab switching ─────────────────────────────────────────────────────────────
function showTab(id, btn) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  btn.classList.add('active');
  const q = document.getElementById('search').value;
  if (q) applySearch(q);
}

// ── Full-content search ────────────────────────────────────────────────────────
// Searches entity name, description, attribute names, relation names,
// and each catalogue row (name, description, declaring classes).
// Highlights matches and hides non-matching cards and catalogue rows.

let _idx = null;

function buildIndex() {
  _idx = [];
  const selected = selectedPackages();
  const groups = selectedGroups();
  document.querySelectorAll('.card').forEach(card => {
    const id = card.id;
    if (!id || id === 'attribute-catalogue' || id === 'relation-catalogue') return;
    _idx.push({ el: card, id, full: indexText(card, selected, groups) });
  });
  document.querySelectorAll('tr.cat-row').forEach(row => {
    if (!pkgOn(row, selected) || !groupOn(row, groups)) return;
    _idx.push({ el: row, id: row.id, full: (row.textContent || '').toLowerCase() });
  });
}

function selectedPackages() {
  const boxes = [...document.querySelectorAll('input.pkg-filter')];
  const selected = new Set(boxes.filter(b => b.checked).map(b => b.value));
  const groups = selectedGroups();
  const base = document.querySelector('input.grp-filter[data-base-pkg]');
  const basePkg = base && base.dataset.basePkg;
  if (basePkg && groups && (groups.has('technical') || groups.has('dispatch'))) selected.add(basePkg);
  if (!boxes.length && !base) return null;
  return selected;
}

function pkgOn(el, selected) {
  if (!selected || !el) return true;
  const pkg = el.dataset.pkg;
  if (!pkg) return true;
  return selected.has(pkg);
}

function groupOn(el, selected) {
  if (!selected || !el) return true;
  const raw = el.dataset.groups || '';
  if (!raw) return true;
  return raw.split(/\\s+/).some(g => selected.has(g));
}

function selectedGroups() {
  const boxes = [...document.querySelectorAll('input.grp-filter')];
  if (!boxes.length) return null;
  return new Set(boxes.filter(b => b.checked).map(b => b.value));
}

function indexText(card, selected, groups) {
  const clone = card.cloneNode(true);
  clone.querySelectorAll('[data-pkg], [data-groups]').forEach(node => {
    if (!pkgOn(node, selected) || !groupOn(node, groups)) node.remove();
  });
  return (clone.textContent || '').toLowerCase();
}

function rowShown(tr) {
  if (tr.style.display === 'none') return false;
  const view = tr.closest('.view-block');
  return !(view && view.style.display === 'none');
}

function applySearch(raw) {
  if (!_idx) buildIndex();
  const q = raw.trim().toLowerCase();
  const tokens = q ? q.split(/ +/).filter(Boolean) : [];
  _idx.forEach(({ el, full }) => {
    if (!q || tokens.every(t => full.includes(t))) delete el.dataset.searchMiss;
    else el.dataset.searchMiss = '1';
    if (q && !el.dataset.searchMiss) addHL(el, tokens);
    else removeHL(el);
  });
  refreshVisibility();
  reportSearch(q);
  if (q) revealSearchHit();
}

// A sidebar entry matches when the class it points at is still visible.
// That includes a class kept because an attribute or relation name matched,
// not only a class whose own name contains the query.
function linkedCardVisible(a) {
  if (!a) return false;
  const id = (a.getAttribute('href') || '').replace(/^#/, '');
  const el = id && document.getElementById(id);
  if (!el || el.style.display === 'none') return false;
  const card = el.classList.contains('card') ? el : el.closest('.card');
  return !!card && card.id !== 'attribute-catalogue' && card.id !== 'relation-catalogue'
    && card.style.display !== 'none';
}

function updateNavFilter(q) {
  const selected = selectedPackages();
  const nodes = [...document.querySelectorAll('#nav-list li.nav-node')];
  nodes.forEach(li => {
    const a = li.querySelector(':scope > .nav-row > a');
    li.dataset.match = linkedCardVisible(a) ? '1' : '0';
  });
  nodes.forEach(li => {
    const keep = li.dataset.match === '1'
      || !!li.querySelector('li.nav-node[data-match="1"]');
    li.style.display = keep ? '' : 'none';
    if (keep && q) {
      let p = li.parentElement && li.parentElement.closest('li.nav-node');
      while (p) {
        p.classList.remove('collapsed');
        const twist = p.querySelector(':scope > .nav-row > .nav-twist');
        if (twist) twist.setAttribute('aria-expanded', 'true');
        p = p.parentElement && p.parentElement.closest('li.nav-node');
      }
    }
  });
}

function visibleSearchHit(root) {
  const card = [...root.querySelectorAll('.card')].find(c =>
    c.id && c.id !== 'attribute-catalogue' && c.id !== 'relation-catalogue'
    && c.style.display !== 'none');
  if (card) return card;
  return [...root.querySelectorAll('tr.cat-row')].find(r => r.style.display !== 'none') || null;
}

function revealSearchHit() {
  const active = document.querySelector('.tab-content.active');
  let hit = active && visibleSearchHit(active);
  if (!hit) {
    for (const tab of document.querySelectorAll('.tab-content')) {
      hit = visibleSearchHit(tab);
      if (!hit) continue;
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      tab.classList.add('active');
      const tabId = tab.id.replace(/^tab-/, '');
      const btn = [...document.querySelectorAll('.tab-btn')].find(b =>
        (b.getAttribute('onclick') || '').includes("'" + tabId + "'"));
      if (btn) btn.classList.add('active');
      break;
    }
  }
  const navHit = document.querySelector('#nav-list li.nav-node[data-match="1"] > .nav-row > a');
  if (navHit) navHit.scrollIntoView({ block: 'nearest' });
  if (!hit) return;
  const mark = hit.querySelector('mark.hl');
  (mark || hit).scrollIntoView({ block: 'center' });
}

function reportSearch(q) {
  const status = document.getElementById('search-status');
  const empty = document.getElementById('search-empty');
  if (!status || !empty) return;
  if (!q) {
    status.textContent = '';
    empty.hidden = true;
    return;
  }
  const cards = _idx.filter(x => x.el.classList.contains('card') && x.el.style.display !== 'none').length;
  const attrN = _idx.filter(x => x.id.startsWith('attr-') && x.el.style.display !== 'none').length;
  const relN = _idx.filter(x => x.id.startsWith('rel-') && x.el.style.display !== 'none').length;
  if (!cards && !attrN && !relN) {
    status.textContent = 'No matches';
    empty.hidden = false;
    return;
  }
  const bits = [];
  if (cards) bits.push(cards + (cards === 1 ? ' class' : ' classes'));
  if (attrN) bits.push(attrN + (attrN === 1 ? ' attribute' : ' attributes'));
  if (relN) bits.push(relN + (relN === 1 ? ' relation' : ' relations'));
  status.textContent = bits.join(' · ');
  empty.hidden = true;
}

// ── Collapsible inheritance tree ──────────────────────────────────────────────
document.querySelectorAll('#nav-list .nav-twist').forEach(btn => {
  btn.addEventListener('click', e => {
    e.preventDefault();
    e.stopPropagation();
    const li = btn.closest('.nav-node');
    if (!li) return;
    const collapsed = li.classList.toggle('collapsed');
    btn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
  });
});

// ── Highlight matching text ────────────────────────────────────────────────────
function addHL(card, tokens) {
  removeHL(card);
  const walk = document.createTreeWalker(card, NodeFilter.SHOW_TEXT);
  const nodes = [];
  let n;
  while ((n = walk.nextNode())) nodes.push(n);
  nodes.forEach(n => {
    if (!n.nodeValue.trim()) return;
    let html = xesc(n.nodeValue);
    tokens.forEach(t => {
      html = html.replace(new RegExp(xre(t), 'gi'), m => `<mark class="hl">${m}</mark>`);
    });
    if (html !== xesc(n.nodeValue)) {
      const s = document.createElement('span');
      s.className = 'hl-wrap'; s.innerHTML = html;
      n.parentNode.replaceChild(s, n);
    }
  });
}
function removeHL(card) {
  card.querySelectorAll('.hl-wrap').forEach(s =>
    s.parentNode.replaceChild(document.createTextNode(s.textContent), s));
}
function xesc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function xre(s)  { return s.replace(/[-.*+?^${}()|[\\]]/g, '\\$&'); }

// ── Smart nav link: switch tab if needed, then scroll ─────────────────────────
function navTo(id) {
  const card = document.getElementById(id);
  if (!card) return;
  const tab = card.closest('.tab-content');
  if (tab && !tab.classList.contains('active')) {
    const tabId = tab.id.replace('tab-', '');
    const btn = document.querySelector(`.tab-btn[onclick*="'${tabId}'"]`);
    if (btn) showTab(tabId, btn);
  }
  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
document.querySelectorAll('#nav-list a').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    navTo(a.getAttribute('href').slice(1));
    document.querySelectorAll('#nav-list a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
  });
});
document.querySelectorAll('a.ref, a.parent').forEach(a => {
  a.addEventListener('click', e => {
    const href = a.getAttribute('href') || '';
    if (!href.startsWith('#')) return;
    e.preventDefault();
    navTo(href.slice(1));
  });
});

// Diagram clicks arrive as a fragment (schema-reference.html#ClassName).
// Cards outside the Assets tab sit in display:none panels, so the browser
// cannot scroll to them until this page opens the right tab.
function openHash() {
  let id = '';
  try {
    id = decodeURIComponent((location.hash || '').replace(/^#/, ''));
  } catch (err) {
    return;
  }
  if (!id) return;
  navTo(id);
  document.querySelectorAll('#nav-list a').forEach(a =>
    a.classList.toggle('active', a.getAttribute('href') === '#' + id));
}
window.addEventListener('hashchange', openHash);
filterPackages();
openHash();

// ── Scroll-based active nav highlight ─────────────────────────────────────────
const obs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const id = e.target.id;
      document.querySelectorAll('#nav-list a').forEach(a =>
        a.classList.toggle('active', a.getAttribute('href') === '#' + id));
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll('[id]').forEach(el => obs.observe(el));

// ── Schema packages, abstract classes, and empty cards ─────────────────────
function refreshVisibility() {
  const selected = selectedPackages();
  const groups = selectedGroups();
  document.querySelectorAll('.view-block').forEach(block => {
    block.style.display = pkgOn(block, selected) ? '' : 'none';
  });
  document.querySelectorAll('.views-section').forEach(sec => {
    const any = [...sec.querySelectorAll('.view-block')].some(b => b.style.display !== 'none');
    sec.style.display = any ? '' : 'none';
  });
  document.querySelectorAll('tr[data-pkg]:not(.cat-row), tr[data-groups]:not(.cat-row)').forEach(tr => {
    tr.style.display = (pkgOn(tr, selected) && groupOn(tr, groups)) ? '' : 'none';
  });
  document.querySelectorAll('.card table, .view-block table').forEach(table => {
    if (table.closest('#tab-attrs, #tab-rels')) return;
    const dataRows = [...table.querySelectorAll('tbody tr[data-pkg]')];
    const any = dataRows.some(tr => tr.style.display !== 'none');
    table.style.display = dataRows.length && !any ? 'none' : '';
  });

  const hideAbstract = document.getElementById('chk-no-abstract')?.checked;
  const onlyContent = document.getElementById('chk-content')?.checked;
  document.querySelectorAll('.card').forEach(card => {
    if (card.id === 'attribute-catalogue' || card.id === 'relation-catalogue') {
      card.style.display = '';
      return;
    }
    // A base class such as ElectricalBus stays when Power flow is the only
    // box ticked, because its power-flow rows are still visible. ShuntUnit
    // is the only class defined in that package.
    let hide = card.dataset.searchMiss === '1';
    if (!hide && !pkgOn(card, selected) && !cardHasShownField(card)) hide = true;
    if (!hide && hideAbstract && card.querySelector('.abstract-badge')) hide = true;
    if (!hide && onlyContent) {
      const hasOwn = [...card.querySelectorAll('tbody tr:not(.inherited)')].some(tr =>
        rowShown(tr) && tr.querySelector('.aname'));
      if (!hasOwn) hide = true;
    }
    card.style.display = hide ? 'none' : '';
  });
  document.querySelectorAll('tr.cat-row').forEach(row => {
    const hide = !pkgOn(row, selected) || !groupOn(row, groups) || row.dataset.searchMiss === '1';
    row.style.display = hide ? 'none' : '';
  });
  document.querySelectorAll('.group').forEach(g => {
    g.style.display = [...g.querySelectorAll('.card')].some(c => c.style.display !== 'none')
      ? '' : 'none';
  });
  const q = (document.getElementById('search')?.value || '').trim();
  updateNavFilter(q);
}

function cardHasShownField(card) {
  return [...card.querySelectorAll('tbody tr')].some(tr =>
    tr.style.display !== 'none' && tr.querySelector('.aname'));
}

function filterPackages() {
  _idx = null;
  const q = (document.getElementById('search')?.value || '').trim();
  if (q) applySearch(q);
  else refreshVisibility();
}

function filterGroups() {
  filterPackages();
}

function filterContent() {
  _idx = null;
  refreshVisibility();
}

function filterAbstract() {
  refreshVisibility();
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# 9.  Full page assembly
# ─────────────────────────────────────────────────────────────────────────────

def _schema_version(schema_dir: pathlib.Path) -> str | None:
    manifest = schema_dir / "SCHEMA_MANIFEST.yaml"
    if not manifest.is_file():
        return None
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    return data.get("version")


def _declared_groups(entities: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """technical/dispatch tags used anywhere a field is declared."""
    attrs: dict[str, set[str]] = {}
    rels: dict[str, set[str]] = {}
    for entity in entities.values():
        for item in entity.get("attributes") or []:
            if isinstance(item, dict) and item.get("id"):
                attrs.setdefault(item["id"], set()).update(_usage_groups(item))
        for item in entity.get("relations") or []:
            if isinstance(item, dict) and item.get("id"):
                rels.setdefault(item["id"], set()).update(_usage_groups(item))
    order = [key for key, _label, _css in _GROUP_MARKS]

    def ordered(found: set[str]) -> list[str]:
        return [key for key in order if key in found]

    return (
        {key: ordered(value) for key, value in attrs.items()},
        {key: ordered(value) for key, value in rels.items()},
    )


def _package_filter_html(packages: list[str]) -> str:
    parts: list[str] = []
    # Technical and Dispatch stand in for the base package. The page opens
    # on those two; power flow and dynamic stay opt-in.
    if "base" in packages:
        parts.append(
            '<label><input type="checkbox" class="grp-filter" value="technical" '
            'data-base-pkg="base" checked onchange="filterGroups()"> Technical</label>'
            '<label><input type="checkbox" class="grp-filter" value="dispatch" '
            'data-base-pkg="base" checked onchange="filterGroups()"> Dispatch</label>'
        )
    if len(packages) >= 2:
        for pkg in packages:
            if pkg == "base":
                continue
            parts.append(
                '<label title="cesdm/schemas/{pkg}">'
                '<input type="checkbox" class="pkg-filter" value="{pkg}" '
                'onchange="filterPackages()"> {label}'
                '</label>'.format(pkg=esc(pkg), label=esc(_pkg_label(pkg)))
            )
    if not parts:
        return ""
    return '<span class="filter-label">Schemas</span>' + "".join(parts)


def build_page(schema_dir: pathlib.Path | list[pathlib.Path]) -> str:
    global _page_packages
    paths = [schema_dir] if isinstance(schema_dir, pathlib.Path) else list(schema_dir)
    _issued_ids.clear()
    entities, attrs_db, rels_db = load_schema(paths)
    schema_dir = paths[0]
    packages: list[str] = []
    for entity in entities.values():
        pkg = entity.get("_schema")
        if pkg and pkg not in packages:
            packages.append(str(pkg))
    _page_packages = packages

    # Annotate each entity with its category
    for name, d in entities.items():
        d["category"] = categorise(name, entities)
        d["views"]    = views_for_asset(name, entities)

    nav   = sidebar_nav(entities)
    tab_a = assets_html(entities, attrs_db, rels_db)
    tab_n = network_html(entities, attrs_db, rels_db)
    tab_d = domain_html(entities, attrs_db, rels_db)
    attr_decl, rel_decl = _declared_on(entities)
    attr_groups, rel_groups = _declared_groups(entities)
    tab_c = attrs_catalogue_html(attrs_db, attr_decl, attr_groups)
    tab_r = rels_catalogue_html(rels_db, rel_decl, rel_groups)

    schema_name = schema_dir.resolve().name
    pkg_filters = _package_filter_html(packages)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CESDM Schema Reference — {esc(schema_name)}</title>
<style>{_CSS}</style>
</head>
<body>

<aside id="sidebar">
  <div class="sidebar-logo">
    <h1>CESDM Schemas</h1>
    <p>Common Energy System Domain Model</p>
  </div>
  <input type="text" id="search"
         placeholder="Search entities, attributes, relations…"
         oninput="applySearch(this.value)">
  <span id="search-status"></span>
  <ul id="nav-list">
    {nav}
  </ul>
</aside>

<main id="main">
  <div class="page-header">
    <h2>CESDM Schema Reference</h2>
    <p>Entity definitions, attributes and relations —
    generated from CESDM schemas{f" v{version}" if (version := _schema_version(schema_dir)) else ""}
    ({len(entities)} entities · {len(attrs_db)} attributes · {len(rels_db)} relations).</p>
  </div>

  <div class="legend">
    <span class="legend-item"><span class="req">required</span> Required field</span>
    <span class="legend-item"><span class="inh">inherited</span> Inherited from parent</span>
    <span class="legend-item"><span class="abstract-badge">abstract</span> Abstract class</span>
    <span class="legend-item" style="color:#7ec8a4">■ </span>
    <span style="font-size:11px;color:var(--text-dim)">Attributes &amp; relations</span>
  </div>

  <div class="filter-bar">
    {pkg_filters}
    <label>
      <input type="checkbox" id="chk-content" onchange="filterContent()">
      Show only entities with attributes or relations
    </label>
    <label>
      <input type="checkbox" id="chk-no-abstract" onchange="filterAbstract()">
      Hide abstract classes
    </label>
  </div>

  <div class="tabs">
    <button class="tab-btn active"  onclick="showTab('assets',this)">Assets</button>
    <button class="tab-btn"        onclick="showTab('network',this)">Network &amp; Carriers</button>
    <button class="tab-btn" onclick="showTab('domain',this)"
            title="Technology types, carriers, time-series, agents, abstract base classes — everything that is not an Asset or a Network node">
      Domain &amp; Types
    </button>
    <button class="tab-btn"        onclick="showTab('attrs',this)">Attribute Catalogue</button>
    <button class="tab-btn"        onclick="showTab('rels',this)">Relation Catalogue</button>
  </div>

  <p id="search-empty" hidden>No class, attribute, or relation matches.</p>

  <div id="tab-assets"  class="tab-content active">{tab_a}</div>
  <div id="tab-network" class="tab-content">{tab_n}</div>
  <div id="tab-domain"  class="tab-content">
    <div class="domain-info">
      <strong>What is a "Domain" entity?</strong>
      These entities do not descend from <code>EnergyAssetInstance</code> or <code>NetworkNode</code>. They are supporting concepts — technology type registries, energy carriers, time-series containers, agent/socio-economic actors, and abstract base classes. The label is a catch-all: the entities share no single role, only the absence of a more specific classification.
    </div>
    {tab_d}
  </div>
  <div id="tab-attrs"   class="tab-content">{tab_c}</div>
  <div id="tab-rels"    class="tab-content">{tab_r}</div>
</main>

<script>{_JS}</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# 10. CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate a self-contained HTML reference from CESDM YAML schemas."
    )
    parser.add_argument(
        "--schema_dir",
        action="append",
        default=None,
        help="Schema directory. Repeat to load several, in order. "
             "The first directory's extends are loaded first, and augmentations "
             "are applied, as in build_model_from_yaml.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output HTML file path. Default: cesdm_schema_ref.html, "
             "or the last positional argument when it ends in .html.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Schema directories, optionally followed by the output .html path.",
    )
    args = parser.parse_args(argv)

    positionals = list(args.paths)
    output = args.output
    if output is None and positionals and str(positionals[-1]).endswith(".html"):
        output = positionals.pop()
    if output is None:
        output = "cesdm_schema_ref.html"
    schema_dirs = [pathlib.Path(p) for p in (args.schema_dir or [])] + [
        pathlib.Path(p) for p in positionals
    ]
    if not schema_dirs:
        schema_dirs = [pathlib.Path("cesdm/schemas/base")]
    missing = [p for p in schema_dirs if not p.exists()]
    if missing:
        sys.exit("Error: schema directory not found: " + ", ".join(str(p) for p in missing))

    print("Reading schemas from: " + ", ".join(str(p.resolve()) for p in schema_dirs), flush=True)
    page = build_page(schema_dirs)
    out = pathlib.Path(output)
    out.write_text(page, encoding="utf-8")
    size_kb = len(page) / 1024
    print(f"Written {size_kb:.0f} KB → {out.resolve()}")


if __name__ == "__main__":
    main()
