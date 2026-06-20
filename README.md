# Compensation Calculator

A single-file web tool that computes per-string **nut and saddle compensation** for an
already-built acoustic guitar, after Trevor Gore's deflection-tension model, and draws a
top-view fabrication map for the bench.

## Use it

Open `index.html` in any browser, or visit the GitHub Pages site once published:
`https://eudes.github.io/guitar-compensation-calculator/`

Everything runs locally in the browser — no build step, no data leaves the page. The 3D preview uses a locally vendored copy of three.js and OpenSCAD-WebAssembly (in `vendor/`), so it works offline too; no CDN.

## What it does

- Per-string saddle setback and nut offset, optimised to flatten the intonation error across the fretboard
- Live before/after error curve (tap or hover for exact cents)
- Saddle break-point map against the existing slot, with an out-of-slot warning
- Nut compensation map from the original straight line
- **OpenSCAD 3D saddle export** — crest profile derived from your target action @12th (uniform base-sand or per-string, both overridable), break points from the compensation result; downloads a parametric `.scad` you can render or export to STL
- **In-page 3D preview** — runs the generated `.scad` through OpenSCAD itself (WebAssembly) and renders the result with three.js; the engine lazy-loads on first use, so the rest of the tool stays instant
- **Download .stl** — exports a mesh straight from the same OpenSCAD render, ready to slice or print without opening OpenSCAD
- String presets: D'Addario, Martin, Elixir, John Pearse (gauges 10–13), with editable per-string values
- Toggles: bending stiffness (off = pure Gore), nut compensation on/off, distances to slot centre or inner break edge

String unit weights are D'Addario's published values; wound-string core diameters follow
their core rule; plain-string masses are computed from steel density.
