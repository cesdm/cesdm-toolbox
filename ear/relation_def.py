# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""ear.relation_def

Schema definition of a single relation slot.

Auto-extracted from the legacy monolithic ``ear_toolbox.py``.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional, Union, Tuple
from difflib import get_close_matches
import os, pathlib
import yaml
from pathlib import Path
import re



from ear.attribute_def import _normalize_belongs_to_group


@dataclass
class RelationDef:
    """
    Definition of a relation from one entity to another in the schema.
    """
    name: str
    targets: List[str]          # list of allowed target class names
    cardinality: str = "1"
    required: Optional[bool] = None
    description: str = ""
    belongsToGroup: List[str] = field(default_factory=list)  # which former
        # representation-view family/families this relation was merged
        # in from -- see AttributeDef.belongsToGroup for the full
        # rationale. A relation can belong to more than one group.
    default: Optional[Any] = None
    # Predefined target entity id (or list of ids). Unlike ``default``,
    # the relation may not be pointed at anything else.
    fixed: Optional[Any] = None

    @property
    def target(self) -> str:
        """
        Backwards-compatible view: the first declared target, or ''.
        Existing code that expects a single string still works.
        """
        return self.targets[0] if self.targets else ""

    def fixed_targets(self) -> List[str]:
        """Entity ids this relation is locked to, or ``[]`` if not fixed."""
        raw = self.fixed
        if raw in (None, "", False):
            return []
        if isinstance(raw, (list, tuple)):
            return [str(x) for x in raw if x not in (None, "")]
        return [str(raw)]

    @staticmethod
    def from_dict(name: str, d: Dict[str, Any]) -> "RelationDef":
        """
        Create a RelationDef from YAML.

        Supports both:
          target: EnergyNode
        and:
          target: [EnergyConversionTechnology1x1, EnergyConversionTechnology1x2]
        """
        raw = d.get("target") or d.get("ref") or ""
        if isinstance(raw, list):
            targets = [str(x).strip() for x in raw if x]
        elif raw:
            targets = [str(raw).strip()]
        else:
            targets = []

        return RelationDef(
            name=name,
            targets=targets,
            cardinality=str(d.get("cardinality", "1")),
            required=d.get("required"),
            description=str(d.get("description", "")) if d.get("description") is not None else "",
            belongsToGroup=_normalize_belongs_to_group(d.get("belongsToGroup")),
            default=d.get("default"),
            fixed=d.get("fixed"),
        )



