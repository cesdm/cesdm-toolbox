# Part 2: Demand and Generation

!!! info "Checkpoint"
    After Part 2 you should have demand units, a `[TimestampSeries](../../community/glossary.md#timestamp-series)`, library resources, and at least one `GenerationUnit`.

## 5. Add demand

```python
demands = [
    ("dem.ch", "CH electricity demand", 60_000, "bus.ch"),
    ("dem.de", "DE electricity demand", 500_000, "bus.de"),
    ("dem.fr", "FR electricity demand", 450_000, "bus.fr"),
    ("dem.it", "IT electricity demand", 300_000, "bus.it"),
    ("dem.at", "AT electricity demand", 70_000, "bus.at"),
]

for demand_id, name, annual_gwh, bus_id in demands:
    demand = model.add_entity("DemandUnit", demand_id)
    demand.name = name
    demand.annual_energy_demand = (annual_gwh * 1000, "MWh/year")
    demand.atNode = model.get_entity(bus_id)
```

The demand entity remains independent of a particular dispatch tool. Its annual demand and network location are part of the common system representation.

!!! abstract "Core EAR alternative"

    ```python
    model.add_entity(entity_class="DemandUnit", entity_id="dem.ch")
    model.add_attribute(
        entity_id="dem.ch",
        attribute_id="name",
        value="CH electricity demand",
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id="dem.ch",
        attribute_id="annual_energy_demand",
        value=60_000_000,
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id="dem.ch",
        relation_id="atNode",
        target_entity_id="bus.ch",
    )
    ```

---

## 6. Define the shared time axis

A `[TimestampSeries](../../community/glossary.md#timestamp-series)` is also an ordinary CESDM entity:

```python
timestamps = model.add_entity("TimestampSeries", "ts.hourly.2030")
timestamps.name = "Hourly, 2030"
timestamps.start_datetime = "2030-01-01T00:00:00"
timestamps.resolution = "PT1H"
timestamps.length = 8760
timestamps.timezone = "Europe/Zurich"
```

Several profiles can reference this one time axis.

---

## 7. Reuse natural resources from the Default Library

The imported [Default Library](../../community/glossary.md#default-library) already contains reusable resource entities such as:

```text
resource.renewable.wind
resource.renewable.solar
resource.water
```

The project model references these existing entities directly — they are not recreated. Add generators and link library resources or carriers as required:

```python
generators = [
    (
        "gen.ch.gas",
        "CH Gas CCGT",
        GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,
        3_000,
        "bus.ch",
        "thermal",
        None,
    ),
    (
        "gen.ch.nuc",
        "CH Nuclear",
        GeneratorTypes.GENERATION_THERMAL_NUCLEAR_STANDARD,
        2_000,
        "bus.ch",
        "nuclear",
        None,
    ),
    (
        "gen.ch.wind",
        "CH Wind",
        GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE,
        500,
        "bus.ch",
        "wind",
        900_000,
    ),
    (
        "gen.ch.solar",
        "CH Solar PV",
        GeneratorTypes.GENERATION_RENEWABLE_SOLAR_PV_UTILITY,
        2_000,
        "bus.ch",
        "solar",
        2_000_000,
    ),
]

for (
    generator_id,
    name,
    technology_id,
    capacity_mw,
    bus_id,
    family,
    annual_mwh,
) in generators:
    generator = model.add_entity("GenerationUnit", generator_id)
    generator.name = name
    generator.nominal_power_capacity = (capacity_mw, "MW")
    generator.hasTechnology = technology_id
    generator.atNode = model.get_entity(bus_id)

    if family == "thermal":
        generator.hasInputCarrier = Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
    elif family == "wind":
        generator.hasInputResource = "resource.renewable.wind"
    elif family == "solar":
        generator.hasInputResource = "resource.renewable.solar"

    if annual_mwh is not None:
        generator.annual_resource_potential = annual_mwh
```

The physical generator contains its asset-specific information. The reusable technology entity from the [Default Library](../../community/glossary.md#default-library) contains shared technology data such as dispatch classification, efficiency, costs, and carrier relations. The system model references that library entity instead of duplicating its content.

Variable renewables (wind, solar) receive availability profiles in [Part 3](part-3-profiles-and-interconnectors.md).

!!! abstract "Core EAR alternative"

    ```python
    model.add_entity(entity_class="GenerationUnit", entity_id="gen.ch.gas")
    model.add_attribute(
        entity_id="gen.ch.gas",
        attribute_id="name",
        value="CH Gas CCGT",
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id="gen.ch.gas",
        attribute_id="nominal_power_capacity",
        value=3000,
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id="gen.ch.gas",
        relation_id="hasTechnology",
        target_entity_id=GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,
    )
    model.add_relation(
        entity_id="gen.ch.gas",
        relation_id="hasInputCarrier",
        target_entity_id=Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS,
    )
    model.add_relation(
        entity_id="gen.ch.gas",
        relation_id="atNode",
        target_entity_id="bus.ch",
    )
    ```

---

## Navigation

← Previous: [Part 1](part-1-system-and-network.md)  
→ Next: [Part 3 — Profiles and Interconnectors](part-3-profiles-and-interconnectors.md)
