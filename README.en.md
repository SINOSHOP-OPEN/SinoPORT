# SinoPORT — Modular Floating Port · Eco-Community

**Track 2 · Open Source Intelligent Hardware Solution**
**Open Atomic Competition 2026**

> A typhoon-resistant floating port that can **move as a whole**, doubling as
> ocean eco-community infrastructure.

**Terminology note**: this release uses **integrated multi-stage living-water
ecological channel (10 columns / 5 walls)**. The earlier "seven-level fishway"
terminology is retired and kept only under `_archive/` for history.

---

## Quick start (judges: start here)

```bash
git clone https://gitee.com/sinoshop/SinoPORT.git
cd SinoPORT
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
python demo.py
```

**Expected output:**

```
演示结论：4 / 4 步 PASS  （总耗时 5.33 s）
```

The script prints six hard indicators right after (132 bores, 381 m
breakwater, 334.9 m berth clearance, ...).

> `demo.py` needs **only NumPy** — no FreeCAD, no GPU, no Blender.
> Any FAIL returns a non-zero exit code, so it drops straight into CI.

Parameter-evolution demo:

```bash
python demo_evolution.py
# -> 3.1416 m2 -> 10.2730 m2   ratio 3.27x
```

---

## What problem it solves

Fixed ports have three structural defects:

1. **Position cannot change.** Pile-founded berths are located once. When a
   typhoon track shifts, all you can do is reinforce — and reinforcement is
   based on historical extremes, which says nothing about unprecedented paths.
2. **Waves cannot be blocked, only reflected.** Conventional breakwaters
   reflect, break and dissipate. The energy does not vanish; it oscillates
   near the harbour, and berths still take residual wave load.
3. **Any offshore structure damages ecology.** Piles and caissons touch the
   seabed and destroy benthic habitat; breakwaters cut off water exchange.

---

## Key numbers (every one script-verified)

| Item | Value |
|---|---|
| Wave-sculpting pyramid | 7 rows 1/1/2/3/5/8/13 x 4 slopes = **132 bores**, dia **D900** |
| Solid validity | single solid, `isValid() = True`, 132 R450 cylinder faces |
| Semi-circular breakwater | single-side thickness **381 m** = 81+200+100, chord R=1,650 |
| Breakwater openings | 9 x 150 m (26 % of arc length) |
| 9 berths | total width 513 m, **all inside the R=1,650 circle** |
| Berth clearance | **334.9 m >= 300 m red line** |
| Wave attenuation | 15 m -> < 0.6 m (25x, **analytic estimate**) |
| Whole-port migration | **1,200 m seaward** (kinematic demo) |
| Eco-community | 27 floating houses + 18 sphere boats + 173 mangrove clusters |

---

## The topology-level innovation

Conventional ports need a **separate fishway** (e.g. a seven-step structure).
Three defects follow: it occupies extra space, it fails independently under
wave attack, and it needs its own tooling.

Worst of all, the fishway and the main structure have **different lifetimes** —
producing an independent failure mode: *"the fishway breaks first while the
main body is still fine."*

SinoPORT upgrades it into an **integrated multi-stage living-water ecological
channel** built **into the load-bearing structure**:

| Module | Array |
|---|---|
| MOD-STD (27x27x8 m) | **10 columns / 5 walls** |
| MOD-DM (27x27x6 m) | **6 columns / 3 walls** |

The walls carry the typhoon load; their reserved openings form the ecological
channel. **One mould delivers both capabilities.**

Measured result — the channel area goes **up**, not down:

| Path | Spec | Area |
|---|---|---|
| Load-bore openings | 12 mortise-tenon columns phi300 mm | 0.8482 m² |
| Ballast tank triple bundle | phi2000 mm x 3 | 9.4248 m² |
| **Total** | — | **10.2730 m²** |

Removed external fishway: 3.1416 m² -> **3.27x larger**.

> **Scope note**: the 1.4092 % permeability is a **geometric computation**,
> **not a CFD flow-exchange rate**. Different physical quantities; we do not
> conflate them.
>
> Recompute with `python demo_evolution.py` (pure Python, seconds).

---

## Parameterisation and measured feedback

One real case proving the chain is not theatre:

When the bore diameter changed from 1,000 mm to 900 mm, extrapolating the
removed-volume baseline by area (D²) predicts **0.8100**, but the measured
ratio is **0.8609** — because a smaller bore widens the gap (357 -> 450 mm),
so adjacent cylinders overlap less. The calibrated coefficient brought the
error from **+7.93 % down to +1.55 %**.

> **Change the geometry, recalibrate the baseline.**
> That is what "parameterisation with measured feedback" actually means.

---

## Honesty statement

| Item | Status |
|---|---|
| Wave hydrodynamics | **analytic estimate, not CFD** (on the roadmap) |
| Towing hydrodynamics / stability | **kinematic demo, no fluid verification** |
| Annual wave-energy output | **white-paper reference**, not measured here |
| Material formulations | **confidential (NDA)**; repo publishes structure and metrics only |

Every innovation figure must answer *"so what?"* — and every limitation is
registered rather than glossed over.

---

## Repository layout

| Path | Contents |
|---|---|
| `demo.py` | one-command demo entry (4-step assertion chain) |
| `demo_evolution.py` | ecological-channel before/after comparison |
| `src/specs/` | **all parameter sources** — the single source of truth |
| `src/model/` | OCC modelling scripts |
| `src/core/` | in-house rasterizer (`raster_core.py`) |
| `src/verify/` | verification scripts (hard gates) |
| `tools/` | screenshot generator, Gitee comment poster, stub tests |
| `captions/` | demo-video subtitles and burn-in script |
| `docs/standards/` | Coding standard V6.4 |
| `docs/reports/` | verification artefacts + real terminal screenshots |
| `docs/papers/` | project introduction document, benchmark table |
| `docs/issues/` | Issue / PR records |
| `_archive/` | historical READMEs (kept, never deleted) |

---

## Governance

| Document | Purpose |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | how to contribute |
| [DEPENDENCIES.md](DEPENDENCIES.md) | dependency and licence compliance |
| `docs/issues/` | refactoring records, kept in the open |

---

## Licence

Apache License 2.0 — see [LICENSE](LICENSE).

Third-party tools are invoked as **separate processes**, never linked, so GPL
copyleft does not propagate.

---

_SinoPORT engineering team · 2026-10-19_
_Every numeric conclusion in this repository is determined by a script; no PASS is hand-written._
