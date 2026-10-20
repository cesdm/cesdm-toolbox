# Living lab: survey and meter data

Energy transition research increasingly brings two kinds of data together: what people **say and do** — surveys, interviews, co-design workshops — and what their buildings and devices **measure** — consumption, PV, batteries. The two usually live with different teams, in different tools, under different conventions. This case shows how a social-science team and an engineering team in the same living lab exchange and combine their data through CESDM. Read it if your project combines energy assets with data from another discipline: it shows how to add your own vocabulary without touching CESDM, and how to keep that discipline's conventions — scales, missing answers, consent — as checked rules.

The survey is new vocabulary, and it points at energy assets that CESDM already describes. This example therefore extends `cesdm/schemas/base` instead of starting a schema of its own. The same choice is the second row of [Extend CESDM, or start a new schema?](../concepts/engine.md#extend-cesdm-or-start-a-new-schema).

```bash
python docs/examples/living-lab/run.py
```

The script runs in six numbered steps. The output blocks below are copied from it and keep its numbers.

!!! note "Inspired by SWEET LANTERN"
    The setting follows the themes of [SWEET LANTERN](https://sweet-lantern.ch/) — *Living Labs Interfaces for the Energy Transition* — which studies, among others, energy communities and smart energy users in living labs, including what drives people to join energy communities and to pay for local renewables. The neighbourhood, households and all numbers here are invented; nothing is LANTERN data.

## Two teams, one neighbourhood

In the (invented) living lab of Montvert, eleven households take part. Two teams work with them:

=== "Team A: social science"

    A household survey, exported from a statistics package. Coded answers, German labels, missing-value codes — all explained in a codebook.

    ```text
    survey_wave1.csv
    id;q1_beitritt;q2_zahlung;q3_umwelt;q4_wohnform;q5_personen;q6_pv;einwilligung
    LL-01;5;20;5;1;4;1;1
    LL-04;5;30;5;1;3;1;0
    LL-05;99;-9;2;2;2;2;1
    LL-06;4;10;4;1;5;2;1
    ```

    | Variable | Question | Codes |
    |---|---|---|
    | `q1_beitritt` | Would you join a local energy community? | 1 certainly not … 5 certainly; **99 don't know** |
    | `q2_zahlung` | How much more per month would you pay for local solar power? | CHF/month; **−9 no answer** |
    | `q4_wohnform` | Do you own or rent? | 1 owner, 2 tenant |
    | `q6_pv` | Does your household have a PV system? | 1 yes, 2 no |
    | `einwilligung` | Consent to link your answers to meter data | 1 yes, 0 no |

=== "Team B: engineering"

    Smart-meter and asset data for one year, as JSON. Energy in kWh, PV in kWp.

    ```json
    {"meter": "ll06", "consumption": 6100, "pv": 10.2, "battery": 13.5, "ev": true}
    ```

| | Team A | Team B |
|---|---|---|
| Household id | `LL-06` | `ll06` |
| Unit of analysis | a response to a survey wave | a household's assets |
| Missing values | codes 99, −9 | absent, or 0 for "has none" |
| Units | CHF per month | kWh/year, kWp, kWh |
| PV | *stated*: "do you have PV?" | *measured*: kWp |

Both teams load one register before they write anything: `shared/living_lab.yaml`. It already contains the canton, the invented municipality of Montvert, the living lab, survey wave 1, and the eleven households `hh.ll01`–`hh.ll11`. The survey file says `LL-06`. The meter file says `ll06`. The register, and every later link, says `hh.ll06`. That id is the only thing the two files share.

| Household | Join | Pay, CHF/month | Tenure | Stated PV | Consent | Demand, kWh/year | PV, kWp | Battery, kWh | EV |
|---|---|---|---|---|---|---|---|---|---|
| `hh.ll01` | 5 | 20 | owner | yes | yes | 4800 | 9.6 | 10 | yes |
| `hh.ll02` | 4 | 15 | tenant | no | yes | 2600 | — | — | no |
| `hh.ll03` | 2 | 0 | tenant | no | yes | 1900 | — | — | no |
| `hh.ll04` | 5 | 30 | owner | yes | no | 5200 | 7.5 | — | yes |
| `hh.ll05` | — | — | tenant | no | yes | 3100 | — | — | no |
| `hh.ll06` | 4 | 10 | owner | no | yes | 6100 | 10.2 | 13.5 | yes |
| `hh.ll07` | 3 | 5 | tenant | no | yes | 3900 | — | — | no |
| `hh.ll08` | 5 | 25 | owner | yes | yes | 3300 | 6.0 | — | no |
| `hh.ll09` | 1 | 0 | owner | no | yes | 5600 | — | — | yes |
| `hh.ll10` | 4 | 20 | tenant | no | yes | — | — | — | — |
| `hh.ll11` | — | — | — | — | — | 4400 | 8.0 | — | no |

`hh.ll05` answered "don't know" on joining and gave no amount. `hh.ll10` answered the survey and has no meter. `hh.ll11` has a meter and did not answer. `hh.ll06` said it has no PV; the meter shows 10.2 kWp.

Together they want to answer a question neither can answer alone: **how large would an energy community be if the households willing to join actually joined?**

## Extend CESDM with the survey

The energy side needs nothing new: `DemandUnit`, `SolarGenerationUnit` and `StorageUnit` are CESDM classes, with CESDM units. Households, where they live, and the survey are one extension package:

```text
docs/examples/living-lab/schema/
├── SCHEMA_MANIFEST.yaml        # extends: cesdm/schemas/base
├── entities/                   # Canton, Municipality, Household, LivingLab, Survey, SurveyResponse
├── attributes/attributes.yaml  # survey answers, and has_ev
├── relations/relations.yaml    # respondent, ownedBy, isPartOf, …
├── units/units.yaml            # CHF/month
└── augmentations.yaml          # ownedBy on DemandUnit, SolarGenerationUnit, StorageUnit
```

```text
response.wave1.ll06              SurveyResponse
├── willingness_to_join          = 4
├── willingness_to_pay           = 10 CHF/month
├── tenure                       = owner
├── reports_pv                   = false             stated by the household
├── consent_data_linkage         = true
├── respondent                   → hh.ll06
└── partOfSurvey                 → survey.wave1

hh.ll06                          Household
├── has_ev                       = true
└── locatedIn                    → mun.montvert

demand.ll06                      DemandUnit          6.1 MWh/year
└── ownedBy                      → hh.ll06
pv.ll06                          SolarGenerationUnit 0.0102 MW      measured
└── ownedBy                      → hh.ll06
battery.ll06                     StorageUnit         0.0135 MWh
└── ownedBy                      → hh.ll06
```

Five design decisions carry most of the weight:

- **A response is not a household.** Answers belong to a `SurveyResponse` that points at its household and its survey wave. A second wave next year adds responses; the household and its assets stay the same objects.
- **"Don't know" is not a number.** The schema limits `willingness_to_join` to 1–5, so a 99 left in by mistake is reported by `validate()`. The adapter turns it into *no value*, and an analysis that needs the answer reports it as missing.
- **Stated and measured stay apart.** `reports_pv` is what the household said. A `SolarGenerationUnit` with `ownedBy → hh.ll06` is what the meter shows. The result below reports both.
- **Consent is data.** `consent_data_linkage` is required on every response. The joint analysis checks it before using any answer together with meter data.
- **The link is added to the CESDM class.** `Household` is a class this package defines, so its own fields go in `Household.yaml`. `DemandUnit`, `SolarGenerationUnit` and `StorageUnit` belong to `cesdm/schemas/base`. The augmentation attaches `ownedBy → Household` to those three classes. Each asset names one household, so a household can own a demand, a PV system and a battery without a multi-target link.

```yaml
# augmentations.yaml
augmentations:
  DemandUnit:
    groups:
      living_lab:
        relations:
          - id: ownedBy            # → Household
  SolarGenerationUnit:
    groups:
      living_lab:
        relations:
          - id: ownedBy
  StorageUnit:
    groups:
      living_lab:
        relations:
          - id: ownedBy
```

```yaml
# attributes/attributes.yaml (excerpt)
willingness_to_join:
  description: '"Would you join a local energy community?" 1 = certainly not … 5 = certainly.'
  value: {type: integer, constraints: {minimum: 1, maximum: 5}}
willingness_to_pay:
  description: Extra amount per month the household would pay for electricity from the community's PV.
  value: {type: decimal, constraints: {minimum: 0.0}}
  unit: {constraints: {enum: [CHF/month]}}
consent_data_linkage:
  description: The household agreed that its answers may be linked to its meter and asset data.
  value: {type: boolean}
```

`CHF/month` is not a CESDM unit, so the package registers it in its own `units/units.yaml`. Both adapters load the register from the start of this page, so the households already exist when the answers and the meters are written.

## One adapter per team

Each team writes down its conventions once, in its adapter. Team A turns codes into values and missing codes into nothing:

```python
MISSING = {"99", "-9"}
WOHNFORM = {"1": "owner", "2": "tenant"}

def _answer(model, rid, attribute, raw, convert=int, **kw):
    if raw not in MISSING:                                    # "don't know" stays unset
        model.add_attribute(rid, attribute, convert(raw), provenance_ref="survey-team-a", **kw)

_answer(model, rid, "willingness_to_join", row["q1_beitritt"])
_answer(model, rid, "willingness_to_pay", row["q2_zahlung"], float, unit="CHF/month")
_answer(model, rid, "tenure", row["q4_wohnform"], WOHNFORM.__getitem__)
```

Team B converts to CESDM units and links each asset to its household:

```python
model.add_entity("SolarGenerationUnit", f"pv.{key}")
model.add_attribute(f"pv.{key}", "nominal_power_capacity", h["pv"] / 1000,      # kWp → MW
                    unit="MW", provenance_ref="meter-team-b")
model.add_relation(f"pv.{key}", "ownedBy", f"hh.{key}")
```

## Check before sending

```text
1 · Each team writes its data with the shared schema
    Team A (survey, CSV): 10 responses, validate(): []
    Team B (meters, JSON): 10 demands, 5 PV systems, 2 batteries, validate(): []
```

The schema catches the typical mistakes of both disciplines:

| Mistake | Message |
|---|---|
| "Don't know" kept as code 99 | `Attribute 'willingness_to_join' violates maximum 5: 99` |
| Willingness to pay per year instead of per month | `Unit 'CHF/year' is not allowed for 'willingness_to_pay'. Allowed: ['CHF/month']` |
| Tenure code not translated | `Attribute 'tenure' not in enum ['owner', 'tenant']: 2` |
| PV left in kWp | `Unit 'kWp' is not allowed for 'nominal_power_capacity'. Allowed: ['MW']` |
| Answers linked to a meter instead of a household | `Relation 'respondent' with 'demand.ll05' is of class 'DemandUnit' not compatible with any of [Household]` |
| A PV system's owner link pointing at a meter | `Relation 'ownedBy' with 'demand.ll05' is of class 'DemandUnit' not compatible with any of [Household]` |

## Same households? Do survey and meters agree?

Both files are loaded into one model. Because they share the register, the households are the same objects, and the comparison is by the shared household id (`hh.ll06` for survey file `LL-06` and meter `ll06`):

```text
3 · Same households? Do survey and meters agree?
    hh.ll10: answered the survey, no meter data
    hh.ll11: meter data, did not answer the survey
    hh.ll06: says PV no, meter data show a PV system
```

The last line is the interesting one. Household 6 has a 10 kWp system but answered "no" — perhaps the landlord owns it, perhaps the question was misread. Neither team would have seen this alone; for the survey team it is a finding about the question, for the engineering team a reason not to read `q6_pv` as asset data.

## Complete for which analysis?

Two profiles in `profiles/`. The survey analysis needs the key answers. The joint analysis needs consent, an answer, and an `ownedBy` link on every demand. A household with no meter has no demand, so that gap is reported when the two files are compared, in the previous section.

```yaml
# profiles/community_potential.yaml
requirements:
  - entity_class: SurveyResponse
    checks:
      - attribute: consent_data_linkage
        required: true
        constraints:
          enum: [true]                 # no linking without consent
      - {attribute: willingness_to_join, required: true}
  - entity_class: DemandUnit
    checks:
      - {attribute: ownedBy, required: true}
```

```text
4 · Complete for which analysis?
    A      survey_analysis     1 gap
        [survey_analysis] [SurveyResponse:response.wave1.ll05] missing required 'willingness_to_join'
    merged community_potential 2 gaps
        [community_potential] [SurveyResponse:response.wave1.ll04] 'consent_data_linkage' value False is not one of [True]
        [community_potential] [SurveyResponse:response.wave1.ll05] missing required 'willingness_to_join'
```

The gaps are reasons, not errors: household 4 did not consent, household 5 does not know. Household 10 has no meter; that was already in the comparison, because there is no demand whose `ownedBy` could be missing. The analysis leaves them out — and the report says exactly why.

## The joint analysis

With the gaps known, the question can be answered:

```text
5 · Joint analysis: willingness and the potential community
    7 households usable (consent given, answer given, meter data present)
    willingness to join (1–5), by measured PV: with PV 4.7 (n=3), without PV 2.5 (n=4)
    willingness to join (1–5), by stated PV: with PV 5.0 (n=2), without PV 2.8 (n=5)
    community of the willing (score ≥ 4): hh.ll01, hh.ll02, hh.ll06, hh.ll08
      demand 16.8 MWh/year, PV 25.8 kWp ≈ 25.8 MWh/year at 1000 kWh/kWp — annual balance 154%
      stated willingness to pay: 17.5 CHF/month on average
```

A score of 4 or 5 on the 1–5 scale counts as willing to join. The annual balance is yearly production divided by yearly consumption, not the share of PV used at the same hour. By the meters, households that already have PV are more willing to join (4.7 against 2.5). By what they said, the gap is wider still (5.0 against 2.8), and household 6 is in the measured group only. The willing four would produce more over the year than they use. With seven households this is an illustration, not a result — the point is that the question needed the survey and the meters, and could be asked in a few lines once both were in one checked model. An hourly study — how much of that PV the community could use itself — would add [profiles](../concepts/files-and-time-series.md#time-series) to the same assets.

## Hand the energy part on

An energy modeller who sizes the community's storage or grid connection needs the assets, not the answers. The example writes the willing households' assets into a model built on `cesdm/schemas/base` alone:

```text
6 · Hand the energy part to an energy modeller
    cesdm/schemas/base only: {'DemandUnit': 4, 'SolarGenerationUnit': 3, 'StorageUnit': 2}, validate(): []
    no survey answers in the file — the energy modeller gets assets, not people
```

That file is ordinary CESDM: it can go through the same adapters, comparisons and [analysis profiles](../concepts/validation.md) as the Swiss system in the tutorial.

## What this shows

| | |
|---|---|
| **Extending, not forking** | Households, the survey and the links to assets are one package on top of `cesdm/schemas/base`. Energy classes, units and checks come unchanged from CESDM. |
| **One model across disciplines** | A survey answer and a PV system are objects in the same model, linked by a typed relation. Joining them is a lookup, not a merge of spreadsheets. |
| **Social-science conventions as rules** | Scales, missing-value codes, stated vs measured, consent — written into the schema and the profiles, checked for everyone. |
| **Data protection by design** | Pseudonymous ids from the living lab's register; consent checked before linking; the energy modeller receives assets only. |

What the example does not do: it does not anonymise data — pseudonymous ids are not anonymity — and the schema is a sketch. A real survey extension would be designed with the survey team and their codebook, versioned like any [extension package](../concepts/schemas.md#extending-without-forking), and could become shared vocabulary for living labs if several projects used it.
