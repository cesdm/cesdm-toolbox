#!/usr/bin/env python3
"""Generate UML-style class diagrams of the CESDM schema as Mermaid pages.

    python -m tools.generate_schema_diagrams            # writes docs/reference/schema-diagrams/
    python -m tools.generate_schema_diagrams --check    # fails if the pages are out of date

Each page is one *view* of the schema: a family of classes drawn with their own
attributes, inheritance arrows and relations. Classes that a view only refers
to (a parent or a relation target from another view) appear as small stubs.

The pages are generated from the same schema load as build_model_from_yaml.
Pass one directory, or several in order. The first directory's ``extends``
entries are loaded first, and augmentations.yaml on any loaded directory is
applied to the existing classes. The default load is the dispatch base plus
`schemas/cesdm_power_flow` and `schemas/cesdm_dynamic`. Every class is
drawn in full in exactly one view: a class not reached by any view root lands
in "Other classes", and --check fails.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cesdm_toolbox import build_model_from_yaml  # noqa: E402

OUT_DIR = REPO / "docs" / "reference" / "schema-diagrams"
# Markdown links are resolved from the source file; Mermaid click targets are
# raw URLs, resolved from the page URL (use_directory_urls: true).
SCHEMA_REFERENCE_MD = "../schema-reference.html"
CLICK_BASE_INDEX = "../schema-reference.html"       # from /reference/schema-diagrams/
CLICK_BASE_VIEW = CLICK_BASE_INDEX                  # a view page adds one "../" itself

# --- Views ------------------------------------------------------------------
# A view is drawn from its root classes and all their subclasses. New
# subclasses in the schema join their root's view automatically.
VIEWS = [
    {
        "slug": "assets", "short": "assets",
        "title": "Assets: generation, storage, demand",
        "lead": "Physical assets that inject, withdraw or store energy at one node or region.",
        "roots": ["SystemAsset", "GenerationUnit", "StorageUnit", "HydraulicStorageUnit",
                  "DemandUnit", "ExternalSupply", "ShuntUnit"],
        "exclude_subtrees": ["ConversionUnit", "TransmissionElement"],
    },
    {
        "slug": "network", "short": "network",
        "title": "Network and transmission",
        "lead": "Nodes per carrier domain, the elements that connect them, and the regions and zones they sit in.",
        "roots": ["NetworkNode", "TransmissionElement", "CarrierDomain", "GeographicalRegion", "MarketZone"],
    },
    {
        "slug": "conversion", "short": "conversion",
        "title": "Conversion units",
        "lead": "Assets that link two carrier domains, and their ports.",
        "roots": ["ConversionUnit", "Port"],
    },
    {
        "slug": "technologies", "short": "technologies",
        "title": "Technologies, carriers and resources",
        "lead": "Shared types that assets point to with hasTechnology, hasCarrier or hasInputResource.",
        "roots": ["EnergyTechnologyType", "Carrier", "NaturalResource"],
    },
    {
        "slug": "time-series", "short": "time series",
        "title": "System and time series",
        "lead": "The model container, profiles and the time axis they share.",
        "roots": ["EnergySystemModel", "Profile", "TimestampSeries"],
    },
    {
        "slug": "dynamics", "short": "dynamics",
        "title": "Dynamic models and controllers",
        "lead": "Machine models and the exciters, governors and stabilisers a generator links to.",
        "roots": ["DynamicMachineModelType", "Controller"],
    },
    {
        "slug": "results", "short": "results",
        "title": "Results and run records",
        "lead": "Outputs of an analysis, linked to the assets they report on, and the run that produced them.",
        "roots": ["Result", "RunRecord"],
    },
]
OVERVIEW_ROOT = "SemanticEntity"


# --- Schema access --------------------------------------------------------------
class Schema:
    def __init__(self, schema_dir: Path | list[Path]):
        self.paths = [schema_dir] if isinstance(schema_dir, Path) else list(schema_dir)
        loaded = [str(path) for path in self.paths]
        # One path: that directory's extends and augmentations apply.
        # Several paths: later directories add classes on top of earlier ones.
        self.model = build_model_from_yaml(loaded[0] if len(loaded) == 1 else loaded)
        self.classes = self.model.classes
        self.children: dict[str, list[str]] = defaultdict(list)
        for name, cls in self.classes.items():
            for parent in cls.parents:
                self.children[parent].append(name)
        for kids in self.children.values():
            kids.sort()

    def subtree(self, root: str, exclude: set[str] = frozenset()) -> list[str]:
        out, stack = [], [root]
        while stack:
            name = stack.pop()
            if name in exclude or name not in self.classes:
                continue
            out.append(name)
            stack.extend(reversed(self.children.get(name, [])))
        return out

    def _inherited(self, name: str, kind: str) -> set[str]:
        return set().union(*(set(getattr(self.classes[p], kind)) for p in self.classes[name].parents)) \
            if self.classes[name].parents else set()

    def own_attributes(self, name: str):
        cls = self.classes[name]
        inherited = self._inherited(name, "attributes")
        return [a for key, a in cls.attributes.items() if key not in inherited]

    def own_relations(self, name: str):
        cls = self.classes[name]
        inherited = self._inherited(name, "relations")
        return [r for key, r in cls.relations.items() if key not in inherited]


# --- Mermaid helpers ------------------------------------------------------------
GROUP_ORDER = ["", "topology", "spatial", "dispatch", "capacity_expansion", "power_flow",
               "technical", "dynamics"]


def node_id(name: str) -> str:
    return name.replace(".", "_")


def unit_of(attr) -> str:
    unit = attr.unit or {}
    allowed = (unit.get("constraints") or {}).get("enum") if isinstance(unit, dict) else None
    return " / ".join(allowed) if allowed else ""


def _safe(text: str) -> str:
    """Mermaid reads a member line containing ( ) as a method; use look-alike brackets."""
    return text.replace("(", "\u27ee").replace(")", "\u27ef")


def member(attr) -> str:
    text = f"+{attr.name} : {attr.type}"
    unit = _safe(unit_of(attr))
    if unit and unit != "-":
        text += f" [{unit}]"
    if attr.required:
        text += " «required»"
    return text


def multiplicity(rel) -> str:
    upper = "*" if str(rel.cardinality).endswith("*") else "1"
    lower = "1" if rel.required else "0"
    return lower if lower == upper else f"{lower}..{upper}"


def group_of(attr) -> str:
    groups = attr.belongsToGroup or []
    return groups[0] if groups else ""


def class_block(schema: Schema, name: str, full: bool, elsewhere: str | None = None) -> list[str]:
    """One class box. `elsewhere` = title of the view that draws it in full."""
    nid = node_id(name)
    cls = schema.classes[name]
    body: list[str] = []
    tags = (["abstract"] if cls.abstract else []) + ([f"see {elsewhere}"] if elsewhere else [])
    if tags:
        body.append(f"<<{', '.join(tags)}>>")
    if full:
        attrs = sorted(schema.own_attributes(name),
                       key=lambda a: (GROUP_ORDER.index(group_of(a)) if group_of(a) in GROUP_ORDER else 99, a.name))
        current = None
        for attr in attrs:
            group = group_of(attr)
            if group and group != current:
                body.append(f"«{group}»")
            current = group
            body.append(member(attr))
    if not body:
        return [f'    class {nid}["{name}"]']
    return [f'    class {nid}["{name}"] {{', *(f"        {line}" for line in body), "    }"]


def diagram(schema: Schema, members: list[str], with_attributes: bool, assignment: dict[str, dict],
            here: str | None, direction: str = "LR") -> str:
    """Mermaid classDiagram. Classes in `members` are drawn in full; parents and relation
    targets from other views appear as stubs that link to their own view."""
    full = set(members)
    referenced: set[str] = set()
    edges: list[str] = []

    for name in members:
        for parent in schema.classes[name].parents:
            if parent not in full:
                referenced.add(parent)
            edges.append(f"    {node_id(parent)} <|-- {node_id(name)}")
        if with_attributes:
            for rel in sorted(schema.own_relations(name), key=lambda r: r.name):
                for target in rel.targets:
                    if target not in schema.classes:
                        continue
                    if target not in full:
                        referenced.add(target)
                    edges.append(f'    {node_id(name)} --> "{multiplicity(rel)}" {node_id(target)} : {rel.name}')

    # A `cesdm-uml` fence holds Mermaid code. docs/javascripts/schema-diagrams.js renders it at
    # natural size with zoom controls (Material's own Mermaid support shrinks it to the column).
    lines = ["```cesdm-uml", "classDiagram", f"    direction {direction}"]
    for name in members:
        lines += class_block(schema, name, full=with_attributes)
    for name in sorted(referenced):
        view = assignment.get(name)
        lines += class_block(schema, name, full=False, elsewhere=view["short"] if view else None)
    lines += edges

    # Every class opens its card in the schema reference. The fragment is the
    # class name, dots included; the reference page reads it on load and shows
    # the tab that holds the card. A stub is still marked with the view where
    # it is drawn in full, but the click does not leave for that view.
    prefix = "" if here is None else "../"          # page URL depth (use_directory_urls)
    for name in list(members) + sorted(referenced):
        target = f"{prefix}{CLICK_BASE_INDEX}#{name}"
        lines.append(
            f'    click {node_id(name)} href "{target}" "{name} in the schema reference"'
        )
    lines.append("```")
    return "\n".join(lines)


# --- Pages ----------------------------------------------------------------------
HEADER = ("---\nhide:\n  - navigation\n  - toc\n---\n\n"
          "<!-- AUTO-GENERATED by tools/generate_schema_diagrams.py — do not edit by hand. -->\n\n")

LEGEND = """!!! info "How to read these diagrams"
    Each box is a class; «abstract» classes are never instantiated. A hollow arrow points from a subclass
    to its parent. A class lists only its **own** attributes, as `name : type [unit]`, grouped under their
    «attribute group»; inherited attributes appear on the parent. A plain arrow is a relation, labelled with
    its name and multiplicity (`0..1` optional, `1` required). A box without attributes, marked with a view
    name, is drawn in full in that view. Click any class to open it in the [schema reference]({ref}).
    Use the buttons above a diagram to zoom, and drag or scroll inside it to move around.
"""


def page(schema: Schema, view: dict, members: list[str], assignment: dict[str, dict]) -> str:
    n_attr = sum(len(schema.own_attributes(m)) for m in members)
    n_rel = sum(len(schema.own_relations(m)) for m in members)
    return (
        HEADER
        + f"# {view['title']}\n\n{view['lead']}\n\n"
        + f"{len(members)} classes, {n_attr} own attributes, {n_rel} own relations. "
          "[All views](index.md).\n\n"
        + LEGEND.format(ref=SCHEMA_REFERENCE_MD) + "\n"
        + diagram(schema, members, with_attributes=True, assignment=assignment, here=view["slug"]) + "\n"
    )


def overview(schema: Schema, assignment: dict[str, dict], views: list[dict]) -> str:
    rows = "\n".join(
        f"| [{v['title']}]({v['slug']}.md) | {len(v['members'])} | {v['lead']} |" for v in views
    )
    manifest = getattr(schema.model, "schema_manifest", None)
    version = getattr(manifest, "version", None)
    subject = f"CESDM schema {version}" if version else "the CESDM schema"
    sources = []
    for path in schema.paths:
        try:
            sources.append(f"`{path.resolve().relative_to(REPO).as_posix()}`")
        except ValueError:
            sources.append(f"`{path}`")
    source = ", ".join(sources) if sources else "`schemas/cesdm`"
    return (
        HEADER
        + "# Schema diagrams\n\n"
        + f"UML-style class diagrams of {subject}, generated from {source}: "
          f"{len(schema.classes)} classes. Each view draws one family of classes with their attributes "
          "and relations. The tree below shows inheritance only; click a class to open its view.\n\n"
        + "| View | Classes | What it shows |\n|---|---|---|\n" + rows + "\n\n"
        + "## Class hierarchy\n\n"
        + diagram(schema, schema.subtree(OVERVIEW_ROOT), with_attributes=False,
                  assignment=assignment, here=None) + "\n"
    )


def build(schema: Schema) -> tuple[dict[str, str], list[str]]:
    views = [dict(v) for v in VIEWS]
    taken: set[str] = set()
    for view in views:
        exclude = set(view.get("exclude_subtrees", []))
        members: list[str] = []
        for root in view["roots"]:
            for name in schema.subtree(root, exclude):
                if name not in taken and name not in members:
                    members.append(name)
        taken.update(members)
        view["members"] = members
    views = [view for view in views if view["members"]]

    leftovers = [n for n in sorted(schema.classes) if n not in taken and n != OVERVIEW_ROOT]
    if leftovers:
        views.append({"slug": "other", "title": "Other classes", "short": "other",
                      "lead": "Classes not yet assigned to a view in tools/generate_schema_diagrams.py.",
                      "members": leftovers})

    assignment = {name: view for view in views for name in view["members"]}
    pages = {f"{v['slug']}.md": page(schema, v, v["members"], assignment) for v in views}
    pages["index.md"] = overview(schema, assignment, views)
    return pages, leftovers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--schemas", type=Path, nargs="+",
        default=[
            REPO / "schemas" / "cesdm",
            REPO / "schemas" / "cesdm_power_flow",
            REPO / "schemas" / "cesdm_dynamic",
        ],
        help="Schema directories, loaded in order like build_model_from_yaml. "
             "Augmentations in those directories are included. "
             "The default is the dispatch base plus both analysis packages.",
    )
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--check", action="store_true", help="fail if the pages on disk are out of date")
    args = parser.parse_args()

    pages, leftovers = build(Schema(args.schemas))

    if args.check:
        stale = []
        for name, text in pages.items():
            path = args.out / name
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
                old = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
                sys.stdout.writelines(f"{line}\n" for line in difflib.unified_diff(
                    old, text.splitlines(), str(path), "generated", lineterm="", n=1))
        if stale or leftovers:
            print(f"Out of date: {', '.join(stale) or '-'}; unassigned classes: {', '.join(leftovers) or '-'}")
            print("Run: python -m tools.generate_schema_diagrams")
            return 1
        print(f"Schema diagrams up to date ({len(pages)} pages).")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in pages.items():
        (args.out / name).write_text(text, encoding="utf-8")
    print(f"Wrote {len(pages)} pages to {args.out}")
    if leftovers:
        print(f"Unassigned classes (drawn under 'Other classes'): {', '.join(leftovers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
