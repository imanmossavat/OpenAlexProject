# Claude web search log (2026-10-29)

Six searches, standard mode, 08:02:20–08:02:37 UTC plus reading time (about 2 minutes in all). Run after the
pre-registration was saved and before any crawl or ChatGPT output. Deliberately short, as in the NCA study.

| # | Query |
|---|---|
| 1 | imitation learning contact-rich manipulation ablation force tactile policy ignores force 2025 2026 |
| 2 | "Much Ado About Noising" generative robotic control myths |
| 3 | diffusion policy insertion assembly failure analysis grasp vs insertion phase ablation real robot 2025 |
| 4 | what matters in imitation learning robot manipulation controlled study action chunking history proprioception shortcut 2025 |
| 5 | compliance stiffness prediction imitation learning contact-rich adaptive compliance policy ablation |
| 6 | past token prediction long-context diffusion policy history copycat robot 2025 |

## Papers named (become crawl-B seeds)

| Paper | arXiv | Lead claim from the search (unverified) |
|---|---|---|
| DexTac (2026) | 2601.21474 | Contact-region variant 91.67% on syringe injection, +31.67 points over force-only |
| DexForce (2025) | 2501.10356 | Force-informed actions; secondary source claims large gains over RGB-only |
| Reactive Diffusion Policy (2025) | 2503.02881 | Normal-force-only input: peeling 0.95 → 0.48 |
| TacForeSight (2026) | 2606.11184 | Ablates force-conditioning and tactile fusion |
| Query-Centric Diffusion Policy (2025) | 2509.18686 | Sim: removing queries drops insert 0.59 → 0.06, grasp 0.64 → 0.60 (grasp vs insertion separated) |
| ContactDP (2026) | 2609.23800 | Contact-guided DP vs vision-only DP, tight connector insertion, real robot |
| Automating Deformable Gasket Assembly (2024) | 2408.12593 | Rates alignment and insertion separately |
| Adaptive Compliance Policy (2024/25) | 2410.09309 | >50% over visuomotor baselines with learned compliance |
| Stiffness Copilot (2026) | 2603.14068 | Kinesthetic stiffness labels biased soft |
| VIDP (2026) | 2608.06210 | Variable impedance DP beats fixed impedance |
| Direction Matters / TDC (2026) | 2602.14174 | Predict force direction, not magnitude (OpenAlex title: "TDC: Sim-to-Real Transferable Directional Compliance…") |
| Past-Token Prediction (2025) | 2505.09561 | Diffusion policies under-use history; PTP ~3× on long-context tasks (secondary source) |
| Learning Foresight without Explicit Trajectories for 3D DP (2026) | 2609.20669 | No mechanism stated in the excerpt |

Also mentioned, not seeded (no identifier found): a visuo-tactile two-phase USB insertion paper (ICRA 2023;
45/45 vs 1/45 for a BC baseline), an adaptive chunk-length paper (MDPI Biomimetics 2026), UMI-FT.
