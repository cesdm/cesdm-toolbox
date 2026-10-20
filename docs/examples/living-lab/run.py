#!/usr/bin/env python3
# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Energy and society: a survey team and a meter team in the same living lab.

    python docs/examples/living-lab/run.py

Team A (social science) asked the households of a living-lab neighbourhood
whether they would join an energy community. Team B (engineering) has their
meter and asset data. Each team writes one adapter to CESDM plus a small
survey extension; then the two datasets are checked against each other,
merged, checked for a joint analysis, analysed, and the energy part handed
on to an energy modeller. All data are invented; the setting is inspired by
the living labs of SWEET LANTERN.
"""

from __future__ import annotations

import contextlib
import io
import warnings
from pathlib import Path
from statistics import mean

import adapter_a
import adapter_b
from common import HERE, PROFILES, load, new_model, save, target

from cesdm_toolbox import build_model_from_yaml
from ear import get_attr_value

OUT = Path.cwd() / "output" / "living-lab"
SURVEY_FILE = HERE / "team-a-survey" / "survey_wave1.csv"
METER_FILE = HERE / "team-b-meters" / "households_2025.json"
SPECIFIC_YIELD = 1000          # kWh per kWp and year — an assumption, stated in the output


def section(title: str) -> None:
    print(f"\n{title}")


def value(model, cls, eid, attribute):
    entity = model.get_entities(cls).get(eid)
    return get_attr_value(entity, attribute) if entity is not None else None


def mistakes() -> None:
    """What the schema catches, each on a fresh model with both teams' data."""
    def attempt(label, action):
        model = new_model()
        adapter_a.to_cesdm(SURVEY_FILE, model)
        adapter_b.to_cesdm(METER_FILE, model)
        try:
            with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()):
                warnings.simplefilter("ignore")
                action(model)
        except (ValueError, KeyError) as error:
            print(f"    {label:<36} refused: {str(error).strip(chr(34))}")
            return
        errors = model.validate()
        print(f"    {label:<36} validate(): {errors[0] if errors else 'no error'}")

    r, hh = "response.wave1.ll05", "hh.ll05"
    attempt("'don't know' kept as code 99", lambda m: m.add_attribute(r, "willingness_to_join", 99))
    attempt("willingness to pay per year", lambda m: m.add_attribute(r, "willingness_to_pay", 120, unit="CHF/year"))
    attempt("tenure code not translated", lambda m: m.add_attribute(r, "tenure", "2"))
    attempt("PV left in kWp", lambda m: m.add_attribute("pv.ll01", "nominal_power_capacity", 9.6, unit="kWp"))
    attempt("answers linked to the meter", lambda m: m.add_relation(r, "respondent", "demand.ll05"))
    attempt("PV owner link pointing at a meter", lambda m: m.add_relation("pv.ll01", "ownedBy", "demand.ll05"))


def assets_owned_by(model, cls, household):
    """Asset ids of this class whose ownedBy link points at the household."""
    return [
        eid for eid in model.get_entities(cls)
        if target(model, eid, "ownedBy") == household
    ]


def compare(model) -> list[str]:
    """Does the survey describe the same households as the meters — and do they agree?"""
    out = []
    responses = {target(model, rid, "respondent"): rid for rid in model.get_entities("SurveyResponse")}
    metered = {target(model, eid, "ownedBy") for eid in model.get_entities("DemandUnit")}
    metered.discard(None)
    for hh in sorted(set(responses) - metered):
        out.append(f"{hh}: answered the survey, no meter data")
    for hh in sorted(metered - set(responses)):
        out.append(f"{hh}: meter data, did not answer the survey")
    for hh in sorted(set(responses) & metered):
        stated = value(model, "SurveyResponse", responses[hh], "reports_pv")
        measured = bool(assets_owned_by(model, "SolarGenerationUnit", hh))
        if stated is not None and stated != measured:
            out.append(f"{hh}: says PV {'yes' if stated else 'no'}, meter data show "
                       f"{'a PV system' if measured else 'none'}")
    return out


def eligible(model):
    """Responses usable in the joint analysis: consent, an answer, measured demand."""
    for rid in sorted(model.get_entities("SurveyResponse")):
        hh = target(model, rid, "respondent")
        if (value(model, "SurveyResponse", rid, "consent_data_linkage") is True
                and value(model, "SurveyResponse", rid, "willingness_to_join") is not None
                and assets_owned_by(model, "DemandUnit", hh)):
            yield rid, hh


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    section("1 · Each team writes its data with the shared schema")
    a, b = new_model(), new_model()
    adapter_a.to_cesdm(SURVEY_FILE, a)
    adapter_b.to_cesdm(METER_FILE, b)
    print(f"    Team A (survey, CSV): {len(a.get_entities('SurveyResponse'))} responses, validate(): {a.validate()}")
    print(f"    Team B (meters, JSON): {len(b.get_entities('DemandUnit'))} demands, "
          f"{len(b.get_entities('SolarGenerationUnit'))} PV systems, "
          f"{len(b.get_entities('StorageUnit'))} batteries, validate(): {b.validate()}")
    save(a, OUT / "team_a.yaml")
    save(b, OUT / "team_b.yaml")

    section("2 · Mistakes the schema catches")
    mistakes()

    section("3 · Same households? Do survey and meters agree?")
    merged = load(OUT / "team_a.yaml", OUT / "team_b.yaml")
    for line in compare(merged):
        print("    " + line)

    section("4 · Complete for which analysis?")
    for name, model, profile in [("A", a, "survey_analysis"), ("merged", merged, "community_potential")]:
        gaps = model.validate_for_analysis(str(PROFILES / f"{profile}.yaml"))
        print(f"    {name:<7}{profile:<20}" + ("ready" if not gaps else f"{len(gaps)} gap" + "s" * (len(gaps) > 1)))
        for gap in gaps:
            print(f"        {gap}")

    section("5 · Joint analysis: willingness and the potential community")
    rows = list(eligible(merged))
    print(f"    {len(rows)} households usable (consent given, answer given, meter data present)")

    def _mean_line(label, chosen):
        scores = [value(merged, "SurveyResponse", r, "willingness_to_join") for r, hh in rows if chosen(r, hh)]
        other = [value(merged, "SurveyResponse", r, "willingness_to_join") for r, hh in rows if not chosen(r, hh)]
        print(f"    willingness to join (1–5), {label}: "
              f"with PV {mean(scores):.1f} (n={len(scores)}), without PV {mean(other):.1f} (n={len(other)})")

    _mean_line("by measured PV", lambda r, hh: bool(assets_owned_by(merged, "SolarGenerationUnit", hh)))
    _mean_line("by stated PV", lambda r, hh: value(merged, "SurveyResponse", r, "reports_pv") is True)

    members = [(r, hh) for r, hh in rows if value(merged, "SurveyResponse", r, "willingness_to_join") >= 4]
    demand = sum(value(merged, "DemandUnit", assets_owned_by(merged, "DemandUnit", hh)[0], "annual_energy_demand")
                  for _, hh in members)
    pv_mw = sum(value(merged, "SolarGenerationUnit", eid, "nominal_power_capacity")
                for _, hh in members for eid in assets_owned_by(merged, "SolarGenerationUnit", hh))
    pv_mwh = pv_mw * 1000 * SPECIFIC_YIELD / 1000
    wtp = [value(merged, "SurveyResponse", r, "willingness_to_pay") for r, _ in members]
    print(f"    community of the willing (score ≥ 4): {', '.join(hh for _, hh in members)}")
    print(f"      demand {demand:.1f} MWh/year, PV {pv_mw * 1000:.1f} kWp ≈ {pv_mwh:.1f} MWh/year "
          f"at {SPECIFIC_YIELD} kWh/kWp — annual balance {pv_mwh / demand:.0%}")
    print(f"      stated willingness to pay: {mean(wtp):.1f} CHF/month on average")

    section("6 · Hand the energy part to an energy modeller")
    energy = build_model_from_yaml(str(HERE.parents[2] / "cesdm" / "schemas" / "base"))
    for _, hh in members:
        for cls in ("DemandUnit", "SolarGenerationUnit", "StorageUnit"):
            for asset in assets_owned_by(merged, cls, hh):
                energy.add_entity(cls, asset)
                for attribute, data in merged.get_entities(cls)[asset].data.items():
                    if not isinstance(data, dict) or "value" not in data:
                        continue  # ownedBy is a relation; the energy-only schema has no household
                    energy.add_attribute(asset, attribute, data["value"], unit=data.get("unit"),
                                         provenance_ref=data.get("provenance_ref"))
    energy.export_yaml(OUT / "community_assets.yaml")
    classes = {c: len(e) for c, e in energy.entities.items() if e}
    print(f"    cesdm/schemas/base only: {classes}, validate(): {energy.validate()}")
    print("    no survey answers in the file — the energy modeller gets assets, not people")


if __name__ == "__main__":
    main()
