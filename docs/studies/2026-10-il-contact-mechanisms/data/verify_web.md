# Verification step 1b: web lookup of papers OpenAlex could not settle (2026-10-29)

Rule (from the user): papers cited by an agentic-search source are checked on the web, not only in
OpenAlex, because OpenAlex misses the newest work. "Not found" below means not found on the web.

| Source | Claimed | Web result | Status |
|---|---|---|---|
| ChatGPT gist | Krohn et al. 2026, CoRL, MiTaS; vision-only 35% → 80% | arXiv 2606.06281 (June 2026), Krohn, Helmut, Funk, Peters, Prasad, Chalvatzaki. Reported 80% (MiTaS) vs 54% visual-tactile baseline vs 31% vision-only. CoRL acceptance only via a co-author's LinkedIn post. | Exists; baseline figure slightly off (31%, not 35%) — to confirm in paper |
| ChatGPT gist | Li & Brock 2026, environment constraints, 0% → 100% (10/10) | No 2026 paper found. Closest: Li, Baum, Brock, arXiv 2210.07015 (2022) and IROS 2023, RA-L 2022. | Not found as cited; year likely wrong, numbers unverifiable |
| ChatGPT gist | Kim et al. 2023, TRO, bottle-cap opening with F/T + dual-action transformer + gaze | arXiv 2202.09574, "Training Robots Without Robots: Deep Imitation Learning for Master-to-Robot Policy Transfer" (Kim et al.; OpenAlex year 2023). | Exists; venue (TRO) to confirm |
| ChatGPT gist | Shukla et al. 2025, NAMRC, bimanual battery-cover assembly | No NAMRC 2025 paper found. Related: Shukla et al., ICRA 2025 (force-conditioned DP for sheet separation); arXiv 2608.03103 (2026, hierarchical IL for time-varying forces). | Not found as cited; venue/task likely wrong |
