# Guitar Compensation — project context

This project covers two linked deliverables for a single acoustic guitar:
1. **`web/`** — a self-contained intonation-compensation calculator (website).
2. **`saddle/`** — a parametric 3D-printable reference for hand-building a new lower-action saddle for the same instrument.

This file is the handoff brief from a planning chat. Numbers below are settled unless flagged.

## The instrument
- Steel-string acoustic, **scale length 634 mm**, strings **John Pearse Light**.
- **Fretboard radius 400 mm.**
- **Saddle slot:** 3 mm wide; centreline runs **639.5 mm (6th/bass end) → 635 mm (1st/treble end)** from the nut. Not being re-routed.
- Old (working) saddle is ~420 mm top radius + bass tilt; intonates within measurement noise.

## The compensation model (Trevor Gore deflection method)
Fretting stretches the string, which sharpens the note; compensation moves the
break point back to cancel it. Sharpening is driven by **fretting deflection**,
not string stiffness (Gore: stiffness ≈ negligible, ~0.25 cents). Key consequence:
**compensation scales with action²**. So lowering the action reduces the required
setback as `new_comp = old_comp × (new_action / old_action)²`. Saddle-position
sensitivity ≈ 2.7 cents/mm at this scale (1731/L).

The web calculator implements the full least-squares version (per-fret deflection
→ ΔT → cents, solved for saddle setback + nut offset). It solves **twice**: once for
the as-built per-string action (§01 Action f1/f12) and once for a **target action**
(§01, low-E/high-E @ 12th, interpolated across strings; 1st-fret action taken as
unchanged since the nut isn't lowered). `RES` = as-built, `REST` = target. Sections
03–06 show both (second table where columns crowd; both marker sets on the maps); the
§07 saddle is cut for the target. It is vanilla JS / inline SVG, no build step, runs
offline. Intended to deploy to GitHub Pages at `guitar-compensation-calculator`
(index.html at repo root).

**§02 Calibration (`calGain`).** The textbook deflection model over-predicts
sharpening (chiefly because a wound string's tension-bearing core is far thinner than
its overall diameter, so the published `EA` runs hot). §02 fits a single
**deflection-gain** `k` that multiplies the per-fret deflection error `ed` everywhere
(both `RES` and `REST`); `k=1` is textbook, real guitars run either side of it. (For this
instrument the fit and an independent cross-check against Mottola's calculator both land
`k`≈1.6–1.9 — it needs *more* compensation than textbook, not less; Mottola's per-string
setbacks come out ≈1.9× ours at gain 1, with identical string rank order.) Critical
gotcha: the deflection-error curve `ed(n)` and the saddle-setback lever `an(n)` are
~99.97 % collinear over the fretted range (that collinearity is *why* a saddle
compensates deflection so well), so **measured cents-vs-fret alone cannot identify
`k`** — a cents-only/shape-only fit is ill-posed and was abandoned. The fit therefore
also needs each string's **current fore-aft break point** (nut→break, mm — a *ruler*
reading on the old saddle, NOT the §07 crest *height*, which is the orthogonal vertical
axis). With the break known, `ds_current=(break−scale)/1000` is a constant, leaving a
clean 2-param linear regression `measured(n) − an·ds_current = k·ed(n) + β` (β = one
shared constant soaking up open-tuning error). The break column pre-fills from the
measured current-saddle break points (`CUR_BREAK`, mm from nut: 639.0/638.0/637.5/
636.0/637.0/635.0 for E2…E4). `fitGain()` does the regression; `calGain` is also
directly editable to explore by hand.

**Save / load (§01).** "Save inputs (.json)" / "Load inputs…" serialise *every* input on
the page — `collectState()` walks all `input[id]`/`select[id]` plus the dynamic tables
(string params by `data-i`/`data-f`, calibration breaks/cents, and the §07 crest `data-ref`
/ `data-sc` overrides incl. their `data-locked` flag). `applyState()` restores them and
calls `recompute()` (locked crest overrides are re-flagged *before* recompute so they
survive the re-derive). Load deliberately does **not** call `loadPreset` — it restores the
saved string values directly. File is `saddle-compensation-<YYYY-MM-DD>.json`.

**Auto-persist (localStorage).** Beyond the explicit file save/load, every input is
auto-saved to `localStorage["saddle-comp-state"]` (debounced `persistSoon()`, fired from
`recompute()` and a document-level `input` listener) and re-applied on startup by
`restoreSaved()` (runs after the build + `loadPreset`, so saved state wins over defaults;
corrupt/stale JSON is ignored). So edits survive a page reload. First-ever load (empty
storage) falls back to the baked defaults: `CUR_BREAK` and `CUR_CENTS` (the measured
break points and cents-sharp of the current saddle, per string × `CAL_FRETS`).

**Anchor target to current saddle (`anchorTarget`, §02, default ON).** Because the
current (old) saddle already intonates well, the preferred way to get the target break
points is *not* the absolute deflection model but a re-scaling of the measured-good
saddle: `target_setback = current_setback × (REST/RES)`, where `REST/RES` is the model's
per-string as-built→target setback ratio (which is the action² scaling with `a1` held
fixed). The deflection **gain cancels in that ratio**, so the cut inherits all the
real-world compensation already in the working saddle and only adjusts it for the lower
action — making the §02 gain irrelevant to the cut when anchoring is on (it still drives
the as-built numbers and §04 curve). `anchorTargetToCurrent(g)` mutates `REST` in place
after the solve: it overrides `REST[i].saddle` and recomputes each fret's `ef`/`rmsA`
against the anchored setback (nut left as the model solved it; needs a break value per
string, else that string falls back to the model). Everything downstream (§02 target
table, §05 map, §07 cut via `saddleModel`) then reads the anchored `REST[i].saddle`
transparently. Toggle off = pure model (old behaviour). Note the four bass breaks still
fall in front of the fixed slot and clamp to the front face, as before.

**Mottola mode (`mottola` + `fretH`, §01, default OFF).** A cross-check against R.M.
Mottola's online compensation calculator (which runs the Elmendorp model server-side in
`compensation1/2.php` — not extractable from the saved `mottola.html`) showed Mottola's
per-string setbacks come out ≈1.9× ours at gain 1 with *identical* string rank order. The
entire gap is one physical parameter: Mottola deflects the string to the **fingerboard**
(`action + fret height`) where we used `action` (to the fret top). `computeString` adds
`fretH` (mm, default 1.0) to the per-fret deflection `cn` when `mottola` is on; with
`fretH`≈1.0 our setbacks match Mottola's to within ~0.3 mm across all six strings
(validated against E2…E4 = 5.72/4.03/3.19/2.63/3.61/1.94 mm). It's an opt-in alternative
physics (orthogonal to the §02 gain/anchor), not the project default. Reconciling against
the real in-tune saddle: Mottola/this mode nails the wound strings but over-compensates
the plain top E (~1.9 vs measured ~1.0 mm), where our gain-1 model is exact — so neither
is uniformly right and the true correction is wound-vs-plain dependent.

## New-saddle build spec (the active work)
Target action at the 12th fret: **2.0 mm low E → 1.6 mm high E** (down from 2.64 mm
measured on the 6th). That's a uniform ~0.64 mm action drop = ~1.28 mm lower saddle.

Saddle blank: **75 mm long × 3 mm thick**, flat base. String spacing 11 mm →
55 mm spread, 10 mm clear at each end.

Per-string targets (string position measured from the **bass end**; height from the
flat **base** to the crest at the break point; break measured forward from the
**back/pin-side face**):

| String | Pos from bass end | Crest height | Break from back face |
|--------|-------------------|--------------|----------------------|
| 6 E2   | 10 mm | 6.42 mm | 3.00 mm (front face) |
| 5 A2   | 21 mm | 6.72 mm | 3.00 mm (front face) |
| 4 D3   | 32 mm | 6.92 mm | 3.00 mm (front face) |
| 3 G3   | 43 mm | 6.83 mm | 3.00 mm (front face) |
| 2 B3   | 54 mm | 6.52 mm | 1.83 mm |
| 1 E4   | 65 mm | 5.61 mm | 1.99 mm |

Notes:
- The four bass strings' ideal breaks fall *in front of* the 3 mm slot, so they are
  **clamped to the front face**; this leaves the low E ~3 cents flat (within noise).
- Crest heights are the old saddle's profile lowered 1.28 mm; they give the ~420 mm
  radius + bass tilt and hit 2.0 / 1.6 at the 12th.
- Top profile = 400 mm radius across the length + bass-side raised ~0.8 mm (the
  bass end stands ~1.1 mm proud of the treble end).
- The B-string height reading was a noisy outlier; the model fairs it onto the curve.

Reference data (base→crest heights, mm) — old saddle vs. an over-sanded blank:
```
str  old   blank(scrapped)
6   7.70   7.75
5   8.00   8.32
4   8.20   8.56
3   8.11   8.40
2   7.80   7.41
1   6.89   6.59
```

## Files
(Layout is flat at the repo root — `index.html`, `README.md`, `saddle/`, `vendor/`.)
- `index.html` — the calculator (open directly in a browser). Section 07 also
  **generates a parametric OpenSCAD saddle** (`Download .scad`): crest heights are
  derived from the as-built Action f12 + target action @12th (uniform base-sand or
  per-string, both overridable); the fore-aft break of each string's crown comes
  from the **target-action** compensation (`REST`). Default state reproduces `saddle_reference.stl`
  (uniform −1.28 mm). Output is a faired radius+tilt top via a hull-lofted solid.
  `saddleModel()` is the single source of geometry; `generateScad()` emits the text.
  Section 07 also has an **in-page 3D preview** that runs the *actual generated
  `.scad`* through **OpenSCAD compiled to WebAssembly** (`vendor/openscad.wasm`),
  reads back the STL, and shows it with three.js + OrbitControls. The ~8 MB engine
  lazy-loads on the first "Render preview" click; a fresh wasm instance is made per
  render (Emscripten `callMain` is single-shot). `buildStl()` is the shared
  "run the .scad → STL bytes" step; both the preview and the **Download .stl**
  button use it (the latter exports the mesh straight to a file).
- `vendor/` — self-contained deps, no CDN (keeps the tool offline / Pages-friendly):
  `three.module.min.js` (r160), `OrbitControls.js`, `STLLoader.js`, and the OpenSCAD
  wasm trio `openscad.js` + `openscad.wasm.js` + `openscad.wasm` (release 2022.03.20,
  core build — fonts/MCAD omitted; the model uses neither).
- `README.md` — repo readme / Pages notes.
- `saddle/mk_stl.py` — **parametric** STL generator. Edit the arrays at the top
  (`strpos`, `crest`, `qbreak`, `LEN`, `TH`, crown `C`) and rerun:
  `python3 mk_stl.py` → writes the STL. Currently writes to an absolute path; change
  the `out=` line to a local path.
- `saddle/saddle_reference.stl` — current 1:1 solid replica (75×3 mm, ~30k tris).

## Open / likely next steps
- Deploy `web/` to GitHub Pages (public repo for a free account).
- Saddle reference variants the chat offered but didn't build: a **check-gauge**
  (negative profile comb) and a **holding cradle**. (OpenSCAD parametric export is
  now built into `web/index.html` §07.)
- After building: strobe-verify intonation at the new action and fine-tune; recheck
  neck relief / 1st-fret buzz once action drops.
