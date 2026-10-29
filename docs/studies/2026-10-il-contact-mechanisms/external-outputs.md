# What ChatGPT and NotebookLM returned, and how it checks out

Report on the three external deep-research outputs in this study, 29 October 2026. The user ran all three
tools. This file presents each output in readable form, translated where needed, with a verdict on every
claim. The verdicts come from checking the paper's full text (`data/verification.md`).
The outputs exactly as received are in `data/raw/`:
- `chatgpt_structured.tsv`
- `chatgpt_gist.md`
- `notebooklm.md`

**Verdicts:**
- **OK**: matches the paper.
- **ERR**: contradicted by the paper.
- **PART**: partly right; the deviation is stated.
- **NF**: no such paper found on the web or in OpenAlex.
- **FIG**: the number sits only in a figure, so it can't be checked from text.

**Question given to all tools:** For imitation-learned robot policies on contact-rich manipulation, which
failure mechanisms have been shown by intervention, not just correlation? For each one: what was changed, on
which task, in simulation or on a real robot, how big was the effect, and has anyone replicated it?

| | ChatGPT, structured prompt | ChatGPT, short prompt | NotebookLM |
|---|---|---|---|
| Prompt | Structured, written by Claude: definition of intervention, scope, 9 required columns, no invented numbers | The question only, written by the user | Not recorded |
| Mode | Deep research | Deep research | Deep research |
| Run time | Not recorded | Not recorded | Not recorded |
| Output | 9-row table, 5 papers | Summary, flowchart and 5-row table, in Dutch | Long essay, 6 mechanisms, ~34 links |
| Errors / partly right | 3 / 1 | 3 (2 citations not found, 1 wrong robot) / 0 | 4 / 5 |
| Papers shared with the other two | none | none | none |

---

## 1. ChatGPT deep research, structured prompt

A single table with the 9 requested columns. It skipped three things the prompt asked for: the
grasp-vs-insertion answer, the list of correlational claims it rejected, and the list of papers it consulted.
The replication column says "None found" in all rows.

| # | Mechanism (as claimed) | Intervention | Paper | Task, sim/real | Effect (as claimed) | Verdict |
|---|---|---|---|---|---|---|
| 1 | No brightness randomization → failure under new lighting | Data: lightness randomization on/off | Zhang et al. 2026, *Memorize, Adapt, Ignore*, arXiv 2609.38401, Table 3 | Cube pick-and-place, real, ACT on Franka | Without: 6/10, 1/10, 1/10 (base/bright/dark); with: 10/10, 8/10, 6/10; 10 trials | **OK**. Outside scope: pick-and-place, not contact-rich |
| 2 | Shape and texture varied together → worse generalization | Data: confounded vs independent variation | Same paper, Fig. 6c | "Objects on a scale", sim | Action error 0.0846 vs 0.0755 on novel categories | **OK** in direction (stated in text); numbers **FIG**. Outside scope |
| 3 | No force-vision curriculum → policy ignores force | Training: blur schedule fixed vs decaying | Liu et al. 2025, *FACTR*, arXiv 2502.17432, Fig. 9 and Table II | Box lifting, pivoting etc., **"simulated"** | Pivoting: fixed 16/25 vs linear 19/25 | **ERR**: FACTR is a real-robot study. Table II numbers are correct. The attention figure is Fig. 8 |
| 4 | No temporal memory → insertion fails | Architecture: BC vs BC-RNN | Mandlekar et al. 2021, *robomimic*, arXiv 2108.03298 | Square (nut on peg), sim | MH: BC 0% vs BC-RNN 2%; PH: 70% vs 80%; 50 trials | **ERR**: Table 1 says MH 52.7 vs 78.0, PH 78.7 vs 84.0 (3 seeds × 50 rollouts, max over training) |
| 5 | Camera loss → large drop; training for it recovers part | Training: MINT fine-tuning | Jiang et al. 2026, arXiv 2609.35003, Fig. 1b | 18 RoboCasa365 tasks, sim (π0.5, GR00T) and real (AgiBot G2) | Qualitative (caption quote) | **OK**. Outside scope: kitchen tasks with vision-language-action models |
| 6 | Single-step execution → lower success | Action horizon: sequence vs single | Yuan et al. 2024, *Unpacking the Individual Components of Diffusion Policy*, arXiv 2412.00084, Table 2 | ManiSkill, Adroit, sim | PegInsertionSide 80 → 55, TurnFaucet 59 → 35, Door 95 → 46; Hammer the exception; **"100 eval runs"** | **PART**: all numbers correct; the paper states no rollout count |
| 7 | No receding-horizon control → long tasks fail | Execution: receding horizon on/off | Same, Table 3 | Sim | Relocate 64 → 11, StackCube 99 → 88, Pen 71 → 73 | **OK** |
| 8 | MLP instead of U-Net denoiser → hard tasks fail | Architecture | Same, Table 4 | Sim | PegInsertionSide 80 → 21, Relocate 64 → 7; easy tasks unchanged | **OK** |
| 9 | No FiLM conditioning → large drop | Architecture | Same, Table 5 | Sim | PegInsertionSide 80 → 44, TurnFaucet 59 → 27, Relocate 64 → 2 | **OK** |

**Assessment.** This run read ablation tables accurately; every value it gave for *Unpacking Diffusion Policy*
is right. Its errors sit in a sim/real label, an older paper's numbers, and an invented trial count. Three of
its nine rows fall outside the contact-rich scope. It found two September 2026 papers that no other source
found.

---

## 2. ChatGPT deep research, short prompt (translated from Dutch)

The prompt was the question alone. The output was in Dutch, although the prompt was in English. That points
to account language or memory settings carrying over.

**Summary (translation).** Recent studies have identified several failure mechanisms and addressed them
experimentally.
- Vision-only policies fail on tasks with complex contact (tight fits, occlusion), and adding touch largely
  solves this.
- Imitation without force sensing fails on tasks that need torque, which improves with an F/T sensor and an
  adapted architecture.
- Other failures are poor generalization to new task configurations, which environmental constraints and
  online corrections solve.
- End-to-end policies react slowly to disturbances, which a hierarchical "slow-fast" approach with real-time
  feedback solves.
- In all cases the interventions improved results dramatically (for example ~35% → ~80%, or 0% → 100%).

**Flowchart (translation).**
1. Vision-only IL fails (occlusion, tight fit) → tactile sensors and multimodal fusion (MiTaS) → 35% to 80%.
2. No force feedback → slip when opening a screw cap → add an F/T sensor and a transformer → ~83%
   (DA-force) vs failing ablations.
3. Policy does not generalize to new configurations → environmental constraints and corrections → baselines
   ~0% → 100%.
4. Vision-only diffusion policy fails at tight assembly → force-conditioned diffusion plus data augmentation
   → better success than standard diffusion.
5. Open-loop IL reacts slowly to disturbances → reactive "slow-fast" diffusion policy (RDP) → >35% better
   than vision-only IL.

| # | Failure mechanism | Intervention | Task, robot | Effect | Replication | Source | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Vision-only policy fails through occlusion and complex contact | Multi-sensor input (GelSight + event-based tactile), transformer (MiTaS) | 5 contact-rich tasks (gear assembly, key insertion), real, **Flexiv Rizon** | 35% → 80% | None reported | Krohn et al. 2026, CoRL | **PART**: exists (arXiv 2606.06281); vision-only 35.5%, MiTaS 80% correct; robot is a **Franka Panda**; CoRL acceptance known only from a co-author's post |
| 2 | Key-in-slot: no generalization to new geometries | Environmental constraints, self-exploration, human corrections | Multi-stage slots and assembly, real | 0% → 100% (10/10) | Not replicated | Li & Brock 2026 | **NF**: no 2026 paper found; nearest is Li, Baum & Brock 2022/2023 |
| 3 | Missing force feedback → slip during cap opening | F/T sensor, dual-action transformer, gaze attention | Bottle-cap opening, real | 83.3% (DA-force); ablations failed | n/a | Kim et al. 2023, TRO | **OK**: arXiv 2202.09574; 83.3% over 18 trials; without force, reaching and grasping succeed but rotation fails. Venue not confirmed |
| 4 | Standard diffusion policy fails at tight assembly | Force-conditioned diffusion, data augmentation | Bimanual battery-cover assembly, real | "Improved success" | n/a | Shukla et al. 2025, NAMRC | **NF**: no such paper found; related Shukla et al. ICRA 2025 (sheet separation) |
| 5 | Open-loop IL reacts slowly to disturbances | Slow-fast reactive diffusion policy (RDP), AR tactile feedback | Peeling, wiping, bimanual lifting, real | >35% over visual IL | n/a | Xue et al. 2025, RSS | **OK**: ">35%" is in the abstract |

**Reproducibility notes (translation, abridged).**
- MiTaS: 30 demonstrations, 20 runs per model.
- The single-demonstration environment-constraint approach: 10 trials per configuration.
- Kim et al.: 90/10 split, about 18 trials.
- Shukla et al.: about 100 demonstrations.
- Xue et al.: 60–80 demonstrations per task.

The MiTaS and Kim details check out against the papers; the Li & Brock and Shukla details belong to papers
that could not be found.

**Assessment.** Without a definition of "intervention", the tool reported what most papers headline: a new
method beating baselines. Two of five citations could not be found. No paper IDs were given.

---

## 3. NotebookLM deep research

A long essay, "Empirical Analysis of Interventional Failure Mechanisms in Imitation-Learned Contact-Rich Robot
Manipulation". Its six mechanisms are summarized below with the claims as made and a verdict on each. The
citation numbers [n] refer to its source list (end of this section).

### 3.1 Multimodal action averaging

| Claim | Cites | Verdict |
|---|---|---|
| Regression heads output the average of multimodal actions; contacts create discontinuous landscapes | 1–4 | Textbook argument; not an intervention result |
| Real Push-T: IBC 0%, best GMM 20% → Diffusion Policy 95% | 1 | **OK**, but a method comparison, not a single-factor change |
| Robomimic: replacing unimodal heads with DP gives +46.9% | 2 | **PART**: 46.9% is DP's average gain over prior methods across 15 tasks on 4 benchmarks |
| On Tool-Hang, flow and diffusion stay above 80% while unimodal models fail at hook engagement | 6, 8 | **ERR**: [6] is *Much Ado About Noising*, which argues generative policies do **not** win through multimodality; "hook engagement" is not in it |
| "Replicated" by H3DP (+27.5% sim, +72.4% real), GPI, a visuotactile flow policy | 10, 7, 8 | Method gains, not replications. The flow-vs-DDIM claim (30% → 80%) is **PART**: with the same architecture it is 53% → 80% |

### 3.2 Compounding distribution shift and recovery data

| Claim | Cites | Verdict |
|---|---|---|
| Recovery data (DAgger, HG-DAgger, DART, Interventional MimicGen, MILE, DiscoDemo) fixes compounding error | 11–16 | A family of different interventions; "Interventional MimicGen" is really **IntervenGen** |
| Peg insertion: BC 39–40% → 78–80% | 11, 12, 16 | **PART**: DiscoDemo is 39% → 78% against the *strongest baseline*, averaged over 4 tasks; MILE reaches 80% after 4 iterations on an octagonal-block insertion, using only intervention data; "<40%" for BC is only in a figure (**FIG**) |
| "Mental Model Interventions" reached 80% on physical peg insertion | 11, 12, 15 | **PART**: the method is MILE (Model-based Intervention Learning) |

### 3.3 Action parameterization: velocity vs position

| Claim | Cites | Verdict |
|---|---|---|
| Position control beats velocity control with the architecture fixed | 1, 17 | **OK** (Diffusion Policy, Fig. 4) |
| Position control holds peak performance up to 4 steps of latency; velocity "failed" | 1, 17 | **OK** on 4 steps; the paper says velocity control is "more affected", not that it fails |
| Equivariant DP: absolute SE(3) actions give +21.9% on 12 MimicGen tasks | 21 | **ERR**: +21.9% is the gain from SO(2) equivariance |
| DP3, SCDP, OpenVLA-OFT "replicate" it | 20, 22, 5 | These adopt absolute actions; none removes them, so not replications |

### 3.4 Action horizon and temporal context

| Claim | Cites | Verdict |
|---|---|---|
| DP: inverted U in action horizon, best near 8 steps | 1 | **OK** |
| ACT: chunking raised real-world success from <20% (k=1) to 80–90% | 9, 24 | **ERR**: the chunking ablation is in simulation, 1% at k=1 → 44% at k=100 |
| Sequential insertion: ACT 0% at stages 3–4; MTIL (Mamba history) 54% | 3, 26 | **OK** (real dual UR3, 50 rollouts); a method comparison |
| Latent Weight Diffusion: 18× smaller models | 23 | **PART**: arXiv 2410.14040 is now titled WARPD; "18×" not found |

### 3.5 Visuomotor blindness and contact forces

| Claim | Cites | Verdict |
|---|---|---|
| Touch reduces contact-related failures by over 40% | 8 | **OK** |
| Match lighting / whiteboard: vision-only 13–20% → vision+touch 80% | 8 | **OK** (3 seeds × 10 real rollouts) |
| Masked tactile training: vision-only 20% → 40% | 8 | **OK** |
| ForceFlow: 20% without force prediction → 81.67% | 30 | **ERR**: 44.17% without force on average (20% only on one task) |
| FTP-1: +31.6% on unseen tactile sensors; AgenticTactileVLA: 65.7% fewer interventions | 29, 18 | Not checked (not needed for the scoring) |

### 3.6 Interpolation artifacts in data generation

| Claim | Cites | Verdict |
|---|---|---|
| MinInter: up to +20.7% policy success, +12.8% data-generation success over MimicGen | 34 | **OK** |
| Gains largest in contact-rich and long-horizon tasks | 34 | **OK** (Nut Assembly D0 +31.1% generation success) |

### 3.7 Synthesis and recommendations (summary)

NotebookLM argues the six mechanisms interact:
- vision-only sensing plus long open-loop chunks amplifies drift;
- absolute actions plus non-physical interpolated data causes binding;
- generative heads plus missing recovery data still fail out of distribution.

It recommends:
- generative heads;
- absolute pose actions;
- chunks of 8–16 with receding horizon or temporal ensembling;
- tactile or force sensing with compliant control;
- recovery data and interpolation-minimizing data generation.

These are reasonable design heuristics. The first one rests on the multimodality argument that its own
source [6] contests.

### Source list as given (34 entries, grouped)

- Diffusion Policy: alphaXiv, arXiv HTML (2303.04137) and ResearchGate copies [1, 2, 5]
- MTIL, arXiv 2505.12410 [3, 26]
- Hoque, PhD thesis on lifelong imitation learning [4]
- *Much Ado About Noising*, arXiv 2512.01809 [6]
- Geometry-aware Policy Imitation, arXiv 2510.08787 [7]
- Match lighting with tactile sensing, arXiv 2504.13618 [8]
- ACT, RSS 2023 [9]
- H3DP, ICLR 2026 [10]
- MILE, arXiv 2502.13519 and lab PDF [11, 12, 15]
- Behavior Retrieval [13]
- IntervenGen, OpenReview [14]
- DiscoDemo, arXiv 2610.32093 [16]
- RL for diffusion policies survey, MDPI [17]
- AgenticTactileVLA [18]
- Robotic ultrasound from freehand demonstrations, arXiv 2610.32525 [19]
- Point-cloud flow-matching policies, arXiv 2409.07343 [20]
- Equivariant Diffusion Policy [21]
- Spatially Conditioned Diffusion Policy [22]
- arXiv 2410.14040 (now WARPD) [23]
- ConceptACT [24]
- Revisiting open-loop execution, arXiv 2608.15938 [25]
- InterACT [27]
- ProTracer, arXiv 2609.21369 [28]
- FTP-1 [29]
- ForceFlow, arXiv 2605.11048 [30]
- Hugging Face papers page [31]
- WT-UMI, arXiv 2606.13232 [32]
- ViTacFormer [33]
- MinInter, arXiv 2606.24078 [34]

**Assessment.** NotebookLM gave the broadest narrative and the most plausible-looking replication claims.
Most of its numbers are right. Its errors carry weight, though: it inverted the noising paper, it moved a
simulation ablation to the real robot, and it credited an equivariance gain to action parameterization.

---

## Across the three

- **No overlap.** The three outputs share no paper with one another. Together with Claude's short search they
  cite only 2 papers more than once (RDP and *Much Ado About Noising*).
- **Prompt structure decided the evidence type.** The structured prompt produced single-factor ablations. The
  short prompt produced method-vs-baseline claims.
- **None found a real replication.** None separated grasp from insertion. Claude's short search found the one
  paper that does (Query-Centric Diffusion Policy).
- How these outputs compare with the crawler: `index.html`. How they feed the survey: `survey.md`, Part 3.
