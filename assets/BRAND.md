# MRFoundry identity

The current identity pairs a friendly blue-and-ivory MRI scanner mascot with the
original two-tone **MRFoundry** wordmark. The approved character has a rounded
scanner body, a visible bore, a short patient table and a small smiling face.
Use the supplied artwork; preserve its proportions and colors.

## Assets

| Asset | Use |
| --- | --- |
| `mrfoundry-logo-light.svg` / `.png` | Full lockup on light backgrounds |
| `mrfoundry-logo-dark.svg` / `.png` | Full lockup on dark backgrounds |
| `mrfoundry-wordmark-light.svg` / `-dark.svg` | Original outlined lettering, unchanged |
| `mrfoundry-mark.svg` / `.png` | Standalone mascot |
| `mark-24.png` through `mark-512.png` | Square, transparent icon sizes |
| `favicon.ico` | Multi-resolution browser icon |
| `mri-mascot.png` | Approved full-size transparent artwork |
| `mrfoundry-mascot-trimmed.png` | Same artwork with transparent padding removed |

`logo.svg`, `mrfoundry-mark-light.svg` and `mrfoundry-mark-dark.svg` are compatible
aliases for the same standalone mascot. `mri-mascot-transparent.png` and
`mri-agent-transparent.png` are identical aliases of the approved full-size PNG.
The latter no longer includes a laptop; `mri-mascot.png` no longer includes a
studio background. Existing links therefore use the current character.

The lockups contain an embedded raster mascot and vector lettering; they are
self-contained SVGs, not wholly vector illustrations. The original outlined
Avenir Next Heavy **MR** and Baskerville Bold **Foundry** letterforms are preserved.
The standalone wordmark SVG files are byte-identical to the earlier identity.
No fonts or images are fetched from the network.

The lettering uses cobalt `#2876E8` and deep ink `#132536` on light backgrounds,
and blue `#82B7FF` and light lettering `#EDF3FA` on dark backgrounds. The mascot
retains its approved blue, ivory and navy illustration colors in both modes.
Preserve aspect ratio and leave clear space around the artwork.

## Provenance

The mascot was generated and its transparent cutout refined with OpenAI image
generation, then approved on **2026-11-03**. Exact prompts are in
[mascot-generation-prompt.txt](mascot-generation-prompt.txt) and
[mascot-alpha-prompt.txt](mascot-alpha-prompt.txt).
[mascot-provenance.json](mascot-provenance.json) records hashes, aliases and the
unchanged original wordmarks. Other `*-prompt.txt` files are explicitly labeled
historical and describe earlier artwork.

These assets are decorative identity artwork, not scanner specifications,
patient images or simulation results. Keep them separate from scientific data.
