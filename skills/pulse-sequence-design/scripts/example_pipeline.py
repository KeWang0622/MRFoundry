#!/usr/bin/env python3
"""Complete, tested simulation-study pipeline to ADAPT (python example_pipeline.py --out demo).

  build exported .seq -> check the read-back file -> waveform figure -> KomaMRI Bloch simulation of the
  exported file -> measurement archive with provenance hashes -> standalone reconstruction from the archive
  alone -> orientation/value check against the known object -> report with MEASURED parameters.

Swap in your own builder (spoiled GRE here; inversion-recovery GRE, bSSFP and spin-echo builders are in
test_check_exported_seq.py), object, expectations and fit (../../mri-reconstruction/scripts/qmri_fit.py).
Keep reconstruct() importable/standalone: it reads only the archive, so it can be rerun on new data.
Needs pypulseq, numpy, matplotlib, komamripy (first KomaMRI call compiles Julia: start it early).
"""
import argparse, hashlib, json, os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
os.environ.setdefault('PYTHON_JULIACALL_HANDLE_SIGNALS', 'yes'); os.environ.setdefault('JULIA_NUM_THREADS', '4')
from mrfoundry_seqlib import simulate_with_koma, kspace_grid, plot_waveforms
from check_exported_seq import measure
from test_seqlib import cartesian_gre

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def reconstruct(archive, output):
    """Standalone: uses only the measurement archive (copy this function into reconstruct.py)."""
    d = np.load(archive); n = tuple(int(v) for v in d['matrix'])
    grid = kspace_grid(d['raw_signal'], d['k_cycles_per_m'], float(d['fov_m']), n)[0]          # [ky, kx] from the exported k
    img = np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(grid)))                                  # [y, x], index n//2 is r = 0
    np.savez(output, image=img, input_sha256=np.array(sha256(archive))); return img

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='demo'); a = ap.parse_args(); out = Path(a.out); out.mkdir(exist_ok=True)
    n, fov, te, tr, flip, sl = 32, 0.2, 6e-3, 20e-3, 15, 5e-3
    seq = cartesian_gre(str(out / 'sequence.seq'), n=n, fov=fov, te=te, tr=tr, flip=flip, sl=sl)
    rep, checks = measure(seq, te=te, tr=tr, flip=flip, slice_thickness=sl, rf_spoil=117, min_spoil_cycles=2, matrix=(n, n), fov=fov, monopolar=True, max_grad=32, max_slew=130)
    bad = [c for c in checks if not c['pass']]; assert not bad, bad                                # stop before simulating a wrong sequence
    plot_waveforms(seq, out / 'waveforms.png', t_window=(0, 3 * tr))
    yy, xx = np.mgrid[0:n, 0:n]; rho = ((xx - 12) ** 2 + (yy - 18) ** 2 <= 36) * 1.0 + ((xx - 22) ** 2 + (yy - 10) ** 2 <= 9) * 0.5
    x = (xx - n // 2) * fov / n; y = (yy - n // 2) * fov / n                                      # object index n//2 at r = 0, [y, x]
    np.savez(out / 'object.npz', x=x, y=y, rho=rho)
    sim = simulate_with_koma(seq, x, y, np.zeros_like(x), rho, np.full(rho.shape, 0.3), np.full(rho.shape, 0.005))
    np.savez(out / 'simulation.npz', raw_signal=sim['samples'], k_cycles_per_m=sim['k'], adc_times_s=sim['t'], fov_m=fov, matrix=np.array([n, n]),
             sequence_sha256=np.array(sha256(seq)), object_sha256=np.array(sha256(out / 'object.npz')))
    img = reconstruct(out / 'simulation.npz', out / 'recon.npz')
    corr = float(np.corrcoef(abs(img).ravel(), rho.ravel())[0, 1]); assert corr > 0.98, f'orientation/centring mismatch: corr {corr:.3f}'
    report = {'measured_from_export': {k: rep[k] for k in ('te_ms', 'tr_ms', 'excitation_flip_deg', 'excitation_slice_fwhm_mm', 'excitations_before_first_adc')},
              'checks': {c['item']: c['pass'] for c in checks}, 'bloch_simulator': 'KomaMRI via komamripy', 'image_object_correlation': corr}
    (out / 'report.json').write_text(json.dumps(report, indent=1)); print(json.dumps(report))

if __name__ == '__main__':
    main()

