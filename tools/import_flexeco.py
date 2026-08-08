"""
import_flexeco.py
================

Bidirectional converter between FlexEco .jpn (JSON) files and the
CESDM V4 model (ear_toolbox / cesdm_toolbox).

Current schema mapping
----------------------
All attributes and relations are stored directly on concrete asset entities.
The converter does not create, resolve, or depend on representation entities.
No backwards-compatible support for the former representation split is retained.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.io import loadmat

import sys

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

_REPO_ROOT = _repo_root()
for _path in (_REPO_ROOT, _REPO_ROOT / "tools"):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from cesdm_toolbox import build_model_from_yaml, CesdmModel
from ear_toolbox import Entity
from hydro_utils import hydro_machine_role, hydro_storage_kind
from generation_classifier import generation_asset_class, hydrogen_generation_efficiency

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------
_DOMAIN_ID  = "domain.electricity"
_CARRIER_ID = "carrier.electricity"

# ---------------------------------------------------------------------------
# Structured asset hierarchy helpers
# ---------------------------------------------------------------------------

GENERATION_ASSET_CLASSES = (
    "GenerationUnit", "HydroGenerationUnit",
    "GenerationUnit", )

STORAGE_ASSET_CLASSES = (
    "StorageUnit",
    "ReservoirStorageUnit",
)

def _entities_for_classes(model: CesdmModel, class_names: tuple[str, ...]) -> dict:
    """Return a merged {entity_id: entity} map for all listed concrete class buckets."""
    out = {}
    for cls in class_names:
        out.update(model.entities.get(cls, {}))
    return out

def _entity_class_name(model: CesdmModel, entity_id: object | None) -> Optional[str]:
    """Return the concrete class name for an entity id or Entity object, if present."""
    if not entity_id:
        return None

    # Some internal helpers pass an Entity instance rather than its id.  In that
    # case the class is already available and using the object as a dict key
    # would fail because Entity is unhashable.
    cls = getattr(entity_id, "cls", None) or getattr(entity_id, "class_name", None)
    if isinstance(cls, str) and cls:
        return cls

    eid = getattr(entity_id, "id", entity_id)
    if not isinstance(eid, str):
        return None

    for cls_name, entities in getattr(model, "entities", {}).items():
        if eid in entities:
            return cls_name
    return None

def _technology_key_from_flexeco(el: dict) -> str:
    """Return a lower-case technology key assembled from common FlexEco fields."""
    parts = [
        str(el.get("technology", "")),
        str(el.get("name", "")),
        str(el.get("carrier", "")),
        str(el.get("fuel", "")),
    ]
    return " ".join(parts).lower()

def _generation_asset_class_from_flexeco(el: dict) -> str:
    """Map a FlexEco generator element to the structured GenerationUnit subclass.

    Uses the shared generation classifier so import_from_flexeco follows the
    same technology semantics as PyPSA/TYNDP import and CESDM→FlexECO export.
    """
    return generation_asset_class(el.get("carrier"), el.get("technology") or el.get("name"))

def _storage_asset_class_from_flexeco(cls: str, el: dict) -> str:
    """Map a FlexEco storage element class to the correct StorageUnit subclass.

    PN_StorageDam          → ReservoirStorageUnit (reservoir hydro)
    PN_StoragePump         → ReservoirStorageUnit (open-loop PHS upper reservoir)
    PN_StoragePumpNoInfeed → ReservoirStorageUnit (closed-loop PHS upper reservoir)
    everything else        → StorageUnit (batteries, generic)

    PHS and reservoir-hydro both use ReservoirStorageUnit. The distinction
    is captured on the linked HydroGenerationUnit (is_reversible = true/false)
    and directly on ReservoirStorageUnit (has_active_charging, annual_natural_inflow_energy).
    """
    key = f"{cls} {_technology_key_from_flexeco(el)}".lower()
    if any(x in key for x in ("battery", "electrochemical")):
        return "StorageUnit"
    if any(x in key for x in ("reservoir", "pondage", "dam", "pn_storagedam",
                              "pump_storage", "pumped", "pn_storagepump",
                              "phs", "pump")):
        return "ReservoirStorageUnit"
    return "StorageUnit"


# ---------------------------------------------------------------------------
# Shared helper: get a scalar value from an entity attribute
# ---------------------------------------------------------------------------

def _av(entity, name, default=None):
    """Return the scalar value of an attribute, unwrapping {value:...} dicts."""
    raw = getattr(entity, "data", {}).get(name, default)
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"]
    if isinstance(entity, dict) and name in entity:
        return entity[name]
    return raw

# ---------------------------------------------------------------------------
# Direct asset topology helpers
# ---------------------------------------------------------------------------

def _connect_to_node(model: CesdmModel, asset_id: str, bus_id: str) -> str:
    """Connect a single-port asset directly to a network node."""
    model.add_relation(asset_id, "atNode", bus_id)
    return asset_id


def _connect_branch(
    model: CesdmModel,
    asset_id: str,
    from_bus: str,
    to_bus: str,
) -> str:
    """Connect a two-port asset directly to its endpoint nodes."""
    model.add_relation(asset_id, "fromNode", from_bus)
    model.add_relation(asset_id, "toNode", to_bus)
    return asset_id


def _entity_by_id(model: CesdmModel, entity_id: str | None):
    """Return the concrete entity object for an id, independent of class."""
    if not entity_id:
        return None
    for entities in model.entities.values():
        ent = entities.get(entity_id)
        if ent is not None:
            return ent
    return None


_HYDRO_CATEGORY_TO_FLEXECO: dict[str, str] = {
    "reservoir_hydro": "PN_StorageDam",
    "phs_open_loop":   "PN_StoragePump",
    "phs_closed_loop": "PN_StoragePumpNoInfeed",
}
_FLEXECO_TO_HYDRO_CATEGORY: dict[str, str] = {
    "PN_StorageDam":          "reservoir_hydro",
    "PN_StoragePump":         "phs_open_loop",
    "PN_StoragePumpNoInfeed": "phs_closed_loop",
}

# ---------------------------------------------------------------------------
# MAT-file profile loaders (unchanged logic, kept for compatibility)
# ---------------------------------------------------------------------------

def load_mat_variable(var_name: str, base_path: Path):
    base_path = Path(base_path)
    candidate = base_path / f"{var_name}.mat"
    if not candidate.is_file():
        print(f"Could not find .mat file for '{var_name}'. Tried: {candidate}")
        return False, None
    data = loadmat(candidate)
    if var_name not in data:
        print(f"Variable '{var_name}' not found in {candidate}.")
        return False, None
    return True, np.asarray(data[var_name])

def load_mat_file(var_name: str,
                  mat_filename: Optional[str] = None,
                  fallback_path: Optional[Path] = None,
                  whole_data: Optional[dict] = None):
    candidates = []
    if fallback_path is not None:
        candidates.append(Path(fallback_path) / mat_filename)

    mat_file = next((c for c in candidates if c.is_file()), None)
    if mat_file is None:
        print(f"Could not find .mat file for '{var_name}'. Tried: {candidates}")
        return False, None, None

    data = whole_data if whole_data is not None else loadmat(mat_file)
    if var_name not in data:
        print(f"Variable '{var_name}' not found in {mat_file}.")
        return False, None, data
    return True, np.asarray(data[var_name]), data

def add_profile(el: dict, type_: int, mat_data: Optional[dict]):
    profile_name = el.get("xi_ref_profile", "")
    if not profile_name:
        return False, None, None
    if type_ == 1:
        ret, arr = load_mat_variable(profile_name,
                                     Path("../data/sach2021/profiles"))
        return ret, (np.transpose(arr) if ret else None), None
    elif type_ == 2:
        ret, arr, mat_data = load_mat_file(
            profile_name, "profiles.mat",
            Path("../data/sach2021/profiles"), mat_data)
        return ret, (np.transpose(arr) if ret else None), mat_data
    return False, None, None

def _rel_target(entity, rel_name: str) -> str | None:
    """Return the first target entity id of a relation on an entity, or None."""
    if entity is None:
        return None
    raw = getattr(entity, "data", {}).get(rel_name)
    if isinstance(raw, (list, tuple)):
        return raw[0] if raw else None
    return raw if raw else None

# ---------------------------------------------------------------------------
# Profile type ↔ FlexEco profile_factor_type mapping
#
# CESDM profile_type         FlexEco profile_factor_type
# ─────────────────────────  ───────────────────────────
# as_SI                      0   absolute SI unit values
# as_normalized_annual_energy 1  values sum to 1 over the year
# as_capacity_factor          2  dimensionless [0, 1]
# ---------------------------------------------------------------------------

_PROFILE_TYPE_TO_FACTOR_TYPE: dict[str, int] = {
    "as_SI":                        0,
    "as_normalized_annual_energy":  1,
    "as_capacity_factor":           2,
}

_FACTOR_TYPE_TO_PROFILE_TYPE: dict[int, str] = {
    v: k for k, v in _PROFILE_TYPE_TO_FACTOR_TYPE.items()
}

def _profile_factor_type(model, prof_id: str | None) -> int | None:
    """
    Return the FlexEco profile_factor_type integer for a Profile entity.

    Looks up the Profile entity by id, reads its ``profile_type`` attribute,
    and maps it to the corresponding integer.  Returns None if the Profile
    entity or its profile_type is absent.
    """
    if not prof_id:
        return None
    prof_ent = model.entities.get("Profile", {}).get(prof_id)
    if prof_ent is None:
        return None
    raw = getattr(prof_ent, "data", {}).get("profile_type")
    if isinstance(raw, dict):
        raw = raw.get("value")
    return _PROFILE_TYPE_TO_FACTOR_TYPE.get(str(raw) if raw else "", None)

# ===========================================================================
# export_to_flexeco
# ===========================================================================

def _export_profiles_hdf5(model: CesdmModel, hdf5_path: str | Path) -> None:
    """
    Collect all Profile entities referenced by model assets and write
    their numeric payloads to an HDF5 file in the FlexEco flat-matrix layout.

    HDF5 layout
    -----------
    /series_names  — ASCII string dataset, shape (n_profiles,), dtype S64.
                     Each entry is the profile entity id (= xi_ref_profile key
                     used in the .jpn file).

    /values        — float64 dataset, shape (n_timesteps, n_profiles),
                     little-endian.  Column order matches series_names.
                     Profiles whose numeric data is not attached are filled
                     with zeros and a warning is printed.

    Profile ids are collected by traversing the profile relations on the
    concrete generation, demand, and storage asset classes:
      hasAvailabilityProfile / hasRunOfRiverInflowProfile
          GenerationUnit and HydroGenerationUnit
      hasDemandProfile
          DemandUnit
      hasNaturalInflowProfile
          StorageUnit and ReservoirStorageUnit

    Numeric arrays must be attached to the in-memory Profile entities before
    calling this function — use _attach_profile_values(model, profiles_values).

    Parameters
    ----------
    model :
        Populated CesdmModel with Profile entities and numeric arrays attached
        via _attach_profile_values.
    hdf5_path :
        Output .h5 file path. Parent directory is created if absent.
    """
    try:
        import h5py
        import numpy as np
    except ImportError:
        raise ImportError(
            "h5py and numpy are required for HDF5 profile export. "
            "Install with: pip install h5py numpy"
        )

    hdf5_path = Path(hdf5_path)
    hdf5_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Collect all referenced profile ids (preserve insertion order) ─────
    ref_relations = ("hasAvailabilityProfile", "hasRunOfRiverInflowProfile", "hasDemandProfile", "hasNaturalInflowProfile")
    seen: set[str] = set()
    series_names: list[str] = []

    for asset_cls in (
        "GenerationUnit",
        "HydroGenerationUnit",
        "DemandUnit",
        "StorageUnit",
        "ReservoirStorageUnit",
    ):
        for ent in (model.entities.get(asset_cls) or {}).values():
            data = getattr(ent, "data", {}) or {}
            for rel in ref_relations:
                raw = data.get(rel)
                if raw is None:
                    continue
                targets = raw if isinstance(raw, (list, tuple)) else [raw]
                for t in targets:
                    pid = str(t) if t else None
                    if pid and pid not in seen:
                        seen.add(pid)
                        series_names.append(pid)

    if not series_names:
        print("[_export_profiles_hdf5] No referenced profiles found — HDF5 not written.")
        return

    # ── Collect arrays in the same order as series_names ─────────────────
    profile_store = model.entities.get("Profile", {})
    n_profiles    = len(series_names)
    n_timesteps   = None   # determined from first non-empty array
    arrays: list  = []

    for pid in series_names:
        prof_ent = profile_store.get(pid)
        arr_raw  = None
        if prof_ent is not None:
            arr_raw = getattr(prof_ent, "data", {}).get("_values")
        if arr_raw is not None:
            arr = np.asarray(arr_raw, dtype=np.float64).ravel()
            if n_timesteps is None:
                n_timesteps = len(arr)
            arrays.append(arr)
        else:
            arrays.append(None)   # placeholder; filled with zeros below

    if n_timesteps is None:
        print("[_export_profiles_hdf5] No numeric arrays attached — "
              "all profiles will be zero-filled.")
        n_timesteps = 8760        # safe default

    # Zero-fill missing profiles and warn
    matrix_cols: list = []
    for pid, arr in zip(series_names, arrays):
        if arr is None:
            print(f"  [WARN] Profile '{pid}' has no attached values — zero-filled.")
            matrix_cols.append(np.zeros(n_timesteps, dtype=np.float64))
        elif len(arr) != n_timesteps:
            print(f"  [WARN] Profile '{pid}' length {len(arr)} ≠ {n_timesteps} — "
                  f"truncated/padded.")
            col = np.zeros(n_timesteps, dtype=np.float64)
            col[:min(len(arr), n_timesteps)] = arr[:n_timesteps]
            matrix_cols.append(col)
        else:
            matrix_cols.append(arr)

    # Shape: (n_timesteps, n_profiles)  — columns = profiles
    data_matrix = np.column_stack(matrix_cols).astype(np.float64)

    # ── Write HDF5 ────────────────────────────────────────────────────────
    with h5py.File(str(hdf5_path), "w") as hf:
        # /series_names  ASCII S64, shape (n_profiles,)
        hf.create_dataset(
            "series_names",
            data=np.array(series_names, dtype="S64"),
        )
        # /values  float64, shape (n_timesteps, n_profiles)
        hf.create_dataset(
            "values",
            data=data_matrix,
            dtype=np.float64,
        )

    print(f"[_export_profiles_hdf5] Written {n_profiles} profiles "
          f"× {n_timesteps} timesteps → {hdf5_path}")

def _attach_profile_values(model: CesdmModel, values_map: dict) -> int:
    """
    Attach numpy arrays from values_map to the corresponding Profile entities
    so that _export_profiles_hdf5 can write them to HDF5.

    Call this after populating the model and before export_to_flexeco::

        _attach_profile_values(model, profiles_values)
        export_to_flexeco(model, "output.jpn", hdf5_path="profiles.h5")

    Parameters
    ----------
    model :
        Populated CesdmModel.
    values_map :
        Dict mapping profile entity id → numpy array (as produced by
        _register_profile_entity in the TYNDP pipeline).

    Returns
    -------
    int
        Number of arrays successfully attached.
    """
    profile_store = model.entities.get("Profile", {})
    attached = 0
    for prof_id, arr in (values_map or {}).items():
        ent = profile_store.get(prof_id)
        if ent is not None:
            data = getattr(ent, "data", None)
            if data is not None:
                data["_values"] = arr
                attached += 1
    return attached


def _is_flexeco_storage_dam_candidate(storage_id: str, ent, tt_id: str | None, sv) -> bool:
    """Return True only for real reservoir/pondage hydro storage assets.

    Detection uses (in order of reliability):
    1. ent.cls — the class name on the ear_toolbox Entity dataclass.
       ReservoirStorageUnit is always a dam candidate.
    2. tt_id (hasTechnology) — explicit technology type (TYNDP importer).
    3. Heuristic key scan — fallback for untyped models.

    PumpedHydro/pump storage is always excluded regardless of detection path.
    """
    # ── 1. Class-based detection (most reliable) ─────────────────────
    cls_name = (
        getattr(ent, "cls", None)          # ear_toolbox Entity.cls
        or getattr(ent, "class_name", "")  # legacy fallback
        or getattr(ent, "type_name", "")   # legacy fallback
    )
    cls_lower = str(cls_name or "").lower()

    if any(x in cls_lower for x in ("pumpedhydro", "pumpedstorage", "pumpstorage",
                                     "pumpedhydrostorageunit")):
        return False
    if cls_lower in ("reservoirstorageunit",):
        return True

    # ── 1b. PHS detection via storage asset has_active_charging ─
    # A ReservoirStorageUnit that is the upper reservoir of a PHS plant has
    # has_active_charging=True. These export as PN_StoragePumpNoInfeed or
    # PN_StoragePump, NOT as PN_StorageDam.
    if sv is not None and _av(sv, "has_active_charging", False):
        return False

    # ── 2. Technology type detection ──────────────────────────────────
    explicit_type = str(tt_id or "").lower()
    if any(x in explicit_type for x in ("pumpedhydro", "pump_storage", "pumped",
                                         "phs.closedloop", "phs.openloop")):
        return False
    if explicit_type in {"storage.hydro.reservoir", "storage.hydro.pondage"}:
        return True

    # ── 3. Heuristic key scan (fallback for untyped models) ───────────
    key = " ".join(str(x or "").lower() for x in [
        storage_id,
        tt_id,
        _av(ent, "name", ""),
        _av(sv, "storage_technology_type", ""),
    ])
    if "pumpedhydro" in key or "pump_storage" in key or "pumped" in key or "pump" in key:
        return False
    if "reservoir" in key or "pondage" in key:
        return True

    return False


def export_to_flexeco(model: CesdmModel, output_path: str | Path, *, hdf5_path: str | Path | None = None) -> None:
    """
    Export a CESDM V4 model to a FlexEco .jpn JSON file.

    ----------------
    - Node data read from NetworkNode subclass entities (ElectricalBus, GasBus, etc.)
    - Node topology (locatedIn, belongsToCarrierDomain) replaces isInGeographicalRegion / isInEnergyDomain
    - Transmission topology and electrical parameters stored directly on branch assets
    - Generator operational data read directly from generation assets
    - Storage operational data read directly from storage assets
    - Demand operational data read directly from demand assets
    - hasTechnology replaces instanceOf for technology-type lookups

    Parameters
    ----------
    model :
        Populated CesdmModel instance.
    output_path :
        Path for the FlexEco .jpn JSON output file.
    hdf5_path : optional
        If provided, all Profile numeric payloads referenced by the model are
        collected via the hasAvailabilityProfile / hasDemandProfile / hasNaturalInflowProfile
        relations and written to an HDF5 file at this path using the same
        /profiles/<profile_id>/values layout as :meth:`CesdmModel.export_hdf5`.
        Profile metadata (profile_type, profile_unit, data_reference) and the
        TimestampSeries metadata are also written as HDF5 group attributes.
        Pass this alongside the .jpn file so FlexEco tooling can resolve the
        xi_ref_profile keys back to numeric arrays.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    elements   = []
    used_uids: set[int] = set()
    id_to_uid: dict[str, int] = {}

    # ── UID assignment ────────────────────────────────────────────────────

    def _uid(ent_id: str, prefix: str) -> int:
        if ent_id in id_to_uid:
            return id_to_uid[ent_id]
        uid = None
        if ent_id.startswith(prefix):
            suffix = ent_id[len(prefix):]
            if suffix.isdigit():
                uid = int(suffix)
        if uid is None:
            uid = (max(used_uids) + 1) if used_uids else 1
        while uid in used_uids:
            uid += 1
        used_uids.add(uid)
        id_to_uid[ent_id] = uid
        return uid

    # ── Entity stores ─────────────────────────────────────────────────────

    # Merge all NetworkNode subclasses into one lookup dict.
    # "Bus" key is retained as a deprecated fallback for models serialised
    # before the NetworkNode refactor (CESDM < v4).
    bus_entities = (
        model.entities.get("Bus",           {})  # deprecated — remove in v5
        | model.entities.get("ElectricalBus",  {})
        | model.entities.get("GasBus",         {})
        | model.entities.get("HydrogenBus",    {})
        | model.entities.get("HeatBus",        {})
        | model.entities.get("WaterBus",       {})
    )
    carrier_entities    = model.entities.get("EnergyCarrier", {})
    transmission_ents   = model.entities.get("TransmissionElement", {})
    line_ents           = (model.entities.get("TransmissionLine", {})
                          | model.entities.get("TransmissionLine_legacy", {}))
    tr2_ents            = (model.entities.get("Transformer", {})
                          | model.entities.get("TwoWindingPowerTransformer", {}))
    hvdc_ents           = model.entities.get("HVDCLink", {})
    ntc_ents            = (model.entities.get("Interconnector", {})
                          | model.entities.get("NetTransferCapacity", {}))
    # NTC and HVDC parameters are stored directly on their concrete assets
    gen_ents            = _entities_for_classes(model, GENERATION_ASSET_CLASSES)
    stor_ents           = _entities_for_classes(model, STORAGE_ASSET_CLASSES)
    dem_ents            = model.entities.get("DemandUnit", {})
    gen_type_ents       = model.entities.get("GeneratorType", {})
    stor_type_ents      = model.entities.get("StorageType", {})
    esm_ents            = model.entities.get("EnergySystemModel", {})

    # Assign UIDs in blocks
    node_uid_map: dict[str, int] = {}
    for uid_start, ent_dict, target in [
        (10_000_001, bus_entities,        node_uid_map),
    ]:
        uid = uid_start
        for eid in ent_dict:
            target[eid] = uid
            used_uids.add(uid)
            id_to_uid[eid] = uid
            uid += 1

    trans_uid_map:  dict[str, int] = {}
    line_uid_map:   dict[str, int] = {}
    tr2_uid_map:    dict[str, int] = {}
    dc_uid_map:     dict[str, int] = {}
    ntc_uid_map:    dict[str, int] = {}
    gen_uid_map:    dict[str, int] = {}
    stor_uid_map:   dict[str, int] = {}
    dem_uid_map:    dict[str, int] = {}

    for uid_start, ent_dict, target in [
        (20_000_001, transmission_ents, trans_uid_map),
        (21_000_001, line_ents,         line_uid_map),
        (21_500_001, ntc_ents,          ntc_uid_map),
        (22_000_001, tr2_ents,          tr2_uid_map),
        (23_000_001, hvdc_ents,          dc_uid_map),
        (40_000_001, gen_ents,          gen_uid_map),
        (50_000_001, stor_ents,         stor_uid_map),
        (30_000_001, dem_ents,          dem_uid_map),
    ]:
        uid = uid_start
        for eid in ent_dict:
            target[eid] = uid
            used_uids.add(uid)
            id_to_uid[eid] = uid
            uid += 1


    # ── Helper: bus uid from entity id ───────────────────────────────────

    def _bus_uid(bus_id: str | None) -> int | None:
        if bus_id is None:
            return None
        return node_uid_map.get(bus_id)

    # ── Helper: carrier attributes ────────────────────────────────────────

    def _carrier_name(cid: str | None) -> str | None:
        if cid is None:
            return None
        return cid[2:] if cid.startswith("c_") else cid

    def _carrier_entity(cid: str | None):
        """Resolve a carrier entity across all concrete schema classes.

        ``model.entities`` stores entities under their concrete class.  A
        nuclear fuel carrier may therefore live under a subclass of
        ``EnergyCarrier`` and is not guaranteed to be present in
        ``model.entities["EnergyCarrier"]``.
        """
        if not cid:
            return None
        return _entity_by_id(model, cid)

    def _carrier_cost(cid: str | None) -> float | None:
        ent = _carrier_entity(cid)
        return _av(ent, "energy_carrier_cost") if ent else None

    def _carrier_co2(cid: str | None) -> float | None:
        ent = _carrier_entity(cid)
        return _av(ent, "co2_emission_intensity") if ent else None

    # ── Helpers: direct topology relations on assets ─────────────────────

    def _bus_from_asset(asset_id: str) -> str | None:
        """Read the direct atNode relation from an asset."""
        return _rel_target(_entity_by_id(model, asset_id), "atNode")

    def _nodes_from_branch(asset_id: str):
        """Return direct (fromNode, toNode) relations from a branch asset."""
        ent = _entity_by_id(model, asset_id)
        return _rel_target(ent, "fromNode"), _rel_target(ent, "toNode")

    map_busses: dict[int, dict] = {}

    # ── 1) ElectricalBus → PN_Busbar ──────────────────────────────────────────
    for bid, ent in bus_entities.items():
        uid  = node_uid_map[bid]
        data = getattr(ent, "data", {})

        region = None
        raw_loc = data.get("locatedIn")
        if isinstance(raw_loc, (list, tuple)):
            region = raw_loc[0] if raw_loc else None
        elif raw_loc:
            region = raw_loc

        bus_el: dict = {
            "class": "PN_Busbar",
            "uid":   uid,
            "name":  _av(ent, "name", bid),
            "Un":    _av(ent, "nominal_voltage", 0.0),
        }
        if region and region != "region_europe":
            bus_el["zone_name"] = region
            bus_el["country"]   = region
        lon = _av(ent, "longitude")
        lat = _av(ent, "latitude")
        if lon is not None:
            bus_el["longitude"] = lon
        if lat is not None:
            bus_el["latitude"] = lat

        map_busses[uid] = bus_el
        elements.append(bus_el)

    # ── 2a) TransmissionLine → PN_Line ────────────────────────────────────
    for eid, ent in line_ents.items():
        uid   = line_uid_map[eid]
        frm, to = _nodes_from_branch(eid)
        pf_ent = topo_ent = ent

        el = {
            "class":    "PN_Line",
            "uid":      uid,
            "name":     _av(ent, "name", eid),
            "bus1_uid": _bus_uid(frm),
            "bus2_uid": _bus_uid(to),
            "r":        _av(pf_ent,  "series_resistance_per_km",      0.0),
            "x":        _av(pf_ent,  "series_reactance_per_km",       0.1),
            "b":        _av(pf_ent,  "shunt_susceptance_per_km",      0.1),
            "Length":   _av(pf_ent,  "line_length",            1.0),
            "numparlines": _av(pf_ent, "parallel_circuit_count", 1),
            "side1_on": int(_av(topo_ent, "from_switch_closed",    1)),
            "side2_on": int(_av(topo_ent, "to_switch_closed",      1)),
            # Smax = corridor rating, NOT multiplied by numparlines
            "Smax":     (_av(pf_ent,  "thermal_capacity_rating") or 0.0),
        }
        elements.append(el)

    # ── 2b) TwoWindingPowerTransformer → PN_TR2 ───────────────────────────
    for eid, ent in tr2_ents.items():
        uid   = tr2_uid_map[eid]
        frm, to = _nodes_from_branch(eid)
        pf_ent = topo_ent = ent

        el = {
            "class":    "PN_TR2",
            "uid":      uid,
            "name":     _av(ent, "name", eid),
            "bus1_uid": _bus_uid(frm),
            "bus2_uid": _bus_uid(to),
            "side1_on": int(_av(topo_ent, "from_switch_closed", 1)),
            "side2_on": int(_av(topo_ent, "to_switch_closed",   1)),
            "numparlines": _av(pf_ent, "parallel_circuit_count", 1),
            "SR":   _av(pf_ent, "thermal_capacity_rating",    0.0),
            "UR1":  _av(pf_ent, "rated_primary_voltage",      0.0),
            "UR2":  _av(pf_ent, "rated_secondary_voltage",    0.0),
            "Smax": _av(pf_ent, "thermal_capacity_rating",    0.0),
            "Usc":  (_av(pf_ent, "short_circuit_voltage_in_percentage") or 10.0),  # default 10% when 0 or missing
        }
        elements.append(el)

    # ── 2c) HVDCLink → PN_HVDC ──────────────────────────────────────────
    for eid, ent in hvdc_ents.items():

        uid      = dc_uid_map[eid]
        frm, to  = _nodes_from_branch(eid)
        topo_ent = ent
        dv       = ent
        el = {
            "class":    "PN_HVDC",
            "uid":      uid,
            "name":     _av(ent, "name", eid),
            "bus1_uid": _bus_uid(frm),
            "bus2_uid": _bus_uid(to),
            "side1_on": int(_av(topo_ent, "from_switch_closed", 1)),
            "side2_on": int(_av(topo_ent, "to_switch_closed",   1)),
            "Pmax":     _av(dv, "max_flow", None),
        }
        elements.append(el)

    # ── 2d) NetTransferCapacity + TransmissionElement → PN_NTC ───────────
    for eid, ent in (ntc_ents | transmission_ents).items():
        uid = ntc_uid_map.get(eid) or trans_uid_map.get(eid)
        if uid is None:
            continue
        frm, to = _nodes_from_branch(eid)
        pf_ent = ent

        p12  = _av(pf_ent, "maximum_power_flow_from_to", None)
        p21  = _av(pf_ent, "maximum_power_flow_to_from", None)

        el = {
            "class":      "PN_NTC",
            "uid":        uid,
            "name":       _av(ent, "name", eid),
            "bus1_uid":   _bus_uid(frm),
            "bus2_uid":   _bus_uid(to),
            "P1max":      p12,
            "P2max":      p21,
            "technology": "NTC",
        }
        elements.append(el)

    # ── 3) DemandUnit → PN_Load / PN_LoadFlexible ────────────────────────
    for lid, ent in dem_ents.items():
        uid   = dem_uid_map[lid]
        dv    = ent
        bus_id = _bus_from_asset(lid)
        busuid = _bus_uid(bus_id)

        is_flex = _av(dv, "is_demand_flexible", False)

        if is_flex:
            load_el = {
                "class":       "PN_LoadFlexible",
                "uid":         uid,
                "name":        _av(ent, "name", lid),
                "busuid":      busuid,
                "profile_factor": _av(dv, "annual_energy_demand",       0.0),
                "u_load_c1":   _av(dv, "variable_operating_cost",       0.0),
                "w_c1":       -_av(dv, "value_of_lost_load",        10000.0),
                "xi_ref_profile": _rel_target(dv, "hasDemandProfile") or "",
                "profile_factor_type": _profile_factor_type(
                    model, _rel_target(dv, "hasDemandProfile")),
                "T0":          _av(dv, "flexibility_window_time_start",  0.0),
                "T1":          _av(dv, "flexibility_window_time_end",    0.0),
                "TP":          _av(dv, "flexibility_time_resolution",    0.0),
            }
        else:
            load_el = {
                "class":       "PN_Load",
                "uid":         uid,
                "name":        _av(ent, "name", lid),
                "busuid":      busuid,
                "w_c1":       -_av(dv, "value_of_lost_load",        10000.0),
                "profile_factor": _av(dv, "annual_energy_demand",       0.0),
                "xi_ref_profile": _rel_target(dv, "hasDemandProfile") or "",
                "profile_factor_type": _profile_factor_type(
                    model, _rel_target(dv, "hasDemandProfile")),
            }

        if _av(dv, "maximum_energy_demand") is not None:
            load_el["u_load_max"] = _av(dv, "maximum_energy_demand")

        if busuid and busuid in map_busses:
            load_el["country"] = map_busses[busuid].get("country", "")
        load_el["technology"] = _av(dv, "demand_type", "")

        if not load_el.get("xi_ref_profile"):
            print(f"Load {lid} has no profile reference — skipped")
            continue

        elements.append(load_el)

    # ── 4) StorageUnit → PN_StoragePumpNoInfeed / PN_StoragePump / PN_StorageDam
    #
    # Design principle (separation of concerns):
    #   ReservoirStorageUnit.asset  → reservoir-only: energy_storage_capacity,
    #                                   annual_natural_inflow_energy
    #   HydroGenerationUnit           → generator-only: nominal_power_capacity,
    #                                   turbine_efficiency, maximum_pumping_power,
    #                                   pumping_efficiency
    #
    # ReservoirStorageUnit is routed from model structure.  A linked reversible
    # HydroGenerationUnit / pump power indicates pumped hydro; natural inflow
    # then distinguishes open-loop from closed-loop.
    #
    exported_as_dam:           set[str] = set()
    exported_as_pump:          set[str] = set()
    exported_as_pump_noinfeed: set[str] = set()
    skipped_as_no_inflow_dam:  set[str] = set()

    for sid, ent in stor_ents.items():
        uid    = stor_uid_map[sid]
        # A ReservoirStorageUnit is never itself electrically connected --
        # only its paired HydroGenerationUnit is, via drawsFromReservoir --
        # so fall back to the bus reachable through that generator when the
        # reservoir may have no direct atNode relation of its own.
        bus_id = _bus_from_asset(sid)
        if bus_id is None:
            for _gid, _gent in (model.entities.get("HydroGenerationUnit") or {}).items():
                _gdraws = (getattr(_gent, "data", {}) or {}).get("drawsFromReservoir")
                _gdraws_list = _gdraws if isinstance(_gdraws, (list, tuple)) else [_gdraws]
                if sid in _gdraws_list:
                    bus_id = _bus_from_asset(_gid)
                    if bus_id is not None:
                        break
        busuid = _bus_uid(bus_id)

        # Operational storage data is stored directly on the asset.
        sv = ent

        # ── Resolve type entity
        tt_data = getattr(ent, "data", {})
        raw_tt  = tt_data.get("hasTechnology")
        tt_id   = (raw_tt[0] if isinstance(raw_tt, (list, tuple)) else raw_tt)
        tt_ent  = stor_type_ents.get(tt_id) if tt_id else None

        def _sv(name, default=None):
            """Resolve a storage value using the composed-schema storage order.

            Preferred lookup order:

            1. StorageUnit or ReservoirStorageUnit asset
            2. Referenced StorageType

            The second step is required for flattened schemas, imported YAML
            models, and aggregated models where dispatch-group attributes may
            be stored directly on the asset.
            """
            val = _av(ent, name)

            if val is None and tt_ent is not None:
                val = _av(tt_ent, name)

            return val if val is not None else default

        # ── Find paired HydroGenerationUnit (draws from this reservoir)
        _hydro_gen_dv = None
        for _gid, _gent in (model.entities.get("HydroGenerationUnit") or {}).items():
            _gdata = getattr(_gent, "data", {}) or {}
            _draws = _gdata.get("drawsFromReservoir")
            _draws_list = _draws if isinstance(_draws, (list, tuple)) else [_draws]
            if sid in _draws_list:
                _hydro_gen_dv = _gent
                break

        def _gv(name, default=None):
            """Get an operational value from the paired hydro generator asset."""
            val = _av(_hydro_gen_dv, name)
            return val if val is not None else default

        # ── Determine hydro/PHS routing from structure
        is_storage_dam_candidate = _is_flexeco_storage_dam_candidate(sid, ent, tt_id, sv)
        stor_carrier = ""
        stor_tech = str(_sv("storage_technology_type") or "").lower()
        if stor_tech:
            stor_carrier = stor_tech
        has_natural_inflow_flag = _sv("has_natural_inflow", False)
        if not stor_carrier and (raw_c := getattr(ent, "data", {}).get("storesCarrier")):
            raw_c = raw_c[0] if isinstance(raw_c, (list, tuple)) else raw_c
            oc_ent = _carrier_entity(raw_c)
            if oc_ent:
                raw_name = getattr(oc_ent, "data", {}).get("name") or str(raw_c)
                stor_carrier = str(raw_name.get("value", raw_name)
                                   if isinstance(raw_name, dict) else raw_name).lower()
        is_reversible_gen = False
        machine_role_gen = None
        if _hydro_gen_dv is not None:
            machine_role_gen = _gv("machine_role")
        if _hydro_gen_dv is not None:
            for _gid, _gent in (model.entities.get("HydroGenerationUnit") or {}).items():
                _gdata = getattr(_gent, "data", {}) or {}
                _draws = _gdata.get("drawsFromReservoir")
                _draws_list = _draws if isinstance(_draws, (list, tuple)) else [_draws]
                if sid in _draws_list:
                    is_reversible_gen = bool(_av(_gent, "is_reversible", False))
                    break
        is_hydro = (
            is_storage_dam_candidate
            or bool(has_natural_inflow_flag)
            or "hydro" in stor_carrier
            or "water" in stor_carrier
            or _hydro_gen_dv is not None
        )
        is_phs = (
            bool(_sv("has_active_charging", False))
            or machine_role_gen == "reversible"
            or is_reversible_gen
            or _gv("maximum_pumping_power") is not None
            or "phs" in stor_carrier
            or "pumped" in stor_carrier
            or "pumpedhydro" in str(tt_id or "").lower()
            or "pump_storage" in str(tt_id or "").lower()
        )
        has_active_charging_flag = is_phs

        # ── Power/efficiency: prefer the paired hydro generator, fall back to storage
        chg_eff  = _gv("pumping_efficiency")   or _sv("pumping_efficiency")  or _sv("charging_efficiency")
        dis_eff  = _gv("turbine_efficiency") or _gv("discharging_efficiency") or _sv("discharging_efficiency")
        voc      = _gv("variable_operating_cost") or _sv("variable_operating_cost")
        gen_max  = _gv("nominal_power_capacity")  or _sv("nominal_power_capacity") or 0.0
        load_max = _gv("maximum_pumping_power")   or _sv("maximum_pumping_power")  or _sv("maximum_charging_power") or 0.0
        chg_voc  = _sv("charging_variable_operating_cost", 0.0)

        # ── Inflow / capacity (always from reservoir sv)
        inflow    = _sv("annual_natural_inflow_energy")
        has_inflow = bool(inflow and inflow > 0.0)
        capacity  = _sv("energy_storage_capacity")

        if capacity is None:
            print(
                f"[WARN] Storage '{sid}' has no energy_storage_capacity in "
                "its asset entity or StorageType; "
                "FlexEco Capacity will be null."
            )

        # ── Branch: which FlexEco element?
        if is_hydro and has_inflow and has_active_charging_flag and chg_eff is not None:
            # ── PN_StoragePump: open-loop PHS with natural inflow
            exported_as_pump.add(sid)
            inflow_ref = _rel_target(sv, "hasNaturalInflowProfile")
            if not inflow_ref:
                print(f"[WARN] {sid} is open-loop PHS but has no hasNaturalInflowProfile — skipped")
                continue
            el = {
                "class":      "PN_StoragePump",
                "uid":        uid,
                "name":       _av(ent, "name", sid),
                "busuid":     busuid,
                "eta_gen":    dis_eff,
                "eta_load":   chg_eff,
                "u_gen_max":  gen_max,
                "u_load_max": load_max,
                "u_gen_c1":   voc if voc is not None else 0.0,
                "u_load_c1":  chg_voc,
                "Capacity":   capacity,
                "xi_ref_profile":     inflow_ref,
                "profile_factor":     inflow,
                "profile_factor_type": _profile_factor_type(model, inflow_ref),
                "has_inflow": True,
                "x_boundary_type": 2,
            }

        elif is_storage_dam_candidate and not has_inflow and not is_phs:
            # ── Reservoir without inflow (not PHS) — cannot be modelled in FlexEco
            skipped_as_no_inflow_dam.add(sid)
            print(f"[INFO] Reservoir/Pondage '{sid}' has no inflow data — "
                  f"skipped (neither PN_StorageDam nor PN_GenDispatchable).")
            continue

        elif is_storage_dam_candidate and has_inflow:
            # ── PN_StorageDam: reservoir hydro with natural inflow
            exported_as_dam.add(sid)
            inflow_ref = _rel_target(sv, "hasNaturalInflowProfile")
            el = {
                "class":      "PN_StorageDam",
                "uid":        uid,
                "name":       _av(ent, "name", sid),
                "busuid":     busuid,
                "eta_gen":    dis_eff,
                "u_gen_max":  gen_max,
                "u_gen_c1":   voc if voc is not None else 0.0,
                "Capacity":   capacity,
                "profile_factor": inflow,
                "has_inflow": True,
                "x_boundary_type": 2,
            }
            if inflow_ref:
                el["xi_ref_profile"]     = inflow_ref
                el["profile_factor_type"] = _profile_factor_type(model, inflow_ref)

        elif chg_eff is not None and chg_eff > 0.0:
            # ── PN_StoragePumpNoInfeed: closed-loop PHS or battery
            if is_phs:
                exported_as_pump_noinfeed.add(sid)
            el = {
                "class":      "PN_StoragePumpNoInfeed",
                "uid":        uid,
                "name":       _av(ent, "name", sid),
                "busuid":     busuid,
                "eta_gen":    dis_eff,
                "eta_load":   chg_eff,
                "u_gen_max":  gen_max,
                "u_load_max": load_max,
                "u_gen_c1":   voc if voc is not None else 0.0,
                "u_load_c1":  chg_voc,
                "Capacity":   capacity,
                "has_inflow": False,
                "x_boundary_type": 2,
            }

        else:
            continue  # No valid FlexEco mapping

        # ── Common post-processing
        # FlexECO storage elements are connected to the electricity bus and should
        # keep the same carrier/cost metadata as legacy exports.
        el["carrier"] = "carrier.electricity"
        c_cost_storage = _carrier_cost("carrier.electricity")
        if c_cost_storage is not None:
            el["xi_c1"] = c_cost_storage

        ramp_up = _gv("maximum_ramp_rate_up") or _sv("maximum_ramp_rate_up")
        ramp_dn = _gv("maximum_ramp_rate_down") or _sv("maximum_ramp_rate_down")
        if ramp_up is not None:
            el.update({"has_ramprate": True, "du_gen_up_max": ramp_up})
        if ramp_dn is not None:
            el.update({"has_ramprate": True, "du_gen_down_max": ramp_dn})
        if busuid and busuid in map_busses:
            el["country"] = map_busses[busuid].get("country", "")
        source_storage_technology = _sv("storage_technology_type")
        if source_storage_technology:
            el["technology"] = source_storage_technology
        elif tt_id:
            el["technology"] = tt_id

        elements.append(el)

    # ── 5) GenerationUnit → PN_GenDispatchable / PN_GenNonDispatchable ────
    for gid, ent in gen_ents.items():
        # Reservoir/Pondage hydro composites are exported through the storage
        # component as PN_StorageDam, matching the legacy FlexEco mapping.
        # Only skip the hydro generator if its reservoir was actually exported
        # as PN_StorageDam (i.e. had inflow data). Without an inflow-driven
        # dam export, the generator must appear as PN_GenDispatchable.
        raw_tt_skip = getattr(ent, "data", {}).get("hasTechnology")
        tt_id_skip = raw_tt_skip[0] if isinstance(raw_tt_skip, (list, tuple)) else raw_tt_skip
        ent_data = getattr(ent, "data", {})
        raw_draws = ent_data.get("drawsFromReservoir")
        draws_from_list = raw_draws if isinstance(raw_draws, (list, tuple)) else [raw_draws]
        draws_from_list = [d for d in draws_from_list if d is not None]
        # Skip generator if it is a reservoir/pondage hydro turbine whose
        # storage was exported as PN_StorageDam (generator implicit in dam)
        # A no-inflow reservoir is not exported as a storage dam; in that case
        # the generator must still be exported as PN_GenDispatchable.
        #
        # Detection is semantic (drawsFromReservoir + technology type), not
        # based on ID prefix — TYNDP produces "gen.hydro.tech.*" while
        # PyPSA produces "generator.hydro.*", so a prefix check would
        # silently skip TYNDP but pass PyPSA generators through.
        # A generator should be skipped when its reservoir was already exported
        # as a FlexEco storage element (PN_StorageDam, PN_StoragePump,
        # PN_StoragePumpNoInfeed) — the generator role is implicit in the
        # storage element and must not appear separately as PN_GenDispatchable.
        _is_hydro_gen_with_reservoir = (
            bool(draws_from_list)
            and (
                tt_id_skip in (
                    "Generation.Renewable.Hydro.Reservoir",
                    "Generation.Renewable.Hydro.Pondage",
                    "Generation.Renewable.Hydro.PHS.ClosedLoop",
                    "Generation.Renewable.Hydro.PHS.OpenLoop",
                )
                or "hydro" in str(gid).lower()
            )
        )
        if _is_hydro_gen_with_reservoir and any(
            d in exported_as_dam or d in exported_as_pump or d in exported_as_pump_noinfeed
            for d in draws_from_list
        ):
            continue

        uid   = gen_uid_map[gid]
        # Operational generation data is stored directly on the asset.
        gv = ent
        bus_id = _bus_from_asset(gid)
        busuid = _bus_uid(bus_id)

        # Resolve type-level attributes via hasTechnology → GeneratorType
        tt_data = getattr(ent, "data", {})
        raw_tt  = tt_data.get("hasTechnology")
        tt_id   = (raw_tt[0] if isinstance(raw_tt, (list, tuple)) else raw_tt)
        tt_ent  = gen_type_ents.get(tt_id) if tt_id else None

        def _gv(name, default=None):
            """Get from the generation asset, then fall back to GeneratorType."""
            val = _av(gv, name)
            if val is None and tt_ent is not None:
                val = _av(tt_ent, name)
            return val if val is not None else default

        # Input carrier/resource: prefer the concrete GenerationUnit relation.
        # GeneratorType is only a fallback for library defaults.
        carrier_id = _rel_target(ent, "hasInputCarrier")
        resource_id = _rel_target(ent, "hasInputResource")
        if carrier_id is None and tt_ent:
            raw_c = getattr(tt_ent, "data", {}).get("hasInputCarrier")
            carrier_id = (raw_c[0] if isinstance(raw_c, (list, tuple)) else raw_c)

        resource_to_flexeco_carrier = {
            "resource.renewable.wind": "carrier.resource.renewable.wind",
            "resource.renewable.solar": "carrier.resource.renewable.solar",
            "resource.water": "carrier.resource.water",
        }

        # Efficiency semantics depend on the concrete generation asset.
        # PyPSA imports often do not create hasTechnology GeneratorType objects;
        # relying only on tt_id therefore made Wind/Solar/Generic generators get
        # eff=None and be silently skipped below.  Resolve from the concrete asset
        # first, then fall back to GeneratorType labels.
        ent_cls = _entity_class_name(model, gid)
        gen_label = " ".join(str(x or "") for x in (gid, tt_id, ent_cls)).lower()
        if ent_cls == "HydroGenerationUnit":
            eff = _gv("turbine_efficiency", 1.0)
        else:
            # GenerationUnit is technology-neutral. Preserve an explicitly
            # imported conversion efficiency for thermal, nuclear, hydrogen,
            # wind and solar alike; use 1.0 only when no value exists.
            eff = _gv("energy_conversion_efficiency", 1.0)
        cap        = _gv("nominal_power_capacity",  0.0)
        voc        = _gv("variable_operating_cost")
        # Annual potential and profile relations live directly on the generator.
        annual_res = _gv("annual_resource_potential")
        prof_ref   = _rel_target(ent, "hasAvailabilityProfile") or _rel_target(ent, "hasRunOfRiverInflowProfile")
        ramp_up    = _gv("maximum_ramp_rate_up")
        ramp_dn    = _gv("maximum_ramp_rate_down")
        ramp_c_up  = _gv("ramping_cost_increase")
        ramp_c_dn  = _gv("ramping_cost_decrease")

        # A generator is non-dispatchable only when it explicitly says so,
        # or when it has a resource profile. Annual resource potential alone
        # is not enough: reservoir/pondage hydro composites may carry an
        # annual potential but are dispatchable and storage/inflow-driven.
        dispatch_type = str(_gv("dispatch_type", "") or "").lower()
        has_resource_profile = bool(prof_ref)
        is_reservoir_hydro = (
            tt_id == "Generation.Renewable.Hydro.Reservoir"
            or "pondage" in gid.lower()
            or "reservoir" in gid.lower()
        )
        is_nondisp = (
            (dispatch_type == "nondispatchable" or has_resource_profile)
            and not is_reservoir_hydro
        )
        cls_name   = "PN_GenNonDispatchable" if is_nondisp else "PN_GenDispatchable"

        el: dict = {
            "class":    cls_name,
            "uid":      uid,
            "name":     _av(ent, "name", gid),
            "busuid":   busuid,
            "eta_gen":  eff,
            "u_gen_max": cap,
            "u_gen_c1":  voc if voc is not None else 0.0,
        }

        if eff is None:
            eff = 1.0

        if is_nondisp:
            if not prof_ref:
                print(f"[WARN] PN_GenNonDispatchable '{gid}' skipped — "
                      f"no availability/run-of-river profile on generator '{gid}'.")
                continue
            # annual_res may be 0.0 (valid for unbuilt capacity) — store as-is
            el["profile_factor"] = float(annual_res) if annual_res is not None else 0.0
            el["xi_ref_profile"] = prof_ref
            el["profile_factor_type"] = _profile_factor_type(model, prof_ref)

        if carrier_id:
            el["carrier"] = _carrier_name(carrier_id)
        elif resource_id:
            mapped_resource = resource_to_flexeco_carrier.get(resource_id)
            if mapped_resource:
                el["carrier"] = mapped_resource

        # Carrier price is canonical data of EnergyCarrier. Natural resources
        # have no EnergyCarrier entity and therefore export a zero xi_c1.
        c_cost = _carrier_cost(carrier_id)
        if c_cost is None and resource_id:
            c_cost = 0.0
        c_co2  = _carrier_co2(carrier_id)
        if c_cost is not None:
            el["xi_c1"] = c_cost
        if c_co2 is not None and c_co2 > 0.0:
            el["has_co2"] = True
            el["MWh_to_tons_co2"] = c_co2
            for _, esm_ent in esm_ents.items():
                el["co2_c1"] = float(_av(esm_ent, "co2_price", 0.0))

        if ramp_up is not None:
            el.update({"has_ramprate": True, "du_gen_up_max": ramp_up})
        if ramp_c_up is not None:
            el.update({"has_ramprate": True, "du_gen_up_c1": ramp_c_up})
        # Preserve down-ramp independently.  If a dispatchable thermal/nuclear
        # source only provided a symmetric up-ramp, export the same value as
        # down-ramp so FlexECO does not silently lose the constraint.
        if ramp_dn is None and ramp_up is not None and tt_id and ("Nuclear" in tt_id or "Thermal" in tt_id):
            ramp_dn = ramp_up
        if ramp_dn is not None:
            el.update({"has_ramprate": True, "du_gen_down_max": ramp_dn})
        if ramp_c_dn is not None:
            el.update({"has_ramprate": True, "du_gen_down_c1": ramp_c_dn})

        if busuid and busuid in map_busses:
            el["country"] = map_busses[busuid].get("country", "")
        source_technology = _gv("generator_technology_type")
        if source_technology:
            el["technology"] = source_technology
        elif tt_id:
            el["technology"] = tt_id

        elements.append(el)

    # ── 6) Write JSON ────────────────────────────────────────────────────
    jpn = {
        "PowerSystemElements": elements,
        "TIMEEND":      8760,
        "TIMESTART":    1,
        "ExportProblem": 0,
        "baseMVA":      1,
    }
    with output_path.open("w") as f:
        json.dump(jpn, f, indent=2, sort_keys=True)

    # ── 7) Optionally write profile payloads to HDF5 ─────────────────────
    if hdf5_path is not None:
        _export_profiles_hdf5(model, hdf5_path)

    # Return uid maps so callers can reverse-look up UID → CESDM entity id
    # when importing FlexEco dispatch results.
    return {
        "id_to_uid":    id_to_uid,           # {cesdm_entity_id → flexeco_uid}
        "uid_to_id":    {v: k for k, v in id_to_uid.items()},
        "node_uid_map": node_uid_map,         # {bus_eid      → uid}
        "gen_uid_map":  gen_uid_map,          # {gen_eid      → uid}
        "stor_uid_map": stor_uid_map,         # {storage_eid  → uid}
        "dem_uid_map":  dem_uid_map,          # {demand_eid   → uid}
        "ntc_uid_map":  ntc_uid_map,          # {ntc_eid      → uid}
        "line_uid_map": line_uid_map,         # {line_eid     → uid}
        "tr2_uid_map":  tr2_uid_map,          # {trafo_eid    → uid}
        "dc_uid_map":   dc_uid_map,           # {hvdc_eid     → uid}
    }

# ===========================================================================
# import_from_flexeco
# ===========================================================================

def _set_profile_type_from_factor(model, prof_id: str | None,
                                   factor_type: int | None) -> None:
    """
    Set profile_type on a Profile entity based on FlexEco profile_factor_type.

    profile_factor_type mapping:
      0 → as_SI                       (absolute SI unit values)
      1 → as_normalized_annual_energy (values sum to 1 over the year)
      2 → as_capacity_factor          (dimensionless [0,1])
    """
    if not prof_id or factor_type is None:
        return
    profile_type = _FACTOR_TYPE_TO_PROFILE_TYPE.get(int(factor_type))
    if profile_type is None:
        return
    prof_ent = model.entities.get("Profile", {}).get(prof_id)
    if prof_ent is not None:
        model.add_attribute(prof_id, "profile_type", profile_type)

def import_from_flexeco(
    schema_dir: str | Path,
    european_json: str | Path,
) -> tuple[dict, CesdmModel]:
    """
    Build a CESDM V4 model from a FlexEco .jpn JSON file.

    ----------------
    - ElectricityNode / EnergyNode → ElectricalBus
    - EnergyDomain               → CarrierDomain
    - isInEnergyDomain            → belongsToCarrierDomain
    - isInGeographicalRegion      → locatedIn
    - hasGeographicalRegionAsParent → isSubRegionOf
    - hasEnergyCarrier            → hasCarrier
    - EnergyConversionTechnology1x1 → GenerationUnit
      + GenerationUnit (operational attributes)
    - instanceOf                → hasTechnology
    - hasInputEnergyCarrier     → hasInputCarrier  (on GeneratorType)
    - hasOutputEnergyCarrier    → hasOutputCarrier (on GeneratorType)
    - carrier attribute on EnergyCarrier: energy_carrier_type removed
      (use carrier_type / carrier_group instead)

    Returns
    -------
    (data_profiles, model)
      data_profiles : dict[str, np.ndarray] of loaded profile arrays
      model         : populated CesdmModel instance
    """
    schema_dir    = Path(schema_dir)
    european_json = Path(european_json)

    model: CesdmModel = build_model_from_yaml(schema_dir)

    # ── Base entities ─────────────────────────────────────────────────────

    model.add_entity("EnergySystemModel", "EnergySystemModel")

    # CarrierDomain (electricity)
    model.add_entity("CarrierDomain", _DOMAIN_ID)
    model.add_attribute(_DOMAIN_ID, "name", "electricity")
    model.add_relation(_DOMAIN_ID, "hasCarrier", _CARRIER_ID)

    # EnergyCarrier (electricity)
    model.add_entity("EnergyCarrier", _CARRIER_ID)
    model.add_attribute(_CARRIER_ID, "name",                 "electricity")
    model.add_attribute(_CARRIER_ID, "co2_emission_intensity", 0.0)
    model.add_attribute(_CARRIER_ID, "energy_carrier_cost",    0.0)

    # ── FlexEco carrier → CESDM carrier id map ─────────────────────────────
    _FC_MAP: dict[str, str] = {
        "coal":             "c_coal",
        "gas":              "c_gas",
        "Gas":              "c_gas",
        "lignite":          "c_lignite",
        "nuclear":          "c_nuclear",
        "oil":              "c_oil",
        "PHS":              "c_water",
        "CHP":              "c_gas",
        "hydro":            "c_water",
        "water":            "c_water",
        "load":             "carrier.electricity",
        "ror":              "c_water",
        "otherRES":         "c_others_renewable",
        "battery":          "carrier.electricity",
        "dsr":              "carrier.electricity",
        "solar":            "c_pv",
        "pv":               "c_pv",
        "wind":             "c_wind",
        "electricity":      "carrier.electricity",
        "others_renewable": "c_others_renewable",
    }
    _TECH_CARRIER_MAP: dict[str, str] = {}

    def _ensure_carrier(cid: str, name: str, carrier_type: str = "FUEL",
                        cost: float | None = None, co2: float | None = None) -> None:
        if cid and cid not in model.entities.get("EnergyCarrier", {}):
            model.add_entity("EnergyCarrier", cid)
        if cid:
            _safe_attr(cid, "name", name)
            if cost is not None:
                _safe_attr(cid, "energy_carrier_cost", cost)
            if co2 is not None:
                _safe_attr(cid, "co2_emission_intensity", co2)

    def _safe_attr(entity_id: str, attr: str, value, unit: str | None = None) -> None:
        if value is None:
            return
        try:
            if unit is None:
                model.add_attribute(entity_id, attr, value)
            else:
                model.add_attribute(entity_id, attr, value, unit=unit)
        except KeyError:
            # Importer is intentionally schema-tolerant across recent CESDM
            # refactorings. Unsupported legacy attributes are skipped rather
            # than written to the wrong asset.
            return

    def _safe_rel(entity_id: str, rel: str, target: str | None) -> None:
        if not target:
            return
        try:
            model.add_relation(entity_id, rel, target)
        except KeyError:
            return

    def _ensure_resource(rid: str, name: str | None = None) -> None:
        if rid and rid not in model.entities.get("NaturalResource", {}):
            model.add_entity("NaturalResource", rid)
        if rid:
            _safe_attr(rid, "name", name or rid)

    def _ensure_generator_type(tid: str | None) -> None:
        if not tid:
            return
        if tid not in model.entities.get("GeneratorType", {}):
            model.add_entity("GeneratorType", tid)
        _safe_attr(tid, "name", tid)

    def _ensure_storage_type(tid: str | None) -> None:
        if not tid:
            return
        if tid not in model.entities.get("StorageType", {}):
            model.add_entity("StorageType", tid)
        _safe_attr(tid, "name", tid)

    def _ensure_timestamp_series(ts_id: str = "timestamps.hourly_8760") -> None:
        if ts_id not in model.entities.get("TimestampSeries", {}):
            model.add_entity("TimestampSeries", ts_id)
        _safe_attr(ts_id, "name", ts_id)
        _safe_attr(ts_id, "start_datetime", "2020-01-01T00:00:00Z")
        _safe_attr(ts_id, "resolution", "PT1H")
        _safe_attr(ts_id, "length", 8760)
        _safe_attr(ts_id, "timezone", "UTC")

    def _ensure_profile(pid: str | None) -> None:
        if not pid:
            return
        if pid not in model.entities.get("Profile", {}):
            model.add_entity("Profile", pid)
        _safe_attr(pid, "name", pid)
        _safe_attr(pid, "profile_type", "as_normalized_annual_energy")
        _safe_attr(pid, "data_reference", f"/profiles/{pid}/values")
        _ensure_timestamp_series()
        _safe_rel(pid, "hasTimestampSeries", "timestamps.hourly_8760")

    def _carrier_or_resource_from_flexeco(el: dict) -> tuple[str | None, str | None]:
        """Return (energy_carrier_id, natural_resource_id) for a FlexECO element."""
        key = _technology_key_from_flexeco(el)
        carrier = str(el.get("carrier", "")).strip().lower()
        if any(x in key for x in ("wind",)) or carrier in ("wind", "c_wind"):
            return None, "resource.renewable.wind"
        if any(x in key for x in ("solar", "pv", "photovoltaic", "csp")) or carrier in ("solar", "pv", "c_pv"):
            return None, "resource.renewable.solar"
        if "hydrogen" in key or carrier in ("hydrogen", "c_hydrogen"):
            return "carrier.hydrogen", None
        if any(x in key for x in ("hydro", "reservoir", "pondage", "run_of_river", "pump_storage", "phs")) or carrier in ("water", "hydro", "ror", "phs", "c_water"):
            return None, "resource.water"
        if carrier in _FC_MAP:
            cid = _FC_MAP[el["carrier"]].lower()
            if cid in ("c_water", "c_wind", "c_pv"):
                return None, {"c_water": "resource.water", "c_wind": "resource.renewable.wind", "c_pv": "resource.renewable.solar"}[cid]
            return cid, None
        if "technology" in el:
            cid = _TECH_CARRIER_MAP.get(str(el["technology"]).lower())
            if cid in ("c_water", "c_wind", "c_pv"):
                return None, {"c_water": "resource.water", "c_wind": "resource.renewable.wind", "c_pv": "resource.renewable.solar"}[cid]
            return cid, None
        return None, None

    # Seed common natural resources used by FlexECO renewable/hydro mappings.
    for _rid, _name in (
        ("resource.water", "water"),
        ("resource.renewable.wind", "wind"),
        ("resource.renewable.solar", "solar irradiation"),
    ):
        _ensure_resource(_rid, _name)

    # ── Load JSON ─────────────────────────────────────────────────────────
    with european_json.open() as f:
        data = json.load(f)
    elements = data["PowerSystemElements"]

    data_profiles: dict[str, np.ndarray] = {}
    mat_data = None

    # ── Pre-pass: resolve carrier ids from generator/storage elements ─────
    for el in elements:
        if el.get("class") not in ("PN_GenDispatchable", "PN_GenNonDispatchable",
                                   "PN_StorageDam", "PN_StoragePump",
                                   "PN_StoragePumpNoInfeed"):
            continue
        carrier_id = None
        if "carrier" in el and el["carrier"] in _FC_MAP:
            carrier_id = _FC_MAP[el["carrier"]].lower()
        elif "technology" in el:
            tech = el["technology"].lower()
            for kw, cid in [
                ("hard coal",            "c_hard_coal"),
                ("lignite",              "c_lignite"),
                ("biofuel",              "c_biofuel"),
                ("waste",                "c_biofuel"),
                ("heavy_oil",            "c_heavy_oil"),
                ("gas",                  "c_gas"),
                ("oil_shale",            "c_shale_oil"),
                ("light_oil",            "c_light_oil"),
                ("oil",                  "c_oil"),
                ("pv",                   "c_pv"),
                ("solar_photovoltaic",   "c_pv"),
                ("solar_thermal",        "c_pv"),
                ("wind",                 "c_wind"),
                ("nuclear",              "c_nuclear"),
                ("hydrogen",             "c_hydrogen"),
                ("reservoir",            "c_water"),
                ("run_of_river",         "c_water"),
                ("pump_storage",         "c_water"),
                ("hydro",                "c_water"),
                ("pondage",              "c_water"),
                ("others_renewable",     "c_others_renewable"),
                ("others_non_renewable", "c_others_non_renewable"),
                ("battery_storage",      "carrier.electricity"),
                ("demand_side_response", "carrier.electricity"),
                ("adequacy",             "carrier.electricity"),
                ("geothermal",           "c_geothermal"),
            ]:
                if kw in tech:
                    carrier_id = cid
                    break

        if carrier_id:
            carrier_id = carrier_id.lower()
            # Wind, solar and water are NaturalResource concepts after the
            # Carrier/Resource split. Keep any legacy c_* token out of
            # EnergyCarrier to avoid accidental hasInputCarrier/storesCarrier
            # validation errors downstream.
            if carrier_id in ("c_water", "c_wind", "c_pv"):
                _ensure_resource({"c_water": "resource.water", "c_wind": "resource.renewable.wind", "c_pv": "resource.renewable.solar"}[carrier_id])
                if "technology" in el:
                    _TECH_CARRIER_MAP[el["technology"].lower()] = carrier_id
                continue
            name = carrier_id[2:] if carrier_id.startswith("c_") else carrier_id
            cost = el.get("xi_c1")
            co2  = el.get("MWh_to_tons_co2")
            _ensure_carrier(carrier_id, name, cost=cost, co2=co2)
            if "has_co2" in el and el["has_co2"]:
                _safe_attr("EnergySystemModel", "co2_price", el.get("co2_c1", 0.0))
            if "technology" in el:
                _TECH_CARRIER_MAP[el["technology"].lower()] = carrier_id

    # ── Pass 1: Regions ───────────────────────────────────────────────────
    for el in elements:
        if el.get("class") != "PN_Busbar":
            continue
        region     = el.get("zone_name") or el.get("country") or "region_europe"
        subregion  = el.get("nuts2_id")

        if region not in model.entities.get("GeographicalRegion", {}):
            model.add_entity("GeographicalRegion", region)
            model.add_attribute(region, "name", region)

        if subregion and subregion not in model.entities.get("GeographicalRegion", {}):
            model.add_entity("GeographicalRegion", subregion)
            model.add_attribute(subregion, "name", subregion)
            model.add_relation(subregion, "isSubRegionOf", region)

    # ── Pass 2: ElectricalBus (was ElectricityNode) ───────────────────────────
    bus_uid_to_id: dict[int, str] = {}
    for el in elements:
        if el.get("class") != "PN_Busbar":
            continue
        uid    = el["uid"]
        bus_id = f"node_{uid}"
        region = el.get("zone_name") or el.get("country") or "region_europe"

        model.add_entity("ElectricalBus", bus_id)
        model.add_attribute(bus_id, "name",            el.get("name"))
        model.add_attribute(bus_id, "nominal_voltage",  el.get("Un"))
        model.add_relation(bus_id, "belongsToCarrierDomain", _DOMAIN_ID)
        model.add_relation(bus_id, "locatedIn",               region)

        bus_uid_to_id[uid] = bus_id

    def _node_id(bus_uid: int | str) -> str:
        return bus_uid_to_id.get(int(bus_uid), f"node_{bus_uid}")

    # ── Pass 3: Transmission, Loads, Generators, Storage ─────────────────
    for el in elements:
        cls = el.get("class")

        # ── Transmission ────────────────────────────────────────────────
        if cls in ("PN_Line", "PN_TR2", "PN_HVDC", "PN_NTC"):
            uid    = el["uid"]
            frm_id = _node_id(el["bus1_uid"])
            to_id  = _node_id(el["bus2_uid"])

            if cls == "PN_Line":
                eid = f"line_{uid}"
                model.add_entity("TransmissionLine", eid)
                model.add_attribute(eid, "name", el.get("name"))
                frm_id = bus_uid_to_id.get(int(el["bus1_uid"]))
                to_id  = bus_uid_to_id.get(int(el["bus2_uid"]))
                _connect_branch(model, eid, frm_id, to_id)
                tv = eid
                model.add_attribute(tv, "from_switch_closed", el.get("side1_on", 1))
                model.add_attribute(tv, "to_switch_closed",   el.get("side2_on", 1))
                pv = eid
                model.add_attribute(pv, "series_resistance_per_km",       el.get("r",      0.0))
                model.add_attribute(pv, "series_reactance_per_km",        el.get("x",      0.1))
                model.add_attribute(pv, "shunt_susceptance_per_km",       el.get("b",      0.1))
                model.add_attribute(pv, "line_length",             el.get("Length", 1.0))
                model.add_attribute(pv, "thermal_capacity_rating", el.get("Smax",   0.0))

            elif cls == "PN_TR2":
                eid = f"tr2_{uid}"
                model.add_entity("Transformer", eid)
                model.add_attribute(eid, "name", el.get("name"))
                _connect_branch(model, eid, frm_id, to_id)
                tv = eid
                model.add_attribute(tv, "from_switch_closed", el.get("side1_on", 1))
                model.add_attribute(tv, "to_switch_closed",   el.get("side2_on", 1))
                pv = eid
                model.add_attribute(pv, "thermal_capacity_rating",   el.get("SR",  0.0))
                model.add_attribute(pv, "rated_primary_voltage",     el.get("UR1", 0.0))
                model.add_attribute(pv, "rated_secondary_voltage",   el.get("UR2", 0.0))
                model.add_attribute(pv, "short_circuit_voltage_in_percentage",     el.get("Usc", 0.0))

            elif cls == "PN_HVDC":
                eid = f"hvdc_{uid}"
                model.add_entity("HVDCLink", eid)
                model.add_attribute(eid, "name", el.get("name"))
                _connect_branch(model, eid, frm_id, to_id)
                # HVDC operational parameters are stored directly on HVDCLink.
                if el.get("Pmax") is not None:
                    model.add_attribute(eid, "p_max_hvdc", el["Pmax"])
                if el.get("Pmin") is not None:
                    model.add_attribute(eid, "p_min_hvdc", el["Pmin"])

            elif cls == "PN_NTC":
                eid = f"ntc_{uid}"
                model.add_entity("Interconnector", eid)
                model.add_attribute(eid, "name", el.get("name"))
                _connect_branch(model, eid, frm_id, to_id)
                pv = eid
                if el.get("P1max") is not None:
                    model.add_attribute(pv, "maximum_power_flow_from_to", el["P1max"])
                    model.add_attribute(pv, "maximum_power_flow_to_from",
                                        el.get("P2max", el["P1max"]))

        # ── Demand ──────────────────────────────────────────────────────
        elif cls in ("PN_Load", "PN_LoadFlexible"):
            uid    = el["uid"]
            dem_id = f"load_{uid}"
            bus_id = _node_id(el["busuid"])

            model.add_entity("DemandUnit", dem_id)
            model.add_attribute(dem_id, "name", el.get("name"))
            _connect_to_node(model, dem_id, bus_id)
            dv = dem_id
            model.add_attribute(dv, "annual_energy_demand",
                                el.get("profile_factor", 0.0))
            model.add_relation(dv, "hasDemandProfile", el.get("xi_ref_profile", ""))
            _set_profile_type_from_factor(model, el.get("xi_ref_profile"),
                                          el.get("profile_factor_type"))
            model.add_attribute(dv, "value_of_lost_load",
                                -el.get("w_c1", -10000.0))
            model.add_attribute(dv, "variable_operating_cost",
                                el.get("u_load_c1", 0.0))
            if el.get("technology") is not None:
                model.add_attribute(dv, "demand_type", el.get("technology"))
            if el.get("u_load_max") is not None:
                model.add_attribute(dv, "maximum_energy_demand",
                                    el["u_load_max"])

            if cls == "PN_LoadFlexible":
                model.add_attribute(dv, "is_demand_flexible",          True)
                model.add_attribute(dv, "flexibility_window_time_start",
                                    el.get("T0", 0.0))
                model.add_attribute(dv, "flexibility_window_time_end",
                                    el.get("T1", 0.0))
                model.add_attribute(dv, "flexibility_time_resolution",
                                    el.get("TP", 0.0))

            # Profile
            ts_key  = el.get("xi_ref_profile", "")
            ds_main = f"DemandUnit/{dem_id}/profile"
            ret, arr, mat_data = add_profile(el, 1, mat_data)
            if ret:
                data_profiles[ds_main] = arr
                if ts_key:
                    data_profiles[f"profiles/{ts_key}"] = arr

        # ── Storage / hydro reservoirs ─────────────────────────────────
        elif cls in ("PN_StoragePumpNoInfeed", "PN_StoragePump", "PN_StorageDam"):
            uid    = el["uid"]
            prefix = ("storage_pump_" if cls != "PN_StorageDam" else "storage_dam_")
            sid    = f"{prefix}{uid}"
            bus_id = _node_id(el["busuid"])

            stor_cls = _storage_asset_class_from_flexeco(cls, el)
            model.add_entity(stor_cls, sid)
            _safe_attr(sid, "name", el.get("name"))

            # Hydro storage is a NaturalResource store. Generic/battery storage
            # stores an EnergyCarrier.  This is the inverse import-side version
            # of the CESDM→FlexECO exporter mapping.
            is_hydro_res = (stor_cls == "ReservoirStorageUnit")
            carrier_id, resource_id = _carrier_or_resource_from_flexeco(el)
            if is_hydro_res:
                resource_id = resource_id or "resource.water"
                _ensure_resource(resource_id)
                _safe_rel(sid, "storesResource", resource_id)
            elif carrier_id:
                _ensure_carrier(carrier_id, carrier_id[2:] if carrier_id.startswith("c_") else carrier_id)
                _safe_rel(sid, "storesCarrier", carrier_id)
            else:
                _safe_rel(sid, "storesCarrier", _CARRIER_ID)

            # Storage technology type. For hydro, the reservoir has a storage
            # technology and the paired HydroGenerationUnit has the generation
            # technology.
            if cls == "PN_StoragePump":
                storage_tech = "Storage.Hydro.PumpedStorage.OpenLoopReservoir"
                hydro_tech = "Generation.Renewable.Hydro.PHS.OpenLoop"
            elif cls == "PN_StoragePumpNoInfeed":
                storage_tech = "Storage.Hydro.PumpedStorage.ClosedLoopReservoir"
                hydro_tech = "Generation.Renewable.Hydro.PHS.ClosedLoop"
            elif "pondage" in _technology_key_from_flexeco(el):
                storage_tech = "Storage.Hydro.PondageReservoir"
                hydro_tech = "Generation.Renewable.Hydro.Pondage"
            else:
                storage_tech = "Storage.Hydro.Reservoir"
                hydro_tech = "Generation.Renewable.Hydro.Reservoir"
            if is_hydro_res:
                _ensure_storage_type(storage_tech)
                _safe_rel(sid, "hasTechnology", storage_tech)

            _connect_to_node(model, sid, bus_id)
            sv = sid
            if el.get("technology") is not None:
                _safe_attr(sv, "storage_technology_type", el.get("technology"))
            if el.get("xi_c1") is not None:
                _safe_attr(_CARRIER_ID, "energy_carrier_cost", el.get("xi_c1"))

            if is_hydro_res:
                _safe_attr(sv, "energy_storage_capacity", el.get("Capacity", 0.0))

                # FlexECO hydro storage elements combine water body and power
                # conversion. CESDM separates them, so create the paired
                # HydroGenerationUnit for PN_StorageDam and PHS alike.
                gen_id = f"generator.hydro.{sid}"
                if gen_id not in model.entities.get("HydroGenerationUnit", {}):
                    model.add_entity("HydroGenerationUnit", gen_id)
                    _safe_attr(gen_id, "name", f"hydro generation for {sid}")
                    if cls in ("PN_StoragePump", "PN_StoragePumpNoInfeed"):
                        _safe_attr(gen_id, "turbine_type", "reversible_francis")
                    _ensure_generator_type(hydro_tech)
                    _safe_rel(gen_id, "hasTechnology", hydro_tech)
                    _safe_rel(gen_id, "hasInputResource", "resource.water")
                    _safe_rel(gen_id, "hasOutputCarrier", _CARRIER_ID)
                    _safe_rel(gen_id, "drawsFromReservoir", sid)
                    _safe_rel(sid, "suppliesResourceTo", gen_id)
                    _connect_to_node(model, gen_id, bus_id)

                gv = gen_id
                _safe_attr(gv, "machine_role", hydro_machine_role(hydro_tech))
                _safe_attr(gv, "dispatch_type", "dispatchable")
                _safe_attr(gv, "nominal_power_capacity", el.get("u_gen_max", 0.0))
                _safe_attr(gv, "turbine_efficiency", el.get("eta_gen", 0.90))
                if cls in ("PN_StoragePump", "PN_StoragePumpNoInfeed"):
                    _safe_attr(gv, "maximum_pumping_power", el.get("u_load_max", 0.0))
                    _safe_attr(gv, "pumping_efficiency", el.get("eta_load", 0.82))
                if el.get("u_gen_c1") is not None:
                    _safe_attr(gv, "variable_operating_cost", el.get("u_gen_c1", 0.0))
            else:
                _safe_attr(sv, "charging_efficiency", el.get("eta_load", 1.0))
                _safe_attr(sv, "discharging_efficiency", el.get("eta_gen", 1.0))
                _safe_attr(sv, "nominal_power_capacity", el.get("u_gen_max", 0.0))
                _safe_attr(sv, "maximum_charging_power", el.get("u_load_max", 0.0))
                _safe_attr(sv, "variable_operating_cost", el.get("u_gen_c1", 0.0))
                _safe_attr(sv, "charging_variable_operating_cost", el.get("u_load_c1", 0.0))
                _safe_attr(sv, "energy_storage_capacity", el.get("Capacity", 0.0))

            # Natural inflow profile: only attach relation if FlexECO supplies a
            # concrete profile id. Closed-loop PHS remains valid with no inflow.
            ts_key = el.get("xi_ref_profile", "")
            if is_hydro_res and (el.get("has_inflow") or cls == "PN_StorageDam" or ts_key):
                if ts_key:
                    _ensure_profile(ts_key)
                    _safe_rel(sv, "hasNaturalInflowProfile", ts_key)
                    _set_profile_type_from_factor(model, ts_key, el.get("profile_factor_type"))
                inflow = el.get("profile_factor", 0.0)
                _safe_attr(sv, "annual_natural_inflow_energy", inflow)
                # _safe_attr(sv, "annual_natural_inflow_energy", inflow)
                ret, arr, mat_data = add_profile(el, 1, mat_data)
                if ret:
                    data_profiles[f"StorageUnit/{sid}/inflow"] = arr
                    if ts_key:
                        data_profiles[f"profiles/{ts_key}"] = arr

            if el.get("du_gen_up_max") is not None:
                _safe_attr(sv, "maximum_ramp_rate_up", el["du_gen_up_max"])
            if el.get("du_gen_down_max") is not None:
                _safe_attr(sv, "maximum_ramp_rate_down", el.get("du_gen_down_max"))
            if el.get("du_gen_up_c1") is not None:
                _safe_attr(sv, "ramping_cost_increase", el.get("du_gen_up_c1"))
            if el.get("du_gen_down_c1") is not None:
                _safe_attr(sv, "ramping_cost_decrease", el.get("du_gen_down_c1"))

        # ── Generators ──────────────────────────────────────────────────
        elif cls in ("PN_GenDispatchable", "PN_GenNonDispatchable"):
            uid    = el["uid"]
            gid    = f"gen_{uid}"
            bus_id = _node_id(el["busuid"])

            gen_cls = _generation_asset_class_from_flexeco(el)
            model.add_entity(gen_cls, gid)
            _safe_attr(gid, "name", el.get("name"))
            tech_id = el.get("technology")
            if tech_id:
                _ensure_generator_type(tech_id)
                _safe_rel(gid, "hasTechnology", tech_id)
            carrier_id, resource_id = _carrier_or_resource_from_flexeco(el)
            if resource_id:
                _ensure_resource(resource_id)
                _safe_rel(gid, "hasInputResource", resource_id)
            elif carrier_id:
                _ensure_carrier(carrier_id, carrier_id[2:] if carrier_id.startswith("c_") else carrier_id)
                _safe_rel(gid, "hasInputCarrier", carrier_id)
            _safe_rel(gid, "hasOutputCarrier", _CARRIER_ID)

            _connect_to_node(model, gid, bus_id)
            gv = gid
            if gen_cls == "HydroGenerationUnit":
                _safe_attr(gv, "machine_role", hydro_machine_role(tech_id or el.get("name")))
                _safe_attr(gv, "turbine_efficiency", el.get("eta_gen", 1.0))
            else:
                _safe_attr(
                    gv,
                    "energy_conversion_efficiency",
                    hydrogen_generation_efficiency(
                        el.get("carrier"), tech_id, el.get("eta_gen", 1.0)
                    ),
                )
            if tech_id:
                _safe_attr(gv, "generator_technology_type", tech_id)
            if el.get("xi_c1") is not None and carrier_id:
                _safe_attr(carrier_id, "energy_carrier_cost", el.get("xi_c1"))
            _safe_attr(gv, "nominal_power_capacity", el.get("u_gen_max", 0.0))
            _safe_attr(gv, "variable_operating_cost", el.get("u_gen_c1", 0.0))

            if el.get("du_gen_up_max") is not None:
                _safe_attr(gv, "maximum_ramp_rate_up", el["du_gen_up_max"])
            if el.get("du_gen_down_max") is not None:
                _safe_attr(gv, "maximum_ramp_rate_down", el.get("du_gen_down_max"))
            if el.get("du_gen_up_c1") is not None:
                _safe_attr(gv, "ramping_cost_increase", el.get("du_gen_up_c1"))
            if el.get("du_gen_down_c1") is not None:
                _safe_attr(gv, "ramping_cost_decrease", el.get("du_gen_down_c1"))

            if cls == "PN_GenNonDispatchable":
                ts_key  = el.get("xi_ref_profile", "")
                ds_main = f"GenerationUnit/{gid}/availability"
                _ensure_profile(ts_key)
                _set_profile_type_from_factor(model, ts_key, el.get("profile_factor_type"))
                if gen_cls == "HydroGenerationUnit":
                    # RoR availability is semantically river inflow. Use the
                    # specialised relation/annual attribute when available,
                    # falling back gracefully for older schemas.
                    _safe_attr(gv, "annual_run_of_river_inflow_energy", el.get("profile_factor", 0.0))
                    _safe_attr(gv, "annual_resource_potential", el.get("profile_factor", 0.0))
                    _safe_rel(gv, "hasRunOfRiverInflowProfile", ts_key)
                else:
                    _safe_attr(gv, "annual_resource_potential", el.get("profile_factor", 0.0))
                    _safe_rel(gv, "hasAvailabilityProfile", ts_key)
                ret, arr, mat_data = add_profile(el, 1, mat_data)
                if ret:
                    data_profiles[ds_main] = arr
                    if ts_key:
                        data_profiles[f"profiles/{ts_key}"] = arr
            else:
                _safe_attr(gv, "annual_resource_potential", 0.0)

    return data_profiles, model

# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    schema_dir    = Path("../schemas")
    european_json = Path("RRE_EU_with_profiles.jpn")

    # ── Import from FlexEco .jpn ──────────────────────────────────────────
    # data_timeseries: dict { profile_id → np.ndarray }
    # m: populated CesdmModel with Profile/TimestampSeries entities
    data_timeseries, m = import_from_flexeco(schema_dir, european_json)

    errors = m.validate()
    print(f"Validation errors: {len(errors)}")
    for e in errors:
        print(" -", e)

    # ── YAML exports ──────────────────────────────────────────────────────
    m.export_yaml_hierarchical("european_system_hierarchical.yaml")
    m.export_yaml("european_system.yaml")

    # ── HDF5: TimestampSeries + Profile payloads (CESDM native format) ───
    # All profiles keyed by their Profile entity id under /profiles/<id>/values
    m.export_hdf5("european_system.h5", values_map=data_timeseries)
    print("Exported YAML (hierarchical + flat) and HDF5 (CESDM format).")

    # ── Round-trip via JSON ───────────────────────────────────────────────
    m.export_json("european_system.json")
    m2: CesdmModel = build_model_from_yaml(schema_dir)
    m2.import_json("european_system.json")
    errors2 = m2.validate()
    print(f"Round-trip validation errors: {len(errors2)}")

    # ── Export back to FlexEco .jpn + HDF5 profiles for FlexEco ─────────
    # Step 1: attach the in-memory arrays to the Profile entities so the
    #         HDF5 exporter can find them.
    _attach_profile_values(m2, data_timeseries)

    # Step 2: export JSON + HDF5 in one call.
    # The HDF5 layout mirrors the CESDM convention:
    #   /profiles/<profile_id>/values  (float64)
    #   /profiles/<profile_id>/attrs   (profile_type, profile_unit, …)
    #   /timestamps/<ts_id>/attrs      (start_datetime, resolution, …)
    export_to_flexeco(
        m2,
        "european_system_flexeco.jpn",
        hdf5_path="european_system_flexeco/profiles/profiles.h5",
    )
    print("Exported FlexEco .jpn + HDF5 profile file.")

    m2.export_csv_by_class_wide("outputs/by_class_wide")
