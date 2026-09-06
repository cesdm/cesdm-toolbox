# CESDM vs Other Tools

CESDM sits next to standards and modelling tools — it does not replace them.

**One distinction:** CESDM standardises the **meaning and structure** of an energy system; neighbouring projects standardise **operations models**, **solvers**, or **dataset contracts**.

---

## Comparison

| Capability | CESDM | CIM | PyPSA | CrossContract |
|------------|:-----:|:---:|:-----:|:-------------:|
| Describe energy-system **meaning** | **Yes** | Yes | Limited | Limited |
| Power-system **operations** standard | No | **Yes** | No | No |
| Solver / capacity-expansion **model** | No | No | **Yes** | No |
| Dataset **contract** (tables, metadata) | Partial | Partial | No | **Yes** |
| Complex **semantic relationships** | **Yes** | Yes | Limited | Limited |
| Multi-tool **interoperability** | **Core purpose** | Yes | Limited | Data-oriented |

---

## How to read this

**CESDM vs PyPSA (or Calliope, OSeMOSYS, pandapower)**  
Those tools **run** studies. CESDM **describes** the system those studies use. You can import a PyPSA network into CESDM, or export a CESDM model toward a tool — see [Tool adapters](../guides/tool-adapters.md).

**CESDM vs CIM**  
CIM is the industry standard for **operational** power-system information exchange. CESDM targets **energy-system studies** (planning, multi-carrier, multi-tool research), not SCADA/EMS operations.

**CESDM vs CrossContract**  
[CrossContract](https://sweet-cross.github.io/crosscontract/) standardises **datasets exchanged about** a system (tables, units, metadata). CESDM standardises the **semantic model of the system itself**. They can complement each other: CESDM for meaning and topology; CrossContract for agreed tabular payloads.

---

## Next step

- New to CESDM: [CESDM in 5 Minutes](cesdm-in-5-minutes.md)
- Already on PyPSA or pandapower: [Tool adapters](../guides/tool-adapters.md)
- Full motivation: [What is CESDM?](what-is-cesdm.md)
