"""cesdm_assumptions_dashboard.py

Build a Scenario-Assumptions-style HTML dashboard from a CESDM hierarchical YAML.

The page shows installed capacity, demand, storage, renewable resource potential
and cross-border transfer limits — the same families as the Sensitivities
dashboard's Scenario Assumptions tab, derived from one CESDM model.

    python tools/cesdm_assumptions_dashboard.py --yaml path/to/model.yaml
    cesdm-assumptions-dashboard --yaml path/to/model.yaml --out assumptions.html
    cesdm-assumptions-dashboard --serve
    cesdm-assumptions-dashboard --serve --yaml path/to/model.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import webbrowser
from collections import defaultdict
from email import message_from_bytes
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tools.explore_cesdm_model import (
        GENERATION_ASSET_CLASSES,
        _DEFAULT_SCHEMAS,
        _REPO_ROOT,
        _af,
        _av,
        _rel,
        annual_renewable_energy_by_country,
        build_asset_to_node,
        build_dispatch_index,
        build_node_to_country,
        cross_border_capacity_summary,
        demand_by_country,
        interconnector_flows,
        iter_entities_by_classes,
        model_entity_counts,
        storage_capacity_by_country,
        summarize_totals_by_country,
        transformer_summary,
        transmission_lines_summary,
    )
except ImportError:  # python tools/cesdm_assumptions_dashboard.py
    from explore_cesdm_model import (
        GENERATION_ASSET_CLASSES,
        _DEFAULT_SCHEMAS,
        _REPO_ROOT,
        _af,
        _av,
        _rel,
        annual_renewable_energy_by_country,
        build_asset_to_node,
        build_dispatch_index,
        build_node_to_country,
        cross_border_capacity_summary,
        demand_by_country,
        interconnector_flows,
        iter_entities_by_classes,
        model_entity_counts,
        storage_capacity_by_country,
        summarize_totals_by_country,
        transformer_summary,
        transmission_lines_summary,
    )

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cesdm_toolbox import CesdmModel, build_model_from_yaml  # noqa: E402

TEMPLATE_PATH = Path(__file__).resolve().with_name("cesdm_assumptions_dashboard.html")


def _country_label(code: str) -> str:
    return "Unspecified" if code in (None, "", "??") else str(code)


def _round(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return round(number, 6)


def _round_map(mapping: Dict[str, float]) -> Dict[str, float]:
    return {str(key): _round(val) or 0.0 for key, val in mapping.items() if (_round(val) or 0.0)}


def _pretty_tech_id(tech_id: str) -> str:
    parts = [p for p in tech_id.replace("_", ".").split(".") if p and p.lower() not in {"generation", "tech"}]
    return " ".join(parts) if parts else tech_id


def technology_label(model: CesdmModel, ent: Any, asset_cls: str, asset_id: str) -> str:
    """Prefer GeneratorType.long_name, then hasTechnology id, then class name."""
    typed = _av(ent, "generator_technology_type")
    if typed:
        return str(typed)
    tech_id = _rel(ent, "hasTechnology")
    if tech_id:
        target = (model.entities.get("GeneratorType") or {}).get(tech_id)
        if target is not None:
            long_name = _av(target, "long_name") or _av(target, "name")
            if long_name and str(long_name) != tech_id:
                return str(long_name)
        return _pretty_tech_id(tech_id)
    return asset_cls or asset_id


def capacity_by_country_and_technology(
    model: CesdmModel,
    a2n: Dict[str, str],
    n2c: Dict[str, str],
) -> Dict[str, Dict[str, float]]:
    result: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for asset_cls, gen_id, ent in iter_entities_by_classes(model, GENERATION_ASSET_CLASSES):
        cap = _af(ent, "nominal_power_capacity") or _af(ent, "maximum_generation")
        if cap is None:
            continue
        node = a2n.get(gen_id)
        country = n2c.get(node, "??") if node else "??"
        result[country][technology_label(model, ent, asset_cls, gen_id)] += cap
    return {country: dict(techs) for country, techs in result.items()}


def demand_by_country_and_type(
    model: CesdmModel,
    a2n: Dict[str, str],
    n2c: Dict[str, str],
) -> Dict[str, Dict[str, float]]:
    """Annual demand [MWh/year] by country and ``demand_type``."""
    dem_dv = build_dispatch_index(model, "DemandUnit")
    result: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for dem_id in (model.entities.get("DemandUnit") or {}):
        dv = dem_dv.get(dem_id)
        demand = _af(dv, "annual_energy_demand") if dv else None
        if demand is None:
            continue
        dtype = str(_av(dv, "demand_type") or "electricity")
        node = a2n.get(dem_id)
        country = n2c.get(node, "??") if node else "??"
        result[country][dtype] += demand
    return {country: dict(types) for country, types in result.items()}


def model_title(model: CesdmModel, yaml_path: Path) -> str:
    for eid, ent in (model.entities.get("EnergySystemModel") or {}).items():
        name = _av(ent, "name") or _av(ent, "model_name") or _av(ent, "title")
        if name:
            return str(name)
        return str(eid)
    return yaml_path.stem


def collect_payload(model: CesdmModel, yaml_path: Path) -> Dict[str, Any]:
    a2n = build_asset_to_node(model)
    n2c = build_node_to_country(model)
    capacity = capacity_by_country_and_technology(model, a2n, n2c)
    demand = demand_by_country(model, a2n, n2c)
    demand_types = demand_by_country_and_type(model, a2n, n2c)
    storage = storage_capacity_by_country(model, a2n, n2c)
    inflow = annual_renewable_energy_by_country(model, a2n, n2c)
    totals = summarize_totals_by_country(model, a2n, n2c)
    ico_rows = interconnector_flows(model, n2c)
    ntc = cross_border_capacity_summary(ico_rows)
    lines = transmission_lines_summary(model)
    transformers = transformer_summary(model)
    counts = model_entity_counts(model)

    storage_energy: Dict[str, Dict[str, float]] = {}
    storage_power: Dict[str, Dict[str, float]] = {}
    for country, techs in storage.items():
        energy = {tech: vals.get("energy_mwh", 0.0) for tech, vals in techs.items()}
        power = {tech: vals.get("power_mw", 0.0) for tech, vals in techs.items()}
        if any(energy.values()):
            storage_energy[_country_label(country)] = _round_map(energy)
        if any(power.values()):
            storage_power[_country_label(country)] = _round_map(power)

    hydro: Dict[str, Dict[str, float]] = {}
    reservoir: Dict[str, Dict[str, float]] = {}
    for country, rec in totals.items():
        label = _country_label(country)
        hydro_row = {
            "turbine_mw": rec.get("hydro_turbine_discharge_capacity_mw") or 0.0,
            "phs_discharge_mw": rec.get("hydro_reversible_discharge_capacity_mw") or 0.0,
            "phs_charge_mw": rec.get("hydro_reversible_charge_capacity_mw") or 0.0,
        }
        if any(hydro_row.values()):
            hydro[label] = {key: _round(val) or 0.0 for key, val in hydro_row.items()}
        res_row = {
            "capacity_mwh": rec.get("reservoir_capacity_mwh") or 0.0,
            "inflow_mwh": rec.get("reservoir_inflow_mwh") or 0.0,
        }
        if any(res_row.values()):
            reservoir[label] = {key: _round(val) or 0.0 for key, val in res_row.items()}

    ntc_rows: List[Dict[str, Any]] = []
    for (left, right), limits in sorted(ntc.items()):
        ntc_rows.append(
            {
                "a": _country_label(left),
                "b": _country_label(right),
                "fwd_mw": _round(limits.get("fwd_mw")) or 0.0,
                "bwd_mw": _round(limits.get("bwd_mw")) or 0.0,
            }
        )

    countries = sorted(
        {
            _country_label(code)
            for mapping in (capacity, demand, demand_types, storage_energy, inflow, hydro)
            for code in mapping
        }
        | {row["a"] for row in ntc_rows}
        | {row["b"] for row in ntc_rows}
    )

    n_entities = sum(counts.values())
    return {
        "meta": {
            "title": model_title(model, yaml_path),
            "yaml": str(yaml_path),
            "yaml_name": yaml_path.name,
            "n_entities": n_entities,
            "n_classes": len(counts),
            "n_countries": len(countries),
        },
        "countries": countries,
        "counts": counts,
        "capacity": {
            _country_label(country): _round_map(techs) for country, techs in capacity.items()
        },
        "demand": {
            _country_label(country): _round(val) or 0.0 for country, val in demand.items()
        },
        "demand_types": {
            _country_label(country): _round_map(types)
            for country, types in demand_types.items()
        },
        "storage_energy": storage_energy,
        "storage_power": storage_power,
        "inflow": {
            _country_label(country): _round_map(cats) for country, cats in inflow.items()
        },
        "hydro": hydro,
        "reservoir": reservoir,
        "ntc": ntc_rows,
        "network": {
            "lines": lines.get("count", 0),
            "line_km": _round(lines.get("total_km")) or 0.0,
            "line_mva": _round(lines.get("total_mva")) or 0.0,
            "transformers": transformers.get("count", 0),
            "transformer_mva": _round(transformers.get("total_mva")) or 0.0,
            "interconnectors": len(ico_rows),
        },
    }


def empty_payload() -> Dict[str, Any]:
    return {
        "meta": {
            "title": "CESDM Scenario Assumptions",
            "yaml": "",
            "yaml_name": "",
            "n_entities": 0,
            "n_classes": 0,
            "n_countries": 0,
        },
        "countries": [],
        "counts": {},
        "capacity": {},
        "demand": {},
        "demand_types": {},
        "storage_energy": {},
        "storage_power": {},
        "inflow": {},
        "hydro": {},
        "reservoir": {},
        "ntc": [],
        "network": {
            "lines": 0,
            "line_km": 0.0,
            "line_mva": 0.0,
            "transformers": 0,
            "transformer_mva": 0.0,
            "interconnectors": 0,
        },
    }


def payload_from_yaml(yaml_path: Path, schemas_dir: Path) -> Dict[str, Any]:
    print(f"Loading schemas from  {schemas_dir}")
    print(f"Loading model from    {yaml_path}")
    model = build_model_from_yaml(str(schemas_dir))
    model.import_yaml_hierarchical(str(yaml_path))
    payload = collect_payload(model, yaml_path)
    meta = payload["meta"]
    print(
        f"Loaded: {meta['n_entities']:,} entities, "
        f"{meta['n_classes']} classes, {meta['n_countries']} countries"
    )
    return payload


def render_html(payload: Dict[str, Any], serve: bool = False) -> str:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Dashboard template not found: {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    if "__CESDM_DATA__" not in template or "__CESDM_SERVE__" not in template:
        raise SystemExit("Dashboard template is missing a required placeholder.")
    return template.replace("__CESDM_DATA__", blob, 1).replace(
        "__CESDM_SERVE__", "true" if serve else "false", 1
    )


def _read_uploaded_yaml(handler: BaseHTTPRequestHandler) -> tuple[str, bytes]:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        raise ValueError("Empty upload.")
    if length > 200 * 1024 * 1024:
        raise ValueError("YAML is larger than 200 MB.")
    body = handler.rfile.read(length)
    content_type = handler.headers.get("Content-Type") or ""
    if "multipart/form-data" not in content_type:
        return "model.yaml", body
    message = message_from_bytes(
        f"Content-Type: {content_type}\nMIME-Version: 1.0\n\n".encode("ascii", "replace") + body,
        policy=email_policy,
    )
    for part in message.iter_parts():
        filename = part.get_filename() or ""
        payload = part.get_payload(decode=True) or b""
        if payload and (filename.lower().endswith((".yaml", ".yml")) or part.get_param("name") == "yaml"):
            return filename or "model.yaml", payload
    raise ValueError("No YAML file in the upload.")


def serve_dashboard(payload: Dict[str, Any], schemas_dir: Path, port: int, open_browser: bool) -> None:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"dashboard: {fmt % args}")

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                html = render_html(self.server.payload, serve=True)  # type: ignore[attr-defined]
                self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                return
            self._send(404, b"Not found", "text/plain; charset=utf-8")

        def do_POST(self) -> None:
            if self.path != "/api/load":
                self._send(404, b'{"error":"Not found"}', "application/json")
                return
            try:
                filename, raw = _read_uploaded_yaml(self)
                suffix = ".yml" if filename.lower().endswith(".yml") else ".yaml"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                    handle.write(raw)
                    tmp_path = Path(handle.name)
                try:
                    loaded = payload_from_yaml(tmp_path, self.server.schemas_dir)  # type: ignore[attr-defined]
                finally:
                    tmp_path.unlink(missing_ok=True)
                loaded.setdefault("meta", {})["yaml_name"] = filename
                loaded["meta"]["yaml"] = filename
                self.server.payload = loaded  # type: ignore[attr-defined]
                blob = json.dumps(loaded, ensure_ascii=False).encode("utf-8")
                self._send(200, blob, "application/json; charset=utf-8")
            except Exception as exc:
                blob = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
                self._send(400, blob, "application/json; charset=utf-8")

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.payload = payload
    server.schemas_dir = schemas_dir
    url = f"http://127.0.0.1:{port}/"
    print(f"Dashboard at {url}")
    print("Use Load YAML in the page to open another CESDM hierarchical YAML.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped dashboard server.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a Scenario Assumptions dashboard from a CESDM YAML.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--yaml", help="CESDM hierarchical YAML.")
    parser.add_argument(
        "--schemas",
        default=str(_DEFAULT_SCHEMAS),
        help="CESDM schemas directory.",
    )
    parser.add_argument(
        "--out",
        help="Output HTML path (default: <yaml>_assumptions.html next to the YAML).",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Open a local page with a Load YAML button.",
    )
    parser.add_argument("--port", type=int, default=8765, help="Port for --serve.")
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated HTML, or the --serve URL, in the browser.",
    )
    args = parser.parse_args()

    schemas_dir = Path(args.schemas).expanduser().resolve()
    if not schemas_dir.exists():
        raise SystemExit(f"Schemas directory not found: {schemas_dir}")
    if not args.serve and not args.yaml:
        raise SystemExit("Provide --yaml, or use --serve and load a YAML from the page.")

    if args.yaml:
        yaml_path = Path(args.yaml).expanduser().resolve()
        if not yaml_path.exists():
            raise SystemExit(f"YAML file not found: {yaml_path}")
        payload = payload_from_yaml(yaml_path, schemas_dir)
    else:
        payload = empty_payload()

    if args.serve:
        serve_dashboard(payload, schemas_dir, args.port, open_browser=True)
        return

    out_path = (
        Path(args.out).expanduser().resolve()
        if args.out
        else Path(args.yaml).expanduser().resolve().with_name(
            f"{Path(args.yaml).stem}_assumptions.html"
        )
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(payload, serve=False), encoding="utf-8")
    print(f"Wrote dashboard       {out_path}")
    if args.open:
        webbrowser.open(out_path.as_uri())


if __name__ == "__main__":
    main()
