# KomaMRI simulation of an exported Pulseq file without Python bindings (MRFoundry, tested with Julia 1.10,
# KomaMRICore 0.13, KomaMRIFiles 0.11). Called by mrfoundry_seqlib.simulate_with_koma(..., backend="julia"):
#   julia --project=<env with KomaMRICore and KomaMRIFiles> koma_sim.jl seq phantom.bin signal.bin dt dt_rf gmax smax
# phantom.bin: Int64 n, then n Float64 values each of x, y, z (m), rho, T1, T2, T2s (s), dw (rad/s).
# signal.bin: ComplexF64 samples of every ADC in chronological order (ADC phase offsets applied), one coil.
using KomaMRICore, KomaMRIFiles

seqf, fin, fout = ARGS[1], ARGS[2], ARGS[3]
dt, dtrf, gmax, smax = parse.(Float64, ARGS[4:7])
io = open(fin, "r"); n = read(io, Int64)
v = [Vector{Float64}(undef, n) for _ in 1:8]
for a in v; read!(io, a); end
close(io)
x, y, z, rho, T1, T2, T2s, dw = v
obj = Phantom(; name="object", x=x, y=y, z=z, ρ=rho, T1=T1, T2=T2, T2s=T2s, Δw=dw)
sys = Scanner(; limits=HardwareLimits(; Gmax=gmax, Smax=smax))
seq = read_seq(seqf)
params = Dict{String,Any}("return_type" => "mat", "gpu" => false, "precision" => "f64", "Δt" => dt, "Δt_rf" => dtrf)
sig = simulate(obj, seq, sys; sim_params=params, verbose=false)
open(fout, "w") do f
    write(f, ComplexF64.(vec(sig)))
end
