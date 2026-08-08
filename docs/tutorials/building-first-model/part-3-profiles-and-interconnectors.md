# Part 3: Profiles and Interconnectors

!!! info "Checkpoint"
    After Part 3 you should have explicit `Profile` entities, reservoir hydro, and `Interconnector` assets.

## 9. Create a Profile explicitly

Renewable generators often need an availability profile. Create the `Profile` entity and link it to the generator and shared time axis:

```python
timestamps = model.get_entity("ts.hourly.2030")

for generator_id in ("gen.ch.wind", "gen.ch.solar"):
    profile_id = f"profile.{generator_id}.capacity_factor"
    profile = model.add_entity("Profile", profile_id)
    profile.profile_type = "as_capacity_factor"
    profile.profile_unit = "pu"
    profile.data_reference = f"/profiles/{profile_id}"
    profile.hasTimestampSeries = timestamps
    model.get_entity(generator_id).hasAvailabilityProfile = profile
```

This makes the semantic chain visible:

```text
GenerationUnit
    └── hasAvailabilityProfile
            └── Profile
                    └── hasTimestampSeries
                            └── TimestampSeries
```

The numerical array is stored separately at the location identified by `data_reference`.

!!! abstract "Core EAR alternative"

    ```python
    profile_id = "profile.gen.ch.wind.capacity_factor"

    model.add_entity(entity_class="Profile", entity_id=profile_id)
    model.add_attribute(
        entity_id=profile_id,
        attribute_id="profile_type",
        value="as_capacity_factor",
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=profile_id,
        attribute_id="profile_unit",
        value="pu",
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=profile_id,
        attribute_id="data_reference",
        value=f"/profiles/{profile_id}",
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id=profile_id,
        relation_id="hasTimestampSeries",
        target_entity_id="ts.hourly.2030",
    )
    model.add_relation(
        entity_id="gen.ch.wind",
        relation_id="hasAvailabilityProfile",
        target_entity_id=profile_id,
    )
    ```

---

## 10. Represent reservoir hydro

Reservoir storage and hydro generation are separate physical entities connected by explicit relations:

```python
bus_ch = model.get_entity("bus.ch")

reservoir = model.add_entity(
    "ReservoirStorageUnit",
    "storage.ch.hydro.reservoir",
)
reservoir.name = "CH Alpine seasonal reservoir"
reservoir.energy_storage_capacity = (8_800_000, "MWh")
reservoir.annual_natural_inflow_energy = (20_000_000, "MWh/year")
reservoir.storesResource = "resource.water"

hydro = model.add_entity("HydroGenerationUnit", "gen.ch.hydro.reservoir")
hydro.name = "CH Reservoir hydro turbines"
hydro.machine_role = "turbine"
hydro.nominal_power_capacity = (8_000, "MW")
hydro.hasTechnology = "Generation.Renewable.Hydro.Reservoir"
hydro.hasInputResource = "resource.water"
hydro.atNode = bus_ch
hydro.drawsFromReservoir = reservoir
reservoir.suppliesResourceTo = hydro
```

The model preserves the distinction between:

- the reservoir that stores water and energy;
- the turbine that converts the resource into electricity;
- the relations that describe their physical association.

Add a natural-inflow profile for the reservoir:

```python
inflow_profile = model.add_entity(
    "Profile",
    "profile.storage.ch.hydro.reservoir.inflow",
)
inflow_profile.profile_type = "as_normalized_annual_energy"
inflow_profile.profile_unit = "pu"
inflow_profile.data_reference = (
    "/profiles/profile.storage.ch.hydro.reservoir.inflow"
)
inflow_profile.hasTimestampSeries = model.get_entity("ts.hourly.2030")
reservoir.hasNaturalInflowProfile = inflow_profile
```

---

## 11. Add interconnectors

Use explicit topology relations:

```python
interconnectors = [
    ("ntc.ch.de", "CH-DE NTC", "bus.ch", "bus.de", 6_000, 5_500),
    ("ntc.ch.fr", "CH-FR NTC", "bus.ch", "bus.fr", 4_000, 3_500),
    ("ntc.ch.it", "CH-IT NTC", "bus.ch", "bus.it", 5_000, 4_500),
    ("ntc.ch.at", "CH-AT NTC", "bus.ch", "bus.at", 2_000, 2_000),
]

for (
    interconnector_id,
    name,
    from_bus,
    to_bus,
    capacity_from_to,
    capacity_to_from,
) in interconnectors:
    interconnector = model.add_entity("Interconnector", interconnector_id)
    interconnector.name = name
    interconnector.maximum_power_flow_from_to = (capacity_from_to, "MW")
    interconnector.maximum_power_flow_to_from = (capacity_to_from, "MW")
    interconnector.fromNode = model.get_entity(from_bus)
    interconnector.toNode = model.get_entity(to_bus)
```

The direction of the connection and both directional transfer capacities are explicit in the model.

!!! abstract "Core EAR alternative"

    ```python
    model.add_entity(entity_class="Interconnector", entity_id="ntc.ch.de")
    model.add_attribute(
        entity_id="ntc.ch.de",
        attribute_id="name",
        value="CH-DE NTC",
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id="ntc.ch.de",
        attribute_id="maximum_power_flow_from_to",
        value=6000,
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id="ntc.ch.de",
        attribute_id="maximum_power_flow_to_from",
        value=5500,
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id="ntc.ch.de",
        relation_id="fromNode",
        target_entity_id="bus.ch",
    )
    model.add_relation(
        entity_id="ntc.ch.de",
        relation_id="toNode",
        target_entity_id="bus.de",
    )
    ```

---

## Navigation

← Previous: [Part 2](part-2-demand-and-generation.md)  
→ Next: [Part 4 — Multi-carrier and Export](part-4-multicarrier-and-export.md)
