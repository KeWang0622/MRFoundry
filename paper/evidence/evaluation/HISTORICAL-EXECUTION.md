# Historical offline execution manifest

This record describes the retained **2–3 November 2026 offline Core/Hard comparison**: 240 Core pairs and 134 Hard pairs, each with a no-skills arm and a skills-plus-discovery-instruction arm. It is a source-based reconstruction, not a newly executed experiment or an immutable run manifest. No models, graders or statistical analyses were rerun. Private Hard identities, prompts, checks and traces are omitted.

The inspected study checkout is clean at `8cede909b1808bc09dea00cc1dd3cd0789c74ac6`. This is the **handoff commit**, not proof of the exact files deployed at each trial start. Sources S01–S26 below are identified by repository-relative path and SHA-256 in [source-provenance.json](source-provenance.json). Original operational logs and private records are not redistributed. Sources distinguish dated observations, retained implementation and unimplemented recommendations.

## Host, gateway and model identity

- **Agent host:** Codex CLI **0.159.2**, `codex app-server --stdio`, used for every analysed model. **Gateway:** `@jeffreycao/copilot-api` **2.8.6**, study endpoint on host loopback port 4143; the arm's loopback port 4141 relayed to it. Provider key `copilot_api`, Responses wire API, no OpenAI authentication. [S01, S03, S05, S07, S20]
- **Requested reasoning:** nominal `medium` in the host configuration and task turn. The 2 November probe reported no reasoning for Claude Sonnet 5.5 at medium (reasoning at high), reasoning for Claude Opus 5.5 at all tested levels, and more reasoning for Gemini 4 Argon at medium than at none. Kimi output grew with effort, but no medium-specific equivalence was established. Non-OpenAI reasoning-token counters could be zero despite reasoning items. These are probe observations, not per-request provider-budget verification. [S01; S19, line 491]
- The following is the retained **request-alias → publication-label mapping**, not an immutable vendor snapshot map. The runner forwards the selected alias; effective backend snapshots, provider-side alias resolution, sampling defaults and provider/gateway retry histories are not recoverable here. [S08, S11, S21, S23]

| Gateway request alias | Published label |
|---|---|
| `claude-haiku-5-5` | Claude Haiku 5.5 |
| `claude-opus-5-5` | Claude Opus 5.5 |
| `claude-sonnet-5-5` | Claude Sonnet 5.5 |
| `gemini-3.8-flash` | Gemini 3.8 Flash |
| `gemini-4-argon` | Gemini 4 Argon |
| `gpt-5.3-codex` | GPT-5.3 Codex |
| `gpt-6.1-sol` | GPT-6.1 Sol |
| `gpt-6.1-terra` | GPT-6.1 Terra |
| `kimi-k3` | Kimi K3 |
| `mai-code-1.1-flash` | MAI Code 1.1 Flash |

All ten aliases occur in the Core analysis. Hard uses seven of them in unequal cohorts, as reported in the supplement; it is not a common-coverage model ranking. A planned eleventh model, Grok 4.7, was excluded after nine started Core pairs because its API rejected the host's custom file-editing tool (HTTP 422); it was not replaced. [S22, line 149; S23]

## Runtime, isolation and intervention

The documented host was a shared Linux x86-64 development container. Each arm began with an empty CPython **3.12.14** virtual environment and its own Julia depot; **Julia 1.10.12** was on PATH. The study/grader environment has a retained requirements file, but agents installed task dependencies during their attempts: that file is not a per-arm package lock. Numerical-library/Julia thread variables were set to one. No immutable container digest, exact CPU model, GPU entitlement, guaranteed CPU share or per-arm dedicated memory allocation is retained. The documented host memory cgroup was **56 GiB**, `oom.group=1`, and the **2.6 TB** SSD was shared with other projects. A log mentions a 32-CPU load denominator; this does not establish an allocation to each arm. [S01, S08, S19, S20, S25]

The Linux recipe builds `runner4l` through asserted text replacements over archived `runner4`. Its namespace wrapper isolates user/mount/PID/network/IPC/UTS state, private HOME (512 MB tmpfs), private temporary storage, and read-only staged inputs. It hides other arms, prior study outputs, graders, host skills and credentials. Preparation and the actual app-server preflight probe these boundaries before a task turn. [S01–S04, S09]

Offline launch explicitly sets native search to `disabled` and shell egress to `pypi.org`, `files.pythonhosted.org`, `pkg.julialang.org`, `julialang.org`, `julialang.net` (the proxy also matches their subdomains), plus the separate model relay. Public-address checks and ports 80/443 constrain package egress; private networks/instance metadata are blocked and attempts logged. This is restricted package access, not a frozen package mirror. [S04, S06]

Both arms receive identical task text and staged input hashes. `stage.py` writes the original task prompt to `TASK.txt`; `run3.py` sends that file verbatim as the task-turn text. No additional generic task preamble was found. Task-specific prompts are not reproduced here. The runner disables user plugins/apps, memories, hooks, multi-agent/browser/computer-use features and MCP servers, clears custom developer instructions, and disables non-system host skills. Ordinary system-skill catalogs are compared across arms. The host's built-in system prompt/tool schemas were not independently archived here. [S08–S11]

The skills arm exports committed `skills/` files from MRFoundry `bd49b9556146bcd70ab1026c52d67713f4cf2e7f` and adds the following **exact** project `AGENTS.md` block, extracted from that commit's `agents-pointer.md`. Project-instruction allowance is 32,768 bytes for this arm and zero for the control. Thus the intervention is **skills plus discovery instruction**; reading/compliance is not forced. The extracted file's SHA-256 is `7e8405a8fb05d5d2316f3238e887c64c09e629454c6483a5e159b76db62f856c`. [S05, S08, S09, S26]

```markdown
## MRI work in this project

MRFoundry MRI skills are installed in `.agents/skills/` (or your agent's skills folder). Before writing code
for an MRI task, read the ONE matching `SKILL.md`, follow its route table to the helper or reference it names,
and import its tested scripts instead of re-deriving their maths. Open other files only when the table
points to them.

- acquisition, pulse sequences, RF/gradient waveforms, Bloch simulation: `pulse-sequence-design`
- images or parameter maps from k-space or images (reconstruction, relaxometry, ASL, DCE, QSM): `mri-reconstruction`
- diffusion-weighted data: `diffusion-mri`
- hardware, field maps, shimming, coils, SAR, PNS, noise and SNR: `mri-hardware`
- trained reconstruction networks: `deep-learning-recon`
- studies with subjects or groups, statistics, reports and papers: `mri-research-workflow`
- spectroscopy, image analysis, formats and references: `mri-research`

Before finishing, run `python .agents/skills/mri-research-workflow/scripts/finish_check.py` with every
deliverable name and the documented entrypoint command, and fix every FAIL line.
```

## Caps, stopping and retry behavior

| Item | Retained rule or observation |
|---|---|
| Task clock | Both arms launch concurrently. Per-arm wall time starts immediately before `turn/start`; model latency and tool work consume it. Core: 45 min for two relaxometry/QSM types, three writing/review types and pilot-study design (6 types); 60 min for 18 other types. Hard: 3 types at 120 min, 6 at 150, 2 at 180, 4 at 210. [S02, S11, S13, S21–S22] |
| Normal/cap termination | A `turn/completed` ends the attempt. At its deadline the runner records timeout and sends `turn/interrupt`; closing the transport sends process-group SIGTERM, waits 5 s, then SIGKILL if necessary. Deliverables are graded as left. Exceptions/EOF are recorded as infrastructure/transport errors. [S08, S11–S12] |
| Wrapper watchdogs | Retained code allows 900 s for preparation, 300 s for staging, `2 × task cap + 900 s` for the run wrapper and 2,400 s per grading call. These are wrapper limits, not extra agent task time. A wrapper exception yields `pipeline_error`; these code paths do not establish actual incident counts. [S12] |
| Retry | The runner refuses already prepared/staged/executed states and has **no implicit task retry**. The batch skips entries with existing output folders; the keeper checks every 5 min and relaunches missing-output queue entries. The setup-error folders were explicitly quarantined so unchanged pairs could be restarted. Provider/host internal HTTP retry/backoff settings and counts are unavailable. [S09–S13, S17, S01] |
| Token/budget gate | No runner-level task token cap was specified. The batch has a credit gate (retained defaults: 1,350,000 used or 85% of entitlement); a separate 10-min budget guard pauses new pairs at 90% of its supplied window budget. The dated record raises that budget from 300k to 400k credits around 03:45Z on 3 November, with a 360k pause point. Running pairs finish; these are launch gates, not equal per-model token budgets. Actual invocation/trigger history is not fully retained. [S13, S16, S18 §c4, S19] |
| Concurrency | `parallel.txt` and `cpu_budget.txt` gate launches; Linux niceness targets +10. Values and pauses changed during the study; there was no fixed dedicated per-arm allocation. A STOP file terminates the Linux batch after running pairs drain. [S02, S13, S19] |

The fairness research note recommends repeated runs, neutral-scaffold checks and up to two infrastructure retries. Those recommendations are **not evidence that these procedures were performed**. The reported dataset contains one attempt per selected model–instance–condition combination, and the original supplement reports no outcome-based reruns for the ten analysed models. Its broad “no reruns/exclusions” wording must be read alongside the separate pre-turn restart and excluded-model records. [S18, S22–S24]

## Resource-policy chronology and unresolved exposure

- **2 November, about 09:12Z:** disk cleanup began for finished pairs, removing rebuildable environments/caches/private temporary files while retaining deliverables, code, traces and grades. Historical prose calls the pause/resume thresholds 300/400 “GB” free and 1.4/1.3 “TB” of project usage. The retained guard measures bytes divided by 2³⁰: its actual numeric thresholds are 300/400 GiB free and 1,400/1,300 GiB used. [S01, S15]
- **2 November, about 11:55Z:** after recursive `finish_check` temporary-input copying, new pairs used private `/tmp` outside the workspace. One retained Core skills arm had produced 232 GB (as reported) of temporary data; its pair finished and was graded before cleanup, with outcome unchanged. The guard also stops an active arm when workspace plus private temporary storage exceeds **60 GiB** (called “60 GB” in the historical prose), using process-group SIGKILL and a resource-stop marker. Its 5-min polling is not a strict instantaneous storage quota. [S01, S15; S19, line 508]
- **2 November, 13:33:55Z and 13:37:56Z:** the progress log records external pod-health terminations of two broad filesystem searches and an agent plotting process. It does not provide an auditable mapping of these kills to analysed arms here. The memory guard's documented operational thresholds were then reduced to pause at 24, resume below 18 and kill above 32 GiB of pod anonymous memory, polling every 10 s and killing the largest sandbox session when necessary. Its retained defaults (34/26/44) are **not** substituted for those dated settings. [S14; S19, line 511]
- **3 November, 00:25Z → about 00:45Z:** after rapid memory growth in three agent scripts, an inherited **8 GiB per-process RLIMIT_DATA** was introduced in each newly prepared arm's policy; it can raise an allocation error inside the arm. It is not an 8 GiB total-arm RSS allocation. Pairs prepared earlier lacked it. The first deployment omitted an import, causing pre-turn `NameError` failures until about **02:45Z**. Within the reported Core/Hard scope there were **143 pair-setup failures: 94 Core + 49 Hard**, not 143 individual model attempts. Failed setup folders were retained/quarantined and those pairs restarted unchanged after the fix. [S01, S02, S04; S19, lines 522–542]
- **3 November, about 16:05–16:10Z:** the final results/log report completion of the offline queues; guards were stopped. “No infrastructure exclusions” in the final analysis does not prove absence of external interruptions or uniform resource exposure. [S19, S24]

The local handoff lacks a complete pair-by-policy ledger, active-pair transition record, guard logs linked to every analysed arm, and arm-specific disk/memory/pod-termination counts. The original supplement's timestamp-derived memory-exposure totals cannot be independently checked against arm policies here; they are not reused as verified exposure counts. Memory settings were documented as matched within a newly prepared pair, but historical disk-policy parity and interference from shared resources cannot be established for every pair. No causal effect is assigned to these incidents, and no scores were changed.

## Reproduction boundary

This manifest preserves the identifiable host/gateway versions, requested aliases, exact discovery instruction, script hashes, caps and incident rules. It does **not** provide immutable effective model snapshots, the complete deployed runner/config state per trial, a container digest, guaranteed hardware allocations, per-arm final package locks, all egress/retry/termination logs or private Hard scoring materials. Re-running today's public tasks and defaults therefore cannot be claimed to reproduce this historical execution environment exactly. The frozen numerical records and their separate provenance remain unchanged.
