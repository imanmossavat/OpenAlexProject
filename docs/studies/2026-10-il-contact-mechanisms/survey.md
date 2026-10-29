# Why imitation-learned policies fail at contact: what has been shown by intervention

A working survey, October 2026. Written by Claude (Opus 5.5, Anthropic) for Iman Mossavat.

Every number below was checked against the paper it comes from (full text, 29 October 2026).
The verification ledger is `data/verification.md`. If a number sits only in a figure, the survey says so.
If something is not known, the survey says that too.

---

## 0. The question and the rule

**Question.** For imitation-learned robot policies on contact-rich manipulation, which failure mechanisms
have been shown by intervention, not just correlation? For each one: what was changed, on which task, sim or
real, how big the effect was, and whether anyone replicated it.

**The rule.** A mechanism counts only if someone changed one thing and measured success with and without it.
"Our method beats the baselines" does not count, because a new method changes many things at once.
An ablation table inside a method paper does count, when one row removes one component.

**Short answer.**

- Six mechanisms have clean single-factor evidence on contact-rich tasks. They are force/touch neglect,
  naive force fusion, chunk length vs reactivity, receding-horizon execution, observation history, and
  missing recovery data.
- Two are replicated across groups and policy classes: "force/touch input helps on force-dependent tasks",
  and "some chunking helps, too much hurts".
- One popular explanation is contested by a controlled study: that generative policies win because they
  model multimodal actions.
- Almost nobody separates grasp failures from insertion failures. In the three papers that report results
  per phase, the intervention changes the contact phase much more than the grasp.

---

# Part 1. Methodology: how to show a failure mechanism

## 1.1 Mechanism = effect of an intervention

Write the policy's success as a binary outcome $S \in \{0,1\}$. A design choice $X$ (for example, "force
input on/off") is a mechanism for failure if forcing it changes the success rate:

$$
\Delta = P(S=1 \mid \mathrm{do}(X=1)) - P(S=1 \mid \mathrm{do}(X=0)).
$$

"do" means you set $X$ yourself (retrain with and without it, everything else fixed). It does not mean you
look at runs where $X$ happened to be on. Attention maps, failure-mode tallies, and probing are observations.
They tell you where to look, but they do not establish $\Delta$.

Three designs give you $\Delta$:

1. **Ablation.** Remove one component, retrain, evaluate. Example: Reactive Diffusion Policy (RDP) keeps only
   the normal-force dimension and peeling drops from 0.95 to 0.48.
2. **Dose–response.** Vary a knob over a range. Example: ACT's chunk size $k$ from 1 to 400. A curve is
   stronger evidence than a single on/off pair, because a real mechanism usually shows a shape (here, a rise
   then a dip).
3. **Factorial.** Vary two knobs jointly to see interactions. Example: *Unpacking the Individual Components of
   Diffusion Policy* crosses observation history with the action space (delta vs absolute) and finds history
   matters only for absolute control.

## 1.2 How many trials you need

A success rate from $n$ trials with $k$ successes is $\hat p = k/n$, with standard error

$$
\mathrm{SE}(\hat p) = \sqrt{\hat p(1-\hat p)/n}.
$$

For small $n$, use the Wilson interval instead of $\hat p \pm 1.96\,\mathrm{SE}$:

$$
\frac{\hat p + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}, \qquad z = 1.96.
$$

What that means at the trial counts this field uses:

| Result | 95% Wilson interval |
|---|---|
| 10/20 | 0.30 – 0.70 |
| 16/20 | 0.58 – 0.92 |
| 8/10 | 0.49 – 0.94 |
| 1/10 | 0.02 – 0.40 |
| 10/10 | 0.72 – 1.00 |

To detect a change from $p_1$ to $p_2$ with a two-sided test at $\alpha = 0.05$ and 80% power, you need
roughly this many trials **per condition**:

$$
n \approx \frac{(z_{\alpha/2} + z_{\beta})^2 \,[\,p_1(1-p_1) + p_2(1-p_2)\,]}{(p_1 - p_2)^2}, \qquad z_{\alpha/2}=1.96,\; z_\beta = 0.84.
$$

| Change | Trials per condition |
|---|---|
| 0.2 → 0.6 | ≈ 20 |
| 0.5 → 0.9 | ≈ 17 |
| 0.6 → 0.8 | ≈ 78 |
| 0.5 → 0.7 | ≈ 90 |
| 0.64 → 0.76 | ≈ 225 |

So 20 trials per condition detects big effects (30–40 points) and nothing smaller. Two checks on published
ablations:

- FACTR's curriculum-schedule ablation compares a constant blur (16/25) with a linear schedule (19/25).
  Fisher's exact test gives $p = 0.54$. The table cannot tell those two apart. FACTR's main result (below)
  is a much larger effect and does not have this problem.
- *Memorize, Adapt, Ignore* reports lightness randomization raising out-of-distribution success from 1/10
  to 8/10 ($p = 0.006$, a real effect) and in-distribution success from 6/10 to 10/10 ($p = 0.09$, not
  resolved at 10 trials).

**Seeds and checkpoints.** Training noise adds variance on top of rollout noise. robomimic trains 3 seeds,
runs 50 rollouts per checkpoint, and reports the **maximum** success over training. That is an optimistic
number. On a real robot you evaluate the final checkpoint, so real-robot numbers are not directly comparable
with max-over-training simulation numbers.

## 1.3 Separating grasp from insertion

For a task with a grasp phase and an insertion phase,

$$
P(S) = P(G)\cdot P(I \mid G),
$$

where $G$ is "grasp succeeded" and $I$ is "insertion succeeded". A single success rate hides which factor
moved. Report both: the grasp rate $P(G)$, and the insertion rate *conditioned on a good grasp*,
$P(I \mid G)$. An intervention is phase-specific if it moves one factor and not the other. Two ways to get
there:

1. Log the phase at which each trial fails, for every condition (cheap, works on real robots).
2. Start rollouts after the grasp (a scripted or replayed grasp), so you measure $P(I \mid G)$ directly
   (easy in simulation).

## 1.4 What counts as a replication

- **Replicated:** the same mechanism shown by a *different group* on a *different policy class or task*.
- **Weakly replicated:** the same group, or the same policy on a new task.
- **Contested:** a controlled result points the other way.
- **Single:** one source.

A later paper that *adopts* a design (for example, uses absolute actions) is not a replication. It never
measured the effect of removing it.

## 1.5 Theory you need to read the evidence

**Compounding error.** Plain behaviour cloning trains on the expert's state distribution and is tested on
its own. With per-step error $\epsilon$ over horizon $T$, the classic bound (Ross and Bagnell) gives a
cost gap that grows like $T^2\epsilon$ for behaviour cloning and like $T\epsilon$ for interactive methods
such as DAgger, which collect labels on the learner's own states. *The Pitfalls of Imitation Learning when
Actions are Continuous* (2025) sharpens this for continuous control. Even with exponentially stable dynamics
and a smooth, deterministic expert, any smooth deterministic imitator suffers execution error exponentially
larger in the horizon than its training error. The exceptions are imitators that are non-smooth,
non-Markovian, or state-dependently stochastic (which covers chunking and diffusion policies), or data that
is spread out enough. That is the theoretical reason behind three of the mechanisms below: chunking, history,
and recovery data.

**Chunking shortens the horizon.** Predicting $k$ actions per observation and executing them open-loop cuts
the number of decisions from $T$ to $T/k$. That reduces compounding but removes feedback for $k$ steps.
Expect an optimum in $k$.

**Regression averages.** A policy trained with squared error predicts $\mathbb{E}[a \mid o]$. If the
demonstrations contain two valid actions $a_1, a_2$ at the same observation, the prediction is their
average, which may be invalid. That is the textbook argument for generative policies. Section 2.4 shows it is
not what explains their advantage on standard benchmarks.

---

# Part 2. Applied: the mechanisms, one by one

Abbreviations: DP = Diffusion Policy, ACT = Action Chunking with Transformers, BC = behaviour cloning,
GCP = generative control policy, RCP = regression control policy.

## 2.1 Force and touch neglect

**Claim.** On tasks where the outcome depends on contact forces, vision-only policies fail, and adding
force/touch fixes much of it.

| Intervention | Task | Sim/real | Effect | Trials |
|---|---|---|---|---|
| FACTR: add force; then add the force-attending curriculum (blur vision early in training) | Box lifting, pivoting, fruit pickup, dough rolling; novel test objects | Real (bimanual Franka, ACT, 50 demos) | Test objects: vision-only 21.3% → vision+force 61.2% → FACTR 87.5% | 5–10 per object |
| FACTR recovery test (box knocked down after first lift) | Box lifting, test objects | Real | Vision-only drops from 31.7% (first attempt) to 13.3% (second); force-attending policies hold their rate | 5 per object |
| Match lighting: add a tactile sensor | Match lighting; whiteboard erasing | Real | Best vision-only ≤ 20% → vision+touch 80%; erasing 13% → 80% | 3 seeds × 10 |
| MiTaS: add two tactile sensors (GelSight Mini + event-based Evetac) | Five contact-rich tasks incl. key-in-lock, lightbulb | Real (Franka Panda, 30 demos) | Vision-only 35.5% → visuotactile baseline 55.5% → MiTaS 80% | 40 per model |
| ForceFlow: remove force from its own model | Six tasks (stamp, plug, press, insert, clean ×2) | Real | Without force 44.17% → with 81.67% (average) | 20 per task |
| RDP: keep only normal force, drop shear/torque | Peeling | Real | 0.95 → 0.48 | 10 per test variation |
| Kim et al.: remove F/T input | Bottle-cap opening | Real | With F/T 83.3% cumulative; without, reach and grasp succeed but rotation fails (fingertip slips) | 18 |

**Replication: replicated.** At least four groups (CMU, TU Darmstadt, Tsinghua/Shanghai Jiao Tong,
Tokyo, plus the ForceFlow authors), several policy classes (ACT, flow-matching policies, diffusion, a
dual-action transformer), and many tasks.

**Training trick that makes force usable: masked training.** Training with touch and then masking it makes
the *vision-only* policy better: match lighting rises from 20% to 40%. The tactile signal shapes the
representation even when it is absent at test time.

## 2.2 Naive force fusion is under-used

**Claim.** Feeding force in as one more input is not enough. The policy under-uses it unless the
architecture or training forces attention to it.

| Intervention | Task | Sim/real | Effect | Trials |
|---|---|---|---|---|
| FACTR: same ACT with force, with vs without the curriculum | As above | Real | 61.2% → 87.5% (test objects) | 5–10 per object |
| FoAR: force as extra tokens or concatenated vs gated by a predicted-contact signal | Wiping, peeling | Real (RISE policy) | Wiping score: vision-only 0.500, tokens 0.575, concat 0.475, gated 0.875. Peeling: 0.377 / 0.487 / 0.524 / 0.756 | 20 per method |
| RDP: DP with tactile embedding vs DP | Peeling | Real | 0.39 vs 0.44: no gain from naive tactile input | 10 per test variation |

**Replication: replicated in direction by two groups, contested in size.** FoAR and RDP (both from Cewu
Lu's group, Shanghai Jiao Tong) show naive fusion gives little or nothing. FACTR (CMU) shows naive force
already helps a lot (21.3% → 61.2%), with the curriculum adding another 26 points. Your own result fits this pattern: the force benefit held for one
policy and broke for three others. Read together, these say the gain from force depends on how the policy
consumes it. Nobody has run the same fusion choices across several policy classes on the same task. That
experiment is open.

## 2.3 Chunk length and receding horizon

**Claim.** Predicting and executing action sequences beats single-step control, up to a point. Too long a
chunk loses reactivity.

| Intervention | Task | Sim/real | Effect | Trials |
|---|---|---|---|---|
| ACT: chunk size $k$ from 1 to 400 | Two sim bimanual tasks, scripted and human data | Sim | 1% at $k=1$ → 44% at $k=100$; slight dip at $k=200, 400$ | Average of 4 settings |
| DP: action horizon sweep | Several sim tasks | Sim | Optimum at 8 steps for most tasks; longer horizons lose reaction time | Paper's Fig. 5 |
| Unpacking DP: execute one action instead of the sequence | PegInsertionSide, TurnFaucet, Door, … | Sim (ManiSkill, Adroit) | 80 → 55, 59 → 35, 95 → 46; Hammer is the exception (17 → 27) | Not stated |
| Unpacking DP: turn off receding-horizon control | Long-horizon tasks | Sim | Relocate 64 → 11, StackCube 99 → 88; short task Pen 71 → 73 | Not stated |
| RDP vs DP under perturbation after contact | Peeling | Real | DP 0.19 vs RDP 0.88 (method comparison: RDP adds a fast tactile loop) | 10 per variation |

**Replication: replicated in simulation** (ACT, DP, Unpacking DP: three groups, two policy classes). The
trade-off has a name in *Bidirectional Decoding* (2024): chunking captures temporal dependencies in the
demonstrations at the cost of reactivity to unexpected states. The real-robot evidence for "too long hurts
on contact" is a method comparison (RDP), not a chunk-length sweep. A real-robot sweep on an insertion task
is missing.

## 2.4 Generative vs regression heads: the multimodality story is contested

**Popular claim.** Diffusion and flow policies win because they model multimodal action distributions.

**What the controlled study found.** *Much Ado About Noising* (ICLR 2026) compares GCPs and RCPs with the
architecture held fixed, across 28 behaviour-cloning benchmarks.

- On tasks long thought to be multimodal, like Push-T, there is no substantial gap between GCPs and RCPs.
- GCPs win only on high-precision tasks (Tool-Hang, Transport).
- Sampling the noise as $z=0$, as random, or as the mean of 64 samples barely matters. On Tool-Hang it gives
  0.78, 0.80 and 0.76. A policy that needed its multimodality would not survive $z=0$.
- A two-step "minimal iterative policy" (MIP) matches flow policies.

The authors attribute the advantage to iterative computation with supervised intermediate steps and some
stochasticity in that supervision, not to distribution fitting.

**Evidence on the other side, and how to read it.**

- ACT's CVAE ablation: removing the CVAE leaves scripted-data success unchanged, but on human data success
  drops from 35.3% to 2%. That is consistent with "human data needs something more than plain regression".
  It does not separate multimodality from the other effects Much Ado identifies.
- DP's large gains over LSTM-GMM and IBC (real Push-T: best baseline 20% vs DP 95%) are method comparisons.
  Architecture, action space and training all change at once.

**Status: contested.** For your purposes, "use a diffusion head" is not a mechanism. "Iterative refinement
helps on high-precision tasks" is the testable version.

## 2.5 Observation history

**Claim.** It depends on the policy class and the action space. This is the clearest case where a simple
claim breaks.

| Intervention | Task | Sim/real | Effect | Trials |
|---|---|---|---|---|
| robomimic: BC vs BC-RNN (history via an RNN) | Square (nut on peg) | Sim | PH: 78.7 → 84.0; MH: 52.7 → 78.0 | 3 seeds × 50, max over training |
| Unpacking DP: remove observation history | 8 tasks | Sim | About a 10% drop on absolute-control tasks (Relocate 64 → 47); none on delta-control tasks (PegInsertionSide 80 vs 81) | Not stated |
| Past-Token Prediction (PTP): naive history vs history + an auxiliary loss predicting past actions | 6 sim + 4 real tasks | Sim + real | Naive history makes diffusion policies *worse*; PTP gives over 30% improvement over no-history and over 60% over naive history; 3× on long-context policies overall | Paper's tables |
| MTIL vs ACT (full history via Mamba) | Sequential insertion, 4 stages | Real (dual UR3) | ACT 0% at stages 3–4 (identical-looking states); MTIL 54% overall | 50 |

Note that BC vs BC-RNN changes the architecture as well as the history, and MTIL vs ACT is a method
comparison.

**Status: conditional, not contradictory.**

- History helps regression policies on human data (robomimic, 2021).
- Naive history hurts diffusion policies, and a past-action loss fixes it (PTP, 2025).
- History matters for absolute but not delta actions (Unpacking DP).
- Nobody has crossed policy class × action space × history on one contact task. That experiment is open, and
  cheap in simulation.

## 2.6 Action space and latency

| Intervention | Task | Sim/real | Effect |
|---|---|---|---|
| DP: position vs velocity control, same policy | Sim benchmarks | Sim | Position control consistently better (Fig. 4) |
| DP: added latency | Sim | Sim | Peak performance holds up to 4 steps of latency with position control; velocity control degrades more |

**Status: single source** for the clean ablation. *Real-time chunking* (2025) addresses the related
inference problem, pauses and jerky motion at chunk boundaries, with asynchronous execution.

## 2.7 Architecture details that matter on hard tasks

*Unpacking the Individual Components of Diffusion Policy* (sim, ManiSkill and Adroit):

| Change | PegInsertionSide | TurnFaucet | Relocate | Easy tasks |
|---|---|---|---|---|
| U-Net → MLP denoiser | 80 → 21 | 59 → 22 | 64 → 7 | StackCube 99 → 99, Pen 71 → 68 |
| FiLM conditioning → direct input | 80 → 44 | 59 → 27 | 64 → 2 | StackCube 99 → 97, Pen 71 → 75 |

The DP paper's own encoder ablation, on robomimic Square (PH): ResNet-18 trained from scratch 0.94, frozen
pretrained 0.58, fine-tuned 0.92. A CLIP ViT-B is 0.22 from scratch, 0.70 frozen and 0.98 fine-tuned.

robomimic: removing image randomization costs 47% (relative) on Square; removing the wrist camera costs 9%.

**Status: single source each.** These are easy, visible, simulation-testable knobs.

## 2.8 Data: recovery data, generation artifacts, diversity

| Intervention | Task | Sim/real | Effect | Trials |
|---|---|---|---|---|
| DiscoDemo: RL-discovered demonstrations vs human / sim-generated data, same π0.5 policy | Pick-and-place, stacking, two peg insertions | Sim + real | Real: 78% vs 39% (strongest baseline), average of 4 tasks | Paper's tables |
| MILE: learn from interventions only, modelling when humans intervene | Octagonal block through a tight hole | Real (WidowX) | 80% after 4 iterations; IL-from-intervention baselines "struggle" (figure) | Fig. only |
| MinInter: pick source segments that minimize linear interpolation in MimicGen | 12 MimicGen tasks incl. Nut Assembly | Sim | Policy success up to +20.7%; data-generation success +12.8% on average (Nut Assembly D0 +31.1%) | Paper's tables |
| robomimic: data quality | Square | Sim | BC drops about 35 points from "better" to "worse" operator data; BC-RNN shrinks the gap on Can but not on Square | 3 seeds × 50 |

**Not contact-rich, but relevant to data design.**

- *Memorize, Adapt, Ignore* (2026): lighting randomization takes out-of-distribution success from 1/10 to
  8/10 (real, ACT, pick-and-place). Independent variation of shape and texture beats confounded variation on
  novel objects (sim, action error).
- *Data Scaling Laws in IL* (2024): generalization follows a rough power law in the number of environments
  and objects. Diversity matters far more than the number of demonstrations per environment.
- *Shortcut Learning in Generalist Robot Policies* (2025): low diversity within sub-datasets and large gaps
  between them drive shortcut learning.

**Status:** "recovery/intervention data fixes compounding error" is supported by several groups. But each
uses a different intervention, so it is a family of results, not a replication of one.

## 2.9 Grasp vs insertion: has anyone separated them?

Barely. These papers do:

| Paper | Intervention | Grasp / early phase | Contact phase |
|---|---|---|---|
| Query-Centric Diffusion Policy (2025, sim, furniture assembly) | Remove the query structure | Grasp 0.64 → 0.60 | Insert 0.59 → 0.06; screw 0.80 → 0.33 |
| Kim et al. (real, bottle cap) | Remove F/T input | Reaching and grasping still succeed | Rotation fails (fingertip slip) |
| MTIL (real, sequential insertion) | ACT vs full-history model (method comparison) | Stage 1: 80 vs 94 | Stages 3–4: 0 vs 62 / 54 |

A related split, by perturbation timing rather than by phase: in RDP's peeling task (real), DP scores 0.58 vs
RDP 0.98 when perturbed before contact, and 0.19 vs 0.88 when perturbed after contact.

In the three phase-resolved cases, the intervention moves the contact phase much more than the grasp. Your nut data
shows most failures at the grasp. The literature's interventions mostly act on the phase *after* the grasp.
So if your failures are grasp failures, the published mechanisms may not be the ones hurting you. Measure
$P(G)$ and $P(I \mid G)$ separately (Section 1.3) before borrowing a fix.

## 2.10 Summary table and where to contribute

| Mechanism | Best single-factor evidence | Sim/real | Status | Visible? | Testable in sim? |
|---|---|---|---|---|---|
| Force/touch neglect | FACTR, MiTaS, ForceFlow, match lighting | Real | Replicated | Yes | Partly (needs force sim) |
| Naive force fusion under-used | FACTR, FoAR, RDP | Real | Direction replicated, size contested | Yes | Partly |
| Chunk length vs reactivity | ACT, DP, Unpacking DP | Sim | Replicated in sim; no real-robot sweep | Yes | Yes |
| Receding-horizon execution | Unpacking DP | Sim | Single | Yes | Yes |
| Observation history | robomimic, Unpacking DP, PTP | Sim (+ real for PTP) | Conditional; interactions untested | Yes | Yes |
| Multimodality explains generative wins | Much Ado About Noising (against) | Sim | Contested | Yes | Yes |
| Position vs velocity actions | DP | Sim | Single | Yes | Yes |
| Denoiser / FiLM architecture | Unpacking DP | Sim | Single | Yes | Yes |
| Recovery / intervention data | DiscoDemo, MILE, IntervenGen | Sim + real | A family, not a replication | Yes | Yes |
| Data-generation interpolation artifacts | MinInter | Sim | Single | Yes | Yes |
| Grasp vs insertion separation | QDP, Kim | Sim / real | Nearly absent | Yes | Yes |

**Experiments that pass all three tests** (visible mechanism, testable in simulation, single or contested):

1. **History × policy class × action space on one insertion task.** Combine robomimic, Unpacking DP and PTP
   in one factorial design. It resolves an apparent contradiction.
2. **Force-fusion choices across policy classes on the same task.** Compare token vs concatenation vs gated
   vs curriculum across ACT, DP and a flow policy. This is your own broken-on-three-policies result, made
   systematic.
3. **Chunk-length sweep with phase-resolved metrics on insertion.** Does too long a chunk hurt $P(I \mid G)$
   but not $P(G)$?
4. **Regression vs MIP vs flow on tight-tolerance insertion.** Much Ado says the gap shows up only on
   high-precision tasks; insertion is the obvious high-precision test it did not focus on.

Any of these, run with at least 50 trials per condition (Section 1.2) and reported per phase, would be a
contribution, because no published study does it.

---

# Part 3. Extra chapter: comparing the search methods

Five ways of gathering this literature were run on the same question on 29 October 2026. What ChatGPT and NotebookLM returned, claim by claim with verdicts, is in `external-outputs.md`. They were scored
against a checklist written and timestamped before any results were seen (`preregistration.md`).

| | ChatGPT deep research, structured AI-written prompt | ChatGPT deep research, short human prompt | NotebookLM deep research | Claude web search (6 queries, ~2 min) | ArticleCrawler (citation crawl in OpenAlex) |
|---|---|---|---|---|---|
| Rows / papers | 9 rows, 5 papers | 5 rows, 5 papers | 6 mechanisms, ~34 links | 13 papers | 11,073 and 13,555 papers (two crawls) |
| Papers that exist as cited | 5/5 | 3/5 | Most; 3 misnamed | 13/13 | n/a (all real) |
| Numbers checked against the paper | 3 errors, 1 invented trial count | 3 errors (2 citations not found, 1 wrong robot) | 4 errors, 5 partly right | 0 errors in 5 checked claims | n/a |
| Single-factor evidence | Mostly yes | Mostly no | Mixed | Mixed | Raw papers; needs reading |
| Replication | "None found" everywhere | Not reported | Claimed, but adoptions, not replications | Not attempted | Holds nearly every OpenAlex-indexed citer of the key papers; surfaced FoAR |
| Newest work (2026) | Two Sept 2026 papers | MiTaS (June 2026) | Several 2026 papers | Several 2026 papers | Weak: most 2026 papers have no citation links in OpenAlex |
| Grasp vs insertion | Not answered | Not answered | Not answered | Found QDP | Not answered without analysis |

**What each one is good for.**

- **ChatGPT with a structured prompt** reads ablation tables well. The exact table numbers it reported for
  *Unpacking DP* were all correct. It still made errors on sim/real labels and on an older paper's numbers,
  and it skipped half of what it was asked to deliver.
- **ChatGPT with a short prompt** returned method-vs-baseline claims (the evidence the question excludes),
  two citations that could not be found, and answered in Dutch. Prompt structure mattered more than any
  other variable here.
- **NotebookLM** gave the broadest narrative and the most plausible-sounding replication claims, and it made
  the most consequential error: it cited *Much Ado About Noising* as support for the very explanation that
  paper argues against.
- **Claude's short web search** was accurate on every number it reported and found the only paper that
  separates grasp from insertion. It was not built to be exhaustive.
- **The crawler** cannot reach papers that OpenAlex holds without references or citations. In this study
  that was 17 of the 36 evidence papers, 16 of them from 2025–2026. Where links exist, it gathers the
  neighbourhood completely, including papers no search tool named (FoAR, which turned out to be the best
  evidence for Section 2.2).

**Practical recipe.** Use a structured prompt for the first pass. Seed the crawler with what search finds.
Check every number against the paper. Use the crawl to find the papers that cite each piece of evidence,
which is where replications and contradictions live.
