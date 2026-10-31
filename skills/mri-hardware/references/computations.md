# Hardware and safety computations: formulas, conventions and sources

All quantities in SI units. Functions refer to `scripts/mrfoundry_hwlib.py`.

## Coil fields (quasi-static)

Biot-Savart for a straight segment from **a** to **b** at point **p**, with
**r1 = a − p**, **r2 = b − p**:

B = μ0 I / (4π) · (r1 × r2)(|r1| + |r2|) / (|r1||r2|(|r1||r2| + r1·r2)).

Summing segments of a polyline approximates curved conductors; the error of an
n-gon circle falls roughly as 1/n². Analytic references: loop on axis
Bz = μ0 I R² / (2 (R² + z²)^{3/2}); Helmholtz pair (separation R) centre field
(4/5)^{3/2} μ0 N I / R; Maxwell pair (separation √3 R, opposed currents) gradient
3 μ0 N I R² h / (R² + h²)^{5/2} with h = √3 R / 2; finite solenoid centre field
μ0 n I (L/2) / √((L/2)² + R²); long wire μ0 I / (2π d). Quasi-static fields are
adequate for gradient and shim coils and for low-frequency RF estimates; at
Larmor wavelengths comparable to the body, use full-wave EM.

Gradient efficiency is the fitted dBz/dx per ampere in a stated region; linearity
is reported as deviation from the fitted (or centre) gradient, normalized either
pointwise or by G·r_max. Turner (1993) reviews coil design methods.

## Spherical-harmonic field description and shimming

Inside a source-free region, Bz satisfies Laplace's equation and can be expanded
in real solid harmonics (Romeo & Hoult 1984). The helpers use unnormalized
Cartesian forms up to 3rd order (z = bore axis); dividing by r0^l makes each
coefficient the term's field at radius r0. Shim currents solve a bounded linear
least-squares problem using measured (or modelled) per-unit-current field maps of
each channel; a free constant term represents the centre-frequency adjustment.
Report residual standard deviation in the target mask and channels at a limit.

## RF energy, B1+rms and SAR

Flip angle θ = 2π γ̄ ∫B1(t) dt. For a pulse of duration τ and peak B1max,
∫B1 dt = B1max τ · (mean/peak of the shape). RF energy per pulse ∝ ∫|B1|² dt;
B1+rms over a window T is √(Σ∫|B1|² dt / T). For a given coil and body, SAR is
proportional to B1rms² and, in the quasi-static regime, approximately to B0²
(Collins & Wang 2011 discuss limits of this scaling).

IEC 60601-2-33 (edition 3.x) volume SAR limits, 6-min average: whole body 2 W/kg
(normal) / 4 W/kg (first level); head 3.2 W/kg; partial body 10 − 8·f (normal) or
10 − 6·f (first level) W/kg with f = exposed mass / patient mass; over any 10 s,
SAR must not exceed twice the stated limit. Local SAR (10 g): head and trunk
10 W/kg, extremities 20 W/kg. Confirm the edition and amendments in force and any
implant-specific conditions (often stated as a B1+rms limit). This is research
orientation, not a compliance assessment.

## Gradient switching and PNS

Slew rate dG/dt; dB/dt at radius r from isocentre ≈ slew · r for an ideal linear
gradient (actual coil fields extend and include concomitant components). The
effective stimulus duration t_s,eff of a monotonic segment is its peak-to-peak
change divided by its maximum rate of change. A hyperbolic strength-duration
model gives the threshold dB/dt = rb (1 + c / t_s,eff); IEC 60601-2-33 uses
rb = 20 T/s (E-field form 2.2 V/m) and c = 0.36 ms for whole-body gradients, with
normal-mode limit 80 % and first-level 100 % of this threshold. Measured
thresholds vary with coil and subject (den Boer et al. 2002); vendor models such
as SAFE predict coil-specific stimulation.

## Noise, coil combination and SNR

Noise covariance Ψ = n nᴴ / N from noise-only samples; prewhitening with
W = L⁻¹ (Ψ = L Lᴴ). Optimal combination (Roemer et al. 1990)
ρ = sᴴΨ⁻¹x / √(sᴴΨ⁻¹s) yields images in SNR units when Ψ is the per-sample noise
covariance (Kellman & McVeigh 2005). SNR ∝ voxel volume · √(total sampling time),
with total sampling time ∝ averages × phase encodes / readout bandwidth per pixel;
the B0 dependence is ~B0 when sample noise dominates and steeper (~B0^{7/4}) when
coil noise dominates at low field (Hoult & Richards 1976).

## Sources

- IEC 60601-2-33: Medical electrical equipment — Particular requirements for the
  basic safety and essential performance of magnetic resonance equipment for
  medical diagnosis (ed. 3.2, 2015; check the current edition).
- Romeo F, Hoult DI. Magnet field profiling: analysis and correcting coil design.
  Magn Reson Med 1984;1:44–65.
- Turner R. Gradient coil design: a review of methods. Magn Reson Imaging
  1993;11:903–920.
- Roemer PB, Edelstein WA, Hayes CE, Souza SP, Mueller OM. The NMR phased array.
  Magn Reson Med 1990;16:192–225.
- Kellman P, McVeigh ER. Image reconstruction in SNR units: a general method for
  SNR measurement. Magn Reson Med 2005;54:1439–1447.
- Hoult DI, Richards RE. The signal-to-noise ratio of the nuclear magnetic
  resonance experiment. J Magn Reson 1976;24:71–85.
- Collins CM, Wang Z. Calculation of radiofrequency electromagnetic fields and
  their effects in MRI of human subjects. Magn Reson Med 2011;65:1470–1482.
- den Boer JA, Bourland JD, Nyenhuis JA, et al. Comparison of the threshold for
  peripheral nerve stimulation during gradient switching in whole body MR systems.
  J Magn Reson Imaging 2002;15:520–525.
