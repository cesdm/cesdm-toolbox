"""cesdm.domain.model.library — Default-library import

Loads reusable master-data instances (carriers, resources,
technology types) from library/default_library/.

Auto-extracted from the legacy monolithic module as part of the
package-hierarchy refactor (see docs/architecture/package_layout.md).
Behaviour is unchanged; only module boundaries moved.
"""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional, Union
import os
import pathlib
import re
import yaml


class LibraryMixin:
    """Mixin — see module docstring for the responsibility this covers."""

    def import_library(self, library_yaml: str, *, namespace: str | None = None) -> int:
        """
        Load a component library YAML file into the model.

        The library defines shared technology type entities (GeneratorType,
        StorageType, ConverterType, Carrier, etc.) with pre-filled
        techno-economic parameters.  Instances (GenerationUnit, StorageUnit)
        reference these types via ``hasTechnology`` so shared parameters do
        not need to be repeated on every instance.

        Parameters
        ----------
        library_yaml :
            Path to a library YAML file or a directory containing modular YAML files.
        namespace :
            Optional id prefix to avoid clashes when loading multiple libraries.

        Returns
        -------
        int
            Number of entities loaded.
        """
        import yaml as _yaml, pathlib as _pl

        path = _pl.Path(library_yaml)
        if path.is_dir():
            lib = {}
            for part in sorted(path.rglob("*.y*ml")):
                doc = _yaml.safe_load(part.read_text(encoding="utf-8")) or {}
                if not isinstance(doc, dict):
                    continue
                for key, value in doc.items():
                    if key in {"description", "version", "source"}:
                        continue
                    if key in lib and isinstance(lib[key], dict) and isinstance(value, dict):
                        overlap = set(lib[key]) & set(value)
                        if overlap:
                            raise ValueError(f"Duplicate library ids in {part}: {sorted(overlap)}")
                        lib[key].update(value)
                    else:
                        lib[key] = value
        else:
            with open(path, encoding="utf-8") as f:
                lib = _yaml.safe_load(f)

        if not isinstance(lib, dict):
            raise ValueError(f"Library YAML must be a mapping, got {type(lib)}")

        count = 0
        # Skip metadata keys
        skip_keys = {"description", "version", "source"}

        for class_name, entities in lib.items():
            if class_name in skip_keys or not isinstance(entities, dict):
                continue
            for eid, ent_def in entities.items():
                full_id = f"{namespace}.{eid}" if namespace else eid
                # Skip if already present — library should not overwrite model data
                if full_id in self.entities.get(class_name, {}):
                    continue
                try:
                    self.add_entity(class_name, full_id)
                except Exception:
                    continue  # unknown class — skip silently

                for item in (ent_def or {}).get("attributes", []):
                    try:
                        self.add_attribute(full_id, item["id"], item["value"])
                    except (KeyError, Exception):
                        pass

                for item in (ent_def or {}).get("relations", []):
                    try:
                        self.add_relation(full_id, item["id"], item["target"])
                    except (KeyError, Exception):
                        pass

                count += 1

        return count
    def ensure_default_library_entity(self, entity_id: str, expected_class: str | None = None) -> bool:
        """Materialize one generated default-library entity and its dependencies."""
        try:
            from cesdm.default_library import (
                DEFAULT_LIBRARY_CLASS_BY_ID,
                DEFAULT_LIBRARY_ENTITIES,
            )
        except ImportError:
            return False
        class_name = DEFAULT_LIBRARY_CLASS_BY_ID.get(str(entity_id))
        if class_name is None:
            return False
        if expected_class and not self.is_class_derived_from(class_name, expected_class, self.inheritance):
            return False
        if self.has_entity(str(entity_id)):
            return True
        definition = DEFAULT_LIBRARY_ENTITIES[class_name][str(entity_id)]
        self.add_entity(class_name, str(entity_id))
        for item in definition.get("attributes", []):
            self.add_attribute(str(entity_id), item["id"], item.get("value"))
        for item in definition.get("relations", []):
            target = str(item["target"])
            self.ensure_default_library_entity(target)
            self.add_relation(str(entity_id), item["id"], target)
        return True

