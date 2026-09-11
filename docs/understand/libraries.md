# Libraries

In the [first model](../get-started/first-model.md) you did not define “what onshore wind is”. You pointed at a shared technology:

```python
model.import_library("library/default_library")
model.import_library("library/regions_library")

wind.hasTechnology = GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE
bus.belongsToGeographicalRegion = model.get_entity("region.country.CH")
```

A **library** is a CESDM model full of reusable objects: technologies, carriers, resources, regions. A **schema** says which types may exist. The library provides commonly used instances of those types.

| | Schema | Library | Your study |
|---|---|---|---|
| Role | Allowed types and fields | Shared catalogue | This system |
| Example | `GenerationUnit` may have `hasTechnology` | onshore-wind technology | `gen.demo.wind` at 500 MW |

Site-specific facts (this plant’s MW, this bus) stay on your objects. Shared defaults (typical efficiency, input carrier) stay on the library technology.

```text
library/default_library/
├── carriers/
├── domains/            # electricity, gas, heat, hydrogen
├── resources/
├── generator_types/
└── storage_types/

library/regions_library/
├── geographical_regions/   # region.country.CH, …
└── market_zones/
```

Import the default library first; regions second (zones refer to electricity). Optional TYNDP generator types: `library/tyndp_library/` after the default library.

When you export, `include_library="referenced"` (the default) writes only the library objects your study actually uses.

You can add a project library the same way: a CESDM YAML plus `import_library()`. Prefer `hasTechnology` over copying fields onto every plant.

## Next

[Carrier domains](carrier-domains.md) · [Profiles](profiles.md) · [Build models](../use/build-models.md)
