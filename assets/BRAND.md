# MRFoundry identity

The identity pairs a friendly blue-and-ivory MRI scanner mascot with a
two-tone **MRFoundry** wordmark. The character has a rounded scanner body,
a visible bore, a short patient table and a small smiling face.
Use the supplied artwork; preserve its proportions and colors.

## Assets

| Asset | Use |
| --- | --- |
| `mrfoundry-logo-light.svg` / `.png` | Full lockup on light backgrounds |
| `mrfoundry-logo-dark.svg` / `.png` | Full lockup on dark backgrounds |
| `mrfoundry-wordmark-light.svg` / `-dark.svg` | Wordmark without the mascot |
| `mrfoundry-mark.svg` / `.png` | Standalone mascot |
| `mark-24.png` through `mark-512.png` | Square, transparent icon sizes |
| `favicon.ico` | Multi-resolution browser icon |
| `mri-mascot.png` | Full-size transparent artwork |
| `mrfoundry-mascot-trimmed.png` | Same artwork with transparent padding removed |

`logo.svg`, `mrfoundry-mark-light.svg` and `mrfoundry-mark-dark.svg` are compatible
aliases for the same standalone mascot. `mri-mascot-transparent.png` and
`mri-agent-transparent.png` are identical aliases of the full-size PNG.

## Format and color

The lockups contain an embedded raster mascot and vector lettering; they are
self-contained SVGs. The lettering uses outlined Avenir Next Heavy **MR** and
Baskerville Bold **Foundry** letterforms. No fonts or images are fetched from
the network.

The lettering uses cobalt `#2876E8` and deep ink `#132536` on light backgrounds,
and blue `#82B7FF` and light lettering `#EDF3FA` on dark backgrounds. The mascot
uses blue, ivory and navy illustration colors in both modes.
Preserve aspect ratio and leave clear space around the artwork.

## Provenance

The mascot and its transparent cutout were made with OpenAI image generation.
Exact prompts are in
[mascot-generation-prompt.txt](mascot-generation-prompt.txt) and
[mascot-alpha-prompt.txt](mascot-alpha-prompt.txt).
[mascot-provenance.json](mascot-provenance.json) records source and asset hashes,
formats and aliases.

These assets are decorative identity artwork, not scanner specifications,
patient images or simulation results. Keep them separate from scientific data.
