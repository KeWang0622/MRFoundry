# MRFoundry identity

The MRFoundry mascot and emblem depict a **long-bore MRI scanner**: a substantial
magnet barrel extends behind the front face, the patient tunnel has visible depth,
and the table enters along the tunnel axis. Preserve this silhouette; do not
shorten the housing into a thin gantry ring.

## Logos and symbol

| Asset | Use |
| --- | --- |
| `mrfoundry-logo-light.svg` | Full lockup on white or light backgrounds |
| `mrfoundry-logo-dark.svg` | Full lockup on dark backgrounds |
| `mrfoundry-wordmark-light.svg` / `-dark.svg` | Typography without the scanner symbol |
| `mrfoundry-mark-light.svg` / `-dark.svg` | Compact three-quarter MRI symbol |
| `mrfoundry-mark.svg` | Light-background symbol, retained as the default icon |
| `logo.svg` | Compatibility alias for the default symbol in the repository |

Blue **MR** uses outlined Avenir Next Heavy; **Foundry** uses outlined Baskerville
Bold. These original letterforms and full-logo dimensions are unchanged. SVGs
contain paths rather than bundled fonts or network font requests. Preserve aspect
ratio, allow clearspace of at least one-quarter cap height, and do not substitute
platform fonts. The light/dark names indicate the intended background.

Primary palette: cobalt `#2876E8`, deep ink `#132536`, dark-surface blue `#82B7FF`,
and light lettering `#EDF3FA`. The compact emblem uses a pale blue `#C6E0FF`
interior to separate the tunnel wall from its opening. Paper body typography is
separate and retains the manuscript template fonts.

## Mascot illustrations

- `mri-mascot-transparent.png`: isolated cream-and-blue scanner for headers,
  websites and light backgrounds; genuine alpha transparency.
- `mri-mascot.png`: the same long-bore design on a quiet dark studio background,
  intended for presentation covers and closing slides.
- `mri-agent-transparent.png`: illustrated scanner with a laptop, for explanatory
  agent-workflow figures. Keep it separate from scientific image panels.

The scanner illustrations were edited with OpenAI image generation on
2026-10-29, retaining the friendly MRFoundry identity while correcting its magnet
depth and patient-tunnel proportions. Exact prompts are in the corresponding
`*-prompt.txt` files. The vector emblem was authored directly in SVG; its design
specification is in `mrfoundry-logo-prompt.txt`. All are decorative identity
artwork, not physical scanner documentation, acquired images or simulation data.
