# Using the schema reference

The [schema reference](schema-reference.html) is the generated list of every class, attribute and relation in schema 1.0.0. It is built from three folders: `cesdm/schemas/base`, `cesdm/schemas/powerflow` and `cesdm/schemas/dynamics`. A field such as `powerflow_bus_type` appears on `ElectricalBus` because the power-flow package attaches it. Open the page from Reference when you need the exact name, unit or target of something you are about to write. The pages in Guides explain the ideas. This page explains the HTML.

## Find a name

The box at the top of the sidebar searches classes, attributes and relations together. Type `nominal_power_capacity`. The line under the box counts the matches, and each match is a class that carries that field. Choose `GenerationUnit`.

The card shows the class name, a link to its parent, and a short description. The table row gives the type (`decimal`), the limits (`min 0.0`) and the unit (`MW`). That unit list is what `add_attribute` accepts. A value in `TWh` is refused because `TWh` is not in the list.

## Read the marks

The legend at the top of the page has three marks.

- **required** means the field must be present for the class to be valid.
- **inherited** means the field is defined on a parent. The row is dimmed. Follow the parent link to see where it comes from. `HydroGenerationUnit` inherits `nominal_power_capacity` from `GenerationUnit`.
- **abstract** means you do not create objects of that class. Abstract names are italic in the sidebar. `EnergyAssetInstance` is abstract. `HydroGenerationUnit` is not.

Two checkboxes narrow the list. **Hide abstract classes** leaves the classes an adapter actually writes. **Show only entities with attributes or relations** drops empty headings.

**Technical**, **Dispatch**, **Power flow** and **Dynamic** choose what the page shows. The page opens with Technical and Dispatch on. Those two are the base schema, `cesdm/schemas/base`. A field such as `nominal_power_capacity` is marked Dispatch. `tilt_angle` on `SolarGenerationUnit` is marked Technical. Clearing Dispatch hides the dispatch rows and leaves the class, its technical fields, and every field that belongs to neither group. A field marked with both, such as `electrical_efficiency` on `CHPUnit`, stays while either box is ticked. Clearing both hides the base classes. Tick **Power flow** and `powerflow_bus_type` appears on `ElectricalBus`, together with classes such as `ShuntUnit`. Tick **Dynamic** for the controllers and `usesDynamicModelType`.

## Attributes and relations

An attribute row is a value: a number, a string, or an enumeration such as `dispatchable | nondispatchable | must_run`. A relation row is a link. It names the class at the other end. `drawsFromHydroReservoir` on `HydroGenerationUnit` points at `HydroReservoir`.

The same attribute can appear on several classes. The **Attribute catalogue** tab lists it once and shows every class that uses it. The **Relation catalogue** does the same for links. Use those tabs when you know the field name and not yet the class.

## Which tab

| Tab | What you look up |
|---|---|
| Assets | Plants, storage, demand, conversion |
| Network & Carriers | Buses, lines, transformers, carriers |
| Domain & Types | Technology types, profiles, regions, other shared objects |
| Attribute catalogue | One attribute across classes |
| Relation catalogue | One link across classes |

## One lookup from the tutorial

Group A's hydro plant has an efficiency of 0.9. Search `efficiency`. `GenerationUnit` has `energy_conversion_efficiency`, a fraction from 0 to 1. `HydroGenerationUnit` also has `turbine_efficiency`. The tutorial writes `energy_conversion_efficiency` on the plant. Both names, both units and both classes are on the card before any code is written.
