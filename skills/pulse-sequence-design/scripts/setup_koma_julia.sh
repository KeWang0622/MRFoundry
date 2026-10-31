#!/bin/sh
# Lean KomaMRI install for backend='julia' of mrfoundry_seqlib.simulate_with_koma (MRFoundry).
# Use it when komamripy's automatic Julia install stalls (no Julia appears after about 3 minutes, a juliapkg lock wait,
# or /tmp is not writable). Everything goes into DIR (default ./koma_julia) inside the workspace; no /tmp, no home folder.
#   sh setup_koma_julia.sh [DIR]            install Julia 1.10 LTS + KomaMRICore + KomaMRIFiles, precompile (5-15 min)
#   sh setup_koma_julia.sh [DIR] --dry-run  print what would be downloaded
# Run it in the background with a log in the workspace and poll the log; it ends with the two lines to export:
#   MRFOUNDRY_JULIA=... MRFOUNDRY_KOMA_PROJECT=...
set -e
TARGET=./koma_julia; DRY=0
for a in "$@"; do case "$a" in --dry-run) DRY=1 ;; *) TARGET=$a ;; esac; done
case "$TARGET" in /*) DIR=$TARGET ;; *) DIR=$(pwd)/$TARGET ;; esac
VER=1.10.10
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)  URL=https://julialang-s3.julialang.org/bin/mac/aarch64/1.10/julia-$VER-macaarch64.tar.gz ;;
  Darwin-x86_64) URL=https://julialang-s3.julialang.org/bin/mac/x64/1.10/julia-$VER-mac64.tar.gz ;;
  Linux-x86_64)  URL=https://julialang-s3.julialang.org/bin/linux/x64/1.10/julia-$VER-linux-x86_64.tar.gz ;;
  Linux-aarch64) URL=https://julialang-s3.julialang.org/bin/linux/aarch64/1.10/julia-$VER-linux-aarch64.tar.gz ;;
  *) echo "unsupported platform $(uname -s)-$(uname -m): get Julia 1.10 from julialang.org" >&2; exit 2 ;;
esac
JL=$DIR/julia-$VER/bin/julia
if [ "$DRY" = 1 ]; then echo "would download $URL into $DIR and create $DIR/env"; echo "MRFOUNDRY_JULIA=$JL MRFOUNDRY_KOMA_PROJECT=$DIR/env"; exit 0; fi
mkdir -p "$DIR/depot" "$DIR/env"
if [ ! -x "$JL" ]; then
  echo "downloading $URL"; curl -fsSL -o "$DIR/julia.tar.gz" "$URL"; tar -xzf "$DIR/julia.tar.gz" -C "$DIR"
fi
export JULIA_DEPOT_PATH="$DIR/depot" JULIA_PKG_PRECOMPILE_AUTO=1 TMPDIR="$DIR"
"$JL" --project="$DIR/env" -e 'import Pkg; Pkg.add(["KomaMRICore", "KomaMRIFiles"]); using KomaMRICore, KomaMRIFiles; println("KomaMRICore ", pkgversion(KomaMRICore), " ready")'
echo "export JULIA_DEPOT_PATH=$DIR/depot MRFOUNDRY_JULIA=$JL MRFOUNDRY_KOMA_PROJECT=$DIR/env"
