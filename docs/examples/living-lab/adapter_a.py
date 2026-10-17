"""Team A: social science. A household survey, exported from a statistics package.

Semicolon CSV with coded answers; the codes are in codebook.txt. The team's
conventions, written down once, here:

- household ids as "LL-01"; the living lab's register writes "hh.ll01";
- missing answers as codes: 99 = "don't know", -9 = "no answer". They become
  *no value*, never a number;
- tenure 1 = owner, 2 = tenant; PV 1 = yes, 2 = no; consent 1 = yes, 0 = no;
- willingness to pay in CHF per month.
"""

from __future__ import annotations

import csv
from pathlib import Path

SOURCE = "survey-team-a"
SURVEY = "survey.wave1"

MISSING = {"99", "-9"}
WOHNFORM = {"1": "owner", "2": "tenant"}
JA_NEIN = {"1": True, "2": False}


def household_id(code: str) -> str:
    """'LL-01' -> 'hh.ll01'."""
    return "hh." + code.lower().replace("-", "")


def _answer(model, rid: str, attribute: str, raw: str, convert=int, **kw) -> None:
    """Store one answer — unless it is a missing-value code: "don't know" stays unset."""
    if raw not in MISSING:
        model.add_attribute(rid, attribute, convert(raw), provenance_ref=SOURCE, **kw)


def to_cesdm(path: Path, model) -> None:
    """Read the survey export and write one SurveyResponse per household."""
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    for row in rows:
        hh = household_id(row["id"])
        rid = f"response.wave1.{hh.removeprefix('hh.')}"
        model.add_entity("SurveyResponse", rid)
        model.add_relation(rid, "respondent", hh)
        model.add_relation(rid, "partOfSurvey", SURVEY)
        model.add_attribute(rid, "consent_data_linkage", row["einwilligung"] == "1", provenance_ref=SOURCE)

        _answer(model, rid, "willingness_to_join", row["q1_beitritt"])
        _answer(model, rid, "willingness_to_pay", row["q2_zahlung"], float, unit="CHF/month")
        _answer(model, rid, "environmental_concern", row["q3_umwelt"])
        _answer(model, rid, "tenure", row["q4_wohnform"], WOHNFORM.__getitem__)
        _answer(model, rid, "household_size", row["q5_personen"])
        _answer(model, rid, "reports_pv", row["q6_pv"], JA_NEIN.__getitem__)
