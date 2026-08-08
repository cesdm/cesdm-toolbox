"""cesdm.domain.model.builders — Entity construction and proxy wrapping

**The one rule for what belongs in this file**: generic, class-agnostic
construction/query infrastructure -- `add_entity()`/`get_entity()`/
`asset_as()` (proxy wrapping), `ensure_entity()`/`ensure_carrier()`/
`ensure_resource()`/`ensure_technology()` (create-if-missing by class
name), topology wiring
(`connect_single_port()`/`connect_two_port()`), and profile-attaching
helpers. Not a per-asset-type domain convenience wrapper -- those were
removed entirely (see CHANGELOG.md): building any model uses core EAR
calls (`add_entity()`/`add_attribute()`/`add_relation()`) plus this
proxy layer for reading/writing afterward.

Auto-extracted from the legacy monolithic module as part of the
package-hierarchy refactor (see docs/architecture/package_layout.md).
"""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional, TypeVar, Union
import os
import pathlib
import re
import yaml

from cesdm.proxy import EntityProxy, _entity_proxy

_T = TypeVar("_T", bound=EntityProxy)


class BuildersMixin:
    """Mixin — see module docstring for the responsibility this covers."""

    def add_entity(self, entity_class: str, entity_id: str) -> EntityProxy:
        """Create a new entity and return it wrapped in its
        schema-specific typed proxy directly -- e.g.
        `gen = model.add_entity("GenerationUnit", "gen1")` gives back a
        `GenerationUnitProxy` you can immediately do
        `gen.dispatch.nominal_power_capacity = 400` on, both at runtime
        and (via `@overload`/`Literal` in the generated stub) in your
        editor's autocomplete/type-checking too -- no `asset_as()` cast
        needed for the common "just created it" case.

        Overrides `ear.model.Model.add_entity()` (still returns the
        bare `ear.entity.Entity` dataclass there, unchanged -- a plain
        EAR domain has no proxy registry to wrap with at all). Asked
        directly why this couldn't "just happen" on `add_entity()`
        itself instead of a separate method: it can, once the return
        value is overridden at the CESDM layer specifically rather
        than the shared EAR primitive underneath it, which stays
        exactly as it was. See CHANGELOG.md.
        """
        super().add_entity(entity_class, entity_id)
        return _entity_proxy(self, entity_id)

    def get_entity(self, entity_id: str) -> EntityProxy:
        """Wrap an existing entity id in its schema-specific generated proxy
        (e.g. `DemandUnitProxy` for a `DemandUnit`), so code that created it
        via the low-level `add_entity()`/`ensure_entity()` calls can still
        use `.dispatch`, `.connect()`, `.add_attribute(...)`, etc. Falls
        back to plain `EntityProxy` if the entity's class has no generated
        proxy (or doesn't exist at all yet). `EntityProxy` is a `str`
        subclass, so `model.get_entity(x) == x` for any entity id `x`
        regardless of which specific proxy subclass wraps it -- wrapping is
        purely additive.

        Statically typed as returning plain `EntityProxy` even though the
        *runtime* value is more specific -- a type checker can't know
        which subclass a string id resolves to. If you need `.dispatch`
        etc. to type-check too (not just work at runtime), use
        `asset_as(entity_id, DemandUnitProxy)` instead, or Python's own
        `typing.cast(DemandUnitProxy, model.get_entity(entity_id))`.
        """
        return _entity_proxy(self, entity_id)

    def asset_as(self, entity_id: str, cls: type[_T] | tuple[type[_T], ...]) -> _T:
        """Like `get_entity()`, but statically typed as `cls` -- so
        `model.asset_as("dem.ch", DemandUnitProxy).dispatch...` type-checks
        correctly, not just works at runtime. Also checked at runtime: raises
        `TypeError` if the entity's actual class doesn't match `cls`, rather
        than silently handing back the wrong type the way a bare
        `typing.cast(...)` would (`cast` is purely a type-checker hint --
        zero runtime effect, so a wrong cast stays wrong until it fails
        somewhere else, confusingly, later). Prefer this over `cast()`
        whenever you're not certain the id is what you expect.

        `cls` can also be a tuple of classes (matching `isinstance()`'s own
        convention) for the recurring case of an entity that's genuinely
        one of several known classes depending on runtime data -- e.g. a
        CSV importer's storage-capacity column covers both `StorageUnit`
        and `ReservoirStorageUnit` rows generically. `.dispatch` etc. on
        the result still type-checks (against whichever of the listed
        classes actually declares it), since all of them share the same
        `EntityProxy`-derived shape.
        """
        proxy = self.get_entity(entity_id)
        if not isinstance(proxy, cls):
            names = cls.__name__ if isinstance(cls, type) else " or ".join(c.__name__ for c in cls)
            raise TypeError(f"{entity_id!r} is a {type(proxy).__name__}, not a {names}")
        return proxy


    def ensure_entity(self, class_name: str, entity_id: str, **attributes) -> EntityProxy:
        """Create an entity if missing and set valid scalar attributes.
        Returns the entity's class-specific generated proxy (e.g.
        `InterconnectorProxy` for `class_name="Interconnector"`), same as
        `asset()` -- this function already knows the exact class from its
        own `class_name` argument, so there's no reason to hand back only
        the generic base type.
        """
        existing = self.entity_class(entity_id)
        if existing:
            if existing != self._canonicalize_class(class_name):
                raise ValueError(f"Entity {entity_id!r} already exists as {existing}, not {class_name}")
        else:
            self.add_entity(class_name, entity_id)
        for key, val in attributes.items():
            self.set_attribute_if_allowed(entity_id, key, val)
        return _entity_proxy(self, entity_id)

    def ensure_carrier(self, carrier_id: str, *, name: str | None = None,
                       carrier_type: str | None = None, carrier_group: str | None = None) -> EntityProxy:
        """Create or update a Carrier. Returns the typed
        `CarrierProxy`, same as `ensure_entity()` itself --
        previously discarded that in favour of the bare id string,
        the one thing that made this genuinely differ from just
        calling `ensure_entity("Carrier", ...)` directly."""
        proxy = self.ensure_entity("Carrier", carrier_id, name=name)
        self.set_attribute_if_allowed(carrier_id, "carrier_type", carrier_type)
        self.set_attribute_if_allowed(carrier_id, "carrier_group", carrier_group)
        return proxy

    def ensure_resource(self, resource_id: str, *, name: str | None = None,
                        resource_type: str | None = None, resource_group: str | None = None,
                        unit: str | None = None) -> EntityProxy:
        """Create or update a NaturalResource. Returns the typed
        `NaturalResourceProxy`, same as `ensure_entity()` itself."""
        proxy = self.ensure_entity("NaturalResource", resource_id, name=name)
        self.set_attribute_if_allowed(resource_id, "resource_type", resource_type)
        self.set_attribute_if_allowed(resource_id, "resource_group", resource_group)
        self.set_attribute_if_allowed(resource_id, "natural_resource_unit", unit)
        return proxy

    def ensure_technology(self, technology_id: str, *, class_name: str = "GeneratorType",
                          name: str | None = None, **attributes) -> EntityProxy:
        """Create or update an EnergyTechnologyType subclass. Returns
        the typed proxy (e.g. `GeneratorTypeProxy`), same as
        `ensure_entity()` itself."""
        proxy = self.ensure_entity(class_name, technology_id, name=name or technology_id)
        for key, val in attributes.items():
            self.set_attribute_if_allowed(technology_id, key, val)
        return proxy

    def set_technology(self, asset_id: str, technology_id: str,
                       *, technology_class: str = "GeneratorType", **technology_attrs) -> bool:
        """Ensure a technology entity and link an asset via hasTechnology."""
        self.ensure_technology(technology_id, class_name=technology_class, **technology_attrs)
        return self.add_relation_if_allowed(asset_id, "hasTechnology", technology_id)


    def connect_single_port(self, asset_id: str, node_id: str, *, view_id: str | None = None) -> str:
        """Attach a single-port asset directly to a network node."""
        self.add_relation_if_allowed(asset_id, "atNode", node_id, strict=True)
        return asset_id

    def connect_two_port(self, asset_id: str, from_node_id: str, to_node_id: str,
                         *, view_id: str | None = None) -> str:
        """Attach a two-port asset directly to two network nodes."""
        if not self.add_relation_if_allowed(asset_id, "fromNode", from_node_id):
            self.add_relation_if_allowed(asset_id, "node_from", from_node_id, strict=False)
        if not self.add_relation_if_allowed(asset_id, "toNode", to_node_id):
            self.add_relation_if_allowed(asset_id, "node_to", to_node_id, strict=False)
        return asset_id


    def attach_profile(self, view_or_asset_id: str, relation_id: str, profile_id: str,
                       *, timestamp_series_id: str | None = None, create: bool = False,
                       profile_type: str = "as_capacity_factor", profile_unit: str | None = None,
                       data_reference: str | None = None) -> EntityProxy:
        """Attach a Profile to a view or to the first view of an asset that supports the relation."""
        if create:
            if timestamp_series_id is None:
                raise ValueError("timestamp_series_id is required when create=True")
            self.ensure_entity("Profile", profile_id, profile_type=profile_type,
                               profile_unit=profile_unit, data_reference=data_reference)
            self.add_relation_if_allowed(profile_id, "hasTimestampSeries", timestamp_series_id, strict=True)
        self.add_relation_if_allowed(view_or_asset_id, relation_id, profile_id, strict=True)
        return _entity_proxy(self, profile_id)



    # ------------------------------------------------------------------
    # Importer-oriented domain helpers
    # ------------------------------------------------------------------


    def attach_availability_profile(self, asset_or_view_id: str, profile_id: str, **kwargs) -> EntityProxy:
        return self.attach_profile(asset_or_view_id, "hasAvailabilityProfile", profile_id, **kwargs)

    def attach_demand_profile(self, asset_or_view_id: str, profile_id: str, **kwargs) -> EntityProxy:
        return self.attach_profile(asset_or_view_id, "hasDemandProfile", profile_id, **kwargs)

    def attach_run_of_river_profile(self, asset_or_view_id: str, profile_id: str, **kwargs) -> EntityProxy:
        return self.attach_profile(asset_or_view_id, "hasRunOfRiverInflowProfile", profile_id, **kwargs)

    def attach_natural_inflow_profile(self, asset_or_view_id: str, profile_id: str, **kwargs) -> EntityProxy:
        return self.attach_profile(asset_or_view_id, "hasNaturalInflowProfile", profile_id, **kwargs)

