"""Shared helpers: the schema, the living lab's register, loading files."""

from __future__ import annotations

import warnings
from pathlib import Path

from cesdm_toolbox import build_model_from_yaml

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "schema"                         # extends schemas/cesdm
REGISTER = HERE / "shared" / "living_lab.yaml"
PROFILES = HERE / "profiles"


def new_model():
    """The schema plus the register both teams share: the lab, the survey, the households."""
    model = build_model_from_yaml(SCHEMA)
    model.import_library(str(REGISTER))
    return model


def save(model, path) -> None:
    """Write a model for the other team. The register goes with it."""
    model.export_yaml(path, include_library="all")


def load(*paths):
    """Receive one or more files into one model."""
    model = build_model_from_yaml(SCHEMA)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")              # the register is in every file
        for path in paths:
            model.import_yaml(str(path))
    return model


def target(model, entity_id: str, relation: str):
    """The single target of a relation, or None."""
    targets = model.get_relation_targets(entity_id, relation)
    return targets[0] if targets else None
