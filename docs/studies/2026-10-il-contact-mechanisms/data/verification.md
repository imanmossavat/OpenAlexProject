# Verification ledger (2026-10-29)

Every claim below was checked against the paper's own text (arXiv HTML full text, downloaded 2026-10-29).
"Fig. only" means the number sits in a figure and cannot be checked from the text; it is neither
confirmed nor counted as an error. Verdicts: **OK** (matches the paper), **ERR** (contradicted by the paper),
**PART** (partly right; the deviation is stated), **NF** (paper not found as cited, after a web search).

## ChatGPT deep research, structured AI-written prompt (G1): 9 rows, 5 papers

| # | Claim | Paper says | Verdict |
|---|---|---|---|
| 1 | Lightness DR: w/o 6/10, 1/10, 1/10 vs with 10/10, 8/10, 6/10; real, ACT, Franka (arXiv 2609.38401, Table 3) | Same numbers, 10 trials per condition, ACT, real | OK (task is cube pick-and-place: outside the contact-rich scope) |
| 2 | Confounded vs independent variation: 0.0846 vs 0.0755 action error, sim (Fig. 6c) | Direction confirmed in text ("independent variation achieves lower action error"); numbers Fig. only | OK direction / Fig. only (out of scope: pick-and-place, metric is action error) |
| 3 | FACTR curriculum: fixed blur 16/25 vs linear 19/25 (Table II); **"Simulated (bimanual Franka)"** | Table II correct; FACTR is a **real-robot** study ("In our real-world evaluation…"); the attention figure is Fig. 8, not Fig. 9 | ERR (sim/real) |
| 4 | robomimic Square: **MH BC 0% vs BC-RNN 2%; PH 70% vs 80%**, 50 trials | Table 1: PH 78.7 vs 84.0; MH 52.7 vs 78.0; 3 seeds × 50 rollouts, max over training | ERR (numbers) |
| 5 | MINT: camera loss removes a large share of successes; MINT recovers part (Fig. 1b) | Caption quoted correctly; π0.5, GR00T N1.5, AgiBot G2 | OK (out of scope: kitchen VLA tasks) |
| 6 | Unpacking DP Table 2: single-step execution PegInsertionSide 80→55, TurnFaucet 59→35, Door 95→46; Hammer exception; **"100 eval runs"** | Numbers correct; the paper states no rollout count | PART (trial count invented) |
| 7 | Unpacking DP Table 3: no receding horizon Relocate 64→11, StackCube 99→88, Pen 71→73 | Correct | OK |
| 8 | Unpacking DP Table 4: MLP denoiser PegInsertionSide 80→21, Relocate 64→7 | Correct | OK |
| 9 | Unpacking DP Table 5: no FiLM PegInsertionSide 80→44, TurnFaucet 59→27, Relocate 64→2 | Correct | OK |

Distinct factual errors: 3 (FACTR sim/real; robomimic numbers; invented trial count). Rows outside the
contact-rich scope: 3 of 9. Not delivered although asked: grasp-vs-insertion answer, list of correlational
claims, list of consulted papers. Replication column: "None found" in all 9 rows.

## ChatGPT deep research, human gist prompt (G2): 5 rows, no IDs, answered in Dutch

| # | Claim | Paper says | Verdict |
|---|---|---|---|
| 1 | MiTaS (Krohn 2026, CoRL): vision-only 35% → 80%; **Flexiv Rizon**; 30 demos; 20 trials per model | arXiv 2606.06281: vision-only 35.5% (ViT) / 34.5%, visuotactile Sparsh-X 55.5%, MiTaS 80%; **Franka Panda**; 30 demos; 20 trials per dataset, 40 per model. CoRL only via a co-author's post | PART (robot wrong) |
| 2 | Li & Brock 2026: environment constraints, baseline 0% → 100% (10/10) | No 2026 paper found on the web or in OpenAlex; nearest is Li, Baum, Brock 2022/2023 | NF |
| 3 | Kim et al. 2023 TRO: F/T + dual-action transformer + gaze, bottle-cap opening, 83.3%, ~18 trials | arXiv 2202.09574: DA-force 83.3% cumulative over 18 trials on bottle A; No-force reaches and grasps but fails in rotation (fingertip slip). Venue not confirmed | OK (venue unconfirmed) |
| 4 | Shukla et al. 2025 NAMRC: force-conditioned diffusion, bimanual battery-cover assembly | No such paper found; related: Shukla et al. ICRA 2025 (sheet separation), arXiv 2608.03103 (2026) | NF |
| 5 | RDP (Xue 2025 RSS): >35% over visual IL | Abstract: ">35%" over DP baselines in three tasks | OK |

Distinct factual errors: 3 (2 citations not found; 1 wrong robot). Most rows are method-vs-baseline gains,
the kind of evidence the question excludes; rows 1 and 3 do contain within-paper ablations.

## NotebookLM deep research (NB): 6 mechanisms, ~34 links

| # | Claim | Paper says | Verdict |
|---|---|---|---|
| 1 | Real Push-T: IBC 0%, best GMM 20% → DP 95% | DP Table 6: baselines 0.00–0.20, DP 0.95 | OK (method comparison, not a single-factor change) |
| 2 | Robomimic: replacing unimodal heads with DP gives +46.9% | 46.9% is DP's average gain over prior state of the art across 15 tasks on 4 benchmarks | PART (misdescribed) |
| 3 | Much Ado About Noising [6] supports "generative heads beat regression because of multimodal averaging"; unimodal models fail at Tool-Hang hook engagement | The paper argues the opposite: GCPs "do not owe their success to their ability to capture multi-modality"; gaps appear only on high-precision tasks (Tool-Hang, Transport); a 2-step MIP matches flow. "Hook engagement" not in the paper | ERR (inverted) |
| 4 | Match lighting: vision-only 13–20% → vision+touch 80%; masked training 20 → 40%; failure rate down >40% | Correct (3 seeds × 10 real rollouts) | OK |
| 5 | Flow vs DDIM: 30% → 80% | 30% is DP architecture + DDIM; same architecture with DDIM is 53% → flow 80% | PART (conflates architecture and sampler) |
| 6 | MILE: physical peg insertion, augmenting offline data, 80% after 4 iterations vs BC <40% | Real task is an octagonal block through a hole (WidowX); MILE uses only intervention data, no offline demos; 80% after 4 iterations confirmed; "<40%" not in text (Fig. only) | PART |
| 7 | DiscoDemo: 39% → 78% real | 78% vs 39% for the **strongest baseline**, averaged over 4 tasks incl. peg insertion, same π0.5 policy | OK |
| 8 | DP: position control beats velocity; peak performance with latency up to 4 steps; action horizon 8 optimal | Correct | OK |
| 9 | Equivariant DP: absolute SE(3) actions give +21.9% | 21.9% is the gain from SO(2) equivariance over baseline DP | ERR (misattributed) |
| 10 | ACT: chunking raised real-world success from <20% (k=1) to 80–90% | The chunking ablation is in simulation: 1% at k=1 → 44% at k=100 (4 sim settings) | ERR |
| 11 | MTIL: ACT 0% at stages 3–4, MTIL 54% | Correct (real dual UR3, 50 rollouts) | OK |
| 12 | ForceFlow: 20% without force → 81.67% | Without force: 44.17% average (20% only on Stamp) | ERR |
| 13 | MinInter: up to +20.7% policy, +12.8% data generation | Correct | OK |
| 14 | Names: "Interventional MimicGen", "Mental Model Interventions", "Latent Weight Diffusion (arXiv 2410.14040)" | IntervenGen; MILE; arXiv 2410.14040 is now titled WARPD; "18× smaller" not found | PART (naming) |
| 15 | Replication: DP3, SCDP, OpenVLA-OFT, H3DP etc. "replicate" mechanisms | These adopt a design or report method gains; none re-runs the original intervention | Not replications |

Factual errors (ERR): 4 (rows 3, 9, 10, 12). Partly right (PART): 5 (rows 2, 5, 6, 14, and row 15's
replication framing is scored separately).

## Claude web search (CS): 6 queries, ~2 minutes, 13 papers

| Claim | Paper says | Verdict |
|---|---|---|
| RDP: normal-force only 0.95 → 0.48 | Table VI, same | OK |
| QDP: w/o query insert 0.59 → 0.06, grasp 0.64 → 0.60, sim | Table I, same (screw 0.80 → 0.33) | OK |
| DexTac: 91.67%, +31.67 points over force-only | Abstract, same | OK |
| ACP: >50% over visuomotor baselines | Abstract, same | OK |
| PTP: ~3× (flagged by the search as secondary) | Abstract: 3× and >10× faster training | OK |
| DexForce: +1600% (flagged by the search as unverified secondary source) | Not checked | — |
| MiTaS 31% vision-only (search excerpt, used in data/verify_web.md) | Paper: 35.5% | ERR (corrected) |

## Papers found only by the crawler and verified

| Paper | Finding | Source |
|---|---|---|
| FoAR (arXiv 2411.15753, 2024/25; cites ACP) | Real, RISE policy, 20 trials per method. Wiping score: vision-only 0.500, force as tokens 0.575, force concatenated 0.475, contact-gated force (FoAR) 0.875. Peeling: 0.377 / 0.487 / 0.524 / 0.756 | Table I |
