"""
import_flexeco.py
================

Bidirectional converter between FlexEco .jpn (JSON) files and the
CESDM V4 model (ear_toolbox / cesdm_toolbox).

V4 schema mapping (V1 → V4)
----------------------------
Entity classes:
  EnergyDomain                  → CarrierDomain
  ElectricityNode / EnergyNode  → ElectricalBus
  EnergyConversionTechnology1x1 → GenerationUnit
  EnergyStorageTechnology       → StorageUnit / ReservoirStorageUnit
  EnergyDemand                  → DemandUnit
  NetTransferCapacity           → Interconnector
  TransmissionLine              → TransmissionLine
  TwoWindingPowerTransformer    → Transformer
  HVDCLink (PN_HVDC)            → HVDCLink
  StorageTechnologyType         → StorageType
  TechnologyType                → GeneratorType

Relations:
  hasEnergyCarrier              → hasCarrier          (on CarrierDomain)
  isInEnergyDomain              → belongsToCarrierDomain (on ElectricalBus)
  isInGeographicalRegion        → locatedIn
  hasGeographicalRegionAsParent → isSubRegionOf
  isOutputNodeOf/isConnectedToNode → atNode
  isFromNodeOf                  → fromNode
  isToNodeOf                    → toNode
  instanceOf                    → hasTechnology
  hasInputEnergyCarrier         → hasInputCarrier
  hasOutputEnergyCarrier        → hasOutputCarrier

Attribute placement (current V4):
  Operational, physical and topology data are stored directly on the asset
  entity through the generic EAR API. Schema groups only organize access and
  hierarchical export; they do not create RepresentationView entities.
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
for _path in (_REPO_ROOT, _REPO_ROOT / 'tools'):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)
from cesdm_toolbox import build_model_from_yaml, CesdmModel
from ear_toolbox import Entity
from hydro_utils import hydro_machine_role, hydro_storage_kind
from generation_classifier import generation_asset_class, hydrogen_generation_efficiency
_DOMAIN_ID = 'domain.electricity'
_CARRIER_ID = 'carrier.electricity'
GENERATION_ASSET_CLASSES = ('GenerationUnit', 'HydroGenerationUnit', 'WindGenerationUnit', 'SolarGenerationUnit', 'ThermalGenerationUnit')
STORAGE_ASSET_CLASSES = ('StorageUnit', 'ReservoirStorageUnit')

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
    cls = getattr(entity_id, 'cls', None) or getattr(entity_id, 'class_name', None)
    if isinstance(cls, str) and cls:
        return cls
    eid = getattr(entity_id, 'id', entity_id)
    if not isinstance(eid, str):
        return None
    for cls_name, entities in getattr(model, 'entities', {}).items():
        if eid in entities:
            return cls_name
    return None

def _technology_key_from_flexeco(el: dict) -> str:
    """Return a lower-case technology key assembled from common FlexEco fields."""
    parts = [str(el.get('technology', '')), str(el.get('name', '')), str(el.get('carrier', '')), str(el.get('fuel', ''))]
    return ' '.join(parts).lower()

def _generation_asset_class_from_flexeco(el: dict) -> str:
    """Map a FlexEco generator element to the structured GenerationUnit subclass.

    Uses the shared generation classifier so import_from_flexeco follows the
    same technology semantics as PyPSA/TYNDP import and CESDM→FlexECO export.
    """
    return generation_asset_class(el.get('carrier'), el.get('technology') or el.get('name'))

def _storage_asset_class_from_flexeco(cls: str, el: dict) -> str:
    """Map a FlexEco storage element class to the correct StorageUnit subclass.

    PN_StorageDam          → ReservoirStorageUnit (reservoir hydro)
    PN_StoragePump         → ReservoirStorageUnit (open-loop PHS upper reservoir)
    PN_StoragePumpNoInfeed → ReservoirStorageUnit (closed-loop PHS upper reservoir)
    everything else        → StorageUnit (batteries, generic)

    PHS and reservoir-hydro both use ReservoirStorageUnit. The distinction
    is captured on the linked HydroGenerationUnit (is_reversible = true/false)
    and on Storage.asset (has_active_charging, annual_natural_inflow_energy).
    """
    key = f'{cls} {_technology_key_from_flexeco(el)}'.lower()
    if any((x in key for x in ('battery', 'electrochemical'))):
        return 'StorageUnit'
    if any((x in key for x in ('reservoir', 'pondage', 'dam', 'pn_storagedam', 'pump_storage', 'pumped', 'pn_storagepump', 'phs', 'pump'))):
        return 'ReservoirStorageUnit'
    return 'StorageUnit'

def load_mat_variable(var_name: str, base_path: Path):
    base_path = Path(base_path)
    candidate = base_path / f'{var_name}.mat'
    if not candidate.is_file():
        print(f"Could not find .mat file for '{var_name}'. Tried: {candidate}")
        return (False, None)
    data = loadmat(candidate)
    if var_name not in data:
        print(f"Variable '{var_name}' not found in {candidate}.")
        return (False, None)
    return (True, np.asarray(data[var_name]))

def load_mat_file(var_name: str, mat_filename: Optional[str]=None, fallback_path: Optional[Path]=None, whole_data: Optional[dict]=None):
    candidates = []
    if fallback_path is not None:
        candidates.append(Path(fallback_path) / mat_filename)
    mat_file = next((c for c in candidates if c.is_file()), None)
    if mat_file is None:
        print(f"Could not find .mat file for '{var_name}'. Tried: {candidates}")
        return (False, None, None)
    data = whole_data if whole_data is not None else loadmat(mat_file)
    if var_name not in data:
        print(f"Variable '{var_name}' not found in {mat_file}.")
        return (False, None, data)
    return (True, np.asarray(data[var_name]), data)

def add_profile(el: dict, type_: int, mat_data: Optional[dict]):
    profile_name = el.get('xi_ref_profile', '')
    if not profile_name:
        return (False, None, None)
    if type_ == 1:
        ret, arr = load_mat_variable(profile_name, Path('../data/sach2021/profiles'))
        return (ret, np.transpose(arr) if ret else None, None)
    elif type_ == 2:
        ret, arr, mat_data = load_mat_file(profile_name, 'profiles.mat', Path('../data/sach2021/profiles'), mat_data)
        return (ret, np.transpose(arr) if ret else None, mat_data)
    return (False, None, None)
_PROFILE_TYPE_TO_FACTOR_TYPE: dict[str, int] = {'as_SI': 0, 'as_normalized_annual_energy': 1, 'as_capacity_factor': 2}
_FACTOR_TYPE_TO_PROFILE_TYPE: dict[int, str] = {v: k for k, v in _PROFILE_TYPE_TO_FACTOR_TYPE.items()}

def _profile_factor_type(model, prof_id: str | None) -> int | None:
    """
    Return the FlexEco profile_factor_type integer for a Profile entity.

    Looks up the Profile entity by id, reads its ``profile_type`` attribute,
    and maps it to the corresponding integer.  Returns None if the Profile
    entity or its profile_type is absent.
    """
    if not prof_id:
        return None
    prof_ent = model.entities.get('Profile', {}).get(prof_id)
    if prof_ent is None:
        return None
    raw = getattr(prof_ent, 'data', {}).get('profile_type')
    if isinstance(raw, dict):
        raw = raw.get('value')
    return _PROFILE_TYPE_TO_FACTOR_TYPE.get(str(raw) if raw else '', None)

def _export_profiles_hdf5(model: CesdmModel, hdf5_path: str | Path) -> None:
    """
    Collect all Profile entities referenced by asset entities and write
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

    Profile ids are collected by traversing the three profile relations on all
    populated view classes:
      hasAvailabilityProfile  (GenerationUnit, GenerationUnit, HydroGenerationUnit,
                           GenerationUnit, GenerationUnit,
                           asset)
      hasDemandProfile    (Demand.asset)
      hasNaturalInflowProfile    (Storage.asset, HydroReservoir.asset)

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
        raise ImportError('h5py and numpy are required for HDF5 profile export. Install with: pip install h5py numpy')
    hdf5_path = Path(hdf5_path)
    hdf5_path.parent.mkdir(parents=True, exist_ok=True)
    ref_relations = ('hasAvailabilityProfile', 'hasRunOfRiverInflowProfile', 'hasDemandProfile', 'hasNaturalInflowProfile')
    seen: set[str] = set()
    series_names: list[str] = []
    for entities in model.entities.values():
        for ent in entities.values():
            data = getattr(ent, 'data', {}) or {}
            for rel in ref_relations:
                raw = data.get(rel)
                if raw is None:
                    continue
                targets = raw if isinstance(raw, (list, tuple)) else [raw]
                for target in targets:
                    profile_id = str(target) if target else None
                    if profile_id and profile_id not in seen:
                        seen.add(profile_id)
                        series_names.append(profile_id)
    if not series_names:
        print('[_export_profiles_hdf5] No referenced profiles found — HDF5 not written.')
        return
    profile_store = model.entities.get('Profile', {})
    n_profiles = len(series_names)
    n_timesteps = None
    arrays: list = []
    for pid in series_names:
        prof_ent = profile_store.get(pid)
        arr_raw = None
        if prof_ent is not None:
            arr_raw = getattr(prof_ent, 'data', {}).get('_values')
        if arr_raw is not None:
            arr = np.asarray(arr_raw, dtype=np.float64).ravel()
            if n_timesteps is None:
                n_timesteps = len(arr)
            arrays.append(arr)
        else:
            arrays.append(None)
    if n_timesteps is None:
        print('[_export_profiles_hdf5] No numeric arrays attached — all profiles will be zero-filled.')
        n_timesteps = 8760
    matrix_cols: list = []
    for pid, arr in zip(series_names, arrays):
        if arr is None:
            print(f"  [WARN] Profile '{pid}' has no attached values — zero-filled.")
            matrix_cols.append(np.zeros(n_timesteps, dtype=np.float64))
        elif len(arr) != n_timesteps:
            print(f"  [WARN] Profile '{pid}' length {len(arr)} ≠ {n_timesteps} — truncated/padded.")
            col = np.zeros(n_timesteps, dtype=np.float64)
            col[:min(len(arr), n_timesteps)] = arr[:n_timesteps]
            matrix_cols.append(col)
        else:
            matrix_cols.append(arr)
    data_matrix = np.column_stack(matrix_cols).astype(np.float64)
    with h5py.File(str(hdf5_path), 'w') as hf:
        hf.create_dataset('series_names', data=np.array(series_names, dtype='S64'))
        hf.create_dataset('values', data=data_matrix, dtype=np.float64)
    print(f'[_export_profiles_hdf5] Written {n_profiles} profiles × {n_timesteps} timesteps → {hdf5_path}')

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
    profile_store = model.entities.get('Profile', {})
    attached = 0
    for prof_id, arr in (values_map or {}).items():
        ent = profile_store.get(prof_id)
        if ent is not None:
            data = getattr(ent, 'data', None)
            if data is not None:
                data['_values'] = arr
                attached += 1
    return attached

def _is_flexeco_storage_dam_candidate(storage_id: str, ent, tt_id: str | None, storage_entity) -> bool:
    """Return True only for real reservoir/pondage hydro storage assets.

    Detection uses (in order of reliability):
    1. ent.cls — the class name on the ear_toolbox Entity dataclass.
       ReservoirStorageUnit is always a dam candidate.
    2. tt_id (hasTechnology) — explicit technology type (TYNDP importer).
    3. Heuristic key scan — fallback for untyped models.

    PumpedHydro/pump storage is always excluded regardless of detection path.
    """
    cls_name = getattr(ent, 'cls', None) or getattr(ent, 'class_name', '') or getattr(ent, 'type_name', '')
    cls_lower = str(cls_name or '').lower()
    if any((x in cls_lower for x in ('pumpedhydro', 'pumpedstorage', 'pumpstorage', 'pumpedhydrostorageunit'))):
        return False
    if cls_lower in ('reservoirstorageunit',):
        return True
    if storage_entity is not None and (storage_entity.get_attr_value('has_active_charging', False) if storage_entity is not None else False):
        return False
    explicit_type = str(tt_id or '').lower()
    if any((x in explicit_type for x in ('pumpedhydro', 'pump_storage', 'pumped', 'phs.closedloop', 'phs.openloop'))):
        return False
    if explicit_type in {'storage.hydro.reservoir', 'storage.hydro.pondage'}:
        return True
    key = ' '.join((str(x or '').lower() for x in [storage_id, tt_id, ent.get_attr_value('name', ''), storage_entity.get_attr_value('storage_technology_type', '') if storage_entity is not None else '']))
    if 'pumpedhydro' in key or 'pump_storage' in key or 'pumped' in key or ('pump' in key):
        return False
    if 'reservoir' in key or 'pondage' in key:
        return True
    return False

def export_to_flexeco(model: CesdmModel, output_path: str | Path, *, hdf5_path: str | Path | None=None) -> None:
    """
    Export a CESDM V4 model to a FlexEco .jpn JSON file.

    ----------------
    - Node data read from NetworkNode subclass entities (ElectricalBus, GasBus, etc.)
    - Node topology (locatedIn, belongsToCarrierDomain) replaces isInGeographicalRegion / isInEnergyDomain
    - Transmission data split across TwoPort.asset (from/to nodes, switch states)
      and Branchasset (impedances, ratings, flow limits)
    - Generator operational data read from GenerationUnit, not GenerationUnit
    - Storage operational data read from Storage.asset, not StorageUnit
    - Demand operational data read from Demand.asset, not DemandUnit
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
    elements = []
    used_uids: set[int] = set()
    id_to_uid: dict[str, int] = {}

    def _uid(ent_id: str, prefix: str) -> int:
        if ent_id in id_to_uid:
            return id_to_uid[ent_id]
        uid = None
        if ent_id.startswith(prefix):
            suffix = ent_id[len(prefix):]
            if suffix.isdigit():
                uid = int(suffix)
        if uid is None:
            uid = max(used_uids) + 1 if used_uids else 1
        while uid in used_uids:
            uid += 1
        used_uids.add(uid)
        id_to_uid[ent_id] = uid
        return uid
    bus_entities = model.entities.get('Bus', {}) | model.entities.get('ElectricalBus', {}) | model.entities.get('GasBus', {}) | model.entities.get('HydrogenBus', {}) | model.entities.get('HeatBus', {}) | model.entities.get('WaterBus', {})
    carrier_entities = model.entities.get('Carrier', {})
    transmission_ents = model.entities.get('TransmissionElement', {})
    line_ents = model.entities.get('TransmissionLine', {}) | model.entities.get('TransmissionLine_legacy', {})
    tr2_ents = model.entities.get('Transformer', {}) | model.entities.get('TwoWindingPowerTransformer', {})
    hvdc_ents = model.entities.get('HVDCLink', {})
    ntc_ents = model.entities.get('Interconnector', {}) | model.entities.get('NetTransferCapacity', {})
    gen_ents = _entities_for_classes(model, GENERATION_ASSET_CLASSES)
    stor_ents = _entities_for_classes(model, STORAGE_ASSET_CLASSES)
    dem_ents = model.entities.get('DemandUnit', {})
    gen_type_ents = model.entities.get('GeneratorType', {})
    stor_type_ents = model.entities.get('StorageType', {})
    esm_ents = model.entities.get('EnergySystemModel', {})
    node_uid_map: dict[str, int] = {}
    for uid_start, ent_dict, target in [(10000001, bus_entities, node_uid_map)]:
        uid = uid_start
        for eid in ent_dict:
            target[eid] = uid
            used_uids.add(uid)
            id_to_uid[eid] = uid
            uid += 1
    trans_uid_map: dict[str, int] = {}
    line_uid_map: dict[str, int] = {}
    tr2_uid_map: dict[str, int] = {}
    dc_uid_map: dict[str, int] = {}
    ntc_uid_map: dict[str, int] = {}
    gen_uid_map: dict[str, int] = {}
    stor_uid_map: dict[str, int] = {}
    dem_uid_map: dict[str, int] = {}
    for uid_start, ent_dict, target in [(20000001, transmission_ents, trans_uid_map), (21000001, line_ents, line_uid_map), (21500001, ntc_ents, ntc_uid_map), (22000001, tr2_ents, tr2_uid_map), (23000001, hvdc_ents, dc_uid_map), (40000001, gen_ents, gen_uid_map), (50000001, stor_ents, stor_uid_map), (30000001, dem_ents, dem_uid_map)]:
        uid = uid_start
        for eid in ent_dict:
            target[eid] = uid
            used_uids.add(uid)
            id_to_uid[eid] = uid
            uid += 1

    def _bus_uid(bus_id: str | None) -> int | None:
        return node_uid_map.get(bus_id) if bus_id is not None else None

    def _carrier_name(carrier_id: str | None) -> str | None:
        if carrier_id is None:
            return None
        return carrier_id[2:] if carrier_id.startswith('c_') else carrier_id

    def _carrier_cost(carrier_id: str | None) -> float | None:
        carrier = carrier_entities.get(carrier_id) if carrier_id else None
        return (carrier.get_attr_value('energy_carrier_cost') if carrier is not None else None) if carrier is not None else None

    def _carrier_co2(carrier_id: str | None) -> float | None:
        carrier = carrier_entities.get(carrier_id) if carrier_id else None
        return (carrier.get_attr_value('co2_emission_intensity') if carrier is not None else None) if carrier is not None else None
    map_busses: dict[int, dict] = {}
    for bid, ent in bus_entities.items():
        uid = node_uid_map[bid]
        data = getattr(ent, 'data', {})
        region = None
        raw_loc = data.get('locatedIn')
        if isinstance(raw_loc, (list, tuple)):
            region = raw_loc[0] if raw_loc else None
        elif raw_loc:
            region = raw_loc
        bus_el: dict = {'class': 'PN_Busbar', 'uid': uid, 'name': ent.get_attr_value('name', bid), 'Un': ent.get_attr_value('nominal_voltage', 0.0)}
        if region and region != 'region_europe':
            bus_el['zone_name'] = region
            bus_el['country'] = region
        lon = ent.get_attr_value('longitude')
        lat = ent.get_attr_value('latitude')
        if lon is not None:
            bus_el['longitude'] = lon
        if lat is not None:
            bus_el['latitude'] = lat
        map_busses[uid] = bus_el
        elements.append(bus_el)
    for eid, ent in line_ents.items():
        uid = line_uid_map[eid]
        frm = ent.get_relation('fromNode')
        to = ent.get_relation('toNode')
        el = {'class': 'PN_Line', 'uid': uid, 'name': ent.get_attr_value('name', eid), 'bus1_uid': _bus_uid(frm), 'bus2_uid': _bus_uid(to), 'r': ent.get_attr_value('series_resistance_per_km', 0.0), 'x': ent.get_attr_value('series_reactance_per_km', 0.1), 'b': ent.get_attr_value('shunt_susceptance_per_km', 0.1), 'Length': ent.get_attr_value('line_length', 1.0), 'numparlines': ent.get_attr_value('parallel_circuit_count', 1), 'side1_on': int(ent.get_attr_value('from_switch_closed', 1)), 'side2_on': int(ent.get_attr_value('to_switch_closed', 1)), 'Smax': ent.get_attr_value('thermal_capacity_rating') or 0.0}
        elements.append(el)
    for eid, ent in tr2_ents.items():
        uid = tr2_uid_map[eid]
        frm = ent.get_relation('fromNode')
        to = ent.get_relation('toNode')
        el = {'class': 'PN_TR2', 'uid': uid, 'name': ent.get_attr_value('name', eid), 'bus1_uid': _bus_uid(frm), 'bus2_uid': _bus_uid(to), 'side1_on': int(ent.get_attr_value('from_switch_closed', 1)), 'side2_on': int(ent.get_attr_value('to_switch_closed', 1)), 'numparlines': ent.get_attr_value('parallel_circuit_count', 1), 'SR': ent.get_attr_value('thermal_capacity_rating', 0.0), 'UR1': ent.get_attr_value('rated_primary_voltage', 0.0), 'UR2': ent.get_attr_value('rated_secondary_voltage', 0.0), 'Smax': ent.get_attr_value('thermal_capacity_rating', 0.0), 'Usc': ent.get_attr_value('short_circuit_voltage_in_percentage') or 10.0}
        elements.append(el)
    for eid, ent in hvdc_ents.items():
        uid = dc_uid_map[eid]
        frm = ent.get_relation('fromNode')
        to = ent.get_relation('toNode')
        el = {'class': 'PN_HVDC', 'uid': uid, 'name': ent.get_attr_value('name', eid), 'bus1_uid': _bus_uid(frm), 'bus2_uid': _bus_uid(to), 'side1_on': int(ent.get_attr_value('from_switch_closed', 1)), 'side2_on': int(ent.get_attr_value('to_switch_closed', 1)), 'Pmax': ent.get_attr_value('max_flow', None)}
        elements.append(el)
    for eid, ent in (ntc_ents | transmission_ents).items():
        uid = ntc_uid_map.get(eid) or trans_uid_map.get(eid)
        if uid is None:
            continue
        frm = ent.get_relation('fromNode')
        to = ent.get_relation('toNode')
        p12 = ent.get_attr_value('maximum_power_flow_from_to', None)
        p21 = ent.get_attr_value('maximum_power_flow_to_from', None)
        el = {'class': 'PN_NTC', 'uid': uid, 'name': ent.get_attr_value('name', eid), 'bus1_uid': _bus_uid(frm), 'bus2_uid': _bus_uid(to), 'P1max': p12, 'P2max': p21, 'technology': 'NTC'}
        elements.append(el)
    for lid, ent in dem_ents.items():
        uid = dem_uid_map[lid]
        demand_entity = ent
        bus_id = ent.get_relation('atNode')
        busuid = _bus_uid(bus_id)
        is_flex = demand_entity.get_attr_value('is_demand_flexible', False)
        if is_flex:
            load_el = {'class': 'PN_LoadFlexible', 'uid': uid, 'name': ent.get_attr_value('name', lid), 'busuid': busuid, 'profile_factor': demand_entity.get_attr_value('annual_energy_demand', 0.0), 'u_load_c1': demand_entity.get_attr_value('variable_operating_cost', 0.0), 'w_c1': -demand_entity.get_attr_value('value_of_lost_load', 10000.0), 'xi_ref_profile': demand_entity.get_relation('hasDemandProfile') or '', 'profile_factor_type': _profile_factor_type(model, demand_entity.get_relation('hasDemandProfile')), 'T0': demand_entity.get_attr_value('flexibility_window_time_start', 0.0), 'T1': demand_entity.get_attr_value('flexibility_window_time_end', 0.0), 'TP': demand_entity.get_attr_value('flexibility_time_resolution', 0.0)}
        else:
            load_el = {'class': 'PN_Load', 'uid': uid, 'name': ent.get_attr_value('name', lid), 'busuid': busuid, 'w_c1': -demand_entity.get_attr_value('value_of_lost_load', 10000.0), 'profile_factor': demand_entity.get_attr_value('annual_energy_demand', 0.0), 'xi_ref_profile': demand_entity.get_relation('hasDemandProfile') or '', 'profile_factor_type': _profile_factor_type(model, demand_entity.get_relation('hasDemandProfile'))}
        if demand_entity.get_attr_value('maximum_energy_demand') is not None:
            load_el['u_load_max'] = demand_entity.get_attr_value('maximum_energy_demand')
        if busuid and busuid in map_busses:
            load_el['country'] = map_busses[busuid].get('country', '')
        load_el['technology'] = demand_entity.get_attr_value('demand_type', '')
        if not load_el.get('xi_ref_profile'):
            print(f'Load {lid} has no profile reference — skipped')
            continue
        elements.append(load_el)
    exported_as_dam: set[str] = set()
    exported_as_pump: set[str] = set()
    exported_as_pump_noinfeed: set[str] = set()
    skipped_as_no_inflow_dam: set[str] = set()
    for sid, ent in stor_ents.items():
        uid = stor_uid_map[sid]
        bus_id = ent.get_relation('atNode')
        if bus_id is None:
            for _gid, _gent in (model.entities.get('HydroGenerationUnit') or {}).items():
                _gdraws = (getattr(_gent, 'data', {}) or {}).get('drawsFromReservoir')
                _gdraws_list = _gdraws if isinstance(_gdraws, (list, tuple)) else [_gdraws]
                if sid in _gdraws_list:
                    bus_id = _gent.get_relation('atNode')
                    if bus_id is not None:
                        break
        busuid = _bus_uid(bus_id)
        storage_entity = ent
        tt_data = getattr(ent, 'data', {})
        raw_tt = tt_data.get('hasTechnology')
        tt_id = raw_tt[0] if isinstance(raw_tt, (list, tuple)) else raw_tt
        tt_ent = stor_type_ents.get(tt_id) if tt_id else None
        hydro_generation_entity = None
        for _gid, _gent in (model.entities.get('HydroGenerationUnit') or {}).items():
            _gdata = getattr(_gent, 'data', {}) or {}
            _draws = _gdata.get('drawsFromReservoir')
            _draws_list = _draws if isinstance(_draws, (list, tuple)) else [_draws]
            if sid in _draws_list:
                hydro_generation_entity = _gent
                break
        is_storage_dam_candidate = _is_flexeco_storage_dam_candidate(sid, ent, tt_id, storage_entity)
        stor_carrier = ''
        stor_tech = str(((storage_entity.get_attr_value('storage_technology_type') if storage_entity is not None else None) or (tt_ent.get_attr_value('storage_technology_type') if tt_ent is not None else None)) or '').lower()
        if stor_tech:
            stor_carrier = stor_tech
        has_natural_inflow_flag = (storage_entity.get_attr_value('has_natural_inflow', False) if storage_entity is not None else False) or (tt_ent.get_attr_value('has_natural_inflow', False) if tt_ent is not None else False)
        if not stor_carrier and (raw_c := getattr(ent, 'data', {}).get('storesCarrier')):
            raw_c = raw_c[0] if isinstance(raw_c, (list, tuple)) else raw_c
            oc_ent = carrier_entities.get(raw_c)
            if oc_ent:
                raw_name = getattr(oc_ent, 'data', {}).get('name') or str(raw_c)
                stor_carrier = str(raw_name.get('value', raw_name) if isinstance(raw_name, dict) else raw_name).lower()
        is_reversible_gen = False
        machine_role_gen = None
        if hydro_generation_entity is not None:
            machine_role_gen = hydro_generation_entity.get_attr_value('machine_role') if hydro_generation_entity is not None else None
        if hydro_generation_entity is not None:
            for _gid, _gent in (model.entities.get('HydroGenerationUnit') or {}).items():
                _gdata = getattr(_gent, 'data', {}) or {}
                _draws = _gdata.get('drawsFromReservoir')
                _draws_list = _draws if isinstance(_draws, (list, tuple)) else [_draws]
                if sid in _draws_list:
                    is_reversible_gen = bool(_gent.get_attr_value('is_reversible', False))
                    break
        is_hydro = is_storage_dam_candidate or bool(has_natural_inflow_flag) or 'hydro' in stor_carrier or ('water' in stor_carrier) or (hydro_generation_entity is not None)
        is_phs = bool((storage_entity.get_attr_value('has_active_charging', False) if storage_entity is not None else False) or (tt_ent.get_attr_value('has_active_charging', False) if tt_ent is not None else False)) or machine_role_gen == 'reversible' or is_reversible_gen or ((hydro_generation_entity.get_attr_value('maximum_pumping_power') if hydro_generation_entity is not None else None) is not None) or ('phs' in stor_carrier) or ('pumped' in stor_carrier) or ('pumpedhydro' in str(tt_id or '').lower()) or ('pump_storage' in str(tt_id or '').lower())
        has_active_charging_flag = is_phs
        chg_eff = (hydro_generation_entity.get_attr_value('pumping_efficiency') if hydro_generation_entity is not None else None) or ((storage_entity.get_attr_value('pumping_efficiency') if storage_entity is not None else None) or (tt_ent.get_attr_value('pumping_efficiency') if tt_ent is not None else None)) or ((storage_entity.get_attr_value('charging_efficiency') if storage_entity is not None else None) or (tt_ent.get_attr_value('charging_efficiency') if tt_ent is not None else None))
        dis_eff = (hydro_generation_entity.get_attr_value('turbine_efficiency') if hydro_generation_entity is not None else None) or (hydro_generation_entity.get_attr_value('discharging_efficiency') if hydro_generation_entity is not None else None) or ((storage_entity.get_attr_value('discharging_efficiency') if storage_entity is not None else None) or (tt_ent.get_attr_value('discharging_efficiency') if tt_ent is not None else None))
        voc = (hydro_generation_entity.get_attr_value('variable_operating_cost') if hydro_generation_entity is not None else None) or ((storage_entity.get_attr_value('variable_operating_cost') if storage_entity is not None else None) or (tt_ent.get_attr_value('variable_operating_cost') if tt_ent is not None else None))
        gen_max = (hydro_generation_entity.get_attr_value('nominal_power_capacity') if hydro_generation_entity is not None else None) or ((storage_entity.get_attr_value('nominal_power_capacity') if storage_entity is not None else None) or (tt_ent.get_attr_value('nominal_power_capacity') if tt_ent is not None else None)) or 0.0
        load_max = (hydro_generation_entity.get_attr_value('maximum_pumping_power') if hydro_generation_entity is not None else None) or ((storage_entity.get_attr_value('maximum_pumping_power') if storage_entity is not None else None) or (tt_ent.get_attr_value('maximum_pumping_power') if tt_ent is not None else None)) or ((storage_entity.get_attr_value('maximum_charging_power') if storage_entity is not None else None) or (tt_ent.get_attr_value('maximum_charging_power') if tt_ent is not None else None)) or 0.0
        chg_voc = (storage_entity.get_attr_value('charging_variable_operating_cost', 0.0) if storage_entity is not None else 0.0) or (tt_ent.get_attr_value('charging_variable_operating_cost', 0.0) if tt_ent is not None else 0.0)
        inflow = (storage_entity.get_attr_value('annual_natural_inflow_energy') if storage_entity is not None else None) or (tt_ent.get_attr_value('annual_natural_inflow_energy') if tt_ent is not None else None)
        has_inflow = bool(inflow and inflow > 0.0)
        capacity = (storage_entity.get_attr_value('energy_storage_capacity') if storage_entity is not None else None) or (tt_ent.get_attr_value('energy_storage_capacity') if tt_ent is not None else None)
        if is_hydro and has_inflow and has_active_charging_flag and (chg_eff is not None):
            exported_as_pump.add(sid)
            inflow_ref = storage_entity.get_relation('hasNaturalInflowProfile') if storage_entity is not None else None
            if not inflow_ref:
                print(f'[WARN] {sid} is open-loop PHS but has no hasNaturalInflowProfile — skipped')
                continue
            el = {'class': 'PN_StoragePump', 'uid': uid, 'name': ent.get_attr_value('name', sid), 'busuid': busuid, 'eta_gen': dis_eff, 'eta_load': chg_eff, 'u_gen_max': gen_max, 'u_load_max': load_max, 'u_gen_c1': voc if voc is not None else 0.0, 'u_load_c1': chg_voc, 'Capacity': capacity, 'xi_ref_profile': inflow_ref, 'profile_factor': inflow, 'profile_factor_type': _profile_factor_type(model, inflow_ref), 'has_inflow': True, 'x_boundary_type': 2}
        elif is_storage_dam_candidate and (not has_inflow) and (not is_phs):
            skipped_as_no_inflow_dam.add(sid)
            print(f"[INFO] Reservoir/Pondage '{sid}' has no inflow data — skipped (neither PN_StorageDam nor PN_GenDispatchable).")
            continue
        elif is_storage_dam_candidate and has_inflow:
            exported_as_dam.add(sid)
            inflow_ref = storage_entity.get_relation('hasNaturalInflowProfile') if storage_entity is not None else None
            el = {'class': 'PN_StorageDam', 'uid': uid, 'name': ent.get_attr_value('name', sid), 'busuid': busuid, 'eta_gen': dis_eff, 'u_gen_max': gen_max, 'u_gen_c1': voc if voc is not None else 0.0, 'Capacity': capacity, 'profile_factor': inflow, 'has_inflow': True, 'x_boundary_type': 2}
            if inflow_ref:
                el['xi_ref_profile'] = inflow_ref
                el['profile_factor_type'] = _profile_factor_type(model, inflow_ref)
        elif chg_eff is not None and chg_eff > 0.0:
            if is_phs:
                exported_as_pump_noinfeed.add(sid)
            el = {'class': 'PN_StoragePumpNoInfeed', 'uid': uid, 'name': ent.get_attr_value('name', sid), 'busuid': busuid, 'eta_gen': dis_eff, 'eta_load': chg_eff, 'u_gen_max': gen_max, 'u_load_max': load_max, 'u_gen_c1': voc if voc is not None else 0.0, 'u_load_c1': chg_voc, 'Capacity': capacity, 'has_inflow': False, 'x_boundary_type': 2}
        else:
            continue
        el['carrier'] = 'carrier.electricity'
        c_cost_storage = _carrier_cost('carrier.electricity')
        if c_cost_storage is not None:
            el['xi_c1'] = c_cost_storage
        ramp_up = (hydro_generation_entity.get_attr_value('maximum_ramp_rate_up') if hydro_generation_entity is not None else None) or ((storage_entity.get_attr_value('maximum_ramp_rate_up') if storage_entity is not None else None) or (tt_ent.get_attr_value('maximum_ramp_rate_up') if tt_ent is not None else None))
        ramp_dn = (hydro_generation_entity.get_attr_value('maximum_ramp_rate_down') if hydro_generation_entity is not None else None) or ((storage_entity.get_attr_value('maximum_ramp_rate_down') if storage_entity is not None else None) or (tt_ent.get_attr_value('maximum_ramp_rate_down') if tt_ent is not None else None))
        if ramp_up is not None:
            el.update({'has_ramprate': True, 'du_gen_up_max': ramp_up})
        if ramp_dn is not None:
            el.update({'has_ramprate': True, 'du_gen_down_max': ramp_dn})
        if busuid and busuid in map_busses:
            el['country'] = map_busses[busuid].get('country', '')
        source_storage_technology = (storage_entity.get_attr_value('storage_technology_type') if storage_entity is not None else None) or (tt_ent.get_attr_value('storage_technology_type') if tt_ent is not None else None)
        if source_storage_technology:
            el['technology'] = source_storage_technology
        elif tt_id:
            el['technology'] = tt_id
        elements.append(el)
    for gid, ent in gen_ents.items():
        raw_tt_skip = getattr(ent, 'data', {}).get('hasTechnology')
        tt_id_skip = raw_tt_skip[0] if isinstance(raw_tt_skip, (list, tuple)) else raw_tt_skip
        ent_data = getattr(ent, 'data', {})
        raw_draws = ent_data.get('drawsFromReservoir')
        draws_from_list = raw_draws if isinstance(raw_draws, (list, tuple)) else [raw_draws]
        draws_from_list = [d for d in draws_from_list if d is not None]
        _is_hydro_gen_with_reservoir = bool(draws_from_list) and (tt_id_skip in ('Generation.Renewable.Hydro.Reservoir', 'Generation.Renewable.Hydro.Pondage', 'Generation.Renewable.Hydro.PHS.ClosedLoop', 'Generation.Renewable.Hydro.PHS.OpenLoop') or 'hydro' in str(gid).lower())
        if _is_hydro_gen_with_reservoir and any((d in exported_as_dam or d in exported_as_pump or d in exported_as_pump_noinfeed for d in draws_from_list)):
            continue
        uid = gen_uid_map[gid]
        generation_entity = ent
        bus_id = ent.get_relation('atNode')
        busuid = _bus_uid(bus_id)
        tt_data = getattr(ent, 'data', {})
        raw_tt = tt_data.get('hasTechnology')
        tt_id = raw_tt[0] if isinstance(raw_tt, (list, tuple)) else raw_tt
        tt_ent = gen_type_ents.get(tt_id) if tt_id else None
        carrier_id = ent.get_relation('hasInputCarrier')
        resource_id = ent.get_relation('hasInputResource')
        if carrier_id is None and tt_ent:
            raw_c = getattr(tt_ent, 'data', {}).get('hasInputCarrier')
            carrier_id = raw_c[0] if isinstance(raw_c, (list, tuple)) else raw_c
        resource_to_flexeco_carrier = {'resource.renewable.wind': 'carrier.resource.renewable.wind', 'resource.renewable.solar': 'carrier.resource.renewable.solar', 'resource.water': 'carrier.resource.water'}
        gv_cls = _entity_class_name(model, generation_entity)
        ent_cls = _entity_class_name(model, gid)
        gen_label = ' '.join((str(x or '') for x in (gid, tt_id, gv_cls, ent_cls))).lower()
        if gv_cls == 'HydroGenerationUnit' or ent_cls == 'HydroGenerationUnit':
            eff = (generation_entity.get_attr_value('turbine_efficiency') if generation_entity is not None else None) or (tt_ent.get_attr_value('turbine_efficiency') if tt_ent is not None else None) or 1.0
        else:
            eff = (generation_entity.get_attr_value('energy_conversion_efficiency') if generation_entity is not None else None) or (tt_ent.get_attr_value('energy_conversion_efficiency') if tt_ent is not None else None) or 1.0
        cap = (generation_entity.get_attr_value('nominal_power_capacity') if generation_entity is not None else None) or (tt_ent.get_attr_value('nominal_power_capacity') if tt_ent is not None else None) or 0.0
        voc = (generation_entity.get_attr_value('variable_operating_cost') if generation_entity is not None else None) or (tt_ent.get_attr_value('variable_operating_cost') if tt_ent is not None else None)
        annual_res = (generation_entity.get_attr_value('annual_resource_potential') if generation_entity is not None else None) or (tt_ent.get_attr_value('annual_resource_potential') if tt_ent is not None else None)
        prof_ref = (generation_entity.get_relation('hasAvailabilityProfile') if generation_entity is not None else None) or (generation_entity.get_relation('hasRunOfRiverInflowProfile') if generation_entity is not None else None)
        ramp_up = (generation_entity.get_attr_value('maximum_ramp_rate_up') if generation_entity is not None else None) or (tt_ent.get_attr_value('maximum_ramp_rate_up') if tt_ent is not None else None)
        ramp_dn = (generation_entity.get_attr_value('maximum_ramp_rate_down') if generation_entity is not None else None) or (tt_ent.get_attr_value('maximum_ramp_rate_down') if tt_ent is not None else None)
        ramp_c_up = (generation_entity.get_attr_value('ramping_cost_increase') if generation_entity is not None else None) or (tt_ent.get_attr_value('ramping_cost_increase') if tt_ent is not None else None)
        ramp_c_dn = (generation_entity.get_attr_value('ramping_cost_decrease') if generation_entity is not None else None) or (tt_ent.get_attr_value('ramping_cost_decrease') if tt_ent is not None else None)
        dispatch_type = str(((generation_entity.get_attr_value('dispatch_type') if generation_entity is not None else None) or (tt_ent.get_attr_value('dispatch_type') if tt_ent is not None else None) or '') or '').lower()
        has_resource_profile = bool(prof_ref)
        is_reservoir_hydro = tt_id == 'Generation.Renewable.Hydro.Reservoir' or 'pondage' in gid.lower() or 'reservoir' in gid.lower()
        is_nondisp = (dispatch_type == 'nondispatchable' or has_resource_profile) and (not is_reservoir_hydro)
        cls_name = 'PN_GenNonDispatchable' if is_nondisp else 'PN_GenDispatchable'
        el: dict = {'class': cls_name, 'uid': uid, 'name': ent.get_attr_value('name', gid), 'busuid': busuid, 'eta_gen': eff, 'u_gen_max': cap, 'u_gen_c1': voc if voc is not None else 0.0}
        if eff is None:
            eff = 1.0
        if is_nondisp:
            if not prof_ref:
                print(f"[WARN] PN_GenNonDispatchable '{gid}' skipped — no availability/run-of-river profile on dispatch view for '{gid}'.")
                continue
            el['profile_factor'] = float(annual_res) if annual_res is not None else 0.0
            el['xi_ref_profile'] = prof_ref
            el['profile_factor_type'] = _profile_factor_type(model, prof_ref)
        if carrier_id:
            el['carrier'] = _carrier_name(carrier_id)
        elif resource_id:
            mapped_resource = resource_to_flexeco_carrier.get(resource_id)
            if mapped_resource:
                el['carrier'] = mapped_resource
        c_cost = _carrier_cost(carrier_id)
        if c_cost is None and resource_id:
            c_cost = 0.0
        c_co2 = _carrier_co2(carrier_id)
        if c_cost is not None:
            el['xi_c1'] = c_cost
        if c_co2 is not None and c_co2 > 0.0:
            el['has_co2'] = True
            el['MWh_to_tons_co2'] = c_co2
            for _, esm_ent in esm_ents.items():
                el['co2_c1'] = float(esm_ent.get_attr_value('co2_price', 0.0) if esm_ent is not None else 0.0)
        if ramp_up is not None:
            el.update({'has_ramprate': True, 'du_gen_up_max': ramp_up})
        if ramp_c_up is not None:
            el.update({'has_ramprate': True, 'du_gen_up_c1': ramp_c_up})
        if ramp_dn is None and ramp_up is not None and tt_id and ('Nuclear' in tt_id or 'Thermal' in tt_id):
            ramp_dn = ramp_up
        if ramp_dn is not None:
            el.update({'has_ramprate': True, 'du_gen_down_max': ramp_dn})
        if ramp_c_dn is not None:
            el.update({'has_ramprate': True, 'du_gen_down_c1': ramp_c_dn})
        if busuid and busuid in map_busses:
            el['country'] = map_busses[busuid].get('country', '')
        source_technology = (generation_entity.get_attr_value('generator_technology_type') if generation_entity is not None else None) or (tt_ent.get_attr_value('generator_technology_type') if tt_ent is not None else None)
        if source_technology:
            el['technology'] = source_technology
        elif tt_id:
            el['technology'] = tt_id
        elements.append(el)
    jpn = {'PowerSystemElements': elements, 'TIMEEND': 8760, 'TIMESTART': 1, 'ExportProblem': 0, 'baseMVA': 1}
    with output_path.open('w') as f:
        json.dump(jpn, f, indent=2, sort_keys=True)
    if hdf5_path is not None:
        _export_profiles_hdf5(model, hdf5_path)
    return {'id_to_uid': id_to_uid, 'uid_to_id': {v: k for k, v in id_to_uid.items()}, 'node_uid_map': node_uid_map, 'gen_uid_map': gen_uid_map, 'stor_uid_map': stor_uid_map, 'dem_uid_map': dem_uid_map, 'ntc_uid_map': ntc_uid_map, 'line_uid_map': line_uid_map, 'tr2_uid_map': tr2_uid_map, 'dc_uid_map': dc_uid_map}

def _set_profile_type_from_factor(model, prof_id: str | None, factor_type: int | None) -> None:
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
    prof_ent = model.entities.get('Profile', {}).get(prof_id)
    if prof_ent is not None:
        model.add_attribute(prof_id, 'profile_type', profile_type)

def import_from_flexeco(schema_dir: str | Path, european_json: str | Path) -> tuple[dict, CesdmModel]:
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
      + GenerationUnit (operational attrs)
      + SinglePort.asset    (atNode)
    - EnergyStorageTechnology   → StorageUnit
      + Storage.asset    (operational attrs)
      + SinglePort.asset    (atNode)
    - EnergyDemand              → DemandUnit
      + Demand.asset (operational attrs)
      + SinglePort.asset    (atNode)
    - NetTransferCapacity / Line / TR2 / DCLink → TransmissionElement
      + TwoPort.asset     (fromNode, toNode, switch states)
      + Branchasset    (impedances, ratings, flow limits)
    - instanceOf                → hasTechnology
    - hasInputEnergyCarrier     → hasInputCarrier  (on GeneratorType)
    - hasOutputEnergyCarrier    → hasOutputCarrier (on GeneratorType)
    - carrier attribute on Carrier: energy_carrier_type removed
      (use carrier_type / carrier_group instead)

    Returns
    -------
    (data_profiles, model)
      data_profiles : dict[str, np.ndarray] of loaded profile arrays
      model         : populated CesdmModel instance
    """
    schema_dir = Path(schema_dir)
    european_json = Path(european_json)
    model: CesdmModel = build_model_from_yaml(schema_dir)
    model.add_entity(entity_class='EnergySystemModel', entity_id='EnergySystemModel')
    model.add_entity(entity_class='CarrierDomain', entity_id=_DOMAIN_ID)
    model.add_attribute(_DOMAIN_ID, 'name', 'electricity')
    model.add_relation(_DOMAIN_ID, 'hasCarrier', _CARRIER_ID)
    model.add_entity(entity_class='Carrier', entity_id=_CARRIER_ID)
    model.add_attribute(_CARRIER_ID, 'name', 'electricity')
    model.add_attribute(_CARRIER_ID, 'co2_emission_intensity', 0.0)
    model.add_attribute(_CARRIER_ID, 'energy_carrier_cost', 0.0)
    _FC_MAP: dict[str, str] = {'coal': 'c_coal', 'gas': 'c_gas', 'Gas': 'c_gas', 'lignite': 'c_lignite', 'nuclear': 'c_nuclear', 'oil': 'c_oil', 'PHS': 'c_water', 'CHP': 'c_gas', 'hydro': 'c_water', 'water': 'c_water', 'load': 'carrier.electricity', 'ror': 'c_water', 'otherRES': 'c_others_renewable', 'battery': 'carrier.electricity', 'dsr': 'carrier.electricity', 'solar': 'c_pv', 'pv': 'c_pv', 'wind': 'c_wind', 'electricity': 'carrier.electricity', 'others_renewable': 'c_others_renewable'}
    _TECH_CARRIER_MAP: dict[str, str] = {}

    def _ensure_carrier(cid: str, name: str, carrier_type: str='FUEL', cost: float | None=None, co2: float | None=None) -> None:
        if cid and cid not in model.entities.get('Carrier', {}):
            model.add_entity(entity_class='Carrier', entity_id=cid)
        if cid:
            _safe_attr(cid, 'name', name)
            if cost is not None:
                _safe_attr(cid, 'energy_carrier_cost', cost)
            if co2 is not None:
                _safe_attr(cid, 'co2_emission_intensity', co2)

    def _safe_attr(entity_id: str, attr: str, value, unit: str | None=None) -> None:
        if value is None:
            return
        try:
            if unit is None:
                model.add_attribute(entity_id, attr, value)
            else:
                model.add_attribute(entity_id, attr, value, unit=unit)
        except KeyError:
            return

    def _safe_rel(entity_id: str, rel: str, target: str | None) -> None:
        if not target:
            return
        try:
            model.add_relation(entity_id, rel, target)
        except KeyError:
            return

    def _ensure_resource(rid: str, name: str | None=None) -> None:
        if rid and rid not in model.entities.get('NaturalResource', {}):
            model.add_entity(entity_class='NaturalResource', entity_id=rid)
        if rid:
            _safe_attr(rid, 'name', name or rid)

    def _ensure_generator_type(tid: str | None) -> None:
        if not tid:
            return
        if tid not in model.entities.get('GeneratorType', {}):
            model.add_entity(entity_class='GeneratorType', entity_id=tid)
        _safe_attr(tid, 'name', tid)

    def _ensure_storage_type(tid: str | None) -> None:
        if not tid:
            return
        if tid not in model.entities.get('StorageType', {}):
            model.add_entity(entity_class='StorageType', entity_id=tid)
        _safe_attr(tid, 'name', tid)

    def _ensure_timestamp_series(ts_id: str='timestamps.hourly_8760') -> None:
        if ts_id not in model.entities.get('TimestampSeries', {}):
            model.add_entity(entity_class='TimestampSeries', entity_id=ts_id)
        _safe_attr(ts_id, 'name', ts_id)
        _safe_attr(ts_id, 'start_datetime', '2020-01-01T00:00:00Z')
        _safe_attr(ts_id, 'resolution', 'PT1H')
        _safe_attr(ts_id, 'length', 8760)
        _safe_attr(ts_id, 'timezone', 'UTC')

    def _ensure_profile(pid: str | None) -> None:
        if not pid:
            return
        if pid not in model.entities.get('Profile', {}):
            model.add_entity(entity_class='Profile', entity_id=pid)
        _safe_attr(pid, 'name', pid)
        _safe_attr(pid, 'profile_type', 'as_normalized_annual_energy')
        _safe_attr(pid, 'data_reference', f'/profiles/{pid}/values')
        _ensure_timestamp_series()
        _safe_rel(pid, 'hasTimestampSeries', 'timestamps.hourly_8760')

    def _carrier_or_resource_from_flexeco(el: dict) -> tuple[str | None, str | None]:
        """Return (energy_carrier_id, natural_resource_id) for a FlexECO element."""
        key = _technology_key_from_flexeco(el)
        carrier = str(el.get('carrier', '')).strip().lower()
        if any((x in key for x in ('wind',))) or carrier in ('wind', 'c_wind'):
            return (None, 'resource.renewable.wind')
        if any((x in key for x in ('solar', 'pv', 'photovoltaic', 'csp'))) or carrier in ('solar', 'pv', 'c_pv'):
            return (None, 'resource.renewable.solar')
        if 'hydrogen' in key or carrier in ('hydrogen', 'c_hydrogen'):
            return ('carrier.hydrogen', None)
        if any((x in key for x in ('hydro', 'reservoir', 'pondage', 'run_of_river', 'pump_storage', 'phs'))) or carrier in ('water', 'hydro', 'ror', 'phs', 'c_water'):
            return (None, 'resource.water')
        if carrier in _FC_MAP:
            cid = _FC_MAP[el['carrier']].lower()
            if cid in ('c_water', 'c_wind', 'c_pv'):
                return (None, {'c_water': 'resource.water', 'c_wind': 'resource.renewable.wind', 'c_pv': 'resource.renewable.solar'}[cid])
            return (cid, None)
        if 'technology' in el:
            cid = _TECH_CARRIER_MAP.get(str(el['technology']).lower())
            if cid in ('c_water', 'c_wind', 'c_pv'):
                return (None, {'c_water': 'resource.water', 'c_wind': 'resource.renewable.wind', 'c_pv': 'resource.renewable.solar'}[cid])
            return (cid, None)
        return (None, None)
    for _rid, _name in (('resource.water', 'water'), ('resource.renewable.wind', 'wind'), ('resource.renewable.solar', 'solar irradiation')):
        _ensure_resource(_rid, _name)
    with european_json.open() as f:
        data = json.load(f)
    elements = data['PowerSystemElements']
    data_profiles: dict[str, np.ndarray] = {}
    mat_data = None
    for el in elements:
        if el.get('class') not in ('PN_GenDispatchable', 'PN_GenNonDispatchable', 'PN_StorageDam', 'PN_StoragePump', 'PN_StoragePumpNoInfeed'):
            continue
        carrier_id = None
        if 'carrier' in el and el['carrier'] in _FC_MAP:
            carrier_id = _FC_MAP[el['carrier']].lower()
        elif 'technology' in el:
            tech = el['technology'].lower()
            for kw, cid in [('hard coal', 'c_hard_coal'), ('lignite', 'c_lignite'), ('biofuel', 'c_biofuel'), ('waste', 'c_biofuel'), ('heavy_oil', 'c_heavy_oil'), ('gas', 'c_gas'), ('oil_shale', 'c_shale_oil'), ('light_oil', 'c_light_oil'), ('oil', 'c_oil'), ('pv', 'c_pv'), ('solar_photovoltaic', 'c_pv'), ('solar_thermal', 'c_pv'), ('wind', 'c_wind'), ('nuclear', 'c_nuclear'), ('hydrogen', 'c_hydrogen'), ('reservoir', 'c_water'), ('run_of_river', 'c_water'), ('pump_storage', 'c_water'), ('hydro', 'c_water'), ('pondage', 'c_water'), ('others_renewable', 'c_others_renewable'), ('others_non_renewable', 'c_others_non_renewable'), ('battery_storage', 'carrier.electricity'), ('demand_side_response', 'carrier.electricity'), ('adequacy', 'carrier.electricity'), ('geothermal', 'c_geothermal')]:
                if kw in tech:
                    carrier_id = cid
                    break
        if carrier_id:
            carrier_id = carrier_id.lower()
            if carrier_id in ('c_water', 'c_wind', 'c_pv'):
                _ensure_resource({'c_water': 'resource.water', 'c_wind': 'resource.renewable.wind', 'c_pv': 'resource.renewable.solar'}[carrier_id])
                if 'technology' in el:
                    _TECH_CARRIER_MAP[el['technology'].lower()] = carrier_id
                continue
            name = carrier_id[2:] if carrier_id.startswith('c_') else carrier_id
            cost = el.get('xi_c1')
            co2 = el.get('MWh_to_tons_co2')
            _ensure_carrier(carrier_id, name, cost=cost, co2=co2)
            if 'has_co2' in el and el['has_co2']:
                _safe_attr('EnergySystemModel', 'co2_price', el.get('co2_c1', 0.0))
            if 'technology' in el:
                _TECH_CARRIER_MAP[el['technology'].lower()] = carrier_id
    for el in elements:
        if el.get('class') != 'PN_Busbar':
            continue
        region = el.get('zone_name') or el.get('country') or 'region_europe'
        subregion = el.get('nuts2_id')
        if region not in model.entities.get('GeographicalRegion', {}):
            model.add_entity(entity_class='GeographicalRegion', entity_id=region)
            model.add_attribute(region, 'name', region)
        if subregion and subregion not in model.entities.get('GeographicalRegion', {}):
            model.add_entity(entity_class='GeographicalRegion', entity_id=subregion)
            model.add_attribute(subregion, 'name', subregion)
            model.add_relation(subregion, 'isSubRegionOf', region)
    bus_uid_to_id: dict[int, str] = {}
    for el in elements:
        if el.get('class') != 'PN_Busbar':
            continue
        uid = el['uid']
        bus_id = f'node_{uid}'
        region = el.get('zone_name') or el.get('country') or 'region_europe'
        model.add_entity(entity_class='ElectricalBus', entity_id=bus_id)
        model.add_attribute(bus_id, 'name', el.get('name'))
        model.add_attribute(bus_id, 'nominal_voltage', el.get('Un'))
        model.add_relation(bus_id, 'belongsToCarrierDomain', _DOMAIN_ID)
        model.add_relation(bus_id, 'locatedIn', region)
        bus_uid_to_id[uid] = bus_id

    def _node_id(bus_uid: int | str) -> str:
        return bus_uid_to_id.get(int(bus_uid), f'node_{bus_uid}')
    for el in elements:
        cls = el.get('class')
        if cls in ('PN_Line', 'PN_TR2', 'PN_HVDC', 'PN_NTC'):
            uid = el['uid']
            frm_id = _node_id(el['bus1_uid'])
            to_id = _node_id(el['bus2_uid'])
            if cls == 'PN_Line':
                eid = f'line_{uid}'
                model.add_entity(entity_class='TransmissionLine', entity_id=eid)
                model.add_attribute(eid, 'name', el.get('name'))
                frm_id = bus_uid_to_id.get(int(el['bus1_uid']))
                to_id = bus_uid_to_id.get(int(el['bus2_uid']))
                model.add_relation(eid, 'fromNode', frm_id)
                model.add_relation(eid, 'toNode', to_id)
                model.add_attribute(eid, 'from_switch_closed', el.get('side1_on', 1))
                model.add_attribute(eid, 'to_switch_closed', el.get('side2_on', 1))
                model.add_attribute(eid, 'series_resistance_per_km', el.get('r', 0.0))
                model.add_attribute(eid, 'series_reactance_per_km', el.get('x', 0.1))
                model.add_attribute(eid, 'shunt_susceptance_per_km', el.get('b', 0.1))
                model.add_attribute(eid, 'line_length', el.get('Length', 1.0))
                model.add_attribute(eid, 'thermal_capacity_rating', el.get('Smax', 0.0))
            elif cls == 'PN_TR2':
                eid = f'tr2_{uid}'
                model.add_entity(entity_class='Transformer', entity_id=eid)
                model.add_attribute(eid, 'name', el.get('name'))
                model.add_relation(eid, 'fromNode', frm_id)
                model.add_relation(eid, 'toNode', to_id)
                model.add_attribute(eid, 'from_switch_closed', el.get('side1_on', 1))
                model.add_attribute(eid, 'to_switch_closed', el.get('side2_on', 1))
                model.add_attribute(eid, 'thermal_capacity_rating', el.get('SR', 0.0))
                model.add_attribute(eid, 'rated_primary_voltage', el.get('UR1', 0.0))
                model.add_attribute(eid, 'rated_secondary_voltage', el.get('UR2', 0.0))
                model.add_attribute(eid, 'short_circuit_voltage_in_percentage', el.get('Usc', 0.0))
            elif cls == 'PN_HVDC':
                eid = f'hvdc_{uid}'
                model.add_entity(entity_class='HVDCLink', entity_id=eid)
                model.add_attribute(eid, 'name', el.get('name'))
                model.add_relation(eid, 'fromNode', frm_id)
                model.add_relation(eid, 'toNode', to_id)
                if el.get('Pmax') is not None:
                    model.add_attribute(eid, 'p_max_hvdc', el['Pmax'])
                if el.get('Pmin') is not None:
                    model.add_attribute(eid, 'p_min_hvdc', el['Pmin'])
            elif cls == 'PN_NTC':
                eid = f'ntc_{uid}'
                model.add_entity(entity_class='Interconnector', entity_id=eid)
                model.add_attribute(eid, 'name', el.get('name'))
                model.add_relation(eid, 'fromNode', frm_id)
                model.add_relation(eid, 'toNode', to_id)
                if el.get('P1max') is not None:
                    model.add_attribute(eid, 'maximum_power_flow_from_to', el['P1max'])
                    model.add_attribute(eid, 'maximum_power_flow_to_from', el.get('P2max', el['P1max']))
        elif cls in ('PN_Load', 'PN_LoadFlexible'):
            uid = el['uid']
            dem_id = f'load_{uid}'
            bus_id = _node_id(el['busuid'])
            model.add_entity(entity_class='DemandUnit', entity_id=dem_id)
            model.add_attribute(dem_id, 'name', el.get('name'))
            model.add_relation(dem_id, 'atNode', bus_id)
            model.add_attribute(dem_id, 'annual_energy_demand', el.get('profile_factor', 0.0))
            model.add_relation(dem_id, 'hasDemandProfile', el.get('xi_ref_profile', ''))
            _set_profile_type_from_factor(model, el.get('xi_ref_profile'), el.get('profile_factor_type'))
            model.add_attribute(dem_id, 'value_of_lost_load', -el.get('w_c1', -10000.0))
            model.add_attribute(dem_id, 'variable_operating_cost', el.get('u_load_c1', 0.0))
            if el.get('technology') is not None:
                model.add_attribute(dem_id, 'demand_type', el.get('technology'))
            if el.get('u_load_max') is not None:
                model.add_attribute(dem_id, 'maximum_energy_demand', el['u_load_max'])
            if cls == 'PN_LoadFlexible':
                model.add_attribute(dem_id, 'is_demand_flexible', True)
                model.add_attribute(dem_id, 'flexibility_window_time_start', el.get('T0', 0.0))
                model.add_attribute(dem_id, 'flexibility_window_time_end', el.get('T1', 0.0))
                model.add_attribute(dem_id, 'flexibility_time_resolution', el.get('TP', 0.0))
            ts_key = el.get('xi_ref_profile', '')
            ds_main = f'DemandUnit/{dem_id}/profile'
            ret, arr, mat_data = add_profile(el, 1, mat_data)
            if ret:
                data_profiles[ds_main] = arr
                if ts_key:
                    data_profiles[f'profiles/{ts_key}'] = arr
        elif cls in ('PN_StoragePumpNoInfeed', 'PN_StoragePump', 'PN_StorageDam'):
            uid = el['uid']
            prefix = 'storage_pump_' if cls != 'PN_StorageDam' else 'storage_dam_'
            sid = f'{prefix}{uid}'
            bus_id = _node_id(el['busuid'])
            stor_cls = _storage_asset_class_from_flexeco(cls, el)
            model.add_entity(entity_class=stor_cls, entity_id=sid)
            _safe_attr(sid, 'name', el.get('name'))
            is_hydro_res = stor_cls == 'ReservoirStorageUnit'
            carrier_id, resource_id = _carrier_or_resource_from_flexeco(el)
            if is_hydro_res:
                resource_id = resource_id or 'resource.water'
                _ensure_resource(resource_id)
                _safe_rel(sid, 'storesResource', resource_id)
            elif carrier_id:
                _ensure_carrier(carrier_id, carrier_id[2:] if carrier_id.startswith('c_') else carrier_id)
                _safe_rel(sid, 'storesCarrier', carrier_id)
            else:
                _safe_rel(sid, 'storesCarrier', _CARRIER_ID)
            if cls == 'PN_StoragePump':
                storage_tech = 'Storage.Hydro.PumpedStorage.OpenLoopReservoir'
                hydro_tech = 'Generation.Renewable.Hydro.PHS.OpenLoop'
            elif cls == 'PN_StoragePumpNoInfeed':
                storage_tech = 'Storage.Hydro.PumpedStorage.ClosedLoopReservoir'
                hydro_tech = 'Generation.Renewable.Hydro.PHS.ClosedLoop'
            elif 'pondage' in _technology_key_from_flexeco(el):
                storage_tech = 'Storage.Hydro.PondageReservoir'
                hydro_tech = 'Generation.Renewable.Hydro.Pondage'
            else:
                storage_tech = 'Storage.Hydro.Reservoir'
                hydro_tech = 'Generation.Renewable.Hydro.Reservoir'
            if is_hydro_res:
                _ensure_storage_type(storage_tech)
                _safe_rel(sid, 'hasTechnology', storage_tech)
            model.add_relation(sid, 'atNode', bus_id)
            if el.get('technology') is not None:
                _safe_attr(sid, 'storage_technology_type', el.get('technology'))
            if el.get('xi_c1') is not None:
                _safe_attr(_CARRIER_ID, 'energy_carrier_cost', el.get('xi_c1'))
            if is_hydro_res:
                _safe_attr(sid, 'energy_storage_capacity', el.get('Capacity', 0.0))
                gen_id = f'generator.hydro.{sid}'
                if gen_id not in model.entities.get('HydroGenerationUnit', {}):
                    model.add_entity(entity_class='HydroGenerationUnit', entity_id=gen_id)
                    _safe_attr(gen_id, 'name', f'hydro generation for {sid}')
                    if cls in ('PN_StoragePump', 'PN_StoragePumpNoInfeed'):
                        _safe_attr(gen_id, 'turbine_type', 'reversible_francis')
                    _ensure_generator_type(hydro_tech)
                    _safe_rel(gen_id, 'hasTechnology', hydro_tech)
                    _safe_rel(gen_id, 'hasInputResource', 'resource.water')
                    _safe_rel(gen_id, 'hasOutputCarrier', _CARRIER_ID)
                    _safe_rel(gen_id, 'drawsFromReservoir', sid)
                    _safe_rel(sid, 'suppliesResourceTo', gen_id)
                    model.add_relation(gen_id, 'atNode', bus_id)
                _safe_attr(gen_id, 'machine_role', hydro_machine_role(hydro_tech))
                _safe_attr(gen_id, 'dispatch_type', 'dispatchable')
                _safe_attr(gen_id, 'nominal_power_capacity', el.get('u_gen_max', 0.0))
                _safe_attr(gen_id, 'turbine_efficiency', el.get('eta_gen', 0.9))
                if cls in ('PN_StoragePump', 'PN_StoragePumpNoInfeed'):
                    _safe_attr(gen_id, 'maximum_pumping_power', el.get('u_load_max', 0.0))
                    _safe_attr(gen_id, 'pumping_efficiency', el.get('eta_load', 0.82))
                if el.get('u_gen_c1') is not None:
                    _safe_attr(gen_id, 'variable_operating_cost', el.get('u_gen_c1', 0.0))
            else:
                _safe_attr(sid, 'charging_efficiency', el.get('eta_load', 1.0))
                _safe_attr(sid, 'discharging_efficiency', el.get('eta_gen', 1.0))
                _safe_attr(sid, 'nominal_power_capacity', el.get('u_gen_max', 0.0))
                _safe_attr(sid, 'maximum_charging_power', el.get('u_load_max', 0.0))
                _safe_attr(sid, 'variable_operating_cost', el.get('u_gen_c1', 0.0))
                _safe_attr(sid, 'charging_variable_operating_cost', el.get('u_load_c1', 0.0))
                _safe_attr(sid, 'energy_storage_capacity', el.get('Capacity', 0.0))
            ts_key = el.get('xi_ref_profile', '')
            if is_hydro_res and (el.get('has_inflow') or cls == 'PN_StorageDam' or ts_key):
                if ts_key:
                    _ensure_profile(ts_key)
                    _safe_rel(sid, 'hasNaturalInflowProfile', ts_key)
                    _set_profile_type_from_factor(model, ts_key, el.get('profile_factor_type'))
                inflow = el.get('profile_factor', 0.0)
                _safe_attr(sid, 'annual_natural_inflow_energy', inflow)
                ret, arr, mat_data = add_profile(el, 1, mat_data)
                if ret:
                    data_profiles[f'StorageUnit/{sid}/inflow'] = arr
                    if ts_key:
                        data_profiles[f'profiles/{ts_key}'] = arr
            if el.get('du_gen_up_max') is not None:
                _safe_attr(sid, 'maximum_ramp_rate_up', el['du_gen_up_max'])
            if el.get('du_gen_down_max') is not None:
                _safe_attr(sid, 'maximum_ramp_rate_down', el.get('du_gen_down_max'))
            if el.get('du_gen_up_c1') is not None:
                _safe_attr(sid, 'ramping_cost_increase', el.get('du_gen_up_c1'))
            if el.get('du_gen_down_c1') is not None:
                _safe_attr(sid, 'ramping_cost_decrease', el.get('du_gen_down_c1'))
        elif cls in ('PN_GenDispatchable', 'PN_GenNonDispatchable'):
            uid = el['uid']
            gid = f'gen_{uid}'
            bus_id = _node_id(el['busuid'])
            gen_cls = _generation_asset_class_from_flexeco(el)
            model.add_entity(entity_class=gen_cls, entity_id=gid)
            _safe_attr(gid, 'name', el.get('name'))
            tech_id = el.get('technology')
            if tech_id:
                _ensure_generator_type(tech_id)
                _safe_rel(gid, 'hasTechnology', tech_id)
            carrier_id, resource_id = _carrier_or_resource_from_flexeco(el)
            if resource_id:
                _ensure_resource(resource_id)
                _safe_rel(gid, 'hasInputResource', resource_id)
            elif carrier_id:
                _ensure_carrier(carrier_id, carrier_id[2:] if carrier_id.startswith('c_') else carrier_id)
                _safe_rel(gid, 'hasInputCarrier', carrier_id)
            _safe_rel(gid, 'hasOutputCarrier', _CARRIER_ID)
            model.add_relation(gid, 'atNode', bus_id)
            if gen_cls == 'HydroGenerationUnit':
                _safe_attr(gid, 'machine_role', hydro_machine_role(tech_id or el.get('name')))
                _safe_attr(gid, 'turbine_efficiency', el.get('eta_gen', 1.0))
            else:
                _safe_attr(gid, 'energy_conversion_efficiency', hydrogen_generation_efficiency(el.get('carrier'), tech_id, el.get('eta_gen', 1.0)))
            if tech_id:
                _safe_attr(gid, 'generator_technology_type', tech_id)
            if el.get('xi_c1') is not None and carrier_id:
                _safe_attr(carrier_id, 'energy_carrier_cost', el.get('xi_c1'))
            _safe_attr(gid, 'nominal_power_capacity', el.get('u_gen_max', 0.0))
            _safe_attr(gid, 'variable_operating_cost', el.get('u_gen_c1', 0.0))
            if el.get('du_gen_up_max') is not None:
                _safe_attr(gid, 'maximum_ramp_rate_up', el['du_gen_up_max'])
            if el.get('du_gen_down_max') is not None:
                _safe_attr(gid, 'maximum_ramp_rate_down', el.get('du_gen_down_max'))
            if el.get('du_gen_up_c1') is not None:
                _safe_attr(gid, 'ramping_cost_increase', el.get('du_gen_up_c1'))
            if el.get('du_gen_down_c1') is not None:
                _safe_attr(gid, 'ramping_cost_decrease', el.get('du_gen_down_c1'))
            if cls == 'PN_GenNonDispatchable':
                ts_key = el.get('xi_ref_profile', '')
                ds_main = f'GenerationUnit/{gid}/availability'
                _ensure_profile(ts_key)
                _set_profile_type_from_factor(model, ts_key, el.get('profile_factor_type'))
                if gen_cls == 'HydroGenerationUnit':
                    _safe_attr(gid, 'annual_run_of_river_inflow_energy', el.get('profile_factor', 0.0))
                    _safe_attr(gid, 'annual_resource_potential', el.get('profile_factor', 0.0))
                    _safe_rel(gid, 'hasRunOfRiverInflowProfile', ts_key)
                else:
                    _safe_attr(gid, 'annual_resource_potential', el.get('profile_factor', 0.0))
                    _safe_rel(gid, 'hasAvailabilityProfile', ts_key)
                ret, arr, mat_data = add_profile(el, 1, mat_data)
                if ret:
                    data_profiles[ds_main] = arr
                    if ts_key:
                        data_profiles[f'profiles/{ts_key}'] = arr
            else:
                _safe_attr(gid, 'annual_resource_potential', 0.0)
    return (data_profiles, model)
if __name__ == '__main__':
    schema_dir = Path('../schemas/cesdm')
    european_json = Path('RRE_EU_with_profiles.jpn')
    data_timeseries, m = import_from_flexeco(schema_dir, european_json)
    errors = m.validate()
    print(f'Validation errors: {len(errors)}')
    for e in errors:
        print(' -', e)
    m.export_yaml_hierarchical('european_system_hierarchical.yaml')
    m.export_yaml('european_system.yaml')
    m.export_hdf5('european_system.h5', values_map=data_timeseries)
    print('Exported YAML (hierarchical + flat) and HDF5 (CESDM format).')
    m.export_json('european_system.json')
    m2: CesdmModel = build_model_from_yaml(schema_dir)
    m2.import_json('european_system.json')
    errors2 = m2.validate()
    print(f'Round-trip validation errors: {len(errors2)}')
    _attach_profile_values(m2, data_timeseries)
    export_to_flexeco(m2, 'european_system_flexeco.jpn', hdf5_path='european_system_flexeco/profiles/profiles.h5')
    print('Exported FlexEco .jpn + HDF5 profile file.')
    m2.export_csv_by_class_wide('outputs/by_class_wide')
