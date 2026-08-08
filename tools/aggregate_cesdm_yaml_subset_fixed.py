#!/usr/bin/env python3
"""
CESDM nodal-model aggregation — nuts3 / nuts2 / nuts1 / country levels.

Reads a CESDM hierarchical YAML produced by the PyPSA→CESDM importer and
aggregates nodes (ElectricalBus) and their attached assets spatially by
NUTS region code.  Profile arrays are aggregated from a companion HDF5 file
and written to a new HDF5 using the CESDM Profile / TimestampSeries structure.

CESDM schema version: v4 (dot-separated view names, NetworkNode hierarchy)
────────────────────────────────────────────────────────────────────────────
Entity / class mapping from old schema to new
────────────────────────────────────────────────────────────────────────────
Old                             New
────────────────────────────────────────────────────────────────────────────
ElectricityNode                 ElectricalBus          (NetworkNode subclass)
EnergyDomain                    CarrierDomain
EnergyConversionTechnology1x1   GenerationUnit  +  Generation.DispatchView
EnergyDemand                    DemandUnit      +  Demand.DispatchView
EnergyStorageTechnology         StorageUnit     +  Storage.DispatchView
TransmissionLine                TransmissionLine  +  TransmissionLine.PowerFlowView
DCLink / TwoWindingPowerTransformer  Interconnector / Transformer
                                        +  Interconnector.PowerFlowView
                                           Transformer.PowerFlowView
────────────────────────────────────────────────────────────────────────────
Relation mapping (old → new)
────────────────────────────────────────────────────────────────────────────
isInGeographicalRegion          locatedIn
isInEnergyDomain                belongsToCarrierDomain
isConnectedToNode               representsAsset → SinglePort.TopologyView.atNode
isOutputNodeOf                  representsAsset → SinglePort.TopologyView.atNode
isFromNodeOf                    representsAsset → TwoPort.TopologyView.fromNode
isToNodeOf                      representsAsset → TwoPort.TopologyView.toNode
────────────────────────────────────────────────────────────────────────────
Attribute mapping (old → new)
────────────────────────────────────────────────────────────────────────────
demand_profile_reference        Profile entity id via hasDemandProfile relation
resource_potential_profile_ref  Profile entity id via hasAvailabilityProfile relation
natural_inflow_profile_ref      Profile entity id via hasNaturalInflowProfile relation
rated_apparent_power            thermal_capacity_rating
────────────────────────────────────────────────────────────────────────────
Profile / time-series structure
────────────────────────────────────────────────────────────────────────────
Old: flat HDF5  /values[:,i]  /series_names[i]
New: CESDM entities —  TimestampSeries  +  Profile
     Profile has relation hasTimestampSeries → TimestampSeries
     and attribute data_reference = "profiles.h5:/profiles/<profile_id>/values"
     HDF5 layout: /profiles/<profile_id>/values  (float32 array, shape (T,))
                  /timestamps/<ts_id>/  (attrs: start_datetime, resolution, …)
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


sys.path.insert(0, str(_repo_root()))
sys.path.insert(0, str(_repo_root() / "tools"))


import h5py

from cesdm_toolbox import build_model_from_yaml, CesdmModel
import numpy as np
import yaml


# ── Default values (overridden by CLI arguments) ──────────────────────────────

_DEFAULT_YAML  = "pypsa_cesdm.yaml"
_DEFAULT_H5    = "pypsa_cesdm_profiles.h5"
_DEFAULT_OUTDIR = "aggregated_output"

# HDF5 dtype for read and write
H5_READ_DTYPE  = np.float32
H5_WRITE_DTYPE = np.float32

# Shared electricity carrier / domain ids (CESDM canonical)
CARRIER_ELECTRICITY_ID = "carrier.electricity"
DOMAIN_ELECTRICITY_ID  = "domain.electricity"

# TimestampSeries entity id written into the output YAML
TIMESTAMP_SERIES_ID = "ts.hourly"


# ── CESDM section keys (new schema) ──────────────────────────────────────────

GENERATION_DISPATCH_VIEW_SECTIONS = [
    "Generation.DispatchView",
    "HydroGenerationUnit.DispatchView",
]

GENERATION_VIEW_TO_ASSET_CLASS = {
    "Generation.DispatchView": "GenerationUnit",
    "HydroGenerationUnit.DispatchView": "HydroGenerationUnit",
}

STORAGE_DISPATCH_VIEW_SECTIONS = [
    "Storage.DispatchView",
    "ReservoirStorageUnit.DispatchView",
]

STORAGE_VIEW_TO_ASSET_CLASS = {
    "Storage.DispatchView": "StorageUnit",
    "ReservoirStorageUnit.DispatchView": "ReservoirStorageUnit",
}

SECTIONS = {
    "Carrier", "NaturalResource",
    "CarrierDomain",
    "GeographicalRegion",
    "ElectricalBus",
    "GenerationUnit", "HydroGenerationUnit", "GenerationUnit", *GENERATION_DISPATCH_VIEW_SECTIONS,
    "SinglePort.TopologyView",
    "TwoPort.TopologyView",
    "DemandUnit",
    "Demand.DispatchView",
    "StorageUnit", "ReservoirStorageUnit",
    *STORAGE_DISPATCH_VIEW_SECTIONS,
    "TransmissionLine",
    "TransmissionLine.PowerFlowView",
    "Interconnector",
    "Interconnector.PowerFlowView",
    "HVDCLink",
    "HVDCLink.DispatchView",
    "HVDCLink.PowerFlowView",
    "Transformer",
    "Transformer.PowerFlowView",
    "Profile",
    "TimestampSeries",
}


# ── Path helpers ──────────────────────────────────────────────────────────────


# ── NUTS code helpers ─────────────────────────────────────────────────────────

def normalize_code(code: str) -> str:
    code = code.strip().lower()
    if "." in code:
        code = code.split(".", 1)[1]
    return code


def nuts3_to_level(code: str, level: str) -> str:
    code = code.lower()
    if level in ("disaggregated", "nuts3"):
        return code
    if level == "nuts2":
        return code[:-1] if len(code) >= 3 else code
    if level == "nuts1":
        return code[:-2] if len(code) >= 4 else code[:2]
    if level == "country":
        return code[:2]
    raise ValueError(level)


def country_of_nuts3(code: str) -> str:
    """ISO-2 country prefix of a NUTS3 code, e.g. 'ch021' -> 'ch'."""
    return code.lower()[:2]


def parse_kv_overrides(pairs: List[str], *, value_type=str, what: str = "override") -> Dict[str, Any]:
    """Parse ``["CH=nuts3", "de=country"]`` (or ``["CH=3", "DE=2"]`` with
    ``value_type=int``) into ``{"ch": "nuts3", "de": "country"}``, keyed by
    lowercased ISO-2 country code. Used identically for both the spatial
    (``--level-by-country``) and technology (``--tech-level-by-country``)
    per-country overrides -- same syntax, same parser, different value type.
    """
    result: Dict[str, Any] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(
                f"Invalid --*-by-country {what} {pair!r}: expected COUNTRY=VALUE "
                f"(e.g. CH=nuts3 or DE=2)."
            )
        key, _, raw_value = pair.partition("=")
        key = normalize_code(key)[:2]
        try:
            result[key] = value_type(raw_value)
        except ValueError:
            raise SystemExit(
                f"Invalid value in --*-by-country {what} {pair!r}: "
                f"{raw_value!r} is not a valid {value_type.__name__}."
            )
    return result


def resolve_level_for_country(
    country: str, level_by_country: Dict[str, str], default_level: str,
) -> str:
    """The spatial aggregation level to use for a bus in this country --
    its explicit per-country override if one was given, the global
    ``--level`` default otherwise."""
    return level_by_country.get(country, default_level)


def resolve_tech_depth_for_country(
    country: str, tech_level_by_country: Dict[str, int], default_depth: Optional[int],
) -> Optional[int]:
    """The technology-aggregation depth to use for an asset in this
    country -- its explicit per-country override if one was given, the
    global ``--tech-level`` default otherwise (``None`` = no technology
    aggregation, the original, fully disaggregated-by-technology
    behaviour)."""
    return tech_level_by_country.get(country, default_depth)


def technology_tag_at_depth(tech_id: str, depth: Optional[int]) -> str:
    """Truncate a dot-separated technology id to ``depth`` segments, so
    e.g. 'Generation.Thermal.Gas.CCGT' at depth=3 becomes
    'Generation.Thermal.Gas' -- merging CCGT/OCGT/other gas subtypes
    into one aggregated technology group -- and at depth=2 becomes
    'Generation.Thermal', merging every thermal technology (gas, coal,
    oil, nuclear, ...) together. ``depth=None`` (or <= 0, or >= the
    id's own segment count) returns the id unchanged -- the default,
    fully-disaggregated-by-technology behaviour.
    """
    if not tech_id:
        return tech_id
    if depth is None or depth <= 0:
        return tech_id
    segments = tech_id.split(".")
    if depth >= len(segments):
        return tech_id
    return ".".join(segments[:depth])


def is_phs_paired_generator(data: Dict[str, Any], gen_asset_id: str) -> bool:
    """True if this HydroGenerationUnit is a reversible pump-turbine
    (PHS), false for a plain (non-reversible) hydro turbine.

    Used to keep PHS-paired and plain-hydro-paired generators in
    separate aggregation groups even at a --tech-level coarse enough
    that their own hasTechnology ids would otherwise truncate to the
    same tag -- merging them would make it impossible for downstream
    consumers (tools/import_flexeco.py's PN_StorageDam vs. PN_StoragePump*
    classification, which determines PHS-ness from the generator a
    reservoir is paired with) to recover which of the aggregated
    generator's original members were actually reversible.

    Checks the same signals import_flexeco.py itself uses for PHS
    detection, so the two stay consistent: the asset's own
    is_reversible attribute, its dispatch view's machine_role/
    maximum_pumping_power, and its paired reservoir's
    storage_technology_type / hasTechnology.
    """
    gen_ent = section_items(data, "HydroGenerationUnit").get(gen_asset_id, {})
    if bool(attr_value(gen_ent, "is_reversible")):
        return True

    for dv_ent in section_items(data, "HydroGenerationUnit.DispatchView").values():
        if first_rel(dv_ent, "representsAsset") != gen_asset_id:
            continue
        if str(attr_value(dv_ent, "machine_role") or "").lower() == "reversible":
            return True
        if attr_value(dv_ent, "maximum_pumping_power") is not None:
            return True
        break

    res_id = first_rel(gen_ent, "drawsFromReservoir")
    if res_id:
        for dv_ent in section_items(data, "ReservoirStorageUnit.DispatchView").values():
            if first_rel(dv_ent, "representsAsset") != res_id:
                continue
            tech = str(attr_value(dv_ent, "storage_technology_type") or "").lower()
            if "phs" in tech or "pumped" in tech:
                return True
            break
        res_ent = section_items(data, "ReservoirStorageUnit").get(res_id, {})
        hastech = str(first_rel(res_ent, "hasTechnology") or "").lower()
        if "phs" in hastech or "pumped" in hastech:
            return True

    return False


def geo_region_id(level: str, code: str) -> str:
    prefix = "nuts3" if level in ("disaggregated", "nuts3") else level
    return f"{prefix}.{code}"


def build_outdir_name(level: str, selectors: List[str]) -> str:
    if not selectors:
        return f"aggregated_{level}"
    tag = "_".join(normalize_code(x) for x in selectors if normalize_code(x))
    return f"aggregated_{level}_{tag}"


# ── Scalar helpers ────────────────────────────────────────────────────────────

def safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except Exception:
        return None


def wavg(
    values: List[Optional[float]], weights: List[Optional[float]]
) -> Optional[float]:
    num = den = 0.0
    for v, w in zip(values, weights):
        if v is None or w is None or w == 0:
            continue
        num += v * w
        den += w
    return None if den == 0.0 else num / den


def normalize_sum_pos1(a: np.ndarray) -> np.ndarray:
    s = float(a.sum())
    return a if s == 0.0 else a / s


def normalize_sum_neg1(a: np.ndarray) -> np.ndarray:
    s = float(a.sum())
    return a if s == 0.0 else a / abs(s)


# ── CESDM entity accessors ────────────────────────────────────────────────────
# The YAML uses the flat EAR structure:
#   { "attributes": [{"id": ..., "value": ..., "unit": ...}, ...],
#     "relations":  [{"id": ..., "target_entity_ids": [...]}, ...] }

def get_attrs(entity: Dict[str, Any]) -> Dict[str, Tuple[Any, Optional[str]]]:
    out: Dict[str, Tuple[Any, Optional[str]]] = {}
    for a in entity.get("attributes", []) or []:
        if isinstance(a, dict):
            aid = a.get("id")
            if isinstance(aid, str):
                out[aid] = (a.get("value"), a.get("unit"))
    return out


def get_rels(entity: Dict[str, Any]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for r in entity.get("relations", []) or []:
        if isinstance(r, dict):
            rid = r.get("id")
            targets = list(r.get("target_entity_ids", []) or [])
            if isinstance(rid, str):
                out[rid] = targets
    return out


def make_attr(aid: str, value: Any, unit: Optional[str] = None) -> Dict[str, Any]:
    d: Dict[str, Any] = {"id": aid, "value": value}
    if unit is not None:
        d["unit"] = unit
    return d


def make_rel(rid: str, targets: List[str]) -> Dict[str, Any]:
    return {"id": rid, "target_entity_ids": targets}


def id_tag(value: Any, fallback: str = "unknown") -> str:
    txt = str(value or fallback).strip().lower()
    txt = re.sub(r"[^a-z0-9]+", ".", txt).strip(".")
    return txt or fallback

def asset_technology_tag(data: Dict[str, Any], asset_class: str, asset_id: str, fallback: str) -> str:
    ent = section_items(data, asset_class).get(asset_id, {})
    tech = first_rel(ent, "hasTechnology") or first_rel(ent, "instanceOfType")
    return id_tag(tech or fallback)

def aggregated_storage_id_for_asset(
    data: Dict[str, Any],
    asset_id: str,
    node_to_agg: Dict[str, str],
    a2n: Dict[str, str],
    sto_d_by_section: Dict[str, Dict[str, Dict[str, Any]]],
    split_voltage: bool,
    bus_country: Optional[Dict[str, str]] = None,
    tech_level: Optional[int] = None,
    tech_level_by_country: Optional[Dict[str, int]] = None,
    reservoir_bus: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    """Return the aggregated storage/reservoir id for an original storage asset.

    This mirrors the storage aggregation naming logic (including the same
    per-country technology-depth truncation and reservoir-via-generator
    bus fallback) and is used to preserve
    HydroGenerationUnit.drawsFromReservoir links after aggregation -- it
    must produce exactly the same id the main storage-aggregation loop
    does, or those links would point at an id that was never created.
    """
    bus_country = bus_country or {}
    tech_level_by_country = tech_level_by_country or {}
    reservoir_bus = reservoir_bus or {}
    bus_id = a2n.get(asset_id) or reservoir_bus.get(asset_id)
    agg_bus = node_to_agg.get(bus_id or "")
    if not agg_bus:
        return None
    for view_section, views in sto_d_by_section.items():
        asset_class = STORAGE_VIEW_TO_ASSET_CLASS.get(view_section, "StorageUnit")
        for _dv_id, dv_ent in views.items():
            if first_rel(dv_ent, "representsAsset") != asset_id:
                continue
            tech = attr_value(dv_ent, "storage_technology_type") or asset_technology_tag(data, asset_class, asset_id, view_section)
            country = bus_country.get(bus_id or "", "")
            depth = resolve_tech_depth_for_country(country, tech_level_by_country, tech_level)
            tech = technology_tag_at_depth(tech, depth)
            parts = agg_bus.split(".")
            rc = parts[1]
            sfx = f".{parts[2]}" if split_voltage and len(parts) >= 3 else ""
            return f"storage.{id_tag(tech)}.agg.{rc}{sfx}"
    return None

def view_profile_relation_for_section(section: str) -> str:
    if section == "HydroGenerationUnit.DispatchView":
        return "hasRunOfRiverInflowProfile"
    if section == "ReservoirStorageUnit.DispatchView":
        return "hasNaturalInflowProfile"
    return "hasAvailabilityProfile"


def allowed_agg_attrs_for_generation(section: str) -> set[str]:
    base = {
        "name",
        "nominal_power_capacity",
        "minimum_generation",
        "maximum_generation",
        "variable_operating_cost",
    }
    if section == "Generation.DispatchView":
        return base | {
            "generator_technology_type",
            "energy_conversion_efficiency",
            "annual_resource_potential",
            "dispatch_type",
            "maximum_ramp_rate_up",
            "maximum_ramp_rate_down",
            "minimum_up_time",
            "minimum_down_time",
            "hot_start_cost",
            "cold_start_cost",
        }
    if section == "HydroGenerationUnit.DispatchView":
        return base | {
            "annual_resource_potential",
            "dispatch_type",
            "machine_role",
            "turbine_efficiency",
            "maximum_pumping_power",
            "pumping_efficiency",
        }
    return base


def attr_float(entity: Dict[str, Any], aid: str) -> Optional[float]:
    v = get_attrs(entity).get(aid, (None, None))[0]
    return safe_float(v)


def attr_value(entity: Dict[str, Any], aid: str) -> Any:
    return get_attrs(entity).get(aid, (None, None))[0]


def attr_unit(entity: Dict[str, Any], aid: str) -> Optional[str]:
    return get_attrs(entity).get(aid, (None, None))[1]


def first_rel(entity: Dict[str, Any], rid: str) -> Optional[str]:
    xs = get_rels(entity).get(rid, [])
    return xs[0] if xs else None


# ── Node NUTS3 resolution ─────────────────────────────────────────────────────
# In the new schema, spatial info lives on the ElectricalBus entity itself:
#   - attribute  latitude / longitude
#   - relation   locatedIn → GeographicalRegion  (id starts with "nuts3.")
# Fallback: parse the entity id (pattern: node.<nuts3>.<kv>)

def node_nuts3_code(node_id: str, node_entity: Dict[str, Any]) -> Optional[str]:
    # Primary: locatedIn relation pointing to a nuts3.* region
    for t in get_rels(node_entity).get("locatedIn", []):
        if isinstance(t, str) and t.lower().startswith("nuts3."):
            return t.split(".", 1)[1].lower()
    # Fallback: node id structure  node.<nuts3>.<kv>
    parts = node_id.split(".")
    if len(parts) >= 3 and parts[0] == "node":
        return parts[1].lower()
    return None


# ── Bus / view index helpers ──────────────────────────────────────────────────
# In the new schema the topology link from an asset to its bus is expressed via
# a SinglePort.TopologyView or TwoPort.TopologyView entity.  We build lookup
# dicts at load time to avoid repeated scans.

def build_asset_to_node(
    topo_views: Dict[str, Dict[str, Any]]
) -> Dict[str, str]:
    """Return {asset_entity_id: bus_entity_id} from SinglePort.TopologyView."""
    mapping: Dict[str, str] = {}
    for _vid, ent in topo_views.items():
        asset = first_rel(ent, "representsAsset")
        node  = first_rel(ent, "atNode")
        if asset and node:
            mapping[asset] = node
    return mapping


def build_reservoir_bus_via_generator(
    data: Dict[str, Any], a2n: Dict[str, str],
) -> Dict[str, str]:
    """Return {reservoir_entity_id: bus_entity_id}.

    A reservoir (ReservoirStorageUnit) is never itself electrically
    connected -- only its paired HydroGenerationUnit is, via
    drawsFromReservoir. Without this, the storage-aggregation loop's
    plain ``a2n.get(reservoir_id)`` always returns None for every
    reservoir (no SinglePort.TopologyView exists for it directly), and
    every reservoir/PHS storage asset is silently excluded from
    aggregation entirely -- this reconstructs the bus a reservoir
    should be grouped by, via the generator that draws from it.
    """
    mapping: Dict[str, str] = {}
    for gen_id, gen_ent in section_items(data, "HydroGenerationUnit").items():
        res_id = first_rel(gen_ent, "drawsFromReservoir")
        bus_id = a2n.get(gen_id)
        if res_id and bus_id:
            mapping[res_id] = bus_id
    return mapping


def build_branch_endpoints(
    topo_views: Dict[str, Dict[str, Any]]
) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """Return {asset_entity_id: (from_bus_id, to_bus_id)} from TwoPort.TopologyView."""
    mapping: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
    for _vid, ent in topo_views.items():
        asset = first_rel(ent, "representsAsset")
        frm   = first_rel(ent, "fromNode")
        to    = first_rel(ent, "toNode")
        if asset:
            mapping[asset] = (frm, to)
    return mapping


def build_asset_dispatch_index(
    dispatch_views: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Return {asset_entity_id: dispatch_view_entity} for fast lookup."""
    mapping: Dict[str, Dict[str, Any]] = {}
    for _vid, ent in dispatch_views.items():
        asset = first_rel(ent, "representsAsset")
        if asset:
            mapping[asset] = ent
    return mapping


# ── Profile relation helpers ──────────────────────────────────────────────────
# Relations: hasDemandProfile, hasAvailabilityProfile, hasNaturalInflowProfile → Profile id

def dispatch_profile_rel(view_entity: Dict[str, Any]) -> Optional[str]:
    """Return the Profile entity id linked from a dispatch view, if any."""
    rels = get_rels(view_entity)
    for rel_id in ("hasAvailabilityProfile", "hasDemandProfile", "hasNaturalInflowProfile", "hasRunOfRiverInflowProfile"):
        t = rels.get(rel_id, [])
        if t:
            return t[0]
    return None


def profile_data_ref(
    profile_id: str, profiles_sec: Dict[str, Dict[str, Any]]
) -> Optional[str]:
    """Return the data_reference attribute of a Profile entity."""
    ent = profiles_sec.get(profile_id)
    if ent is None:
        return None
    return attr_value(ent, "data_reference")


# ── NUTS selector helpers ─────────────────────────────────────────────────────

def selector_matches_nuts3(nuts3_code: str, selectors: List[str]) -> bool:
    if not selectors:
        return True
    c = nuts3_code.lower()
    for s in selectors:
        s = normalize_code(s)
        if not s:
            continue
        if c[:2] == s if len(s) == 2 else c.startswith(s):
            return True
    return False


def collect_all_nuts3_codes(buses: Dict[str, Dict[str, Any]]) -> List[str]:
    return sorted({
        c for nid, ent in buses.items()
        if (c := node_nuts3_code(nid, ent))
    })


def validate_selectors(
    selectors: List[str], valid_nuts3: List[str]
) -> Tuple[List[str], List[str]]:
    valid, invalid = [], []
    for s in selectors:
        ss = normalize_code(s)
        found = any(
            (code[:2] == ss if len(ss) == 2 else code.startswith(ss))
            for code in valid_nuts3
        )
        (valid if found else invalid).append(ss)
    return valid, invalid


def summarize_kept_by_country(
    node_ids: List[str], buses: Dict[str, Dict[str, Any]]
) -> Counter:
    c: Counter = Counter()
    for nid in node_ids:
        n3 = node_nuts3_code(nid, buses.get(nid, {}))
        if n3:
            c[n3[:2].upper()] += 1
    return c


# ── YAML load ────────────────────────────────────────────────────────────────

def load_cesdm_model(schemas_dir: Path, yaml_path: Path) -> "CesdmModel":
    """Load schema and import model YAML via the CESDM toolbox."""
    model = build_model_from_yaml(str(schemas_dir))
    model.import_yaml_hierarchical(str(yaml_path))
    return model


def model_to_data(model: "CesdmModel") -> Dict[str, Any]:
    """
    Convert a CesdmModel into the flat EAR dict structure used internally
    by the aggregation logic:
        { class_name: { entity_id: {"attributes": [...], "relations": [...]} } }

    Relations are stored in entity.data as plain scalars (single target) or
    lists (multiple targets) keyed by relation name — not as dicts.
    We distinguish them from attributes by consulting the class schema.
    """
    data: Dict[str, Any] = {}
    for cls_name, entities in model.entities.items():
        # Build the set of relation names for this class (including inherited)
        cdef = model.classes.get(cls_name)
        _, rel_defs = model._collect_inherited_fields(cdef) if cdef else ({}, {})
        rel_names = set(rel_defs.keys())

        sec: Dict[str, Dict[str, Any]] = {}
        for eid, ent in entities.items():
            raw = getattr(ent, "data", {}) or {}
            attrs = []
            rels = []
            for key, val in raw.items():
                if key in rel_names:
                    # Relations: stored as a string or list of strings
                    if isinstance(val, list):
                        targets = [str(t) for t in val if t is not None]
                    elif val is not None:
                        targets = [str(val)]
                    else:
                        targets = []
                    if targets:
                        rels.append({"id": key, "target_entity_ids": targets})
                elif isinstance(val, dict) and "value" in val:
                    a = {"id": key, "value": val["value"]}
                    if "unit" in val:
                        a["unit"] = val["unit"]
                    attrs.append(a)
                elif val is not None:
                    attrs.append({"id": key, "value": val})
            sec[eid] = {"attributes": attrs, "relations": rels}
        data[cls_name] = sec
    for sec_name in SECTIONS:
        data.setdefault(sec_name, {})
    synthesize_flat_view_sections(data, model)
    return data


def section_items(data: Dict[str, Any], sec: str) -> Dict[str, Dict[str, Any]]:
    x = data.get(sec, {})
    return x if isinstance(x, dict) else {}


_CANONICAL_SECTION_NAMES = {
    ("HydroGenerationUnit", "dispatch"): "HydroGenerationUnit.DispatchView",
    ("GenerationUnit", "dispatch"): "Generation.DispatchView",
    ("ReservoirStorageUnit", "dispatch"): "ReservoirStorageUnit.DispatchView",
    ("StorageUnit", "dispatch"): "Storage.DispatchView",
    ("DemandUnit", "dispatch"): "Demand.DispatchView",
    ("ExternalSupply", "dispatch"): "ExternalSupply.DispatchView",
    ("HVDCLink", "dispatch"): "HVDCLink.DispatchView",
    ("GenerationUnit", "power_flow"): "Generator.PowerFlowView",
    ("DemandUnit", "power_flow"): "Demand.PowerFlowView",
    ("ElectricalBus", "power_flow"): "ElectricalBus.PowerFlowView",
    ("TransmissionLine", "power_flow"): "TransmissionLine.PowerFlowView",
    ("HVDCLink", "power_flow"): "HVDCLink.PowerFlowView",
    ("Interconnector", "power_flow"): "Interconnector.PowerFlowView",
    ("Transformer", "power_flow"): "Transformer.PowerFlowView",
    ("ShuntUnit", "power_flow"): "Shunt.PowerFlowView",
    ("TransmissionElement", "topology"): "TwoPort.TopologyView",
    ("TransmissionLine", "topology"): "TwoPort.TopologyView",
    ("HVDCLink", "topology"): "TwoPort.TopologyView",
    ("Interconnector", "topology"): "TwoPort.TopologyView",
    ("Transformer", "topology"): "TwoPort.TopologyView",
}
_DEFAULT_TOPOLOGY_SECTION = "SinglePort.TopologyView"


def _find_view_class_for_group(model: "CesdmModel", asset_cls_name: str, group_name: str) -> Optional[str]:
    """Return the canonical synthesized-section name for a given
    (asset class, belongsToGroup) pair -- a hardcoded, local mapping
    rather than a schema lookup, since the old representation-view
    schema classes this used to introspect (checking each candidate's
    view_family and representsAsset target) no longer exist at all
    (see CHANGELOG.md: this toolbox's "initial version without views").
    Only the exact names this tool's own downstream per-class
    processing has always expected matter here; walks the asset's
    ancestor chain (most specific first) for anything not listed
    directly, falling back to SinglePort.TopologyView for the
    "topology" group (the default for every single-port asset that
    isn't a TransmissionElement subclass).
    """
    ancestors = [asset_cls_name] + sorted(
        model._all_parents_of(asset_cls_name),
        key=lambda c: c not in _CANONICAL_SECTION_NAMES.values(),
    )
    for cname in ancestors:
        name = _CANONICAL_SECTION_NAMES.get((cname, group_name))
        if name:
            return name
    if group_name == "topology":
        return _DEFAULT_TOPOLOGY_SECTION
    return None


def synthesize_flat_view_sections(data: Dict[str, Any], model: "CesdmModel") -> None:
    """Mutate ``data`` in place: for every asset whose class has
    belongsToGroup-tagged attributes/relations populated directly on it
    (the flattened representation-view pattern -- see CHANGELOG.md),
    synthesize a virtual separate-view-entity section entry for it, so
    every other function in this tool (which still expects e.g. a
    "Generation.DispatchView" section with representsAsset-linked
    entries, unchanged) keeps working exactly as before regardless of
    whether the source model used the old split-view pattern, the new
    flattened one, or a mix of both on different assets.

    Skipped for an asset that already has a genuine, separate view
    entity of the matching class (the old pattern already covers it;
    synthesizing a second, competing one would be wrong).
    """
    for asset_cls_name, entities in list(data.items()):
        cdef = model.classes.get(asset_cls_name)
        if cdef is None or getattr(cdef, "abstract", False) or not entities:
            continue
        attr_defs = getattr(cdef, "attributes", {}) or {}
        rel_defs = getattr(cdef, "relations", {}) or {}
        groups: Dict[str, Tuple[set, set]] = {}
        for name, d in attr_defs.items():
            for g in (getattr(d, "belongsToGroup", None) or []):
                groups.setdefault(g, (set(), set()))[0].add(name)
        for name, d in rel_defs.items():
            for g in (getattr(d, "belongsToGroup", None) or []):
                groups.setdefault(g, (set(), set()))[1].add(name)
        if not groups:
            continue

        for group_name, (attr_names, rel_names) in groups.items():
            view_cls = _find_view_class_for_group(model, asset_cls_name, group_name)
            if view_cls is None:
                continue
            existing_section = data.setdefault(view_cls, {})
            already_represented = set()
            for v in existing_section.values():
                for r in v.get("relations", []):
                    if r["id"] == "representsAsset":
                        already_represented.update(r["target_entity_ids"])

            for asset_id, ent in entities.items():
                if asset_id in already_represented:
                    continue
                flat_attrs = [a for a in ent.get("attributes", []) if a["id"] in attr_names]
                flat_rels = [r for r in ent.get("relations", []) if r["id"] in rel_names]
                if not flat_attrs and not flat_rels:
                    continue
                synth_id = f"{group_name}.{asset_id}"
                synth_rels = list(flat_rels) + [
                    {"id": "representsAsset", "target_entity_ids": [asset_id]}
                ]
                existing_section[synth_id] = {"attributes": flat_attrs, "relations": synth_rels}


def build_bus_location_index(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return {bus_id: BusLocationView_entity} by inverting representsAsset."""
    idx: Dict[str, Dict[str, Any]] = {}
    for view_id, view_ent in section_items(data, "BusLocationView").items():
        raw = first_rel(view_ent, "representsAsset")
        if raw:
            idx[raw] = view_ent
    return idx


def data_to_model(schemas_dir: Path, data: Dict[str, Any]) -> "CesdmModel":
    """
    Populate a fresh CesdmModel from the flat EAR aggregated-output dict,
    using only add_entity / add_attribute / add_relation (the three primitives).
    """
    model = build_model_from_yaml(str(schemas_dir))

    # This tool's internal output-construction still organizes dispatch/
    # topology/power-flow data into separate per-view sections (e.g.
    # "ReservoirStorageUnit.DispatchView"), a legacy of the pre-flattening
    # architecture -- those class names no longer exist in the schema at
    # all (see CHANGELOG.md: this toolbox's "initial version without
    # views"). Rather than rewriting every place in this 2000+-line file
    # that still builds output this way, flatten it here, at the single
    # point where the model actually gets built: for any section whose
    # name isn't a real class in the current schema, merge each of its
    # entities' attributes/relations directly onto the asset its
    # representsAsset relation points at, instead of trying (and
    # silently failing) to create a separate entity for it.
    flattened: Dict[str, Any] = {}
    for cls_name, entities in data.items():
        if not isinstance(entities, dict) or cls_name in model.classes:
            continue
        for eid, ent in entities.items():
            if not isinstance(ent, dict):
                continue
            asset_id = None
            remaining_rels = []
            for r in ent.get("relations", []) or []:
                if r.get("id") == "representsAsset":
                    targets = r.get("target_entity_ids") or []
                    asset_id = targets[0] if targets else None
                else:
                    remaining_rels.append(r)
            if not asset_id:
                continue
            bucket = flattened.setdefault(asset_id, {"attributes": [], "relations": []})
            bucket["attributes"].extend(ent.get("attributes", []) or [])
            bucket["relations"].extend(remaining_rels)

    for cls_name, entities in data.items():
        if not isinstance(entities, dict):
            continue
        for eid, ent in entities.items():
            if not isinstance(ent, dict):
                continue
            try:
                model.add_entity(entity_class=cls_name, entity_id=eid)
            except Exception:
                continue  # unknown class in this schema version — skip
            for a in ent.get("attributes", []) or []:
                if not isinstance(a, dict):
                    continue
                aid = a.get("id")
                val = a.get("value")
                unit = a.get("unit")
                if aid is None or val is None:
                    continue
                try:
                    model.add_attribute(eid, aid, val, unit=unit)
                except Exception:
                    pass  # unknown attribute — skip silently
            for r in ent.get("relations", []) or []:
                if not isinstance(r, dict):
                    continue
                rid = r.get("id")
                targets = r.get("target_entity_ids", []) or []
                if not rid or not targets:
                    continue
                try:
                    # add_relation() validates the relation/target and sets
                    # the first one exactly as before.
                    model.add_relation(eid, rid, targets[0])
                except Exception:
                    continue  # unknown relation or target — skip silently
                if len(targets) > 1:
                    # add_relation() has no append semantics -- calling it
                    # again per additional target would silently overwrite
                    # (it always *sets*, and even stringifies a list rather
                    # than storing it), which is why a single aggregated
                    # generator drawing from more than one aggregated
                    # reservoir (after merging different reservoir-side
                    # technology groups together on the generator side --
                    # see CHANGELOG) used to lose every target but the
                    # last. Build the real list directly on the entity's
                    # own data instead, once the relation/first target is
                    # already known-valid from the call above.
                    entity_obj = model.entities.get(cls_name, {}).get(eid)
                    if entity_obj is not None and hasattr(entity_obj, "data"):
                        entity_obj.data[rid] = list(targets)

    # Apply the flattened-legacy-section data collected above, now that
    # every real asset entity exists.
    for asset_id, bucket in flattened.items():
        for a in bucket["attributes"]:
            aid, val, unit = a.get("id"), a.get("value"), a.get("unit")
            if aid is None or val is None:
                continue
            try:
                model.add_attribute(asset_id, aid, val, unit=unit)
            except Exception:
                pass
        for r in bucket["relations"]:
            rid = r.get("id")
            targets = r.get("target_entity_ids", []) or []
            if not rid or not targets:
                continue
            try:
                model.add_relation(asset_id, rid, targets[0])
            except Exception:
                continue
            if len(targets) > 1:
                cls = model.entity_class(asset_id)
                entity_obj = model.entities.get(cls, {}).get(asset_id) if cls else None
                if entity_obj is not None and hasattr(entity_obj, "data"):
                    entity_obj.data[rid] = list(targets)

    return model


# ── HDF5 profile I/O ─────────────────────────────────────────────────────────
# Old format: /values (T×N matrix), /series_names (N strings)
# New format: /profiles/<profile_id>/values  (T-length float32)
#             /timestamps/<ts_id>/  (group attrs)

class ProfileMatrix:
    """
    Reads profile stores from HDF5 (legacy flat or CESDM) or Parquet (CESDM wide).

    Formats detected automatically:

    HDF5 — legacy flat (old PyPSA→CESDM exporter):
        /values          float matrix (T × N)
        /series_names    N byte-strings

    HDF5 — CESDM format (write_profiles_h5_cesdm / CesdmModel.export_hdf5):
        /profiles/<profile_id>/values    float array (T,)
        /timestamps/<ts_id>/             group

    Parquet — CESDM wide format (CesdmModel.export_parquet(wide=True)):
        <stem>_profiles.parquet          columns: timestamp_index, <profile_id>…
    """

    def __init__(self, path: Path):
        path = Path(path)
        if path.suffix.lower() == ".parquet" or "_profiles" in path.stem:
            self._fmt = "parquet"
            self._init_parquet(path)
        else:
            self.f = h5py.File(path, "r")
            self._fmt = self._detect_format()
            if self._fmt == "flat":
                self._init_flat()
            else:
                self._init_cesdm()

    def _init_parquet(self, path: Path) -> None:
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "pyarrow is required to read Parquet profiles. "
                "Install with: pip install pyarrow"
            )
        # Accept both <stem>_profiles.parquet and bare <stem>.parquet
        if not path.exists():
            # try _profiles suffix
            alt = path.parent / (path.stem + "_profiles.parquet")
            if alt.exists():
                path = alt
        tbl = pq.read_table(str(path)).to_pydict()
        self._parquet_data: Dict[str, "np.ndarray"] = {}
        T = 0
        for col, arr in tbl.items():
            if col == "timestamp_index":
                T = len(arr)
                continue
            self._parquet_data[col] = np.asarray(arr, dtype=H5_READ_DTYPE)
            T = len(arr)
        self.T = T
        self.name_to_idx = {k: k for k in self._parquet_data}
        self.values = None

    def _detect_format(self) -> str:
        if "/values" in self.f and "/series_names" in self.f:
            return "flat"
        if "/profiles" in self.f:
            return "cesdm"
        raise ValueError(
            f"Unrecognised HDF5 layout — expected either "
            f"'/values' + '/series_names' (flat) or '/profiles/*' (CESDM). "
            f"Top-level keys: {list(self.f.keys())}"
        )

    def _init_flat(self) -> None:
        self.values = self.f["/values"]
        raw = self.f["/series_names"][:]
        names = [
            x.decode("utf-8", errors="replace") if isinstance(x, (bytes, bytearray))
            else str(x)
            for x in raw
        ]
        self.name_to_idx = {n: i for i, n in enumerate(names)}
        self.T = int(self.values.shape[0])

    def _init_cesdm(self) -> None:
        self.values = None  # not used in CESDM mode
        profiles_grp = self.f["/profiles"]
        # Determine T from the first available dataset
        T = 0
        for pid in profiles_grp:
            ds = profiles_grp[pid].get("values")
            if ds is not None:
                T = int(ds.shape[0])
                break
        self.T = T
        self.name_to_idx = {pid: pid for pid in profiles_grp}

    def col(self, name: str) -> Optional[np.ndarray]:
        if self._fmt == "parquet":
            return self._parquet_data.get(name)
        if self._fmt == "flat":
            idx = self.name_to_idx.get(name)
            if idx is None:
                return None
            return np.array(self.f["/values"][:, idx], dtype=H5_READ_DTYPE)
        # cesdm hdf5
        grp = self.f["/profiles"].get(name)
        if grp is None:
            return None
        ds = grp.get("values")
        if ds is None:
            return None
        return np.array(ds[:], dtype=H5_READ_DTYPE)

    def close(self) -> None:
        if self._fmt != "parquet":
            self.f.close()


def write_profiles_parquet(
    out_parquet_path: Path,
    series_dict: Dict[str, np.ndarray],
    T: int,
    ts_id: str = TIMESTAMP_SERIES_ID,
) -> None:
    """
    Write aggregated profiles in the CESDM Parquet wide format:
        <stem>_profiles.parquet    columns: timestamp_index, <profile_id>…
        <stem>_metadata.parquet   one row per entity attribute (TimestampSeries only)
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError(
            "pyarrow is required to write Parquet profiles. "
            "Install with: pip install pyarrow"
        )
    out_parquet_path = Path(out_parquet_path)
    out_parquet_path.parent.mkdir(parents=True, exist_ok=True)

    stem = str(out_parquet_path.with_suffix(""))
    profiles_path = Path(stem + "_profiles.parquet")
    metadata_path = Path(stem + "_metadata.parquet")

    # Profiles wide table
    cols: Dict[str, Any] = {
        "timestamp_index": pa.array(np.arange(T, dtype=np.int64))
    }
    for pid, arr in series_dict.items():
        cols[pid] = pa.array(arr.astype(np.float64))
    pq.write_table(pa.table(cols), str(profiles_path), compression="snappy")

    # Minimal metadata table (just the TimestampSeries id)
    pq.write_table(
        pa.table({
            "entity_class": pa.array(["TimestampSeries"], pa.string()),
            "entity_id":    pa.array([ts_id],            pa.string()),
            "attribute":    pa.array(["resolution"],     pa.string()),
            "value":        pa.array(["PT1H"],           pa.string()),
        }),
        str(metadata_path),
        compression="snappy",
    )


def write_profiles_h5_cesdm(
    out_h5_path: Path,
    series_dict: Dict[str, np.ndarray],
    T: int,
    ts_id: str = TIMESTAMP_SERIES_ID,
) -> None:
    """
    Write profiles in the CESDM HDF5 layout:
      /timestamps/<ts_id>/   (empty group; metadata is in the YAML Profile entity)
      /profiles/<profile_id>/values   (float32 array, shape (T,))
    """
    out_h5_path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(out_h5_path, "w") as f:
        f.create_group(f"timestamps/{ts_id}")
        for profile_id, arr in series_dict.items():
            grp = f.require_group(f"profiles/{profile_id}")
            grp.create_dataset(
                "values",
                data=arr.astype(H5_WRITE_DTYPE),
                compression="gzip",
                compression_opts=4,
            )


# ── CESDM entity builders ─────────────────────────────────────────────────────

def make_profile_entity(
    profile_id: str,
    profile_type: str,
    profile_unit: str,
    h5_path_relative: str,
    ts_id: str = TIMESTAMP_SERIES_ID,
) -> Dict[str, Any]:
    """Build a CESDM Profile entity dict."""
    return {
        "attributes": [
            make_attr("name", profile_id),
            make_attr("profile_type", profile_type),
            make_attr("profile_unit", profile_unit),
            make_attr("data_reference", f"{h5_path_relative}:/profiles/{profile_id}/values"),
        ],
        "relations": [make_rel("hasTimestampSeries", [ts_id])],
    }


def make_electrical_bus(
    bus_id: str,
    name: str,
    lat: Optional[float],
    lon: Optional[float],
    kv: Optional[float],
    region_id: str,
    domain_id: str = DOMAIN_ELECTRICITY_ID,
) -> Dict[str, Any]:
    """Return (bus_entity, location_view_entity_or_None).

    Coordinates are stored on a BusLocationView, not on the NetworkNode entity,
    so that BusLocationView is the single spatial source of truth.
    """
    attrs = [make_attr("name", name)]
    if kv is not None:
        attrs.append(make_attr("nominal_voltage", kv, "kV"))
    bus_ent = {
        "attributes": attrs,
        "relations": [
            make_rel("locatedIn",              [region_id]),
            make_rel("belongsToCarrierDomain", [domain_id]),
        ],
    }
    loc_ent = None
    if lat is not None or lon is not None:
        loc_attrs = []
        if lat is not None:
            loc_attrs.append(make_attr("latitude",  lat, "decimal degrees"))
        if lon is not None:
            loc_attrs.append(make_attr("longitude", lon, "decimal degrees"))
        loc_ent = {
            "attributes": loc_attrs,
            "relations": [make_rel("representsAsset", [bus_id])],
        }
    return bus_ent, loc_ent


def make_single_port_topo(
    view_id: str, asset_id: str, node_id: str
) -> Dict[str, Any]:
    return {
        "attributes": [make_attr("name", view_id)],
        "relations": [
            make_rel("representsAsset", [asset_id]),
            make_rel("atNode",          [node_id]),
        ],
    }


def make_two_port_topo(
    view_id: str, asset_id: str, from_node: str, to_node: str
) -> Dict[str, Any]:
    return {
        "attributes": [make_attr("name", view_id)],
        "relations": [
            make_rel("representsAsset", [asset_id]),
            make_rel("fromNode",        [from_node]),
            make_rel("toNode",          [to_node]),
        ],
    }


# ── Disaggregated subset (no aggregation, just filtering) ────────────────────

def build_subset_disaggregated(
    data: Dict[str, Any],
    kept_buses: Dict[str, Dict[str, Any]],
    pm: Optional[ProfileMatrix],
    log,
) -> Tuple[Dict[str, Any], Dict[str, int]]:

    kept_bus_ids = set(kept_buses.keys())
    drop = Counter()

    # Build index: asset_id → bus_id  and  asset_id → dispatch_view
    spv   = section_items(data, "SinglePort.TopologyView")
    tpv   = section_items(data, "TwoPort.TopologyView")
    gen_d_by_section = {sec: section_items(data, sec) for sec in GENERATION_DISPATCH_VIEW_SECTIONS}
    dem_d = section_items(data, "Demand.DispatchView")
    sto_d_by_section = {sec: section_items(data, sec) for sec in STORAGE_DISPATCH_VIEW_SECTIONS}
    txl_d = section_items(data, "TransmissionLine.PowerFlowView")
    ico_d = section_items(data, "Interconnector.PowerFlowView")
    hvdc_pf_d = section_items(data, "HVDCLink.PowerFlowView")
    hvdc_dispatch_d = section_items(data, "HVDCLink.DispatchView")
    trf_d = section_items(data, "Transformer.PowerFlowView")

    a2n    = build_asset_to_node(spv)
    a2br   = build_branch_endpoints(tpv)

    # Filter each section
    def _keep_asset(asset_id: str) -> bool:
        n = a2n.get(asset_id)
        return n in kept_bus_ids if n else False

    def _keep_branch(asset_id: str) -> bool:
        frm, to = a2br.get(asset_id, (None, None))
        return frm in kept_bus_ids and to in kept_bus_ids

    out_gen_assets_by_class = {
        cls: {aid: e for aid, e in section_items(data, cls).items() if _keep_asset(aid)}
        for cls in {"GenerationUnit", *GENERATION_VIEW_TO_ASSET_CLASS.values()}
    }
    out_gens = out_gen_assets_by_class.get("GenerationUnit", {})
    out_dem  = {aid: e for aid, e in section_items(data, "DemandUnit").items()
                if _keep_asset(aid) or (drop.__setitem__("dem_outside", drop.get("dem_outside", 0)+1) and False)}
    out_sto_assets_by_class = {
        cls: {aid: e for aid, e in section_items(data, cls).items() if _keep_asset(aid)}
        for cls in {"StorageUnit", *STORAGE_VIEW_TO_ASSET_CLASS.values()}
    }
    out_sto = out_sto_assets_by_class.get("StorageUnit", {})
    out_txl  = {aid: e for aid, e in section_items(data, "TransmissionLine").items()
                if _keep_branch(aid) or (drop.__setitem__("line_outside", drop.get("line_outside", 0)+1) and False)}
    out_ico  = {aid: e for aid, e in section_items(data, "Interconnector").items()
                if _keep_branch(aid) or (drop.__setitem__("ico_outside", drop.get("ico_outside", 0)+1) and False)}
    out_hvdc = {aid: e for aid, e in section_items(data, "HVDCLink").items()
                if _keep_branch(aid) or (drop.__setitem__("hvdc_outside", drop.get("hvdc_outside", 0)+1) and False)}
    out_trf  = {aid: e for aid, e in section_items(data, "Transformer").items()
                if _keep_branch(aid) or (drop.__setitem__("trf_outside", drop.get("trf_outside", 0)+1) and False)}

    # Filter topology views to only those whose asset is kept
    all_kept_gen_assets = set().union(*(set(v) for v in out_gen_assets_by_class.values())) if out_gen_assets_by_class else set()
    all_kept_sto_assets = set().union(*(set(v) for v in out_sto_assets_by_class.values())) if out_sto_assets_by_class else set()
    all_kept_assets = (all_kept_gen_assets | set(out_dem) | all_kept_sto_assets |
                       set(out_txl) | set(out_ico) | set(out_hvdc) | set(out_trf))
    out_spv = {vid: e for vid, e in spv.items()
               if first_rel(e, "representsAsset") in all_kept_assets}
    out_tpv = {vid: e for vid, e in tpv.items()
               if first_rel(e, "representsAsset") in all_kept_assets}

    # Dispatch views for kept assets
    out_gen_d_by_section = {
        sec: {vid: e for vid, e in views.items() if first_rel(e, "representsAsset") in all_kept_gen_assets}
        for sec, views in gen_d_by_section.items()
    }
    out_gen_d = {vid: e for views in out_gen_d_by_section.values() for vid, e in views.items()}
    out_dem_d = {vid: e for vid, e in dem_d.items()
                 if first_rel(e, "representsAsset") in out_dem}
    out_sto_d_by_section = {
        sec: {vid: e for vid, e in views.items() if first_rel(e, "representsAsset") in all_kept_sto_assets}
        for sec, views in sto_d_by_section.items()
    }
    out_sto_d = {vid: e for views in out_sto_d_by_section.values() for vid, e in views.items()}
    out_txl_d = {vid: e for vid, e in txl_d.items()
                 if first_rel(e, "representsAsset") in out_txl}
    out_ico_d = {vid: e for vid, e in ico_d.items()
                 if first_rel(e, "representsAsset") in out_ico}
    out_hvdc_pf_d = {vid: e for vid, e in hvdc_pf_d.items()
                     if first_rel(e, "representsAsset") in out_hvdc}
    out_hvdc_dispatch_d = {vid: e for vid, e in hvdc_dispatch_d.items()
                           if first_rel(e, "representsAsset") in out_hvdc}
    out_trf_d = {vid: e for vid, e in trf_d.items()
                 if first_rel(e, "representsAsset") in out_trf}

    # Geographic regions referenced by kept buses
    geo_ids = {
        t for ent in kept_buses.values()
        for t in get_rels(ent).get("locatedIn", [])
    }
    out_geo = {}
    geo_sec = section_items(data, "GeographicalRegion")
    for gid in sorted(geo_ids):
        out_geo[gid] = geo_sec.get(gid) or {"attributes": [make_attr("name", gid)], "relations": []}

    # Copy Profile entities for kept dispatch views
    profiles_sec = section_items(data, "Profile")
    all_disp_views = {**out_gen_d, **out_dem_d, **out_sto_d}
    kept_profile_ids = {
        pid
        for dv in all_disp_views.values()
        if (pid := dispatch_profile_rel(dv))
    }
    out_profiles = {pid: profiles_sec[pid] for pid in kept_profile_ids if pid in profiles_sec}

    # Copy HDF5 profiles
    series_dict: Dict[str, np.ndarray] = {}
    if pm is not None:
        for pid, pent in out_profiles.items():
            dref = attr_value(pent, "data_reference")
            if isinstance(dref, str):
                # data_reference format: "file.h5:/profiles/<id>/values"
                # resolve the series name from the old h5 index
                col = pm.col(pid) or pm.col(dref.split(":")[-1].lstrip("/"))
                if col is not None:
                    series_dict[pid] = col.astype(H5_WRITE_DTYPE)
                else:
                    log(f"[WARN] missing profile in source h5: {pid}")

    for k, v in drop.items():
        log(f"dropped {k}={v}")

    out_obj: Dict[str, Any] = {
        "Carrier":              section_items(data, "Carrier"),
        "NaturalResource":            section_items(data, "NaturalResource"),
        "CarrierDomain":              section_items(data, "CarrierDomain"),
        "GeographicalRegion":         out_geo,
        "TimestampSeries":            section_items(data, "TimestampSeries"),
        "Profile":                    out_profiles,
        "ElectricalBus":              kept_buses,
        **out_gen_assets_by_class,
        "DemandUnit":                 out_dem,
        **out_sto_assets_by_class,
        "TransmissionLine":           out_txl,
        "Interconnector":             out_ico,
        "HVDCLink":                   out_hvdc,
        "Transformer":                out_trf,
        "SinglePort.TopologyView":    out_spv,
        "TwoPort.TopologyView":       out_tpv,
        **out_gen_d_by_section,
        "Demand.DispatchView":        out_dem_d,
        **out_sto_d_by_section,
        "TransmissionLine.PowerFlowView":  out_txl_d,
        "Interconnector.PowerFlowView":    out_ico_d,
        "HVDCLink.PowerFlowView":          out_hvdc_pf_d,
        "HVDCLink.DispatchView":           out_hvdc_dispatch_d,
        "Transformer.PowerFlowView":       out_trf_d,
    }

    stats = {
        "buses":  len(kept_buses),
        "gens":   len(out_gens),
        "loads":  len(out_dem),
        "stors":  len(out_sto),
        "lines":  len(out_txl),
        "icos":   len(out_ico),
        "trafos": len(out_trf),
    }
    return out_obj, series_dict, stats


# ── Aggregation ───────────────────────────────────────────────────────────────

def aggregate_subset(
    data: Dict[str, Any],
    kept_buses: Dict[str, Dict[str, Any]],
    level: str,
    split_voltage: bool,
    pm: Optional[ProfileMatrix],
    log,
    h5_path_relative: str = "profiles/profiles.h5",
    round_kv: int = 1,
    level_by_country: Optional[Dict[str, str]] = None,
    tech_level: Optional[int] = None,
    tech_level_by_country: Optional[Dict[str, int]] = None,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray], Dict[str, int]]:

    level_by_country = level_by_country or {}
    tech_level_by_country = tech_level_by_country or {}

    kept_bus_ids = set(kept_buses.keys())

    spv  = section_items(data, "SinglePort.TopologyView")
    tpv  = section_items(data, "TwoPort.TopologyView")
    gen_d_by_section = {sec: section_items(data, sec) for sec in GENERATION_DISPATCH_VIEW_SECTIONS}
    dem_d = section_items(data, "Demand.DispatchView")
    sto_d_by_section = {sec: section_items(data, sec) for sec in STORAGE_DISPATCH_VIEW_SECTIONS}
    txl_d = section_items(data, "TransmissionLine.PowerFlowView")
    ico_d = section_items(data, "Interconnector.PowerFlowView")
    hvdc_pf_d = section_items(data, "HVDCLink.PowerFlowView")
    hvdc_dispatch_d = section_items(data, "HVDCLink.DispatchView")
    trf_d = section_items(data, "Transformer.PowerFlowView")
    profiles_sec = section_items(data, "Profile")

    a2n  = build_asset_to_node(spv)
    reservoir_bus = build_reservoir_bus_via_generator(data, a2n)
    a2br = build_branch_endpoints(tpv)

    # ── Map each kept bus to its aggregated bus id ─────────────────────────────
    node_to_agg: Dict[str, str] = {}
    agg_members: Dict[str, List[str]] = defaultdict(list)
    agg_id_level: Dict[str, str] = {}   # agg_id -> the spatial level actually used to produce it
    region_codes: set = set()
    region_code_level: Dict[str, str] = {}   # region code -> the level that produced it
    bus_country: Dict[str, str] = {}   # original bus id -> country, for per-country tech depth below

    for bid, ent in kept_buses.items():
        n3 = node_nuts3_code(bid, ent)
        if not n3:
            continue
        country = country_of_nuts3(n3)
        bus_country[bid] = country
        effective_level = resolve_level_for_country(country, level_by_country, level)
        rc = nuts3_to_level(n3, effective_level)
        region_codes.add(rc)
        region_code_level[rc] = effective_level
        kv = attr_float(ent, "nominal_voltage")
        if split_voltage and kv is not None:
            kvn = int(round(kv, round_kv))
            agg_id = f"node.{rc}.{kvn}"
        else:
            agg_id = f"node.{rc}"
        node_to_agg[bid] = agg_id
        agg_members[agg_id].append(bid)
        agg_id_level[agg_id] = effective_level

    series_dict:      Dict[str, np.ndarray] = {}
    out_profiles:     Dict[str, Dict[str, Any]] = {}
    out_buses:        Dict[str, Dict[str, Any]] = {}
    out_bus_locs:     Dict[str, Dict[str, Any]] = {}
    out_gens:         Dict[str, Dict[str, Any]] = {}
    out_dem:          Dict[str, Dict[str, Any]] = {}
    out_sto:          Dict[str, Dict[str, Any]] = {}
    out_lines:        Dict[str, Dict[str, Any]] = {}
    out_icos:         Dict[str, Dict[str, Any]] = {}
    out_hvdcs:        Dict[str, Dict[str, Any]] = {}
    out_trafos:       Dict[str, Dict[str, Any]] = {}
    out_spv_agg:      Dict[str, Dict[str, Any]] = {}
    out_tpv_agg:      Dict[str, Dict[str, Any]] = {}
    out_gen_d_agg:    Dict[str, Dict[str, Any]] = {}
    out_dem_d_agg:    Dict[str, Dict[str, Any]] = {}
    out_sto_d_agg:    Dict[str, Dict[str, Any]] = {}
    out_txl_d_agg:    Dict[str, Dict[str, Any]] = {}
    out_ico_d_agg:    Dict[str, Dict[str, Any]] = {}
    out_hvdc_dispatch_d_agg: Dict[str, Dict[str, Any]] = {}
    out_hvdc_pf_d_agg: Dict[str, Dict[str, Any]] = {}
    out_trf_d_agg:    Dict[str, Dict[str, Any]] = {}

    # Index: bus_id → BusLocationView entity (single spatial source of truth)
    bus_loc_index = build_bus_location_index(data)

    # ── Aggregated ElectricalBus entities ─────────────────────────────────────
    for agg_id, members in agg_members.items():
        parts = agg_id.split(".")
        rc = parts[1]
        kv_out = float(parts[2]) if split_voltage and len(parts) >= 3 else None

        # Read coordinates from BusLocationView, not the bus entity directly
        lats = [attr_float(bus_loc_index[m], "latitude")  for m in members if m in bus_loc_index]
        lons = [attr_float(bus_loc_index[m], "longitude") for m in members if m in bus_loc_index]
        kvs  = [attr_float(kept_buses[m], "nominal_voltage") for m in members]

        lat_vals = [x for x in lats if x is not None]
        lon_vals = [x for x in lons if x is not None]

        bus_ent, loc_ent = make_electrical_bus(
            bus_id    = agg_id,
            name      = agg_id,
            lat       = float(sum(lat_vals) / len(lat_vals)) if lat_vals else None,
            lon       = float(sum(lon_vals) / len(lon_vals)) if lon_vals else None,
            kv        = kv_out if kv_out is not None
                        else (max(x for x in kvs if x is not None) if any(x is not None for x in kvs) else None),
            region_id = geo_region_id(agg_id_level.get(agg_id, level), rc),
        )
        out_buses[agg_id] = bus_ent
        if loc_ent is not None:
            out_bus_locs[f"location.{agg_id}"] = loc_ent

    # ── Helper: load profile array from old h5 via dispatch view ──────────────
    def load_profile(dv_ent: Dict[str, Any]) -> Optional[np.ndarray]:
        pid = dispatch_profile_rel(dv_ent)
        if pid is None or pm is None:
            return None
        col = pm.col(pid)
        return col.astype(np.float64) if col is not None else None

    # ── Aggregated DemandUnit + Demand.DispatchView ───────────────────────────
    # Group demand dispatch views by aggregated bus, identified via representsAsset → SinglePort.TopologyView
    dem_asset_to_node: Dict[str, str] = {
        first_rel(e, "representsAsset"): a2n.get(first_rel(e, "representsAsset"), "")
        for e in dem_d.values()
        if first_rel(e, "representsAsset")
    }

    load_groups: Dict[str, List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    for dv_id, dv_ent in dem_d.items():
        asset_id = first_rel(dv_ent, "representsAsset")
        if not asset_id:
            continue
        bus_id = a2n.get(asset_id)
        if bus_id in node_to_agg:
            load_groups[node_to_agg[bus_id]].append((asset_id, dv_ent))

    for agg_bus, members in load_groups.items():
        parts = agg_bus.split(".")
        rc = parts[1]
        sfx = f".{parts[2]}" if split_voltage and len(parts) >= 3 else ""
        lid = f"demand.agg.{rc}{sfx}"
        dv_id = f"dispatch.{lid}"

        ann_sum = sum((attr_float(dv, "annual_energy_demand") or 0.0) for _, dv in members)
        profs = [
            (arr, attr_float(dv, "annual_energy_demand") or 0.0)
            for _, dv in members
            if (arr := load_profile(dv)) is not None
        ]

        dem_attrs = [
            make_attr("name", lid),
            make_attr("annual_energy_demand", float(ann_sum), "MWh/year"),
        ]

        if profs:
            arrays, weights = zip(*profs)
            W = np.array(weights, dtype=np.float64)
            if W.sum() > 0:
                raw = (np.vstack(arrays).T * W).T.sum(axis=0)
                agg_arr = normalize_sum_neg1(raw).astype(H5_WRITE_DTYPE)
                new_pid = f"profile.demand.{rc}{sfx}"
                series_dict[new_pid] = agg_arr
                out_profiles[new_pid] = make_profile_entity(
                    new_pid, "as_normalized_annual_energy", "pu",
                    h5_path_relative,
                )
                dem_dv_attrs = list(dem_attrs)
                dem_dv_rel = [
                    make_rel("representsAsset", [lid]),
                    make_rel("hasDemandProfile", [new_pid]),
                ]
            else:
                dem_dv_attrs = list(dem_attrs)
                dem_dv_rel = [make_rel("representsAsset", [lid])]
        else:
            dem_dv_attrs = list(dem_attrs)
            dem_dv_rel = [make_rel("representsAsset", [lid])]

        out_dem[lid] = {"attributes": [make_attr("name", lid)], "relations": []}
        out_dem_d_agg[dv_id] = {"attributes": dem_dv_attrs, "relations": dem_dv_rel}
        out_spv_agg[f"topo.{lid}"] = make_single_port_topo(f"topo.{lid}", lid, agg_bus)

    # ── Aggregated generation assets + their original specialised DispatchViews ──
    # Keep the original view class semantics. Wind remains Generation.DispatchView,
    # Solar remains Generation.DispatchView, Hydro remains HydroGenerationUnit.DispatchView,
    # Thermal/Nuclear remain their specialised views, and only true fallback assets
    # become Generation.DispatchView.
    out_gen_assets_agg_by_class: Dict[str, Dict[str, Dict[str, Any]]] = {
        cls: {} for cls in set(GENERATION_VIEW_TO_ASSET_CLASS.values())
    }
    out_gen_d_agg_by_section: Dict[str, Dict[str, Dict[str, Any]]] = {
        sec: {} for sec in GENERATION_DISPATCH_VIEW_SECTIONS
    }

    gen_groups: Dict[Tuple[str, str, str], List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    for view_section, views in gen_d_by_section.items():
        asset_class = GENERATION_VIEW_TO_ASSET_CLASS[view_section]
        for dv_id, dv_ent in views.items():
            asset_id = first_rel(dv_ent, "representsAsset")
            if not asset_id:
                continue
            bus_id = a2n.get(asset_id)
            if bus_id in node_to_agg:
                tech = attr_value(dv_ent, "generator_technology_type") or asset_technology_tag(data, asset_class, asset_id, view_section)
                country = bus_country.get(bus_id, "")
                depth = resolve_tech_depth_for_country(country, tech_level_by_country, tech_level)
                tech = technology_tag_at_depth(tech, depth)
                tag = id_tag(tech)
                if view_section == "HydroGenerationUnit.DispatchView":
                    # PHS-paired and plain-hydro-paired generators must never
                    # merge, no matter how coarse --tech-level is: they draw
                    # from structurally different reservoirs (reversible
                    # pump-turbine vs. simple turbine), and downstream tools
                    # (tools/import_flexeco.py's PN_StorageDam/PN_StoragePump
                    # classification) determine PHS-ness from the generator
                    # a reservoir is paired with -- merge them and that
                    # distinction can no longer be recovered afterward.
                    tag = id_tag(f"{tag}.{'phs' if is_phs_paired_generator(data, asset_id) else 'nonphs'}")
                gen_groups[(view_section, node_to_agg[bus_id], tag)].append((asset_id, dv_ent))

    for (view_section, agg_bus, tech), members in gen_groups.items():
        asset_class = GENERATION_VIEW_TO_ASSET_CLASS[view_section]
        parts = agg_bus.split(".")
        rc = parts[1]
        sfx = f".{parts[2]}" if split_voltage and len(parts) >= 3 else ""
        gid = f"gen.{tech}.agg.{rc}{sfx}"
        dv_id = f"dispatch.{gid}"

        caps = [attr_float(dv, "nominal_power_capacity") for _, dv in members]
        anns = [attr_float(dv, "annual_resource_potential") for _, dv in members]
        effs = [attr_float(dv, "energy_conversion_efficiency") for _, dv in members]
        vops = [attr_float(dv, "variable_operating_cost") for _, dv in members]
        max_pump = [attr_float(dv, "maximum_pumping_power") for _, dv in members]
        pump_effs = [attr_float(dv, "pumping_efficiency") for _, dv in members]
        turb_effs = [attr_float(dv, "turbine_efficiency") for _, dv in members]

        cap_sum = sum(x or 0.0 for x in caps)
        ann_sum = sum(x or 0.0 for x in anns)
        eff_avg = wavg(effs, caps)
        vop_avg = wavg(vops, caps)
        pump_sum = sum(x or 0.0 for x in max_pump)
        pump_eff_avg = wavg(pump_effs, max_pump if any(max_pump) else caps)
        turb_eff_avg = wavg(turb_effs, caps)
        energy_shape = ann_sum > 0
        allowed = allowed_agg_attrs_for_generation(view_section)

        gen_dv_attrs = [make_attr("name", gid)]
        if "generator_technology_type" in allowed:
            gen_dv_attrs.append(make_attr("generator_technology_type", tech))
        if "nominal_power_capacity" in allowed:
            gen_dv_attrs.append(make_attr("nominal_power_capacity", float(cap_sum), "MW"))
        if eff_avg is not None and "energy_conversion_efficiency" in allowed:
            gen_dv_attrs.append(make_attr("energy_conversion_efficiency", float(eff_avg)))
        if vop_avg is not None and "variable_operating_cost" in allowed:
            gen_dv_attrs.append(make_attr("variable_operating_cost", float(vop_avg), "MU/MWh"))
        if ann_sum > 0 and "annual_resource_potential" in allowed:
            gen_dv_attrs.append(make_attr("annual_resource_potential", float(ann_sum), "MWh/year"))
        if pump_sum > 0 and "maximum_pumping_power" in allowed:
            gen_dv_attrs.append(make_attr("maximum_pumping_power", float(pump_sum), "MW"))
        if pump_eff_avg is not None and "pumping_efficiency" in allowed:
            gen_dv_attrs.append(make_attr("pumping_efficiency", float(pump_eff_avg)))
        if turb_eff_avg is not None and "turbine_efficiency" in allowed:
            gen_dv_attrs.append(make_attr("turbine_efficiency", float(turb_eff_avg)))
        # For hydro, preserve the dominant/non-default machine role when present.
        if "machine_role" in allowed:
            roles = [attr_value(dv, "machine_role") for _, dv in members if attr_value(dv, "machine_role")]
            if roles:
                gen_dv_attrs.append(make_attr("machine_role", Counter(roles).most_common(1)[0][0]))
        # dispatch_type distinguishes dispatchable from non-dispatchable
        # generation downstream (tools/import_flexeco.py's PN_GenDispatchable
        # vs. PN_GenNonDispatchable classification) -- preserve the
        # dominant value among merged members, the same way machine_role is.
        if "dispatch_type" in allowed:
            dtypes = [attr_value(dv, "dispatch_type") for _, dv in members if attr_value(dv, "dispatch_type")]
            if dtypes:
                gen_dv_attrs.append(make_attr("dispatch_type", Counter(dtypes).most_common(1)[0][0]))

        gen_dv_rels = [make_rel("representsAsset", [gid])]

        profs = []
        weights = []
        for _, dv in members:
            arr = load_profile(dv)
            if arr is None:
                continue
            w = float((attr_float(dv, "annual_resource_potential") if energy_shape else attr_float(dv, "nominal_power_capacity")) or 0.0)
            if w > 0:
                profs.append(arr)
                weights.append(w)

        if profs and sum(weights) > 0:
            W = np.array(weights, dtype=np.float64)
            raw = (np.vstack(profs).T * W).T.sum(axis=0)
            agg_arr = (normalize_sum_pos1(raw) if energy_shape else (raw / W.sum())).astype(H5_WRITE_DTYPE)
            new_pid = f"profile.gen.{tech}.{rc}{sfx}"
            series_dict[new_pid] = agg_arr
            out_profiles[new_pid] = make_profile_entity(
                new_pid,
                "as_normalized_annual_energy" if energy_shape else "as_capacity_factor",
                "pu", h5_path_relative,
            )
            gen_dv_rels.append(make_rel(view_profile_relation_for_section(view_section), [new_pid]))

        gen_asset_rels: List[Dict[str, Any]] = []
        if view_section == "HydroGenerationUnit.DispatchView":
            mapped_reservoirs: List[str] = []
            for original_asset_id, _dv in members:
                original_asset = section_items(data, asset_class).get(original_asset_id, {})
                res_id = first_rel(original_asset, "drawsFromReservoir")
                if not res_id:
                    continue
                agg_res_id = aggregated_storage_id_for_asset(
                    data, res_id, node_to_agg, a2n, sto_d_by_section, split_voltage,
                    bus_country=bus_country, tech_level=tech_level,
                    tech_level_by_country=tech_level_by_country,
                    reservoir_bus=reservoir_bus,
                )
                if agg_res_id and agg_res_id not in mapped_reservoirs:
                    mapped_reservoirs.append(agg_res_id)
            if mapped_reservoirs:
                gen_asset_rels.append(make_rel("drawsFromReservoir", mapped_reservoirs))

        out_gen_assets_agg_by_class[asset_class][gid] = {"attributes": [make_attr("name", gid)], "relations": gen_asset_rels}
        out_gen_d_agg_by_section[view_section][dv_id] = {"attributes": gen_dv_attrs, "relations": gen_dv_rels}
        out_spv_agg[f"topo.{gid}"] = make_single_port_topo(f"topo.{gid}", gid, agg_bus)

    out_gens = {aid: ent for sec in out_gen_assets_agg_by_class.values() for aid, ent in sec.items()}

    # ── Aggregated storage assets + their original specialised DispatchViews ─────
    # Non-hydro storage stays Storage.DispatchView; hydraulic reservoirs stay
    # ReservoirStorageUnit.DispatchView. Do not collapse reservoirs into generic
    # Storage.DispatchView, otherwise the Frictionless subset loses specialised CSVs.
    out_sto_assets_agg_by_class: Dict[str, Dict[str, Dict[str, Any]]] = {
        cls: {} for cls in set(STORAGE_VIEW_TO_ASSET_CLASS.values())
    }
    out_sto_d_agg_by_section: Dict[str, Dict[str, Dict[str, Any]]] = {
        sec: {} for sec in STORAGE_DISPATCH_VIEW_SECTIONS
    }

    sto_groups: Dict[Tuple[str, str, str], List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    for view_section, views in sto_d_by_section.items():
        asset_class = STORAGE_VIEW_TO_ASSET_CLASS[view_section]
        for dv_id, dv_ent in views.items():
            asset_id = first_rel(dv_ent, "representsAsset")
            if not asset_id:
                continue
            # Reservoirs have no SinglePort.TopologyView of their own --
            # only their paired HydroGenerationUnit does -- so fall back
            # to the bus reachable via drawsFromReservoir.
            bus_id = a2n.get(asset_id) or reservoir_bus.get(asset_id)
            if bus_id in node_to_agg:
                tech = attr_value(dv_ent, "storage_technology_type") or asset_technology_tag(data, asset_class, asset_id, view_section)
                country = bus_country.get(bus_id, "")
                depth = resolve_tech_depth_for_country(country, tech_level_by_country, tech_level)
                tech = technology_tag_at_depth(tech, depth)
                sto_groups[(view_section, node_to_agg[bus_id], id_tag(tech))].append((asset_id, dv_ent))

    for (view_section, agg_bus, tech), members in sto_groups.items():
        asset_class = STORAGE_VIEW_TO_ASSET_CLASS[view_section]
        parts = agg_bus.split(".")
        rc = parts[1]
        sfx = f".{parts[2]}" if split_voltage and len(parts) >= 3 else ""
        sid = f"storage.{tech}.agg.{rc}{sfx}"
        dv_id = f"dispatch.{sid}"

        pcaps   = [attr_float(dv, "nominal_power_capacity")         for _, dv in members]
        ecaps   = [attr_float(dv, "energy_storage_capacity")        for _, dv in members]
        pch     = [attr_float(dv, "maximum_charging_power")         for _, dv in members]
        eff_ch  = [attr_float(dv, "charging_efficiency")            for _, dv in members]
        eff_dis = [attr_float(dv, "discharging_efficiency")         for _, dv in members]
        vop     = [attr_float(dv, "variable_operating_cost")        for _, dv in members]
        vop_ch  = [attr_float(dv, "charging_variable_operating_cost") for _, dv in members]
        inflows = [attr_float(dv, "annual_natural_inflow_energy")   for _, dv in members]

        pc_sum     = sum(x or 0.0 for x in pcaps)
        ec_sum     = sum(x or 0.0 for x in ecaps)
        pch_sum    = sum(x or 0.0 for x in pch)
        inflow_sum = sum(x or 0.0 for x in inflows)

        sto_dv_attrs = [make_attr("name", sid), make_attr("energy_storage_capacity", float(ec_sum), "MWh")]
        if view_section == "Storage.DispatchView":
            sto_dv_attrs.append(make_attr("storage_technology_type", tech))
            if pc_sum > 0:
                sto_dv_attrs.append(make_attr("nominal_power_capacity", float(pc_sum), "MW"))
            if pch_sum > 0:
                sto_dv_attrs.append(make_attr("maximum_charging_power", float(pch_sum), "MW"))
            for aid, vals, weights, unit in [
                ("charging_efficiency", eff_ch, pch, None),
                ("discharging_efficiency", eff_dis, pcaps, None),
                ("variable_operating_cost", vop, pcaps, "MU/MWh"),
                ("charging_variable_operating_cost", vop_ch, pch, "MU/MWh"),
            ]:
                val = wavg(vals, weights)
                if val is not None:
                    sto_dv_attrs.append(make_attr(aid, float(val), unit))
        else:
            if inflow_sum > 0:
                sto_dv_attrs.append(make_attr("annual_natural_inflow_energy", float(inflow_sum), "MWh/year"))

        sto_dv_rels = [make_rel("representsAsset", [sid])]

        if inflow_sum > 0:
            profs = []
            weights = []
            for _, dv in members:
                arr = load_profile(dv)
                if arr is None:
                    continue
                w = float(attr_float(dv, "annual_natural_inflow_energy") or 0.0)
                if w > 0:
                    profs.append(arr)
                    weights.append(w)
            if profs:
                W = np.array(weights, dtype=np.float64)
                raw = (np.vstack(profs).T * W).T.sum(axis=0)
                agg_arr = normalize_sum_pos1(raw).astype(H5_WRITE_DTYPE)
                new_pid = f"profile.inflow.{tech}.{rc}{sfx}"
                series_dict[new_pid] = agg_arr
                out_profiles[new_pid] = make_profile_entity(
                    new_pid, "as_normalized_annual_energy", "pu", h5_path_relative,
                )
                if view_section == "ReservoirStorageUnit.DispatchView":
                    sto_dv_rels.append(make_rel("hasNaturalInflowProfile", [new_pid]))

        out_sto_assets_agg_by_class[asset_class][sid] = {"attributes": [make_attr("name", sid)], "relations": []}
        out_sto_d_agg_by_section[view_section][dv_id] = {"attributes": sto_dv_attrs, "relations": sto_dv_rels}
        out_spv_agg[f"topo.{sid}"] = make_single_port_topo(f"topo.{sid}", sid, agg_bus)

    out_sto = {aid: ent for sec in out_sto_assets_agg_by_class.values() for aid, ent in sec.items()}

    # ── Diagnostic: every aggregated ReservoirStorageUnit should have at
    # least one aggregated HydroGenerationUnit's drawsFromReservoir
    # pointing to it. If not, this is either a genuine pre-existing gap
    # in the source data (some reservoirs were never paired with a
    # generator to begin with) or a real aggregation bug -- surfaced
    # here explicitly, with the original pre-aggregation reservoir ids
    # that fed into it, rather than silently producing an orphaned
    # reservoir with no way to trace it back.
    reservoir_class_ids = set(out_sto_assets_agg_by_class.get("ReservoirStorageUnit", {}).keys())
    if reservoir_class_ids:
        linked_reservoir_ids: set = set()
        for gen_ent in out_gens.values():
            for rel in gen_ent.get("relations", []):
                if rel["id"] == "drawsFromReservoir":
                    linked_reservoir_ids.update(rel["target_entity_ids"])
        orphaned = reservoir_class_ids - linked_reservoir_ids
        for orphan_id in sorted(orphaned):
            original_ids = [
                orig_id for (_vs, _bus, _tech), members in sto_groups.items()
                if _tech in orphan_id  # the aggregated id embeds this group's tech tag
                for orig_id, _dv in members
            ]
            log(
                f"[WARN] Aggregated reservoir '{orphan_id}' has no aggregated "
                f"HydroGenerationUnit linked via drawsFromReservoir -- check "
                f"whether its pre-aggregation source reservoir(s) "
                f"{original_ids or '(could not trace)'} were ever paired with a "
                f"generator in the input data at all."
            )
            # Trace each pre-aggregation source reservoir individually: did it
            # have a paired generator before aggregation, and if so, what id
            # does aggregated_storage_id_for_asset() compute for it right now?
            # A generator that WAS paired pre-aggregation, but whose computed
            # id doesn't match orphan_id, is a real aggregation bug -- a
            # mismatch, not a source-data gap. A reservoir with no paired
            # generator at all pre-aggregation is a genuine source-data gap.
            all_hydro_gens = section_items(data, "HydroGenerationUnit")
            for orig_res_id in original_ids:
                paired_gens = [
                    gen_id for gen_id, gen_ent in all_hydro_gens.items()
                    if first_rel(gen_ent, "drawsFromReservoir") == orig_res_id
                ]
                if not paired_gens:
                    log(f"  - source reservoir '{orig_res_id}': no HydroGenerationUnit "
                        f"draws from it in the input data (genuine source-data gap).")
                    continue
                for gen_id in paired_gens:
                    recomputed = aggregated_storage_id_for_asset(
                        data, orig_res_id, node_to_agg, a2n, sto_d_by_section, split_voltage,
                        bus_country=bus_country, tech_level=tech_level,
                        tech_level_by_country=tech_level_by_country,
                        reservoir_bus=reservoir_bus,
                    )
                    gen_bus = a2n.get(gen_id)
                    gen_agg_bus = node_to_agg.get(gen_bus or "")
                    match = "MATCHES orphan_id" if recomputed == orphan_id else "MISMATCH -- this is the bug"
                    log(f"  - source reservoir '{orig_res_id}' <- generator '{gen_id}' "
                        f"(bus={gen_bus}, agg_bus={gen_agg_bus}): "
                        f"aggregated_storage_id_for_asset() computes '{recomputed}' ({match})")

    # ── Aggregated branch assets ───────────────────────────────────────────────
    dropped_cross = dropped_switch = dropped_internal = 0

    def _process_branch(
        asset_id: str,
        asset_ent: Dict[str, Any],
        pf_views: Dict[str, Dict[str, Any]],
        link_groups: Dict[Tuple[str, str, str], List[Tuple[str, Dict[str, Any]]]],
        branch_type: str,
    ) -> None:
        nonlocal dropped_cross, dropped_switch, dropped_internal
        frm0, to0 = a2br.get(asset_id, (None, None))
        if frm0 not in node_to_agg or to0 not in node_to_agg:
            dropped_cross += 1
            return
        # Find the power flow view for this asset
        pf_ent = next(
            (e for e in pf_views.values() if first_rel(e, "representsAsset") == asset_id),
            {}
        )
        sf = attr_float(pf_ent, "from_switch_closed")
        st = attr_float(pf_ent, "to_switch_closed")
        if (sf is not None and sf == 0) or (st is not None and st == 0):
            dropped_switch += 1
            return
        a = node_to_agg[frm0]
        b = node_to_agg[to0]
        if a == b:
            dropped_internal += 1
            return
        x, y = (a, b) if a < b else (b, a)
        link_groups[(branch_type, x, y)].append((asset_id, pf_ent))

    link_groups: Dict[Tuple[str, str, str], List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)

    for aid, ent in section_items(data, "TransmissionLine").items():
        _process_branch(aid, ent, txl_d, link_groups, "TransmissionLine")
    for aid, ent in section_items(data, "Interconnector").items():
        _process_branch(aid, ent, ico_d, link_groups, "Interconnector")
    for aid, ent in section_items(data, "HVDCLink").items():
        pf_for_hvdc = hvdc_pf_d or hvdc_dispatch_d
        _process_branch(aid, ent, pf_for_hvdc, link_groups, "HVDCLink")
    for aid, ent in section_items(data, "Transformer").items():
        _process_branch(aid, ent, trf_d, link_groups, "Transformer")

    for (btype, a, b), members in link_groups.items():
        a_tag = a.split(".", 1)[1]
        b_tag = b.split(".", 1)[1]

        if btype == "TransmissionLine":
            pf_ents   = [pf for _, pf in members]
            caps       = [attr_float(e, "thermal_capacity_rating") for e in pf_ents]
            xs_vals    = [attr_float(e, "series_reactance_per_km")        for e in pf_ents]
            lens       = [attr_float(e, "line_length")             for e in pf_ents]
            cap_sum    = sum(x or 0.0 for x in caps)
            xw         = wavg(xs_vals, caps)
            lw         = wavg(lens,    caps)

            eid   = f"line.agg.{a_tag}.{b_tag}"
            dv_id = f"pf.{eid}"
            pf_attrs = [
                make_attr("name", dv_id),
                make_attr("thermal_capacity_rating", float(cap_sum), "MVA"),
                make_attr("from_switch_closed", 1),
                make_attr("to_switch_closed",   1),
            ]
            if lw is not None:
                pf_attrs.append(make_attr("line_length",    float(lw), "km"))
            if xw is not None:
                pf_attrs.append(make_attr("series_reactance_per_km", float(xw), "ohm"))

            out_lines[eid]        = {"attributes": [make_attr("name", eid)], "relations": []}
            out_txl_d_agg[dv_id] = {
                "attributes": pf_attrs,
                "relations":  [make_rel("representsAsset", [eid])],
            }
            out_tpv_agg[f"topo.{eid}"] = make_two_port_topo(f"topo.{eid}", eid, a, b)

        elif btype == "Interconnector":
            pf_ents = [pf for _, pf in members]
            caps12    = [attr_float(e, "maximum_power_flow_from_to") for e in pf_ents]
            cap12_sum = sum(x or 0.0 for x in caps12)
            caps21    = [attr_float(e, "maximum_power_flow_to_from") for e in pf_ents]
            cap21_sum = sum(x or 0.0 for x in caps21)

            eid   = f"interconnector.agg.{a_tag}.{b_tag}"
            dv_id = f"pf.{eid}"
            out_icos[eid]        = {"attributes": [make_attr("name", eid)], "relations": []}
            out_ico_d_agg[dv_id] = {
                "attributes": [
                    make_attr("name",             dv_id),
                    make_attr("maximum_power_flow_from_to",         float(cap12_sum), "MW"),
                    make_attr("maximum_power_flow_to_from",         float(cap21_sum), "MW"),
                    make_attr("from_switch_closed", 1),
                    make_attr("to_switch_closed",   1),
                ],
                "relations": [make_rel("representsAsset", [eid])],
            }
            out_tpv_agg[f"topo.{eid}"] = make_two_port_topo(f"topo.{eid}", eid, a, b)

        elif btype == "HVDCLink":
            pf_ents = [pf for _, pf in members]
            caps = [attr_float(e, "p_max_hvdc") or attr_float(e, "max_flow") for e in pf_ents]
            cap_sum = sum(x or 0.0 for x in caps)
            eid = f"hvdc.agg.{a_tag}.{b_tag}"
            pf_id = f"pf.{eid}"
            dv_id = f"dispatch.{eid}"
            out_hvdcs[eid] = {"attributes": [make_attr("name", eid)], "relations": []}
            out_hvdc_pf_d_agg[pf_id] = {
                "attributes": [
                    make_attr("name", pf_id),
                    # The schema only allows concrete HVDC technologies.  For an
                    # aggregated corridor, keep the common member technology when
                    # available; otherwise use VSC as a neutral valid default.
                    make_attr("hvdc_technology_type", (lambda vals: vals[0] if vals and all(v == vals[0] for v in vals) else "VSC")([str(attr_value(e, "hvdc_technology_type")) for e in pf_ents if attr_value(e, "hvdc_technology_type") in ("LCC", "VSC")]) ),
                    make_attr("p_max_hvdc", float(cap_sum), "MW"),
                ],
                "relations": [make_rel("representsAsset", [eid])],
            }
            out_hvdc_dispatch_d_agg[dv_id] = {
                "attributes": [
                    make_attr("name", dv_id),
                    make_attr("max_flow", float(cap_sum), "MW"),
                ],
                "relations": [make_rel("representsAsset", [eid])],
            }
            out_tpv_agg[f"topo.{eid}"] = make_two_port_topo(f"topo.{eid}", eid, a, b)

        else:  # Transformer
            pf_ents  = [pf for _, pf in members]
            caps     = [attr_float(e, "thermal_capacity_rating")  for e in pf_ents]
            vprim    = [attr_float(e, "rated_primary_voltage")    for e in pf_ents]
            vsec     = [attr_float(e, "rated_secondary_voltage")  for e in pf_ents]
            scv      = [attr_float(e, "short_circuit_voltage_in_percentage")    for e in pf_ents]
            npar     = [attr_float(e, "parallel_circuit_count")   for e in pf_ents]
            cap_sum  = sum(x or 0.0 for x in caps)
            np_sum   = sum(x or 0.0 for x in npar)
            vp       = max((x for x in vprim if x is not None), default=None)
            vs       = max((x for x in vsec  if x is not None), default=None)
            scvw     = wavg(scv, caps)

            eid   = f"transformer.agg.{a_tag}.{b_tag}"
            dv_id = f"pf.{eid}"
            pf_attrs = [
                make_attr("name",                 dv_id),
                make_attr("thermal_capacity_rating", float(cap_sum), "MVA"),
                make_attr("from_switch_closed",   1),
                make_attr("to_switch_closed",     1),
            ]
            if np_sum > 0:
                pf_attrs.append(make_attr("parallel_circuit_count", float(np_sum)))
            if vp is not None:
                pf_attrs.append(make_attr("rated_primary_voltage",  float(vp), "kV"))
            if vs is not None:
                pf_attrs.append(make_attr("rated_secondary_voltage", float(vs), "kV"))
            if scvw is not None:
                pf_attrs.append(make_attr("short_circuit_voltage_in_percentage",   float(scvw), "%"))

            out_trafos[eid]       = {"attributes": [make_attr("name", eid)], "relations": []}
            out_trf_d_agg[dv_id] = {
                "attributes": pf_attrs,
                "relations":  [make_rel("representsAsset", [eid])],
            }
            out_tpv_agg[f"topo.{eid}"] = make_two_port_topo(f"topo.{eid}", eid, a, b)

    log(f"dropped_links_outside_subset={dropped_cross}")
    log(f"dropped_links_switch_off={dropped_switch}")
    log(f"dropped_links_internal_after_agg={dropped_internal}")

    # ── Geographic regions ─────────────────────────────────────────────────────
    out_geo: Dict[str, Dict[str, Any]] = {}
    for rc in sorted(region_codes):
        gid = geo_region_id(region_code_level.get(rc, level), rc)
        out_geo[gid] = {"attributes": [make_attr("name", gid)], "relations": []}

    # ── TimestampSeries entity (carry through or create placeholder) ───────────
    ts_sec = section_items(data, "TimestampSeries")
    out_ts: Dict[str, Dict[str, Any]] = {}
    if ts_sec:
        out_ts = ts_sec  # carry through existing
    else:
        out_ts[TIMESTAMP_SERIES_ID] = {
            "attributes": [
                make_attr("name",       TIMESTAMP_SERIES_ID),
                make_attr("resolution", "PT1H"),
            ],
            "relations": [],
        }

    out_obj: Dict[str, Any] = {
        "Carrier":                   section_items(data, "Carrier"),
        "NaturalResource":                 section_items(data, "NaturalResource"),
        "CarrierDomain":                   section_items(data, "CarrierDomain"),
        "GeographicalRegion":              out_geo,
        "TimestampSeries":                 out_ts,
        "Profile":                         out_profiles,
        "ElectricalBus":                   out_buses,
        "BusLocationView":                 out_bus_locs,
        **out_gen_assets_agg_by_class,
        "DemandUnit":                      out_dem,
        **out_sto_assets_agg_by_class,
        "TransmissionLine":                out_lines,
        "Interconnector":                  out_icos,
        "HVDCLink":                        out_hvdcs,
        "Transformer":                     out_trafos,
        "SinglePort.TopologyView":         out_spv_agg,
        "TwoPort.TopologyView":            out_tpv_agg,
        **out_gen_d_agg_by_section,
        "Demand.DispatchView":             out_dem_d_agg,
        **out_sto_d_agg_by_section,
        "TransmissionLine.PowerFlowView":  out_txl_d_agg,
        "Interconnector.PowerFlowView":    out_ico_d_agg,
        "HVDCLink.PowerFlowView":          out_hvdc_pf_d_agg,
        "HVDCLink.DispatchView":           out_hvdc_dispatch_d_agg,
        "Transformer.PowerFlowView":       out_trf_d_agg,
    }

    stats = {
        "buses":  len(out_buses),
        "gens":   len(out_gens),
        "loads":  len(out_dem),
        "stors":  len(out_sto),
        "lines":  len(out_lines),
        "icos":   len(out_icos),
        "trafos": len(out_trafos),
    }
    return out_obj, series_dict, stats


# ── Summary writer ────────────────────────────────────────────────────────────

def write_summary(
    outdir: Path,
    level: str,
    split_voltage: bool,
    selectors: List[str],
    invalid_selectors: List[str],
    kept_buses: Dict[str, Dict[str, Any]],
    original_data: Dict[str, Any],
    result_stats: Dict[str, int],
    log_lines: List[str],
) -> None:
    country_counts = summarize_kept_by_country(
        list(kept_buses.keys()), section_items(original_data, "ElectricalBus")
    )
    lines = [
        f"LEVEL={level}",
        f"SPLIT_VOLTAGE={split_voltage}",
        f"KEEP_CODES={selectors}",
        f"INVALID_KEEP_CODES={invalid_selectors}",
        "",
        "Kept buses by country:",
        *(f"  {k}: {v}" for k, v in sorted(country_counts.items())),
        "",
        "Output entity counts:",
        *(f"  {k}: {result_stats.get(k, 0)}"
          for k in ["buses", "gens", "loads", "stors", "lines", "icos", "trafos"]),
        "",
        "Run log:",
        *log_lines,
    ]
    (outdir / "subset_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="CESDM nodal-model aggregation — nuts3 / nuts2 / nuts1 / country.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ── I/O ──────────────────────────────────────────────────────────────────
    p.add_argument(
        "--schemas", metavar="DIR", default="schemas/cesdm",
        help="CESDM schema directory (passed to build_model_from_yaml).",
    )
    p.add_argument(
        "--yaml", metavar="FILE", default=_DEFAULT_YAML,
        help="Input CESDM hierarchical YAML file.",
    )
    p.add_argument(
        "--h5", metavar="FILE", default=_DEFAULT_H5,
        help="Input profile HDF5 file (legacy flat format). "
             "Required unless --no-profiles is set.",
    )
    p.add_argument(
        "--outdir", metavar="DIR", default=None,
        help="Output directory. Defaults to '<cwd>/aggregated_<level>[_<codes>]'.",
    )

    # ── Aggregation control ───────────────────────────────────────────────────
    p.add_argument(
        "--level", metavar="LEVEL",
        choices=["disaggregated", "nuts3", "nuts2", "nuts1", "country"],
        default="disaggregated",
        help="Default spatial aggregation level, used for every country "
             "not given its own override in --level-by-country.",
    )
    p.add_argument(
        "--level-by-country", metavar="COUNTRY=LEVEL", nargs="*", default=[],
        help="Per-country spatial aggregation level overrides, e.g. "
             "--level-by-country CH=nuts3 DE=country -- keeps Switzerland "
             "at nuts3 resolution while aggregating Germany down to one "
             "node per country, in the same run. Countries not listed use "
             "--level.",
    )
    p.add_argument(
        "--tech-level", metavar="N", type=int, default=None,
        help="Default technology-aggregation depth: how many dot-separated "
             "segments of each asset's hasTechnology id to keep as a "
             "distinct aggregation group, e.g. 3 keeps "
             "'Generation.Thermal.Gas.CCGT' as 'Generation.Thermal.Gas' -- "
             "merging CCGT/OCGT/other gas subtypes at the same node into "
             "one aggregated generator. Omit (the default) for no "
             "technology aggregation -- every distinct technology stays "
             "its own aggregated asset, the original behaviour.",
    )
    p.add_argument(
        "--tech-level-by-country", metavar="COUNTRY=N", nargs="*", default=[],
        help="Per-country technology-aggregation depth overrides, e.g. "
             "--tech-level-by-country DE=2 keeps fine-grained per-"
             "technology assets everywhere except Germany, where "
             "'Generation.Thermal.Gas.CCGT' and 'Generation.Thermal.Coal.*' "
             "both collapse to 'Generation.Thermal' (all thermal merged "
             "into one). Countries not listed use --tech-level.",
    )
    p.add_argument(
        "--keep", metavar="CODE", nargs="*", default=["CH"],
        help="ISO-2 or NUTS prefix codes to include (e.g. CH DE fr042). "
             "Pass no arguments to keep everything.",
    )
    p.add_argument(
        "--split-voltage", action=argparse.BooleanOptionalAction, default=True,
        help="Maintain separate aggregated nodes per voltage level.",
    )
    p.add_argument(
        "--round-kv", metavar="N", type=int, default=1,
        help="Decimal rounding precision for voltage grouping.",
    )

    # ── Output switches ───────────────────────────────────────────────────────
    p.add_argument(
        "--no-yaml", dest="export_yaml", action="store_false", default=True,
        help="Skip writing the output YAML file.",
    )
    p.add_argument(
        "--no-profiles", dest="export_profiles", action="store_false", default=True,
        help="Skip reading / writing profile HDF5 files.",
    )
    p.add_argument(
        "--no-log", dest="write_log", action="store_false", default=True,
        help="Skip writing the aggregation_log.txt file.",
    )

    return p.parse_args()


def main():
    args = parse_args()

    schemas_dir = Path(args.schemas).expanduser().resolve()
    yaml_path   = Path(args.yaml).expanduser().resolve()
    h5_path     = Path(args.h5).expanduser().resolve()

    keep_codes: List[str] = args.keep or []
    level         = args.level
    level_by_country = parse_kv_overrides(args.level_by_country, value_type=str, what="level")
    invalid_levels = {c: lv for c, lv in level_by_country.items()
                       if lv not in ("disaggregated", "nuts3", "nuts2", "nuts1", "country")}
    if invalid_levels:
        raise SystemExit(
            f"Invalid --level-by-country value(s) {invalid_levels} -- must be one "
            f"of disaggregated/nuts3/nuts2/nuts1/country."
        )
    tech_level = args.tech_level
    tech_level_by_country = parse_kv_overrides(args.tech_level_by_country, value_type=int, what="tech depth")
    split_voltage = args.split_voltage
    export_yaml    = args.export_yaml
    export_profiles = args.export_profiles
    write_log_txt  = args.write_log

    if args.outdir:
        outdir = Path(args.outdir).expanduser().resolve()
    else:
        outdir = Path.cwd() / build_outdir_name(level, keep_codes)
    outdir.mkdir(parents=True, exist_ok=True)

    log_lines: List[str] = []

    def log(msg: str) -> None:
        print(msg)
        log_lines.append(msg)

    log(f"input yaml={yaml_path}")
    log(f"input h5={h5_path}")
    log(f"outdir={outdir}")
    log(f"level={level}  split_voltage={split_voltage}  keep={keep_codes}")
    if level_by_country:
        log(f"level_by_country={level_by_country}")
    log(f"tech_level={tech_level}")
    if tech_level_by_country:
        log(f"tech_level_by_country={tech_level_by_country}")

    if not schemas_dir.exists():
        raise SystemExit(f"Schema directory not found: {schemas_dir}")
    if not yaml_path.exists():
        raise SystemExit(f"YAML not found: {yaml_path}")
    if export_profiles and not h5_path.exists():
        raise SystemExit(f"HDF5 not found: {h5_path}")

    log(f"loading schema from {schemas_dir} …")
    input_model = load_cesdm_model(schemas_dir, yaml_path)
    data = model_to_data(input_model)
    log(f"schema + model loaded via cesdm_toolbox")

    buses_sec = section_items(data, "ElectricalBus")
    log(
        f"parsed buses={len(buses_sec)} "
        f"gens={len(section_items(data, 'GenerationUnit'))} "
        f"loads={len(section_items(data, 'DemandUnit'))} "
        f"stors={len(section_items(data, 'StorageUnit'))} "
        f"lines={len(section_items(data, 'TransmissionLine'))} "
        f"icos={len(section_items(data, 'Interconnector'))} "
        f"trafos={len(section_items(data, 'Transformer'))}"
    )

    # Resolve profile input: Parquet takes priority over HDF5
    _profiles_parquet = getattr(args, "profiles_parquet", None)
    _out_format       = getattr(args, "out_format", "hdf5")
    if export_profiles and _profiles_parquet:
        pm = ProfileMatrix(Path(_profiles_parquet).expanduser().resolve())
    elif export_profiles:
        pm = ProfileMatrix(h5_path)
    else:
        pm = None
    if pm is not None:
        log(f"h5 T={pm.T} profiles={len(pm.name_to_idx)}")

    all_nuts3   = collect_all_nuts3_codes(buses_sec)
    selectors_r = [normalize_code(x) for x in keep_codes if normalize_code(x)]
    selectors, invalid_selectors = validate_selectors(selectors_r, all_nuts3)

    if invalid_selectors:
        log(f"[WARN] invalid selectors={invalid_selectors}")
    log(f"subset selectors={selectors}")

    kept_buses: Dict[str, Dict[str, Any]] = {
        bid: ent for bid, ent in buses_sec.items()
        if (n3 := node_nuts3_code(bid, ent)) and selector_matches_nuts3(n3, selectors)
    }

    log(f"kept_buses={len(kept_buses)} dropped={len(buses_sec) - len(kept_buses)}")
    if not kept_buses:
        raise SystemExit(f"No buses remain after applying --keep {keep_codes}")

    # Relative path for data_reference attributes in Profile entities
    h5_out_path = outdir / "cesdm" / "profiles" / "profiles.h5"
    h5_relative = str(h5_out_path.relative_to(outdir))

    uses_pure_disaggregated = (
        level == "disaggregated" and not level_by_country and not tech_level and not tech_level_by_country
    )

    if uses_pure_disaggregated:
        out_obj, series_dict, stats = build_subset_disaggregated(
            data, kept_buses, pm, log
        )
        log(
            f"mode=disaggregated buses={stats['buses']} gens={stats['gens']} "
            f"loads={stats['loads']} stors={stats['stors']} "
            f"lines={stats['lines']} icos={stats['icos']} trafos={stats['trafos']}"
        )
    else:
        out_obj, series_dict, stats = aggregate_subset(
            data, kept_buses, level, split_voltage, pm, log, h5_relative,
            round_kv=args.round_kv,
            level_by_country=level_by_country,
            tech_level=tech_level,
            tech_level_by_country=tech_level_by_country,
        )
        log(
            f"mode={level} buses={stats['buses']} gens={stats['gens']} "
            f"loads={stats['loads']} stors={stats['stors']} "
            f"lines={stats['lines']} icos={stats['icos']} trafos={stats['trafos']}"
        )

    if export_profiles and series_dict:
        T = pm.T if pm is not None else 8760
        if _out_format == "parquet":
            pq_out = outdir / "cesdm" / "profiles" / "profiles.parquet"
            write_profiles_parquet(pq_out, series_dict, T)
            log(f"wrote profiles (parquet)={pq_out} n_series={len(series_dict)}")
        else:
            write_profiles_h5_cesdm(h5_out_path, series_dict, T)
            log(f"wrote profiles (hdf5)={h5_out_path} n_series={len(series_dict)}")

    if export_yaml:
        out_yaml = outdir / "cesdm" / "yaml" / f"aggregated_cesdm_{level}.yaml"
        out_model = data_to_model(schemas_dir, out_obj)
        out_model.export_yaml_hierarchical(str(out_yaml))
        log(f"wrote yaml={out_yaml} (via cesdm_toolbox export_yaml_hierarchical)")

        # Frictionless Data Package — self-describing, one CSV per class
        out_model.export_frictionless(
            outdir / "cesdm" / "frictionless",
            name  = f"pypsa data in {level} resolution",
            title = f"pypsa {level}-level model",
        )

    write_summary(outdir, level, split_voltage, selectors, invalid_selectors, kept_buses, data, stats, log_lines)

    if write_log_txt:
        (outdir / "aggregation_log.txt").write_text(
            "\n".join(log_lines) + "\n", encoding="utf-8"
        )

    if pm is not None:
        pm.close()


if __name__ == "__main__":
    main()
